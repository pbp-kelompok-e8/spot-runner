# apps/review/urls.py
from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
    path('api/reviews/', views.get_all_reviews, name='get_all_reviews'),
    path('api/reviews/<str:review_id>/', views.get_review_detail, name='get_review_detail'),
    path('api/reviews/event/<str:event_id>/', views.get_event_reviews, name='get_event_reviews'),
    path('create/<uuid:event_id>/', views.create_review, name='create_review'),
    path('<str:review_id>/edit/', views.edit_review, name='edit_review'),
    path('<str:review_id>/delete/', views.delete_review, name='delete_review'),
    path('proxy-image/', views.proxy_image, name='proxy_image'),
    path('create-flutter/', views.create_review_flutter, name='create_review_flutter'),
]