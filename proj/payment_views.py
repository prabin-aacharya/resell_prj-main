import uuid
import requests
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User

from .models import Product, BikePaymentTransaction, Customer

logger = logging.getLogger(__name__)

@login_required
def initiate_bike_payment(request):
    """
    Initiates a payment with Khalti KPG-2 for a bike purchase
    """
    if request.method != 'POST':
        return redirect('home')
    
    bike_id = request.POST.get('bike_id')
    sale_price = request.POST.get('sale_price')
    
    if not bike_id or not sale_price:
        messages.error(request, "Missing product information")
        return redirect('home')
    
    try:
        # Get product and user information
        product = get_object_or_404(Product, id=bike_id, status='available')
        buyer = request.user
        
        # Get seller info (assuming product has a seller field)
        # If not, you can adjust this to get the seller from elsewhere
        seller = get_object_or_404(User, username=product.seller_name)
        
        # Format amount (convert to paisa)
        amount = int(float(sale_price) * 100)
        if amount <= 0:
            messages.error(request, "Invalid product price")
            return redirect('home')
        
        # Generate a unique order ID
        purchase_order_id = f"BIKE-{uuid.uuid4()}"
        
        # Get customer info for the buyer
        customer = get_object_or_404(Customer, user=buyer)
        
        # Prepare the return URL
        return_url = request.build_absolute_uri(reverse('verify_bike_payment'))
        website_url = request.build_absolute_uri('/')
        
        # Prepare payload for Khalti
        payload = {
            "return_url": return_url,
            "website_url": website_url,
            "amount": amount,
            "purchase_order_id": purchase_order_id,
            "purchase_order_name": f"Bike Purchase: {product.title}",
            "customer_info": {
                "name": buyer.get_full_name() or buyer.username,
                "email": buyer.email,
                "phone": customer.mobile,
            },
            "product_details": [
                {
                    "identity": str(product.id),
                    "name": product.title,
                    "total_price": amount,
                    "quantity": 1,
                    "unit_price": amount,
                }
            ],
            "amount_breakdown": [
                {
                    "label": "Bike Price",
                    "amount": amount
                }
            ]
        }
        
        # Make the request to Khalti
        headers = {
            "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                "https://a.khalti.com/api/v2/epayment/initiate/",
                json=payload,
                headers=headers
            )
            
            # Log the response for debugging
            logger.info(f"Khalti initiate response: {response.status_code}, {response.text}")
            
            # Check if the response was successful
            response_data = response.json()
            if response.status_code == 200 and response_data.get('payment_url'):
                # Store transaction details
                transaction = BikePaymentTransaction.objects.create(
                    pidx=response_data['pidx'],
                    purchase_order_id=purchase_order_id,
                    product=product,
                    buyer=buyer,
                    seller=seller,
                    amount=amount,
                    status='Initiated'
                )
                
                # Update product status to pending
                product.status = 'pending'
                product.save()
                
                # Redirect to Khalti payment page
                return redirect(response_data['payment_url'])
            else:
                # Handle error
                error_msg = response_data.get('detail', 'Payment initialization failed')
                messages.error(request, error_msg)
                return redirect('payment_error', error=error_msg)
                
        except requests.RequestException as e:
            logger.error(f"Khalti request error: {str(e)}")
            messages.error(request, "Could not connect to payment gateway")
            return redirect('payment_error', error="Connection error")
            
    except Exception as e:
        logger.error(f"Payment initiation error: {str(e)}")
        messages.error(request, "An error occurred while processing your payment")
        return redirect('payment_error', error="General error")

@login_required
def verify_bike_payment(request):
    """
    Verifies a payment with Khalti KPG-2 after user returns from payment gateway
    """
    # Get transaction details from callback parameters
    pidx = request.GET.get('pidx')
    purchase_order_id = request.GET.get('purchase_order_id')
    
    if not pidx or not purchase_order_id:
        messages.error(request, "Missing transaction information")
        return redirect('payment_error', error="Invalid transaction")
    
    try:
        # Look up the transaction in our database
        transaction = get_object_or_404(
            BikePaymentTransaction, 
            pidx=pidx,
            purchase_order_id=purchase_order_id
        )
        
        # Verify with Khalti
        headers = {
            "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {"pidx": pidx}
        
        try:
            response = requests.post(
                "https://a.khalti.com/api/v2/epayment/lookup/",
                json=payload,
                headers=headers
            )
            
            # Log the response for debugging
            logger.info(f"Khalti lookup response: {response.status_code}, {response.text}")
            
            # Check if the response was successful
            if response.status_code == 200:
                response_data = response.json()
                
                # Verify the transaction
                if response_data.get('status') == 'Completed':
                    # Verify amount
                    if int(response_data.get('total_amount', 0)) == transaction.amount:
                        # Update transaction status
                        transaction.status = 'Completed'
                        transaction.save()
                        
                        # Update product status
                        product = transaction.product
                        product.status = 'sold'
                        product.save()
                        
                        # Success message and redirect
                        messages.success(request, "Payment successful! Your bike purchase is complete.")
                        return render(request, 'payment_success.html', {'transaction': transaction})
                    else:
                        # Amount mismatch
                        logger.error(f"Amount mismatch: {response_data.get('total_amount')} vs {transaction.amount}")
                        transaction.status = 'Failed'
                        transaction.save()
                        messages.error(request, "Payment verification failed: Amount mismatch")
                        return render(request, 'payment_error.html', {'error': 'Amount verification failed'})
                else:
                    # Payment not completed
                    transaction.status = response_data.get('status', 'Failed')
                    transaction.save()
                    messages.warning(request, f"Payment {transaction.status.lower()}")
                    return render(request, 'payment_error.html', {'error': f"Payment {transaction.status.lower()}"})
            else:
                # Failed to verify with Khalti
                transaction.status = 'Failed'
                transaction.save()
                messages.error(request, "Payment verification failed")
                return render(request, 'payment_error.html', {'error': 'Verification failed'})
                
        except requests.RequestException as e:
            logger.error(f"Khalti verification request error: {str(e)}")
            messages.error(request, "Could not verify payment with gateway")
            return render(request, 'payment_error.html', {'error': 'Verification failed'})
            
    except Exception as e:
        logger.error(f"Payment verification error: {str(e)}")
        messages.error(request, "An error occurred while verifying your payment")
        return render(request, 'payment_error.html', {'error': 'Verification error'})

def payment_error(request):
    """Display payment error page"""
    error = request.GET.get('error', 'Unknown error')
    return render(request, 'payment_error.html', {'error': error})

def payment_success(request):
    """Display payment success page"""
    return render(request, 'payment_success.html') 