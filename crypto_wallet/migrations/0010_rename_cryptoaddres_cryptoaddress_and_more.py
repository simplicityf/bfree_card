# Generated by Django 4.2.7 on 2024-10-14 17:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crypto_wallet', '0009_alter_cryptofundingrequest_amount'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CryptoAddres',
            new_name='CryptoAddress',
        ),
        migrations.AlterModelOptions(
            name='cryptoaddress',
            options={'verbose_name_plural': 'Bfree Crypto Addresses'},
        ),
    ]
