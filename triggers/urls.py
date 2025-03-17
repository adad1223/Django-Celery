from django.urls import path
from django.urls import re_path
from .views import trigger_list, create_trigger, trigger_execute,delete_trigger,fetch_executed_events,execute_api_trigger,trigger_test_event,update_trigger

urlpatterns = [
    path('', trigger_list, name='trigger-list'),
    path('create/', create_trigger, name='create-trigger'),
    path('execute/<int:trigger_id>/', trigger_execute, name='trigger-execute'),
    path('delete/<int:trigger_id>/', delete_trigger, name='delete-trigger'),
    path('executed/', fetch_executed_events, name='fetch-executed-events'),
    path("test/", trigger_test_event, name="test-trigger"),
    path("update/<int:trigger_id>/", update_trigger, name="update-trigger"),
]