from django.contrib import admin
from .models import SystemConfiguration, AuditLog, APIUsageStats


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action_type', 'resource_type', 'resource_id', 'created_at']
    list_filter = ['action_type', 'resource_type', 'created_at']
    search_fields = ['user__email', 'user__username', 'description', 'resource_id']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(APIUsageStats)
class APIUsageStatsAdmin(admin.ModelAdmin):
    list_display = ['date', 'endpoint', 'method', 'total_requests', 'successful_requests', 'failed_requests', 'avg_response_time']
    list_filter = ['method', 'date']
    search_fields = ['endpoint']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
