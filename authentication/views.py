import json
import secrets
import dateutil.parser
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import BadHeaderError, EmailMessage
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from core.models import CriticalBroadcast
from authentication.models import Profile, LoginDetail
from authentication.forms import SignupForm, ProfileForm
from .forms import validate_password_strength
from user_agents import parse
from django.conf import settings
from rest_framework.authtoken.models import Token
@login_required
def security(request):
    """
    Returns the user's obfuscated email and any active critical broadcasts.
    """
    email = request.user.email
    try:
        first_part, last_part = email.split('@')
    except ValueError:
        first_part, last_part = email, ''
    if len(first_part) > 4:
        obfuscated_first = '*' * (len(first_part) - 4) + first_part[-4:]
    else:
        obfuscated_first = first_part
    obfuscated_email = f"{obfuscated_first}@{last_part}"
    
    critical_broadcasts = list(CriticalBroadcast.objects.filter(active=True).values())
    return JsonResponse({
        "email": obfuscated_email,
        "critical_broadcasts": critical_broadcasts
    })


def password_reset(request):
    """
    API endpoint to trigger a password reset email.
    Expects a POST request with an "email" parameter.
    """
    if request.method == "POST":
        email = request.POST.get("email")
        if not email:
            return JsonResponse({"error": "Email is required."}, status=400)
        
        password_reset_form = PasswordResetForm({"email": email})
        if password_reset_form.is_valid():
            associated_users = User.objects.filter(email=email)
            if associated_users.exists():
                for user in associated_users:
                    subject = "Bfree Password Reset Request"
                    email_template_name = "email_templates/password_reset_email.html"
                    context = {
                        "email": user.email,
                        "domain": request.get_host(),
                        "site_name": "Interface",
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "token_expiry_minutes": settings.PASSWORD_RESET_TIMEOUT // 60,
                        "token": default_token_generator.make_token(user),
                        "protocol": "http",
                    }
                    email_content = render_to_string(email_template_name, context)
                    try:
                        msg = EmailMessage(subject, email_content, settings.EMAIL_HOST_USER, [user.email])
                        msg.content_subtype = "html"
                        msg.send()
                    except BadHeaderError:
                        return JsonResponse({"error": "Invalid header found."}, status=400)
            return JsonResponse({"message": "If that email exists, password reset instructions have been sent."})
        else:
            return JsonResponse({"error": "Invalid email."}, status=400)
    return JsonResponse({"error": "Only POST method allowed."}, status=405)


@sensitive_post_parameters()
@csrf_protect
@never_cache
def Signin(request):
    """
    API endpoint for initial login.
    Expects POST with "email" and "password".
    On success, generates an OTP and sends it to the user.
    """
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        if not (email and password):
            return JsonResponse({"error": "Email and password are required."}, status=400)
        
        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            return JsonResponse({"error": "Wrong login details. Please try again."}, status=400)
        
        if not user.check_password(password):
            return JsonResponse({"error": "Wrong login details. Please try again."}, status=400)
        
        login_otp = str(secrets.randbelow(90000) + 10000)
        request.session["login_otp"] = login_otp
        request.session["user_id"] = user.id
        request.session["user_email"] = user.email
        request.session["user_password"] = password
        request.session["login_otp_timestamp"] = timezone.now().isoformat()
        
        subject = "Bfree Login Verification Code"
        email_template_name = "email_templates/login_otp_email_template.html"
        context = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "login_otp": login_otp,
        }
        email_content = render_to_string(email_template_name, context)
        try:
            msg = EmailMessage(subject, email_content, settings.EMAIL_HOST_USER, [user.email])
            msg.content_subtype = "html"
            msg.send()
        except BadHeaderError:
            return JsonResponse({"error": "Invalid header found."}, status=400)
        return JsonResponse({"message": "OTP sent. Please verify."})
    return JsonResponse({"error": "Only POST method allowed."}, status=405)


