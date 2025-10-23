from django.contrib import admin
from .models import EventOrganizer

@admin.register(EventOrganizer)
class EventOrganizerAdmin(admin.ModelAdmin):
    list_display = ('user', 'base_location', 'created_at')
    list_filter = ('base_location', 'created_at')
    search_fields = ('user__username', 'base_location')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'profile_picture', 'base_location')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )