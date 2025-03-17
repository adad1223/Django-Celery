from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Trigger
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django.utils import timezone 
from django.utils.timezone import make_aware
from .tasks import execute_trigger 
from event_logs.models import EventLog
import datetime
from rest_framework.decorators import api_view
import json
def trigger_list(request):
    """Render the scheduled events list."""
    triggers = Trigger.objects.all()
    return render(request, "triggers/trigger_list.html", {"triggers": triggers})
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Trigger
from django.utils.timezone import make_aware
from django_celery_beat.models import CrontabSchedule, PeriodicTask
import datetime
from .tasks import execute_trigger
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from django.utils.timezone import now
import datetime

def parse_relative_time(relative_time):
    """Parses time like '10m', '2h', '1d' into a future timestamp."""
    unit = relative_time[-1]  # Get the last character (m, h, d)
    value = int(relative_time[:-1])  # Get the number part

    if unit == "m":
        return now() + datetime.timedelta(minutes=value)
    elif unit == "h":
        return now() + datetime.timedelta(hours=value)
    elif unit == "d":
        return now() + datetime.timedelta(days=value)
    else:
        raise ValueError("Invalid relative time format. Use 'm', 'h', or 'd'.")
@csrf_exempt
def create_trigger(request):
    """Creates a new trigger and schedules execution."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name")
            schedule_type = data.get("schedule_type")
            schedule_time_str = data.get("schedule_time")
            frequency = data.get("frequency")

            schedule_time = None
            if schedule_type == "one-time":
                if schedule_time_str[-1] in ["m", "h", "d"]:  # Check if it's relative time
                    schedule_time = parse_relative_time(schedule_time_str)
                else:
                    schedule_time = make_aware(datetime.datetime.strptime(schedule_time_str, "%Y-%m-%dT%H:%M"))
                    #add check to verify if the schedule time is in the future
                    if schedule_time < now():
                        return JsonResponse({"error": "Schedule time must be in the future"}, status=400)
                        
            trigger = Trigger.objects.create(
                name=name,
                schedule_type=schedule_type,
                schedule_time=schedule_time if schedule_type == "one-time" else None,
                frequency=frequency,

            )

            print(f"Trigger saved with ID: {trigger.id}")

            # ✅ Handle recurring scheduling
            if schedule_type == "recurring":
                schedule = None

                if frequency.endswith("m"):  
                    every = int(frequency[:-1])
                    schedule, _ = IntervalSchedule.objects.get_or_create(every=every, period=IntervalSchedule.MINUTES)
                elif frequency.endswith("h"):  
                    every = int(frequency[:-1])
                    schedule, _ = IntervalSchedule.objects.get_or_create(every=every, period=IntervalSchedule.HOURS)
                elif frequency.endswith("d"):  
                    every = int(frequency[:-1])
                    schedule, _ = IntervalSchedule.objects.get_or_create(every=every, period=IntervalSchedule.DAYS)
                elif frequency.endswith("w"):  
                    every = int(frequency[:-1])
                    schedule, _ = IntervalSchedule.objects.get_or_create(every=every, period=IntervalSchedule.WEEKS)
                else:
                    cron_parts = frequency.split(" ")
                    if len(cron_parts) != 5:
                        return JsonResponse({"error": "Invalid cron expression. Must be like: '*/5 * * * *'"}, status=400)

                    schedule, _ = CrontabSchedule.objects.get_or_create(
                        minute=cron_parts[0],
                        hour=cron_parts[1],
                        day_of_month=cron_parts[2],
                        month_of_year=cron_parts[3],
                        day_of_week=cron_parts[4]
                    )

                PeriodicTask.objects.create(
                    interval=schedule if isinstance(schedule, IntervalSchedule) else None,
                    crontab=schedule if isinstance(schedule, CrontabSchedule) else None,
                    name=f"Trigger-{trigger.id}-{name}",
                    task="triggers.tasks.execute_trigger",
                    args=json.dumps([trigger.id]),
                    one_off=False,
                )

                execute_trigger.delay(trigger.id)  # ✅ Immediate execution for recurring

            elif schedule_type == "one-time":
                execute_trigger.apply_async((trigger.id,), eta=schedule_time)

            return JsonResponse({"message": "Event scheduled successfully", "trigger_id": trigger.id})

        except Exception as e:
            print(f"Error creating trigger: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)
# @csrf_exempt
# def create_trigger(request):
#     """Creates a new trigger and schedules execution."""
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             name = data.get("name")
#             schedule_type = data.get("schedule_type")
#             schedule_time_str = data.get("schedule_time")
#             frequency = data.get("frequency")

#             schedule_time = None
#             if schedule_type == "one-time" and schedule_time_str:
#                 schedule_time = make_aware(datetime.datetime.strptime(schedule_time_str, "%Y-%m-%dT%H:%M"))

#             trigger = Trigger.objects.create(
#                 name=name,
#                 schedule_type=schedule_type,
#                 schedule_time=schedule_time if schedule_type == "one-time" else None,
#                 frequency=frequency,
#             )

#             print(f"Trigger saved with ID: {trigger.id}")

#             # ✅ Handle recurring scheduling
#             if schedule_type == "recurring":
#                 schedule = None

#                 if frequency.endswith("m"):  # Handle minutes-based interval
#                     every = int(frequency[:-1])
#                     schedule, _ = IntervalSchedule.objects.get_or_create(every=every, period=IntervalSchedule.MINUTES)

#                 elif frequency.endswith("h"):  # Handle hours-based interval
#                     every = int(frequency[:-1])
#                     schedule, _ = IntervalSchedule.objects.get_or_create(every=every, period=IntervalSchedule.HOURS)

#                 elif frequency.endswith("d"):  # Handle days-based interval
#                     every = int(frequency[:-1])
#                     schedule, _ = IntervalSchedule.objects.get_or_create(every=every, period=IntervalSchedule.DAYS)

#                 elif frequency.endswith("w"):  # Handle weeks-based interval
#                     every = int(frequency[:-1])
#                     schedule, _ = IntervalSchedule.objects.get_or_create(every=every, period=IntervalSchedule.WEEKS)

#                 else:
#                     # ✅ If it's not a predefined interval, assume it's a **custom cron expression**
#                     cron_parts = frequency.split(" ")
#                     if len(cron_parts) != 5:
#                         return JsonResponse({"error": "Invalid cron expression. Must be like: '*/5 * * * *'"}, status=400)

#                     schedule, _ = CrontabSchedule.objects.get_or_create(
#                         minute=cron_parts[0],
#                         hour=cron_parts[1],
#                         day_of_month=cron_parts[2],
#                         month_of_year=cron_parts[3],
#                         day_of_week=cron_parts[4]
#                     )

#                 # ✅ Create the Periodic Task for Celery Beat
#                 periodic_task = PeriodicTask.objects.create(
#                     interval=schedule if isinstance(schedule, IntervalSchedule) else None,
#                     crontab=schedule if isinstance(schedule, CrontabSchedule) else None,
#                     name=f"Trigger-{trigger.id}-{name}",
#                     task="triggers.tasks.execute_trigger",
#                     args=json.dumps([trigger.id]),
#                     one_off=False,
#                 )

#                 # ✅ Execute **immediately**, then let it continue recurring
#                 execute_trigger.delay(trigger.id)

#             elif schedule_type == "one-time":
#                 execute_trigger.apply_async((trigger.id,), eta=schedule_time)  # ✅ Schedule execution for one-time

#             return JsonResponse({"message": "Event scheduled successfully", "trigger_id": trigger.id})

#         except Exception as e:
#             print(f"Error creating trigger: {e}")
#             return JsonResponse({"error": str(e)}, status=500)

#     return JsonResponse({"error": "Invalid request"}, status=400)
# def create_trigger(request):
#     """Creates a new trigger and schedules execution."""
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             name = data.get("name")
#             schedule_type = data.get("schedule_type")
#             schedule_time_str = data.get("schedule_time")
#             frequency = data.get("frequency")

#             schedule_time = None
#             if schedule_type == "one-time" and schedule_time_str:
#                 schedule_time = make_aware(datetime.datetime.strptime(schedule_time_str, "%Y-%m-%dT%H:%M"))

#             trigger = Trigger.objects.create(
#                 name=name,
#                 schedule_type=schedule_type,
#                 schedule_time=schedule_time if schedule_type == "one-time" else None,
#                 frequency=frequency,
#             )

#             print(f"Trigger saved with ID: {trigger.id}")

#             # ✅ Handle recurring scheduling
#             if schedule_type == "recurring":
#                 schedule = None

#                 if frequency.endswith("m"):  # Handle minutes-based interval
#                     every = int(frequency[:-1])
#                     schedule, _ = IntervalSchedule.objects.get_or_create(every=every, period=IntervalSchedule.MINUTES)

#                 elif frequency.endswith("h"):  # Handle hours-based interval
#                     every = int(frequency[:-1])
#                     schedule, _ = IntervalSchedule.objects.get_or_create(every=every, period=IntervalSchedule.HOURS)

#                 elif frequency.endswith("d"):  # Handle days-based interval
#                     every = int(frequency[:-1])
#                     schedule, _ = IntervalSchedule.objects.get_or_create(every=every, period=IntervalSchedule.DAYS)

#                 elif frequency.endswith("w"):  # Handle weeks-based interval
#                     every = int(frequency[:-1])
#                     schedule, _ = IntervalSchedule.objects.get_or_create(every=every, period=IntervalSchedule.WEEKS)

#                 else:
#                     # ✅ If it's not a predefined interval, assume it's a **custom cron expression**
#                     cron_parts = frequency.split(" ")
#                     if len(cron_parts) != 5:
#                         return JsonResponse({"error": "Invalid cron expression. Must be like: '*/5 * * * *'"}, status=400)

#                     schedule, _ = CrontabSchedule.objects.get_or_create(
#                         minute=cron_parts[0],
#                         hour=cron_parts[1],
#                         day_of_month=cron_parts[2],
#                         month_of_year=cron_parts[3],
#                         day_of_week=cron_parts[4]
#                     )

#                 # ✅ Create the Periodic Task for Celery Beat
#                 PeriodicTask.objects.create(
#                     interval=schedule if isinstance(schedule, IntervalSchedule) else None,
#                     crontab=schedule if isinstance(schedule, CrontabSchedule) else None,
#                     name=f"Trigger-{trigger.id}-{name}",
#                     task="triggers.tasks.execute_trigger",
#                     args=json.dumps([trigger.id]),
#                     one_off=False,
#                 )

#             elif schedule_type == "one-time":
#                 execute_trigger.apply_async((trigger.id,), eta=schedule_time)  # ✅ Schedule execution for one-time

#             return JsonResponse({"message": "Event scheduled successfully", "trigger_id": trigger.id})

#         except Exception as e:
#             print(f"Error creating trigger: {e}")
#             return JsonResponse({"error": str(e)}, status=500)

#     return JsonResponse({"error": "Invalid request"}, status=400)
def trigger_execute(request, trigger_id):
    """Manually execute a scheduled trigger."""
    execute_trigger.delay(trigger_id)  # Call Celery task asynchronously
    return JsonResponse({"message": f"Trigger {trigger_id} execution started"})

@csrf_exempt
def delete_trigger(request, trigger_id):
    """Deletes a trigger and its Celery Beat periodic task if applicable."""
    if request.method == "DELETE":  
        try:
            trigger = Trigger.objects.get(id=trigger_id)
            periodic_task_name = f"Trigger-{trigger.id}-{trigger.name}"

            # ✅ Ensure proper deletion of PeriodicTask
            PeriodicTask.objects.filter(name=periodic_task_name).delete()

            trigger.delete()
            return JsonResponse({"message": "Trigger deleted successfully"})
        except Trigger.DoesNotExist:
            return JsonResponse({"error": "Trigger not found"}, status=404)
    
    return JsonResponse({"error": "Invalid request method"}, status=400)
def fetch_executed_events(request):
    """Returns a list of event logs, including name and type even after deletion."""
    executed_events = EventLog.objects.order_by('-executed_at')[:10]

    event_data = [
        {
            "name": event.trigger_name if event.trigger_name else "Unknown",
            "type": event.trigger_type if event.trigger_type else "Unknown",
            "executed_at": event.executed_at.strftime('%Y-%m-%d %H:%M:%S'),
            "source": event.creation_source,
            "payload": event.payload if event.payload else {},
            "status": event.status,

        }
        for event in executed_events
    ]
    return JsonResponse({"executed_events": event_data})

def fetch_scheduled_events(request):
    """Returns scheduled events, excluding executed one-time triggers."""
    executed_trigger_ids = EventLog.objects.values_list("trigger_id", flat=True)  # Get executed triggers
    
    scheduled_triggers = Trigger.objects.filter(schedule_type="recurring") | Trigger.objects.filter(
        schedule_type="one-time",
        schedule_time__gte=now(),  # Only show future one-time events
    ).exclude(id__in=executed_trigger_ids)  # Remove already executed one-time triggers

    return JsonResponse({
        "scheduled_events": [
            {
                "id": t.id,
                "name": t.name,
                "schedule_type": t.schedule_type,
                "schedule_time": t.schedule_time.strftime("%Y-%m-%d %H:%M:%S") if t.schedule_time else "N/A"
            }
            for t in scheduled_triggers
        ]
    })
@csrf_exempt
@api_view(['POST'])
def execute_api_trigger(request):
    """Handles API-triggered events: creates and executes immediately."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name")
            trigger_type = data.get("type")
            schedule_time_str = data.get("schedule_time")
            frequency = data.get("frequency")
            payload = data.get("payload", {})

            if not name or not trigger_type:
                return JsonResponse({"error": "Missing required fields (name, type)"}, status=400)

            schedule_time = None
            if trigger_type == "one-time":
                if not schedule_time_str:
                    return JsonResponse({"error": "Missing schedule_time for one-time trigger"}, status=400)
                schedule_time = timezone.make_aware(datetime.datetime.strptime(schedule_time_str, "%Y-%m-%dT%H:%M:%S"))
            trigger = Trigger.objects.create(
                name=name,
                schedule_type=trigger_type,
                schedule_time=schedule_time,
                creation_source="api",
                frequency=frequency if trigger_type == "recurring" else None,
                payload=json.dumps(payload)
            )

            # Log execution (creation source = API)
            # EventLog.objects.create(
            #     trigger=trigger,
            #     trigger_name=trigger.name,
            #     trigger_type=trigger.schedule_type,
            #     creation_source="api",
            #     executed_at=timezone.now(),
            #     payload=payload,
            #     status="completed"
            # )

            #  Handle one-time execution
            if trigger_type == "one-time":
                execute_trigger.apply_async((trigger.id,), eta=schedule_time)
            
            #  Handle recurring execution
            elif trigger_type == "recurring":
                if not frequency:
                    return JsonResponse({"error": "Missing frequency for recurring trigger"}, status=400)
                
                cron_parts = frequency.split(" ")
                if len(cron_parts) != 5:
                    return JsonResponse({"error": "Invalid cron expression"}, status=400)

                schedule, _ = CrontabSchedule.objects.get_or_create(
                    minute=cron_parts[0], hour=cron_parts[1],
                    day_of_month=cron_parts[2], month_of_year=cron_parts[3],
                    day_of_week=cron_parts[4]
                )

                PeriodicTask.objects.update_or_create(
                    name=f"API-Trigger-{trigger.id}-{name}",
                    defaults={
                        "crontab": schedule,
                        "task": "triggers.tasks.execute_trigger",
                        "args": json.dumps([trigger.id])
                    }
                )

                # Execute immediately once
                execute_trigger.delay(trigger.id)

            return JsonResponse({"message": "API trigger executed successfully", "trigger_id": trigger.id})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)
