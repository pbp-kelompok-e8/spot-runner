import uuid
from django.db import models
from apps.event_organizer.models import EventOrganizer
from apps.main.models import Runner
from django.core.validators import MinValueValidator

# from django.conf import settings
# User = settings.AUTH_USER_MODEL 

class Merchandise(models.Model):
    CATEGORY_CHOICES = [
        ('apparel', 'Apparel'),
        ('accessories', 'Accessories'),
        ('totebag', 'Tote Bag'),
        ('water_bottle', 'Water Bottle'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    price_coins = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    organizer = models.ForeignKey(EventOrganizer, on_delete=models.CASCADE, related_name='merchandise')
    description = models.TextField()
    image_url = models.URLField(max_length=500)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='apparel')
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} — {self.organizer}"
    
    @property
    def available(self):
        return self.stock > 0

class Redemption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Runner, on_delete=models.CASCADE, related_name='redemptions')
    merchandise = models.ForeignKey(Merchandise, on_delete=models.SET_NULL, null=True, related_name='redemptions')
    
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    redeemed_at = models.DateTimeField(auto_now_add=True)

    def total_coins(self):
        return self.merchandise.price_coins * self.quantity


