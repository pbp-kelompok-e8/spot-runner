from django.contrib import admin
from .models import Merchandise, MerchVariant, MerchImage, Redemption

# Register your models here.

@admin.register(Merchandise)
class MerchandiseAdmin(admin.ModelAdmin):
    list_display = ('name', 'organizer', 'price_coins', 'category', 'is_active')
    list_filter = ('category', 'is_active', 'product_type')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'organizer__username')

@admin.register(MerchVariant)
class MerchVariantAdmin(admin.ModelAdmin):
    list_display = ('merchandise', 'size', 'stock', 'sku')
    list_filter = ('size',)

@admin.register(MerchImage)
class MerchImageAdmin(admin.ModelAdmin):
    list_display = ('merchandise', 'alt_text', 'order')

@admin.register(Redemption)
class RedemptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'merchandise', 'variant', 'total_coins', 'status', 'redeemed_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'merchandise__name')
