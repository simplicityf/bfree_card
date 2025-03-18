from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from authentication.models import Profile
from django.contrib.auth.password_validation import validate_password
from django.core.validators import (
    EmailValidator
)
import re
from django.utils.translation import gettext as _
from django.contrib.auth.forms import SetPasswordForm

def UniqueEmail(value):
    if User.objects.filter(email__iexact=value).exists():
        raise ValidationError(f"User with this email already exists.")
    
def UniquePhoneNumber(value):
    if Profile.objects.filter(phone_number__iexact=value).exists():
        raise ValidationError(f"User with this phone number already exists.")
        
def name_validator(value):
    if any(char.isdigit() for char in value):
        raise ValidationError(_("Numbers are't allowed in names."), code='name_no_numeric')
    
def validate_password_strength(value):
    if not any(char.isupper() for char in value):
        raise ValidationError(_("The password must contain at least one uppercase letter."), code='password_no_uppercase')
    if not any(char.islower() for char in value):
        raise ValidationError(_("The password must contain at least one lowercase letter."), code='password_no_lowercase')
    if not any(char.isdigit() for char in value):
        raise ValidationError(_("The password must contain at least one numeric digit (0–9)."), code='password_no_numeric')
    if not re.search(r'[^\w\s]', value):
        raise ValidationError(_("The password must contain at least one special character."), code='password_no_special')
        
class CustomConfirmResetPasswordForm(SetPasswordForm):
    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        if not any(char.isupper() for char in password1):
            raise ValidationError(_("The password must contain at least one uppercase letter."), code='password_no_uppercase')
        if not any(char.islower() for char in password1):
            raise ValidationError(_("The password must contain at least one lowercase letter."), code='password_no_lowercase')
        if not any(char.isdigit() for char in password1):
            raise ValidationError(_("The password must contain at least one numeric digit (0–9)."), code='password_no_numeric')
        if not re.search(r'[^\w\s]', password1):
            raise ValidationError(_("The password must contain at least one special character."), code='password_no_special')

        return password1

class SignupForm(forms.ModelForm):
    first_name = forms.CharField(
        widget=forms.TextInput(),
        required=True,
        min_length=2,
        max_length=10000,
        validators=[
            name_validator,
        ],
    )
    last_name = forms.CharField(
        widget=forms.TextInput(),
        required=True,
        min_length=2,
        max_length=1000,
        validators=[
            name_validator,
        ],
    )
    email = forms.EmailField(
        max_length=1000,
        required=True,
        validators=[
            UniqueEmail,
        ],
    )
    password = forms.CharField(
        widget=forms.PasswordInput(),
        validators=[
            validate_password,
            validate_password_strength,
        ],
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(), required=True, label="Confirm your password."
    )
    phone_number = forms.CharField(
        widget=forms.TextInput(),
        required=True,
        max_length=15,
        validators=[
            UniquePhoneNumber,
        ],
    )
    country = forms.CharField(
        widget=forms.TextInput(),
        required=True,
        max_length=1000,
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "password")

    def clean_confirm_password(self):
        password = self.cleaned_data.get("password")
        confirm_password = self.cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match. Try again.")

        return confirm_password


class ProfileForm(forms.ModelForm):
    phone_number = forms.CharField(
        widget=forms.TextInput(),
        required=False,
        max_length=15,
    )
    address = forms.CharField(
        widget=forms.TextInput(),
        required=False,
        max_length=1000,
    )
    city = forms.CharField(
        widget=forms.TextInput(),
        required=False,
        max_length=100,
    )
    state = forms.CharField(
        widget=forms.TextInput(),
        required=False,
        max_length=100,
    )
    country = forms.CharField(
        widget=forms.TextInput(),
        required=False,
        max_length=100,
    )

    class Meta:
        model = Profile
        fields = (
            "phone_number",
            "address",
            "city",
            "state",
            "country",
        )
