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

    # Flutter JSON endpoints
    path('json/', show_json, name='merchandise_json'),
    path('json/<uuid:id>/', show_json_by_id, name='merchandise_detail_json'),
    path('redemption/json/', show_redemption_json, name='redemption_json'),
    path('redemption/json/<uuid:id>/', show_redemption_json_by_id, name='redemption_detail_json'),
    path('user-coins/', get_user_coins, name='user_coins'),

    # path('debug-user/', debug_user_info, name='debug_user'),

    path('create-flutter/', create_merchandise_flutter, name='create_merchandise_flutter'),
    path('edit-flutter/<uuid:id>/', edit_merchandise_flutter, name='edit_merchandise_flutter'),
    path('delete-flutter/<uuid:id>/', delete_merchandise_flutter, name='delete_merchandise_flutter'),
    path('proxy-image/', proxy_image, name='proxy_image'),
]