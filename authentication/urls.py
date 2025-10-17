from django.urls import path
from .views import (
    RegisterView, 
    LoginView, 
    LogoutView, 
    ForgotPasswordView, 
    ResetPasswordView,
    VerifyResetCodeView,
    UpdateProfileView,
    ChangePasswordView,
    RefreshTokenView,
    DashboardStatsView  # Make sure this is imported
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', RefreshTokenView.as_view(), name='refresh'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('verify-reset-code/', VerifyResetCodeView.as_view(), name='verify_reset_code'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('update-profile/', UpdateProfileView.as_view(), name='update_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard_stats'),  # Add this line
]