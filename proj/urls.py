from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .forms import LoginForm,MyPasswordResetForm,MyPasswordChangeForm,MySetResetForm
from .views import CustomLoginView






urlpatterns = [
    path('', views.home),
    path('about/', views.about,name='about'),
    path('contact/', views.contact,name='contact'),



    path('brand/<slug:val>', views.BrandView.as_view(),name="brand"),
    path('brand-title/<val>', views.BrandTitle.as_view(),name="brand-title"),

    path('product-detail/<int:pk>', views.ProductDetail.as_view(),name="product-detail"),

    path('profile/',views.ProfileView.as_view(),name='profile'),
    path('address/',views.address,name='address'),
    path('updateAddress/<int:pk>',views.updateAddress.as_view(),name='updateAddress'),

    #login authentication
    path('registration/',views.CustomerRegistrationView.as_view(), name='customerregistration'),
    path('accounts/login/', CustomLoginView.as_view(template_name='proj/login.html', authentication_form=LoginForm), name='login'),
    path('passwordchange/', auth_views.PasswordChangeView.as_view (template_name='proj/changepassword.html', form_class=MyPasswordChangeForm, success_url='/passwordchangedone'),name='passwordchange'),
    path('passwordchangedone/', auth_views.PasswordChangeDoneView.as_view (template_name='proj/passwordchangedone.html'),name='passwordchangedone'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),




    path('password-reset/', auth_views.PasswordResetView.as_view (template_name='proj/password_reset.html', form_class=MyPasswordResetForm),name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view (template_name='proj/password_reset_done.html'),name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view (template_name='proj/password_reset_confirm.html', form_class=MySetResetForm),name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view (template_name='proj/password_reset_complete.html'),name='password_reset_complete'),

    path('sell/', views.sell_bike, name='sell_bike'),
    path('buy/', views.buy_bikes, name='buy_bikes'),

    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    path('ajax/toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    path('check-uploaded-files/', views.check_uploaded_files, name='check_uploaded_files'),




]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
