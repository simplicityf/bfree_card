from django.urls import path
from .views import *

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('terms_and_conditions', terms_and_conditions, name='terms_and_conditions'),
    path('privacy_policy', privacy_policy, name='privacy_policy'),
    path('admin-interface/logo/logo.png', redirect_logo, name="redirect_logo"),
    path('admin-interface/favicon/logo.png', redirect_logo, name="redirect_logo"),
]