from django.urls import path
from .views import execute_api_trigger, fetch_executed_events

urlpatterns = [
    path("create/", execute_api_trigger, name="execute-api-trigger"),
    path("executed/", fetch_executed_events, name="fetch-executed-events"),
]