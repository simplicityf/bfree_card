# Generated by Django 4.2.7 on 2024-04-04 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_alter_profile_wallet_balance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='wallet_balance',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=50),
        ),
    ]
