from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = (
        ('runner', 'Runner'),
        ('event_organizer', 'Event Organizer'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='runner')
    email = models.EmailField(unique=True)

class Runner(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        primary_key=True
    )

    LOCATION_CHOICES = [
        ('jakarta', 'Jakarta'),
        ('surabaya', 'Surabaya'),
        ('bandung', 'Bandung'),
        ('medan', 'Medan'),
        ('semarang', 'Semarang'),
        ('makassar', 'Makassar'),
        ('palembang', 'Palembang'),
        ('denpasar', 'Denpasar'),
        ('yogyakarta', 'Yogyakarta'),
        ('surakarta', 'Surakarta'),
        ('malang', 'Malang'),
        ('pekanbaru', 'Pekanbaru'),
        ('depok', 'Depok'),
    ]

    base_location = models.CharField(max_length=50, choices=LOCATION_CHOICES, default='depok')
    coin = models.IntegerField(default=0)


    
