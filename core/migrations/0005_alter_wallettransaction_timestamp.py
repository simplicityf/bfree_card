# Generated by Django 4.2.7 on 2024-04-25 04:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_rename_cryptotransactionhistorie_cryptotransaction_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wallettransaction',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, help_text='Note: Time is in Coordinated Universal Time (UTC+00:00)'),
        ),
    ]
