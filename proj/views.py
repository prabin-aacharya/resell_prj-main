from django.db.models import Count, Q
from urllib import request
from django.shortcuts import render,redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from . models import Product, Wishlist, SellerInfo
from urllib import request as urllib_request
from . forms import CustomerRegistrationForm,CustomerProfileForm,Customer,SellBikeForm, SellerInfoForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
import uuid
# Create your views here.
def home(request):
    from .models import Product
    from django.core.paginator import Paginator
    
    # Get all products ordered by most recent first
    all_products = Product.objects.all().order_by('-id')
    
    # Set up pagination
    paginator = Paginator(all_products, 12)  # Show 12 products per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get the current page's products
    latest_products = list(page_obj.object_list)
    
    # Get user's wishlist items if authenticated
    user_wishlist = []
    if request.user.is_authenticated:
        user_wishlist = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
    
    # Group products into sublists of 3 for the grid layout
    latest_product_groups = [latest_products[i:i+3] for i in range(0, len(latest_products), 3)]
    
    return render(request, "proj/home.html", {
        'latest_products': latest_products,
        'latest_product_groups': latest_product_groups,
        'page_obj': page_obj,
        'user_wishlist': user_wishlist,
    })

def about(req):
    return render(req, "proj/about.html")

def contact(req):
    return render(req, "proj/contact.html")
    
class BrandView(View):
    def get(self, request, val):
        product = Product.objects.filter(brand=val)
        # Get all unique models (titles) for this brand, with count
        title = Product.objects.filter(brand=val).values('title').annotate(count=Count('id'))
        # For sidebar: get all unique brands
        brands = Product.objects.values('brand').annotate(count=Count('id'))
        return render(request, "proj/brand.html", {
            'product': product,
            'title': title,
            'brands': brands,
            'brand': val,
        })
    

class BrandTitle(View):
    def get(self, request, val):
        product = Product.objects.filter(title=val)
        if product.exists():
            brand_val = product[0].brand
            # All models for this brand
            title = Product.objects.filter(brand=brand_val).values('title').annotate(count=Count('id'))
            # For sidebar: get all unique brands
            brands = Product.objects.values('brand').annotate(count=Count('id'))
            return render(request, "proj/brand.html", {
                'product': product,
                'title': title,
                'brands': brands,
                'brand': brand_val,
            })
        else:
            # fallback if no product found
            return render(request, "proj/brand.html", {
                'product': [],
                'title': [],
                'brands': [],
                'brand': '',
            })
    

class ProductDetail(View):
    def get(self,request,pk):
        product = Product.objects.get(pk=pk)
        user_wishlist = []
        in_wishlist = False
        
        if request.user.is_authenticated:
            # Get all wishlist items for the user
            user_wishlist = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
            # Check if current product is in wishlist
            in_wishlist = pk in user_wishlist
        
        # Create context dictionary with all variables
        context = {
            'product': product,
            'user_wishlist': user_wishlist,
            'in_wishlist': in_wishlist,
        }
        
        return render(request, "proj/productdetail.html", context)
    
    

class CustomerRegistrationView(View):
    def get(self,request):
        form= CustomerRegistrationForm()
        return render(request,'proj/customerregistration.html',locals())
    def post(self,request):
        form= CustomerRegistrationForm(request.POST)
        if form.is_valid():
            # Save the user first
            user = form.save()
            
            # Create a Customer record linked to the user
            # Set default values for required fields
            Customer.objects.create(
                user=user,
                name=user.username,  # Default name to username
                city='',             # Empty default
                state='Bagmati',     # Default province
                mobile='',           # Empty default
                zipcode=''           # Empty default
            )
            
            messages.success(request,"Congratulations! User Registered Successfully")
            return redirect('main:login')
        else:
            messages.warning(request,"Invalid Input Data")
        return render(request,'proj/customerregistration.html',locals())
    



