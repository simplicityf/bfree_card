# Generated by Django 5.0.2 on 2024-04-01 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("card", "0004_rename_full_name_card_card_full_name_card_card_color_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Card_Profit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("failed_card_payment_fee", models.CharField(max_length=10000)),
                ("card_maintenance_fee", models.CharField(max_length=10000)),
            ],
        ),
        migrations.AddField(
            model_name="card",
            name="activated",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="card",
            name="amount_limit",
            field=models.CharField(blank=True, max_length=100000, null=True),
        ),
        migrations.AlterField(
            model_name="card",
            name="balance",
            field=models.CharField(max_length=100000),
        ),
    ]
