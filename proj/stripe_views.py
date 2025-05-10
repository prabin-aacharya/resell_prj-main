import json
import stripe
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User

from .models import Product, BikePaymentTransaction, Customer
import uuid

# Configure Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)

@login_required
def initiate_stripe_payment(request):
    """
    Initiates a payment with Stripe for a bike purchase
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
        
        # Get seller info
        seller = get_object_or_404(User, username=product.seller_name)
        
        # Format amount (convert to cents for Stripe)
        amount = int(float(sale_price) * 100)
        if amount <= 0:
            messages.error(request, "Invalid product price")
            return redirect('main:home')
        
        # Generate a unique order ID
        purchase_order_id = f"BIKE-{uuid.uuid4()}"
        
        # Get customer info for the buyer
        customer = get_object_or_404(Customer, user=buyer)
        
        # Create a Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',  # Change as needed for your currency
                        'product_data': {
                            'name': product.title,
                            'description': product.description[:100],  # Truncate description
                        },
                        'unit_amount': amount,
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=request.build_absolute_uri(
                reverse('main:stripe_success') + f'?session_id={{CHECKOUT_SESSION_ID}}&order_id={purchase_order_id}'
            ),
            cancel_url=request.build_absolute_uri(reverse('main:stripe_cancel')),
            client_reference_id=purchase_order_id,
            customer_email=buyer.email,
            metadata={
                'product_id': product.id,
                'buyer_id': buyer.id,
                'seller_id': seller.id,
            }
        )
        
        # Store transaction details
        transaction = BikePaymentTransaction.objects.create(
            pidx=checkout_session.id,
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
        
        # Redirect to Stripe payment page
        return redirect(checkout_session.url)
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        messages.error(request, "Payment processing error")
        return redirect('main:payment_error', error="Stripe payment processing error")
        
    except Exception as e:
        logger.error(f"Payment initiation error: {str(e)}")
        messages.error(request, "An error occurred while processing your payment")
        return redirect('main:payment_error', error="General error")

@csrf_exempt
def stripe_webhook(request):
    """
    Handles Stripe webhooks for payment events
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_ENDPOINT_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)
    
    return HttpResponse(status=200)

def handle_successful_payment(session):
    """
    Processes a successful payment from Stripe
    """
    try:
        # Find the transaction by session ID (pidx)
        transaction = BikePaymentTransaction.objects.get(pidx=session.id)
        
        # Update transaction status
        transaction.status = 'Completed'
        transaction.save()
        
        # Update product status
        product = transaction.product
        product.status = 'sold'
        product.save()
        
        logger.info(f"Payment completed successfully for transaction {transaction.purchase_order_id}")
    except BikePaymentTransaction.DoesNotExist:
        logger.error(f"Transaction not found for session ID: {session.id}")
    except Exception as e:
        logger.error(f"Error processing successful payment: {str(e)}")

@login_required
def stripe_success(request):
    """
    Handles successful payment return from Stripe
    """
    session_id = request.GET.get('session_id')
    order_id = request.GET.get('order_id')
    
    if not session_id or not order_id:
        messages.error(request, "Missing transaction information")
        return redirect('main:payment_error', error="Invalid transaction")
    
    try:
        # Verify the transaction
        transaction = get_object_or_404(
            BikePaymentTransaction, 
            pidx=session_id,
            purchase_order_id=order_id
        )
        
        # Retrieve the session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Check if payment was successful
        if session.payment_status == 'paid':
            # Update transaction status if not already done by webhook
            if transaction.status != 'Completed':
                transaction.status = 'Completed'
                transaction.save()
                
                # Update product status
                product = transaction.product
                product.status = 'sold'
                product.save()
            
            messages.success(request, "Payment successful! Your bike purchase is complete.")
            return render(request, 'payment_success.html', {'transaction': transaction})
        else:
            transaction.status = 'Failed'
            transaction.save()
            messages.error(request, "Payment verification failed")
            return render(request, 'payment_error.html', {'error': 'Payment verification failed'})
            
    except Exception as e:
        logger.error(f"Payment verification error: {str(e)}")
        messages.error(request, "An error occurred while verifying your payment")
        return render(request, 'payment_error.html', {'error': 'Verification error'})

@login_required
def stripe_cancel(request):
    """
    Handles cancelled payment from Stripe
    """
    messages.warning(request, "Payment was cancelled")
    return render(request, 'payment_error.html', {'error': 'Payment was cancelled'}) 