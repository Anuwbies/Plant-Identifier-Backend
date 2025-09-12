from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import UserInfo  # This is the line you need to add

class CustomUserAdmin(DefaultUserAdmin):
    list_display = ('username', 'email', 'is_staff')
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(UserInfo)  # Add this line to register your model