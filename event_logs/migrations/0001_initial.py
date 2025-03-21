# Generated by Django 5.1.7 on 2025-03-12 13:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("triggers", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EventLog",
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
                ("triggered_at", models.DateTimeField(auto_now_add=True)),
                ("payload", models.JSONField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("archived", "Archived"),
                            ("deleted", "Deleted"),
                        ],
                        default="active",
                        max_length=10,
                    ),
                ),
                (
                    "trigger",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="triggers.trigger",
                    ),
                ),
            ],
        ),
    ]
