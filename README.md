# Getting started

```git clone https://github.com/simplicityf/bfree_card.git```
```cd bfree_card```
- Create and activate virtual env
<!-- On mac or linux -->
```python3 -m venv .venv``` 
```source .venv/bin/activate```

<!-- On windows -->
```python -m venv .venv```
```.venv/scripts/activate```

- To get started

<!-- To make migration -->
```python manage.py migrate```
<!-- To run server  -->
```python manage.py runserver``` 

success_response :
``` Django version 5.1.7, using settings 'Bfree.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C. ```

# To test routes

- Signup route
```POST: http://127.0.0.1:8000/auth/signup```
It is in json format
```
{
    "email": "",
    "password": "",
    "first_name": "",
    "last_name": "",
    "phone_number": "",
    "country": ""
}

and also it will return a json response
{
    "message": "Email verification OTP sent."
}
```
- To verify email verification code
``` 
POST: http://127.0.0.1:8000/auth/email-verification-otp
Data to send: {
    "otp": "otpcode"
}
response: {
    "message": "Signup successful.",
    "token": "8cb3193119eea9576bc967c682898fd7b1322d1d"
}
```
- Forgot password 
```POST: http://127.0.0.1:8000/auth/password-reset
{ "email": "email@example.com"} for this an otp for password reset will be sent to user mailbox

To verify otp and change password
POST: http://127.0.0.1:8000/auth/password-reset-otp
{"otp": "otpcode",
 "new_password": "newpassword!",
 "confirm_password": "confirmpassword"} 

 Success response: {
    "message": "Password reset successfully."
}
```
- Signin
```POST: http://127.0.0.1:8000/auth/signin
{ "email": "email@example.com", "password": "password"} an otp to verify signin will be sent to user
Success response: {"message": "OTP sent. Please verify."}

To verify sigin otp
POST: http://127.0.0.1:8000/auth/signin-otp
{"otp": "otpcode"}
success response: {"message": "Login successful.",
    "token": "8cb3193119eea9576bc967c682898fd7b1322d1d"}
```

### Note: Please store token in local storage, session storage, or an HTTP-only cookie (Authorization: Token usergeneratedtoken)

- To get or update user profile
```GET: http://127.0.0.1:8000/auth/profile```
success response: {
    "profile": {
        "email": "email@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "profile_picture": null,
        "phone_number": "123456789",
        "address": null,
        "city": null,
        "state": null,
        "country": "country",
        "wallet_id": "id",
        "wallet_balance": "0.00"
    }
}
```POST: http://127.0.0.1:8000/auth/profile```
### If User email is chage, an otp will be sent to user mailbox, to veriy otp for changing email: POST: http://127.0.0.1:8000/auth/verify_email_change, {"otp": "otpcode"}, the user will be prompt to login in again.

- To check security update ```GET: http://127.0.0.1:8000/auth/security```

- To change password when logged in
```POST: http://127.0.0.1:8000/auth/send-change-password-otp  {"new_password": "password", "confirm_password": "password"}```, an otp code will be sent to email
To verify the otp for change password: ```POST: http://127.0.0.1:8000/auth/validate-change-password-otp {"otp": "otpcode}```, success response{ "message": "Password Successfully Changed." }

# Card Route (Funding Account, Funding other person account, create a new card)
- To get user card(s) ```GET: http://127.0.0.1:8000/card/``` success_response: { "cards": [], "critical_broadcasts": [], "today": "2025-03-19", "maintenance_fee": "2.00", "card_count": 0 }

- To fund account ```POST: http://127.0.0.1:8000/crypto/  request_to_send {"amount": "100"}``` success_response: { "invoice_url": "https://sandbox.nowpayments.io/payment/?iid=5190721729" }-- User can click on the link and follow the steps and can choose the steps or crypto currency to buy(fund account with)

- To get list of crypto currency addresses ```GET: http://127.0.0.1:8000/crypto/```
success_response: {
    "crypto_addresses": [
        {
            "id": 10,
            "address": "",
            "coin": "BTC",
            "network_chain": "BITCOIN"
        },
        {
            "id": 11,
            "address": "",
            "coin": "USDT",
            "network_chain": "USDT BEP20"
        },
        {
            "id": 12,
            "address": "",
            "coin": "USDT",
            "network_chain": "USDT ERC20"
        },
        {
            "id": 13,
            "address": "",
            "coin": "LTC",
            "network_chain": "LTC"
        },
        {
            "id": 14,
            "address": "",
            "coin": "SOL",
            "network_chain": "SOLANA"
        },
        {
            "id": 15,
            "address": "",
            "coin": "USDT",
            "network_chain": "USDT TRC20"
        }
    ],
    "critical_broadcasts": []
}

- Funcing request **This endpoint is used after initiating a crypto invoice (via the crypto endpoint) and is not directly pulling funds—it’s recording the user’s request to have those funds credited once the payment is confirmed.** : ```Post: rypto/crypto_funding_request```
data_to_send:{
  "funding_request_amount": "500",
  "transaction_id": "01",
  "address_id": "12"
}  
The transaction_id comes from successful payment that went through, and the address_id comes from crypto addresses id {
            "id": 15,
            "address": "",
            "coin": "",
            "network_chain": "USDT TRC20"
        }
success_response: {
    "message": "Funding Request Received"
}

- To create a new card ```POST: http://127.0.0.1:8000/card/create_card```
data_to_send: {
  "amount": "0",
  "card_color": "blue",
  "brand": "MasterCard"
}

- To Get list of card transactions: ```GET: http://127.0.0.1:8000/card/card_transactions/{card_id}``` success_response: { "transactions": []}

- To Get card statements: ```GET: http://127.0.0.1:8000/card/card_statement/{card_id}```
success_response: { "card_id": "dummy_card_id", "start_date": null, "end_date": null, "transactions": []}

- To Freeze and Unfreeze a card: ```POST: http://127.0.0.1:8000/card/freeze_and_unfreeze_card/{card_id}``` **It is a toggle switch Return a JSON response with a message like "Card Frozen Successfully" or "Card Activated Successfully".**

- To Fund card: ```POST: http://127.0.0.1:8000/card/fund_card/{card_id}```
date to send: {"amount": "0000"}
success_response: {"message": "Card funded successfully."}

- To withdraw from card: ```POST http://127.0.0.1:8000/card/withdraw_from_card/dummy_card_id```
data_to_send: {"amount": "0000"}
response_status: {"message": "Card withdrawal successful"}

- To cancel card: ```POST: http://127.0.0.1:8000/card/cancel_card/dummy_card_id```
success_response: {"message": "Card cancelled successfully."}

- To get user dashboard (Landing page/ Home page) ```GET: http://127.0.0.1:8000/core/```
It will return this data:  data = {
        'card_count': card_count,
        'cards': cards,
        'critical_broadcasts': critical_broadcasts,
        'wallet_history_transaction': wallet_history_transaction,
        'transaction_count': transaction_count
    }