from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from apps.event.models import Event, EventCategory
import uuid

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = (
        ('runner', 'Runner'),
        ('event_organizer', 'Event Organizer'),
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='runner')


class Attendance(models.Model):

    STATUS_CHOICES = [
        ('attending', 'Attending'),
        ('canceled', 'Canceled'),
        ('finished', 'Finished'), 
    ]


    runner = models.ForeignKey(
        'main.Runner', 
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    
    event = models.ForeignKey(
        'event.Event',
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )

    category = models.ForeignKey(
        'event.EventCategory',
        on_delete=models.SET_NULL, # Agar jika kategori dihapus, attendance tetap ada
        null=True
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='attending')
    
    participant_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('runner', 'event') 

    def __str__(self):
        return f"{self.runner.user.username} @ {self.event.name} ({self.status})"

class Runner(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        primary_key=True
    )

    attended_events = models.ManyToManyField(
        'event.Event',
        through='main.Attendance',
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

    base_location = models.CharField(max_length=50, choices=LOCATION_CHOICES, default='depok')
    coin = models.IntegerField(default=0)




    