
from django.db import models
from django.conf import settings


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
    total_events = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    review_count = models.IntegerField(default=0)
    coin = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username
    
    @property
    def name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username
    

