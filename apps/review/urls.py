# apps/review/urls.py
from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
    path('create/<uuid:event_id>/', views.create_review, name='create_review'),
    path('<int:review_id>/edit/', views.edit_review, name='edit_review'),
    path('<int:review_id>/delete/', views.delete_review, name='delete_review'),
]