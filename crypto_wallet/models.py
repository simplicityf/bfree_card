from django.db import models
from django.contrib.auth.models import User
from core.models import WalletTransaction
from django.dispatch import receiver
from django.db.models.signals import post_save

from django.http import HttpResponse
from django.core.mail import BadHeaderError, EmailMessage
from django.template.loader import render_to_string 
from django.conf import settings
from django.utils import timezone

class CryptoAddress(models.Model):
    address = models.CharField(max_length=10000, blank=True, null=True)
    coin = models.CharField(max_length=10000, blank=True, null=True)
    network_chain = models.CharField(max_length=10000, blank=True, null=True)

    def __str__(self):
        return f"{self.coin} - {self.network_chain}"
        
    class Meta:
        verbose_name_plural = "Bfree Crypto Addresses"
        
class CryptoFundingRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=10000)
    amount = models.DecimalField(max_digits=50, decimal_places=2, default="0.00",null=True, blank=True)
    fee_percentage = models.DecimalField(max_digits=50, decimal_places=2, default="10.00",null=True, blank=True, help_text="This is the fee in percentage to be charged on the amount. Default is 10%")
    confirmed = models.BooleanField(default=False)
    last_update_timestamp = models.DateTimeField(auto_now=True)
    creation_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}"
        
@receiver(post_save, sender=CryptoFundingRequest)
def update_wallet_balance_upon_confirmation(sender, instance, created, **kwargs):
    if not created and instance.confirmed:
        WalletTransaction.objects.create(
            user=instance.user,
            purpose="Credit",
            fee_percentage=instance.fee_percentage,
            amount=instance.amount,
            credit=True
        )
        fee = instance.amount * instance.fee_percentage / 100
        amount_credited = instance.amount - fee
        subject = "Funding Request Approved"
        email_template_name = "crypto_transaction_email_templates/funding_request_approved.html"
        c = {
            "first_name": instance.user.first_name,
            "last_name": instance.user.last_name,
            'amount_credited': amount_credited,
            'fee': fee,
            'wallet_balance': instance.user.profile.wallet_balance,
            'dateTime': timezone.now(),
        }
        email = render_to_string(email_template_name, c)
        try:
            msg = EmailMessage(subject, email, settings.EMAIL_HOST_USER, [instance.user.email])
            msg.content_subtype = 'html'
            msg.send()
        except BadHeaderError:
            return HttpResponse('Invalid header found.')
            
    elif not created and not instance.confirmed:
        fee = instance.amount * instance.fee_percentage / 100
        debit_amount = instance.amount - fee
        WalletTransaction.objects.create(
            user=instance.user,
            purpose="Debit",
            fee=fee,
            fee_percentage=instance.fee_percentage,
            amount=debit_amount,
            credit=False
        )
    

