from django.db import models
from django.utils.timezone import now
from triggers.models import Trigger

class EventLog(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
    ]

    CREATION_SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('api', 'API'),
    ]

    trigger = models.ForeignKey(
        Trigger,
        on_delete=models.SET_NULL,  
        null=True,
        blank=True
    )
    trigger_name = models.CharField(max_length=255, null=True, blank=True)  
    trigger_type = models.CharField(max_length=20, null=True, blank=True)  
    creation_source = models.CharField(  
        max_length=10,
        choices=CREATION_SOURCE_CHOICES,
        default='manual'  
    )
    triggered_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    executed_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"Event {self.id} - {self.status} ({self.creation_source})"