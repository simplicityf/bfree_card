import hashlib
import hmac
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from decouple import config
from .models import *
from core.views import *
import json
from card.models import *
from core.models import *
from django.core.mail import BadHeaderError, EmailMessage
from django.template.loader import render_to_string 
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from authentication.models import Profile

def np_signature_check(np_secret_key, np_x_signature, message):
    sorted_msg = json.dumps(message, separators=(',', ':'), sort_keys=True)
    digest = hmac.new(
        str(np_secret_key).encode(), 
        f'{sorted_msg}'.encode(),
        hashlib.sha512
    )
    signature = digest.hexdigest()
    return hmac.compare_digest(signature, np_x_signature)


@csrf_exempt
def nowpayments(request):
    if request.method == 'POST':
        secret_hash = config('NOWPAYMENTS_IPN_KEY')
        
        signature = request.META.get('HTTP_X_NOWPAYMENTS_SIG')
        request_json = request.body.decode('utf-8')
        payload = json.loads(request_json)
        
        if not signature or not np_signature_check(secret_hash, signature, payload):
            payload_exists = Payload.objects.filter(payload=payload).exists()
            if not payload_exists:
                Payload.objects.create(
                    source="NowPayments",
                    event=f"Webhook Authorization Failed",
                    payload=payload
                )
            return HttpResponse(status=401)
        
        try:
            payload_exists = Payload.objects.filter(payload=payload).exists()
            if not payload_exists:
                event = payload['payment_status']
                Payload.objects.create(
                    source="NowPayments",
                    event=event,
                    payload=payload
                )
                
                event = payload['payment_status']
                if event == 'finished':
                    transaction_obj = get_object_or_404(CryptoTransaction, transaction_id=payload['invoice_id'], amount=Decimal(payload['price_amount']))
                    
                    if transaction_obj.processed:
                        return HttpResponse(status=400)
                        
                    transaction_obj.processed = True
                    
                    WalletTransaction.objects.create(
                        user=transaction_obj.user,
                        purpose="Credit",
                        fee_percentage=10,
                        amount=payload['price_amount'],
                        credit=True
                    )
                    transaction_obj.save()
                    
                    fee = transaction_obj.amount * 10 / 100
                    amount_credited = transaction_obj.amount - fee
                    
                    subject = "Wallet Funding Successful"
                    email_template_name = "crypto_transaction_email_templates/wallet_funding_successful.html"
                    c = {
                        "first_name": transaction_obj.user.first_name,
                        "last_name": transaction_obj.user.last_name,
                        'pay_currency': payload['pay_currency'].upper(),
                        'pay_address' : payload['pay_address'],
                        'amount_credited': amount_credited,
                        'fee': fee,
                        'wallet_balance': transaction_obj.user.profile.wallet_balance,
                        'dateTime': timezone.now(),
                    }
                    email = render_to_string(email_template_name, c)
                    try:
                        msg = EmailMessage(subject, email, settings.EMAIL_HOST_USER, [transaction_obj.user.email])
                        msg.content_subtype = 'html'
                        msg.send()
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                return HttpResponse(status=200)
            return HttpResponse(status=200)
        
        except json.JSONDecodeError:
            return HttpResponse(status=400)
    
    return HttpResponse(status=405)