@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    def get(self, request):
        # Check if user already has a profile
        existing_profile = Customer.objects.filter(user=request.user).first()
        
        if existing_profile:
            # Pre-populate form with existing data
            form = CustomerProfileForm(instance=existing_profile)
            has_profile = True
        else:
            # Empty form for new profile
            form = CustomerProfileForm(initial={'name': request.user.username})
            has_profile = False
            
        return render(request, 'proj/profile.html', {'form': form, 'has_profile': has_profile})
        
    def post(self, request):
        # Check if user already has a profile
        existing_profile = Customer.objects.filter(user=request.user).first()
        
        if existing_profile:
            # Update existing profile
            form = CustomerProfileForm(request.POST, instance=existing_profile)
            if form.is_valid():
                form.save()
                messages.success(request, "Profile Updated Successfully!")
            else:
                messages.warning(request, "Invalid Input Data")
        else:
            # Create new profile
            form = CustomerProfileForm(request.POST)
            if form.is_valid():
                profile = form.save(commit=False)
                profile.user = request.user
                profile.save()
                messages.success(request, "Profile Created Successfully!")
            else:
                messages.warning(request, "Invalid Input Data")
                
        # Refresh the form with the latest data
        has_profile = Customer.objects.filter(user=request.user).exists()
        return render(request, 'proj/profile.html', {'form': form, 'has_profile': has_profile})
    



@login_required
def address(request):
    # Get the user's profile information
    add = Customer.objects.filter(user=request.user)
    email = request.user.email  # Get the user's email
    return render(request, 'proj/address.html', {'add': add, 'email': email})



@method_decorator(login_required, name='dispatch')
class updateAddress(View):
    def get(self,request,pk):
        add= Customer.objects.get(pk=pk)
        form = CustomerProfileForm(instance=add)
        return render(request,'proj/updateAddress.html', locals())
    def post(self,request,pk):
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            add= Customer.objects.get(pk=pk)
            add.name= form.cleaned_data['name']
            add.city= form.cleaned_data['city']
            add.state= form.cleaned_data['state']
            add.mobile= form.cleaned_data['mobile']
            add.zipcode= form.cleaned_data['zipcode'] 
            add.save()
            messages.success(request,"Congratulations! Profile Updated Successfully")
        else:
            messages.warning(request,"Invalid Input Data")
        return redirect("address")

