# Getting started

```git clone ```
```cd ```

# To test routes

- Signup route
```http://127.0.0.1:8000/auth/signup```
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
http://127.0.0.1:8000/auth/email-verification-otp
Data to send: {
    "otp": "45053"
}
response: {
    "message": "Signup successful.",
    "token": "8cb3193119eea9576bc967c682898fd7b1322d1d"
}
```