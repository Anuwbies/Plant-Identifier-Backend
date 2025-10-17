from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import PlantHistory

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

class PlantHistorySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # <-- nested user serializer

    class Meta:
        model = PlantHistory
        fields = '__all__'
