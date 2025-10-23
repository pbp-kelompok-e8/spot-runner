from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db.models import Sum
from django.conf import settings
import uuid


User = settings.AUTH_USER_MODEL  # string 'main.User' work di FK
# # contoh:
# user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='redemptions')


# If you keep Profile in accounts app, ensure it includes a coins field:
# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     is_organizer = models.BooleanField(default=False)
#     coins = models.IntegerField(default=0)   # <-- important: user's coin balance


class Merchandise(models.Model):
    """
    Core product entity. Organizer is a User (custom user model).
    """
    CATEGORY_CHOICES = [
        ('apparel', 'Apparel'),
        ('accessories', 'Accessories'),
        ('totebag', 'Tote Bag'),
        ('water_bottle', 'Water Bottle'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='merchandise')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='apparel', db_index=True)
    price_coins = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.organizer}"

    @property
    def total_stock(self):
        return self.variants.aggregate(total=Sum('stock'))['total'] or 0

    @property
    def available(self):
        return self.total_stock > 0

    @property
    def main_image(self):
        return self.images.order_by('order').first()


class MerchVariant(models.Model):
    """
    Variant for a merchandise (size, maybe color) with separate stock.
    """
    SIZE_CHOICES = [
        ('XS','XS'), ('S','S'), ('M','M'), ('L','L'), ('XL','XL'), ('XXL','XXL'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchandise = models.ForeignKey(Merchandise, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=64, blank=True)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, blank=True)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('merchandise', 'size', 'sku')
        ordering = ['-created_at']

    @property
    def is_in_stock(self):
        return self.stock > 0


class MerchImage(models.Model):
    """
    Optional multiple images per merchandise.
    """
    merchandise = models.ForeignKey(Merchandise, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='merch_images/')
    alt_text = models.CharField(max_length=255, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.merchandise.name} (order {self.order})"


class Redemption(models.Model):
    """
    Record of a user redeeming a merchandise variant.
    Snapshot price_per_item and total_coins so history stays consistent.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='redemptions')
    merchandise = models.ForeignKey(Merchandise, on_delete=models.SET_NULL, null=True, related_name='redemptions')
    variant = models.ForeignKey(MerchVariant, on_delete=models.SET_NULL, null=True, related_name='redemptions')
    price_per_item = models.PositiveIntegerField()   # snapshot
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    total_coins = models.PositiveIntegerField()
    redeemed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-redeemed_at']


