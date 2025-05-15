from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator, MinLengthValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


# Create your models here.
BRAND_CHOICES=(
    ('HONDA','Honda'),
    ('YAMAHA','Yamaha'),
    ('BAJAJ','Bajaj'),
    ('HERO','Hero'),
    ('TVS','TVS'),
    

)

STATE_CHOICES = (
    ('', 'Select Province'),
    ('Koshi Province', 'Koshi'),
    ('Madhesh Province', 'Madhesh'),
    ('Bagmati Province', 'Bagmati'),
    ('Gandaki Province', 'Gandaki'),
    ('Lumbini Province', 'Lumbini'),
    ('Karnali Province', 'Karnali'),
    ('Sudurpashchim Province', 'Sudurpashchim'),  # Corrected spelling
)

GENDER_CHOICES = (
    ('', 'Select Gender'),
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
)

def bluebook_upload_path(instance, filename):
    # Get a safe version of the seller name for the folder name
    safe_name = instance.seller_name.replace(' ', '_').lower()
    # Return the complete path including the owner's name
    return f'bluebook/{safe_name}/{filename}'

class Product(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('pending', 'Pending'),
        ('reserved', 'Reserved'),
    )
    
    CONDITION_CHOICES = (
        ('New', 'New'),
        ('Like New', 'Like New'),
        ('Excellent', 'Excellent'),
        ('Good', 'Good'),
        ('Fair', 'Fair'),
        ('Poor', 'Poor'),
    )
    
    title = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    made_year = models.IntegerField()
    kilometers = models.IntegerField()
    engine_size = models.CharField(max_length=50)
    brand = models.CharField(max_length=50)
    location = models.CharField(max_length=100)
    seller_name = models.CharField(max_length=100)
    product_image = models.ImageField(upload_to='product_images/')
    bluebook_page2 = models.ImageField(upload_to='bluebook_images/', null=True, blank=True)
    bluebook_page9 = models.ImageField(upload_to='bluebook_images/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    def __str__(self):
        return self.title
        
    class Meta:
        ordering = ['-created_at']

class Customer(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='customers'  # Added for better querying
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Full Name'
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default='',
        verbose_name='Gender'
    )
    city = models.CharField(
        max_length=50,
        verbose_name='City'
    )
    state = models.CharField(
        choices=STATE_CHOICES,
        max_length=100,
        verbose_name='Province'
    )
    mobile = models.CharField(  # Changed to CharField
        max_length=10,
        validators=[MinLengthValidator(10)],  # For 10-digit numbers
        verbose_name='Mobile Number'
    )
    zipcode = models.CharField(  # Changed to CharField
        max_length=10,
        verbose_name='Postal Code'
    )

    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.city}, {self.state})"

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'product')
    
    def __str__(self):
        return f"{self.user.username}'s wishlist - {self.product.title}"

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Order {self.id} - {self.customer.name}"

class SellerInfo(models.Model):
    STATUS_CHOICES = (
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    )
    
    VERIFICATION_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )
    
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    bike_brand = models.CharField(max_length=50)
    bike_model = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.full_name

class BikePaymentTransaction(models.Model):
    """Track bike payments and purchases"""
    STATUS_CHOICES = [
        ('Initiated', 'Initiated'),
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]
    
    pidx = models.CharField(max_length=100, unique=True)
    purchase_order_id = models.CharField(max_length=100, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bike_purchases')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Initiated')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, default="Khalti", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Bike Payment"
        verbose_name_plural = "Bike Payments"

    def __str__(self):
        return f"{self.product.title} - {self.buyer.username} - {self.status}"

    @property
    def amount_in_paisa(self):
        """Returns amount in paisa for Khalti"""
        return int(self.amount * 100)
    
    @property
    def amount_display(self):
        """Returns formatted amount for display"""
        return f"Rs. {self.amount}"

# Signal handlers to keep SellerInfo in sync with Customer profile updates
@receiver(post_save, sender=Customer)
def update_seller_info_on_customer_update(sender, instance, **kwargs):
    """
    When a Customer profile is updated, update all related SellerInfo records
    that match the customer's email or phone number.
    """
    # Find all SellerInfo records with matching email
    if instance.user and instance.user.email:
        seller_infos_by_email = SellerInfo.objects.filter(email=instance.user.email)
        for seller_info in seller_infos_by_email:
            # Update the phone number if it's not already set
            if not seller_info.phone or seller_info.phone == '':
                seller_info.phone = instance.mobile
                seller_info.save()
    
    # Find all SellerInfo records with matching phone
    if instance.mobile:
        seller_infos_by_phone = SellerInfo.objects.filter(phone=instance.mobile)
        for seller_info in seller_infos_by_phone:
            # Update the email if it's not already set
            if (not seller_info.email or seller_info.email == '') and instance.user and instance.user.email:
                seller_info.email = instance.user.email
                seller_info.save()

