from django.db.models import Count, Q, Min, Max
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
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail, EmailMessage
import uuid
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model, login
from .tokens import account_activation_token
import logging
from django.conf import settings
from django.urls import reverse
import json

def home(request):
    from .models import Product
    
    # Get all verified products 
    all_products = Product.objects.filter(
        verification_status='approved',
        status__in=['available', 'sold']
    ).order_by('status', '-created_at')
    
    # user ko wishlist items authenticated user matra
    user_wishlist = []
    if request.user.is_authenticated:
        user_wishlist = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
    
    latest_product_groups = [all_products[i:i+3] for i in range(0, len(all_products), 3)]
    
    return render(request, "proj/home.html", {
        'latest_products': all_products,
        'latest_product_groups': latest_product_groups,
        'user_wishlist': user_wishlist,
    })

def about(req):
    return render(req, "proj/about.html")

from django.views.decorators.csrf import csrf_protect

@csrf_protect
def contact(req):
    from django.contrib import messages
    from django.middleware.csrf import get_token
    
    csrf_token = get_token(req)
    
    if req.method == 'POST':
        name = req.POST.get('name')
        email = req.POST.get('email')
        subject = req.POST.get('subject')
        message = req.POST.get('message')
        
        # Prepare email
        email_subject = f"Contact Form: {subject}"
        email_message = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        
        try:
            # Send email
            from django.core.mail import send_mail
            from django.conf import settings
            from django.middleware.csrf import get_token
            
            get_token(req)
            
            send_mail(
                email_subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,  # From email (system email)
                ['prabinacharya573@gmail.com'],  # To email (your email)
                fail_silently=False,
            )
            messages.success(req, "Your message has been sent successfully. We'll get back to you soon!")
        except Exception as e:
            messages.error(req, "There was an error sending your message. Please try again later.")
            print(f"Email Error: {str(e)}")
            
        return redirect('main:contact')
        
    return render(req, "proj/contact.html", {'csrf_token': csrf_token})
    
class BrandView(View):
    def get(self, request, val):
        product = Product.objects.filter(
            brand=val, 
            verification_status='approved', 
            status__in=['available', 'sold']
        ).order_by('status', '-created_at')
        
        title = Product.objects.filter(
            brand=val, 
            verification_status='approved', 
            status__in=['available', 'sold']
        ).values('title').annotate(count=Count('id'))
        
        brands = Product.objects.filter(
            verification_status='approved', 
            status__in=['available', 'sold']
        ).values('brand').annotate(count=Count('id'))
        
        user_wishlist = []
        if request.user.is_authenticated:
            user_wishlist = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
            
        return render(request, "proj/brand.html", {
            'product': product,
            'title': title,
            'brands': brands,
            'brand': val,
            'user_wishlist': user_wishlist,
        })
    
class BrandTitle(View):
    def get(self, request, val):
        product = Product.objects.filter(title=val, verification_status='approved', status__in=['available', 'sold'])
        if product.exists():
            brand_val = product[0].brand
           
            title = Product.objects.filter(brand=brand_val, verification_status='approved', status__in=['available', 'sold']).values('title').annotate(count=Count('id'))
            
            brands = Product.objects.filter(verification_status='approved', status__in=['available', 'sold']).values('brand').annotate(count=Count('id'))
            
            user_wishlist = []
            if request.user.is_authenticated:
                user_wishlist = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
                
            return render(request, "proj/brand.html", {
                'product': product,
                'title': title,
                'brands': brands,
                'brand': brand_val,
                'user_wishlist': user_wishlist,
            })
        else:
            return render(request, "proj/brand.html", {
                'product': [],
                'title': [],
                'brands': [],
                'brand': '',
            })
    
class ProductDetail(View):
    def get(self,request,pk):
        try:
            product = Product.objects.get(pk=pk)
            
            if not request.user.is_staff:
                if product.verification_status != 'approved':
                    messages.error(request, "This product is not available for viewing.")
                    return redirect('main:home')
                
            user_wishlist = []
            in_wishlist = False
            
            if request.user.is_authenticated:
                user_wishlist = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
                in_wishlist = pk in user_wishlist
            
            context = {
                'product': product,
                'user_wishlist': user_wishlist,
                'in_wishlist': in_wishlist,
            }
            
            return render(request, "proj/productdetail.html", context)
        except Product.DoesNotExist:
            messages.error(request, "Product not found.")
            return redirect('main:home')
    
