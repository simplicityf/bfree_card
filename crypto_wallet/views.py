from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.views import nowpayments_api_client
import requests
from core.models import CryptoTransaction
from crypto_wallet.models import CryptoFundingRequest
from django.http import JsonResponse, HttpResponseForbidden
import uuid
from .models import *
from core.models import *

@login_required
def crypto(request):
    if request.method == "POST":
        amount = request.POST.get("amount")
        
        if not amount:
            return JsonResponse({'error': "Amount is required."}, status=400)
        
        if amount and amount.isdigit() and int(amount) > 2000:
            return JsonResponse({'error': "Amount mustn't be more than $2000"}, status=400)

        payload = {
          "price_amount": amount,
          "price_currency": "usd",
          "is_fee_paid_by_user": True,
          "ipn_callback_url": "https://crypto.bfree.cards/webhook/nowpayments",
          "success_url": "https://crypto.bfree.cards/crypto/",
          "cancel_url": "https://crypto.bfree.cards/crypto/"
        }

        response = nowpayments_api_client('invoice', 'POST', data=payload)

        if 'id' in response:
            CryptoTransaction.objects.create(user=request.user, transaction_id=response['id'], amount=amount, invoice_url=response['invoice_url'])
            return JsonResponse({'invoice_url': response['invoice_url']})
        else:
            return JsonResponse({'error': response}, status=400)
    crypto_addresses = CryptoAddress.objects.all()
    critical_broadcasts = CriticalBroadcast.objects.filter(active=True)
    
    return render(request, 'crypto.html', {'crypto_addresses': crypto_addresses, 'critical_broadcasts': critical_broadcasts,})
    
@login_required
def crypto_funding_request(request):
    if request.method == "POST":
        amount = request.POST.get("funding_request_amount")
        transaction_id = request.POST.get("transaction_id")
        address_id = request.POST.get("address_id")
        if not amount or not transaction_id:
            return JsonResponse({'error': "Amount and Transaction ID is required."}, status=400)
        
        if amount and not amount.isdigit():
            return JsonResponse({'error': "Amount must be a numeric value"}, status=400)
        
        CryptoFundingRequest.objects.create(user=request.user, transaction_id=transaction_id, amount=amount)
        address = CryptoAddress.objects.get(id=address_id)
        
        subject = "Funding Request Received"
        email_template_name = "crypto_transaction_email_templates/funding_request_received.html"
        c = {
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            'amount': amount,
            'transaction_id': transaction_id,
            'network_chain': address.network_chain,
            'coin': address.coin,
            'address': address.address,
            'dateTime': timezone.now(),
        }
        email = render_to_string(email_template_name, c)
        try:
            msg = EmailMessage(subject, email, settings.EMAIL_HOST_USER, [request.user.email, settings.EMAIL_HOST_USER])
            msg.content_subtype = 'html'
            msg.send()
        except BadHeaderError:
            return HttpResponse('Invalid header found.')
        return JsonResponse({'message': 'Funding Request Received'}, status=200)
    return HttpResponseForbidden()
    

def test(request):
    response = nowpayments_api_client('currencies?fixed_rate=true', 'GET')
    return render(request, 'test.html', {'response': response})



