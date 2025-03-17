from event_trigger_platform.celery import app as celery_app
import triggers.tasks

__all__ = ["celery_app"]