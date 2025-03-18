from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum


class Account(models.Model):
    total_funding_profit = models.DecimalField(max_digits=5000, decimal_places=2, null=True, blank=True)
    total_card_creation_profit = models.DecimalField(max_digits=5000, decimal_places=2, null=True, blank=True)
    total_card_debit_withdrawals = models.DecimalField(max_digits=5000, decimal_places=2, null=True, blank=True)
    total_card_maintenance_profit = models.DecimalField(max_digits=5000, decimal_places=2, null=True, blank=True)
    total_wallet_balance = models.DecimalField(max_digits=5000, decimal_places=2, null=True, blank=True)

class WalletTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    purpose = models.CharField(max_length=1000, null=True, blank=True)
    fee = models.DecimalField(max_digits=50, decimal_places=2, default="0.00",null=True, blank=True, help_text="This is the fee charged for this transaction.")
    fee_percentage = models.DecimalField(max_digits=50, decimal_places=2, default="10.00",null=True, blank=True, help_text="This is the fee in percentage to be charged on the amount. Default is 10%")
    timestamp = models.DateTimeField(auto_now_add=True, help_text="Note: Time is in Coordinated Universal Time (UTC+00:00)")
    amount = models.DecimalField(max_digits=50, decimal_places=2, null=True, blank=True, help_text="The original amount deposited by the user before deducting any charges.")
    funded_amount = models.DecimalField(max_digits=50, decimal_places=2, null=True, blank=True, help_text="The amount credited to the user's wallet.")
    credit = models.BooleanField(help_text="True for credit, False for debit")

@receiver(post_save, sender=WalletTransaction)
def update_wallet_balance(sender, instance, created, **kwargs):
    if created:
        amount = Decimal(instance.amount)
        fee_percentage = Decimal(instance.fee_percentage)

        deduction = amount * fee_percentage / 100

        if instance.credit:
            new_amount = amount - deduction
            instance.fee = deduction
            instance.amount = amount
            if not instance.purpose:
                instance.purpose = "Credit"
            instance.funded_amount = new_amount
            instance.save()
            instance.user.profile.add_to_wallet_balance(new_amount)
        else:
            if not instance.purpose:
                instance.purpose = "Debit"
            instance.save()
            instance.user.profile.deduct_from_wallet_balance(amount)


@receiver([post_save, post_delete], sender=WalletTransaction)
def update_total_funding_profit(sender, instance, **kwargs):
    funding_credit = WalletTransaction.objects.filter(
        credit=True,
    ).aggregate(Sum('fee'))['fee__sum'] or 0.00
    
    funding_debit = WalletTransaction.objects.filter(
        credit=False,
    ).aggregate(Sum('fee'))['fee__sum'] or 0.00
    
    total_profit = Decimal(funding_credit) - Decimal(funding_debit)

    account, created = Account.objects.get_or_create(pk=1)
    account.total_funding_profit = total_profit
    account.save()
        
        
class CryptoTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=10000, null=True, blank=True)
    amount = models.DecimalField(max_digits=50, decimal_places=2, null=True, blank=True)
    invoice_url = models.URLField(max_length=10000, null=True, blank=True)
    processed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'transaction_id')

    def __str__(self):
        return f"Crypto Address Owner: {self.user.first_name} {self.user.last_name} - {self.user.email}"
        
class CriticalBroadcast(models.Model):
    active = models.BooleanField(default=False)
    message = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

        
