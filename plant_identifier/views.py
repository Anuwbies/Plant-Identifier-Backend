from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from plant_identifier.form import UserRegistrationForm

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