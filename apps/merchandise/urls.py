from django.urls import path
from apps.merchandise.views import show_main
from . import views

app_name = 'merchandise'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('redeem/<uuid:variant_id>/', views.redeem_variant, name='redeem_variant'),
]
