#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'summproj.settings')
django.setup()

from proj.models import Product, SellerInfo

def update_product_verification_status():
    print("Updating product verification status...")
    
    # Get all products
    products = Product.objects.all()
    print(f"Total products: {products.count()}")
    
    # Count initial statuses
    pending_count = products.filter(verification_status='pending').count()
    approved_count = products.filter(verification_status='approved').count()
    rejected_count = products.filter(verification_status='rejected').count()
    empty_count = products.filter(verification_status='').count()
    null_count = products.filter(verification_status__isnull=True).count()
    
    print(f"Initial status counts:")
    print(f"- Pending: {pending_count}")
    print(f"- Approved: {approved_count}")
    print(f"- Rejected: {rejected_count}")
    print(f"- Empty: {empty_count}")
    print(f"- Null: {null_count}")
    
    # Update any products with empty or null verification_status to 'pending'
    updated_products = 0
    for product in products:
        if not product.verification_status or product.verification_status == '':
            product.verification_status = 'pending'
            product.save()
            updated_products += 1
            
            # If the product is linked to a seller info, sync the status
            seller_infos = SellerInfo.objects.filter(product=product)
            for seller_info in seller_infos:
                if seller_info.verification_status != 'verified':
                    seller_info.verification_status = 'pending'
                    seller_info.save()
    
    print(f"Updated {updated_products} products to 'pending' status")
    
    # Count final statuses
    pending_count = products.filter(verification_status='pending').count()
    approved_count = products.filter(verification_status='approved').count()
    rejected_count = products.filter(verification_status='rejected').count()
    
    print(f"Final status counts:")
    print(f"- Pending: {pending_count}")
    print(f"- Approved: {approved_count}")
    print(f"- Rejected: {rejected_count}")
    
    print("Verification status update completed.")

if __name__ == "__main__":
    update_product_verification_status() 