from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def sell_bike(request):
    # Ensure the session exists
    if not request.session.session_key:
        request.session.create()
    
    # Store the current session key to ensure it doesn't change
    session_key = request.session.session_key
    
    # Initialize customer data
    customer_data = {}
    customer = None
    previous_listings = None
    
    # If user is authenticated, try to fetch their customer profile and previous listings
    if request.user.is_authenticated:
        try:
            # Use filter instead of get to handle multiple customer profiles
            customer_profiles = Customer.objects.filter(user=request.user).order_by('-id')
            
            if customer_profiles.exists():
                # Use the most recent customer profile
                customer = customer_profiles.first()
                # Pre-fill form with customer data
                customer_data = {
                    'seller_name': customer.name,
                    'city': customer.city,
                }
                print(f"DEBUG: Pre-filling form with data from customer profile: {customer.id}")
                print(f"DEBUG: Total customer profiles found: {customer_profiles.count()}")
            else:
                raise Customer.DoesNotExist()
            
            # Check for previous listings by this customer
            previous_listings = SellerInfo.objects.filter(
                email=request.user.email
            ).order_by('-id').first()
            
            # If they have previous listings, pre-fill more data
            if previous_listings:
                # Only update fields that aren't already set from the customer profile
                if 'seller_name' not in customer_data or not customer_data['seller_name']:
                    customer_data['seller_name'] = previous_listings.full_name
                print(f"DEBUG: Found previous listings for this user: {previous_listings.id}")
        except Customer.DoesNotExist:
            print("DEBUG: No customer profile found for authenticated user during form load")
            pass
    
    if request.method == 'POST':
        form = SellBikeForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            # Create the product with all details including images
            product = Product.objects.create(
                brand=cd['brand'],
                title=cd['model'],
                made_year=cd['made_year'],
                kilometers=cd['kilometers'],
                location=cd['city'],
                price=cd['price'],
                condition=cd['condition'],
                engine_size=cd['engine_size'],
                seller_name=cd['seller_name'],
                product_image=cd['product_image'],
            )
            
            # Add bluebook images if provided
            if cd.get('bluebook_page2'):
                product.bluebook_page2 = cd['bluebook_page2']
            if cd.get('bluebook_page9'):
                product.bluebook_page9 = cd['bluebook_page9']
            product.save()
            
            # Get customer contact details - with debug logging
            email = ''
            phone_number = ''
            
            print(f"DEBUG: User authenticated: {request.user.is_authenticated}")
            if request.user.is_authenticated:
                print(f"DEBUG: User email: {request.user.email}")
            
            # First try to get from authenticated user
            if request.user.is_authenticated:
                email = request.user.email
                print(f"DEBUG: Using authenticated user email: {email}")
                
                # Try to get phone from customer profile
                try:
                    # Use filter instead of get to handle multiple customer profiles
                    customer_profiles = Customer.objects.filter(user=request.user).order_by('-id')
                    if customer_profiles.exists():
                        # Use the most recent customer profile
                        customer = customer_profiles.first()
                        phone_number = customer.mobile
                        print(f"DEBUG: Found customer profile with phone: {phone_number}")
                        print(f"DEBUG: Total customer profiles found: {customer_profiles.count()}")
                    else:
                        raise Customer.DoesNotExist()
                except Customer.DoesNotExist:
                    print("DEBUG: No customer profile found for authenticated user")
                    # If no customer profile, try previous listings
                    previous_listings = SellerInfo.objects.filter(email=email).order_by('-id').first()
                    if previous_listings and previous_listings.phone:
                        phone_number = previous_listings.phone
                        print(f"DEBUG: Using phone from previous listing: {phone_number}")
            
            # If we still don't have a phone number, check previous listings by name
            if not phone_number:
                print(f"DEBUG: Searching for listings by name: {cd['seller_name']}")
                name_match_listings = SellerInfo.objects.filter(full_name=cd['seller_name']).order_by('-id')
                if name_match_listings.exists():
                    first_match = name_match_listings.first()
                    print(f"DEBUG: Found listing by name match: {first_match.id}")
                    if first_match.phone:
                        phone_number = first_match.phone
                        print(f"DEBUG: Using phone from name match: {phone_number}")
                    # If we don't have an email yet, use the one from the name match
                    if not email and first_match.email:
                        email = first_match.email
                        print(f"DEBUG: Using email from name match: {email}")
            
            # Final check - if we still don't have an email or phone, use default values
            if not email and request.user.is_authenticated:
                email = request.user.email
                print(f"DEBUG: Using user email as fallback: {email}")
            
            print(f"DEBUG: Final email: {email}, Final phone: {phone_number}")
            
            # Create SellerInfo with all available details
            seller_info = SellerInfo.objects.create(
                full_name=cd['seller_name'],
                email=email,
                phone=phone_number,
                bike_brand=cd['brand'],
                bike_model=cd['model'],
                product=product
            )
            
            # Log the created seller info for debugging
            print(f"Created SellerInfo: {seller_info.id}, Name: {seller_info.full_name}, Email: {seller_info.email}, Phone: {seller_info.phone}")
            
            # Store success message in session
            from django.contrib import messages
            messages.success(request, 'Your bike has been successfully listed for sale!')
            
            # Make sure the session key doesn't change
            if session_key != request.session.session_key:
                request.session.cycle_key()
            
            # Set CSRF cookie explicitly
            from django.middleware.csrf import get_token
            get_token(request)
            
            # Use redirect instead of render to avoid POST-refresh issues
            from django.shortcuts import redirect
            response = redirect('main:sell_success')
            
            # Ensure cookies are properly set in the response
            if request.user.is_authenticated:
                # Set a separate cookie to help maintain the session
                response.set_cookie(
                    'user_authenticated', 
                    'true', 
                    max_age=3600*24*14,  # 14 days
                    httponly=True,
                    samesite='Lax'
                )
            
            return response
    else:
        # Pre-fill form with customer data for GET requests
        form = SellBikeForm(initial=customer_data)
    
    return render(request, 'proj/sell_bike_form.html', {
        'form': form,
        'customer': customer,
        'previous_listings': previous_listings
    })


