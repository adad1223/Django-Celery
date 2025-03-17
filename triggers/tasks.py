from celery import shared_task
from django.utils import timezone
from django.utils.timezone import now
from .models import Trigger
from event_logs.models import EventLog
from datetime import timedelta
from django_celery_beat.models import PeriodicTask
@shared_task
def process_scheduled_triggers():
    """Finds and executes due scheduled triggers."""
    triggers = Trigger.objects.filter(trigger_type='scheduled', schedule_time__lte=now())

    for trigger in triggers:
        EventLog.objects.create(trigger=trigger, payload={}, status='active')
        print(f"Executed scheduled trigger: {trigger.name}")

@shared_task
def archive_old_events():
    """Moves events from active to archived after 2 hours."""
    threshold = now() - timedelta(hours=2)
    EventLog.objects.filter(status='active', triggered_at__lte=threshold).update(status='archived')

@shared_task
def delete_old_events():
    """Deletes archived events after 48 hours."""
    threshold = now() - timedelta(hours=48)
    EventLog.objects.filter(status='archived', triggered_at__lte=threshold).delete()


@shared_task
def execute_trigger(trigger_id=None):
    """Processes a trigger and sends a WebSocket message if it's a test event."""
    execution_time = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')

    if trigger_id is None:
        print(f"Test Trigger Executed at {execution_time}")
        return {"test_trigger": True, "executed_at": execution_time}

    try:
        trigger = Trigger.objects.get(id=trigger_id)
        print(f" Executing Trigger ID: {trigger.id}, Name: {trigger.name}")


        EventLog.objects.create(
            trigger=trigger,
            trigger_name=trigger.name,
            trigger_type=trigger.schedule_type,
            creation_source=trigger.creation_source,
            executed_at=timezone.now(),
            payload=trigger.payload,
            status='active'
        )

        print(f"Event Logged for Trigger {trigger.id}")

        if trigger.schedule_type == "one-time":
            trigger.delete()
            print(f" Deleted One-Time Trigger: {trigger.id}")

        return f"Trigger {trigger.id} ({trigger.name}) executed successfully"

    except Trigger.DoesNotExist:
        print(f" Warning: Trigger {trigger_id} not found.")
        return "Trigger not found"
@shared_task
def delete_one_time_trigger(trigger_id):
    """Deletes an executed one-time trigger after 48 hours."""
    try:
        trigger = Trigger.objects.get(id=trigger_id, schedule_type="one-time")
        print(f" Deleting one-time trigger: {trigger.id} ({trigger.name}) after 48 hours")
        trigger.delete()
    except Trigger.DoesNotExist:
        print(f" One-time trigger {trigger_id} already deleted.")
# def manage_even_retention():
#     """Archives events after 2 hours, deletes archived events after 48 hours."""
#     now_time = now()
    
#     # Move "active" events older than 2 hours to "archived"
#     archive_threshold = now_time - timedelta(hours=2)
#     EventLog.objects.filter(status="active", executed_at__lte=archive_threshold).update(status="archived")

#     # Delete "archived" events older than 48 hours
#     delete_threshold = now_time - timedelta(hours=48)
#     EventLog.objects.filter(status="archived", executed_at__lte=delete_threshold).delete()

#     return " Event retention task completed!"
# @shared_task
# def execute_trigger(trigger_id):
#     """Processes a trigger and logs the event."""
#     try:
#         trigger = Trigger.objects.get(id=trigger_id)

#         # ✅ Log Execution in EventLog
#         EventLog.objects.create(trigger=trigger, executed_at=now(), status='completed')

#         print(f"✅ Executed Trigger: {trigger.id} - {trigger.name}")

#         # ✅ If it's a one-time event, schedule deletion after 48 hours
#         if trigger.schedule_type == "one-time":
#             trigger.delete()
#             print(f"🗑 Deleted One-Time Trigger: {trigger.id}")

#         return f"Trigger {trigger.id} executed successfully"

#     except Trigger.DoesNotExist:
#         print(f"⚠️ Warning: Trigger {trigger_id} not found")
#         return "Trigger not found"