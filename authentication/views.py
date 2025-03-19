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
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny


# Function to handle json request from postman
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
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

@csrf_exempt
def password_reset(request):
    """
    API endpoint to request a password reset OTP.
    Expects a POST request with an "email" parameter.
    If the email exists, an OTP is generated, stored in the session,
    and sent to the user via email.
    """
    if request.method == "POST":
        data = get_request_data(request)
        email = data.get("email")
        if not email:
            return JsonResponse({"error": "Email is required."}, status=400)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # For security, do not reveal whether the email exists.
            return JsonResponse({"message": "User or Email does not exist, please check and try again."})
        
        # Generate a 6-digit OTP
        otp = str(secrets.randbelow(900000) + 100000)
        
        # Store the OTP and email in the session along with a timestamp (expires in 10 minutes)
        request.session["password_reset_otp"] = otp
        request.session["password_reset_email"] = email
        request.session["password_reset_otp_timestamp"] = timezone.now().isoformat()
        
        subject = "Bfree Password Reset OTP"
        email_content = (
            f"Hello {user.first_name} {user.last_name},\n\n"
            f"Your password reset OTP is: {otp}\n\n"
            f"This OTP will expire in 10 minutes.\n\n"
            f"If you did not request a password reset, please ignore this email.\n\n"
            f"Thank you,\n"
            f"The Bfree Team"
        )
        try:
            msg = EmailMessage(subject, email_content, settings.EMAIL_HOST_USER, [email])
            msg.send()
        except BadHeaderError:
            return JsonResponse({"error": "Invalid header found."}, status=400)
        
        return JsonResponse({"message": "Password reset OTP has been sent to your mail, please check your mail."})
    return JsonResponse({"error": "Only POST method allowed."}, status=405)

@csrf_exempt
def verify_password_reset_otp(request):
    """
    API endpoint to verify the OTP for password reset and update the password.
    Expects a POST request with "otp", "new_password", and "confirm_password".
    """
    if request.method == "POST":
        data = get_request_data(request)
        otp_entered = data.get("otp")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")
        
        if not otp_entered or not new_password or not confirm_password:
            return JsonResponse({"error": "OTP, new password, and confirm password are required."}, status=400)
        
        if new_password != confirm_password:
            return JsonResponse({"error": "Passwords do not match."}, status=400)
        
        saved_otp = request.session.get("password_reset_otp")
        saved_email = request.session.get("password_reset_email")
        otp_timestamp = request.session.get("password_reset_otp_timestamp")
        
        if not saved_otp or not saved_email or not otp_timestamp:
            return JsonResponse({"error": "OTP session expired. Please request a new OTP."}, status=400)
        
        otp_timestamp_datetime = dateutil.parser.parse(otp_timestamp)
        # Check if more than 10 minutes (600 seconds) have passed
        if (timezone.now() - otp_timestamp_datetime).total_seconds() > 600:
            return JsonResponse({"error": "OTP expired. Please request a new OTP."}, status=400)
        
        if otp_entered != saved_otp:
            return JsonResponse({"error": "Invalid OTP."}, status=400)
        
        try:
            user = User.objects.get(email=saved_email)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=400)
        
        # Set the new password
        user.set_password(new_password)
        user.save()
        
        # Clear OTP-related session variables
        del request.session["password_reset_otp"]
        del request.session["password_reset_email"]
        del request.session["password_reset_otp_timestamp"]
        
        return JsonResponse({"message": "Password reset successfully."})
    return JsonResponse({"error": "Only POST method allowed."}, status=405)

