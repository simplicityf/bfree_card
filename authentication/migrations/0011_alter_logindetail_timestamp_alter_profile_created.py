# Generated by Django 4.2.7 on 2024-04-25 04:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0010_remove_logindetail_ip_address_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logindetail',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, help_text='Note: Time is in Coordinated Universal Time (UTC+00:00)'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='created',
            field=models.DateTimeField(auto_now_add=True, help_text='Note: Time is in Coordinated Universal Time (UTC+00:00)'),
        ),
    ]
