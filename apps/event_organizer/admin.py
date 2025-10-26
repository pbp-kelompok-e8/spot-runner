from django.contrib import admin
from .models import EventOrganizer


@admin.register(EventOrganizer)
class EventOrganizerAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'name',
        'base_location',
        'total_events',
        'rating',
        'review_count',
        'coin',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'base_location',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'base_location',
    )
    readonly_fields = ('created_at', 'updated_at',)
    ordering = ('-created_at',)

    fieldsets = (
        ('Account Info', {
            'fields': ('user', 'profile_picture', 'base_location')
        }),
        ('Performance Metrics', {
            'fields': ('total_events', 'rating', 'review_count', 'coin')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def name(self, obj):
        """Menampilkan nama lengkap (atau username jika nama kosong)."""
        return obj.name
    name.short_description = "Organizer Name"