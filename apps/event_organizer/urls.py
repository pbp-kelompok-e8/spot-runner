# apps/event_organizer/urls.py
from django.urls import path
from . import views

app_name = 'event_organizer'

app_name = 'event_organizer'

urlpatterns = [
    path('', views.index, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),
]