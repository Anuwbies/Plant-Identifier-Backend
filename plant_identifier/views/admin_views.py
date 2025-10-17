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
    Returns all plant identification records with user info.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(f"[AllPlantIdentifications] User: {request.user}")
        print(f"[AllPlantIdentifications] User authenticated: {request.user.is_authenticated}")
        
        # Check if user is authenticated
        if not request.user.is_authenticated or request.user.is_anonymous:
            return Response({
                'success': False,
                'error': 'Authentication required',
                'code': 'authentication_required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            # Verify user exists
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(id=request.user.id)
                print(f"[AllPlantIdentifications] User found: {user.username}")
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'User account not found',
                    'code': 'user_not_found'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get all identifications with related user data
            identifications = PlantHistory.objects.select_related('user').all().order_by('-identified_at')
            
            # Serialize the data manually to ensure correct field names
            data = []
            for identification in identifications:
                user_data = None
                if identification.user:
                    user_data = {
                        'username': identification.user.username,
                        'email': identification.user.email,
                        'first_name': identification.user.first_name,
                        'last_name': identification.user.last_name,
                    }
                
                data.append({
                    'id': identification.id,
                    'user': user_data,
                    'common_name': identification.common_name,
                    'scientific_name': identification.scientific_name,
                    'confidence': identification.confidence * 100 if identification.confidence else None,
                    'image_url': identification.image_url,
                    'identified_at': identification.identified_at.isoformat(),
                    'is_correct': identification.is_correct,
                })
            
            print(f"[AllPlantIdentifications] Returning {len(data)} identifications")
            return Response({
                'success': True,
                'identifications': data,
                'count': len(data)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"[AllPlantIdentifications] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': str(e),
                'code': 'internal_error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AnalyticsPlantView(APIView):
    """
    Simple analytics for plant identifications
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(f"[AnalyticsPlant] User: {request.user.username}")
        
        try:
            from django.contrib.auth.models import User
            
            # Verify user exists
            try:
                user = User.objects.get(id=request.user.id)
                print(f"[AnalyticsPlant] User verified: {user.username}")
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'User not found'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get time range parameter
            time_range = request.GET.get('time_range', 'month')
            search = request.GET.get('search', '')

            # Get all plant identifications
            queryset = PlantHistory.objects.select_related('user').all()
            
            # Apply search filter
            if search:
                queryset = queryset.filter(common_name__icontains=search)

            # Apply time filter
            now = datetime.now()
            if time_range == 'today':
                queryset = queryset.filter(identified_at__date=now.date())
                days_to_show = 7  # Show last 7 days for chart
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

            # Build time series data
            time_series = []
            for i in range(days_to_show):
                day = now - timedelta(days=i)
                day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                
                daily_records = PlantHistory.objects.filter(
                    identified_at__range=[day_start, day_end]
                )
                if search:
                    daily_records = daily_records.filter(common_name__icontains=search)
                    
                identifications = daily_records.count()
                unique_users = daily_records.values('user').distinct().count()
                
                time_series.append({
                    "date": day.strftime("%Y-%m-%d"),
                    "identifications": identifications,
                    "uniqueUsers": unique_users
                })
            
            time_series.reverse()

            # Get top plants
            top_plants = (
                queryset.values('species_id', 'common_name', 'scientific_name')
                .annotate(searchCount=models.Count('id'))
                .order_by('-searchCount')[:10]
            )
            
            top_searched = [
                {
                    "id": str(p['species_id']),
                    "commonName": p['common_name'] or 'Unknown',
                    "scientificName": p['scientific_name'] or 'Unknown',
                    "searchCount": p['searchCount'],
                    "successRate": 90,
                    "averageConfidence": 85
                } for p in top_plants
            ]

            # Get flagged cases
            flagged_cases_qs = queryset.filter(is_correct=False)[:10]
            flagged_cases = [
                {
                    "id": str(f.id),
                    "plantName": f.common_name or 'Unknown',
                    "scientificName": f.scientific_name or 'Unknown',
                    "flagCount": 1,
                    "lastFlagged": f.identified_at.isoformat(),
                    "flagReasons": ["Low confidence"],
                    "status": "pending"
                } for f in flagged_cases_qs
            ]

            # Calculate summary stats
            total_identifications = queryset.count()
            total_unique_users = queryset.values('user').distinct().count()
            
            correct_count = queryset.filter(is_correct=True).count()
            average_success_rate = round((correct_count / total_identifications * 100), 2) if total_identifications > 0 else 0

            # Get recent uploads (last 20)
            recent_uploads_qs = queryset.select_related('user').order_by('-identified_at')[:20]
            recent_uploads = []
            
            for upload in recent_uploads_qs:
                user_data = None
                if upload.user:
                    user_data = {
                        'username': upload.user.username,
                        'email': upload.user.email,
                    }
                
                recent_uploads.append({
                    'id': upload.id,
                    'common_name': upload.common_name,
                    'scientific_name': upload.scientific_name,
                    'confidence': upload.confidence * 100 if upload.confidence else 0,
                    'image_url': upload.image_url,
                    'identified_at': upload.identified_at.isoformat(),
                    'user': user_data
                })

            response_data = {
                "success": True,
                "timeSeries": time_series,
                "topSearched": top_searched,
                "flaggedCases": flagged_cases,
                "recentUploads": recent_uploads,
                "totalIdentifications": total_identifications,
                "totalUniqueUsers": total_unique_users,
                "averageSuccessRate": average_success_rate
            }
            
            print(f"[AnalyticsPlant] Returning data for {total_identifications} identifications")
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"[AnalyticsPlant] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
