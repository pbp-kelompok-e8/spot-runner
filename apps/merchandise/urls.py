from django.urls import path
from apps.merchandise.views import show_merchandise
from apps.merchandise import views 

app_name = 'merchandise'

urlpatterns = [
    path('', views.show_merchandise, name='show_merchandise'),
    path('redeem/<uuid:variant_id>/', views.redeem_variant, name='redeem_variant'),
]
