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
    merchandise = models.ForeignKey(Merchandise, on_delete=models.SET_NULL, null=True, blank=True, related_name='redemptions')
    
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price_per_item = models.PositiveIntegerField(default=0) 
    total_coins = models.PositiveIntegerField(default=0)
    redeemed_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-calculate HANYA jika data baru dan merchandise masih ada
        if self.merchandise and not self._state.adding:  # ← Cek jika baru (belum punya id)
            self.price_per_item = self.merchandise.price_coins
            self.total_coins = self.price_per_item * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        merch_name = self.merchandise.name if self.merchandise else "[Deleted Product]"
        return f"{self.user.user.username} - {merch_name} x{self.quantity}"

    class Meta:
        ordering = ['-redeemed_at']


