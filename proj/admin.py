from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.contrib.auth.models import User, Group
from django.contrib.admin.views.main import ChangeList
from django.db.models import Count, Sum
from . models import Product, Customer, Wishlist, SellerInfo, Order, BikePaymentTransaction
from .forms import SellBikeForm, SellerInfoForm
from django import forms
import datetime
from . import admin_views
from django.shortcuts import render, redirect
from django.contrib.auth import logout

# Customize admin site
admin.site.site_header = 'Bike Resell Admin'
admin.site.site_title = 'Bike Resell Admin Portal'
admin.site.index_title = 'Welcome to Bike Resell Admin Portal'

# Custom admin index view to add statistics
from django.contrib.admin.sites import AdminSite

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
            path('wishlists/', self.admin_view(admin_views.WishlistListView.as_view()), name='admin_wishlist_list'),
            path('sellers/', self.admin_view(admin_views.SellerInfoListView.as_view()), name='admin_seller_list'),
            path('sellers/create/', self.admin_view(admin_views.SellerInfoCreateView.as_view()), name='admin_seller_create'),
            path('sellers/<int:pk>/update/', self.admin_view(admin_views.SellerInfoUpdateView.as_view()), name='admin_seller_update'),
            path('sellers/<int:pk>/delete/', self.admin_view(admin_views.SellerInfoDeleteView.as_view()), name='admin_seller_delete'),
            path('logout/', self.logout_view, name='logout'),
        ]
        
        # Insert our custom URLs before the default admin URLs
        return custom_urls + urls
    
    def logout_view(self, request):
        """Custom logout view that redirects to the admin login page"""
        logout(request)
        return redirect('admin:login')
    
    def dashboard_view(self, request):
        """Custom dashboard view that displays statistics"""
        context = self.each_context(request)
        
        # Get statistics for dashboard
        context['product_count'] = Product.objects.count()
        context['customer_count'] = Customer.objects.count()
        context['wishlist_count'] = Wishlist.objects.count()
        context['seller_count'] = SellerInfo.objects.count()
        
        # Recent products
        context['recent_products'] = Product.objects.order_by('-id')[:5]
        
        # Recent customers
        context['recent_customers'] = Customer.objects.order_by('-id')[:5]
        
        # Recent orders
        context['recent_orders'] = Order.objects.select_related('customer', 'product').order_by('-order_date')[:5]
        
        # Recent actions for admin activity feed
        from django.contrib.admin.models import LogEntry
        context['recent_actions'] = LogEntry.objects.select_related('user', 'content_type').order_by('-action_time')[:10]
        
        return render(request, 'admin/dashboard.html', context)
    
    def index(self, request, extra_context=None):
        # Redirect to our custom dashboard
        return self.dashboard_view(request)

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
        ('USED', 'USED'),
        ('NEW', 'NEW'),
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
    
    made_year = forms.IntegerField(
        label="Year of manufacturing",
        required=True,
        widget=forms.Select(
            choices=YEAR_CHOICES,
            attrs={'class': 'form-select'}
        )
    )
    
    class Meta:
        model = Product
        fields = ['title', 'brand', 'price', 'condition', 'made_year', 'kilometers', 'engine_size', 'location', 'seller_name', 'description', 'product_image', 'bluebook_page2', 'bluebook_page9']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Honda CB Shine 125cc'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Expected price'}),
            'kilometers': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Kilometers ridden'}),
            'engine_size': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Engine size in cc'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City or area'}),
            'seller_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Owner name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Additional details about the bike'}),
            'product_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'bluebook_page2': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'bluebook_page9': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