class CustomerRegistrationView(View):
    def get(self,request):
        form= CustomerRegistrationForm()
        return render(request,'proj/customerregistration.html',locals())
    def post(self,request):
        form= CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            
            Customer.objects.create(
                user=user,
                name=user.username,
                city='',
                state='',
                mobile='',
                zipcode='',
                gender=''
            )
            
            # Get email from form
            user_email = form.cleaned_data.get('email')
            print(f"DEBUG: Sending activation email to {user_email}")
            
            try:
                # Send activation email
                send_result = send_activation_email(request, user, user_email)
                print(f"DEBUG: Activation email send result: {send_result}")
                
                if not send_result and settings.DEBUG:
                    user.is_active = True
                    user.save()
                    print(f"DEBUG: Activated user {user.username} despite email failure (DEBUG mode)")
                    messages.warning(request, "Email could not be sent, but your account has been activated for testing purposes.")
            except Exception as e:
                print(f"DEBUG: Exception during email sending: {str(e)}")
                if settings.DEBUG:
                    user.is_active = True
                    user.save()
                    print(f"DEBUG: Activated user {user.username} despite exception (DEBUG mode)")
                    messages.warning(request, f"Email sending error: {str(e)}. Your account has been activated for testing purposes.")
            
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
            form = CustomerProfileForm(initial={
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email
            })
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
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    customer_data = {}
    customer = None
    previous_listings = None
    
    if request.user.is_authenticated:
        try:
            customer_profiles = Customer.objects.filter(user=request.user).order_by('-id')
            
            if customer_profiles.exists():
                customer = customer_profiles.first()
                customer_data = {
                    'seller_name': customer.name,
                    'city': customer.city,
                }
            else:
                raise Customer.DoesNotExist()
            
            previous_listings = SellerInfo.objects.filter(
                email=request.user.email
            ).order_by('-id').first()
            
            if previous_listings:
                if 'seller_name' not in customer_data or not customer_data['seller_name']:
                    customer_data['seller_name'] = previous_listings.full_name
        except Customer.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = SellBikeForm(request.POST, request.FILES)
        cd = form.data
        errors_occurred = False

        if 'number_plate' in cd and cd['number_plate'].strip():
            if Product.objects.filter(number_plate=cd['number_plate']).exists():
                form.add_error('number_plate', f'A bike with number plate {cd["number_plate"]} is already registered.')
                errors_occurred = True

        if 'engine_number' in cd and cd['engine_number'].strip():
            if Product.objects.filter(engine_number=cd['engine_number']).exists():
                form.add_error('engine_number', f'A bike with engine number {cd["engine_number"]} is already registered.')
                errors_occurred = True

        if 'chassis_number' in cd and cd['chassis_number'].strip():
            if Product.objects.filter(chassis_number=cd['chassis_number']).exists():
                form.add_error('chassis_number', f'A bike with chassis number {cd["chassis_number"]} is already registered.')
                errors_occurred = True

        if form.is_valid() and not errors_occurred:
            cd = form.cleaned_data

            product = Product.objects.create(
                brand=cd['brand'],
                title=cd['model'],
                made_year=cd['made_year'],
                kilometers=cd['kilometers'],
                location=cd['city'],
                price=cd['price'],
                condition=cd['condition'],
                engine_size=cd['engine_size'],
                engine_number=cd['engine_number'],
                chassis_number=cd['chassis_number'],
                color=cd['color'],
                number_plate=cd['number_plate'],
                previous_owners=cd['previous_owners'],
                seller_name=cd['seller_name'],
                product_image=cd['product_image'],
                description=cd.get('description', ''),
            )

            if cd.get('bluebook_page2'):
                product.bluebook_page2 = cd['bluebook_page2']
            if cd.get('bluebook_page9'):
                product.bluebook_page9 = cd['bluebook_page9']

            product.save()

            email = ''
            phone_number = ''

            if request.user.is_authenticated:
                email = request.user.email

                try:
                    customer_profiles = Customer.objects.filter(user=request.user).order_by('-id')
                    if customer_profiles.exists():
                        customer = customer_profiles.first()
                        phone_number = customer.mobile
                except Customer.DoesNotExist:
                    pass

                if not phone_number:
                    previous_listings = SellerInfo.objects.filter(email=email).order_by('-id').first()
                    if previous_listings and previous_listings.phone:
                        phone_number = previous_listings.phone

            seller_info = SellerInfo.objects.create(
                full_name=cd['seller_name'],
                email=email,
                phone=phone_number,
                bike_brand=cd['brand'],
                bike_model=cd['model'],
                product=product
            )

            messages.success(request, 'Your bike has been successfully listed for sale!')

            if session_key != request.session.session_key:
                request.session.cycle_key()

            from django.middleware.csrf import get_token
            get_token(request)

            return redirect('main:sell_success')
        else:
            messages.warning(request, "Please correct the errors below.")
    else:
        form = SellBikeForm(initial=customer_data)

    return render(request, 'proj/sell_bike_form.html', {
        'form': form,
        'customer': customer,
        'previous_listings': previous_listings
    })

