#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plant.settings')
django.setup()

from django.conf import settings
from django.urls import get_resolver
from django.conf.urls.static import static

print("=" * 70)
print("DEBUGGING STATIC FILES SERVING")
print("=" * 70)

print(f"\nDEBUG mode: {settings.DEBUG}")
print(f"STATIC_URL: {settings.STATIC_URL}")
print(f"STATIC_ROOT: {settings.STATIC_ROOT}")

# Show what static() generates
static_patterns = static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
print(f"\nStatic URL patterns generated: {len(static_patterns)} patterns")
for pattern in static_patterns:
    print(f"  - {pattern.pattern}")

# Check if static files middleware is being used
print("\n" + "=" * 70)
print("CHECKING URL RESOLUTION")
print("=" * 70)

resolver = get_resolver()
print(f"\nTotal URL patterns: {len(resolver.url_patterns)}")

# Try to resolve static file URL
from django.urls import resolve, Resolver404

try:
    match = resolve('/static/admin/css/base.css')
    print(f"\n✅ URL /static/admin/css/base.css resolves to: {match.view_name}")
    print(f"   View: {match.func}")
except Resolver404 as e:
    print(f"\n❌ URL /static/admin/css/base.css DOES NOT RESOLVE")
    print(f"   Error: {e}")
    
    # List all URL patterns
    print("\nFirst 10 URL patterns:")
    for i, pattern in enumerate(resolver.url_patterns[:10]):
        print(f"  {i+1}. {pattern.pattern}")

print("\n" + "=" * 70)
