# Generated by Django 4.2.7 on 2024-04-03 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_profile_card_user_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='wallet_balance',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=20),
        ),
    ]
