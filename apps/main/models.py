from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from apps.event.models import Event
import uuid

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
        through='Attendance',
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



class Attendance(models.Model):

    
    # Pilihan status untuk PENDAFTARAN, bukan untuk Event
    STATUS_CHOICES = [
        ('attending', 'Attending'),
        ('canceled', 'Canceled'),
        ('finished', 'Finished'), 
    ]
    
    # Hubungan ke Runner Anda
    # Ganti 'runner.Runner' jika model Runner Anda ada di app lain
    runner = models.ForeignKey(
        Runner,  # <--- Bukan 'runner.Runner'
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    
    # Hubungan ke Event
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    
    # Status pendaftaran spesifik untuk user ini di event ini
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='attending')
    
    # Participant ID unik untuk pendaftaran ini
    participant_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Tanggal pendaftaran (opsional tapi sangat disarankan)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('runner', 'event') 

    def __str__(self):
        return f"{self.runner.user.username} @ {self.event.name} ({self.status})"


    