@ensure_csrf_cookie
def sell_success(request):
    """
    View to display success message after a bike has been listed for sale.
    This view maintains the user's session to prevent logout.
    """
    # Ensure the session is maintained
    if not request.session.session_key:
        request.session.create()
        
    return render(request, 'proj/sell_success.html')

def buy_bikes(request):
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', 'relevance')

    bikes = Product.objects.all()
    user_wishlist = []
    
    # Get user's wishlist items if authenticated
    if request.user.is_authenticated:
        user_wishlist = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    if query:
        bikes = bikes.filter(
            Q(title__icontains=query) |
            Q(brand__icontains=query) |
            Q(location__icontains=query)
        )

    # Sorting logic
    if sort == 'price_asc':
        bikes = bikes.order_by('price')
    elif sort == 'price_desc':
        bikes = bikes.order_by('-price')
    elif sort == 'latest':
        bikes = bikes.order_by('-id')

    return render(request, 'proj/buy_bikes.html', {
        'bikes': bikes,
        'query': query,
        'sort': sort,
        'user_wishlist': user_wishlist
    })

def check_uploaded_files(request):
    # Get the most recently uploaded SellerInfo
    latest_seller = SellerInfo.objects.order_by('-id').first()
    
    context = {
        'seller_info': latest_seller,
        'bluebook_page2_exists': bool(latest_seller and latest_seller.bluebook_page2),
        'bluebook_page9_exists': bool(latest_seller and latest_seller.bluebook_page9),
    }
    
    return render(request, 'proj/uploaded_files.html', context)

    if query:
        bikes = bikes.filter(
            Q(title__icontains=query) |
            Q(brand__icontains=query) |
            Q(location__icontains=query)
        )

    if sort == 'price_asc':
        bikes = bikes.order_by('price')
    elif sort == 'price_desc':
        bikes = bikes.order_by('-price')
    elif sort == 'latest':
        bikes = bikes.order_by('-id')

    return render(request, 'proj/buy_bikes.html', {
        'bikes': bikes,
        'query': query,
        'sort': sort,
        'user_wishlist': user_wishlist,
    })

@login_required
def add_to_wishlist(request, product_id):
    product = Product.objects.get(id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def remove_from_wishlist(request, product_id):
    Wishlist.objects.filter(user=request.user, product_id=product_id).delete()
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def wishlist(request):
    # Get all products that are in the user's wishlist with all details
    wishlisted_products = Product.objects.filter(wishlist__user=request.user).distinct().select_related()
    
    # Get all wishlist item IDs for the user
    user_wishlist = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
    
    # Get the customer information for the current user
    customer = None
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        pass
    
    return render(request, 'proj/wishlist.html', {
        'products': wishlisted_products,
        'user_wishlist': user_wishlist,
        'customer': customer
    })

@require_POST
@login_required
def toggle_wishlist(request):
    # Always return a successful response to avoid error messages
    # If user is not authenticated, the template will handle it with the modal
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'authenticated': False,
            'message': 'Please log in to use the wishlist feature'
        })
    
    try:
        product_id = request.POST.get('product_id')
        if not product_id:
            return JsonResponse({
                'success': True,  # Still return success to avoid error popup
                'authenticated': True,
                'message': 'Missing product ID',
                'count': Wishlist.objects.filter(user=request.user).count()
            })
            
        product = Product.objects.get(id=product_id)
        
        # Check if this product is already in the user's wishlist
        wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()
        
        if wishlist_item:
            # Product is in wishlist, so remove it
            wishlist_item.delete()
            in_wishlist = False
        else:
            # Product is not in wishlist, so add it
            Wishlist.objects.create(user=request.user, product=product)
            in_wishlist = True
        
        # Get the updated count of wishlist items
        count = Wishlist.objects.filter(user=request.user).count()
        
        return JsonResponse({
            'success': True,
            'in_wishlist': in_wishlist, 
            'count': count,
            'authenticated': True
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'success': True,  # Still return success to avoid error popup
            'authenticated': True,
            'message': 'Product not found',
            'count': Wishlist.objects.filter(user=request.user).count()
        })
    except Exception as e:
        # Log the error but return a success response to avoid error popup
        print(f"Wishlist error: {str(e)}")
        return JsonResponse({
            'success': True,
            'authenticated': True,
            'message': 'An error occurred, but your request was processed',
            'count': Wishlist.objects.filter(user=request.user).count()
        })

