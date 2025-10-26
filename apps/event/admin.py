from django.contrib import admin
from .models import Event, EventCategory


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'get_category_display_name')
    search_fields = ('category',)
    ordering = ('category',)

    def get_category_display_name(self, obj):
        return obj.get_category_display()
    get_category_display_name.short_description = 'Category Name'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'user_eo',
        'location',
        'event_date',
        'regist_deadline',
        'event_status',
        'capacity',
        'total_participans',
        'full',
    )
    list_filter = (
        'event_status',
        'location',
        'event_category',
        'user_eo',
    )
    search_fields = (
        'name',
        'description',
        'user_eo__user__username',
    )
    readonly_fields = ('id', 'full',)
    filter_horizontal = ('event_category',)
    ordering = ('-event_date',)

    fieldsets = (
        ('Event Information', {
            'fields': (
                'id',
                'name',
                'description',
                'user_eo',
                'event_category',
                'location',
                'event_status',
            )
        }),
        ('Media', {
            'fields': ('image', 'image2', 'image3')
        }),
        ('Schedule & Capacity', {
            'fields': (
                'event_date',
                'regist_deadline',
                'capacity',
                'total_participans',
                'full',
            )
        }),
        ('Contact & Rewards', {
            'fields': ('contact', 'coin')
        }),
    )

    # Tambahkan aksi cepat di admin
    actions = ['mark_as_finished', 'mark_as_ongoing']

    def mark_as_finished(self, request, queryset):
        updated = queryset.update(event_status='finished')
        self.message_user(request, f"{updated} event(s) marked as Finished.")
    mark_as_finished.short_description = "Mark selected events as Finished"

    def mark_as_ongoing(self, request, queryset):
        updated = queryset.update(event_status='on_going')
        self.message_user(request, f"{updated} event(s) marked as On Going.")
    mark_as_ongoing.short_description = "Mark selected events as On Going"
