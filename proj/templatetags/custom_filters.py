from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def split(value, delimiter):
    """
    Split a string by a delimiter and return a list of parts.
    
    Usage:
    {% for part in value|split:'delimiter' %}
        {{ part }}
    {% endfor %}
    """
    if value:
        return value.split(delimiter)
    return [] 