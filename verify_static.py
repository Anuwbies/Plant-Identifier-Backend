#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plant.settings')
django.setup()

from django.conf import settings
from pathlib import Path

print("=" * 70)
print("STATIC FILES CONFIGURATION VERIFICATION")
print("=" * 70)

print(f"\nDEBUG: {settings.DEBUG}")
print(f"STATIC_URL: {settings.STATIC_URL}")
print(f"STATIC_ROOT: {settings.STATIC_ROOT}")
print(f"STATICFILES_DIRS: {settings.STATICFILES_DIRS}")

print("\n" + "=" * 70)
print("CHECKING STATIC FILES")
print("=" * 70)

static_root = Path(settings.STATIC_ROOT)
if static_root.exists():
    print(f"✅ STATIC_ROOT exists: {static_root}")
    
    # Check admin files
    admin_path = static_root / 'admin'
    if admin_path.exists():
        print(f"✅ Admin static files found")
        
        css_path = admin_path / 'css' / 'base.css'
        if css_path.exists():
            print(f"✅ base.css exists ({css_path.stat().st_size} bytes)")
        else:
            print(f"❌ base.css NOT found at {css_path}")
            
        js_path = admin_path / 'js' / 'theme.js'
        if js_path.exists():
            print(f"✅ theme.js exists ({js_path.stat().st_size} bytes)")
        else:
            print(f"❌ theme.js NOT found at {js_path}")
    else:
        print(f"❌ Admin folder NOT found at {admin_path}")
else:
    print(f"❌ STATIC_ROOT does not exist: {static_root}")
    print("\nRun: python manage.py collectstatic")

print("\n" + "=" * 70)
print("URL CONFIGURATION")
print("=" * 70)
print("Static files should be accessible at:")
print(f"  http://127.0.0.1:8000{settings.STATIC_URL}admin/css/base.css")
print(f"  http://127.0.0.1:8000{settings.STATIC_URL}admin/js/theme.js")
print("\n⚠️  IMPORTANT: Restart your Django development server!")
print("=" * 70)
