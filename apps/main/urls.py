from django.urls import path
from apps.main.views import register, show_main, login_user, show_user, logout_user, edit_profile_runner, cancel_event, participate_in_event
from apps.event.views import create_event, show_event, show_xml, show_json, show_xml_by_id, show_json_by_id, edit_event, delete_event
from apps.review.views import create_review

app_name = "main"

urlpatterns = [
    path('', show_main, name='show_main'),
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('user/<str:username>', show_user, name='show_user'),
    path('logout/', logout_user, name='logout'),
    path('create-event/', create_event, name='create_event'),
    path('<str:id>/', show_event, name='show_event'),
    path('xml/', show_xml, name='show_xml'),
    path('json/', show_json, name='show_json'),
    path('xml/<str:event_id>/', show_xml_by_id, name='show_xml_by_id'),
    path('json/<str:event_id>/', show_json_by_id, name='show_json_by_id'),
    path('<uuid:id>/edit', edit_event, name='edit_event'),
    path('<uuid:id>/delete', delete_event, name='delete_event'),
    path('user/<str:username>/edit', edit_profile_runner, name='edit_profile'),
    path('user/<str:username>/cancel-event/<str:id>/', cancel_event, name='cancel_event'),
    path('user/<str:username>/participate-event/<str:id>/', participate_in_event, name='participate_event'),
    path('user/<str:username>/change-password', edit_profile_runner, name='edit_profile'),
]