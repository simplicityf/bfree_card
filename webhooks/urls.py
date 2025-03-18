from django.urls import path
from .views import *

urlpatterns = [
    path('alphaspace', alphaspace, name='alphaspace'),
    path('nowpayments', nowpayments, name='nowpayments')
]