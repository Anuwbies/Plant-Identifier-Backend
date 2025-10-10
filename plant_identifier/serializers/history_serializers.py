from rest_framework import serializers
from ..models import PlantHistory

class PlantHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantHistory
        fields = '__all__'
