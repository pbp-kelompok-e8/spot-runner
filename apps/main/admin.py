from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Runner
# test
class RunnerInline(admin.StackedInline):
    model = Runner
    can_delete = False
    verbose_name_plural = 'Runner Profile'
    fk_name = 'user'

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active', 'has_runner_profile')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)
    
    def get_inlines(self, request, obj=None):
        if obj and obj.role == 'runner':
            return [RunnerInline]
        return []
    
    def has_runner_profile(self, obj):
        if obj.role == 'runner':
            return Runner.objects.filter(user=obj).exists() 
        return None
    has_runner_profile.short_description = 'Has Runner Profile'
    has_runner_profile.boolean = True

@admin.register(Runner)
class RunnerAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_username', 'get_email', 'base_location', 'coin')
    list_filter = ('base_location',)
    
    search_fields = ('user__username', 'user__email', 'base_location') 
    raw_id_fields = ('user',)
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    
    @admin.display(description='Email', ordering='user__email')
    def get_email(self, obj):
        return obj.user.email
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
