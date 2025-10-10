from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import SavedPlant, PlantHistory


@admin.register(SavedPlant)
class SavedPlantAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
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
        'user__username',
    )
    list_filter = ('created_at', 'updated_at')


@admin.register(PlantHistory)
class PlantHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
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
        'user__username',
    )
    list_filter = ('identified_at',)


class CustomUserAdmin(DefaultUserAdmin):
    list_display = ('id', 'username', 'email', 'is_staff')


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
