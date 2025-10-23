# merchandise/admin.py
from django.contrib import admin
from .models import Merchandise, Redemption 

@admin.register(Merchandise)
class MerchandiseAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_coins', 'category', 'stock', 'organizer']
    list_filter = ['category', 'organizer']
    search_fields = ['name']

@admin.register(Redemption)
class RedemptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'merchandise', 'quantity', 'total_coins', 'redeemed_at']
    list_filter = ['redeemed_at']