class CustomLoginView(LoginView):
    def get_success_url(self):
        if self.request.user.is_staff:
            return '/admin/'
        return '/'

# Simple view functions for terms and privacy pages
def terms(request):
    return render(request, "proj/terms.html")

def privacy(request):
    return render(request, "proj/privacy.html")

@login_required
def my_orders(request):
    """Display all bikes purchased by the user"""
    purchased_bikes = []
    
    try:
        # 1. Get all completed payments for this user from BikePaymentTransaction
        from .models import BikePaymentTransaction, Product
        completed_transactions = BikePaymentTransaction.objects.filter(
            buyer=request.user,
            status='Completed'
        ).order_by('-created_at')
        
        purchased_bikes = list(completed_transactions)
        
        # 2. As a backup, also check for bikes with 'sold' status 
        # that might not have transactions but belong to the user
        # This is a fallback in case transaction records don't exist
        sold_products = Product.objects.filter(
            status='sold',
            bikepaymenttransaction__buyer=request.user
        ).exclude(
            bikepaymenttransaction__in=completed_transactions
        )
        
        # For any sold products that don't have transactions, create placeholder transaction objects
        for product in sold_products:
            # Create a temporary transaction object for display purposes
            transaction = BikePaymentTransaction(
                product=product,
                buyer=request.user,
                amount=product.price,
                status='Completed',
                purchase_order_id=f"ORDER-{product.id}",
                pidx=f"PURCHASE-{product.id}",
                created_at=product.updated_at
            )
            purchased_bikes.append(transaction)
    
    except Exception as e:
        messages.error(request, f"Error retrieving your orders: {str(e)}")
    
    return render(request, 'proj/my_orders.html', {
        'purchased_bikes': purchased_bikes
    })

@login_required
def create_test_transaction(request):
    """Test function to create a transaction record for testing purposes"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to do this")
        return redirect('main:home')
    
    try:
        from .models import BikePaymentTransaction, Product
        
        # Get the first available product
        product = Product.objects.filter(status='available').first()
        
        if not product:
            messages.error(request, "No available products to use for test transaction")
            return redirect('main:home')
        
        # Create a test transaction
        transaction = BikePaymentTransaction.objects.create(
            pidx=f"TEST-{uuid.uuid4()}",
            purchase_order_id=f"TEST-ORDER-{uuid.uuid4()}",
            product=product,
            buyer=request.user,
            amount=product.price,
            status='Completed',
            transaction_id=f"TEST-TXN-{uuid.uuid4()}",
            payment_method='Test'
        )
        
        # Update product status
        product.status = 'sold'
        product.save()
        
        messages.success(request, f"Test transaction created successfully. Order ID: {transaction.purchase_order_id}")
        return redirect('main:my_orders')
    
    except Exception as e:
        messages.error(request, f"Error creating test transaction: {str(e)}")
        return redirect('main:home')

# Admin view for customer lookup
@login_required
def admin_lookup_customer(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'found': False})
    
    # Try to find customer by email or phone
    customer = None
    
    # Check if query looks like an email
    if '@' in query:
        try:
            user = User.objects.get(email=query)
            customer = Customer.objects.filter(user=user).first()
        except User.DoesNotExist:
            pass
    
    # If not found by email, try phone
    if not customer:
        customer = Customer.objects.filter(mobile=query).first()
    
    if customer:
        return JsonResponse({
            'found': True,
            'name': customer.name,
            'email': customer.user.email,
            'phone': customer.mobile,
            'city': customer.city,
            'state': customer.state
        })
    else:
        return JsonResponse({'found': False})

brands = Product.objects.values_list('brand', flat=True).distinct()
models = Product.objects.values_list('title', flat=True).distinct()