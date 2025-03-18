from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.views import *
import json
import requests

import secrets
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from .models import *
from authentication.models import Profile
from django.core.mail import BadHeaderError, EmailMessage
from django.template.loader import render_to_string 
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from core.models import *
from decouple import config
from datetime import datetime, date

# Some comments
def generate_unique_nickname():
    while True:
        nickname = secrets.token_hex(8)
        if not Card.objects.filter(nickname=nickname).exists():
            return str(nickname)

@login_required
def cards(request):
    cards = Card.objects.filter(user=request.user)
    card_profit = get_object_or_404(CardProfitDeclaration, pk=1)
    card_count = Card.objects.filter(user=request.user).count()
    critical_broadcasts = CriticalBroadcast.objects.filter(active=True)
    today = date.today()
    context = {
        'cards': cards,
        'critical_broadcasts': critical_broadcasts,
        'today': today,
        'maintenance_fee': f"{card_profit.card_maintenance_fee + Decimal('1.5')}", 
        'card_count': card_count
    }
    return render(request, 'cards.html', context)


@login_required
def create_card(request):
    if request.method == "POST":
        str_amount = request.POST.get("amount")
        card_creation_fee = Decimal(10)
        amount = Decimal(str_amount) - card_creation_fee
        card_color = request.POST.get("card_color")
        brand = request.POST.get("brand")
            
        if  Decimal(str_amount) < Decimal(15):
            messages.error(request, "Amount must be a number not less than $15")
            return redirect('cards')
            
        elif Decimal(str_amount) > Decimal(990):
            messages.error(request, "Amount must not exceed $1000.")
            return redirect('cards')
            
        if brand == "MasterCard":
            purpose = "general"
        elif brand == "Visa":
            purpose = "media"
            
        profile = Profile.objects.get(user=request.user)
        if profile.wallet_balance < Decimal(str_amount):
            messages.error(request, "Insufficient balance.")
            return redirect('cards')
        
        if brand == "MasterCard":
            payload = {
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "nickname": generate_unique_nickname(),
                "purpose": purpose,
                "type": "premium",
                "card_amount": f"{amount}"
            }
        elif brand == "Visa":
            payload = {
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "nickname": generate_unique_nickname(),
                "purpose": purpose,
                "type": "premium",
                "spending_limit": 50000,
                "spending_control": "lifetime",
                "card_amount": f"{amount}"
            }
        
        response = AlphaspaceAPIClient('alpha/cards', 'POST', data=payload)
        
        if response.get('error') is None:
            card_id = response['data']['card']['id']
            card_response = AlphaspaceAPIClient(f'alpha/cards/{card_id}', 'GET')
            if card_response.get('error') is None: 
                nickname = card_response['data']['card']['nickname']
                balance = response['data']['card']['balance']
                type = card_response['data']['card']['type']
                purpose = card_response['data']['card']['purpose']
                card_token = card_response['data']['card']['card_token']
                card_number = card_response['data']['card']['card_number']
                card_masked_number = card_response['data']['card']['masked_number']
                card_cvv = card_response['data']['details']['card_cvv']
                state = card_response['data']['card']['state']
                card_expiration_date = f"{card_response['data']['details']['card_exp_month']}/{card_response['data']['details']['card_exp_year']}"
                billing_address_line_1 = card_response['data']['billing']['AdrLine1']
                billing_address_line_2 = card_response['data']['billing']['AdrLine2']
                billing_address_city = card_response['data']['billing']['City']
                billing_address_state = card_response['data']['billing']['State']
                billing_address_country = card_response['data']['billing']['Country']
                billing_address_zip_code = card_response['data']['billing']['ZipCode']
            else:
                messages.error(request, f"{response['message']}")
                return redirect('cards')
        else:
            messages.error(request, f"{response['message']}")
            return redirect('cards')
        
        Card.objects.create(user=request.user, 
            card_id=card_id, 
            nickname=nickname, 
            type=type, 
            purpose=purpose, 
            card_token=card_token, 
            card_number=card_number,
            card_masked_number=card_masked_number,
            card_cvv=card_cvv,
            balance=balance, 
            state=state, 
            card_color=card_color,
            brand=brand,
            card_expiration_date=card_expiration_date,
            billing_address_line_1=billing_address_line_1,
            billing_address_line_2=billing_address_line_2,
            billing_address_city=billing_address_city,
            billing_address_state=billing_address_state,
            billing_address_zip_code=billing_address_zip_code,
            billing_address_country=billing_address_country,
            card_creation_response=response,
            last_card_activity_response=card_response
        )
        
        WalletTransaction.objects.create(user=request.user, purpose=f"Card Creation Fee - {card_masked_number}", amount=card_creation_fee, credit=False)    
        WalletTransaction.objects.create(user=request.user, purpose=f"Card Funding - {card_masked_number}", amount=amount, credit=False)
        
        account, _ = Account.objects.get_or_create(id=1)
        account.total_card_creation_profit += Decimal('10')
        account.save()
        
        profile.deduct_from_wallet_balance(Decimal(str_amount))
            
        return redirect('cards')
    
    return HttpResponseForbidden()


