"""
URL configuration for spot_runner project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('apps.main.urls')),  # Routing ke app main
    path('admin/', admin.site.urls),
    path('event/', include('apps.event.urls')),  # Routing ke app event
    path('event-organizer/', include('apps.event_organizer.urls')),  # Routing ke app event_organizer
    path('merchandise/', include('apps.merchandise.urls')),  # Routing ke app merchandise
    path('review/', include('apps.review.urls')),  # Routing ke app review
]
