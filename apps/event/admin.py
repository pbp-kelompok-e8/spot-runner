from django.contrib import admin
from .models import EventCategory, Event

@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('get_category_display', 'category')
    search_fields = ('category',)
    
    def get_category_display(self, obj):
        return obj.get_category_display()
    get_category_display.short_description = 'Category Name'

class EventCategoryInline(admin.TabularInline):
    model = Event.event_category.through
    extra = 1

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_eo', 'location', 'event_date', 'event_status', 'full', 'capacity', 'total_participans')
    list_filter = ('event_status', 'location', 'event_date', 'full')
    search_fields = ('name', 'description', 'user_eo__user__username')
    readonly_fields = ('id', 'total_participans', 'full')
    date_hierarchy = 'event_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'user_eo')
        }),
        ('Event Details', {
            'fields': ('location', 'event_date', 'regist_deadline', 'contact')
        }),
        ('Capacity & Status', {
            'fields': ('capacity', 'total_participans', 'full', 'event_status')
        }),
        ('Media & Rewards', {
            'fields': ('image', 'image2', 'image3', 'coin')
        }),
    )
    
    inlines = [EventCategoryInline]
    
    def save_model(self, request, obj, form, change):
        # Auto-update full status based on capacity
        if obj.total_participans >= obj.capacity:
            obj.full = True
        else:
            obj.full = False
        super().save_model(request, obj, form, change)