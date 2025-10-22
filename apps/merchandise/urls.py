from django.urls import path
from apps.merchandise.views import show_main

urlpatterns = [
    path('', show_main, name='show_main'),
]
