#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agentic_django.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create a superuser for testing
try:
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
    )
    
    if created:
        user.set_password('admin123')
        user.save()
        print(f"Superuser '{user.username}' created successfully")
    else:
        # Update password if user exists
        user.set_password('admin123')
        user.save()
        print(f"Superuser '{user.username}' password updated")
        
except Exception as e:
    print(f"Error creating superuser: {e}")