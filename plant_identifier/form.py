from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# ---------------- SIGN UP FORM ----------------
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

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists")
        if not 3 <= len(username) <= 16:
            raise ValidationError("Username must be 3-16 characters")
        return username

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


# ---------------- SIGN IN FORM ----------------
class UserSignInForm(forms.Form):
    username = forms.CharField(max_length=150, label='Username')
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Try username
            user = authenticate(username=username, password=password)

            # Try email if username fails
            if user is None:
                try:
                    user_by_email = User.objects.get(email=username)
                    user = authenticate(username=user_by_email.username, password=password)
                except User.DoesNotExist:
                    pass

            if user is None:
                raise forms.ValidationError("Invalid username/email or password.")
            else:
                self.user = user  # Save for views.py

        return cleaned_data
