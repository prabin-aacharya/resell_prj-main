from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils.http import http_date
from django.utils.cache import patch_vary_headers
import time


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
        
        # Special handling for form submissions to prevent session loss
        is_form_submission = request.method == 'POST' and ('/sell/' in request.path or '/sell/success/' in request.path)
        
        # For form submissions, we need to check both session cookies
        if is_form_submission:
            # First try the regular session cookie
            settings.SESSION_COOKIE_NAME = getattr(settings, 'SESSION_COOKIE_NAME', 'sessionid')
            super().process_request(request)
            
            # If no user is authenticated, try the admin session cookie
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                # Save any session data
                session_data = None
                if hasattr(request, 'session'):
                    session_data = request.session.items()
                
                # Try admin cookie
                settings.SESSION_COOKIE_NAME = getattr(settings, 'ADMIN_SESSION_COOKIE_NAME', 'admin_sessionid')
                super().process_request(request)
                
                # Restore session data if needed
                if session_data and hasattr(request, 'session'):
                    for key, value in session_data:
                        request.session[key] = value
            
            # Reset to default cookie name
            settings.SESSION_COOKIE_NAME = getattr(settings, 'SESSION_COOKIE_NAME', 'sessionid')
            return
        
        # Regular processing for non-form requests
        # Use the appropriate session cookie name based on the URL
        if is_admin_url:
            session_cookie_name = getattr(settings, 'ADMIN_SESSION_COOKIE_NAME', 'admin_sessionid')
        else:
            session_cookie_name = settings.SESSION_COOKIE_NAME
        
        # Store the original cookie name
        self.original_cookie_name = settings.SESSION_COOKIE_NAME
        
        # Temporarily change the session cookie name
        settings.SESSION_COOKIE_NAME = session_cookie_name
        
        # Call the parent class's process_request method
        super().process_request(request)
        
        # Restore the original cookie name
        settings.SESSION_COOKIE_NAME = self.original_cookie_name
    
    def process_response(self, request, response):
        # Check if this is an admin URL
        is_admin_url = self.is_admin_path(request.path)
        
        # Special handling for form submissions to prevent session loss
        is_form_submission = request.method == 'POST' and ('/sell/' in request.path or '/sell/success/' in request.path)
        is_form_redirect = '/sell/success/' in request.path and hasattr(request, 'session')
        
        if is_form_submission or is_form_redirect:
            # For form submissions, use only the regular session cookie
            session_cookie_name = settings.SESSION_COOKIE_NAME
            self.original_cookie_name = session_cookie_name
            
            # Call parent method
            response = super().process_response(request, response)
            
            # Add Vary header to prevent caching issues
            patch_vary_headers(response, ('Cookie',))
            return response
        
        # Regular processing for non-form requests
        # Use the appropriate session cookie name based on the URL
        if is_admin_url:
            session_cookie_name = getattr(settings, 'ADMIN_SESSION_COOKIE_NAME', 'admin_sessionid')
        else:
            session_cookie_name = settings.SESSION_COOKIE_NAME
        
        # Store the original cookie name
        self.original_cookie_name = settings.SESSION_COOKIE_NAME
        
        # Temporarily change the session cookie name
        settings.SESSION_COOKIE_NAME = session_cookie_name
        
        # Call the parent class's process_response method
        response = super().process_response(request, response)
        
        # Restore the original cookie name
        settings.SESSION_COOKIE_NAME = self.original_cookie_name
        
        # Add Vary header to prevent caching issues
        patch_vary_headers(response, ('Cookie',))
        
        return response
