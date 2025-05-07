from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator


# Create your models here.
BRAND_CHOICES=(
    ('HONDA','Honda'),
    ('YAMAHA','Yamaha'),
    ('BAJAJ','Bajaj'),
    ('HERO','Hero'),
    ('TVS','TVS'),
    

)

STATE_CHOICES = (
    ('Koshi', 'Koshi'),
    ('Madhesh', 'Madhesh'),  # Corrected spelling
    ('Bagmati', 'Bagmati'),
    ('Gandaki', 'Gandaki'),
    ('Lumbini', 'Lumbini'),
    ('Karnali', 'Karnali'),
    ('Sudurpashchim', 'Sudurpashchim'),  # Corrected spelling
)

class Product(models.Model):
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Better for currency
    description = models.TextField()
    condition = models.TextField()
    made_year = models.IntegerField()  # Year as integer
    kilometers = models.IntegerField()  # Whole number for kilometers
    engine_size = models.IntegerField()  # Whole number for engine size (e.g., 1500 for 1.5L)
    brand = models.CharField(choices=BRAND_CHOICES, max_length=20)
    location = models.TextField()
    seller_name = models.TextField()
    product_image = models.ImageField(upload_to='product')
    bluebook_page2 = models.ImageField(upload_to='bluebook', null=True, blank=True)
    bluebook_page9 = models.ImageField(upload_to='bluebook', null=True, blank=True)
    
    def __str__(self):
        return self.title

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

class SellerInfo(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    bike_brand = models.CharField(choices=BRAND_CHOICES, max_length=20, default='HONDA')
    bike_model = models.CharField(max_length=100, default='Unknown Model')
    bike_photo = models.BinaryField(null=True, blank=True)
    bluebook_page2 = models.BinaryField(null=True, blank=True)
    bluebook_page9 = models.BinaryField(null=True, blank=True)
    # Optionally, link to Product if you want
    product = models.OneToOneField('Product', on_delete=models.CASCADE, related_name='seller_info')



