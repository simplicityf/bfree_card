# Getting started

```git clone ```
```cd ```

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

### Note: Please store token in local storage, session storage, or an HTTP-only cookie

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