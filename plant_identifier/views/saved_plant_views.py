from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth.models import User
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
