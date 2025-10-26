from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'runner',
        'event',
        'event_organizer',
        'rating',
        'created_at',
    )
    list_filter = (
        'rating',
        'event',
        'event_organizer',
        'created_at',
    )
    search_fields = (
        'runner__user__username',
        'event__name',
        'event_organizer__user__username',
        'review_text',
    )
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    fieldsets = (
        ('Reviewer & Event Info', {
            'fields': ('runner', 'event', 'event_organizer')
        }),
        ('Review Details', {
            'fields': ('rating', 'review_text')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
