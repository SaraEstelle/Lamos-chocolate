"""
Add the contact/qualification fields to B2BRequest and rename
email -> contact_email.

This reconciles the model with B2BRequestForm, services, selectors, the email
templates and the test-suite, which all already expect these fields.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("b2b", "0001_initial"),
    ]

    operations = [
        # 1) Keep existing data: rename the old column instead of dropping it.
        migrations.RenameField(
            model_name="b2brequest",
            old_name="email",
            new_name="contact_email",
        ),
        # 2) New contact fields (safe defaults => no data migration needed).
        migrations.AddField(
            model_name="b2brequest",
            name="contact_name",
            field=models.CharField(max_length=120, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="b2brequest",
            name="contact_phone",
            field=models.CharField(max_length=40, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="b2brequest",
            name="sector",
            field=models.CharField(max_length=120, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="b2brequest",
            name="estimated_qty",
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="b2brequest",
            name="occasion",
            field=models.CharField(max_length=120, blank=True, default=""),
        ),
        # 3) Server-side fields (anti-abuse + i18n).
        migrations.AddField(
            model_name="b2brequest",
            name="ip_address",
            field=models.GenericIPAddressField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="b2brequest",
            name="language",
            field=models.CharField(max_length=5, blank=True, default="fr"),
        ),
    ]