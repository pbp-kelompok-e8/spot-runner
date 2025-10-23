from django.urls import path
from apps.merchandise.views import *

app_name = 'merchandise'

urlpatterns = [
    path('', show_merchandise, name='show_merchandise'),
    path('<uuid:id>/', product_detail, name='product_detail'),
    path('add/', add_merchandise, name='add_merchandise'),
    path('edit/<int:id>/', edit_merchandise, name='edit_merchandise'),
    path('delete/<int:id>/', delete_merchandise, name='delete_merchandise'),

]