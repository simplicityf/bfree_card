# Generated by Django 4.2.7 on 2024-04-09 15:14

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0003_rename_crypto_transactions_history_cryptotransactionhistorie_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CryptoTransactionHistorie',
            new_name='CryptoTransaction',
        ),
        migrations.RenameModel(
            old_name='WalletTransactionHistorie',
            new_name='WalletTransaction',
        ),
    ]
