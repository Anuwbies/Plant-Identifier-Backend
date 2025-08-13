from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import SavedPlant

# Custom UserAdmin to show only username, email, and is_staff
class CustomUserAdmin(DefaultUserAdmin):
    list_display = ('username', 'email', 'is_staff')

# Unregister the default User admin
admin.site.unregister(User)
# Register User with the custom admin
admin.site.register(User, CustomUserAdmin)

@admin.register(SavedPlant)
class SavedPlantAdmin(admin.ModelAdmin):
    list_display = ('common_name', 'scientific_name', 'image_url')
    search_fields = ('common_name', 'scientific_name')
