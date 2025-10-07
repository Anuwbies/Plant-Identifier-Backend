from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from plant_identifier.views.auth_views import registerUser, loginUser
from plant_identifier.views.prediction_views import predict
from plant_identifier.views.random_views import random_plants

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', registerUser, name='register'),
    path('login/', loginUser, name='login'),
    path('predict/', predict, name='predict'),
    path('random-plants/', random_plants, name='random_plants'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
