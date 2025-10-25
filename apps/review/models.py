# apps/review/models.py

from django.db import models
from django.conf import settings
from apps.event.models import Event
from apps.main.models import Runner
from apps.event_organizer.models import EventOrganizer


class Review(models.Model):
    # Runner yang memberikan review (relasi ke Runner model)
    runner = models.ForeignKey(
        Runner,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    # Event yang direview
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    # Event Organizer yang menerima review
    event_organizer = models.ForeignKey(
        EventOrganizer,
        on_delete=models.CASCADE,
        related_name='received_reviews',
        null=True,
        blank=True
    )

    # Rating dan konten review
    rating = models.PositiveIntegerField(default=0)
    review_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.runner.user.username} for {self.event.name}"

    class Meta:
        ordering = ['-created_at']
        # Optional: Pastikan satu runner hanya bisa review satu event sekali
        unique_together = ['runner', 'event']
