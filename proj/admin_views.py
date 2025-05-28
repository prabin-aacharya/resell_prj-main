from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from .models import Product, Customer, Wishlist, SellerInfo, BikePaymentTransaction
from django.contrib.auth.models import User
from .forms import ProductForm, SellerInfoForm, AdminCustomerCreateForm

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = '/admin/login/'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, "You need admin privileges to access this page.")
        return redirect(self.login_url)

@user_passes_test(is_admin, login_url='/admin/login/')
def admin_dashboard(request):
    # Get statistics for the dashboard
    total_products = Product.objects.count()
    total_customers = Customer.objects.count()
    total_sellers = SellerInfo.objects.count()
    
    # Recent products
    recent_products = Product.objects.order_by('-id')[:5]
    
    # Sales statistics
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    monthly_sales = Order.objects.filter(
        order_date__date__gte=thirty_days_ago,
        status='completed'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Recent actions for admin activity feed
    from django.contrib.admin.models import LogEntry
    recent_actions = LogEntry.objects.select_related('user', 'content_type').order_by('-action_time')[:10]
    
    context = {
        'product_count': total_products,
        'customer_count': total_customers,
        'wishlist_count': Wishlist.objects.count(),
        'seller_count': total_sellers,
        'recent_products': recent_products,
        'monthly_sales': monthly_sales,
        'recent_actions': recent_actions,
    }
    return render(request, 'admin/dashboard.html', context)

# Products Views
class ProductListView(AdminRequiredMixin, ListView):
    model = Product
    template_name = 'proj/admin/product_list.html'
    context_object_name = 'products'
    ordering = ['-created_at']
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Get search query and status filter from URL parameters
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        
        # Apply filters if they exist
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(brand__icontains=search_query) | 
                Q(location__icontains=search_query) |
                Q(seller_name__icontains=search_query)
            )
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset

