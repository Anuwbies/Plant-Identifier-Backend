from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

# Mobile app endpoints (existing)
from plant_identifier.views.auth_views import registerUser, loginUser
from plant_identifier.views.prediction_views import predict
from plant_identifier.views.random_views import random_plants
from plant_identifier.views.saved_plant_views import SavedPlantListCreateView, SavedPlantDetailView
from plant_identifier.views.plant_history_views import PlantHistoryListCreateView, PlantHistoryDetailView

# Import the dashboard stats view directly
from authentication.views import DashboardStatsView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Mobile app endpoints (legacy compatibility)
    path('register/', registerUser, name='mobile_register'),
    path('login/', loginUser, name='mobile_login'),
    path('predict/', predict, name='mobile_predict'),
    path('random-plants/', random_plants, name='mobile_random_plants'),
    path('saved-plants/', SavedPlantListCreateView.as_view(), name='saved-plant-list-create'),
    path('saved-plants/<int:id>/', SavedPlantDetailView.as_view(), name='saved-plant-detail'),
    path('plant-history/', PlantHistoryListCreateView.as_view(), name='plant-history'),
    path('plant-history/<int:id>/', PlantHistoryDetailView.as_view(), name='plant-history-detail'),
    
    # Admin web dashboard endpoints
    path('api/auth/', include('authentication.urls')),
    
    # Direct dashboard stats endpoint
    path('api/plants/admin/stats/', DashboardStatsView.as_view(), name='dashboard_stats_direct'),
    
    # Root endpoint
    path("", lambda request: HttpResponse("🌱 Unified Plant Identifier Backend is running!")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)