from django.contrib import admin
from .models import User, Runner, Attendance


# ======================
# 1️⃣ User Admin
# ======================
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    fieldsets = (
        ('User Info', {'fields': ('username', 'email', 'first_name', 'last_name', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Role & Metadata', {'fields': ('role', 'last_login', 'date_joined')}),
    )
    readonly_fields = ('last_login', 'date_joined')


# ======================
# 2️⃣ Runner Admin
# ======================
@admin.register(Runner)
class RunnerAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'base_location', 'coin')
    list_filter = ('base_location',)
    search_fields = ('user__username', 'email', 'user__first_name', 'user__last_name')
    ordering = ('user__username',)

    fieldsets = (
        ('Runner Info', {'fields': ('user', 'email', 'base_location', 'coin')}),
        ('Attendance Info', {'fields': ('attended_events',)}),
    )

    def username(self, obj):
        """Menampilkan username dari user terkait."""
        return obj.user.username
    username.short_description = "Username"


# ======================
# 3️⃣ Attendance Admin
# ======================
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'runner_username',
        'event_name',
        'status',
        'participant_id',
        'registered_at',
    )
    list_filter = ('status', 'registered_at', 'event__event_status')
    search_fields = ('runner__user__username', 'event__name', 'participant_id')
    readonly_fields = ('participant_id', 'registered_at')
    ordering = ('-registered_at',)

    fieldsets = (
        ('Attendance Info', {
            'fields': ('runner', 'event', 'status')
        }),
        ('Metadata', {
            'fields': ('participant_id', 'registered_at')
        }),
    )

    def runner_username(self, obj):
        """Menampilkan username runner."""
        return obj.runner.user.username
    runner_username.short_description = "Runner"

    def event_name(self, obj):
        """Menampilkan nama event."""
        return obj.event.name
    event_name.short_description = "Event"
