from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

# Create your models here.
class Card(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card_id = models.CharField(max_length=10000, blank=True, null=True)
    nickname = models.CharField(max_length=10000, blank=True, null=True)
    type = models.CharField(max_length=10000, blank=True, null=True)
    purpose = models.CharField(max_length=10000, blank=True, null=True)
    card_token = models.CharField(max_length=10000, blank=True, null=True)
    card_number = models.CharField(max_length=10000, blank=True, null=True)
    card_masked_number = models.CharField(max_length=10000, blank=True, null=True)
    card_cvv = models.CharField(max_length=3, blank=True, null=True)
    state = models.CharField(max_length=10000, blank=True, null=True)
    card_color = models.CharField(max_length=10000, blank=True, null=True)
    balance = models.DecimalField(max_digits=50, decimal_places=2, blank=True, null=True)
    brand = models.CharField(max_length=10000, blank=True, null=True)
    card_expiration_date = models.CharField(max_length=10, blank=True, null=True)
    billing_address_line_1 = models.CharField(max_length=10000, blank=True, null=True)
    billing_address_line_2 = models.CharField(max_length=10000, blank=True, null=True)
    billing_address_city = models.CharField(max_length=10000, blank=True, null=True)
    billing_address_state = models.CharField(max_length=10000, blank=True, null=True)
    billing_address_zip_code = models.CharField(max_length=10000, blank=True, null=True)
    billing_address_country = models.CharField(max_length=10000, blank=True, null=True)
    card_creation_response = models.JSONField(blank=True, null=True,)
    last_card_activity_response = models.JSONField(blank=True, null=True,)
    creation_date = models.DateTimeField(auto_now_add=True, help_text="Note: Time is in Coordinated Universal Time (UTC+00:00)")
    last_updated_date = models.DateTimeField(auto_now=True, help_text="Note: Time is in Coordinated Universal Time (UTC+00:00)")
    
    def __str__(self):
        return f"Card: {self.user.first_name} {self.user.last_name}"
        
    def add_to_card_balance(self, amount):
        if amount <= Decimal('0.00'):
            raise ValueError("Amount must be a positive number.")
        self.balance += Decimal(amount)
        self.save()
    
    def deduct_from_card_balance(self, amount):
        if amount <= Decimal('0.00'):
            raise ValueError("Amount must be a positive number.")
        if amount > self.balance:
            raise ValueError("Insufficient balance.")
        self.balance -= Decimal(amount)
        self.save()
        

class CardProfitDeclaration(models.Model):
    failed_card_payment_fee = models.DecimalField(max_digits=50, decimal_places=2, default=0.00)
    card_maintenance_fee = models.DecimalField(max_digits=50, decimal_places=2, default=0.00)
    


    

