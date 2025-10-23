from django.urls import path
from apps.main.views import register, show_main, login_user

app_name = "main"

urlpatterns = [
    path('', show_main, name='show_main'),
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
]