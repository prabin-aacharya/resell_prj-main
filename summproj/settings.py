"""
Django settings for summproj project.

Generated by 'django-admin startproject' using Django 5.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/



# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-(s3523=q07k=n#)+o$@+)pk=-#aiv9x@d7zf(&bk8u2nrmx2y9'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'proj',
    'proj.templatetags',
    'django_extensions',
    'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'proj.middleware.AdminSessionMiddleware',  # Custom middleware for separate admin/user sessions
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'proj.middleware.AllowAdminSessionForPDFMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'proj.middleware.TimezoneMiddleware',  # Set timezone to Nepal Standard Time
]

ROOT_URLCONF = 'summproj.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'proj', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'proj.context_processors.timezone_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'summproj.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kathmandu'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'proj', 'static'),
]

MEDIA_URL='/media/'
MEDIA_ROOT= BASE_DIR/'media'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = 'main:login'  # Redirect to login page after logout


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email configuration for account confirmation
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'prabinacharya573@gmail.com'
EMAIL_HOST_PASSWORD = 'qomswzrkqpnuzbhx'  #  app password here (without spaces)
DEFAULT_FROM_EMAIL = 'prabinacharya573@gmail.com'

# Password reset token timeout (in seconds)
PASSWORD_RESET_TIMEOUT = 86400  # 24 hours

# Session configuration
SESSION_COOKIE_NAME = 'sessionid'  # Default session cookie name
ADMIN_SESSION_COOKIE_NAME = 'admin_sessionid'  # Admin session cookie name

# Session settings
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Don't expire when browser closes
SESSION_SAVE_EVERY_REQUEST = True  # Update the session on every request

# Payment Gateway Settings
KHALTI_SECRET_KEY = '2fdb277ebbb144448fca0564e5c8c2f8'  
KHALTI_PUBLIC_KEY = 'c887a495931546fabfb8a85dd58a1e90'  

# Set to True to use sandbox environment, False for production
KHALTI_DEBUG = True  

# Configure logging for better debugging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'proj': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Custom password reset templates
PASSWORD_RESET_TEMPLATES = {
    'email_template_name': 'registration/password_reset_email.html',
    'subject_template_name': 'registration/password_reset_subject.txt',
}