@sensitive_post_parameters()
@csrf_exempt
@never_cache
def Signin(request):
    """
    API endpoint for initial login.
    Expects POST with "email" and "password".
    On success, generates an OTP and sends it to the user.
    """
    if request.method == "POST":
        data = get_request_data(request)
        email = data.get("email")
        password = data.get("password")
        if not (email and password):
            return JsonResponse({"error": "Email and password are required."}, status=400)
        
        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            return JsonResponse({"error": "Wrong login details. Please try again."}, status=400)
        
        if not user.check_password(password):
            return JsonResponse({"error": "Wrong login details. Please try again."}, status=400)
        
        # Generate the OTP and store it in session
        login_otp = str(secrets.randbelow(90000) + 10000)
        request.session["login_otp"] = login_otp
        request.session["user_id"] = user.id
        request.session["user_email"] = user.email
        request.session["user_password"] = password
        request.session["login_otp_timestamp"] = timezone.now().isoformat()
        
        subject = "Bfree Login Verification Code"
        # Build a plain text email message directly
        email_content = (
            f"Hello {user.first_name} {user.last_name},\n\n"
            f"Your login verification code is: {login_otp}\n\n"
            "Please use this code to complete your login.\n\n"
            "Thank you,\n"
            "The Bfree Team"
        )
        
        try:
            msg = EmailMessage(subject, email_content, settings.EMAIL_HOST_USER, [user.email])
            msg.send()
        except BadHeaderError:
            return JsonResponse({"error": "Invalid header found."}, status=400)
        
        return JsonResponse({"message": "OTP sent. Please verify."})
    return JsonResponse({"error": "Only POST method allowed."}, status=405)

@sensitive_post_parameters()
@csrf_exempt
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
        data = get_request_data(request)
        user_entered_otp = data.get("otp")
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
                del request.session["login_otp"]
                token, created = Token.objects.get_or_create(user=user)
                return JsonResponse({"message": "Login successful.", "token": token.key})
            return JsonResponse({"error": "Your verification code is incorrect."}, status=400)
        return JsonResponse({"error": "Incorrect or expired OTP. Please try again."}, status=400)
    return JsonResponse({"error": "Only POST method allowed."}, status=405)

@sensitive_post_parameters()
@csrf_exempt
@never_cache
def Signup(request):
    """
    API endpoint for user signup.
    Expects POST with "email", "password", "first_name", "last_name",
    "phone_number", and "country".
    Generates an OTP for email verification.
    """
    if request.method == "POST":
        data = get_request_data(request)
        email = data.get("email")
        password = data.get("password")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        phone_number = data.get("phone_number")
        country = data.get("country")
        
        if not (email and password and first_name and last_name):
            return JsonResponse({"error": "Missing required fields."}, status=400)
        
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
        email_content = f"Hello {first_name},\n\nYour email verification code is: {request.session.get('email_verification_otp')}\n\nThanks,\nThe Team"
        try:
            msg = EmailMessage(subject, email_content, settings.EMAIL_HOST_USER, [email])
            msg.content_subtype = "html"
            msg.send()
        except BadHeaderError:
            return JsonResponse({"error": "Invalid header found."}, status=400)
        return JsonResponse({"message": "Email verification OTP sent."})
    return JsonResponse({"error": "Only POST method allowed."}, status=405)

