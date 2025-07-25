# Generated by Django 4.2.11 on 2025-07-15 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("system", "0002_alter_privatemsg_options_privatemsg_created_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="daily_rate",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="order",
            name="email_sent",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="order",
            name="email_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="order_number",
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="order",
            name="rental_days",
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("confirmed", "Confirmed"),
                    ("cancelled", "Cancelled"),
                    ("completed", "Completed"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="subtotal",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="order",
            name="tax_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="order",
            name="tax_rate",
            field=models.DecimalField(decimal_places=2, default=10.0, max_digits=5),
        ),
        migrations.AddField(
            model_name="order",
            name="total_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="order",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
