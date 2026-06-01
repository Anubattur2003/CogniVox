from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SubscriptionPlan


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin configuration for User model
    """
    list_display = ('username', 'email', 'full_name', 'role', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('username', 'email', 'full_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'full_name')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Custom fields', {'fields': ('role', 'subscription_plan', 'subscription_start_date', 'subscription_end_date')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """
    Admin configuration for SubscriptionPlan model
    """
    list_display = ('name', 'price', 'duration_days', 'max_requests', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('name', 'description')}),
        ('Pricing', {'fields': ('price', 'duration_days', 'max_requests')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')
