# plant_identifier/views/admin_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
from django.db import models

from ..models import PlantHistory
from ..serializers.history_serializers import PlantHistorySerializer


class AllPlantIdentificationsView(APIView):
    """
    Returns all plant identifications.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        records = PlantHistory.objects.all().order_by('-identified_at')
        serializer = PlantHistorySerializer(records, many=True)
        return Response({
            'success': True,
            'identifications': serializer.data
        }, status=status.HTTP_200_OK)


class AnalyticsPlantView(APIView):
    """
    Returns analytics data for plant identifications:
    - Time series
    - Top searched plants
    - Flagged cases
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        time_range = request.GET.get('time_range', 'month')
        search = request.GET.get('search', '')

        queryset = PlantHistory.objects.select_related('plant').all()
        if search:
            queryset = queryset.filter(plant__common_name__icontains=search)

        now = datetime.now()
        if time_range == 'today':
            queryset = queryset.filter(identified_at__date=now.date())
            days_to_show = 1
        elif time_range == 'week':
            start = now - timedelta(days=7)
            queryset = queryset.filter(identified_at__gte=start)
            days_to_show = 7
        elif time_range == 'month':
            start = now - timedelta(days=30)
            queryset = queryset.filter(identified_at__gte=start)
            days_to_show = 30
        else:
            days_to_show = 30

        # Build time series
        time_series = []
        for i in range(days_to_show):
            day = now - timedelta(days=i)
            daily_records = queryset.filter(identified_at__date=day.date())
            identifications = daily_records.count()
            unique_users = daily_records.values('user').distinct().count()
            time_series.append({
                "date": day.strftime("%Y-%m-%d"),
                "identifications": identifications,
                "uniqueUsers": unique_users
            })
        time_series.reverse()

        # Top searched plants
        top_plants = (
            queryset.values('plant__id', 'plant__common_name', 'plant__scientific_name')
            .annotate(searchCount=models.Count('id'))
            .order_by('-searchCount')[:8]
        )
        top_searched = [
            {
                "id": str(p['plant__id']),
                "commonName": p['plant__common_name'],
                "scientificName": p['plant__scientific_name'],
                "searchCount": p['searchCount'],
                "successRate": 90,          # placeholder
                "averageConfidence": 85     # placeholder
            } for p in top_plants
        ]

        # Flagged cases
        flagged_cases_qs = queryset.filter(status='flagged')
        flagged_cases = [
            {
                "id": str(f.id),
                "plantName": f.plant.common_name,
                "scientificName": f.plant.scientific_name,
                "flagCount": getattr(f, 'flag_count', 0),
                "lastFlagged": f.identified_at.isoformat(),
                "flagReasons": getattr(f, 'flag_reasons', []),
                "status": f.status
            } for f in flagged_cases_qs
        ]

        total_identifications = queryset.count()
        total_unique_users = queryset.values('user').distinct().count()
        average_success_rate = 90  # placeholder

        return Response({
            "timeSeries": time_series,
            "topSearched": top_searched,
            "flaggedCases": flagged_cases,
            "totalIdentifications": total_identifications,
            "totalUniqueUsers": total_unique_users,
            "averageSuccessRate": average_success_rate
        }, status=status.HTTP_200_OK)