@csrf_exempt
def trigger_test_event(request):
    """Triggers a one-time test event without storing it in the database."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name")
            schedule_time_str = data.get("schedule_time")

            if not name or not schedule_time_str:
                return JsonResponse({"error": "Missing required fields (name, schedule_time)"}, status=400)

            # ✅ Handle relative scheduling (e.g., "10m", "2h")
            if schedule_time_str[-1] in ["m", "h", "d"]:
                unit = schedule_time_str[-1]
                value = int(schedule_time_str[:-1])

                time_deltas = {
                    "m": datetime.timedelta(minutes=value),
                    "h": datetime.timedelta(hours=value),
                    "d": datetime.timedelta(days=value),
                }
                schedule_time = timezone.now() + time_deltas[unit]
            else:
                # ✅ Handle absolute scheduling (Datetime format)
                schedule_time = timezone.make_aware(datetime.datetime.strptime(schedule_time_str, "%Y-%m-%dT%H:%M"))

            result = execute_trigger.apply_async(args=[None], eta=schedule_time)

            return JsonResponse({
                "message": f"Test event '{name}' scheduled successfully for {schedule_time}!",
                "test_trigger": True,
                "scheduled_at": schedule_time.strftime('%Y-%m-%d %H:%M:%S')
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def update_trigger(request, trigger_id):
    """Updates an existing trigger."""
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
            name = data.get("name")
            schedule_time = data.get("schedule_time")
            frequency = data.get("frequency")

            trigger = Trigger.objects.get(id=trigger_id)
            trigger.name = name
            trigger.schedule_time = schedule_time if schedule_time else None
            trigger.frequency = frequency if frequency else None
            trigger.save()

            return JsonResponse({"message": "Trigger updated successfully!"})
        except Trigger.DoesNotExist:
            return JsonResponse({"error": "Trigger not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)