from event_trigger_platform.celery import app as celery_app

__all__ = ["celery_app"]  # ✅ Ensures Celery gets initialized properly