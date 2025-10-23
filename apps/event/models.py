from django.db import models
from django.utils import timezone


# Create your models here.
class Event(models.Model):
    STATUS_CHOICES = [
        ('ongoing', 'On Going'),
        ('finished', 'Finished'),
        ('canceled', 'Canceled'),
    ]

    TYPES_CHOICES = [
        ('marathon', 'Marathon'),
        ('half_marathon', 'Half Marathon'),
        ('10k', '10K Marathon'),
    ]

    organizer = models.ForeignKey('event_organizer.EventOrganizer', on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    venue = models.CharField(max_length=255)  # e.g. "New Jersey Motorsports Park"
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')
    types = models.JSONField(help_text="List of event types (Marathon, Half marathon, 10K)")  
    total_participants = models.IntegerField(default=0)
    max_participants = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title