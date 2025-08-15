from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

class CustomUserAdmin(DefaultUserAdmin):
    list_display = ('username', 'email', 'is_staff')
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)