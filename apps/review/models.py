from django.db import models
from apps.event_organizer.models import EventOrganizer

# Create your models here.
class Review(models.Model):
    organizer = models.ForeignKey(EventOrganizer, on_delete=models.CASCADE, related_name='review')