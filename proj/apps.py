from django.apps import AppConfig


class ProjConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'proj'
    
    def ready(self):
        # Initialize app when ready
        # Check email configuration on startup
        import os
        if not os.environ.get('DJANGO_SETTINGS_MODULE', '').endswith('.testing'):
            try:
                from django.conf import settings
                if settings.EMAIL_BACKEND.endswith('smtp.EmailBackend'):
                    # Only check SMTP settings if using SMTP backend
                    print("\n=== Email Configuration Check ===")
                    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
                    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
                    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
                    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
                    print(f"EMAIL_HOST_PASSWORD: {'[SET]' if settings.EMAIL_HOST_PASSWORD else '[NOT SET]'}")
                    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
                    print("================================\n")
                    
                    if not settings.EMAIL_HOST_PASSWORD:
                        print("WARNING: EMAIL_HOST_PASSWORD is not set. Email sending will fail.")
            except Exception as e:
                print(f"Error checking email configuration: {str(e)}")