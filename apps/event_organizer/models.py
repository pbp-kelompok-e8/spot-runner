from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


# EventOrganizer represents a user who can create and manage events.
# Username/password are managed by Django's user model; this model
# stores organizer-specific profile data (profile picture, base location).
class EventOrganizer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='event_organizer_profile'
    )

    profile_picture = models.URLField(blank=True, null=True)
    base_location = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return getattr(self.user, 'username', f'EventOrganizer({self.pk})')