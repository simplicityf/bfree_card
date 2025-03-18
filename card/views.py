from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from card.models import *
from authentication.models import AlphaspaceAuthToken
from .models import *
from crypto_wallet.models import *
import requests
import secrets
from decouple import config
import json

from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from datetime import datetime, date
from decimal import Decimal

# --- CARDS LIST ENDPOINT ---
@login_required
def cards(request):
    # Get cards belonging to the user
    cards_qs = Card.objects.filter(user=request.user)
    cards_data = list(cards_qs.values())
    # Get card profit declaration (using primary key 1)
    card_profit = get_object_or_404(CardProfitDeclaration, pk=1)
    card_count = cards_qs.count()
    # Get any active broadcasts
    critical_broadcasts = list(CriticalBroadcast.objects.filter(active=True).values())
    today_str = date.today().isoformat()
    # Calculate maintenance fee by adding 1.5 to the fee
    maintenance_fee = str(card_profit.card_maintenance_fee + Decimal('1.5'))
    data = {
        'cards': cards_data,
        'critical_broadcasts': critical_broadcasts,
        'today': today_str,
        'maintenance_fee': maintenance_fee,
        'card_count': card_count,
    }
    return JsonResponse(data)

# --- CREATE CARD ENDPOINT ---
@login_required
def create_card(request):
    if request.method != "POST":
        return HttpResponseForbidden("Only POST method allowed.")
    
    str_amount = request.POST.get("amount")
    card_creation_fee = Decimal(10)
    try:
        amount = Decimal(str_amount) - card_creation_fee
    except Exception:
        return JsonResponse({"error": "Invalid amount."}, status=400)
    
    card_color = request.POST.get("card_color")
    brand = request.POST.get("brand")
    
    if Decimal(str_amount) < Decimal(15):
        return JsonResponse({"error": "Amount must be not less than $15."}, status=400)
    elif Decimal(str_amount) > Decimal(990):
        return JsonResponse({"error": "Amount must not exceed $1000."}, status=400)
    
    if brand == "MasterCard":
        purpose = "general"
    elif brand == "Visa":
        purpose = "media"
    else:
        purpose = "general"
    
    profile = get_object_or_404(Profile, user=request.user)
    if profile.wallet_balance < Decimal(str_amount):
        return JsonResponse({"error": "Insufficient balance."}, status=400)
    
    # Use your helper function; these are assumed to be defined elsewhere.
    # They generate a unique nickname and call the Alphaspace API.
    nickname = generate_unique_nickname()
    if brand == "MasterCard":
        payload = {
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "nickname": nickname,
            "purpose": purpose,
            "type": "premium",
            "card_amount": f"{amount}"
        }
    elif brand == "Visa":
        payload = {
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "nickname": nickname,
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
            type_card = card_response['data']['card']['type']
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
            return JsonResponse({"error": response.get('message', 'Error retrieving card details.')}, status=400)
    else:
        return JsonResponse({"error": response.get('message', 'Error creating card.')}, status=400)
    
    # Create a new Card instance with the details returned by the API
    card_obj = Card.objects.create(
        user=request.user, 
        card_id=card_id, 
        nickname=nickname, 
        type=type_card, 
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
    
    WalletTransaction.objects.create(
        user=request.user, 
        purpose=f"Card Creation Fee - {card_masked_number}", 
        amount=card_creation_fee, 
        credit=False
    )
    WalletTransaction.objects.create(
        user=request.user, 
        purpose=f"Card Funding - {card_masked_number}", 
        amount=amount, 
        credit=False
    )
    
    account, _ = Account.objects.get_or_create(id=1)
    account.total_card_creation_profit += Decimal('10')
    account.save()
    
    profile.deduct_from_wallet_balance(Decimal(str_amount))
        
    return JsonResponse({"message": "Card created successfully.", "card_id": card_obj.card_id})

# --- FREEZE / UNFREEZE CARD ENDPOINT ---
@login_required
def freeze_and_unfreeze_card(request, card_id):
    if request.method != "POST":
        return HttpResponseForbidden("Only POST method allowed.")
    
    card = Card.objects.filter(user=request.user, card_id=card_id).first()
    if not card:
        return JsonResponse({'error': 'Card not found or unauthorized.'}, status=403)
    
    if card.state == "Active":
        payload = {"status": "deactivate"}
        response = AlphaspaceAPIClient(f'alpha/cards/change-status/{card_id}', 'POST', data=payload)
        if response.get('error') is not None:
            return JsonResponse({'message': response.get('message')}, status=400)
        card.state = "Deactivated"
        message = "Card Frozen Successfully"
    else:
        payload = {"status": "activate"}
        response = AlphaspaceAPIClient(f'alpha/cards/change-status/{card_id}', 'POST', data=payload)
        if response.get('error') is not None:
            return JsonResponse({'message': response.get('message')}, status=400)
        card.state = "Active"
        message = "Card Activated Successfully"
    card.save()
    return JsonResponse({'message': message})

# --- FUND CARD ENDPOINT ---
@login_required
def fund_card(request, card_id):
    if request.method != "POST":
        return HttpResponseForbidden("Only POST method allowed.")
    
    str_amount = request.POST.get("amount")
    try:
        amount = Decimal(str_amount)
    except Exception:
        return JsonResponse({"error": "Invalid amount."}, status=400)
    
    card = Card.objects.filter(user=request.user, card_id=card_id).first()
    profile = get_object_or_404(Profile, user=request.user)
    if not card or request.user != card.user:
        return JsonResponse({"error": "Unauthorized."}, status=403)
    
    if amount > profile.wallet_balance:
        return JsonResponse({"error": "Insufficient funds: Funding amount exceeds your wallet balance."}, status=400)
    if amount < 3:
        return JsonResponse({"error": "Amount must be at least $3 to fund your card."}, status=400)
    if amount > 10000:
        return JsonResponse({"error": "Amount must not exceed $10,000."}, status=400)
    
    payload = {"card": card_id, "amount": f"{amount}"}
    response = AlphaspaceAPIClient('alpha/cards/add-funds', 'POST', data=payload)
    if response.get('error') is not None:
        return JsonResponse({"error": response.get('message')}, status=400)
    
    WalletTransaction.objects.create(
        user=card.user, 
        purpose=f"Card Funding - {card.card_masked_number}", 
        amount=amount, 
        credit=False
    )
    card.add_to_card_balance(amount)
    
    return JsonResponse({"message": "Card funded successfully."})

# --- WITHDRAW FROM CARD ENDPOINT ---
@login_required
def withdraw_from_card(request, card_id):
    if request.method != "POST":
        return HttpResponseForbidden("Only POST method allowed.")
    
    str_amount = request.POST.get("amount")
    try:
        amount = Decimal(str_amount)
    except Exception:
        return JsonResponse({"error": "Invalid amount."}, status=400)
    
    card = Card.objects.filter(user=request.user, card_id=card_id).first()
    profile = get_object_or_404(Profile, user=request.user)
    if not card or request.user != card.user:
        return JsonResponse({"error": "Unauthorized."}, status=403)
    
    if amount > card.balance:
        return JsonResponse({"error": "Insufficient funds: Withdrawal amount exceeds card balance."}, status=400)
    if card.balance < amount + Decimal('1'):
        return JsonResponse({"error": "Insufficient funds: Card balance cannot fall below $1 after withdrawal."}, status=400)
    if amount < 1:
        return JsonResponse({"error": "Withdrawal amount must be at least $1."}, status=400)
    if amount > 10000:
        return JsonResponse({"error": "Withdrawal amount must not exceed $10,000."}, status=400)
    
    payload = {"card": card_id, "amount": f"{amount}"}
    response = AlphaspaceAPIClient('alpha/cards/withdraw-funds', 'POST', data=payload)
    if response.get('error') is not None:
        return JsonResponse({"error": response.get('message')}, status=400)
    
    card.deduct_from_card_balance(amount)
    WalletTransaction.objects.create(
        user=card.user, 
        purpose=f"Card Withdrawal - {card.card_masked_number}", 
        amount=amount, 
        credit=True
    )
    
    return JsonResponse({"message": "Card withdrawal successful."})

# --- CANCEL CARD ENDPOINT ---
@login_required
def cancel_card(request, card_id):
    if request.method != "POST":
        return HttpResponseForbidden("Only POST method allowed.")
    
    card = Card.objects.filter(user=request.user, card_id=card_id).first()
    profile = get_object_or_404(Profile, user=request.user)
    if not card or request.user != card.user:
        return JsonResponse({"error": "Unauthorized."}, status=403)
    
    response = AlphaspaceAPIClient(f'alpha/cards/{card_id}', 'DELETE')
    if response.get('error') is not None:
        return JsonResponse({"error": response.get('message')}, status=400)
    
    if card.balance > Decimal(0):
        profile.add_to_wallet_balance(card.balance)
        WalletTransaction.objects.create(
            user=card.user, 
            purpose=f"Card Withdrawal - {card.card_masked_number}", 
            amount=card.balance, 
            credit=True
        )
    card.delete()
    return JsonResponse({"message": "Card cancelled successfully."})

# --- CARD TRANSACTIONS ENDPOINT ---
@login_required
def card_transactions(request, card_id):
    if request.method != "GET":
        return HttpResponse("Only GET method allowed.", status=405)
    
    card = Card.objects.filter(user=request.user, card_id=card_id).first()
    if not card:
        return JsonResponse({"error": "Unauthorized or card not found."}, status=403)
    
    response = AlphaspaceAPIClient(f'alpha/reports/view-cards-transactions?card={card.card_id}', 'GET')
    filtered_transactions = []
    for transaction in response.get('data', {}).get('data', []):
        filtered_transactions.append({
            'currency': transaction.get('currency'),
            'merchant': transaction.get('merchant'),
            'description': transaction.get('description'),
            'amount': transaction.get('amount'),
            'date_created': transaction.get('date_created'),
        })
    return JsonResponse({'transactions': filtered_transactions})

# --- CARD STATEMENT ENDPOINT ---
@login_required
def card_statement(request, card_id):
    card = Card.objects.filter(user=request.user, card_id=card_id).first()
    if not card or card.user != request.user:
        return JsonResponse({"error": "Unauthorized."}, status=403)
    
    if request.method == "GET":
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        verbose_start_date = None
        verbose_end_date = None
        if start_date:
            try:
                verbose_start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%B %d, %Y")
            except Exception:
                return JsonResponse({"error": "Invalid start_date format. Use YYYY-MM-DD."}, status=400)
        if end_date:
            try:
                verbose_end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%B %d, %Y")
            except Exception:
                return JsonResponse({"error": "Invalid end_date format. Use YYYY-MM-DD."}, status=400)
        
        response = AlphaspaceAPIClient(
            f'alpha/reports/search-cards-transactions?card={card.card_id}&start_date={start_date}&end_date={end_date}', 
            'GET'
        )
        filtered_transactions = []
        data_list = response.get('data', [])
        if data_list and len(data_list) > 0 and data_list[0].get('data'):
            for transaction in data_list[0]['data']:
                try:
                    dt = datetime.strptime(transaction['date_created'], "%Y-%m-%d %H:%M:%S")
                    date_only = dt.strftime("%m-%d-%Y")
                    time_only = dt.strftime("%H:%M:%S")
                except Exception:
                    date_only = transaction.get('date_created')
                    time_only = ""
                filtered_transactions.append({
                    'currency': transaction.get('currency'),
                    'merchant': transaction.get('merchant'),
                    'description': transaction.get('description'),
                    'amount': transaction.get('amount'),
                    'date_created': date_only,
                    'time_created': time_only,
                })
        result = {
            'card_id': card.card_id,
            'start_date': verbose_start_date,
            'end_date': verbose_end_date,
            'transactions': filtered_transactions,
        }
        return JsonResponse(result)
    
    elif request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        statement_email = request.POST.get("email")
        card_statement_pdf = request.FILES.get('card_statement_pdf')
        if not card_statement_pdf:
            return JsonResponse({"error": "PDF file is required."}, status=400)
        
        subject = f"{card.user.first_name} {card.user.last_name} - Card Statement"
        email_content = f"Card statement for card {card.card_masked_number} from {start_date} to {end_date}."
        try:
            recipients = [card.user.email, "info@bfree.cards"]
            if statement_email and statement_email.strip() != card.user.email:
                recipients.append(statement_email.strip())
            msg = EmailMessage(subject, email_content, settings.EMAIL_HOST_USER, recipients)
            msg.content_subtype = 'html'
            msg.attach(card_statement_pdf.name, card_statement_pdf.read(), 'application/pdf')
            msg.send()
        except BadHeaderError:
            return JsonResponse({"error": "Invalid header found."}, status=400)
            
        return JsonResponse({"message": "Card statement emailed successfully."})
    
    return JsonResponse({"error": "Invalid HTTP method."}, status=405)

# --- TEST ENDPOINT ---
@login_required
def test(request):
    response_data = AlphaspaceAPIClient(
        f'alpha/reports/view-cards-transactions?card=9d911dda-d9da-4c0a-add0-62dd5c1fb4e2', 
        'GET'
    )
    return JsonResponse({'response': response_data})