@login_required
def freeze_and_unfreeze_card(request, card_id):
    if request.method == "POST":
        card = Card.objects.filter(user=request.user, card_id=card_id).first()

        if card:
            if card.state == "Active":
                payload = {
                    "status": "deactivate"
                }
                
                response = AlphaspaceAPIClient(f'alpha/cards/change-status/{card_id}', 'POST', data=payload)
                
                if response.get('error') is not None:
                    message = response['message']
                    return JsonResponse({'message': message})
                card.state = "Deactivated"
                message = "Card Frozen Successfully"
            else:
                payload = {
                    "status": "activate"
                }
                
                response = AlphaspaceAPIClient(f'alpha/cards/change-status/{card_id}', 'POST', data=payload)
                
                if response.get('error') is not None:
                    message = response['message']
                    return JsonResponse({'message': message})
                card.state = "Active"
                message = "Card Activated Successfully"
            card.save()
            return JsonResponse({'message': message})
        return HttpResponseForbidden()
    return HttpResponseForbidden()


@login_required
def fund_card(request, card_id):
    if request.method == "POST":
        str_amount = request.POST.get("amount")
        amount = Decimal(str_amount)

        card = Card.objects.filter(user=request.user, card_id=card_id).first()
        profile = Profile.objects.get(user=request.user)

        if request.user != card.user:
            return HttpResponseForbidden()

        if amount > request.user.profile.wallet_balance:
            messages.error(request, "Insufficient funds: You cannot fund the card with an amount greater than your current wallet balance.")
            return redirect('cards')
            
        if amount < 3:
            messages.error(request, "Amount to fund must be greater than or equal to $3 to fund your card.")
            return redirect('cards')
            
        elif amount > 10000:
            messages.error(request, "Amount to fund must not exceed $10,000.")
            return redirect('cards')
        
        payload = {
            "card": card_id,
            "amount": f"{amount}",
        }
        
        response = AlphaspaceAPIClient('alpha/cards/add-funds', 'POST', data=payload)
        
        if response.get('error') is not None:
            messages.error(request, f"{response['message']}")
            return redirect('cards')
        
        WalletTransaction.objects.create(user=card.user, purpose=f"Card Funding - {card.card_masked_number}", amount=amount, credit=False)
        card.add_to_card_balance(amount)
        
        subject = "Card Funding Successful"
        email_template_name = "card_email_templates/card_funding_successful.html"
        c = {
            "first_name": card.user.first_name,
            "last_name": card.user.last_name,
            'amount_funded': amount,
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
        return redirect('cards')
    
    return HttpResponseForbidden()



@login_required
def withdraw_from_card(request, card_id):
    if request.method == "POST":
        str_amount = request.POST.get("amount")
        amount = Decimal(str_amount)

        card = Card.objects.filter(user=request.user, card_id=card_id).first()
        profile = Profile.objects.get(user=request.user)

        if request.user != card.user:
            return HttpResponseForbidden()

        if amount > card.balance:
            messages.error(request, "Insufficient funds: You cannot withdraw an amount greater than your current card balance to your wallet.")
            return redirect('cards')
        
        if card.balance < amount + 1:
            messages.error(request, "Insufficient funds: Your card balance cannot be less than $1 after the withdrawal.")
            return redirect('cards')
            
        if amount < 1:
            messages.error(request, "Amount to withdraw must be greater than or equal to $1 to withdraw from card.")
            return redirect('cards')
        elif amount > 10000:
            messages.error(request, "Amount to withdraw must not exceed $10,000.")
            return redirect('cards')

        payload = {
            "card": card_id,
            "amount": f"{amount}",
        }
        
        response = AlphaspaceAPIClient('alpha/cards/withdraw-funds', 'POST', data=payload)
        
        if response.get('error') is not None:
            messages.error(request, f"{response['message']}")
            return redirect('cards')
            
        card.deduct_from_card_balance(amount)
        WalletTransaction.objects.create(user=card.user, purpose=f"Card Withdrawal - {card.card_masked_number}", amount=amount, credit=True)
        
        subject = "Card Withdrawal Successful"
        email_template_name = "card_email_templates/card_withdrawal_successful.html"
        c = {
            "first_name": card.user.first_name,
            "last_name": card.user.last_name,
            'amount_withdrawn': amount,
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

        return redirect('cards')
    
    return HttpResponseForbidden()

@login_required
def cancel_card(request, card_id):
    if request.method == "POST":
        card = Card.objects.filter(user=request.user, card_id=card_id).first()
        profile = Profile.objects.get(user=request.user)

        if request.user != card.user:
            return HttpResponseForbidden()

        response = AlphaspaceAPIClient(f'alpha/cards/{card_id}', 'DELETE')
                
        if response.get('error') is not None:
            messages.error(request, f"{response['message']}")
            return redirect('cards')
        
        if card.balance > Decimal(0):
            profile.add_to_wallet_balance(card.balance)
            WalletTransaction.objects.create(user=card.user, purpose=f"Card Withdrawal - {card.card_masked_number}", amount=card.balance, credit=True)
        
            subject = "Card Withdrawal Successful"
            email_template_name = "card_email_templates/card_withdrawal_successful.html"
            c = {
                "first_name": card.user.first_name,
                "last_name": card.user.last_name,
                'amount_withdrawn': card.balance,
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
            
        card.delete()
        messages.success(request, "Card Deleted Successfully")
        return redirect('cards')
    
    return HttpResponseForbidden()

def card_transactions(request, card_id):
    if request.method == "GET":
        card = Card.objects.filter(user=request.user, card_id=card_id).first()
        transactions = AlphaspaceAPIClient(f'alpha/reports/view-cards-transactions?card={card.card_id}', 'GET')
    
        filtered_transactions = []
        for transaction in transactions['data']['data']:
            filtered_transactions.append({
                'currency': transaction['currency'],
                'merchant': transaction['merchant'],
                'description': transaction['description'],
                'amount': transaction['amount'],
                'date_created': transaction['date_created'],
            })
    
        return JsonResponse({'transactions': filtered_transactions})
    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)
    
def card_statement(request, card_id):
    card = Card.objects.filter(user=request.user, card_id=card_id).first()
    if card.user != request.user:
        return HttpResponseForbidden()
    if request.method == "GET":
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        email = request.GET.get('email')
        first_name = request.GET.get('first_name')
        last_name = request.GET.get('last_name')
        billing_address_line_1 = request.GET.get('billing_address_line_1')
        billing_address_line_2 = request.GET.get('billing_address_line_2')
        billing_address_city = request.GET.get('billing_address_city')
        billing_address_state = request.GET.get('billing_address_state')
        billing_address_country = request.GET.get('billing_address_country')
        billing_address_zip_code = request.GET.get('billing_address_zip_code')
        
        if start_date:
            api_start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%m-%d-%Y")
            verbose_start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%B %d, %Y")
        
        if end_date:
            api_end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%m-%d-%Y")
            verbose_end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%B %d, %Y")
        
        transactions = AlphaspaceAPIClient(f'alpha/reports/search-cards-transactions?card={card.card_id}&start_date={start_date}&end_date={end_date}', 'GET')
        
        filtered_transactions = []
        if not len(transactions['data'][0]) == 0:
            for transaction in transactions['data'][0]['data']:
                date_created_str = transaction['date_created']
    
                date_created = datetime.strptime(date_created_str, "%Y-%m-%d %H:%M:%S")
                
                date_only = date_created.strftime("%m-%d-%Y")
                time_only = date_created.strftime("%H:%M:%S")
                filtered_transactions.append({
                    'currency': transaction['currency'],
                    'merchant': transaction['merchant'],
                    'description': transaction['description'],
                    'amount': transaction['amount'],
                    'date_created': date_only,
                    'time_created': time_only,
                })
        
        context = {
            'card': card,
            'start_date': verbose_start_date,
            'end_date': verbose_end_date,
            'transactions': filtered_transactions,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'billing_address_line_1': billing_address_line_1,
            'billing_address_line_2': billing_address_line_2,
            'billing_address_city': billing_address_city,
            'billing_address_state': billing_address_state,
            'billing_address_country': billing_address_country,
            'billing_address_zip_code': billing_address_zip_code,
        }
        return render(request, 'card_statement.html', context)
    elif request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        statement_email = request.POST.get("email")
        card_statement_pdf = request.FILES['card_statement_pdf']
        
        subject = f"{card.user.first_name} {card.user.last_name} - Card Statement"
        email_template_name = "card_email_templates/card_statement.html"
        c = {
            "first_name": card.user.first_name,
            "last_name": card.user.last_name,
            "start_date": start_date,
            "end_date": end_date,
            "card_masked_number": card.card_masked_number
        }
        email = render_to_string(email_template_name, c)
        try:
            if statement_email.strip() == card.user.email:
                msg = EmailMessage(subject, email, settings.EMAIL_HOST_USER, [card.user.email, "info@bfree.cards"])
            else:
                msg = EmailMessage(subject, email, settings.EMAIL_HOST_USER, [card.user.email, statement_email.strip(), "info@bfree.cards"])
            msg.content_subtype = 'html'
            msg.attach(card_statement_pdf.name, card_statement_pdf.read(), 'application/pdf')
            msg.send()
        except BadHeaderError:
            return HttpResponse('Invalid header found.')
            
    return HttpResponseForbidden()
    
def test(request):
    #payload = {
    #    "channel": "web",
    #    "type": "purchase",
    #    "currency": "USD",
    #    "merchant": {
    #        "category": "Tech",
    #        "merchantId": "uuutuy5888585",
    #        "name": "Google",
    #        "city": "London",
    #        "state": "UK",
    #        "country": "GB"
    #    },
    #    "cardId": "667beb4bbceecdb5dcd94d7b",
    #    "amount": 10
    #}
    response = AlphaspaceAPIClient(f'alpha/reports/view-cards-transactions?card=9d911dda-d9da-4c0a-add0-62dd5c1fb4e2', 'GET')
    return render(request, 'test.html', {'response': response})



