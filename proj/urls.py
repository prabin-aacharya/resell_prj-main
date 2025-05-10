from django.urls import path, include
from . import views, admin_views, payment_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .forms import LoginForm,MyPasswordResetForm,MyPasswordChangeForm,MySetResetForm
from .views import CustomLoginView

# Import our custom admin site
from proj.admin import admin_site

app_name = 'main'

urlpatterns = [
    path('admin/', admin_site.urls),  # Use our custom admin site
    
    # Admin functionality
    path('admin/lookup-customer/', views.admin_lookup_customer, name='admin_lookup_customer'),
    
    # Original URLs
    path('', views.home),
    path('about/', views.about,name='about'),
    path('contact/', views.contact,name='contact'),

    path('brand/<slug:val>', views.BrandView.as_view(),name="brand"),
    path('brand-title/<val>', views.BrandTitle.as_view(),name="brand-title"),

    path('product-detail/<int:pk>', views.ProductDetail.as_view(),name="product-detail"),

    path('profile/',views.ProfileView.as_view(),name='profile'),
    path('address/',views.address,name='address'),

    #login authentication
    path('registration/',views.CustomerRegistrationView.as_view(), name='customerregistration'),
    path('accounts/login/', CustomLoginView.as_view(template_name='proj/login.html', authentication_form=LoginForm), name='login'),
    path('passwordchange/', auth_views.PasswordChangeView.as_view(template_name='proj/changepassword.html', form_class=MyPasswordChangeForm, success_url='/passwordchange?success=true'),name='passwordchange'),
    path('logout/', auth_views.LogoutView.as_view(next_page='main:login'), name='logout'),

    path('password-reset/', auth_views.PasswordResetView.as_view (template_name='proj/password_reset.html', form_class=MyPasswordResetForm),name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view (template_name='proj/password_reset_done.html'),name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view (template_name='proj/password_reset_confirm.html', form_class=MySetResetForm),name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view (template_name='proj/password_reset_complete.html'),name='password_reset_complete'),

    path('sell/', views.sell_bike, name='sell_bike'),
    path('sell/success/', views.sell_success, name='sell_success'),
    path('buy/', views.buy_bikes, name='buy_bikes'),

    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    path('ajax/toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    path('check-uploaded-files/', views.check_uploaded_files, name='check_uploaded_files'),
    
    # Payment URLs
    path('payment/buy/', payment_views.initiate_bike_payment, name='initiate_bike_payment'),
    path('payment/verify/', payment_views.verify_bike_payment, name='verify_bike_payment'),
    path('payment/success/', payment_views.payment_success, name='payment_success'),
    path('payment/error/', payment_views.payment_error, name='payment_error'),
    
    # Terms and Privacy pages
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
]

# Add static and media URLs in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
