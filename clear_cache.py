#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'summproj.settings')
django.setup()

from django.core.cache import cache

def clear_cache():
    """Clear Django cache"""
    print("Clearing Django cache...")
    cache.clear()
    print("Cache cleared successfully.")

if __name__ == "__main__":
    clear_cache() 