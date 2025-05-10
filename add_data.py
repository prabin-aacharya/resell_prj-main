import os
import django
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "summproj.settings")
django.setup()

from proj.models import Product
from django.utils import timezone

# Check if we have any products
if Product.objects.count() == 0:
    # Add sample products
    products = [
        {
            'title': 'Honda CBR 150R',
            'price': 275000,
            'description': 'Well maintained Honda CBR 150R with low mileage. Perfect sports bike for enthusiasts.',
            'condition': 'Good',
            'made_year': 2020,
            'kilometers': 12000,
            'engine_size': '150cc',
            'brand': 'HONDA',
            'location': 'Kathmandu',
            'seller_name': 'Raj Kumar',
            'status': 'available'
        },
        {
            'title': 'Yamaha FZ-S V3',
            'price': 215000,
            'description': 'Stylish Yamaha FZ-S with great fuel efficiency and smooth performance.',
            'condition': 'Excellent',
            'made_year': 2021,
            'kilometers': 8500,
            'engine_size': '149cc',
            'brand': 'YAMAHA',
            'location': 'Pokhara',
            'seller_name': 'Amit Sharma',
            'status': 'available'
        },
        {
            'title': 'Bajaj Pulsar NS200',
            'price': 295000,
            'description': 'Powerful Pulsar NS200 with ABS. Great condition and regularly serviced.',
            'condition': 'Like New',
            'made_year': 2022,
            'kilometers': 5000,
            'engine_size': '200cc',
            'brand': 'BAJAJ',
            'location': 'Lalitpur',
            'seller_name': 'Sunil Thapa',
            'status': 'available'
        },
        {
            'title': 'TVS Apache RTR 160',
            'price': 190000,
            'description': 'TVS Apache with good mileage and excellent performance. Single owner.',
            'condition': 'Good',
            'made_year': 2019,
            'kilometers': 20000,
            'engine_size': '160cc',
            'brand': 'TVS',
            'location': 'Bhaktapur',
            'seller_name': 'Krishna Shrestha',
            'status': 'sold'
        },
        {
            'title': 'Hero Xpulse 200',
            'price': 320000,
            'description': 'Adventure ready Hero Xpulse with all terrain capability. Perfect for off-road enthusiasts.',
            'condition': 'Excellent',
            'made_year': 2022,
            'kilometers': 7500,
            'engine_size': '200cc',
            'brand': 'HERO',
            'location': 'Kathmandu',
            'seller_name': 'Binod Gurung',
            'status': 'available'
        }
    ]
    
    for product_data in products:
        # Create product without image fields first
        product = Product.objects.create(
            title=product_data['title'],
            price=product_data['price'],
            description=product_data['description'],
            condition=product_data['condition'],
            made_year=product_data['made_year'],
            kilometers=product_data['kilometers'],
            engine_size=product_data['engine_size'],
            brand=product_data['brand'],
            location=product_data['location'],
            seller_name=product_data['seller_name'],
            created_at=timezone.now(),
            product_image='product_images/placeholder.jpg',  # Default placeholder
            status=product_data['status']
        )
        print(f"Created product: {product.title}")
    
    print(f"Added {len(products)} sample products to the database")
else:
    print(f"Database already has {Product.objects.count()} products. No sample data added.") 