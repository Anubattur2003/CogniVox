"""
Django models for MCP (Model Context Protocol) server management.

These models store user-specific MCP server configurations and discovered
tools, resources, and prompts from connected servers.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import json


class MCPServerConfig(models.Model):
    """
    User-specific MCP server configurations.
    Stores connection details for different types of MCP servers.
    """
    
    SERVER_TYPES = [
        ('stdio', 'Standard I/O'),
        ('sse', 'Server-Sent Events'),
        ('http', 'HTTP/REST'),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mcp_servers'
    )
    name = models.CharField(max_length=255, help_text="Display name for the server")
    description = models.TextField(blank=True, null=True, help_text="Optional description")
    server_type = models.CharField(
        max_length=10,
        choices=SERVER_TYPES,
        default='stdio',
        help_text="Type of MCP server connection"
    )
    
    # Connection details
    command = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Command to run for stdio servers (e.g., 'node server.js')"
    )
    url = models.URLField(
        blank=True,
        null=True,
        help_text="URL for HTTP/SSE servers"
    )
    args = models.JSONField(
        default=list,
        blank=True,
        help_text="Command arguments as JSON array"
    )
    env_vars = models.JSONField(
        default=dict,
        blank=True,
        help_text="Environment variables as JSON object"
    )
    
    # Configuration options
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this server is currently enabled"
    )
    auto_connect = models.BooleanField(
        default=True,
        help_text="Automatically connect on app startup"
    )
    require_approval = models.BooleanField(
        default=False,
        help_text="Require user approval before executing tools"
    )
    timeout = models.IntegerField(
        default=30,
        help_text="Connection timeout in seconds"
    )
    
    # Metadata
    last_connected_at = models.DateTimeField(blank=True, null=True)
    last_sync_at = models.DateTimeField(blank=True, null=True)
    connection_status = models.CharField(
        max_length=20,
        default='disconnected',
        choices=[
            ('connected', 'Connected'),
            ('disconnected', 'Disconnected'),
            ('error', 'Error'),
            ('connecting', 'Connecting'),
        ]
    )
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'mcpserver'
        db_table = 'mcp_server_configs'
        ordering = ['-created_at']
        unique_together = [['user', 'name']]
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['connection_status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.server_type})"
    
    def mark_connected(self):
        """Mark server as successfully connected."""
        self.connection_status = 'connected'
        self.last_connected_at = timezone.now()
        self.error_message = None
        self.save(update_fields=['connection_status', 'last_connected_at', 'error_message'])
    
    def mark_disconnected(self, error=None):
        """Mark server as disconnected."""
        self.connection_status = 'error' if error else 'disconnected'
        self.error_message = error
        self.save(update_fields=['connection_status', 'error_message'])
    
    def get_connection_config(self):
        """Get connection configuration as a dictionary."""
        config = {
            'type': self.server_type,
            'timeout': self.timeout,
        }
        
        if self.server_type == 'stdio':
            config['command'] = self.command or ''
            # Ensure args is always a list (JSONField might return None or other types)
            if self.args is None:
                config['args'] = []
            elif isinstance(self.args, list):
                config['args'] = self.args
            else:
                # Convert to list if it's not already
                config['args'] = [str(self.args)]
            # Ensure env_vars is always a dict
            config['env'] = self.env_vars if isinstance(self.env_vars, dict) else {}
        else:
            config['url'] = self.url or ''
        
        return config


class MCPTool(models.Model):
    """
    Discovered tools from MCP servers.
    Tools are callable functions exposed by MCP servers.
    """
    
    id = models.AutoField(primary_key=True)
    server_config = models.ForeignKey(
        MCPServerConfig,
        on_delete=models.CASCADE,
        related_name='tools'
    )
    tool_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    input_schema = models.JSONField(
        default=dict,
        help_text="JSON Schema for tool input parameters"
    )
    
    # Usage tracking
    is_enabled = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    last_used_at = models.DateTimeField(blank=True, null=True)
    average_execution_time = models.FloatField(
        default=0.0,
        help_text="Average execution time in seconds"
    )
    
    # Metadata
    last_synced_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'mcpserver'
        db_table = 'mcp_tools'
        ordering = ['tool_name']
        unique_together = [['server_config', 'tool_name']]
        indexes = [
            models.Index(fields=['server_config', 'is_enabled']),
            models.Index(fields=['tool_name']),
        ]

    def __str__(self):
        return f"{self.server_config.name} - {self.tool_name}"
    
    def record_usage(self, execution_time=None):
        """Record a tool usage."""
        self.usage_count += 1
        self.last_used_at = timezone.now()
        
        if execution_time is not None:
            # Update moving average
            if self.average_execution_time == 0:
                self.average_execution_time = execution_time
            else:
                # Simple moving average
                self.average_execution_time = (
                    (self.average_execution_time * (self.usage_count - 1) + execution_time) 
                    / self.usage_count
                )
        
        self.save(update_fields=['usage_count', 'last_used_at', 'average_execution_time'])


class MCPResource(models.Model):
    """
    Resources exposed by MCP servers.
    Resources are readable data sources (like GET endpoints).
    """
    
    id = models.AutoField(primary_key=True)
    server_config = models.ForeignKey(
        MCPServerConfig,
        on_delete=models.CASCADE,
        related_name='resources'
    )
    resource_uri = models.CharField(
        max_length=500,
        help_text="URI or identifier for the resource"
    )
    resource_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    resource_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Type of resource (e.g., 'file', 'database', 'api')"
    )
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="MIME type of the resource content"
    )
    
    # Metadata
    is_enabled = models.BooleanField(default=True)
    access_count = models.IntegerField(default=0)
    last_accessed_at = models.DateTimeField(blank=True, null=True)
    last_synced_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'mcpserver'
        db_table = 'mcp_resources'
        ordering = ['resource_name']
        unique_together = [['server_config', 'resource_uri']]
        indexes = [
            models.Index(fields=['server_config', 'is_enabled']),
            models.Index(fields=['resource_type']),
        ]

    def __str__(self):
        return f"{self.server_config.name} - {self.resource_name}"
    
    def record_access(self):
        """Record a resource access."""
        self.access_count += 1
        self.last_accessed_at = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed_at'])


class MCPPrompt(models.Model):
    """
    Prompts (templates) exposed by MCP servers.
    Prompts are reusable templates for LLM interactions.
    """
    
    id = models.AutoField(primary_key=True)
    server_config = models.ForeignKey(
        MCPServerConfig,
        on_delete=models.CASCADE,
        related_name='prompts'
    )
    prompt_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    prompt_template = models.TextField(
        blank=True,
        null=True,
        help_text="The actual prompt template text"
    )
    arguments = models.JSONField(
        default=list,
        help_text="List of argument definitions for the prompt"
    )
    
    # Metadata
    is_enabled = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    last_used_at = models.DateTimeField(blank=True, null=True)
    last_synced_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'mcpserver'
        db_table = 'mcp_prompts'
        ordering = ['prompt_name']
        unique_together = [['server_config', 'prompt_name']]
        indexes = [
            models.Index(fields=['server_config', 'is_enabled']),
            models.Index(fields=['prompt_name']),
        ]

    def __str__(self):
        return f"{self.server_config.name} - {self.prompt_name}"
    
    def record_usage(self):
        """Record a prompt usage."""
        self.usage_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['usage_count', 'last_used_at'])


class MCPExecutionLog(models.Model):
    """
    Logs of MCP tool executions for debugging and auditing.
    Stored in MongoDB for better performance with large logs.
    """
    
    EXECUTION_STATUS = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('error', 'Error'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mcp_executions'
    )
    tool = models.ForeignKey(
        MCPTool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executions'
    )
    tool_name = models.CharField(max_length=255, help_text="Tool name for reference")
    server_name = models.CharField(max_length=255, help_text="Server name for reference")
    
    # Execution details
    status = models.CharField(
        max_length=20,
        choices=EXECUTION_STATUS,
        default='pending'
    )
    input_params = models.JSONField(default=dict)
    output_result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Timing
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(blank=True, null=True)
    execution_time = models.FloatField(
        default=0.0,
        help_text="Execution time in seconds"
    )
    
    # Context
    chat_thread_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Associated chat thread if executed from chat"
    )
    
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = 'mcpserver'
        db_table = 'mcp_execution_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['tool', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['chat_thread_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.tool_name} - {self.status}"
    
    def mark_running(self):
        """Mark execution as running."""
        self.status = 'running'
        self.save(update_fields=['status'])
    
    def mark_success(self, result, execution_time):
        """Mark execution as successful."""
        self.status = 'success'
        self.output_result = result
        self.completed_at = timezone.now()
        self.execution_time = execution_time
        self.save(update_fields=['status', 'output_result', 'completed_at', 'execution_time'])
    
    def mark_error(self, error_msg, execution_time=None):
        """Mark execution as failed."""
        self.status = 'error'
        self.error_message = error_msg
        self.completed_at = timezone.now()
        if execution_time:
            self.execution_time = execution_time
        self.save(update_fields=['status', 'error_message', 'completed_at', 'execution_time'])

