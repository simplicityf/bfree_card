from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    Signup, Signin, signin_otp, email_verification_otp,
    security, password_reset, send_change_password_otp,
    validate_change_password_otp, profile
)

urlpatterns = [
    # DRF endpoint for obtaining auth token
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    
    # Custom authentication endpoints
    path('signup', Signup, name='signup'),
    path('signin', Signin, name='signin'),
    path('signin-otp', signin_otp, name='signin_otp'),
    path('email-verification-otp', email_verification_otp, name='email_verification_otp'),
    path('profile', profile, name='profile'),
    path('password-reset', password_reset, name='password_reset'),
    path('send-change-password-otp', send_change_password_otp, name='send_change_password_otp'),
    path('validate-change-password-otp', validate_change_password_otp, name='validate_change_password_otp'),
    path('security', security, name='security'),
]
