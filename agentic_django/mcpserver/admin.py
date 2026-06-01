"""
Admin interface for MCP models.
"""
from django.contrib import admin
from .models import MCPServerConfig, MCPTool, MCPResource, MCPPrompt, MCPExecutionLog


@admin.register(MCPServerConfig)
class MCPServerConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'server_type', 'connection_status', 'is_active', 'last_connected_at')
    list_filter = ('server_type', 'connection_status', 'is_active', 'auto_connect')
    search_fields = ('name', 'description', 'user__username')
    readonly_fields = ('last_connected_at', 'last_sync_at', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'description', 'server_type')
        }),
        ('Connection Details', {
            'fields': ('command', 'url', 'args', 'env_vars', 'timeout')
        }),
        ('Configuration', {
            'fields': ('is_active', 'auto_connect', 'require_approval')
        }),
        ('Status', {
            'fields': ('connection_status', 'error_message', 'last_connected_at', 'last_sync_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MCPTool)
class MCPToolAdmin(admin.ModelAdmin):
    list_display = ('tool_name', 'server_config', 'is_enabled', 'usage_count', 'average_execution_time', 'last_used_at')
    list_filter = ('is_enabled', 'server_config__server_type')
    search_fields = ('tool_name', 'description', 'server_config__name')
    readonly_fields = ('usage_count', 'last_used_at', 'average_execution_time', 'last_synced_at', 'created_at', 'updated_at')


@admin.register(MCPResource)
class MCPResourceAdmin(admin.ModelAdmin):
    list_display = ('resource_name', 'server_config', 'resource_type', 'is_enabled', 'access_count', 'last_accessed_at')
    list_filter = ('is_enabled', 'resource_type', 'mime_type')
    search_fields = ('resource_name', 'resource_uri', 'description', 'server_config__name')
    readonly_fields = ('access_count', 'last_accessed_at', 'last_synced_at', 'created_at', 'updated_at')


@admin.register(MCPPrompt)
class MCPPromptAdmin(admin.ModelAdmin):
    list_display = ('prompt_name', 'server_config', 'is_enabled', 'usage_count', 'last_used_at')
    list_filter = ('is_enabled',)
    search_fields = ('prompt_name', 'description', 'server_config__name')
    readonly_fields = ('usage_count', 'last_used_at', 'last_synced_at', 'created_at', 'updated_at')


@admin.register(MCPExecutionLog)
class MCPExecutionLogAdmin(admin.ModelAdmin):
    list_display = ('tool_name', 'server_name', 'user', 'status', 'execution_time', 'started_at', 'completed_at')
    list_filter = ('status', 'started_at', 'server_name')
    search_fields = ('tool_name', 'server_name', 'user__username', 'chat_thread_id')
    readonly_fields = ('created_at', 'started_at', 'completed_at', 'execution_time')
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Execution Info', {
            'fields': ('user', 'tool', 'tool_name', 'server_name', 'status')
        }),
        ('Parameters & Results', {
            'fields': ('input_params', 'output_result', 'error_message')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'execution_time')
        }),
        ('Context', {
            'fields': ('chat_thread_id',)
        }),
    )

