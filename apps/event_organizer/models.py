from django.db import models

# Create your models here.
class EventOrganizer(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    profile_picture = models.ImageField(upload_to='organizer_profiles/', blank=True, null=True)
    base_location = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Event Organizer'
        verbose_name_plural = 'Event Organizers'