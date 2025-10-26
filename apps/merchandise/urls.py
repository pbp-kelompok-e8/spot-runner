from django.urls import path
from apps.merchandise.views import *

app_name = 'merchandise'

urlpatterns = [
    path('', show_merchandise, name='show_merchandise'),
    path('add/', add_merchandise, name='add_merchandise'),
    path('history/', history, name='history'),
    path('<uuid:id>/', product_detail, name='product_detail'),
    path('<uuid:id>/redeem/', redeem_merchandise, name='redeem_merchandise'),
    path('edit/<uuid:id>/', edit_merchandise, name='edit_merchandise'),
    path('delete/<uuid:id>/', delete_merchandise, name='delete_merchandise'),
]