@csrf_exempt
def alphaspace(request):
    if request.method == 'POST':
        payload = json.loads(request.body)
        
        try:
            payload_exists = Payload.objects.filter(payload=payload).exists()
            if not payload_exists:
                event = payload['action']
                Payload.objects.create(
                    source="Alphaspace",
                    event=event,
                    payload=payload
                )
                
                if event == 'card_transaction':
                    card_id = payload['card_id']
                    card = Card.objects.filter(card_id=card_id).first()
                    if card:
                        state = payload['state']
                        if card.brand == "MasterCard":
                            response = AlphaspaceAPIClient(f'alpha/cards/balance/{card.card_id}/', 'GET')
                            balance = response['data']['available']
                            card.last_card_activity_response = response
                            card.balance = balance
                            card.save()
                        else:
                            if state == "Payment approved - pending" or state == "Approved or completed successfully":
                                card.deduct_from_card_balance(Decimal(payload['usd_amount']))
                            elif state == "Payment declined":
                                card.add_to_card_balance(Decimal(payload['usd_amount']))
                            elif state == "Reversal settled":
                                card.add_to_card_balance(Decimal(payload['usd_amount']))
                        
                        
                        if state == "Payment settled":
                            account, _ = Account.objects.get_or_create(id=1)
                            account.total_card_debit_withdrawals += Decimal(payload['usd_amount'])
                            account.save()
                            return HttpResponse(status=200)
                        
                        if state == "Payment approved - pending" or state == "Approved or completed successfully":
                            subject = "Card Transaction Successful"
                        elif state == "Payment declined":
                            subject = "Card Transaction Declined"
                        elif state == "Reversal settled":
                            subject = "Card Transaction Reversed"
                            
                        email_template_name = "card_email_templates/card_transaction.html"
                        
                        c = {
                            "subject": subject,
                            "first_name": card.user.first_name,
                            "last_name": card.user.last_name,
                            'transaction_type': payload['transaction_type'],
                            'amount_debited': payload['usd_amount'],
                            'card_number': card.card_masked_number,
                            'balance': card.balance,
                            'merchant': payload['merchant_name'],
                            'transaction_reference': payload['transaction_reference'],
                            'dateTime': payload['transaction_date'],
                        }
                        email = render_to_string(email_template_name, c)
                        try:
                            msg = EmailMessage(subject, email, settings.EMAIL_HOST_USER, [card.user.email])
                            msg.content_subtype = 'html'
                            msg.send()
                        except BadHeaderError:
                            return HttpResponse('Invalid header found.')
                elif event == 'card_deletion':
                    card_id = payload['card_id']
                    card = Card.objects.filter(card_id=card_id).first()
                    if card:
                        card.delete()
                elif event == 'card_maintenance':
                    card_id = payload['card_id']
                    card = Card.objects.filter(card_id=card_id).first()
                    profile = Profile.objects.get(user=card.user)
                    card_profit = get_object_or_404(CardProfitDeclaration, pk=1)
                    
                    if card:
                        payload = {
                            "card": card_id,
                            "amount": f"{card_profit.card_maintenance_fee}",
                        }
                        
                        response = AlphaspaceAPIClient('alpha/cards/withdraw-funds', 'POST', data=payload)
                        
                        if response.get('error') is not None:
                            profile.deduct_from_wallet_balance(card_profit.card_maintenance_fee, allow_negative=True)
                            WalletTransaction.objects.create(user=card.user, purpose=f"Card Maintenance Fee - {card.card_number_mask}", amount=card_profit.card_maintenance_fee, is_credit=False)
                        else:
                            card.deduct_from_card_balance(card_profit.card_maintenance_fee)
                            
                        account, _ = Account.objects.get_or_create(id=1)
                        account.total_card_maintenance_profit += card_profit.card_maintenance_fee
                        account.save()
                        
                        subject = "Card Maintenace Fee Charged"
                        email_template_name = "card_email_templates/card_maintenance_fee_charged.html"
                        c = {
                            "first_name": card.user.first_name,
                            "last_name": card.user.last_name,
                            'maintenance_fee': f"{card_profit.card_maintenance_fee + Decimal('1.5')}",
                            'card_number': card.card_masked_number,
                            'brand': card.brand,
                            'balance': card.balance,
                            'wallet_balance': card.user.profile.wallet_balance,
                            'dateTime': timezone.now(),
                        }
                        email = render_to_string(email_template_name, c)
                        try:
                            msg = EmailMessage(subject, email, settings.EMAIL_HOST_USER, [card.user.email])
                            msg.content_subtype = 'html'
                            msg.send()
                        except BadHeaderError:
                            return HttpResponse('Invalid header found.')

                return HttpResponse(status=200)
            return HttpResponse(status=200)
        
        except json.JSONDecodeError:
            return HttpResponse(status=400)
    else:
        return HttpResponse(status=405)


