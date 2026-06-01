"""
Serializers for MCP models.
"""
from rest_framework import serializers
from .models import MCPServerConfig, MCPTool, MCPResource, MCPPrompt, MCPExecutionLog


class MCPServerConfigSerializer(serializers.ModelSerializer):
    """Serializer for MCP Server Configuration."""
    
    tool_count = serializers.SerializerMethodField()
    resource_count = serializers.SerializerMethodField()
    prompt_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MCPServerConfig
        fields = [
            'id', 'name', 'description', 'server_type', 'command', 'url',
            'args', 'env_vars', 'is_active', 'auto_connect', 'require_approval',
            'timeout', 'connection_status', 'error_message', 'last_connected_at',
            'last_sync_at', 'created_at', 'updated_at', 'tool_count',
            'resource_count', 'prompt_count'
        ]
        read_only_fields = [
            'connection_status', 'error_message', 'last_connected_at',
            'last_sync_at', 'created_at', 'updated_at'
        ]
    
    def get_tool_count(self, obj):
        return obj.tools.filter(is_enabled=True).count()
    
    def get_resource_count(self, obj):
        return obj.resources.filter(is_enabled=True).count()
    
    def get_prompt_count(self, obj):
        return obj.prompts.filter(is_enabled=True).count()
    
    def validate(self, data):
        """Validate server configuration based on type."""
        server_type = data.get('server_type')
        
        if server_type == 'stdio':
            if not data.get('command'):
                raise serializers.ValidationError({
                    'command': 'Command is required for stdio servers'
                })
        elif server_type in ['sse', 'http']:
            if not data.get('url'):
                raise serializers.ValidationError({
                    'url': 'URL is required for SSE/HTTP servers'
                })
        
        return data


class MCPServerConfigListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing servers."""
    
    tool_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MCPServerConfig
        fields = [
            'id', 'name', 'server_type', 'is_active', 'connection_status',
            'tool_count', 'last_connected_at', 'created_at'
        ]
    
    def get_tool_count(self, obj):
        return obj.tools.filter(is_enabled=True).count()


class MCPToolSerializer(serializers.ModelSerializer):
    """Serializer for MCP Tools."""
    
    server_name = serializers.CharField(source='server_config.name', read_only=True)
    server_id = serializers.IntegerField(source='server_config.id', read_only=True)
    server_is_active = serializers.BooleanField(source='server_config.is_active', read_only=True)
    server_connection_status = serializers.CharField(source='server_config.connection_status', read_only=True)
    
    class Meta:
        model = MCPTool
        fields = [
            'id', 'server_id', 'server_name', 'server_is_active', 'server_connection_status',
            'tool_name', 'description', 'input_schema', 'is_enabled', 'usage_count',
            'last_used_at', 'average_execution_time', 'last_synced_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'usage_count', 'last_used_at', 'average_execution_time',
            'last_synced_at', 'created_at', 'updated_at'
        ]


class MCPResourceSerializer(serializers.ModelSerializer):
    """Serializer for MCP Resources."""
    
    server_name = serializers.CharField(source='server_config.name', read_only=True)
    server_id = serializers.IntegerField(source='server_config.id', read_only=True)
    server_is_active = serializers.BooleanField(source='server_config.is_active', read_only=True)
    server_connection_status = serializers.CharField(source='server_config.connection_status', read_only=True)
    
    class Meta:
        model = MCPResource
        fields = [
            'id', 'server_id', 'server_name', 'server_is_active', 'server_connection_status',
            'resource_uri', 'resource_name', 'description', 'resource_type', 'mime_type',
            'is_enabled', 'access_count', 'last_accessed_at', 'last_synced_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'access_count', 'last_accessed_at', 'last_synced_at',
            'created_at', 'updated_at'
        ]


class MCPPromptSerializer(serializers.ModelSerializer):
    """Serializer for MCP Prompts."""
    
    server_name = serializers.CharField(source='server_config.name', read_only=True)
    server_id = serializers.IntegerField(source='server_config.id', read_only=True)
    server_is_active = serializers.BooleanField(source='server_config.is_active', read_only=True)
    server_connection_status = serializers.CharField(source='server_config.connection_status', read_only=True)
    
    class Meta:
        model = MCPPrompt
        fields = [
            'id', 'server_id', 'server_name', 'server_is_active', 'server_connection_status',
            'prompt_name', 'description', 'prompt_template', 'arguments', 'is_enabled',
            'usage_count', 'last_used_at', 'last_synced_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'usage_count', 'last_used_at', 'last_synced_at',
            'created_at', 'updated_at'
        ]


class MCPExecutionLogSerializer(serializers.ModelSerializer):
    """Serializer for MCP Execution Logs."""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = MCPExecutionLog
        fields = [
            'id', 'user', 'user_username', 'tool', 'tool_name', 'server_name',
            'status', 'input_params', 'output_result', 'error_message',
            'started_at', 'completed_at', 'execution_time', 'chat_thread_id',
            'created_at'
        ]
        read_only_fields = ['user', 'created_at']


class MCPToolExecutionSerializer(serializers.Serializer):
    """Serializer for tool execution requests."""
    
    tool_id = serializers.IntegerField()
    arguments = serializers.JSONField(default=dict)
    chat_thread_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    def validate_tool_id(self, value):
        """Validate tool exists and is enabled."""
        try:
            tool = MCPTool.objects.get(id=value, is_enabled=True)
            # Check if server is active
            if not tool.server_config.is_active:
                raise serializers.ValidationError("Server is not active")
            return value
        except MCPTool.DoesNotExist:
            raise serializers.ValidationError("Tool not found or not enabled")


class MCPServerTestSerializer(serializers.Serializer):
    """Serializer for server connection testing."""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    server_info = serializers.JSONField(required=False)
    error = serializers.CharField(required=False)

