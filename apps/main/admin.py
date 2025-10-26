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


class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    fields = ('event', 'status', 'registered_at')
    readonly_fields = ('registered_at',)

@admin.register(Runner)
class RunnerAdmin(admin.ModelAdmin):
    list_display = ('username', 'user_email', 'base_location', 'coin')
    list_filter = ('base_location',)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    ordering = ('user__username',)
    inlines = [AttendanceInline]  # ✅ Tambahkan inline

    fieldsets = (
        ('Runner Info', {'fields': ('user', 'base_location', 'coin')}),
    )

    def username(self, obj):
        return obj.user.username
    username.short_description = "Username"
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Email"


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