# Generated by Django 4.2.7 on 2024-04-29 10:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_account_total_card_debit_withdrawals'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='total_failed_card_payment_profit',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5000, null=True),
        ),
    ]
