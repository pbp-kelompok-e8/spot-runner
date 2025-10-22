from django.db import models


# Create your models here.
class Review(models.Model):
	organizer = models.ForeignKey('event_organizer.EventOrganizer', on_delete=models.CASCADE, related_name='reviews')
