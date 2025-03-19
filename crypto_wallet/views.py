from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from core.views import nowpayments_api_client
from core.models import CryptoTransaction, CriticalBroadcast, Account  # adjust imports as needed
from crypto_wallet.models import CryptoFundingRequest, CryptoAddress
import uuid
import requests
from django.conf import settings
import json
from decouple import config

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

def get_request_data(request):
    """
    Returns parsed JSON data if the content type is JSON,
    otherwise returns request.POST.
    """
    if request.content_type == "application/json":
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            return {}
    return request.POST

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def crypto(request):
    if request.method == "POST":
        data = get_request_data(request)
        
        amount = data.get("amount")
        
        if not amount:
            return JsonResponse({'error': "Amount is required."}, status=400)
        
        # Check if amount is numeric and within allowed range
        if amount.isdigit() and int(amount) > 2000:
            return JsonResponse({'error': "Amount mustn't be more than $2000"}, status=400)
        
        payload = {
            "price_amount": amount,
            "price_currency": "usd",
            "is_fee_paid_by_user": True,
            "ipn_callback_url": config('IPN_CALLBACK_URL'),
            "success_url": config('SUCCESS_URL'),
            "cancel_url": config('CANCEL_URL')
        }
        
        response = nowpayments_api_client('invoice', 'POST', data=payload)
        
        if 'id' in response:
            CryptoTransaction.objects.create(
                user=request.user,
                transaction_id=response['id'],
                amount=amount,
                invoice_url=response['invoice_url']
            )
            return JsonResponse({'invoice_url': response['invoice_url']})
        else:
            return JsonResponse({'error': response}, status=400)
    
    crypto_addresses = list(CryptoAddress.objects.all().values())
    critical_broadcasts = list(CriticalBroadcast.objects.filter(active=True).values())
    
    return JsonResponse({
        'crypto_addresses': crypto_addresses,
        'critical_broadcasts': critical_broadcasts
    })

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def crypto_funding_request(request):
    if request.method == "POST":
        data = get_request_data(request)
        amount = data.get("funding_request_amount")
        transaction_id = data.get("transaction_id")
        address_id = data.get("address_id")
        if not amount or not transaction_id:
            return JsonResponse({'error': "Amount and Transaction ID are required."}, status=400)
        
        if amount and not amount.isdigit():
            return JsonResponse({'error': "Amount must be a numeric value"}, status=400)
        
        # Create a funding request
        CryptoFundingRequest.objects.create(user=request.user, transaction_id=transaction_id, amount=amount)
        try:
            address = CryptoAddress.objects.get(id=address_id)
        except CryptoAddress.DoesNotExist:
            return JsonResponse({'error': "Crypto address not found."}, status=404)
        
        # Compose a plain text email message
        email_content = (
            f"Hello {request.user.first_name} {request.user.last_name},\n\n"
            f"Your funding request for ${amount} has been received.\n"
            f"Transaction ID: {transaction_id}\n"
            f"Network Chain: {address.network_chain}\n"
            f"Coin: {address.coin}\n"
            f"Address: {address.address}\n"
            f"DateTime: {timezone.now()}\n\n"
            "Thank you,\nThe Bfree Team"
        )
        subject = "Funding Request Received"
        try:
            from django.core.mail import EmailMessage, BadHeaderError
            msg = EmailMessage(subject, email_content, settings.EMAIL_HOST_USER, [request.user.email, settings.EMAIL_HOST_USER])
            msg.send()
        except BadHeaderError:
            return JsonResponse({'error': "Invalid header found."}, status=400)
        
        return JsonResponse({'message': 'Funding Request Received'}, status=200)
    
    return HttpResponseForbidden()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test(request):
    response = nowpayments_api_client('currencies?fixed_rate=true', 'GET')
    return JsonResponse({'response': response})
