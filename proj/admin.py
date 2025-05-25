from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.contrib.auth.models import User, Group
from django.contrib.admin.views.main import ChangeList
from django.db.models import Count, Sum, Q
from . models import Product, Customer, Wishlist, SellerInfo, BikePaymentTransaction
from .forms import SellBikeForm, SellerInfoForm
from django import forms
import datetime
from . import admin_views
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.admin import AdminSite
from django.core.paginator import Paginator
from django.conf import settings
from .payment_views import generate_pdf_sales_report_admin

# Customize admin site
admin.site.site_header = 'Bike Resell Admin'
admin.site.site_title = 'Bike Resell Admin Portal'
admin.site.index_title = 'Welcome to Bike Resell Admin Portal'

# Custom admin index view to add statistics
class BikeResellAdminSite(AdminSite):
    """
    Custom admin site for Bike Resell with dashboard statistics
    """
    site_header = 'Bike Resell Admin'
    site_title = 'Bike Resell Admin Portal'
    index_title = 'Dashboard'
    index_template = 'admin/dashboard.html'
    login_template = 'admin/login.html'  # Specify the custom admin login template
    
    def get_urls(self):
        urls = super().get_urls()
        
        # Add our custom admin views
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='admin_dashboard'),
            path('products/', self.admin_view(admin_views.ProductListView.as_view()), name='admin_product_list'),
            path('products/create/', self.admin_view(admin_views.ProductCreateView.as_view()), name='admin_product_create'),
            path('products/<int:pk>/update/', self.admin_view(admin_views.ProductUpdateView.as_view()), name='admin_product_update'),
            path('products/<int:pk>/delete/', self.admin_view(admin_views.ProductDeleteView.as_view()), name='admin_product_delete'),
            path('orders/', self.admin_view(admin_views.OrderListView.as_view()), name='admin_order_list'),
            path('orders/<int:pk>/update/', self.admin_view(admin_views.OrderUpdateView.as_view()), name='admin_order_update'),
            path('customers/', self.admin_view(admin_views.CustomerListView.as_view()), name='admin_customer_list'),
            path('customers/<int:pk>/update/', self.admin_view(admin_views.CustomerUpdateView.as_view()), name='admin_customer_update'),
            path('customers/<int:pk>/delete/', self.admin_view(admin_views.CustomerDeleteView.as_view()), name='admin_customer_delete'),
            path('customers/create/', self.admin_view(admin_views.CustomerCreateView.as_view()), name='admin_customer_create'),
            path('customers/<int:pk>/view/', self.admin_view(admin_views.CustomerDetailView.as_view()), name='admin_customer_detail'),
            path('wishlists/', self.admin_view(admin_views.WishlistListView.as_view()), name='admin_wishlist_list'),
            path('sellers/', self.admin_view(admin_views.SellerInfoListView.as_view()), name='admin_seller_list'),
            path('sellers/create/', self.admin_view(admin_views.SellerInfoCreateView.as_view()), name='admin_seller_create'),
            path('sellers/<int:pk>/update/', self.admin_view(admin_views.SellerInfoUpdateView.as_view()), name='admin_seller_update'),
            path('sellers/<int:pk>/delete/', self.admin_view(admin_views.SellerInfoDeleteView.as_view()), name='admin_seller_delete'),
            path('purchases/', self.admin_view(self.bike_purchases_view), name='admin_bike_purchases'),
            path('seller-listings/', self.admin_view(self.seller_listings_view), name='seller_listings'),
            path('seller-listings/approve/<int:pk>/', self.admin_view(self.approve_listing), name='approve_listing'),
            path('seller-listings/reject/<int:pk>/', self.admin_view(self.reject_listing), name='reject_listing'),
            path('seller-listings/mark-sold/<int:pk>/', self.admin_view(self.mark_listing_sold), name='mark_sold'),
            path('logout/', self.logout_view, name='logout'),
            path('download-invoice/<str:transaction_id>/', self.admin_view(generate_pdf_sales_report_admin), name='admin_download_invoice'),
        ]
        
        # Insert our custom URLs before the default admin URLs
        return custom_urls + urls
    
    def logout_view(self, request):
        """Custom logout view that redirects to the admin login page"""
        # Store the admin session cookie
        admin_session_cookie = getattr(settings, 'ADMIN_SESSION_COOKIE_NAME', 'admin_sessionid')
        
        # Perform logout
        logout(request)
        
        # Create response that redirects to admin login
        response = redirect('admin:login')
        
        # Explicitly delete the admin session cookie
        response.delete_cookie(admin_session_cookie)
        
        return response
    
    def dashboard_view(self, request):
        """Custom dashboard view that displays statistics"""
        context = self.each_context(request)
        
        # Get statistics for dashboard
        context['product_count'] = Product.objects.count()
        context['customer_count'] = Customer.objects.count()
        context['wishlist_count'] = Wishlist.objects.count()
        context['seller_count'] = SellerInfo.objects.count()
        
        # Purchase statistics
        context['purchase_count'] = BikePaymentTransaction.objects.filter(status='Completed').count()
        context['total_revenue'] = BikePaymentTransaction.objects.filter(status='Completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Recent products
        context['recent_products'] = Product.objects.order_by('-id')[:5]
        
        # Recent customers
        context['recent_customers'] = Customer.objects.order_by('-id')[:5]
        
        # Recent bike payments
        context['recent_bike_payments'] = BikePaymentTransaction.objects.select_related('buyer', 'product').order_by('-created_at')[:5]
        
        # Seller listings statistics
        context['pending_verification_count'] = SellerInfo.objects.filter(product__verification_status='pending').count()
        context['approved_count'] = SellerInfo.objects.filter(product__verification_status='approved').count()
        context['rejected_count'] = SellerInfo.objects.filter(product__verification_status='rejected').count()
        
        # Recent seller listings (with products)
        context['recent_listings'] = SellerInfo.objects.filter(product__isnull=False).select_related('product').order_by('-created_at')[:6]
        
        return render(request, 'admin/dashboard.html', context)
    
    def bike_purchases_view(self, request):
        """Custom view for bike purchases"""
        context = self.each_context(request)
        
        # Get all bike payment transactions
        context['bike_payments'] = BikePaymentTransaction.objects.select_related(
            'product', 'buyer'
        ).order_by('-created_at')
        
        # Get purchase statistics
        context['total_purchases'] = BikePaymentTransaction.objects.filter(status='Completed').count()
        context['total_revenue'] = BikePaymentTransaction.objects.filter(status='Completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Get top buyers
        from django.db.models import Count
        context['top_buyers'] = User.objects.annotate(
            purchase_count=Count('bike_purchases', filter=Q(bike_purchases__status='Completed'))
        ).filter(purchase_count__gt=0).order_by('-purchase_count')[:5]
        
        return render(request, 'admin/bike_purchases.html', context)
    
    def index(self, request, extra_context=None):
        # Redirect to our custom dashboard
        return self.dashboard_view(request)
    
    def seller_listings_view(self, request):
        """Custom view for managing seller listings"""
        from proj.models import SellerInfo, Product
        from django.core.paginator import Paginator
        from django.db.models import Count
        
        context = self.each_context(request)
        
        # Get filter parameters
        verification_status = request.GET.get('verification_status', '')
        status = request.GET.get('status', '')
        search = request.GET.get('search', '')
        
        # Base queryset - get all seller infos with products
        queryset = SellerInfo.objects.filter(product__isnull=False).select_related('product')
        
        # Get counts for statistics before applying filters
        context['pending_count'] = queryset.filter(product__verification_status='pending').count()
        context['approved_count'] = queryset.filter(product__verification_status='approved').count()
        context['rejected_count'] = queryset.filter(product__verification_status='rejected').count()
        
        # Apply filters
        if verification_status:
            queryset = queryset.filter(product__verification_status=verification_status)
        if status:
            queryset = queryset.filter(product__status=status)
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) | 
                Q(email__icontains=search) | 
                Q(phone__icontains=search) | 
                Q(bike_brand__icontains=search) | 
                Q(bike_model__icontains=search) |
                Q(product__title__icontains=search)
            )
        
        # Order by most recent first
        queryset = queryset.order_by('-created_at')
        
        # Paginate results
        paginator = Paginator(queryset, 9)  # 9 cards per page (3x3 grid)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context.update({
            'title': 'Seller Listings',
            'listings': page_obj,
            'page_obj': page_obj,
            'paginator': paginator,
            'is_paginated': paginator.num_pages > 1,
        })
        
        return render(request, 'admin/seller_listings.html', context)
    
    def approve_listing(self, request, pk):
        """Approve a seller listing"""
        from proj.models import SellerInfo
        from django.contrib import messages
        import datetime
        
        if request.method == 'POST':
            try:
                seller_info = SellerInfo.objects.get(pk=pk)
                if seller_info.product:
                    # Get admin notes if provided
                    admin_notes = request.POST.get('admin_notes', '')
                    
                    # Update the product
                    seller_info.product.verification_status = 'approved'
                    seller_info.product.status = 'available'
                    
                    # Add verification metadata
                    verified_by = f"{request.user.username} ({request.user.email})"
                    verified_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    verification_meta = f"Verified by {verified_by} on {verified_date}"
                    
                    # Store admin notes if provided
                    if admin_notes:
                        existing_notes = seller_info.product.description or ""
                        admin_note_text = f"\n\n[Admin Verification Notes: {admin_notes}]\n{verification_meta}"
                        seller_info.product.description = existing_notes + admin_note_text
                    else:
                        existing_notes = seller_info.product.description or ""
                        seller_info.product.description = existing_notes + f"\n\n[{verification_meta}]"
                    
                    seller_info.product.save()
                    
                    # Update the seller info
                    seller_info.verification_status = 'verified'
                    seller_info.save()
                    
                    messages.success(request, f'Listing "{seller_info.product.title}" has been approved and is now visible on the marketplace.')
                else:
                    messages.error(request, 'No product associated with this listing.')
            except SellerInfo.DoesNotExist:
                messages.error(request, 'Listing not found.')
        
        return redirect('admin:seller_listings')
    
    def reject_listing(self, request, pk):
        """Reject a seller listing"""
        from proj.models import SellerInfo
        from django.contrib import messages
        import datetime
        
        if request.method == 'POST':
            try:
                seller_info = SellerInfo.objects.get(pk=pk)
                if seller_info.product:
                    # Get admin notes if provided
                    admin_notes = request.POST.get('admin_notes', '')
                    
                    # Update the product
                    seller_info.product.verification_status = 'rejected'
                    
                    # Add verification metadata
                    verified_by = f"{request.user.username} ({request.user.email})"
                    verified_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    verification_meta = f"Rejected by {verified_by} on {verified_date}"
                    
                    # Store admin notes if provided
                    if admin_notes:
                        existing_notes = seller_info.product.description or ""
                        admin_note_text = f"\n\n[Admin Rejection Notes: {admin_notes}]\n{verification_meta}"
                        seller_info.product.description = existing_notes + admin_note_text
                    else:
                        existing_notes = seller_info.product.description or ""
                        seller_info.product.description = existing_notes + f"\n\n[{verification_meta}]"
                    
                    seller_info.product.save()
                    
                    # Update the seller info
                    seller_info.verification_status = 'rejected'
                    seller_info.save()
                    
                    messages.success(request, f'Listing "{seller_info.product.title}" has been rejected.')
                else:
                    messages.error(request, 'No product associated with this listing.')
            except SellerInfo.DoesNotExist:
                messages.error(request, 'Listing not found.')
        
        return redirect('admin:seller_listings')
    
    def mark_listing_sold(self, request, pk):
        """Mark a listing as sold"""
        from proj.models import SellerInfo
        from django.contrib import messages
        
        if request.method == 'POST':
            try:
                seller_info = SellerInfo.objects.get(pk=pk)
                if seller_info.product:
                    # Update the product
                    seller_info.product.status = 'sold'
                    seller_info.product.save()
                    
                    # Update the seller info
                    seller_info.status = 'completed'
                    seller_info.save()
                    
                    messages.success(request, f'Listing "{seller_info.product.title}" has been marked as sold.')
                else:
                    messages.error(request, 'No product associated with this listing.')
            except SellerInfo.DoesNotExist:
                messages.error(request, 'Listing not found.')
        
        return redirect('admin:seller_listings')

