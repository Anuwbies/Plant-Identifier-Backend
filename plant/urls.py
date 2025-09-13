from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from plant_identifier.views import registerUser, predict
from plant_identifier.views import random_plants

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/register/', registerUser, name='api-register'),
    path("predict/", predict, name="predict"),
    path('random-plants/', random_plants, name='random_plants'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)