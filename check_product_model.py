#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'summproj.settings')
django.setup()

from proj.models import Product
from django.db import connection

def inspect_product_model():
    # Get all field names from the Product model
    fields = [field.name for field in Product._meta.get_fields()]
    print(f"Product model fields: {fields}")
    
    # Check if verification_status is in the fields
    if 'verification_status' in fields:
        print("✓ verification_status field exists in Product model")
        
        # Get the choices for verification_status
        verification_choices = Product._meta.get_field('verification_status').choices
        print(f"Verification status choices: {verification_choices}")
        
        # Check the database schema for this field
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(proj_product)")
            columns = cursor.fetchall()
            
            for column in columns:
                if column[1] == 'verification_status':
                    print(f"✓ verification_status column exists in database: {column}")
                    break
            else:
                print("✗ verification_status column not found in database!")
    else:
        print("✗ verification_status field does not exist in Product model!")
    
    # Count products by verification status
    total = Product.objects.count()
    pending = Product.objects.filter(verification_status='pending').count()
    approved = Product.objects.filter(verification_status='approved').count()
    rejected = Product.objects.filter(verification_status='rejected').count()
    
    print(f"\nProduct counts by verification status:")
    print(f"Total: {total}")
    print(f"Pending: {pending} ({pending/total*100:.1f}%)")
    print(f"Approved: {approved} ({approved/total*100:.1f}%)")
    print(f"Rejected: {rejected} ({rejected/total*100:.1f}%)")
    
    # List a few products with their verification status
    print("\nSample products:")
    for product in Product.objects.all()[:5]:
        print(f"ID: {product.id}, Title: {product.title}, Status: {product.status}, Verification: {product.verification_status}")

if __name__ == "__main__":
    inspect_product_model() 