class ProductCreateView(AdminRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'proj/admin/product_form.html'
    success_url = reverse_lazy('admin:admin_product_list')
    
    def form_valid(self, form):
        # Set admin info as seller if not provided
        product = form.save(commit=False)
        if not product.seller_name:
            product.seller_name = self.request.user.username
        product.save()
        # Create SellerInfo for admin if not exists
        from .models import SellerInfo
        if not SellerInfo.objects.filter(product=product).exists():
            SellerInfo.objects.create(
                full_name=self.request.user.get_full_name() or self.request.user.username,
                email=self.request.user.email,
                phone='9840587573',
                bike_brand=product.brand,
                bike_model=product.title,
                product=product,
                status='completed',
                verification_status='verified',
            )
        messages.success(self.request, "Product created successfully!")
        return redirect(self.success_url)

class ProductUpdateView(AdminRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'proj/admin/product_form.html'
    success_url = reverse_lazy('admin:admin_product_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        product = self.object
        seller_infos = SellerInfo.objects.filter(product=product)
        if seller_infos.exists():
            for seller_info in seller_infos:
                # Update SellerInfo fields based on product
                seller_info.bike_brand = product.brand
                seller_info.bike_model = product.title
                # Update number plate and previous owners
                seller_info_number_plate = getattr(product, 'number_plate', None)
                if seller_info_number_plate is not None:
                    seller_info.number_plate = seller_info_number_plate
                seller_info_previous_owners = getattr(product, 'previous_owners', None)
                if seller_info_previous_owners is not None:
                    seller_info.previous_owners = seller_info_previous_owners
                # Update verification status to match product
                if product.verification_status == 'approved':
                    seller_info.verification_status = 'verified'
                elif product.verification_status == 'rejected':
                    seller_info.verification_status = 'rejected'
                # Update status to match product
                if product.status == 'sold':
                    seller_info.status = 'completed'
                elif product.status == 'available':
                    seller_info.status = 'completed'  # Completed means listing process is done
                seller_info.save()
            messages.success(self.request, f"Product and {seller_infos.count()} associated seller listing(s) updated successfully!")
        else:
            messages.success(self.request, "Product updated successfully!")
        # Ensure available products are approved
        if product.status == 'available' and product.verification_status != 'approved':
            product.verification_status = 'approved'
            product.save()
        return response
    
    def form_invalid(self, form):
        # Log detailed form errors
        error_msg = "Product update failed. Please check the following errors:\n"
        for field, errors in form.errors.items():
            error_msg += f"- {field}: {', '.join(errors)}\n"
        messages.error(self.request, error_msg)
        return super().form_invalid(form)
        
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Ensure the form knows it's for an existing instance
        if self.object and self.object.pk:
            form.instance = self.object
        return form

class ProductDeleteView(AdminRequiredMixin, DeleteView):
    model = Product
    template_name = 'proj/admin/product_confirm_delete.html'
    success_url = reverse_lazy('admin:admin_product_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Product deleted successfully!")
        return super().delete(request, *args, **kwargs)

class ProductDetailView(AdminRequiredMixin, DetailView):
    model = Product
    template_name = 'proj/admin/product_detail.html'
    context_object_name = 'product'

# Customers Views
class CustomerListView(AdminRequiredMixin, ListView):
    model = Customer
    template_name = 'proj/admin/customer_list.html'
    context_object_name = 'customers'
    ordering = ['name']
    paginate_by = 10

class CustomerUpdateView(AdminRequiredMixin, UpdateView):
    model = Customer
    template_name = 'proj/admin/customer_form.html'
    fields = ['name', 'gender', 'city', 'state', 'mobile', 'zipcode']
    success_url = reverse_lazy('admin:admin_customer_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Customer information updated successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = False  # Indicate that this is an update form
        return context

class CustomerDetailView(AdminRequiredMixin, UpdateView):
    model = Customer
    template_name = 'proj/admin/customer_detail.html'
    fields = ['name', 'gender', 'city', 'state', 'mobile', 'zipcode']
    context_object_name = 'customer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.get_object()
        
        # Get customer's purchase transactions
        context['purchases'] = BikePaymentTransaction.objects.filter(buyer=customer.user).select_related('product')
        
        # Get customer's wishlist
        context['wishlist_items'] = Wishlist.objects.filter(user=customer.user).select_related('product')
        
        return context
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class CustomerDeleteView(AdminRequiredMixin, DeleteView):
    model = Customer
    template_name = 'admin/proj/customer/delete_confirmation.html'
    success_url = reverse_lazy('admin:admin_customer_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['opts'] = self.model._meta
        context['opts'].app_label = 'proj'  # Set app_label explicitly
        return context
        
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = self.object.user
        response = super().delete(request, *args, **kwargs)
        if user and not user.is_superuser:
            user.delete()
        messages.success(request, "Customer and associated user account deleted successfully!")
        return response

class CustomerCreateView(AdminRequiredMixin, CreateView):
    model = Customer
    form_class = AdminCustomerCreateForm
    template_name = 'proj/admin/customer_form.html'
    success_url = reverse_lazy('admin:admin_customer_list')

    def form_valid(self, form):
        try:
            customer = form.save()
            messages.success(self.request, f"Customer '{customer.name}' created successfully with user account.")
            return super(CreateView, self).form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error creating customer: {str(e)}")
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = True
        return context

# Wishlist Views
class WishlistListView(AdminRequiredMixin, ListView):
    model = Wishlist
    template_name = 'proj/admin/wishlist_list.html'
    context_object_name = 'wishlists'
    paginate_by = 10

    def get_queryset(self):
        return Wishlist.objects.select_related('user', 'product').all()

# Seller Info Views
class SellerInfoListView(AdminRequiredMixin, ListView):
    model = SellerInfo
    template_name = 'proj/admin/seller_info_list.html'
    context_object_name = 'sellers'
    ordering = ['-created_at']
    paginate_by = 10

class SellerInfoCreateView(AdminRequiredMixin, CreateView):
    model = SellerInfo
    form_class = SellerInfoForm
    template_name = 'proj/admin/seller_info_form.html'
    success_url = reverse_lazy('admin:admin_seller_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Seller information created successfully!")
        return super().form_valid(form)

class SellerInfoUpdateView(AdminRequiredMixin, UpdateView):
    model = SellerInfo
    form_class = SellerInfoForm
    template_name = 'proj/admin/seller_info_form.html'
    success_url = reverse_lazy('admin:admin_seller_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Seller information updated successfully!")
        return super().form_valid(form)

class SellerInfoDeleteView(AdminRequiredMixin, DeleteView):
    model = SellerInfo
    template_name = 'proj/admin/seller_info_confirm_delete.html'
    success_url = reverse_lazy('admin:admin_seller_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Seller information deleted successfully!")
        return super().delete(request, *args, **kwargs) 