@ensure_csrf_cookie
def sell_success(request):
    if not request.session.session_key:
        request.session.create()
        
    return render(request, 'proj/sell_success.html')

def buy_bikes(request):
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', 'relevance')
    brand_filter = request.GET.get('brand', '')
    condition_filter = request.GET.get('condition', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    year_filter = request.GET.get('year', '')

    bikes = Product.objects.filter(verification_status='approved', status__in=['available', 'sold']).order_by('status', '-created_at')
    user_wishlist = []
    
    if request.user.is_authenticated:
        user_wishlist = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    if query:
        bikes = bikes.filter(
            Q(title__icontains=query) |
            Q(brand__icontains=query) |
            Q(location__icontains=query) |
            Q(description__icontains=query)
        )
    
    if brand_filter:
        bikes = bikes.filter(brand=brand_filter)
    
    if condition_filter:
        bikes = bikes.filter(condition=condition_filter)
    
    if min_price:
        try:
            bikes = bikes.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            bikes = bikes.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    if year_filter:
        try:
            bikes = bikes.filter(made_year=int(year_filter))
        except ValueError:
            pass

    brands = Product.objects.filter(verification_status='approved', status='available').values('brand').annotate(count=Count('id'))
    
    all_brands = Product.objects.filter(verification_status='approved', status='available').values_list('brand', flat=True).distinct().order_by('brand')
    all_conditions = Product.objects.filter(verification_status='approved', status='available').values_list('condition', flat=True).distinct().order_by('condition')
    all_years = Product.objects.filter(verification_status='approved', status='available').values_list('made_year', flat=True).distinct().order_by('-made_year')
    
    price_range = Product.objects.filter(verification_status='approved', status='available').aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )

    if sort == 'price_asc':
        bikes = bikes.order_by('price')
    elif sort == 'price_desc':
        bikes = bikes.order_by('-price')
    elif sort == 'latest':
        bikes = bikes.order_by('-id')
    elif sort == 'oldest':
        bikes = bikes.order_by('id')
    elif sort == 'year_desc':
        bikes = bikes.order_by('-made_year')
    elif sort == 'year_asc':
        bikes = bikes.order_by('made_year')
    
    total_count = bikes.count()
    
    return render(request, 'proj/buy_bikes.html', {
        'bikes': bikes,
        'query': query,
        'sort': sort,
        'user_wishlist': user_wishlist,
        'brand': brand_filter,
        'condition_filter': condition_filter,
        'min_price': min_price,
        'max_price': max_price,
        'year_filter': year_filter,
        'brands': brands,
        'all_brands': all_brands,
        'all_conditions': all_conditions,
        'all_years': all_years,
        'price_range': price_range,
        'total_count': total_count,
    })

def check_uploaded_files(request):
    latest_seller = SellerInfo.objects.order_by('-id').first()
    
    context = {
        'seller_info': latest_seller,
        'bluebook_page2_exists': bool(latest_seller and latest_seller.bluebook_page2),
        'bluebook_page9_exists': bool(latest_seller and latest_seller.bluebook_page9),
    }
    
    return render(request, 'proj/uploaded_files.html', context)

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
    wishlisted_products = Product.objects.filter(wishlist__user=request.user).distinct().select_related()
    
    user_wishlist = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
    
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
def toggle_wishlist(request):
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
                'success': False,
                'authenticated': True,
                'message': 'Missing product ID',
                'count': Wishlist.objects.filter(user=request.user).count()
            })
            
        product = Product.objects.get(id=product_id)
        
        wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()
        
        if wishlist_item:
            wishlist_item.delete()
            in_wishlist = False
        else:
            Wishlist.objects.create(user=request.user, product=product)
            in_wishlist = True
        
        count = Wishlist.objects.filter(user=request.user).count()
        
        return JsonResponse({
            'success': True,
            'in_wishlist': in_wishlist, 
            'count': count,
            'authenticated': True
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'authenticated': True,
            'message': 'Product not found',
            'count': Wishlist.objects.filter(user=request.user).count()
        })
    except Exception as e:
        print(f"Wishlist error: {str(e)}")
        return JsonResponse({
            'success': False,
            'authenticated': True,
            'message': f'An error occurred: {str(e)}',
            'count': Wishlist.objects.filter(user=request.user).count()
        }, status=500)

