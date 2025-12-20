from django.urls import path
from apps.main.views import register, show_main, login_user, show_user, logout_user, edit_profile_runner, cancel_event, participate_in_event, change_password, delete_profile, show_all_users_json, api_profile, api_events, show_all_users_json, show_user_json, api_participate_event, api_cancel_event, api_change_password, api_delete_account, api_edit_profile
from apps.event.views import create_event, show_event, show_xml, show_json, show_xml_by_id, show_json_by_id, edit_event, delete_event
from apps.review.views import create_review

app_name = "main"

urlpatterns = [
    path('', show_main, name='show_main'),
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('user/<str:username>', show_user, name='show_user'),
    path('user/<str:username>/edit', edit_profile_runner, name='edit_profile'),
    path('user/<str:username>/change-password', change_password, name='change_password'),
    path('user/<str:username>/cancel-event/<str:id>/', cancel_event, name='cancel_event'),
    path('user/<str:username>/participate-event/<str:id>/<str:category_key>/', participate_in_event, name='participate_event'),
    path('user/<str:username>/delete-account', delete_profile, name='delete_profile'),
    path('all-users/', show_all_users_json, name='show_all_users_json'),
    path('<str:username>/json', show_user_json, name='show_user_json'),
    path('api/profile/', api_profile, name='api_profile'),
    path('api/events/', api_events, name='api_events'),
    path('api/participate/<str:username>/<str:id>/<str:category_key>/', api_participate_event, name='api_participate_event'),
    path('api/cancel/<str:username>/<str:id>/', api_cancel_event, name='api_cancel_event'),
    path('api/change-password/', api_change_password, name='api_change_password'),
    path('api/delete-account/', api_delete_account, name='api_delete_account'),
    path('api/edit-profile/', api_edit_profile, name='api_edit_profile'),


    # path('create-event/', create_event, name='create_event'),
    # path('xml/', show_xml, name='show_xml'),
    # path('json/', show_json, name='show_json'),
    # path('xml/<str:event_id>/', show_xml_by_id, name='show_xml_by_id'),
    # path('json/<str:event_id>/', show_json_by_id, name='show_json_by_id'),
    # path('<uuid:id>/edit', edit_event, name='edit_event'),
    # path('<uuid:id>/delete', delete_event, name='delete_event'),
    # path('<str:id>/', show_event, name='show_event'),
]