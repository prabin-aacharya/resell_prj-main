from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils.http import http_date
from django.utils.cache import patch_vary_headers
import time
import pytz
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import login
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect


class TimezoneMiddleware:
    """
    Middleware to set the timezone to Nepal Standard Time for all requests
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __process_request(self, request):
        # Use Nepal Standard Time
        tzname = settings.TIME_ZONE
        timezone.activate(pytz.timezone(tzname))

    def __call__(self, request):
        self.__process_request(request)
        response = self.get_response(request)
        return response


class AdminSessionMiddleware(SessionMiddleware):
    """
    Middleware that handles separate admin and user sessions.
    
    This middleware ensures that admin sessions are maintained independently
    from regular user sessions, allowing admins to log in and out as different
    users without losing their admin session.
    """
    
    def is_admin_path(self, path):
        """Check if the path is for an admin section"""
        return path.startswith('/admin/')
    
    def process_request(self, request):
        # Check if this is an admin URL
        is_admin_url = self.is_admin_path(request.path)
        
        # Use different session cookie names for admin and frontend
        if is_admin_url:
            # Use admin-specific session cookie
            settings.SESSION_COOKIE_NAME = 'admin_sessionid'
        else:
            # Use regular session cookie for frontend
            settings.SESSION_COOKIE_NAME = 'sessionid'
        
        # Call the parent class's process_request method
        super().process_request(request)
    
    def process_response(self, request, response):
        # Check if this is an admin URL
        is_admin_url = self.is_admin_path(request.path)
        
        # Use different session cookie names for admin and frontend
        if is_admin_url:
            # Use admin-specific session cookie
            settings.SESSION_COOKIE_NAME = 'admin_sessionid'
        else:
            # Use regular session cookie for frontend
            settings.SESSION_COOKIE_NAME = 'sessionid'
        
        # Call the parent class's process_response method
        response = super().process_response(request, response)
        
        # Add Vary header to prevent caching issues
        patch_vary_headers(response, ('Cookie',))
        
        return response


class AllowAdminSessionForPDFMiddleware(MiddlewareMixin):
    """
    For /payment/sales-report/ URLs, if the user is not authenticated or not staff,
    try to authenticate using the admin_sessionid cookie. If that user is staff,
    set request.user to the admin user for this request.
    """
    def process_request(self, request):
        if request.path.startswith('/payment/sales-report/'):
            if not request.user.is_authenticated or not request.user.is_staff:
                admin_session_key = request.COOKIES.get('admin_sessionid')
                if admin_session_key:
                    try:
                        session = Session.objects.get(session_key=admin_session_key)
                        session_data = session.get_decoded()
                        user_id = session_data.get('_auth_user_id')
                        User = get_user_model()
                        user = User.objects.get(pk=user_id)
                        if user.is_staff:
                            request.user = user
                    except Exception:
                        pass
