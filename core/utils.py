import secrets
import requests
import json
from decouple import config
from django.shortcuts import get_object_or_404
from authentication.models import AlphaspaceAuthToken

def generate_unique_nickname():
    """
    Generates a unique nickname.
    You could add extra logic to ensure uniqueness against the Card model,
    but for now it just returns a random hexadecimal string.
    """
    return secrets.token_hex(8)

def request_alphaspace_auth_tokens():
    """
    Requests new Alphaspace tokens.
    This function makes an API call to fetch fresh authentication tokens
    and updates your AlphaspaceAuthToken instance in the database.
    """
    request_url = f"{config('ALPHASPACE_BASE_URL')}oauth/token"
    data = {
        "grant_type": "password",
        "client_id": config('ALPHASPACE_CLIENT_ID'),
        "client_secret": config('ALPHASPACE_CLIENT_SECRET'),
        "username": config('ALPHASPACE_CLIENT_USERNAME'),
        "password": config('ALPHASPACE_CLIENT_PASSWORD'),
    }
    response = requests.post(request_url, json=data, headers={'Content-Type': 'application/json'})
    if response.status_code == 200:
        new_tokens = response.json()
        token_instance = get_object_or_404(AlphaspaceAuthToken, pk=1)
        token_instance.token_type = new_tokens['token_type']
        token_instance.refresh_token = new_tokens['refresh_token']
        token_instance.access_token = new_tokens['access_token']
        token_instance.expires_in = new_tokens['expires_in']
        token_instance.save()
        return True
    return False

def AlphaspaceAPIClient(endpoint, method, data=None):
    """
    A client for making API calls to Alphaspace.
    It constructs the full URL, sets headers (including an access token),
    and handles HTTP GET, POST, and DELETE requests.
    If the access token is expired (status code 401), it will try to refresh the tokens.
    """
    url = f"{config('ALPHASPACE_BASE_URL')}{endpoint}"
    token_instance = get_object_or_404(AlphaspaceAuthToken, pk=1)
    headers = {
        'Authorization': f"Bearer {token_instance.access_token}",
        'Idempotency-key': secrets.token_urlsafe(100),
        'Content-Type': 'application/json',
    }

    def make_request():
        if method.upper() == 'GET':
            return requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            return requests.post(url, headers=headers, json=data)
        elif method.upper() == 'DELETE':
            return requests.delete(url, headers=headers)
        else:
            raise ValueError("Unsupported HTTP method")

    response = make_request()

    if response.status_code == 401:
        if request_alphaspace_auth_tokens():
            token_instance = get_object_or_404(AlphaspaceAuthToken, pk=1)
            headers['Authorization'] = f"Bearer {token_instance.access_token}"
            response = make_request()

    return response.json()
