from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import login
from plant_identifier.form import UserRegistrationForm, UserSignInForm
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['POST'])
def registerUser(request):
    form = UserRegistrationForm(request.data)
    if form.is_valid():
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        return Response({'success': 'User created successfully!'}, status=status.HTTP_201_CREATED)
    else:
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@authentication_classes([])
@permission_classes([AllowAny])  
@api_view(['POST'])
def signUser(request):
    form = UserSignInForm(request.data)
    if form.is_valid():
        user = form.user
        login(request, user)  # Django session login
        return Response(
            {'success': 'User signed in successfully!', 'username': user.username},
            status=status.HTTP_200_OK
        )
    else:
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
