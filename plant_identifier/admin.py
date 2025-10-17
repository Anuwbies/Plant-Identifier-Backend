from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import SavedPlant, PlantHistory


@admin.register(SavedPlant)
class SavedPlantAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'get_user_full_name',
        'common_name',
        'scientific_name',
        'species_id',
        'confidence',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'common_name',
        'scientific_name',
        'species_id',
        'user__first_name',
        'user__last_name',
        'user__email',
    )
    list_filter = ('created_at', 'updated_at')

    def get_user_full_name(self, obj):
        if obj.user:
            full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
            return full_name if full_name else obj.user.email
        return "No User"
    get_user_full_name.short_description = "User"


@admin.register(PlantHistory)
class PlantHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'get_user_full_name',
        'common_name',
        'scientific_name',
        'species_id',
        'confidence',
        'identified_at',
    )
    search_fields = (
        'common_name',
        'scientific_name',
        'species_id',
        'user__first_name',
        'user__last_name',
        'user__email',
    )
    list_filter = ('identified_at',)

    def get_user_full_name(self, obj):
        if obj.user:
            full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
            return full_name if full_name else obj.user.email
        return "No User"
    get_user_full_name.short_description = "User"


class CustomUserAdmin(DefaultUserAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'is_staff')
    search_fields = ('first_name', 'last_name', 'email')


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
