from django.contrib import admin
from django.urls import path
from plant_identifier.views import registerUser

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/register/', registerUser, name='api-register'),
]