@sensitive_post_parameters()
@csrf_protect
@never_cache
def signin_otp(request):
    """
    API endpoint to verify the login OTP.
    Expects POST with "otp".
    On successful OTP verification, returns a token for API authentication.
    """
    if not request.session.get("user_email"):
        return JsonResponse({"error": "Session expired, please sign in again."}, status=400)
    if request.method == "POST":
        user_entered_otp = request.POST.get("otp")
        saved_otp = request.session.get("login_otp")
        otp_timestamp = request.session.get("login_otp_timestamp")
        if not otp_timestamp:
            return JsonResponse({"error": "OTP timestamp missing."}, status=400)
        otp_timestamp_datetime = dateutil.parser.parse(otp_timestamp)
        
        if saved_otp:
            if (timezone.now() - otp_timestamp_datetime).total_seconds() > 300:
                return JsonResponse({"error": "Expired OTP Code. Please resend OTP."}, status=400)
            if user_entered_otp == saved_otp:
                try:
                    user = User.objects.get(id=request.session.get("user_id"))
                except User.DoesNotExist:
                    return JsonResponse({"error": "User not found."}, status=400)
                # Clear OTP from session
                del request.session["login_otp"]
                # Create or get token for the user
                token, created = Token.objects.get_or_create(user=user)
                # (Optionally) Log the user in via session if needed:
                # login(request, user)
                return JsonResponse({"message": "Login successful.", "token": token.key})
            return JsonResponse({"error": "Your verification code is incorrect."}, status=400)
        return JsonResponse({"error": "Incorrect or expired OTP. Please try again."}, status=400)
    return JsonResponse({"error": "Only POST method allowed."}, status=405)


@sensitive_post_parameters()
@csrf_protect
@never_cache
def Signup(request):
    """
    API endpoint for user signup.
    Expects POST with "email", "password", "first_name", "last_name",
    "phone_number", and "country".
    Generates an OTP for email verification.
    """
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        phone_number = request.POST.get("phone_number")
        country = request.POST.get("country")
        
        if not (email and password and first_name and last_name):
            return JsonResponse({"error": "Missing required fields."}, status=400)
        
        # Check if email is already registered
        if User.objects.filter(username=email).exists():
            return JsonResponse({"error": "Email is already registered."}, status=400)
            
        email_verification_otp = str(secrets.randbelow(90000) + 10000)
        request.session["email_verification_otp"] = email_verification_otp
        request.session["email"] = email
        request.session["password"] = password
        request.session["first_name"] = first_name
        request.session["last_name"] = last_name
        request.session["phone_number"] = phone_number
        request.session["country"] = country
        request.session["email_verification_otp_timestamp"] = timezone.now().isoformat()
        
        subject = "Bfree Email Verification Code"
        email_template_name = "email_templates/email_verification_otp_email_template.html"
        context = {
            "first_name": first_name,
            "last_name": last_name,
            "email_verification_otp": email_verification_otp
        }
        email_content = render_to_string(email_template_name, context)
        try:
            msg = EmailMessage(subject, email_content, settings.EMAIL_HOST_USER, [email])
            msg.content_subtype = "html"
            msg.send()
        except BadHeaderError:
            return JsonResponse({"error": "Invalid header found."}, status=400)
        return JsonResponse({"message": "Email verification OTP sent."})
    return JsonResponse({"error": "Only POST method allowed."}, status=405)


@sensitive_post_parameters()
@csrf_protect
@never_cache
def email_verification_otp(request):
    """
    API endpoint to verify the OTP sent during signup.
    Expects POST with "otp".
    On successful verification, creates the user and returns a token.
    """
    if not request.session.get("email"):
        return JsonResponse({"error": "Session expired, please signup again."}, status=400)
    if request.method == "POST":
        user_entered_otp = request.POST.get("otp")
        saved_otp = request.session.get("email_verification_otp")
        otp_timestamp = request.session.get("email_verification_otp_timestamp")
        if not otp_timestamp:
            return JsonResponse({"error": "OTP timestamp missing."}, status=400)
        otp_timestamp_datetime = dateutil.parser.parse(otp_timestamp)
        
        if saved_otp:
            if (timezone.now() - otp_timestamp_datetime).total_seconds() > 300:
                return JsonResponse({"error": "Expired OTP Code. Please resend OTP."}, status=400)
            if user_entered_otp == saved_otp:
                email = request.session.get("email")
                password = request.session.get("password")
                first_name = request.session.get("first_name")
                last_name = request.session.get("last_name")
                phone_number = request.session.get("phone_number")
                country = request.session.get("country")
                
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                # (Optionally) Log the user in via session if needed:
                # login(request, user)
                token, created = Token.objects.get_or_create(user=user)
                
                user_agent = request.META.get("HTTP_USER_AGENT", "")
                ip_address = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
                parsed_user_agent = parse(user_agent)
                LoginDetail.objects.create(
                    user=user,
                    user_browser=parsed_user_agent.browser.family,
                    user_os=parsed_user_agent.os.family,
                    user_device=parsed_user_agent.device.family,
                    user_ip_address=ip_address
                )
                
                try:
                    profile = Profile.objects.get(user=user)
                except Profile.DoesNotExist:
                    profile = Profile.objects.create(user=user)
                profile.phone_number = phone_number
                profile.country = country
                profile.save()
                
                email_subject = "Welcome to Bfree"
                email_body = render_to_string("email_templates/welcome_email_template.html", {
                    "first_name": first_name,
                    "last_name": last_name
                })
                try:
                    msg = EmailMessage(email_subject, email_body, settings.EMAIL_HOST_USER, [email, settings.EMAIL_HOST_USER])
                    msg.content_subtype = "html"
                    msg.send()
                except BadHeaderError:
                    return JsonResponse({"error": "Invalid header found while sending welcome email."}, status=400)
                
                return JsonResponse({"message": "Signup successful.", "token": token.key})
            return JsonResponse({"error": "Your verification code is incorrect."}, status=400)
        return JsonResponse({"error": "Incorrect or expired OTP. Please try again."}, status=400)
    return JsonResponse({"error": "Only POST method allowed."}, status=405)


