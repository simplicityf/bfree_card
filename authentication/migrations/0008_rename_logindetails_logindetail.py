# Generated by Django 4.2.7 on 2024-04-09 10:57

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('authentication', '0007_rename_loginattempt_logindetails'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='LoginDetails',
            new_name='LoginDetail',
        ),
    ]
