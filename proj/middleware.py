from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils.http import http_date
from django.utils.cache import patch_vary_headers
import time
import pytz
from django.utils import timezone


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