# Replace the default admin site
admin_site = BikeResellAdminSite(name='bikeresell')
admin.site = admin_site

# Custom Product Admin Form
class ProductAdminForm(forms.ModelForm):
    # Match fields from the frontend SellBikeForm
    BRAND_CHOICES = [
        ('', 'Select Brand'),
        ('HONDA', 'Honda'),
        ('YAMAHA', 'Yamaha'),
        ('BAJAJ', 'Bajaj'),
        ('HERO', 'Hero'),
        ('TVS', 'TVS'),
    ]
    
    CONDITION_CHOICES = [
        ('', 'Select Condition'),
        ('Like New', 'Like New'),
        ('Excellent', 'Excellent'),
        ('Good', 'Good'),
        ('Fair', 'Fair'),
        ('Poor', 'Poor'),
    ]
    
    CURRENT_YEAR = datetime.datetime.now().year
    YEAR_CHOICES = [(year, str(year)) for year in range(CURRENT_YEAR, 1949, -1)]
    
    # Override fields to match frontend
    brand = forms.ChoiceField(
        choices=BRAND_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    condition = forms.ChoiceField(
        choices=CONDITION_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If we have an instance (editing existing product), ensure condition is properly set
        if 'instance' in kwargs and kwargs['instance']:
            instance = kwargs['instance']
            if instance.condition:
                self.initial['condition'] = instance.condition
    
    made_year = forms.IntegerField(
        label="Year of manufacturing",
        required=True,
        widget=forms.Select(
            choices=YEAR_CHOICES,
            attrs={'class': 'form-select'}
        )
    )
    
    # Add missing fields from the sell bike form
    number_plate = forms.CharField(
        max_length=50,
        label="Number Plate",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., BA 12 PA 3456'})
    )
    
    previous_owners = forms.IntegerField(
        label="Number of Previous Owners",
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 1'})
    )
    
    engine_number = forms.CharField(
        max_length=50,
        label="Engine Number",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter engine number'})
    )
    
    chassis_number = forms.CharField(
        max_length=50,
        label="Chassis Number",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter chassis number'})
    )
    
    color = forms.CharField(
        max_length=30,
        label="Vehicle Color",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Red, Black, Blue'})
    )
    
    # Override price field to add Rs prefix
    price = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        label="Price",
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Expected price',
            'min': '0'
        })
    )
    
    # Override engine_size field to add cc suffix
    engine_size = forms.CharField(
        max_length=50,
        label="Engine Size",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Engine size (e.g., 150)'})
    )
    
    class Meta:
        model = Product
        fields = ['title', 'brand', 'price', 'condition', 'made_year', 'kilometers', 'engine_size', 
                 'engine_number', 'chassis_number', 'color', 'number_plate', 'previous_owners',
                 'location', 'seller_name', 'product_image', 'bluebook_page2', 'bluebook_page9']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Honda CB Shine 125cc'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Expected price'}),
            'kilometers': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Kilometers ridden'}),
            'engine_size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Engine size in cc'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City or area'}),
            'seller_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Owner name'}),
            'product_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'bluebook_page2': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'bluebook_page9': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

