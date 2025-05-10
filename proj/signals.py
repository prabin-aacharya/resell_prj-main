from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import BikePaymentTransaction

@receiver(post_save, sender=BikePaymentTransaction)
def notify_payment_status(sender, instance, created, **kwargs):
    """Send email notifications when a payment is completed"""
    if not created and instance.status == 'Completed':
        # Notify buyer
        send_mail(
            'Payment Successful for Bike Purchase',
            f'''Dear {instance.buyer.get_full_name() or instance.buyer.username},

Your payment of Rs. {instance.amount/100:.2f} for {instance.product.title} was successful!

Transaction Details:
- Product: {instance.product.title} ({instance.product.brand})
- Transaction ID: {instance.purchase_order_id}
- Date: {instance.updated_at.strftime('%d %b %Y, %H:%M')}

Please contact the seller to arrange pickup/delivery.

Thank you for using our platform!
Bike Resell Team
            ''',
            settings.DEFAULT_FROM_EMAIL,
            [instance.buyer.email],
            fail_silently=True,
        )
        
        # Notify seller
        send_mail(
            'Your Bike Has Been Sold!',
            f'''Dear {instance.seller.get_full_name() or instance.seller.username},

Great news! Your bike {instance.product.title} has been sold to {instance.buyer.get_full_name() or instance.buyer.username} for Rs. {instance.amount/100:.2f}.

Transaction Details:
- Product: {instance.product.title} ({instance.product.brand})
- Transaction ID: {instance.purchase_order_id}
- Date: {instance.updated_at.strftime('%d %b %Y, %H:%M')}

Please contact the buyer to arrange pickup/delivery.

Thank you for using our platform!
Bike Resell Team
            ''',
            settings.DEFAULT_FROM_EMAIL,
            [instance.seller.email],
            fail_silently=True,
        ) 