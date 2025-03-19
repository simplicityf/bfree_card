from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from card.models import *
from authentication.models import AlphaspaceAuthToken
from .models import *
from crypto_wallet.models import *
import requests
import secrets
from decouple import config
import json
from django.http import JsonResponse

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

def request_alphaspace_auth_tokens():
    request_url = f"{config('ALPHASPACE_BASE_URL')}oauth/token"
    data = {
        "grant_type" : "password",
        "client_id" : config('ALPHASPACE_CLIENT_ID'),
        "client_secret" : config('ALPHASPACE_CLIENT_SECRET'),
        "username" : config('ALPHASPACE_CLIENT_USERNAME'),
        "password" : config('ALPHASPACE_CLIENT_PASSWORD')
    }
    response = requests.post(request_url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        new_tokens = response.json()
        alphaspace_auth_token = get_object_or_404(AlphaspaceAuthToken, pk=1)
        alphaspace_auth_token.token_type = new_tokens['token_type']
        alphaspace_auth_token.refresh_token = new_tokens['refresh_token']
        alphaspace_auth_token.access_token = new_tokens['access_token']
        alphaspace_auth_token.expires_in = new_tokens['expires_in']
        alphaspace_auth_token.save()
        return True
    return False


def AlphaspaceAPIClient(endpoint, method, data=None):
    url = f"{config('ALPHASPACE_BASE_URL')}{endpoint}"
    alphaspace_auth_token = get_object_or_404(AlphaspaceAuthToken, pk=1)
    
    headers = {
        'Authorization': f"Token {alphaspace_auth_token.access_token}",
        'Idempotency-key': secrets.token_urlsafe(100),
        'Content-Type': 'application/json',
    }

    def make_request():
        if method == 'GET':
            return requests.get(url, headers=headers)
        elif method == 'POST':
            return requests.post(url, headers=headers, data=json.dumps(data))
        elif method == 'DELETE':
            return requests.delete(url, headers=headers)

    response = make_request()

    if response.status_code == 401:
        if request_alphaspace_auth_tokens():
            alphaspace_auth_token = get_object_or_404(AlphaspaceAuthToken, pk=1)
            headers['Authorization'] = f"Token {alphaspace_auth_token.access_token}"
            response = make_request()

    response_data = response.json()

    return response_data
        
        
def nowpayments_api_client(endpoint, method, data=None):
    url = f"{config('NOWPAYMENTS_BASE_URL')}{endpoint}"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        'x-api-key': f"{config('NOWPAYMENTS_API_KEY')}"
    }
    if method == 'GET':
        response = requests.get(url, headers=headers)
    elif method == 'POST':
        response = requests.post(url, headers=headers, json=data)
    
    response_data = response.json()
    if response.status_code == 200:
        return response_data
    else:
        return f"NowPayments Error: {response_data}"


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    card_count = Card.objects.filter(user=request.user).count()
    cards = list(Card.objects.filter(user=request.user).values())
    wallet_history_transaction = list(WalletTransaction.objects.filter(user=request.user).values())
    transaction_count = WalletTransaction.objects.filter(user=request.user).count()
    critical_broadcasts = list(CriticalBroadcast.objects.filter(active=True).values())
    data = {
        'card_count': card_count,
        'cards': cards,
        'critical_broadcasts': critical_broadcasts,
        'wallet_history_transaction': wallet_history_transaction,
        'transaction_count': transaction_count
    }
    return JsonResponse(data)


