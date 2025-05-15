import uuid
import requests
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.utils import timezone

from .models import Product, Customer, BikePaymentTransaction

logger = logging.getLogger(__name__)

@login_required
def initiate_bike_payment(request):
    """
    Initiates a payment with Khalti KPG-2 for a bike purchase
    """
    if request.method != 'POST':
        return redirect('main:home')
    
    bike_id = request.POST.get('bike_id')
    sale_price = request.POST.get('sale_price')
    
    if not bike_id or not sale_price:
        messages.error(request, "Missing product information")
        return redirect('main:home')
    
    try:
        # Get product and user information
        product = get_object_or_404(Product, id=bike_id, status='available')
        buyer = request.user
        
        # Format amount (convert to paisa)
        amount = int(float(sale_price) * 100)
        if amount <= 0:
            messages.error(request, "Invalid product price")
            return redirect('main:home')
        
        # Generate a unique order ID
        purchase_order_id = f"BIKE-{uuid.uuid4()}"
        
        # Check if customer info exists
        try:
            # Get customer info for the buyer
            customer = get_object_or_404(Customer, user=buyer)
            phone = customer.mobile
        except:
            # No customer record, show error
            messages.error(request, "Your profile is incomplete. Please update your profile with contact information.")
            return redirect('main:profile')
        
        # Prepare the return URL
        return_url = request.build_absolute_uri(reverse('main:payment_callback'))
        website_url = request.build_absolute_uri('/')
        
        logger.info(f"Initiating payment for product {product.id} with amount {amount} paisa")
        
        # Prepare payload for Khalti based on KPG-2 documentation
        payload = {
            "return_url": return_url,
            "website_url": website_url,
            "amount": amount,
            "purchase_order_id": purchase_order_id,
            "purchase_order_name": f"Bike: {product.title}",
            "customer_info": {
                "name": buyer.get_full_name() or buyer.username,
                "email": buyer.email,
                "phone": phone
            },
            "product_details": [
                {
                    "identity": str(product.id),
                    "name": product.title,
                    "total_price": amount,
                    "quantity": 1,
                    "unit_price": amount
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
            # Log the payload for debugging
            logger.debug(f"Khalti request payload: {json.dumps(payload)}")
            
            # Use the correct API endpoint based on the Khalti documentation
            khalti_endpoint = "https://khalti.com/api/v2/epayment/initiate/"
            if hasattr(settings, 'KHALTI_DEBUG') and settings.KHALTI_DEBUG:
                khalti_endpoint = "https://dev.khalti.com/api/v2/epayment/initiate/"
                
            response = requests.post(
                khalti_endpoint,
                json=payload,
                headers=headers
            )
            
            # Log the response for debugging
            logger.info(f"Khalti initiate response: {response.status_code}")
            logger.debug(f"Khalti initiate response text: {response.text}")
            
            # Check if the response was successful
            if response.status_code == 200:
                response_data = response.json()
                if 'payment_url' in response_data:
                    # Store product in session for later verification
                    request.session['pending_product_id'] = product.id
                    request.session['pending_purchase_order_id'] = purchase_order_id
                    request.session['pending_pidx'] = response_data['pidx']
                    
                    logger.info(f"Payment initiated with pidx: {response_data['pidx']}")
                    
                    # Update product status to pending
                    product.status = 'pending'
                    product.save()
                    
                    # Redirect to Khalti payment page
                    return redirect(response_data['payment_url'])
                else:
                    logger.error(f"Payment URL not found in response: {response_data}")
                    messages.error(request, "Payment initialization failed (no payment URL)")
                    return redirect('main:product-detail', pk=product.id)
            else:
                # Handle error
                error_msg = "Payment initialization failed"
                try:
                    response_json = response.json()
                    logger.error(f"Khalti error response: {response_json}")
                    if 'detail' in response_json:
                        error_msg = response_json['detail']
                    elif 'error_key' in response_json:
                        error_msg = f"Error: {response_json.get('error_key')}"
                except Exception as json_err:
                    logger.exception(f"Error parsing JSON response: {str(json_err)}")
                
                messages.error(request, error_msg)
                return redirect('main:product-detail', pk=product.id)
                
        except requests.RequestException as e:
            logger.exception(f"Khalti request error: {str(e)}")
            messages.error(request, "Could not connect to payment gateway")
            return redirect('main:product-detail', pk=product.id)
            
    except Exception as e:
        logger.exception(f"Payment initiation error: {str(e)}")
        messages.error(request, "An error occurred while processing your payment")
        return redirect('main:home')

def payment_callback(request):
    """
    Callback endpoint for Khalti payments - handles both success and failure
    """
    # Log all request parameters for debugging
    logger.info(f"Payment callback received: {request.GET}")
    
    # Get parameters from the callback
    pidx = request.GET.get('pidx')
    status = request.GET.get('status')
    transaction_id = request.GET.get('transaction_id') or request.GET.get('txnId')
    amount = request.GET.get('amount')
    mobile = request.GET.get('mobile')
    purchase_order_id = request.GET.get('purchase_order_id')
    
    if not pidx:
        logger.error("No pidx in callback parameters")
        messages.error(request, "Invalid payment callback")
        return redirect('main:home')
    
    # Get the pending product from session
    product_id = request.session.get('pending_product_id')
    session_purchase_order_id = request.session.get('pending_purchase_order_id')
    session_pidx = request.session.get('pending_pidx')
    
    logger.info(f"Session data: product_id={product_id}, purchase_order_id={session_purchase_order_id}, pidx={session_pidx}")
    
    # Clear session data
    if 'pending_product_id' in request.session:
        del request.session['pending_product_id']
    if 'pending_purchase_order_id' in request.session:
        del request.session['pending_purchase_order_id']
    if 'pending_pidx' in request.session:
        del request.session['pending_pidx']
    
    # Verify the pidx matches
    if session_pidx != pidx:
        logger.error(f"Pidx mismatch: session={session_pidx}, callback={pidx}")
        messages.error(request, "Payment verification failed - mismatched transaction ID")
        return redirect('main:home')
    
    try:
        product = get_object_or_404(Product, id=product_id)
        
        # Check status first
        if status == 'Completed' and transaction_id:
            logger.info(f"Payment status: Completed, transaction_id: {transaction_id}")
            
            # Verify with Khalti lookup API
            headers = {
                "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
                "Content-Type": "application/json"
            }
            
            lookup_payload = {"pidx": pidx}
            
            try:
                # Use the correct API endpoint based on the Khalti documentation
                khalti_lookup_endpoint = "https://khalti.com/api/v2/epayment/lookup/"
                if hasattr(settings, 'KHALTI_DEBUG') and settings.KHALTI_DEBUG:
                    khalti_lookup_endpoint = "https://dev.khalti.com/api/v2/epayment/lookup/"
                    
                lookup_response = requests.post(
                    khalti_lookup_endpoint,
                    json=lookup_payload,
                    headers=headers
                )
                
                logger.info(f"Khalti lookup response: {lookup_response.status_code}")
                logger.debug(f"Khalti lookup response text: {lookup_response.text}")
                
                if lookup_response.status_code == 200:
                    lookup_data = lookup_response.json()
                    
                    # Final verification
                    if lookup_data.get('status') == 'Completed':
                        logger.info(f"Payment verified as Completed for pidx: {pidx}")
                        
                        # Payment successful - mark product as sold
                        product.status = 'sold'
                        product.save()
                        
                        # Create a BikePaymentTransaction record
                        try:
                            # Convert amount from paisa to rupees if needed
                            payment_amount = float(amount) / 100 if amount else product.price
                            
                            # Create the transaction record
                            BikePaymentTransaction.objects.create(
                                pidx=pidx,
                                purchase_order_id=purchase_order_id or session_purchase_order_id,
                                product=product,
                                buyer=request.user,
                                amount=payment_amount,
                                status='Completed',
                                transaction_id=transaction_id,
                                payment_method='Khalti'
                            )
                            logger.info(f"Created BikePaymentTransaction record for pidx: {pidx}")
                        except Exception as tx_error:
                            logger.exception(f"Error creating transaction record: {str(tx_error)}")
                        
                        messages.success(request, "Payment successful! The bike is now yours.")
                        return render(request, 'proj/payment_success.html', {
                            'product': product,
                            'transaction_id': purchase_order_id or session_purchase_order_id
                        })
                    else:
                        logger.warning(f"Payment not completed in lookup: {lookup_data.get('status')}")
                        
                        # Payment not completed
                        product.status = 'available'
                        product.save()
                        
                        messages.warning(request, f"Payment status: {lookup_data.get('status')}")
                        return render(request, 'proj/payment_error.html', {
                            'error': f"Payment status: {lookup_data.get('status')}",
                            'product': product
                        })
                else:
                    logger.error(f"Lookup verification failed: {lookup_response.status_code}")
                    
                    # Verification failed
                    product.status = 'available'
                    product.save()
                    
                    messages.error(request, "Payment verification failed")
                    return render(request, 'proj/payment_error.html', {
                        'error': 'Payment verification failed',
                        'product': product
                    })
            
            except Exception as e:
                # API error
                logger.exception(f"Khalti lookup error: {str(e)}")
                
                product.status = 'available'
                product.save()
                
                messages.error(request, "Error verifying payment")
                return render(request, 'proj/payment_error.html', {
                    'error': 'Error verifying payment',
                    'product': product
                })
        
        else:
            logger.info(f"Payment not completed: {status}")
            
            # Payment not completed
            product.status = 'available'
            product.save()
            
            if status == 'User canceled':
                messages.info(request, "Payment was canceled")
                return redirect('main:product-detail', pk=product.id)
            elif status == 'Expired':
                messages.info(request, "Payment session expired")
                return redirect('main:product-detail', pk=product.id)
            else:
                messages.warning(request, f"Payment status: {status}")
                return render(request, 'proj/payment_error.html', {
                    'error': f"Payment status: {status}",
                    'product': product
                })
    
    except Exception as e:
        logger.exception(f"Payment callback error: {str(e)}")
        messages.error(request, "An error occurred while processing your payment")
        return redirect('main:home')

# Add a test view to check Khalti configuration
def test_khalti_config(request):
    """Simple view to test if Khalti is properly configured"""
    return JsonResponse({
        'khalti_public_key': settings.KHALTI_PUBLIC_KEY[:5] + '...',
        'khalti_secret_key': settings.KHALTI_SECRET_KEY[:5] + '...' if settings.KHALTI_SECRET_KEY else 'Not configured',
        'is_debug': getattr(settings, 'KHALTI_DEBUG', False)
    })

def generate_pdf_sales_report(request, transaction_id):
    """
    Generate a PDF sales report for a completed transaction
    """
    # Get the transaction
    transaction = get_object_or_404(BikePaymentTransaction, purchase_order_id=transaction_id)
    
    # Check if user is authorized (either the buyer or staff)
    if request.user != transaction.buyer and not request.user.is_staff:
        return HttpResponse("Unauthorized", status=401)
    
    # Get the related product
    product = transaction.product
    
    # Get buyer profile
    buyer_profile = Customer.objects.filter(user=transaction.buyer).first()
    
    # Prepare context for template
    context = {
        'transaction': transaction,
        'product': product,
        'buyer': transaction.buyer,
        'buyer_profile': buyer_profile,
        'now': timezone.now(),
    }
    
    # Render template
    template = get_template('pdf/sales_report.html')
    html = template.render(context)
    
    # Create PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('UTF-8')), result)
    
    # Return PDF as response
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        filename = f'bike_sales_report_{transaction.purchase_order_id}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    return HttpResponse("Error generating PDF", status=500) 