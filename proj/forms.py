from django import forms
from django.core.validators import EmailValidator
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm,UsernameField,PasswordChangeForm,SetPasswordForm,PasswordResetForm
from django.contrib.auth.models import User
from .models import Customer

class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus' : 'True', 'class':'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocompete': 'current-password' ,'class':'form-control'}))



class CustomerRegistrationForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus' : 'True', 'class':'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={ 'class':'form-control'}))
    password1 = forms.CharField(label='Password',widget=forms.PasswordInput(attrs={'class':'form-control'}))
    password2 = forms.CharField(label='Confirm Password',widget=forms.PasswordInput(attrs={'class':'form-control'}))


    class Meta:
        model = User
        fields = ['username','email','password1','password2']



class MyPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(label='Old password',widget=forms.PasswordInput(attrs={'autofocus' : 'True', 'autocomplete':'current-password', 'class':'form-control'}))
    new_password1 = forms.CharField(label='New password',widget=forms.PasswordInput(attrs={'autocomplete':'current-password', 'class':'form-control'}))
    new_password2 = forms.CharField(label='Confirm password',widget=forms.PasswordInput(attrs={'autocomplete':'current-password', 'class':'form-control'}))
    

class MyPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control'}))
    

class MySetResetForm(SetPasswordForm):
    new_password1= forms.CharField(label='New password',widget=forms.PasswordInput(attrs={'autocomplete':'current-password', 'class':'form-control'}))
    new_password2= forms.CharField(label='Confirm New password',widget=forms.PasswordInput(attrs={'autocomplete':'current-password', 'class':'form-control'}))

from django import forms
from .models import Product

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)
    message = forms.CharField(widget=forms.Textarea, required=True)

from .models import Customer

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'city', 'state', 'mobile', 'zipcode']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-select'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'zipcode': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_mobile(self):
        mobile = self.cleaned_data['mobile']
        if len(mobile) != 10:
            raise forms.ValidationError("Mobile number must be 10 digits")
        return mobile

from datetime import datetime

BRAND_CHOICES = [
    ('', 'Select Brand'),  # Add blank first option
    ('HONDA', 'Honda'),
    ('YAMAHA', 'Yamaha'),
    ('BAJAJ', 'Bajaj'),
    ('HERO', 'Hero'),
    ('TVS', 'TVS'),
]

CONDITION_CHOICES = [
    ('', 'Select Condition'),  # Add blank first option
    ('USED', 'USED'),  # Changed to uppercase
    ('NEW', 'NEW'),  # Changed to uppercase
]

CURRENT_YEAR = datetime.now().year

class SellBikeForm(forms.Form):
    brand = forms.ChoiceField(
        choices=BRAND_CHOICES, 
        initial='',  # No default selection
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    model = forms.CharField(
        max_length=100, label="Model",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    made_year = forms.IntegerField(
        label="Year of manufacturing",
        min_value=1950,  # Reasonable lower bound
        max_value=CURRENT_YEAR,
        widget=forms.Select(
            choices=[(year, str(year)) for year in range(CURRENT_YEAR, 1949, -1)],
            attrs={'class': 'form-select'}
        )
    )
    kilometers = forms.IntegerField(
        label="Kms ridden",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    city = forms.CharField(
        max_length=100, label="City",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    price = forms.DecimalField(
        label="Expected price", max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    condition = forms.ChoiceField(
        choices=CONDITION_CHOICES, 
        initial='',  # No default selection
        label="Condition",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    engine_size = forms.CharField(
        max_length=20, label="Engine Size",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    seller_name = forms.CharField(
        max_length=100, label="Owner Name",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    product_image = forms.ImageField(
        label="Bike Image",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
    bluebook_page2 = forms.ImageField(
        label="Bluebook Page 2 Image",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
    bluebook_page9 = forms.ImageField(
        label="Bluebook Page 9 Image",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

class SellerInfoForm(forms.Form):
    full_name = forms.CharField(label="Name", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(label="Mobile number", max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    agree = forms.BooleanField(
        label="I agree with BikeWale sell bike Terms & Conditions, visitor agreement and privacy policy. I agree that by clicking 'List your bike' button, I am permitting buyers to contact me on my Mobile number.",
        required=True
    )