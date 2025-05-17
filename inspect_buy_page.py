#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'summproj.settings')
django.setup()

from proj.models import Product

def inspect_buy_page():
    print("Examining products that should appear on Buy page:")
    
    # Get products that should be on Buy page: approved verification status
    approved_products = Product.objects.filter(verification_status='approved')
    print(f"Total products with approved verification status: {approved_products.count()}")
    
    if approved_products.exists():
        print("\nApproved Products (should appear on Buy page):")
        for product in approved_products:
            print(f"ID: {product.id}, Title: {product.title}, Status: {product.status}, Verification: {product.verification_status}")
    else:
        print("No approved products found!")
    
    # Get products that should NOT be on Buy page: pending verification status
    pending_products = Product.objects.filter(verification_status='pending')
    print(f"\nTotal products with pending verification status: {pending_products.count()}")
    
    if pending_products.exists():
        print("\nPending Products (should NOT appear on Buy page):")
        for product in pending_products[:5]:  # Show first 5 if there are many
            print(f"ID: {product.id}, Title: {product.title}, Status: {product.status}, Verification: {product.verification_status}")
        if pending_products.count() > 5:
            print(f"...and {pending_products.count() - 5} more")
    
    # Get products that should NOT be on Buy page: rejected verification status
    rejected_products = Product.objects.filter(verification_status='rejected')
    print(f"\nTotal products with rejected verification status: {rejected_products.count()}")
    
    if rejected_products.exists():
        print("\nRejected Products (should NOT appear on Buy page):")
        for product in rejected_products:
            print(f"ID: {product.id}, Title: {product.title}, Status: {product.status}, Verification: {product.verification_status}")
    
    # Check for ambiguous cases - important edge cases
    sold_approved = Product.objects.filter(status='sold', verification_status='approved').count()
    available_pending = Product.objects.filter(status='available', verification_status='pending').count()
    
    print(f"\nEdge Cases:")
    print(f"Products with status=sold, verification=approved: {sold_approved}")
    print(f"Products with status=available, verification=pending: {available_pending}")
    
    # Check what's actually used in the Buy page
    from proj.views import buy_bikes
    from django.http import HttpRequest
    from django.contrib.auth.models import AnonymousUser
    
    print("\nSimulating the buy_bikes view logic:")
    request = HttpRequest()
    request.user = AnonymousUser()
    request.GET = {}
    request.method = 'GET'
    
    # Extract the query logic from buy_bikes function
    bikes = Product.objects.filter(verification_status='approved')
    print(f"Products retrieved by buy_bikes filter: {bikes.count()}")

if __name__ == "__main__":
    inspect_buy_page() 