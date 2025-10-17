from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from plant_identifier.form import UserRegistrationForm, UserLoginForm

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

#===================================================================================================================================================================================


@api_view(['POST'])
def loginUser(request):
    form = UserLoginForm(request.data)
    if form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        try:
            # Find user by email
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate using username (Django requires this internally)
        user = authenticate(username=user_obj.username, password=password)

        if user is not None:
            login(request, user)
            return Response({
                'success': True,
                'user': {
                    'userId': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'joined_date': user.date_joined.strftime('%b %d, %Y'),
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

