import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'summproj.settings')
django.setup()

from proj.models import Product
from django.db.models import Count
import random
import string

def generate_unique_suffix():
    """Generate a random string to make values unique"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

def fix_duplicate_fields():
    print("Checking for duplicate engine numbers...")
    # Find duplicates for engine_number
    duplicates = Product.objects.values('engine_number')\
                .annotate(count=Count('id'))\
                .filter(count__gt=1)\
                .exclude(engine_number__isnull=True)\
                .exclude(engine_number='')
    
    for dup in duplicates:
        engine_number = dup['engine_number']
        print(f"Found duplicate engine number: {engine_number}")
        
        # Get all products with this engine number except the first one
        products = Product.objects.filter(engine_number=engine_number)[1:]
        
        # Update each product with a unique engine number
        for product in products:
            new_value = f"{engine_number}-{generate_unique_suffix()}"
            print(f"Updating product {product.id} engine number to {new_value}")
            product.engine_number = new_value
            product.save(update_fields=['engine_number'])
    
    print("\nChecking for duplicate chassis numbers...")
    # Find duplicates for chassis_number
    duplicates = Product.objects.values('chassis_number')\
                .annotate(count=Count('id'))\
                .filter(count__gt=1)\
                .exclude(chassis_number__isnull=True)\
                .exclude(chassis_number='')
    
    for dup in duplicates:
        chassis_number = dup['chassis_number']
        print(f"Found duplicate chassis number: {chassis_number}")
        
        # Get all products with this chassis number except the first one
        products = Product.objects.filter(chassis_number=chassis_number)[1:]
        
        # Update each product with a unique chassis number
        for product in products:
            new_value = f"{chassis_number}-{generate_unique_suffix()}"
            print(f"Updating product {product.id} chassis number to {new_value}")
            product.chassis_number = new_value
            product.save(update_fields=['chassis_number'])
    
    print("\nChecking for duplicate number plates...")
    # Find duplicates for number_plate
    duplicates = Product.objects.values('number_plate')\
                .annotate(count=Count('id'))\
                .filter(count__gt=1)\
                .exclude(number_plate__isnull=True)\
                .exclude(number_plate='')
    
    for dup in duplicates:
        number_plate = dup['number_plate']
        print(f"Found duplicate number plate: {number_plate}")
        
        # Get all products with this number plate except the first one
        products = Product.objects.filter(number_plate=number_plate)[1:]
        
        # Update each product with a unique number plate
        for product in products:
            new_value = f"{number_plate}-{generate_unique_suffix()}"
            print(f"Updating product {product.id} number plate to {new_value}")
            product.number_plate = new_value
            product.save(update_fields=['number_plate'])
    
    print("\nAll duplicates have been fixed!")

if __name__ == "__main__":
    fix_duplicate_fields()
