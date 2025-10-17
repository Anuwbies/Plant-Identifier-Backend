# plant/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.urls import path
from . import views


# Mobile app endpoints (existing)
from plant_identifier.views.auth_views import registerUser, loginUser
from plant_identifier.views.prediction_views import predict, explain_llm
from plant_identifier.views.random_views import random_plants
from plant_identifier.views.saved_plant_views import SavedPlantListCreateView, SavedPlantDetailView
from plant_identifier.views.plant_history_views import PlantHistoryListCreateView, PlantHistoryDetailView
from plant_identifier.views.admin_views import AllPlantIdentificationsView, AnalyticsPlantView

# Import the dashboard stats view directly
from authentication.views import DashboardStatsView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', registerUser, name='register'),
    path('login/', loginUser, name='login'),
    path('predict/', predict, name='predict'),
    path('explain-llm/', explain_llm, name='explain_llm'),
    path('random-plants/', random_plants, name='random_plants'),
    path('api/plants/admin/identifications/', AllPlantIdentificationsView.as_view(), name='admin_identifications'),

    # ✅ SavedPlant endpoints
    path('saved-plants/', SavedPlantListCreateView.as_view(), name='saved-plant-list-create'),
    path('saved-plants/<int:id>/', SavedPlantDetailView.as_view(), name='saved-plant-detail'),

    path('plant-history/', PlantHistoryListCreateView.as_view(), name='plant-history'),
    path('plant-history/<int:id>/', PlantHistoryDetailView.as_view(), name='plant-history-detail'),
    path('api/plants/analytics/', AnalyticsPlantView.as_view(), name='analytics-plant'),
    

    
    # Admin web dashboard endpoints
    path('api/auth/', include('authentication.urls')),
    
    # Direct dashboard stats endpoint
    path('api/plants/admin/stats/', DashboardStatsView.as_view(), name='dashboard_stats_direct'),
    
    # Root endpoint
    path("", lambda request: HttpResponse("🌱 Unified Plant Identifier Backend is running!")),

    # Analytics endpoints
    path('analytics/', views.get_analytics, name='analytics'),
    path('time-series/', views.get_time_series, name='time-series'),
    path('top-searched/', views.get_top_searched, name='top-searched'),
    path('flagged/', views.get_flagged_cases, name='flagged-cases'),
    path('summary/', views.get_summary, name='summary'),
    
    # Plant CRUD endpoints
    path('', views.plant_list_create, name='plant-list-create'),
    path('api/plants/<str:plant_id>/', views.plant_detail, name='plant-detail'),
    path('api/plants/tags/available/', views.get_available_tags, name='available-tags'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)