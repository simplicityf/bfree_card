# Generated by Django 4.2.7 on 2024-04-09 11:27

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0002_alter_wallet_transactions_history_amount_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Crypto_Transactions_History',
            new_name='CryptoTransactionHistorie',
        ),
        migrations.RenameModel(
            old_name='Wallet_Transactions_History',
            new_name='WalletTransactionHistorie',
        ),
    ]