def validate_password_and_return_error(password):
    """
    Helper function to validate password strength.
    Returns an error message if validation fails; otherwise, None.
    """
    try:
        from django.core.exceptions import ValidationError
        from django.core.validators import MinLengthValidator, MaxLengthValidator
        MinLengthValidator(8)(password)
        MaxLengthValidator(128)(password)
        validate_password(password)
        validate_password_strength(password)
    except Exception as e:
        error_message = str(e)
        if isinstance(error_message, list) and error_message:
            error_message = error_message[0]
        return error_message
    return None


@login_required
def send_change_password_otp(request):
    """
    API endpoint to send an OTP for password change.
    Expects POST with "new_password" and "confirm_password".
    """
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        if new_password != confirm_password:
            return JsonResponse({"error": "Passwords do not match. Please try again."}, status=400)
        
        error = validate_password_and_return_error(new_password)
        if error:
            return JsonResponse({"error": error}, status=400)
        
        password_change_otp = str(secrets.randbelow(9000) + 1000)
        request.session["new_password"] = new_password
        request.session["password_change_otp"] = password_change_otp
        request.session["password_change_otp_timestamp"] = timezone.now().isoformat()
        
        subject = "Bfree Password Change Verification Code"
        email_template_name = "email_templates/password_change_otp_email.html"
        context = {
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "password_change_otp": password_change_otp,
        }
        email_content = render_to_string(email_template_name, context)
        try:
            msg = EmailMessage(subject, email_content, settings.EMAIL_HOST_USER, [request.user.email])
            msg.content_subtype = "html"
            msg.send()
        except BadHeaderError:
            return JsonResponse({"error": "Invalid header found."}, status=400)
        return JsonResponse({"message": "Email sent."})
    return JsonResponse({"error": "Only POST method allowed."}, status=405)


@login_required
def validate_change_password_otp(request):
    """
    API endpoint to verify OTP for password change.
    Expects POST with "otp".
    """
    if request.method == "POST":
        user_entered_otp = request.POST.get("otp")
        saved_otp = request.session.get("password_change_otp")
        new_password = request.session.get("new_password")
        otp_timestamp = request.session.get("password_change_otp_timestamp")
        if not otp_timestamp:
            return JsonResponse({"error": "OTP timestamp missing."}, status=400)
        otp_timestamp_datetime = dateutil.parser.parse(otp_timestamp)
        
        if saved_otp:
            if (timezone.now() - otp_timestamp_datetime).total_seconds() > 300:
                return JsonResponse({"error": "Expired OTP Code. Please resend."}, status=400)
            if user_entered_otp == saved_otp:
                request.user.set_password(new_password)
                request.user.save()
                del request.session["password_change_otp"]
                logout(request)
                return JsonResponse({"message": "Password Successfully Changed."})
            return JsonResponse({"error": "Your verification code is incorrect."}, status=400)
        return JsonResponse({"error": "Incorrect or expired OTP. Please try again."}, status=400)
    return JsonResponse({"error": "Only POST method allowed."}, status=405)


@login_required
def profile(request):
    """
    API endpoint to view or update a user's profile.
    GET returns profile details; POST updates the profile.
    """
    try:
        profile_obj = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        return JsonResponse({"error": "Profile not found."}, status=404)
    
    if request.method == "POST":
        phone_number = request.POST.get("phone_number")
        address = request.POST.get("address")
        city = request.POST.get("city")
        state = request.POST.get("state")
        country = request.POST.get("country")
        
        if phone_number is not None:
            profile_obj.phone_number = phone_number
        if address is not None:
            profile_obj.address = address
        if city is not None:
            profile_obj.city = city
        if state is not None:
            profile_obj.state = state
        if country is not None:
            profile_obj.country = country
        profile_obj.save()
        return JsonResponse({"message": "Profile updated successfully."})
    
    data = {
        "phone_number": profile_obj.phone_number,
        "address": profile_obj.address,
        "city": profile_obj.city,
        "state": profile_obj.state,
        "country": profile_obj.country,
    }
    return JsonResponse({"profile": data})
