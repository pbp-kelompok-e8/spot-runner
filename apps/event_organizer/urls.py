# apps/event_organizer/urls.py
from django.urls import path
from apps.main.views import show_main, logout_user
from apps.event_organizer.views import dashboard_view , show_profile, edit_profile, change_password, delete_account, show_json, change_password_flutter, edit_profile_flutter, delete_account_flutter, profile_json



app_name = 'event_organizer'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('profile/', show_profile, name='profile'),
    path('logout/', logout_user, name='logout'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('change-password/', change_password, name='change_password'),
    path('delete-account/', delete_account, name='delete_account'),
    path('json/', show_json, name='show_json'),
    path('change-password-flutter/', change_password_flutter, name='change_password_flutter'),
    path('edit-profile-flutter/', edit_profile_flutter, name='edit_profile_flutter'),
    path('delete-account-flutter/', delete_account_flutter, name='delete_account_flutter'),
    path('profile/json/', profile_json, name='event_organizer_profile_json'),

]