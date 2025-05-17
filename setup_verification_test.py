#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'summproj.settings')
django.setup()

from proj.models import Product, SellerInfo

def setup_verification_test():
    """
    Set up test verification statuses on products
    """
    print("Setting up test verification statuses...")
    
    # Get all products
    all_products = Product.objects.all()
    print(f"Found {all_products.count()} products")
    
    # Ensure we have at least one product with each verification status
    if all_products.count() < 3:
        print("Not enough products to set up test. Need at least 3 products.")
        return
    
    # Divide products into roughly equal groups
    total = all_products.count()
    approved_count = total // 3
    pending_count = total // 3
    rejected_count = total - approved_count - pending_count
    
    # Make sure we have at least one of each
    approved_count = max(approved_count, 1)
    pending_count = max(pending_count, 1)
    rejected_count = max(rejected_count, 1)
    
    print(f"Setting up {approved_count} approved, {pending_count} pending, and {rejected_count} rejected products")
    
    # Update products
    i = 0
    for i, product in enumerate(all_products):
        if i < approved_count:
            status = 'approved'
            product_status = 'available'
        elif i < approved_count + pending_count:
            status = 'pending'
            product_status = 'pending'
        else:
            status = 'rejected'
            product_status = 'pending'
        
        # Update the product
        product.verification_status = status
        product.status = product_status
        product.save()
        
        # Update any associated SellerInfo
        seller_infos = SellerInfo.objects.filter(product=product)
        for seller_info in seller_infos:
            if status == 'approved':
                seller_info.verification_status = 'verified'
            elif status == 'rejected':
                seller_info.verification_status = 'rejected'
            else:
                seller_info.verification_status = 'pending'
            
            if product_status == 'available':
                seller_info.status = 'active'
            elif product_status == 'sold':
                seller_info.status = 'completed'
            else:
                seller_info.status = 'pending'
                
            seller_info.save()
    
    # Verify the results
    approved = Product.objects.filter(verification_status='approved').count()
    pending = Product.objects.filter(verification_status='pending').count()
    rejected = Product.objects.filter(verification_status='rejected').count()
    
    print(f"Results: {approved} approved, {pending} pending, {rejected} rejected")
    
    # Get few example products for each status
    print("\nExample approved products (should appear on Buy page):")
    for p in Product.objects.filter(verification_status='approved')[:3]:
        print(f"ID: {p.id}, Title: {p.title}, Status: {p.status}, Verification: {p.verification_status}")
    
    print("\nExample pending products (should NOT appear on Buy page):")
    for p in Product.objects.filter(verification_status='pending')[:3]:
        print(f"ID: {p.id}, Title: {p.title}, Status: {p.status}, Verification: {p.verification_status}")
    
    print("\nExample rejected products (should NOT appear on Buy page):")
    for p in Product.objects.filter(verification_status='rejected')[:3]:
        print(f"ID: {p.id}, Title: {p.title}, Status: {p.status}, Verification: {p.verification_status}")

if __name__ == "__main__":
    setup_verification_test() 