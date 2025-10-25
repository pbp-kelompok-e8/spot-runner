# apps/review/urls.py
from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
    path('create/<uuid:event_id>/', views.create_review, name='create_review'),
]