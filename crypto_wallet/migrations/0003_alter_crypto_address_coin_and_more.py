# Generated by Django 5.0.2 on 2024-02-28 17:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crypto_wallet", "0002_alter_crypto_address_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="crypto_address",
            name="coin",
            field=models.CharField(max_length=10000),
        ),
        migrations.AlterField(
            model_name="crypto_address",
            name="purpose",
            field=models.CharField(max_length=10000),
        ),
    ]
