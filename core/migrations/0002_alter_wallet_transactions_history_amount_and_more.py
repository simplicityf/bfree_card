# Generated by Django 4.2.7 on 2024-04-08 17:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wallet_transactions_history',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=50, null=True),
        ),
        migrations.CreateModel(
            name='Crypto_Transactions_History',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.CharField(blank=True, max_length=10000, null=True)),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=50, null=True)),
                ('status', models.CharField(blank=True, max_length=10000, null=True)),
                ('txHash', models.CharField(blank=True, max_length=10000, null=True)),
                ('assetId', models.CharField(blank=True, max_length=10000, null=True)),
                ('networkFee', models.CharField(blank=True, max_length=10000, null=True)),
                ('amountUSD', models.DecimalField(blank=True, decimal_places=2, max_digits=50, null=True)),
                ('blockHash', models.CharField(blank=True, max_length=10000, null=True)),
                ('blockHeight', models.CharField(blank=True, max_length=10000, null=True)),
                ('createdAt', models.CharField(blank=True, max_length=10000, null=True)),
                ('netAmount', models.DecimalField(blank=True, decimal_places=2, max_digits=50, null=True)),
                ('requestedAmount', models.DecimalField(blank=True, decimal_places=2, max_digits=50, null=True)),
                ('operation', models.CharField(blank=True, max_length=10000, null=True)),
                ('subStatus', models.CharField(blank=True, max_length=10000, null=True)),
                ('addressType', models.CharField(blank=True, max_length=10000, null=True)),
                ('feeCurrency', models.CharField(blank=True, max_length=10000, null=True)),
                ('lastUpdated', models.CharField(blank=True, max_length=10000, null=True)),
                ('destinations', models.CharField(blank=True, max_length=10000, null=True)),
                ('exchangeTxId', models.CharField(blank=True, max_length=10000, null=True)),
                ('externalTxId', models.CharField(blank=True, max_length=10000, null=True)),
                ('customerRefId', models.CharField(blank=True, max_length=10000, null=True)),
                ('sourceAddress', models.CharField(blank=True, max_length=10000, null=True)),
                ('destinationTag', models.CharField(blank=True, max_length=10000, null=True)),
                ('signedMessages', models.CharField(blank=True, max_length=10000, null=True)),
                ('destinationAddress', models.CharField(blank=True, max_length=10000, null=True)),
                ('numOfConfirmations', models.CharField(blank=True, max_length=10000, null=True)),
                ('destinationAddressDescription', models.CharField(blank=True, max_length=10000, null=True)),
                ('purpose', models.CharField(blank=True, max_length=10000, null=True)),
                ('tenantId', models.CharField(blank=True, max_length=10000, null=True)),
                ('ownerName', models.CharField(blank=True, max_length=10000, null=True)),
                ('timestamp', models.CharField(blank=True, max_length=10000, null=True)),
                ('custom_timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
