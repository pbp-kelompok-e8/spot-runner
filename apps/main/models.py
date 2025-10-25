from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from apps.event.models import Event

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = (
        ('runner', 'Runner'),
        ('event_organizer', 'Event Organizer'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='runner')

class Runner(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        primary_key=True
    )

    attended_events = models.ManyToManyField(
        Event,           
        related_name='attendees',     
        blank=True                    
    )

    LOCATION_CHOICES = [
        ('jakarta_barat', 'Jakarta Barat'),
        ('jakarta_pusat', 'Jakarta Pusat'),
        ('jakarta_selatan', 'Jakarta Selatan'),
        ('jakarta_timur', 'Jakarta Timur'),
        ('jakarta_utara', 'Jakarta Utara'),
        ('bekasi', 'Bekasi'),
        ('bogor', 'Bogor'),
        ('depok', 'Depok'),
        ('tangerang', 'Tangerang')
    ]

    email = models.EmailField(unique=True)
    base_location = models.CharField(max_length=50, choices=LOCATION_CHOICES, default='depok')
    coin = models.IntegerField(default=0)


    


    