class CustomLoginView(LoginView):
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
            
        if self.request.user.is_staff and self.request.path.startswith('/admin/'):
            return '/admin/'
            
        return '/'

def terms(request):
    return render(request, "proj/terms.html")

def privacy(request):
    return render(request, "proj/privacy.html")

@login_required
def my_deals(request):
    user = request.user
    
    purchased_bikes = []
    
    try:
        from .models import BikePaymentTransaction, Product, SellerInfo
        completed_transactions = BikePaymentTransaction.objects.filter(
            buyer=user,
            status='Completed'
        ).order_by('-created_at')
        
        purchased_bikes = list(completed_transactions)
        
        sold_products = Product.objects.filter(
            status='sold',
            bikepaymenttransaction__buyer=user
        ).exclude(
            bikepaymenttransaction__in=completed_transactions
        )
        
        for product in sold_products:
            transaction = BikePaymentTransaction(
                product=product,
                buyer=user,
                amount=product.price,
                status='Completed',
                purchase_order_id=f"ORDER-{product.id}",
                pidx=f"PURCHASE-{product.id}",
                created_at=product.updated_at
            )
            purchased_bikes.append(transaction)
    
    except Exception as e:
        messages.error(request, f"Error retrieving your purchased bikes: {str(e)}")
    
    listed_bikes = []
    
    try:
        seller_infos = SellerInfo.objects.filter(email=user.email).order_by('-created_at')
        
        for seller_info in seller_infos:
            if seller_info.product:
                verification_status = seller_info.product.verification_status
                verification_badge = ""
                
                if verification_status == 'pending':
                    verification_badge = '<span class="badge bg-warning text-dark">Pending Verification</span>'
                elif verification_status == 'approved':
                    verification_badge = '<span class="badge bg-success">Verified</span>'
                elif verification_status == 'rejected':
                    verification_badge = '<span class="badge bg-danger">Rejected</span>'
                
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
    
    except Exception as e:
        messages.error(request, f"Error retrieving your listed bikes: {str(e)}")
    
    return render(request, 'proj/my_deals.html', {
        'purchased_bikes': purchased_bikes,
        'listed_bikes': listed_bikes,
        'user': user
    })

