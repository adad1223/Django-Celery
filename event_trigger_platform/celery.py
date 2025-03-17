# import os
# from celery import Celery

# # Set default Django settings for Celery
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_trigger_platform.settings')

# app = Celery('event_trigger_platform')

# # Celery timezone settings
# app.conf.enable_utc = False
# app.conf.update(timezone='Asia/Kolkata')

# # Load settings from Django
# app.config_from_object('django.conf:settings', namespace='CELERY')

# # Ensure Celery auto-discovers tasks inside Django apps
# app.autodiscover_tasks()

# # Uncomment these if using Celery Beat for periodic tasks
# app.conf.beat_schedule = {
#     'process-scheduled-triggers': {
#         'task': 'triggers.tasks.process_scheduled_triggers',
#         'schedule': 10.0,  # Runs every 10 seconds
#     },
#     'archive-old-events': {
#         'task': 'triggers.tasks.archive_old_events',
#         'schedule': 10.0,
#     },
#     'delete-old-events': {
#         'task': 'triggers.tasks.delete_old_events',
#         'schedule': 10.0,
#     },
# }

# @app.task(bind=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "event_trigger_platform.settings")

app = Celery("event_trigger_platform")
app.conf.enable_utc = False
app.conf.update(timezone='Asia/Kolkata')
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

import django
django.setup()

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
app.conf.beat_schedule = {
    'archive-old-events': {
        'task': 'triggers.tasks.archive_old_events',
        'schedule': 60.0,
    },
    'delete-old-events': {
        'task': 'triggers.tasks.delete_old_events',
        'schedule': 60.0,
    },
}