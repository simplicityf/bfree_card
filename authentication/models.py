from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
import secrets
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from core.models import *

phone_regex = RegexValidator(
    regex=r'^\+?\d{8,15}$',
    message="Enter a valid phone number, including an optional plus sign (+), and between 8 and 15 digits."
)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wallet_id = models.CharField(max_length=12, default=None)
    wallet_balance = models.DecimalField(max_digits=50, decimal_places=2, default=0.00)
    phone_number = models.CharField(validators=[phone_regex], max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(max_length=255, blank=True, null=True)
    address = models.TextField(max_length=1000, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, help_text="Note: Time is in Coordinated Universal Time (UTC+00:00)")
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.wallet_id = self.generate_wallet_id()
        
        if self.wallet_balance <= Decimal('-4.00'):
            self.user.is_active = False
            self.user.save()

        super().save(*args, **kwargs)

    def generate_wallet_id(self):
        while True:
            new_wallet_id = secrets.token_hex(6)
            if not Profile.objects.filter(wallet_id=new_wallet_id).exists():
                return new_wallet_id
                
    def add_to_wallet_balance(self, amount):
        if amount <= Decimal('0.00'):
            
            raise ValidationError({'wallet_balance':"Amount must be a positive number."})
        self.wallet_balance += Decimal(amount)
        self.save()
    
    def deduct_from_wallet_balance(self, amount, allow_negative=False):
        if amount <= Decimal('0.00'):
            raise ValidationError({'wallet_balance': "Amount must be a positive number."})
        
        if not allow_negative and amount > self.wallet_balance:
            raise ValidationError({'wallet_balance': "Insufficient balance."})
        
        self.wallet_balance -= Decimal(amount)
        self.save()


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
    
@receiver([post_save, post_delete], sender=Profile)
def update_account_wallet_balance(sender, instance, **kwargs):
    total_wallet_balance = Profile.objects.aggregate(total_balance=models.Sum('wallet_balance'))['total_balance'] or 0
    account, created = Account.objects.get_or_create(pk=1)
    account.total_wallet_balance = total_wallet_balance
    account.save()


class LoginDetail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_ip_address = models.CharField(max_length=50, blank=True, null=True)
    user_browser = models.CharField(max_length=50, blank=True, null=True)
    user_os = models.CharField(max_length=50, blank=True, null=True)
    user_device = models.CharField(max_length=50, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, help_text="Note: Time is in Coordinated Universal Time (UTC+00:00)")

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.user.email}"
        
class AlphaspaceAuthToken(models.Model):
    token_type = models.CharField(max_length=100, blank=True, null=True)
    refresh_token = models.CharField(max_length=1000, blank=True, null=True)
    access_token = models.CharField(max_length=1000, blank=True, null=True)
    expires_in = models.CharField(max_length=100, blank=True, null=True, help_text="Expiry is in seconds.")
    timestamp = models.DateTimeField(auto_now_add=True, help_text="Note: Time is in Coordinated Universal Time (UTC+00:00)")

    def __str__(self):
        return f"Alphaspace Auth Tokens"



post_save.connect(create_user_profile, sender=User)
post_save.connect(save_user_profile, sender=User)