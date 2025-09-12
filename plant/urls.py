from django.contrib import admin
from django.urls import path
from plant_identifier.views import registerUser, signUser

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/register/', registerUser, name='api-register'),
    path('api/signin/', signUser, name='api-signin'),
]
