# Generated by Django 5.1.3 on 2024-12-20 03:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_cryptotransaction_processed'),
    ]

    operations = [
        migrations.RenameField(
            model_name='account',
            old_name='total_card_profit',
            new_name='total_card_creation_profit',
        ),
        migrations.RenameField(
            model_name='account',
            old_name='total_failed_card_payment_profit',
            new_name='total_card_maintenance_profit',
        ),
    ]