@login_required
def update_product(request, pk):
    try:
        from django.shortcuts import get_object_or_404
        product = get_object_or_404(Product, pk=pk)
        
        seller_info = SellerInfo.objects.filter(product=product, email=request.user.email).first()
        
        if not seller_info:
            messages.error(request, "You don't have permission to update this listing.")
            return redirect('main:my_deals')
        
        if product.status == 'sold':
            messages.error(request, "This listing has already been sold and cannot be edited.")
            return redirect('main:my_deals')
        
        if request.method == 'POST':
            form = SellBikeForm(request.POST, request.FILES)
            if form.is_valid():
                cd = form.cleaned_data

                duplicate_product = Product.objects.filter(
                    Q(number_plate=cd['number_plate']) |
                    Q(engine_number=cd['engine_number']) |
                    Q(chassis_number=cd['chassis_number'])
                ).exclude(pk=product.pk).first()

                if duplicate_product:
                    if duplicate_product.number_plate == cd['number_plate']:
                        form.add_error('number_plate', f'A bike with number plate {cd["number_plate"]} is already registered.')
                    if duplicate_product.engine_number == cd['engine_number']:
                        form.add_error('engine_number', f'A bike with engine number {cd["engine_number"]} is already registered.')
                    if duplicate_product.chassis_number == cd['chassis_number']:
                        form.add_error('chassis_number', f'A bike with chassis number {cd["chassis_number"]} is already registered.')

                    if form.errors:
                        messages.warning(request, "Please correct the errors below.")
                        return render(request, 'proj/update_product.html', {
                            'form': form,
                            'product': product
                        })

                product.title = form.cleaned_data['model']
                product.brand = form.cleaned_data['brand']
                product.price = form.cleaned_data['price']
                product.condition = form.cleaned_data['condition']
                product.made_year = form.cleaned_data['made_year']
                product.kilometers = form.cleaned_data['kilometers']
                product.engine_size = form.cleaned_data['engine_size']
                product.engine_number = form.cleaned_data.get('engine_number', '')
                product.chassis_number = form.cleaned_data.get('chassis_number', '')
                product.color = form.cleaned_data.get('color', '')
                product.number_plate = form.cleaned_data.get('number_plate', '')
                product.previous_owners = form.cleaned_data.get('previous_owners', 0)
                product.location = form.cleaned_data['city']
                product.seller_name = form.cleaned_data['seller_name']
                product.description = form.cleaned_data.get('description', '')
                
                if 'product_image' in request.FILES:
                    product.product_image = request.FILES['product_image']
                if 'bluebook_page2' in request.FILES:
                    product.bluebook_page2 = request.FILES['bluebook_page2']
                if 'bluebook_page9' in request.FILES:
                    product.bluebook_page9 = request.FILES['bluebook_page9']
                
                if product.verification_status == 'approved' or product.verification_status == 'rejected':
                    product.verification_status = 'pending'
                    product.status = 'pending'
                    messages.info(request, "Your updated listing will need to be verified again before it appears in the marketplace.")
                
                product.save()
                
                seller_info.bike_brand = product.brand
                seller_info.bike_model = product.title
                seller_info.verification_status = 'pending'
                seller_info.save()
                
                my_deals_url = reverse('main:my_deals')
                redirect_url = f'{my_deals_url}?updated=true#selling'
                return redirect(redirect_url)
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in {field}: {error}")
        else:
            initial_data = {
                'brand': product.brand,
                'model': product.title,
                'made_year': product.made_year,
                'kilometers': product.kilometers,
                'city': product.location,
                'price': product.price,
                'condition': product.condition,
                'engine_size': product.engine_size,
                'engine_number': product.engine_number,
                'chassis_number': product.chassis_number,
                'color': product.color,
                'number_plate': product.number_plate,
                'previous_owners': product.previous_owners,
                'seller_name': product.seller_name,
                'description': product.description,
            }
            form = SellBikeForm(initial=initial_data)
            
            form.fields['product_image'].required = False
            form.fields['bluebook_page2'].required = False
            form.fields['bluebook_page9'].required = False
        
        return render(request, 'proj/update_product.html', {
            'form': form,
            'product': product
        })
        
    except Exception as e:
        messages.error(request, f"Error updating listing: {str(e)}")
        return redirect('main:my_deals')

@login_required
def delete_product(request, pk):
    try:
        from django.shortcuts import get_object_or_404
        product = get_object_or_404(Product, pk=pk)
        
        seller_info = SellerInfo.objects.filter(product=product, email=request.user.email).first()
        
        if not seller_info:
            messages.error(request, "You don't have permission to delete this listing.")
            return redirect('main:my_deals')
        
        if request.method == 'POST':
            product.delete()
            messages.success(request, "Your listing has been deleted successfully.")
            return redirect('main:my_deals')
        
        return render(request, 'proj/delete_product_confirm.html', {
            'product': product
        })
        
    except Exception as e:
        messages.error(request, f"Error deleting listing: {str(e)}")
        return redirect('main:my_deals')

@login_required
def create_test_transaction(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to do this")
        return redirect('main:home')
    
    try:
        from .models import BikePaymentTransaction, Product
        
        product = Product.objects.filter(status='available').first()
        
        if not product:
            messages.error(request, "No available products to use for test transaction")
            return redirect('main:home')
        
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
        
        product.status = 'sold'
        product.save()
        
        messages.success(request, f"Test transaction created successfully. Order ID: {transaction.purchase_order_id}")
        return redirect('main:my_deals')
    
    except Exception as e:
        messages.error(request, f"Error creating test transaction: {str(e)}")
        return redirect('main:home')

@login_required
def admin_lookup_customer(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'found': False})
    
    customer = None
    
    if '@' in query:
        try:
            user = User.objects.get(email=query)
            customer = Customer.objects.filter(user=user).first()
        except User.DoesNotExist:
            pass
    
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

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token) and not user.is_active:
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, "Your account has been activated successfully! You are now logged in.")
        return redirect('main:home')
    elif user is not None and user.is_active:
        return redirect('main:home')
    else:
        messages.error(request, "Activation link is invalid or has expired!")
        return redirect('main:home')

