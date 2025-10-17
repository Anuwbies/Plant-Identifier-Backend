from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
import secrets
import string
from datetime import datetime, timedelta
from django.utils import timezone
from django.urls import path
from .models import PasswordResetCode 
class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        username = request.data.get('username') or email  # Use email as username if no username provided
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        if not email or not password:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
            
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
            
        user = User.objects.create_user(
            username=username, 
            email=email, 
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        return Response({
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'firstName': user.first_name,
                'lastName': user.last_name,
                'fullName': f"{user.first_name} {user.last_name}".strip()
            }
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        remember_me = request.data.get('rememberMe', False)
        
        if not email or not password:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to find user by email first
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
            
        # Authenticate with username and password
        user = authenticate(username=username, password=password)
        
        if user is not None and user.is_active:
            # Create refresh token
            refresh = RefreshToken.for_user(user)
            
            # Extend refresh token lifetime if remember_me is True
            if remember_me:
                refresh.set_exp(lifetime=timedelta(days=30))
            else:
                refresh.set_exp(lifetime=timedelta(days=7))
                
            # Create full name
            full_name = f"{user.first_name} {user.last_name}".strip()
            if not full_name:
                full_name = user.username
                
            return Response({
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'name': full_name,
                    'firstName': user.first_name,
                    'lastName': user.last_name,
                    'username': user.username,
                    'role': 'admin' if user.is_staff else 'user'
                },
                'accessToken': str(refresh.access_token),
                'refreshToken': str(refresh),
                'rememberMe': remember_me,
                'expiresIn': 3600  # 1 hour in seconds
            }, status=status.HTTP_200_OK)
        
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get('refreshToken')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RefreshTokenView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refreshToken')
            if not refresh_token:
                return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
                
            token = RefreshToken(refresh_token)
            new_access_token = str(token.access_token)
            
            return Response({
                'accessToken': new_access_token
            })
        except Exception:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Return clear error message for unregistered emails
            return Response({
                'error': 'No account found with this email address. Please check your email or create a new account.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Generate reset code
        reset_code = PasswordResetCode.generate_code(user)
        
        # Send email with HTML template
        subject = 'Password Reset Code - Plant-Identifier'
        
        # HTML email template with inline CSS for compatibility
        html_message = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset Code</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; line-height: 1.6;">
    <div style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #000000 0%, #000000 100%); padding: 32px 24px; text-align: center;">
            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600; letter-spacing: -0.5px;">Password Reset</h1>
            <p style="margin: 8px 0 0 0; color: #e8f0fe; font-size: 16px;">Secure your account with a new password</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 32px 24px;">
            <h2 style="margin: 0 0 16px 0; color: #1a202c; font-size: 20px; font-weight: 600;">Hello {user.first_name or user.username},</h2>
            
            <p style="margin: 0 0 24px 0; color: #4a5568; font-size: 16px;">
                We received a request to reset your password for your Plant-identifier account. Use the verification code below to complete your password reset:
            </p>
            
            <!-- Verification Code Block -->
            <div style="background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%); border: 2px solid #e2e8f0; border-radius: 12px; padding: 24px; text-align: center; margin: 24px 0;">
                <p style="margin: 0 0 8px 0; color: #718096; font-size: 14px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">Verification Code</p>
                <div style="background: #ffffff; border: 2px solid #667eea; border-radius: 8px; padding: 16px 24px; display: inline-block; margin: 8px 0;">
                    <span style="font-family: 'Courier New', monospace; font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 4px;">{reset_code.code}</span>
                </div>
                <p style="margin: 8px 0 0 0; color: #a0aec0; font-size: 12px;">Code expires in 10 minutes</p>
            </div>
            
            <div style="background: #fef5e7; border-left: 4px solid #f6ad55; padding: 16px; border-radius: 6px; margin: 24px 0;">
                <p style="margin: 0; color: #744210; font-size: 14px;">
                    <strong>Security tip:</strong> Never share this code with anyone. Plant-identifier will never ask for your verification code.
                </p>
            </div>
            
            <p style="margin: 24px 0 0 0; color: #4a5568; font-size: 16px;">
                If you have any questions or need assistance, feel free to contact our support team.
            </p>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f7fafc; padding: 24px; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0 0 8px 0; color: #718096; font-size: 14px; text-align: center;">
                If you didn't request this password reset, please ignore this email and your password will remain unchanged.
            </p>
            <p style="margin: 0; color: #a0aec0; font-size: 12px; text-align: center;">
                © 2025 Plant-identifier. All rights reserved.
            </p>
        </div>
    </div>
    
    <!-- Mobile responsive styles -->
    <style>
        @media only screen and (max-width: 600px) {{
            .container {{ margin: 20px auto !important; }}
            .content {{ padding: 24px 16px !important; }}
            .code {{ font-size: 28px !important; }}
        }}
    </style>
</body>
</html>
        '''
        
        # Plain text fallback
        text_message = f'''
Hello {user.first_name or user.username},

You requested a password reset for your Plant-identifier account.

Your verification code is: {reset_code.code}

This code will expire in 10 minutes.

If you didn't request this reset, please ignore this email.

Best regards,
Plant-identifier Team
        '''
        
        try:
            from django.core.mail import EmailMultiAlternatives
            
            # Create email with both HTML and text versions
            email_msg = EmailMultiAlternatives(
                subject,
                text_message,  # Plain text version
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            email_msg.attach_alternative(html_message, "text/html")  # HTML version
            email_msg.send(fail_silently=False)
            
            return Response({
                'message': 'Reset code sent to your email',
                'email': email,
                'code': reset_code.code  # TEMP: Remove this in production
            }, status=status.HTTP_200_OK)
        except Exception as e:
            # For development/testing, still return success but log the error
            print(f"Email sending failed: {e}")
            return Response({
                'message': 'Reset code generated (email sending disabled for development)',
                'email': email,
                'code': reset_code.code  # TEMP: For testing - remove in production
            }, status=status.HTTP_200_OK)

class VerifyResetCodeView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        from .models import PasswordResetCode
        
        email = request.data.get('email')
        code = request.data.get('code')
        
        if not email or not code:
            return Response({'error': 'Email and code are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid email'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reset_code = PasswordResetCode.objects.get(
                user=user, 
                code=code, 
                is_used=False
            )
            
            if reset_code.is_expired():
                return Response({'error': 'Code has expired'}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'message': 'Code verified successfully',
                'email': email,
                'code': code  # Include for next step
            }, status=status.HTTP_200_OK)
            
        except PasswordResetCode.DoesNotExist:
            return Response({'error': 'Invalid or expired code'}, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        from .models import PasswordResetCode
        
        email = request.data.get('email')
        code = request.data.get('code')
        new_password = request.data.get('password')
        
        if not email or not code or not new_password:
            return Response({'error': 'Email, code, and new password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid email'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reset_code = PasswordResetCode.objects.get(
                user=user, 
                code=code, 
                is_used=False
            )
            
            if reset_code.is_expired():
                return Response({'error': 'Code has expired'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            # Mark code as used
            reset_code.is_used = True
            reset_code.save()
            
            return Response({
                'message': 'Password reset successfully'
            }, status=status.HTTP_200_OK)
            
        except PasswordResetCode.DoesNotExist:
            return Response({'error': 'Invalid or expired code'}, status=status.HTTP_400_BAD_REQUEST)

class UpdateProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        user = request.user
        
        first_name = request.data.get('firstName', '').strip()
        last_name = request.data.get('lastName', '').strip()
        email = request.data.get('email', '').strip()
        
        if not first_name or not last_name or not email:
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if email is already taken by another user
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            return Response({'error': 'Email is already taken'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            
            full_name = f"{user.first_name} {user.last_name}".strip()
            
            return Response({
                'message': 'Profile updated successfully',
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'name': full_name,
                    'firstName': user.first_name,
                    'lastName': user.last_name,
                    'role': 'user'
                }
            })
        except Exception as e:
            return Response({'error': 'Failed to update profile'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChangePasswordView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        user = request.user
        
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        if not current_password or not new_password:
            return Response({'error': 'Current password and new password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify current password
        if not user.check_password(current_password):
            return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate new password length
        if len(new_password) < 8:
            return Response({'error': 'New password must be at least 8 characters long'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user.set_password(new_password)
            user.save()
            
            return Response({
                'message': 'Password changed successfully'
            })
        except Exception as e:
            return Response({'error': 'Failed to change password'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DashboardStatsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Debug logging
        print(f"[DashboardStats] Authorization header: {request.META.get('HTTP_AUTHORIZATION', 'NOT FOUND')[:50]}")
        print(f"[DashboardStats] User authenticated: {request.user.is_authenticated}")
        print(f"[DashboardStats] User: {request.user}")
        print(f"[DashboardStats] User ID: {request.user.id if request.user.is_authenticated else 'N/A'}")
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'error': 'Authentication required',
                'code': 'authentication_required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user exists
        if request.user.is_anonymous:
            return Response({
                'success': False,
                'error': 'User not found',
                'code': 'user_not_found'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        from django.contrib.auth.models import User
        from plant_identifier.models import PlantHistory, SavedPlant
        from django.db.models import Count
        from datetime import datetime, timedelta
        
        try:
            # Verify user exists in database
            try:
                user = User.objects.get(id=request.user.id)
                print(f"[DashboardStats] User found: {user.username} (ID: {user.id})")
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'User account not found in database',
                    'code': 'user_not_found'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get basic stats
            total_users = User.objects.count()
            total_identifications = PlantHistory.objects.count()
            total_saved_plants = SavedPlant.objects.count()
            
            # Get recent identifications (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_identifications = PlantHistory.objects.filter(
                identified_at__gte=week_ago
            ).count()
            
            # Get popular plants (most identified species)
            popular_plants = PlantHistory.objects.values(
                'species_id', 'common_name', 'scientific_name'
            ).annotate(
                count=Count('species_id')
            ).order_by('-count')[:5]
            
            # Format popular plants data
            popular_plants_formatted = []
            for plant in popular_plants:
                popular_plants_formatted.append({
                    'species_id': plant['species_id'],
                    'predicted_name': plant['common_name'] or plant['scientific_name'],
                    'scientific_name': plant['scientific_name'],
                    'count': plant['count']
                })
            
            response_data = {
                'success': True,
                'stats': {
                    'total_users': total_users,
                    'total_identifications': total_identifications,
                    'total_saved_plants': total_saved_plants,
                    'recent_identifications': recent_identifications,
                    'popular_plants': popular_plants_formatted,
                }
            }
            
            print(f"[DashboardStats] Returning stats: {response_data}")
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"[DashboardStats] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': str(e),
                'code': 'internal_error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# URL patterns
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('stats/', DashboardStatsView.as_view(), name='dashboard_stats'),
]
