from django.urls import path
from . import views
from .views import create_event, show_event, show_xml, show_json, show_xml_by_id, show_json_by_id, edit_event, delete_event

app_name = 'event'

urlpatterns = [
    path('create-event/', create_event, name='create_event'),
    path('<str:id>/', show_event, name='show_event'),
    path('xml/', show_xml, name='show_xml'),
    path('json/', show_json, name='show_json'),
    path('xml/<str:event_id>/', show_xml_by_id, name='show_xml_by_id'),
    path('json/<str:event_id>/', show_json_by_id, name='show_json_by_id'),
    path('<uuid:id>/edit', edit_event, name='edit_event'),
    path('<uuid:id>/delete', delete_event, name='delete_event'),
]