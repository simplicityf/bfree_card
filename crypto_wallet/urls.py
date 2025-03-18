from django.urls import path
from . import views

urlpatterns = [
    path('', views.crypto, name='crypto'),
    path('crypto_funding_request', views.crypto_funding_request, name='crypto_funding_request'),
    path('test', views.test, name='test')
]