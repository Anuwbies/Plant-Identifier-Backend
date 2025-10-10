from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from plant_identifier.views.auth_views import registerUser, loginUser
from plant_identifier.views.prediction_views import predict
from plant_identifier.views.random_views import random_plants
from plant_identifier.views.saved_plant_views import SavedPlantListCreateView, SavedPlantDetailView
from plant_identifier.views.plant_history_views import PlantHistoryListCreateView, PlantHistoryDetailView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', registerUser, name='register'),
    path('login/', loginUser, name='login'),
    path('predict/', predict, name='predict'),
    path('random-plants/', random_plants, name='random_plants'),

    # ✅ SavedPlant endpoints
    path('saved-plants/', SavedPlantListCreateView.as_view(), name='saved-plant-list-create'),
    path('saved-plants/<int:id>/', SavedPlantDetailView.as_view(), name='saved-plant-detail'),

    path('plant-history/', PlantHistoryListCreateView.as_view(), name='plant-history'),
    path('plant-history/<int:id>/', PlantHistoryDetailView.as_view(), name='plant-history-detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
