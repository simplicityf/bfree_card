# Generated by Django 4.2.7 on 2024-04-11 20:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0009_alter_profile_created'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='logindetail',
            name='ip_address',
        ),
        migrations.AddField(
            model_name='logindetail',
            name='user_browser',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='logindetail',
            name='user_device',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='logindetail',
            name='user_ip_address',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='logindetail',
            name='user_os',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