def send_activation_email(request, user, to_email):
    from django.conf import settings
    import sys
    
    try:
        mail_subject = 'Activate your BikeResale account'
        
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        domain = get_current_site(request).domain
        protocol = 'https' if request.is_secure() else 'http'
        
        message = render_to_string('email_activation.html', {
            'user': user,
            'domain': domain,
            'uid': uid,
            'token': token,
            'protocol': protocol
        })
        
        from_email = settings.DEFAULT_FROM_EMAIL
        if not from_email:
            from_email = 'noreply@bikeresell.com'
            print(f"WARNING: Using fallback email address: {from_email}")
        
        email = EmailMessage(
            mail_subject,
            message,
            from_email,
            [to_email]
        )
        
        send_result = email.send(fail_silently=False)
        
        if send_result > 0:
            messages.success(request, 
                f"Dear {user.username}, please check your email {to_email} to complete registration. "
                f"Note: Check your spam folder if you don't see the email.")
            return True
        else:
            messages.error(request, f"Problem sending confirmation email to {to_email}. Email system returned {send_result}.")
            return False
            
    except Exception as e:
        print(f"Email Error: {str(e)}")
        print(f"Exception type: {type(e)}")
        messages.error(request, f"Email could not be sent. Error: {str(e)}")
        
        if settings.DEBUG:
            user.is_active = True
            user.save()
            messages.info(request, "DEBUG: User has been auto-activated due to email sending failure in DEBUG mode.")
        
        return False

def test_email(request):
    """
    Test view to debug email sending
    """
    from django.core.mail import send_mail
    from django.conf import settings
    import sys
    
    test_email_to = request.GET.get('email', 'test@example.com')
    
    result = {
        'success': False,
        'errors': [],
        'config': {
            'backend': settings.EMAIL_BACKEND,
            'host': settings.EMAIL_HOST,
            'port': settings.EMAIL_PORT,
            'user': settings.EMAIL_HOST_USER,
            'from_email': settings.DEFAULT_FROM_EMAIL,
            'tls': settings.EMAIL_USE_TLS,
        }
    }
    
    try:
        send_result = send_mail(
            'Test Email from BikeResell',
            'This is a test email to debug email sending functionality.',
            settings.DEFAULT_FROM_EMAIL,
            [test_email_to],
            fail_silently=False,
        )
        
        result['send_result'] = send_result
        result['success'] = send_result > 0
        
    except Exception as e:
        result['errors'].append(str(e))
        result['exception_type'] = str(type(e))
        result['traceback'] = str(sys.exc_info())
    
    
    from django.http import JsonResponse
    return JsonResponse(result)

def check_unique_field(request):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
        
    field_name = request.GET.get('field')
    value = request.GET.get('value')
    exclude_id = request.GET.get('exclude_id')
    
    if not field_name or not value:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
        
    allowed_fields = ['engine_number', 'chassis_number', 'number_plate']
    if field_name not in allowed_fields:
        return JsonResponse({'error': 'Invalid field'}, status=400)
    
    query = {field_name: value}
    queryset = Product.objects.filter(**query)
    
    if exclude_id:
        queryset = queryset.exclude(pk=exclude_id)
    
    existing_product = queryset.first()
    exists = existing_product is not None
    
    response_data = {'exists': exists}
    
    if exists:
        brand = existing_product.brand if existing_product.brand else 'Unknown'
        model = existing_product.title if existing_product.title else 'Unknown'
        
        response_data['product_info'] = {
            'brand': brand,
            'model': model,
            'field_name': field_name.replace('_', ' ').title(),
            'value': value
        }
        
        print(f"Found duplicate {field_name}: {value} - Used by product {existing_product.id} ({brand} {model})")
    else:
        print(f"Checked {field_name}: {value} - No duplicates found")
    
    return JsonResponse(response_data)

def custom_logout(request):
    from django.contrib.auth import logout
    from django.shortcuts import redirect
    from django.conf import settings
    from django.contrib import messages
    
    session_cookie_name = settings.SESSION_COOKIE_NAME
    
    logout(request)
    
    response = redirect('main:login')
    
    response.delete_cookie(session_cookie_name)
    
    messages.success(request, "You have been successfully logged out. Please refresh any open forms before submitting them.")
    
    request.session['needs_refresh'] = True
    
    return response

@login_required
@require_POST
def validate_old_password(request):
    try:
        data = json.loads(request.body)
        old_password = data.get('old_password')
        
        if not old_password:
            return JsonResponse({'valid': False, 'error': 'Password is required'})
            
        is_valid = request.user.check_password(old_password)
        return JsonResponse({'valid': is_valid})
        
    except json.JSONDecodeError:
        return JsonResponse({'valid': False, 'error': 'Invalid request data'})
    except Exception as e:
        return JsonResponse({'valid': False, 'error': str(e)})