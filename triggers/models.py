from django.db import models
from django_celery_beat.models import PeriodicTask
from django.db.models.signals import post_delete
from django.dispatch import receiver

class Trigger(models.Model):
    SCHEDULE_TYPE_CHOICES = [
        ('one-time', 'One-Time'),
        ('recurring', 'Recurring'),
    ]
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ]
    
    CREATION_SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('api', 'API'),
    ]

    name = models.CharField(max_length=255)
    schedule_type = models.CharField(
        max_length=10,
        choices=SCHEDULE_TYPE_CHOICES,
        default='one-time'
    )
    
    schedule_time = models.DateTimeField(null=True, blank=True)  # Only for one-time events
    
    frequency = models.CharField(
        max_length=50,
        choices=FREQUENCY_CHOICES,
        null=True,
        blank=True
    )
    
    custom_frequency_expression = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Cron expression for custom frequency, e.g., '*/5 * * * *'"
    )

    creation_source = models.CharField(
        max_length=50,
        choices=CREATION_SOURCE_CHOICES,
        default='manual'
    )
    payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.schedule_type})"

@receiver(post_delete, sender=Trigger)
def delete_periodic_task(sender, instance, **kwargs):
    """Deletes the corresponding PeriodicTask when a Trigger is deleted."""
    task_name = f"Trigger-{instance.id}-{instance.name}"
    periodic_task = PeriodicTask.objects.filter(name=task_name).first()

    if periodic_task:
        periodic_task.delete()
        print(f"✅ Deleted PeriodicTask: {task_name}")
    else:
        print(f"⚠️ No periodic task found for {task_name}")