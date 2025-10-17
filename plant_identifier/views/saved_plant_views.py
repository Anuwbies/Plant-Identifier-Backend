from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.db.models import Count, Q
from ..models import SavedPlant
from ..serializers.saved_plant_serializers import SavedPlantSerializer


class SavedPlantListCreateView(generics.GenericAPIView):
    serializer_class = SavedPlantSerializer

    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        plants = SavedPlant.objects.filter(user=user)
        serializer = SavedPlantSerializer(plants, many=True)
        return Response(serializer.data)

    def post(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SavedPlantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SavedPlantDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SavedPlantSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        if not user_id:
            return SavedPlant.objects.none()
        return SavedPlant.objects.filter(user__id=user_id)


class AdminSavedPlantsView(APIView):
    """View all saved plants across all users (Admin only)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(f"[AdminSavedPlants] User: {request.user.username}")
        
        try:
            # Verify user exists
            try:
                user = User.objects.get(id=request.user.id)
                print(f"[AdminSavedPlants] User verified: {user.username}")
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'User not found'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get query parameters
            search = request.GET.get('search', '')
            user_filter = request.GET.get('user', '')
            
            # Get all saved plants
            saved_plants = SavedPlant.objects.select_related('user').all()
            
            # Apply filters
            if search:
                saved_plants = saved_plants.filter(
                    Q(common_name__icontains=search) |
                    Q(scientific_name__icontains=search)
                )
            
            if user_filter:
                saved_plants = saved_plants.filter(
                    Q(user__username__icontains=user_filter) |
                    Q(user__email__icontains=user_filter)
                )
            
            # Serialize data
            plants_data = []
            for plant in saved_plants.order_by('-created_at'):
                user_data = None
                if plant.user:
                    user_data = {
                        'id': plant.user.id,
                        'username': plant.user.username,
                        'email': plant.user.email,
                        'full_name': f"{plant.user.first_name} {plant.user.last_name}".strip() or plant.user.username
                    }
                
                plants_data.append({
                    'id': plant.id,
                    'user': user_data,
                    'species_id': plant.species_id,
                    'common_name': plant.common_name,
                    'scientific_name': plant.scientific_name,
                    'confidence': plant.confidence * 100 if plant.confidence else None,
                    'image_url': plant.image_url,
                    'created_at': plant.created_at.isoformat(),
                    'updated_at': plant.updated_at.isoformat(),
                })
            
            # Get statistics
            total_saved = saved_plants.count()
            unique_users = saved_plants.values('user').distinct().count()
            unique_species = saved_plants.values('species_id').distinct().count()
            
            # Get top saved plants
            top_plants = (
                saved_plants.values('common_name', 'scientific_name')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            )
            
            response_data = {
                'success': True,
                'saved_plants': plants_data,
                'statistics': {
                    'total_saved': total_saved,
                    'unique_users': unique_users,
                    'unique_species': unique_species,
                    'top_plants': list(top_plants)
                }
            }
            
            print(f"[AdminSavedPlants] Returning {len(plants_data)} saved plants")
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"[AdminSavedPlants] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
