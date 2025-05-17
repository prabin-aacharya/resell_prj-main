import os
import django
import sys

print("Script started")

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "summproj.settings")
print("Django settings module set")

try:
    django.setup()
    print("Django setup completed")
except Exception as e:
    print(f"Error during django.setup(): {e}")
    sys.exit(1)

try:
    from proj.models import Product, SellerInfo
    print("Models imported successfully")
except Exception as e:
    print(f"Error importing models: {e}")
    sys.exit(1)

def update_product_statuses():
    """
    Update all existing products to have a verification status
    - Products with status='available' get verification_status='approved'
    - Products with other statuses get verification_status='pending'
    """
    print("Updating product verification statuses...")
    
    try:
        # Get all products
        total_products = Product.objects.all().count()
        print(f"Total products found: {total_products}")
        
        # Check if verification_status field exists
        print("Checking field names in Product model:")
        print([f.name for f in Product._meta.get_fields()])
        
        # Update all available products to be approved
        available_products = Product.objects.filter(status='available')
        print(f"Available products found: {available_products.count()}")
        
        # Update products with pending verification status
        pending_products = available_products.filter(verification_status='pending')
        count1 = pending_products.update(verification_status='approved')
        print(f"Updated {count1} available products to 'approved'")
        
        # Update all SellerInfo objects related to available products
        seller_count1 = 0
        for product in pending_products:
            seller_info = SellerInfo.objects.filter(product=product).first()
            if seller_info:
                seller_info.verification_status = 'verified'
                seller_info.save()
                seller_count1 += 1
        print(f"Updated {seller_count1} seller info records to 'verified'")
        
        # Update count of products in different states
        total = Product.objects.count()
        approved = Product.objects.filter(verification_status='approved').count()
        pending = Product.objects.filter(verification_status='pending').count()
        rejected = Product.objects.filter(verification_status='rejected').count()
        
        print("\nProduct status summary:")
        print(f"Total products: {total}")
        print(f"Approved: {approved}")
        print(f"Pending: {pending}")
        print(f"Rejected: {rejected}")
    
    except Exception as e:
        print(f"Error updating products: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Running main function")
    update_product_statuses()
    print("Script completed") 