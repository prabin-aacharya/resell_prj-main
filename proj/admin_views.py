from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from .models import Product, Order, Customer, Wishlist, SellerInfo
from django.contrib.auth.models import User
from .forms import ProductForm, SellerInfoForm

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
    total_orders = Order.objects.count()
    total_customers = Customer.objects.count()
    total_sellers = SellerInfo.objects.count()
    
    # Recent orders
    recent_orders = Order.objects.select_related('customer', 'product').order_by('-order_date')[:5]
    
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
        'recent_orders': recent_orders,
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
        messages.success(self.request, "Product created successfully!")
        return super().form_valid(form)

class ProductUpdateView(AdminRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'proj/admin/product_form.html'
    success_url = reverse_lazy('admin:admin_product_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Product updated successfully!")
        return super().form_valid(form)

class ProductDeleteView(AdminRequiredMixin, DeleteView):
    model = Product
    template_name = 'proj/admin/product_confirm_delete.html'
    success_url = reverse_lazy('admin:admin_product_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Product deleted successfully!")
        return super().delete(request, *args, **kwargs)

# Orders Views
class OrderListView(AdminRequiredMixin, ListView):
    model = Order
    template_name = 'proj/admin/order_list.html'
    context_object_name = 'orders'
    ordering = ['-order_date']
    paginate_by = 10

class OrderUpdateView(AdminRequiredMixin, UpdateView):
    model = Order
    template_name = 'proj/admin/order_form.html'
    fields = ['status', 'payment_status', 'notes']
    success_url = reverse_lazy('admin:admin_order_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Order updated successfully!")
        return super().form_valid(form)

# Customers Views
class CustomerListView(AdminRequiredMixin, ListView):
    model = Customer
    template_name = 'proj/admin/customer_list.html'
    context_object_name = 'customers'
    ordering = ['name']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for customer in context['customers']:
            customer.order_count = Order.objects.filter(customer=customer).count()
            customer.total_spent = Order.objects.filter(
                customer=customer, 
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
        return context

class CustomerUpdateView(AdminRequiredMixin, UpdateView):
    model = Customer
    template_name = 'proj/admin/customer_form.html'
    fields = ['name', 'city', 'state', 'mobile', 'zipcode']
    success_url = reverse_lazy('admin:admin_customer_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Customer information updated successfully!")
        return super().form_valid(form)

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
    template_name = 'proj/admin/customer_form.html'
    fields = ['name', 'city', 'state', 'mobile', 'zipcode', 'user']
    success_url = reverse_lazy('admin:admin_customer_list')

    def form_valid(self, form):
        messages.success(self.request, "Customer created successfully!")
        return super().form_valid(form)

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