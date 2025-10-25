# apps/review/urls.py

from django.urls import path
from . import views

app_name = 'review'  # Namespace untuk app review

urlpatterns = [
    path('create/', views.create_review, name='create_review'),
]