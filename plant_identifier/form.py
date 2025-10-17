from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        error_messages={'min_length': 'Password must be at least 8 characters'}
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm Password"
    )
    email = forms.EmailField(
        error_messages={'invalid': 'Enter a valid email address'}
    )

    first_name = forms.CharField(
        max_length=30,
        required=True,
        error_messages={'required': 'First name is required'}
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        error_messages={'required': 'Last name is required'}
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        return password

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match")
        return confirm_password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # use email as username
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


# ===================================================================================================================================================================================

class UserLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            try:
                # Find the user by email and authenticate using username (email)
                user_obj = User.objects.get(email=email)
                username = user_obj.username
                user = authenticate(username=username, password=password)
                if user is None:
                    raise ValidationError("Invalid email or password")
            except User.DoesNotExist:
                raise ValidationError("Invalid email or password")
        return cleaned_data
