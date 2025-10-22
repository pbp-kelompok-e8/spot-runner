from django.db import models


# Create your models here.
class Event(models.Model):
    organizer = models.ForeignKey('event_organizer.EventOrganizer', on_delete=models.CASCADE, related_name='events')