# Product Admin
class ProductModelAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ['id', 'title', 'brand', 'price', 'condition', 'made_year', 'location', 'seller_name', 'display_image']
    list_filter = ['brand', 'condition', 'made_year', 'location']
    search_fields = ['title', 'brand', 'seller_name', 'description']
    list_per_page = 20
    ordering = ['-id']
    readonly_fields = ['display_large_image', 'display_bluebook_images']
    fieldsets = [
        ('Basic Information', {
            'fields': ['title', 'brand', 'price', 'condition'],
            'description': 'Enter the basic details of the bike',
        }),
        ('Specifications', {
            'fields': ['made_year', 'kilometers', 'engine_size'],
            'description': 'Enter the technical specifications of the bike',
        }),
        ('Seller Information', {
            'fields': ['seller_name', 'location'],
            'description': 'Enter the owner name and location',
        }),
        ('Description', {
            'fields': ['description'],
            'description': 'Provide additional details about the bike',
        }),
        ('Bike Image', {
            'fields': ['product_image', 'display_large_image'],
            'description': 'Upload a clear image of the bike (required)',
        }),
        ('Bluebook Images', {
            'fields': ['bluebook_page2', 'bluebook_page9', 'display_bluebook_images'],
            'description': 'Upload images of bluebook page 2 and page 9 for verification',
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
        ('USED', 'USED'),
        ('NEW', 'NEW'),
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
        fields = ['full_name', 'email', 'phone', 'bike_brand', 'bike_model', 'product']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

# SellerInfo Admin
class SellerInfoAdmin(admin.ModelAdmin):
    form = SellerInfoAdminForm
    # List display shows product owner, customer details, and product details
    list_display = ['id', 'full_name', 'customer_email', 'customer_phone', 'bike_brand', 'bike_model', 'linked_product_image', 'linked_bluebook_image']
    list_filter = ['bike_brand']
    search_fields = ['full_name', 'email', 'phone', 'bike_model']
    list_per_page = 20
    readonly_fields = ['customer_details', 'product_preview', 'bluebook_preview', 'email', 'phone', 'full_name']
    
    # Remove the ability to add new seller info entries
    def has_add_permission(self, request):
        return False
    
    fieldsets = [
        ('Seller Information', {
            'fields': ['lookup_customer', 'full_name', ('email', 'phone'), 'customer_details'],
            'description': 'Owner name, email, and phone are read-only',
        }),
        ('Bike Information', {
            'fields': ['bike_brand', 'bike_model', 'product']
        }),
        ('Upload Images', {
            'fields': ['product_image_upload', 'bluebook_page2_upload', 'bluebook_page9_upload'],
            'description': 'Upload images for the bike and bluebook pages',
        }),
        ('Image Previews', {
            'fields': ['product_preview', 'bluebook_preview'],
            'classes': ['collapse'],
        }),
    ]
    
    def save_model(self, request, obj, form, change):
        # Get form data
        product_image = form.cleaned_data.get('product_image_upload')
        bluebook_page2 = form.cleaned_data.get('bluebook_page2_upload')
        bluebook_page9 = form.cleaned_data.get('bluebook_page9_upload')
        selected_product = form.cleaned_data.get('product')
        
        # If a product is selected, use it; otherwise create a new one
        if not selected_product and form.cleaned_data.get('bike_model'):
            # Create a new product with basic information
            product = Product(
                title=form.cleaned_data.get('bike_model'),
                brand=form.cleaned_data.get('bike_brand'),
                price=0,  # Default price
                condition="USED",  # Default condition
                made_year=datetime.datetime.now().year,  # Current year as default
                kilometers=0,  # Default value
                engine_size=0,  # Default value
                location="",  # Empty location
                seller_name=form.cleaned_data.get('full_name'),
                description="Added via admin panel"
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

# Register all models with our custom admin site
admin_site.register(Product, ProductModelAdmin)
admin_site.register(Customer, CustomerModelAdmin)
admin_site.register(Wishlist, WishlistAdmin)
admin_site.register(SellerInfo, SellerInfoAdmin)

# Register User model from django.contrib.auth
admin_site.register(User)

@admin.register(BikePaymentTransaction)
class BikePaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['purchase_order_id', 'product', 'buyer', 'seller', 'amount', 'status', 'created_at']
    search_fields = ['purchase_order_id', 'product__title', 'buyer__username', 'seller__username']
    list_filter = ['status', 'created_at']
