# apps/event_organizer/urls.py
from django.urls import path
from . import views

app_name = 'event_organizer'

urlpatterns = [
    path('profile/', views.event_organizer_profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]