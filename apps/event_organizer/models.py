from django.db import models
from django.conf import settings

<<<<<<< HEAD
# Create your models here.
# class EventOrganizer(models.Model):
#     id = models
=======

# EventOrganizer represents a user who can create and manage events.
# Username/password are managed by Django's user model; this model
# stores organizer-specific profile data (profile picture, base location).
class EventOrganizer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='event_organizer_profile'
    )
    profile_picture = models.ImageField(upload_to='organizer_profiles/', null=True, blank=True)
    base_location = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return getattr(self.user, 'username', f"Organizer {self.pk}")
>>>>>>> d63aff08ffc7953020809a080cd6c724ea2da1c3
