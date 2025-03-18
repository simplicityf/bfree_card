from django.urls import path
from .views import *
from .forms import CustomConfirmResetPasswordForm
from django.contrib.auth import views as auth_views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
	#path('find_account/', find_account, name='find_account'),
 	path('api-token-auth/', obtain_auth_token, name='api_token_auth'),

    path('profile/', profile, name='profile'),
    path('security/', security, name='security'),
	path('send_change_password_otp/', send_change_password_otp, name='send_change_password_otp'),
    path('validate_change_password_otp/', validate_change_password_otp, name='validate_change_password_otp'),
   	path('signup/', Signup, name='signup'),
   	path('signin/', Signin, name='signin'),
    path('signin_otp/', signin_otp, name='signin_otp'),
    path('email_verification_otp/', email_verification_otp, name='email_verification_otp'),
   	path('logout/', auth_views.LogoutView.as_view(), {'next_page' : 'signin'}, name='logout'),
    
   	path('passwordreset/', password_reset, name='password_reset'),
   	path('passwordreset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
   	path('passwordreset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html', form_class=CustomConfirmResetPasswordForm), name='password_reset_confirm'),
   	path('passwordreset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
]