# Generated by Django 5.1.7 on 2025-03-13 14:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("triggers", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="trigger",
            name="api_payload",
        ),
        migrations.RemoveField(
            model_name="trigger",
            name="interval",
        ),
        migrations.RemoveField(
            model_name="trigger",
            name="trigger_type",
        ),
        migrations.AddField(
            model_name="trigger",
            name="frequency",
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name="trigger",
            name="schedule_type",
            field=models.CharField(
                choices=[("one-time", "One-Time"), ("recurring", "Recurring")],
                default="one-time",
                max_length=10,
            ),
        ),
    ]
