from django.urls import path
from apps.main.views import show_main, logout_user
from apps.event_organizer.views import dashboard_view , profile_view, edit_profile, change_password

app_name = 'event_organizer'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('profile/', profile_view, name='profile'),
    path('logout/', logout_user, name='logout'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('change-password/', change_password, name='change_password'),
]