# merchandise/admin.py
from django.contrib import admin
from .models import Merchandise, Redemption 

@admin.register(Merchandise)
class MerchandiseAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_coins', 'category', 'stock', 'organizer', 'available', 'created_at')
    list_filter = ('category', 'organizer', 'created_at')
    search_fields = ('name', 'organizer__user__username')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('organizer',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'description', 'category', 'image_url')
        }),
        ('Pricing & Inventory', {
            'fields': ('price_coins', 'stock', 'organizer')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def available(self, obj):
        return obj.available
    available.boolean = True
    available.short_description = 'Available'

@admin.register(Redemption)
class RedemptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'merchandise', 'quantity', 'price_per_item', 'total_coins', 'redeemed_at')
    list_filter = ('redeemed_at', 'merchandise__category')
    search_fields = ('user__user__username', 'merchandise__name')
    readonly_fields = ('redeemed_at', 'price_per_item', 'total_coins')
    raw_id_fields = ('user', 'merchandise')
    date_hierarchy = 'redeemed_at'
    
    fieldsets = (
        ('Redemption Details', {
            'fields': ('user', 'merchandise', 'quantity')
        }),
        ('Pricing', {
            'fields': ('price_per_item', 'total_coins'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('redeemed_at',),
            'classes': ('collapse',)
        }),
    )