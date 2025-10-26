from django.contrib import admin
from .models import Merchandise, Redemption


# ======================
# 1️⃣ Merchandise Admin
# ======================
@admin.register(Merchandise)
class MerchandiseAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'organizer_name',
        'category',
        'price_coins',
        'stock',
        'available',
        'created_at',
        'updated_at',
    )
    list_filter = ('category', 'organizer__base_location', 'created_at')
    search_fields = ('name', 'organizer__user__username', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Merchandise Info', {
            'fields': ('name', 'organizer', 'description', 'image_url', 'category')
        }),
        ('Inventory & Pricing', {
            'fields': ('price_coins', 'stock')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def organizer_name(self, obj):
        """Menampilkan nama Event Organizer dari merchandise."""
        return obj.organizer.user.username
    organizer_name.short_description = "Organizer"

    def available(self, obj):
        """Tampilkan status ketersediaan stok."""
        return "✅ Yes" if obj.stock > 0 else "❌ No"
    available.short_description = "Available"
    available.admin_order_field = 'stock'


# ======================
# 2️⃣ Redemption Admin
# ======================
@admin.register(Redemption)
class RedemptionAdmin(admin.ModelAdmin):
    list_display = (
        'runner_username',
        'merchandise_name',
        'quantity',
        'price_per_item',
        'total_coins',
        'redeemed_at',
    )
    list_filter = ('redeemed_at', 'merchandise__category')
    search_fields = ('user__user__username', 'merchandise__name')
    ordering = ('-redeemed_at',)
    readonly_fields = ('price_per_item', 'total_coins', 'redeemed_at')

    fieldsets = (
        ('Redemption Info', {
            'fields': ('user', 'merchandise', 'quantity')
        }),
        ('Transaction Details', {
            'fields': ('price_per_item', 'total_coins', 'redeemed_at')
        }),
    )

    def runner_username(self, obj):
        """Menampilkan username runner yang menukar merchandise."""
        return obj.user.user.username
    runner_username.short_description = "Runner"

    def merchandise_name(self, obj):
        """Menampilkan nama merchandise."""
        return obj.merchandise.name if obj.merchandise else "[Deleted Product]"
    merchandise_name.short_description = "Merchandise"
