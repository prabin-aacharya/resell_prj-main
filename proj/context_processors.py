import datetime
import pytz
from django.conf import settings

def timezone_context(request):
    """
    Context processor to provide Nepal Standard Time information to all templates
    """
    nepal_timezone = pytz.timezone('Asia/Kathmandu')
    current_time = datetime.datetime.now(nepal_timezone)
    
    return {
        'nepal_time': current_time,
        'timezone_name': 'Nepal Standard Time (UTC+5:45)',
        'timezone_short': 'NPT',
    } 