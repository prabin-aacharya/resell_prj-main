#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'summproj.settings')
django.setup()

from django.contrib.auth.models import User
from proj.models import Product, SellerInfo
from django.urls import reverse, NoReverseMatch

def debug_my_deals_page():
    """Debug the My Deals page permissions for a user"""
    # You need to specify a user email that exists in your system
    user_email = input("Enter a user email to check: ")
    
    try:
        # Get the user
        user = User.objects.get(email=user_email)
        print(f"Found user: {user.username} ({user.email})")
        
        # 1. Check for seller info records associated with this user
        seller_infos = SellerInfo.objects.filter(email=user.email).order_by('-created_at')
        print(f"\nFound {seller_infos.count()} seller info records for this user")
        
        # Display all seller infos and their associated products
        for i, seller_info in enumerate(seller_infos, 1):
            print(f"\n--- Seller Info #{i} ---")
            print(f"ID: {seller_info.id}")
            print(f"Name: {seller_info.full_name}")
            print(f"Email: {seller_info.email}")
            print(f"Phone: {seller_info.phone}")
            print(f"Bike Brand: {seller_info.bike_brand}")
            print(f"Bike Model: {seller_info.bike_model}")
            print(f"Status: {seller_info.status}")
            print(f"Verification Status: {seller_info.verification_status}")
            
            if seller_info.product:
                print("\nAssociated Product:")
                print(f"ID: {seller_info.product.id}")
                print(f"Title: {seller_info.product.title}")
                print(f"Status: {seller_info.product.status}")
                print(f"Verification Status: {seller_info.product.verification_status}")
                
                # Check if we can access this product for editing
                try:
                    product = Product.objects.get(pk=seller_info.product.id)
                    # Check if the seller_info is correctly linked to this user's email
                    check_seller_info = SellerInfo.objects.filter(product=product, email=user.email).first()
                    if check_seller_info:
                        print("✓ User has permission to edit this product")
                        
                        # Check if product is sold (which means it can't be edited)
                        if product.status == 'sold':
                            print("✗ Product is sold, so it can't be edited")
                        else:
                            print("✓ Product is not sold, so it can be edited")
                            
                        # Check URL resolution
                        try:
                            update_url = reverse('main:update_product', args=[product.id])
                            print(f"✓ Update URL resolves: {update_url}")
                        except NoReverseMatch:
                            print("✗ Cannot resolve 'main:update_product' URL")
                            
                        try:
                            delete_url = reverse('main:delete_product', args=[product.id])
                            print(f"✓ Delete URL resolves: {delete_url}")
                        except NoReverseMatch:
                            print("✗ Cannot resolve 'main:delete_product' URL")
                    else:
                        print("✗ Permission error: seller_info email doesn't match user email")
                except Product.DoesNotExist:
                    print("✗ Product does not exist in database")
            else:
                print("✗ No product associated with this seller info")
        
        # Check if URL patterns resolve
        print("\n----- Testing URL resolution -----")
        example_id = 1
        
        try:
            update_url = reverse('main:update_product', args=[example_id])
            print(f"✓ Update URL pattern 'main:update_product' resolves to: {update_url}")
        except NoReverseMatch:
            print("✗ URL pattern 'main:update_product' does not resolve")
        
        try:
            delete_url = reverse('main:delete_product', args=[example_id])
            print(f"✓ Delete URL pattern 'main:delete_product' resolves to: {delete_url}")
        except NoReverseMatch:
            print("✗ URL pattern 'main:delete_product' does not resolve")
        
        # 2. Simulate the my_deals view logic 
        from proj.views import my_deals
        from django.http import HttpRequest
        
        print("\n----- Simulating my_deals view logic -----")
        listed_bikes = []
        
        try:
            # Find all SellerInfo records that match the user's email
            print(f"Looking for seller infos with email: {user.email}")
            seller_infos = SellerInfo.objects.filter(email=user.email).order_by('-created_at')
            print(f"Found {seller_infos.count()} seller info records")
            
            # For each SellerInfo, get the associated product
            for seller_info in seller_infos:
                if seller_info.product:
                    # Add verification status info for the UI
                    verification_status = seller_info.product.verification_status
                    verification_badge = ""
                    
                    if verification_status == 'pending':
                        verification_badge = '<span class="badge bg-warning text-dark">Pending Verification</span>'
                    elif verification_status == 'approved':
                        verification_badge = '<span class="badge bg-success">Verified</span>'
                    elif verification_status == 'rejected':
                        verification_badge = '<span class="badge bg-danger">Rejected</span>'
                    
                    # Add status info for the UI
                    status = seller_info.product.status
                    status_badge = ""
                    
                    if status == 'available':
                        status_badge = '<span class="badge bg-success">Available</span>'
                    elif status == 'sold':
                        status_badge = '<span class="badge bg-primary">Sold</span>'
                    elif status == 'pending':
                        status_badge = '<span class="badge bg-warning text-dark">Pending</span>'
                    elif status == 'reserved':
                        status_badge = '<span class="badge bg-info">Reserved</span>'
                    
                    listed_bikes.append({
                        'seller_info': seller_info,
                        'product': seller_info.product,
                        'is_active': seller_info.product.status == 'available',
                        'status': seller_info.product.status,
                        'verification_status': verification_status,
                        'verification_badge': verification_badge,
                        'status_badge': status_badge
                    })
                    print(f"Added product ID {seller_info.product.id} to listed_bikes")
                else:
                    print(f"Seller info ID {seller_info.id} has no associated product")
        
        except Exception as e:
            print(f"Error retrieving listed bikes: {str(e)}")
        
        # Print summary of listed_bikes
        print(f"\nTotal listed_bikes: {len(listed_bikes)}")
        for i, item in enumerate(listed_bikes, 1):
            print(f"\nListed Bike #{i}:")
            print(f"Product ID: {item['product'].id}")
            print(f"Title: {item['product'].title}")
            print(f"Status: {item['status']}")
            print(f"Verification: {item['verification_status']}")
            
            # Check if the edit/delete buttons would show
            if item['status'] != 'sold':
                print("✓ Edit/Delete buttons should be visible")
                try:
                    update_url = reverse('main:update_product', args=[item['product'].id])
                    print(f"  Edit URL resolves to: {update_url}")
                except NoReverseMatch:
                    print("  ✗ Edit URL doesn't resolve")
                    
                try:
                    delete_url = reverse('main:delete_product', args=[item['product'].id])
                    print(f"  Delete URL resolves to: {delete_url}")
                except NoReverseMatch:
                    print("  ✗ Delete URL doesn't resolve")
            else:
                print("✗ Edit/Delete buttons should NOT be visible (item is sold)")
        
    except User.DoesNotExist:
        print(f"No user found with email: {user_email}")
        
if __name__ == "__main__":
    debug_my_deals_page() 