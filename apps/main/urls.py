from django.urls import path
from apps.main.views import register, show_main, login_user, show_user, logout_user

app_name = "main"

urlpatterns = [
    path('', show_main, name='show_main'),
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('user/<str:username>', show_user, name='show_user'),
    path('logout/', logout_user, name='logout'),
]