# Product Admin
class ProductModelAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ['id', 'title', 'brand', 'price', 'condition', 'made_year', 'location', 'seller_name', 'display_image', 'status', 'verification_status']
    list_filter = ['brand', 'condition', 'made_year', 'location', 'status', 'verification_status']
    search_fields = ['title', 'brand', 'seller_name']
    list_per_page = 20
    ordering = ['-id']
    readonly_fields = ['display_large_image', 'display_bluebook_images']
    actions = ['approve_products', 'reject_products', 'mark_as_sold', 'mark_as_available']
    
    # Override the default admin templates
    change_form_template = 'admin/product_form.html'
    
    # Custom class attributes for the template
    object_history_template = None  # Hide history button
    
    def get_fieldsets(self, request, obj=None):
        """Override the fieldsets to customize the form layout"""
        if request.GET.get('_popup'):
            # Using default fieldsets in popup mode
            return super().get_fieldsets(request, obj)
        return []  # Return empty fieldsets to use our custom template

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Customize the change view to use our template"""
        extra_context = extra_context or {}
        extra_context['show_save'] = False  # Hide default save buttons
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        extra_context['show_delete_link'] = False
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
    
    def add_view(self, request, form_url='', extra_context=None):
        """Customize the add view to use our template"""
        extra_context = extra_context or {}
        extra_context['show_save'] = False  # Hide default save buttons
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        return super().add_view(request, form_url, extra_context=extra_context)
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['title', 'brand', 'price', 'condition'],
            'description': 'Enter the basic details of the bike',
        }),
        ('Specifications', {
            'fields': ['made_year', 'kilometers', 'engine_size', 'engine_number', 'chassis_number', 'color'],
            'description': 'Enter the technical specifications of the bike',
        }),
        ('Vehicle Details', {
            'fields': ['number_plate', 'previous_owners'],
            'description': 'Enter vehicle registration and ownership details',
        }),
        ('Seller Information', {
            'fields': ['seller_name', 'location'],
            'description': 'Enter the owner name and location',
        }),
        ('Bike Image', {
            'fields': ['product_image', 'display_large_image'],
            'description': 'Upload a clear image of the bike (required)',
        }),
        ('Bluebook Images', {
            'fields': ['bluebook_page2', 'bluebook_page9', 'display_bluebook_images'],
            'description': 'Upload images of bluebook page 2 and page 9 for verification',
        }),
        ('Status Information', {
            'fields': ['status', 'verification_status'],
            'description': 'Set the product status and verification status',
        }),
    ]
    
    def display_image(self, obj):
        if obj.product_image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.product_image.url)
        return 'No Image'
    display_image.short_description = 'Image'
    
    def display_large_image(self, obj):
        if obj.product_image:
            return format_html('<img src="{}" width="300" style="max-height: 300px; object-fit: contain;" />', obj.product_image.url)
        return 'No Image'
    display_large_image.short_description = 'Product Image Preview'
    
    def display_bluebook_images(self, obj):
        html = '<div style="display: flex; gap: 20px;">'
        if obj.bluebook_page2:
            html += format_html('<div><h4>Bluebook Page 2</h4><a href="{}" target="_blank"><img src="{}" width="300" style="max-height: 300px; object-fit: contain; border: 1px solid #ddd; padding: 5px;" /></a><br/><a href="{}" class="button" target="_blank">View Full Size</a></div>', 
                              obj.bluebook_page2.url, obj.bluebook_page2.url, obj.bluebook_page2.url)
        if obj.bluebook_page9:
            html += format_html('<div><h4>Bluebook Page 9</h4><a href="{}" target="_blank"><img src="{}" width="300" style="max-height: 300px; object-fit: contain; border: 1px solid #ddd; padding: 5px;" /></a><br/><a href="{}" class="button" target="_blank">View Full Size</a></div>', 
                              obj.bluebook_page9.url, obj.bluebook_page9.url, obj.bluebook_page9.url)
        html += '</div>'
        if not obj.bluebook_page2 and not obj.bluebook_page9:
            return 'No Bluebook Images'
        return format_html(html)
    display_bluebook_images.short_description = 'Bluebook Images Preview'
    
    def approve_products(self, request, queryset):
        updated = queryset.update(verification_status='approved', status='available')
        self.message_user(request, f'{updated} product(s) have been approved and are now visible on the Buy page.')
    approve_products.short_description = "Approve selected products"
    
    def reject_products(self, request, queryset):
        updated = queryset.update(verification_status='rejected')
        self.message_user(request, f'{updated} product(s) have been rejected.')
    reject_products.short_description = "Reject selected products"
    
    def mark_as_sold(self, request, queryset):
        updated = queryset.update(status='sold')
        self.message_user(request, f'{updated} product(s) have been marked as sold.')
    mark_as_sold.short_description = "Mark selected products as sold"
    
    def mark_as_available(self, request, queryset):
        updated = queryset.update(status='available')
        self.message_user(request, f'{updated} product(s) have been marked as available.')
    mark_as_available.short_description = "Mark selected products as available"

# Customer Admin
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'user_email', 'mobile', 'city', 'state', 'delete_customer']
    list_filter = ['state', 'city']
    search_fields = ['name', 'user__email', 'mobile', 'city']
    list_per_page = 20
    actions = ['delete_selected_customers']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def delete_customer(self, obj):
        if obj.user.is_superuser:
            return "Cannot delete admin"
        return format_html(
            '<a class="btn btn-danger btn-sm" href="{}" onclick="return confirm(\'Are you sure you want to delete this customer? This will also delete their user account.\')">'
            '<i class="fas fa-trash"></i> Delete</a>',
            reverse('admin:proj_customer_delete', args=[obj.id])
        )
    delete_customer.short_description = 'Actions'
    
    def delete_selected_customers(self, request, queryset):
        # Don't allow deleting superusers
        non_superusers = queryset.exclude(user__is_superuser=True)
        count = 0
        for customer in non_superusers:
            try:
                # Delete the associated user account
                user = customer.user
                customer.delete()
                user.delete()
                count += 1
            except Exception as e:
                self.message_user(request, f"Error deleting customer {customer.name}: {str(e)}", level='error')
        
        self.message_user(request, f"Successfully deleted {count} customers.")
    delete_selected_customers.short_description = "Delete selected customers"
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deleting superusers
        if obj and obj.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

# Wishlist Admin
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'customer_phone', 'product_title', 'product_brand', 'product_price', 'product_image']
    list_filter = ['user', 'product__brand']
    search_fields = ['user__username', 'product__title', 'user__customers__mobile', 'product__brand']
    list_per_page = 20
    
    def customer_name(self, obj):
        # Try to get the customer name from the Customer model if it exists
        customer = Customer.objects.filter(user=obj.user).first()
        if customer and customer.name:
            return format_html('<a href="{}">{}</a>', 
                             reverse('admin:proj_customer_change', args=[customer.id]), 
                             customer.name)
        # Fallback to username if no customer record or name is empty
        return obj.user.username
    customer_name.short_description = 'Customer Name'
    
    def customer_phone(self, obj):
        # Get the customer's phone number if available
        customer = Customer.objects.filter(user=obj.user).first()
        if customer and customer.mobile:
            return customer.mobile
        return 'Not provided'
    customer_phone.short_description = 'Phone Number'
    
    def product_title(self, obj):
        return format_html('<a href="{}">{}</a>', 
                          reverse('admin:proj_product_change', args=[obj.product.id]), 
                          obj.product.title)
    product_title.short_description = 'Product Title'
    
    def product_brand(self, obj):
        return obj.product.brand
    product_brand.short_description = 'Brand'
    
    def product_price(self, obj):
        return f'Rs. {obj.product.price}'
    product_price.short_description = 'Price'
    
    def product_image(self, obj):
        if obj.product.product_image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', 
                              obj.product.product_image.url)
        return 'No Image'
    product_image.short_description = 'Image'

# Custom SellerInfo Admin Form
class SellerInfoAdminForm(forms.ModelForm):
    # Match fields from the frontend SellBikeForm
    BRAND_CHOICES = [
        ('', 'Select Brand'),
        ('HONDA', 'Honda'),
        ('YAMAHA', 'Yamaha'),
        ('BAJAJ', 'Bajaj'),
        ('HERO', 'Hero'),
        ('TVS', 'TVS'),
    ]
    
    CONDITION_CHOICES = [
        ('', 'Select Condition'),
        ('Like New', 'Like New'),
        ('Excellent', 'Excellent'),
        ('Good', 'Good'),
        ('Fair', 'Fair'),
        ('Poor', 'Poor'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('pending', 'Pending'),
        ('reserved', 'Reserved'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    CURRENT_YEAR = datetime.datetime.now().year
    YEAR_CHOICES = [(year, str(year)) for year in range(CURRENT_YEAR, 1949, -1)]
    
    # Add customer lookup fields
    lookup_customer = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by email or phone'}),
        help_text="Enter email or phone to find existing customer"
    )
    
    # Make email, phone, and full_name read-only
    full_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        help_text="Owner name is read-only"
    )
    
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        help_text="Email is fetched from customer profile and is read-only"
    )
    
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        help_text="Phone is fetched from customer profile and is read-only"
    )
    
    # Add fields to match the frontend form
    bike_brand = forms.ChoiceField(
        choices=BRAND_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    bike_model = forms.CharField(
        max_length=100,
        required=True,
        label="Model",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Add product fields for direct management
    price = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Product price'})
    )
    
    made_year = forms.IntegerField(
        required=False,
        widget=forms.Select(choices=YEAR_CHOICES, attrs={'class': 'form-select'}),
        help_text="Year of manufacturing"
    )
    
    kilometers = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Kilometers driven'})
    )
    
    engine_size = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Engine size in cc'})
    )
    
    condition = forms.ChoiceField(
        choices=CONDITION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'})
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Product description'})
    )
    
    product_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label="Product Status",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    product_verification_status = forms.ChoiceField(
        choices=VERIFICATION_STATUS_CHOICES,
        required=False,
        label="Verification Status",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Add a product selection field
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select an existing product or leave blank to create a new one"
    )
    
    # Add image upload fields - these are not model fields, just form fields
    product_image_upload = forms.ImageField(
        required=False,
        label="Bike Image",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        help_text="Upload a photo of the bike"
    )
    
    bluebook_page2_upload = forms.ImageField(
        required=False,
        label="Bluebook Page 2 Image",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        help_text="Upload bluebook page 2 image"
    )
    
    bluebook_page9_upload = forms.ImageField(
        required=False,
        label="Bluebook Page 9 Image",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        help_text="Upload bluebook page 9 image"
    )
    
    class Meta:
        model = SellerInfo
        fields = ['full_name', 'email', 'phone', 'bike_brand', 'bike_model', 'product', 'status', 'verification_status']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

# SellerInfo Admin
class SellerInfoAdmin(admin.ModelAdmin):
    form = SellerInfoAdminForm
    # List display shows product owner, customer details, and product details
    list_display = ['id', 'full_name', 'customer_email', 'customer_phone', 'bike_brand', 
                    'get_product_title', 'get_product_made_year', 'get_product_kilometers', 
                    'get_product_engine_size', 'get_product_engine_number', 'get_product_chassis_number', 
                    'get_product_color', 'get_product_condition', 'get_product_location', 
                    'get_product_price', 'get_product_seller_name', 
                    'display_number_plate', 'display_previous_owners', 
                    'linked_product_image', 'linked_bluebook_image', 'product_verification_status', 'product_status', 'created_at']
    list_filter = ['bike_brand', 'verification_status', 'status', 'created_at', 'product__verification_status', 'product__status', 'product__made_year', 'product__condition', 'product__location']
    search_fields = ['full_name', 'email', 'phone', 'bike_model', 'bike_brand', 'product__title', 'product__engine_number', 'product__chassis_number', 'product__color', 'product__location', 'product__seller_name', 'product__number_plate']
    list_per_page = 20
    readonly_fields = ['customer_details', 'product_preview', 'bluebook_preview', 'created_at']
    actions = ['verify_and_publish_products', 'reject_products', 'mark_products_as_sold']
    
    # Allow adding new seller info entries
    def has_add_permission(self, request):
        return True
    
    fieldsets = [
        ('Customer Information', {
            'fields': ['lookup_customer', 'full_name', 'email', 'phone', 'customer_details'],
            'description': 'Customer details'
        }),
        ('Bike Information', {
            'fields': ['bike_brand', 'bike_model', 'price', 'condition', 'made_year', 'kilometers', 'engine_size', 'location', 'description'],
            'description': 'Bike details'
        }),
        ('Status Management', {
            'fields': [('status', 'verification_status'), 'created_at', ('product_status', 'product_verification_status')],
            'description': 'Set the verification status of this bike listing and related product'
        }),
        ('Product Images', {
            'fields': ['product_image_upload', 'bluebook_page2_upload', 'bluebook_page9_upload'],
            'description': 'Upload product images'
        }),
        ('Product Management', {
            'fields': ['product', 'product_preview', 'bluebook_preview'],
            'description': 'Link to the associated product or preview of a newly created one'
        }),
    ]
    
    def product_status(self, obj):
        if obj.product and obj.product.status:
            status = obj.product.status
            if status == 'available':
                return format_html('<span style="color: green; font-weight: bold;">Available</span>')
            elif status == 'sold':
                return format_html('<span style="color: blue; font-weight: bold;">Sold</span>')
            elif status == 'pending':
                return format_html('<span style="color: orange; font-weight: bold;">Pending</span>')
            else:
                return format_html('<span>{}</span>', status)
        return 'No product linked'
    product_status.short_description = 'Product Status'
    
    def product_verification_status(self, obj):
        if obj.product and obj.product.verification_status:
            status = obj.product.verification_status
            if status == 'approved':
                return format_html('<span style="color: green; font-weight: bold;">Approved</span>')
            elif status == 'rejected':
                return format_html('<span style="color: red; font-weight: bold;">Rejected</span>')
            else:
                return format_html('<span style="color: orange; font-weight: bold;">Pending</span>')
        return 'No product linked'
    product_verification_status.short_description = 'Verification Status'
    
    def display_number_plate(self, obj):
        if obj.product:
            return obj.product.number_plate
        return "N/A"
    display_number_plate.short_description = 'Number Plate'

    def display_previous_owners(self, obj):
        if obj.product is not None:
            return obj.product.previous_owners
        return "N/A"
    display_previous_owners.short_description = 'Previous Owners'
    
    def verify_and_publish_products(self, request, queryset):
        for seller_info in queryset:
            if seller_info.product:
                seller_info.product.verification_status = 'approved'
                seller_info.product.status = 'available'
                seller_info.product.save()
                seller_info.verification_status = 'verified'
                seller_info.save()
        
        self.message_user(request, f'{queryset.count()} seller listing(s) have been verified and their products published.')
    verify_and_publish_products.short_description = "Verify and publish selected listings"
    
    def reject_products(self, request, queryset):
        for seller_info in queryset:
            if seller_info.product:
                seller_info.product.verification_status = 'rejected'
                seller_info.product.save()
                seller_info.verification_status = 'rejected'
                seller_info.save()
        
        self.message_user(request, f'{queryset.count()} seller listing(s) have been rejected.')
    reject_products.short_description = "Reject selected listings"
    
    def mark_products_as_sold(self, request, queryset):
        for seller_info in queryset:
            if seller_info.product:
                seller_info.product.status = 'sold'
                seller_info.product.save()
                seller_info.status = 'completed'
                seller_info.save()
        
        self.message_user(request, f'{queryset.count()} seller listing(s) have been marked as sold.')
    mark_products_as_sold.short_description = "Mark selected listings as sold"
    
    def save_model(self, request, obj, form, change):
        # Get form data
        product_image = form.cleaned_data.get('product_image_upload')
        bluebook_page2 = form.cleaned_data.get('bluebook_page2_upload')
        bluebook_page9 = form.cleaned_data.get('bluebook_page9_upload')
        selected_product = form.cleaned_data.get('product')
        
        # Extract product data from form
        price = form.cleaned_data.get('price')
        made_year = form.cleaned_data.get('made_year')
        kilometers = form.cleaned_data.get('kilometers')
        engine_size = form.cleaned_data.get('engine_size')
        condition = form.cleaned_data.get('condition')
        location = form.cleaned_data.get('location')
        description = form.cleaned_data.get('description')
        product_status = form.cleaned_data.get('product_status')
        product_verification_status = form.cleaned_data.get('product_verification_status')
        
        # If a product is selected, use it; otherwise create a new one
        if not selected_product and form.cleaned_data.get('bike_model'):
            # Create a new product with all available information
            product = Product(
                title=form.cleaned_data.get('bike_model'),
                brand=form.cleaned_data.get('bike_brand'),
                price=price or 0,  # Use form value or default
                condition=condition or "Good",  # Use form value or default
                made_year=made_year or datetime.datetime.now().year,  # Use form value or default
                kilometers=kilometers or 0,  # Use form value or default
                engine_size=engine_size or 0,  # Use form value or default
                location=location or "",  # Use form value or default
                seller_name=form.cleaned_data.get('full_name'),
                description=description or "Added via admin panel",
                status=product_status or 'pending',
                verification_status=product_verification_status or 'pending'
            )
            
            # Save the product first to get an ID
            product.save()
            
            # Assign images if provided
            if product_image:
                product.product_image = product_image
            if bluebook_page2:
                product.bluebook_page2 = bluebook_page2
            if bluebook_page9:
                product.bluebook_page9 = bluebook_page9
                
            # Save the product again with images
            product.save()
            
            # Link the product to the seller info
            obj.product = product
        elif selected_product:
            # Update the selected product with new data if provided
            if form.cleaned_data.get('bike_model'):
                selected_product.title = form.cleaned_data.get('bike_model')
            if form.cleaned_data.get('bike_brand'):
                selected_product.brand = form.cleaned_data.get('bike_brand')
            if form.cleaned_data.get('full_name'):
                selected_product.seller_name = form.cleaned_data.get('full_name')
                
            # Update other product fields if provided
            if price is not None:
                selected_product.price = price
            if made_year is not None:
                selected_product.made_year = made_year
            if kilometers is not None:
                selected_product.kilometers = kilometers
            if engine_size:
                selected_product.engine_size = engine_size
            if condition:
                selected_product.condition = condition
            if location:
                selected_product.location = location
            if description:
                selected_product.description = description
            if product_status:
                selected_product.status = product_status
            if product_verification_status:
                selected_product.verification_status = product_verification_status
                
            # Update images if provided
            if product_image:
                selected_product.product_image = product_image
            if bluebook_page2:
                selected_product.bluebook_page2 = bluebook_page2
            if bluebook_page9:
                selected_product.bluebook_page9 = bluebook_page9
                
            # Save the updated product
            selected_product.save()
            
            # Update the seller info with the selected product
            obj.product = selected_product
        
        # If the product verification status has changed, update seller info status accordingly
        if obj.product:
            if obj.product.verification_status == 'approved' and obj.verification_status != 'verified':
                obj.verification_status = 'verified'
            elif obj.product.verification_status == 'rejected' and obj.verification_status != 'rejected':
                obj.verification_status = 'rejected'
        
        # Save the seller info object
        super().save_model(request, obj, form, change)
    
    # Add custom JavaScript for customer lookup
    class Media:
        js = ('admin/js/seller_admin.js',)
    
    def customer_email(self, obj):
        # Try to find a matching customer by email
        customer = Customer.objects.filter(user__email=obj.email).first()
        if customer:
            return format_html('<a href="{}">{}</a>', 
                              reverse('admin:proj_customer_change', args=[customer.id]), 
                              obj.email)
        return obj.email
    customer_email.short_description = 'Email'
    
    def customer_phone(self, obj):
        # Try to find a matching customer by phone
        customer = Customer.objects.filter(mobile=obj.phone).first()
        if customer:
            return format_html('<a href="{}">{}</a>', 
                              reverse('admin:proj_customer_change', args=[customer.id]), 
                              obj.phone)
        return obj.phone
    customer_phone.short_description = 'Phone'
    
    def linked_product(self, obj):
        if obj.product:
            return format_html('<a href="{}">{}</a>', 
                              reverse('admin:proj_product_change', args=[obj.product.id]), 
                              obj.product.title)
        return 'No product linked'
    linked_product.short_description = 'Product'
    
    def linked_product_image(self, obj):
        if obj.product and obj.product.product_image:
            return format_html('<a href="{}" target="_blank"><img src="{}" width="50" height="50" style="object-fit: cover;" /></a>', 
                              obj.product.product_image.url, obj.product.product_image.url)
        return 'No Image'
    linked_product_image.short_description = 'Product Image'
    
    def linked_bluebook_image(self, obj):
        if obj.product and obj.product.bluebook_page9:
            return format_html('<a href="{}" target="_blank"><img src="{}" width="50" height="50" style="object-fit: cover;" /></a>', 
                              obj.product.bluebook_page9.url, obj.product.bluebook_page9.url)
        return 'No Image'
    linked_bluebook_image.short_description = 'Bluebook Image'
    
    # Methods to get product attributes for list_display
    def get_product_title(self, obj):
        if obj.product:
            return obj.product.title
        return "N/A"
    get_product_title.short_description = 'Title'
    
    def get_product_made_year(self, obj):
        if obj.product:
            return obj.product.made_year
        return "N/A"
    get_product_made_year.short_description = 'Year'
    
    def get_product_kilometers(self, obj):
        if obj.product:
            return obj.product.kilometers
        return "N/A"
    get_product_kilometers.short_description = 'Kilometers'
    
    def get_product_engine_size(self, obj):
        if obj.product:
            return obj.product.engine_size
        return "N/A"
    get_product_engine_size.short_description = 'Engine Size'
    
    def get_product_engine_number(self, obj):
        if obj.product:
            return obj.product.engine_number
        return "N/A"
    get_product_engine_number.short_description = 'Engine Number'
    
    def get_product_chassis_number(self, obj):
        if obj.product:
            return obj.product.chassis_number
        return "N/A"
    get_product_chassis_number.short_description = 'Chassis Number'
    
    def get_product_color(self, obj):
        if obj.product:
            return obj.product.color
        return "N/A"
    get_product_color.short_description = 'Color'
    
    def get_product_condition(self, obj):
        if obj.product:
            return obj.product.condition
        return "N/A"
    get_product_condition.short_description = 'Condition'
    
    def get_product_location(self, obj):
        if obj.product:
            return obj.product.location
        return "N/A"
    get_product_location.short_description = 'Location'
    
    def get_product_price(self, obj):
        if obj.product:
            return obj.product.price
        return "N/A"
    get_product_price.short_description = 'Price'
    
    def get_product_seller_name(self, obj):
        if obj.product:
            return obj.product.seller_name
        return "N/A"
    get_product_seller_name.short_description = 'Seller Name'
    
    def customer_details(self, obj):
        # Try to find a matching customer
        customer = Customer.objects.filter(user__email=obj.email).first() or Customer.objects.filter(mobile=obj.phone).first()
        if customer:
            return format_html(
                '<div style="padding: 10px; background-color: #f8f9fa; border-radius: 5px;">' 
                '<h4>Customer Profile</h4>' 
                '<p><strong>Name:</strong> {}</p>' 
                '<p><strong>Email:</strong> {}</p>' 
                '<p><strong>Phone:</strong> {}</p>' 
                '<p><strong>Location:</strong> {}, {}</p>' 
                '<p><a href="{}" class="button">View Full Profile</a></p>' 
                '</div>',
                customer.name,
                customer.user.email,
                customer.mobile,
                customer.city,
                customer.state,
                reverse('admin:proj_customer_change', args=[customer.id])
            )
        return 'No matching customer profile found.'
    customer_details.short_description = 'Customer Profile'
    
    def product_preview(self, obj):
        if obj.product and obj.product.product_image:
            return format_html('<img src="{}" width="300" style="max-height: 300px; object-fit: contain;" />', 
                              obj.product.product_image.url)
        return 'No product image available'
    product_preview.short_description = 'Product Image Preview'
    
    def bluebook_preview(self, obj):
        html = '<div style="display: flex; gap: 20px;">'
        if obj.product and obj.product.bluebook_page2:
            html += format_html('<div><h4>Bluebook Page 2</h4><a href="{}" target="_blank"><img src="{}" width="300" style="max-height: 300px; object-fit: contain; border: 1px solid #ddd; padding: 5px;" /></a><br/><a href="{}" class="button" target="_blank">View Full Size</a></div>', 
                               obj.product.bluebook_page2.url, obj.product.bluebook_page2.url, obj.product.bluebook_page2.url)
        if obj.product and obj.product.bluebook_page9:
            html += format_html('<div><h4>Bluebook Page 9</h4><a href="{}" target="_blank"><img src="{}" width="300" style="max-height: 300px; object-fit: contain; border: 1px solid #ddd; padding: 5px;" /></a><br/><a href="{}" class="button" target="_blank">View Full Size</a></div>', 
                               obj.product.bluebook_page9.url, obj.product.bluebook_page9.url, obj.product.bluebook_page9.url)
        html += '</div>'
        if not (obj.product and (obj.product.bluebook_page2 or obj.product.bluebook_page9)):
            return 'No bluebook images available'
        return format_html(html)
    bluebook_preview.short_description = 'Bluebook Images Preview'

# BikePaymentTransaction Admin
class BikePaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['purchase_order_id', 'get_product_title', 'get_buyer_name', 'amount', 'status', 'created_at', 'payment_method']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['purchase_order_id', 'pidx', 'product__title', 'buyer__username', 'buyer__email']
    readonly_fields = ['purchase_order_id', 'pidx', 'transaction_id', 'created_at', 'updated_at']
    list_per_page = 20
    ordering = ['-created_at']

    actions = ['download_invoice']

    def download_invoice(self, request, queryset):
        if queryset.count() == 1:
            obj = queryset.first()
            return redirect(f'./download-invoice/{obj.purchase_order_id}/')
        else:
            self.message_user(request, "Please select exactly one transaction to download the invoice.", level='error')
    download_invoice.short_description = "Download Invoice PDF"

    def get_product_title(self, obj):
        return obj.product.title
    get_product_title.short_description = 'Product'
    
    def get_buyer_name(self, obj):
        return f"{obj.buyer.username} ({obj.buyer.email})"
    get_buyer_name.short_description = 'Buyer'

# Register all models with our custom admin site
admin_site.register(Product, ProductModelAdmin)
admin_site.register(Customer, CustomerModelAdmin)
admin_site.register(Wishlist, WishlistAdmin)
admin_site.register(SellerInfo, SellerInfoAdmin)
admin_site.register(BikePaymentTransaction, BikePaymentTransactionAdmin)

# Register User model from django.contrib.auth
admin_site.register(User)
