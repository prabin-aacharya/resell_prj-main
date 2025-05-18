from django import forms
from django.core.validators import EmailValidator, RegexValidator
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm,UsernameField,PasswordChangeForm,SetPasswordForm,PasswordResetForm
from django.contrib.auth.models import User
from .models import Customer, Product, SellerInfo
import re
import dns.resolver
from django.utils import timezone

class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus' : 'True', 'class':'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocompete': 'current-password' ,'class':'form-control'}))


# Regex patterns
USERNAME_PATTERN = r'^[a-zA-Z0-9_]{4,20}$'  # 4-20 characters, alphanumeric and underscore
EMAIL_PATTERN = r'^[a-zA-Z][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'  # Must start with a letter
PASSWORD_PATTERN = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'  # At least 8 chars, 1 letter, 1 number, 1 special char

def validate_email_domain(value):
    """Custom validator for email domains"""
    # Extract domain from email
    domain = value.split('@')[-1]
    
    # Check if domain is numeric-only
    if re.match(r'^[0-9.]+$', domain):
        raise forms.ValidationError('Email domain cannot be numeric-only.')
    
    # Check for valid TLD
    if not re.search(r'\.(com|org|net|edu|gov|mil|io|co|in|info|biz|np)$', domain.lower()):
        raise forms.ValidationError('Email must use a valid top-level domain (.com, .org, etc.)')
    
    # Check for disposable email domains
    disposable_domains = [
        'mailinator.com', 'tempmail.com', 'temp-mail.org', 'guerrillamail.com',
        'throwawaymail.com', 'yopmail.com', 'getnada.com', 'mailnesia.com',
        'dispostable.com', '10minutemail.com', 'trashmail.com', 'emailondeck.com'
    ]
    
    if domain.lower() in disposable_domains:
        raise forms.ValidationError('Disposable email addresses are not allowed.')
    
    # Check for minimum length of local part
    local_part = value.split('@')[0]
    if len(local_part) < 3:
        raise forms.ValidationError('Username part of email must be at least 3 characters.')
    
    return value

class CustomerRegistrationForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'autofocus': 'True', 
            'class': 'form-control',
            'pattern': USERNAME_PATTERN,
            'title': 'Username must be 4-20 characters and contain only letters, numbers, and underscores.',
            'oninput': 'this.setCustomValidity(""); if(!this.checkValidity()) this.setCustomValidity(this.title);'
        }),
        validators=[
            RegexValidator(
                regex=USERNAME_PATTERN,
                message='Username must be 4-20 characters and contain only letters, numbers, and underscores.',
                code='invalid_username'
            )
        ]
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'pattern': EMAIL_PATTERN,
            'title': 'Email must start with a letter and be a valid email address.',
            'oninput': 'this.setCustomValidity(""); if(!this.checkValidity()) this.setCustomValidity(this.title);'
        }),
        validators=[
            validate_email_domain,
            RegexValidator(
                regex=EMAIL_PATTERN,
                message='Email must start with a letter and be a valid email address.',
                code='invalid_email'
            )
        ]
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'pattern': PASSWORD_PATTERN,
            'title': 'Password must be at least 8 characters and include a letter, a number, and a special character.',
            'oninput': 'this.setCustomValidity(""); if(!this.checkValidity()) this.setCustomValidity(this.title);'
        }),
        validators=[
            RegexValidator(
                regex=PASSWORD_PATTERN,
                message='Password must be at least 8 characters and include a letter, a number, and a special character.',
                code='invalid_password'
            )
        ]
    )
    password2 = forms.CharField(
        label='Confirm Password', 
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'oninput': 'this.setCustomValidity(""); if(this.value !== document.getElementById("id_password1").value) this.setCustomValidity("Passwords do not match.");'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()  # Convert to lowercase
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('This email is already registered.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Additional custom validation if needed
        if username and len(username) < 4:
            raise forms.ValidationError('Username must be at least 4 characters long.')
        return username
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        # Additional custom validation
        if password:
            # Check for common passwords
            common_passwords = ['password', 'admin', '12345678', 'qwerty', 'letmein']
            if password.lower() in common_passwords:
                raise forms.ValidationError('This password is too common. Please choose a stronger password.')
        return password



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
    email = forms.EmailField(
        required=False, 
        disabled=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Customer
        fields = ['name', 'gender', 'city', 'state', 'mobile', 'zipcode']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-select'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'zipcode': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If instance is provided (editing mode) and it has a user
        if self.instance and hasattr(self.instance, 'user') and self.instance.user:
            # Set initial value for email from the associated user
            self.fields['email'].initial = self.instance.user.email

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
    description = forms.CharField(
        required=False,
        label="Description",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5})
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

from django.utils.safestring import mark_safe

class SellerInfoForm(forms.ModelForm):
    # Define the BRAND_CHOICES constant from the Product model
    BRAND_CHOICES = [
        ('', 'Select Brand'),
        ('HONDA', 'Honda'),
        ('YAMAHA', 'Yamaha'),
        ('BAJAJ', 'Bajaj'),
        ('HERO', 'Hero'),
        ('TVS', 'TVS'),
    ]
    
    # Override the bike_brand field to use choices
    bike_brand = forms.ChoiceField(
        choices=BRAND_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Include product field
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        required=False,
        empty_label="No associated product"
    )
    
    class Meta:
        model = SellerInfo
        fields = ['full_name', 'email', 'phone', 'bike_brand', 'bike_model', 
                  'status', 'verification_status', 'product']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'price', 'description', 'condition', 'made_year', 
                  'kilometers', 'engine_size', 'brand', 'location', 'seller_name', 
                  'product_image', 'bluebook_page2', 'bluebook_page9', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'made_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'kilometers': forms.NumberInput(attrs={'class': 'form-control'}),
            'engine_size': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'seller_name': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price
        
    def clean_made_year(self):
        year = self.cleaned_data.get('made_year')
        current_year = timezone.now().year
        if year < 1900 or year > current_year:
            raise forms.ValidationError(f"Year must be between 1900 and {current_year}.")
        return year

class AdminCustomerCreateForm(forms.ModelForm):
    """Form for admin to create a customer with associated user account"""
    # User account fields
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="The customer will use this password to log in."
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    # Override the name field to make it required and more prominent
    name = forms.CharField(
        label='Full Name',
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Customer
        fields = ['name', 'gender', 'city', 'state', 'mobile', 'zipcode']
        widgets = {
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-select'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'zipcode': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()  # Convert to lowercase
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('This email is already registered.')
        return email

    def clean_mobile(self):
        mobile = self.cleaned_data['mobile']
        if len(mobile) != 10:
            raise forms.ValidationError("Mobile number must be 10 digits")
        return mobile
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords don't match")
            
        return cleaned_data
    
    def save(self, commit=True):
        # Create the User instance
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1']
        )
        
        # Create the Customer instance
        customer = super().save(commit=False)
        customer.user = user
        
        if commit:
            customer.save()
            
        return customer