#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plant.settings')
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

print("=" * 60)
print("TESTING DJANGO ADMIN AUTHENTICATION")
print("=" * 60)

# List all superusers
print("\nSuperusers in database:")
superusers = User.objects.filter(is_superuser=True)
for user in superusers:
    print(f"  - Username: {user.username}, Email: {user.email}")
    print(f"    is_active: {user.is_active}, is_staff: {user.is_staff}")

# Test authentication with 'admin' user
print("\n" + "=" * 60)
print("Testing authentication for 'admin' user")
print("=" * 60)

test_passwords = ['admin', 'admin123', 'password', '123456']
admin_user = User.objects.filter(username='admin').first()

if admin_user:
    print(f"User found: {admin_user.username}")
    print(f"Email: {admin_user.email}")
    print(f"is_active: {admin_user.is_active}")
    print(f"is_staff: {admin_user.is_staff}")
    print(f"is_superuser: {admin_user.is_superuser}")
    
    print("\nTrying common passwords...")
    for pwd in test_passwords:
        result = authenticate(username='admin', password=pwd)
        if result:
            print(f"✅ SUCCESS! Password is: {pwd}")
            break
        else:
            print(f"❌ Failed with password: {pwd}")
else:
    print("❌ User 'admin' not found!")

print("\n" + "=" * 60)
print("CREATING A NEW TEST SUPERUSER")
print("=" * 60)

# Create a new test superuser with known password
try:
    test_user = User.objects.filter(username='testadmin').first()
    if test_user:
        test_user.delete()
        print("Deleted existing 'testadmin' user")
    
    test_user = User.objects.create_superuser(
        username='testadmin',
        email='testadmin@plantidentifier.com',
        password='Admin@123'
    )
    print(f"✅ Created superuser: {test_user.username}")
    print(f"   Email: {test_user.email}")
    print(f"   Password: Admin@123")
    
    # Test authentication
    auth_result = authenticate(username='testadmin', password='Admin@123')
    if auth_result:
        print("\n✅ Authentication TEST PASSED!")
    else:
        print("\n❌ Authentication TEST FAILED!")
        
except Exception as e:
    print(f"❌ Error creating test user: {e}")

print("\n" + "=" * 60)
print("Use these credentials to login to Django admin:")
print("  URL: http://127.0.0.1:8000/admin/")
print("  Username: testadmin")
print("  Password: Admin@123")
print("=" * 60)