@sensitive_post_parameters()
@csrf_exempt
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
        data = get_request_data(request)
        user_entered_otp = data.get("otp")
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
                email_body = f"Welcome {first_name} {last_name},\n\nThank you for signing up for Bfree!"
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_change_password_otp(request):
    """
    API endpoint to send an OTP for password change.
    Expects POST with "new_password" and "confirm_password".
    """
    if request.method == "POST":
        data = get_request_data(request)
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")
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
        email_content = (
                f"Hello {request.user.first_name} {request.user.last_name},<br><br>"
                f"Your change password OTP is: {password_change_otp}<br><br>"
                "Please use this OTP to change your password."
            )
        try:
            msg = EmailMessage(subject, email_content, settings.EMAIL_HOST_USER, [request.user.email])
            msg.content_subtype = "html"
            msg.send()
        except BadHeaderError:
            return JsonResponse({"error": "Invalid header found."}, status=400)
        return JsonResponse({"message": "Email sent."})
    return JsonResponse({"error": "Only POST method allowed."}, status=405)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_change_password_otp(request):
    """
    API endpoint to verify OTP for password change.
    Expects POST with "otp".
    """
    if request.method == "POST":
        data = get_request_data(request)
        user_entered_otp = data.get("otp")
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

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    API endpoint to view or update a user's profile.
    GET returns profile details; POST updates the profile.
    If the email is updated, an OTP is sent to the new email,
    the new email and OTP are stored in session, and the user is logged out.
    """
    try:
        profile_obj = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        return JsonResponse({"error": "Profile not found."}, status=404)
    
    if request.method == "POST":
        data = get_request_data(request)
        
        # Update fields in the Profile model
        phone_number = data.get("phone_number")
        address = data.get("address")
        city = data.get("city")
        state = data.get("state")
        country = data.get("country")
        
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
        
        # Handle file upload for profile picture (if provided)
        if "profile_picture" in request.FILES:
            profile_obj.profile_picture = request.FILES["profile_picture"]
        
        profile_obj.save()
        
        # Update User model fields (email, first_name, last_name)
        new_email = data.get("email")
        new_first_name = data.get("first_name")
        new_last_name = data.get("last_name")
        email_changed = False
        
        if new_email and new_email != request.user.email:
            # If the email is changing, generate an OTP and send it to the new email.
            otp = str(secrets.randbelow(900000) + 100000)  # 6-digit OTP
            # Store new email, OTP, timestamp, and user id in session
            request.session["new_email"] = new_email
            request.session["new_email_otp"] = otp
            request.session["new_email_otp_timestamp"] = timezone.now().isoformat()
            request.session["user_id_for_email_change"] = request.user.id
            # Compose and send OTP email
            subject = "Verify Your New Email for Bfree"
            email_content = (
                f"Hello {request.user.first_name} {request.user.last_name},\n\n"
                f"We received a request to change your email to {new_email}.\n"
                f"Your verification OTP is: {otp}\n\n"
                f"This OTP will expire in 10 minutes.\n"
                f"Please verify your new email to complete the update.\n\n"
                f"If you did not request this change, please contact support.\n\n"
                f"Thank you,\nThe Bfree Team"
            )
            try:
                from django.core.mail import EmailMessage, BadHeaderError
                msg = EmailMessage(subject, email_content, settings.EMAIL_HOST_USER, [new_email])
                msg.send()
            except BadHeaderError:
                return JsonResponse({"error": "Invalid header found while sending OTP."}, status=400)
            email_changed = True
        
        if new_first_name:
            request.user.first_name = new_first_name
        if new_last_name:
            request.user.last_name = new_last_name
        request.user.save()
        
        if email_changed:
            # Log the user out so they must verify the new email before continuing.
            logout(request)
            return JsonResponse({
                "message": "Profile updated. An OTP has been sent to your new email. Please verify your new email and log in again."
            })
        else:
            return JsonResponse({"message": "Profile updated successfully."})
    
    # For GET: return a complete profile (combining User and Profile fields)
    data = {
        "email": request.user.email,
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "profile_picture": profile_obj.profile_picture.url if profile_obj.profile_picture else None,
        "phone_number": profile_obj.phone_number,
        "address": profile_obj.address,
        "city": profile_obj.city,
        "state": profile_obj.state,
        "country": profile_obj.country,
        "wallet_id": profile_obj.wallet_id,
        "wallet_balance": profile_obj.wallet_balance
    }
    return JsonResponse({"profile": data})

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email_change(request):
    """
    API endpoint to verify the OTP for a new email.
    Expects a POST request with "otp".
    On successful verification, updates the user's email.
    """
    data = get_request_data(request)
    otp_entered = data.get("otp")
    
    saved_otp = request.session.get("new_email_otp")
    new_email = request.session.get("new_email")
    otp_timestamp = request.session.get("new_email_otp_timestamp")
    user_id = request.session.get("user_id_for_email_change")
    
    if not (otp_entered and saved_otp and new_email and otp_timestamp and user_id):
        return JsonResponse({"error": "Missing OTP verification data. Please request a new OTP."}, status=400)
    
    otp_timestamp_datetime = dateutil.parser.parse(otp_timestamp)
    # Check if more than 10 minutes (600 seconds) have passed
    if (timezone.now() - otp_timestamp_datetime).total_seconds() > 600:
        return JsonResponse({"error": "OTP expired. Please request a new OTP."}, status=400)
    
    if otp_entered != saved_otp:
        return JsonResponse({"error": "Invalid OTP."}, status=400)
    
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found."}, status=400)
    
    # Update the user's email
    user.email = new_email
    user.save()
    
    # Clear OTP-related session keys
    for key in ["new_email", "new_email_otp", "new_email_otp_timestamp", "user_id_for_email_change"]:
        if key in request.session:
            del request.session[key]
    
    return JsonResponse({"message": "Email updated successfully. Please log in with your new email."})

