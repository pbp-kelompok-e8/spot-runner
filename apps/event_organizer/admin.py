from django.contrib import admin
from .models import EventOrganizer
from apps.merchandise.models import Merchandise

class MerchandiseInline(admin.TabularInline):
    model = Merchandise
    extra = 0
    fields = ('name', 'price_coins', 'category', 'stock')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(EventOrganizer)
class EventOrganizerAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_username', 'base_location', 'total_events', 'rating', 'review_count', 'coin', 'created_at')
    list_filter = ('base_location', 'created_at')
    search_fields = ('user__username', 'base_location')
    readonly_fields = ('created_at', 'updated_at', 'total_events', 'rating', 'review_count')
    raw_id_fields = ('user',)
    
    fieldsets = (
        ('Profile Information', {
            'fields': ('user', 'profile_picture', 'base_location')
        }),
        ('Statistics', {
            'fields': ('total_events', 'rating', 'review_count', 'coin'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [MerchandiseInline]
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'user__username'