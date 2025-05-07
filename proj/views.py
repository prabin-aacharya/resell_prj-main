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
# Create your views here.
def home(request):
    from .models import Product
    latest_products = list(Product.objects.all().order_by('-id')[:8])
    # Group products into sublists of 3
    latest_product_groups = [latest_products[i:i+3] for i in range(0, len(latest_products), 3)]
    return render(request, "proj/home.html", {'latest_products': latest_products, 'latest_product_groups': latest_product_groups})

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
        if request.user.is_authenticated:
            user_wishlist = request.user.wishlist_set.all().values_list('product_id', flat=True)
        return render(request,"proj/productdetail.html",locals())
    
    

class CustomerRegistrationView(View):
    def get(self,request):
        form= CustomerRegistrationForm()
        return render(request,'proj/customerregistration.html',locals())
    def post(self,request):
        form= CustomerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Congratulations! User Registered Successfully")
            return redirect('login')
        else:
            messages.warning(request,"Invalid Input Data")
        return render(request,'proj/customerregistration.html',locals())
    



@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    def get(self,request):
        form = CustomerProfileForm()
        return render(request,'proj/profile.html', locals())
    def post(self,request):
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            user = request.user
            name= form.cleaned_data['name']
            city= form.cleaned_data['city']
            state= form.cleaned_data['state']
            mobile= form.cleaned_data['mobile']
            zipcode= form.cleaned_data['zipcode']

            reg = Customer(user=user,name=name,city=city,state=state,mobile=mobile,zipcode=zipcode)
            reg.save()
            messages.success(request,"Congratulations! Profile Saved Successfully")
        else:
            messages.warning(request,"Invalid Input Data")
        return render(request,'proj/profile.html', locals())
    



@login_required
def address(request):
    add= Customer.objects.filter(user=request.user)
    return render(request,'proj/address.html', locals())



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

def sell_bike(request):
    if request.method == 'POST':
        form = SellBikeForm(request.POST, request.FILES)
        if form.is_valid():
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
                seller_name=cd['seller_name'],
                product_image=cd['product_image'],
            )
            
            # Create SellerInfo
            # Read image files as binary
            bike_photo_binary = cd['product_image'].read() if cd['product_image'] else None
            bluebook_page2_binary = cd['bluebook_page2'].read() if cd.get('bluebook_page2') else None
            bluebook_page9_binary = cd['bluebook_page9'].read() if cd.get('bluebook_page9') else None
            
            SellerInfo.objects.create(
                full_name=cd['seller_name'],
                bike_brand=cd['brand'],
                bike_model=cd['model'],
                bike_photo=bike_photo_binary,
                bluebook_page2=bluebook_page2_binary,
                bluebook_page9=bluebook_page9_binary,
                product=product
            )
            
            return render(request, 'proj/sell_success.html')
    else:
        form = SellBikeForm()
    return render(request, 'proj/sell_bike_form.html', {'form': form})

def buy_bikes(request):
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', 'relevance')

    bikes = Product.objects.all()
    user_wishlist = []
    if request.user.is_authenticated:
        user_wishlist = request.user.wishlist_set.all().values_list('product_id', flat=True)

    if query:
        bikes = bikes.filter(
            Q(title__icontains=query) |
            Q(brand__icontains=query)
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
    wishlisted_products = Product.objects.filter(wishlist__user=request.user)
    return render(request, 'proj/wishlist.html', {'products': wishlisted_products})

@require_POST
@login_required
def toggle_wishlist(request):
    product_id = request.POST.get('product_id')
    product = Product.objects.get(id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    if product in wishlist.products.all():
        wishlist.products.remove(product)
        in_wishlist = False
    else:
        wishlist.products.add(product)
        in_wishlist = True
    count = wishlist.products.count()
    return JsonResponse({'in_wishlist': in_wishlist, 'count': count})

class CustomLoginView(LoginView):
    def get_success_url(self):
        if self.request.user.is_staff:
            return '/admin/'
        return '/'

brands = Product.objects.values_list('brand', flat=True).distinct()
models = Product.objects.values_list('title', flat=True).distinct()