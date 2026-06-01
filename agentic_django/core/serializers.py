from rest_framework import serializers
from .models import SystemConfiguration, AuditLog, APIUsageStats
from authentication.models import User


class SystemConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for SystemConfiguration model"""
    
    class Meta:
        model = SystemConfiguration
        fields = [
            'id', 'key', 'value', 'description', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_key(self, value):
        """Ensure configuration key is unique"""
        if self.instance:
            # Update case - exclude current instance
            if SystemConfiguration.objects.filter(key=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("A configuration with this key already exists.")
        else:
            # Create case
            if SystemConfiguration.objects.filter(key=value).exists():
                raise serializers.ValidationError("A configuration with this key already exists.")
        return value

    def validate_key_format(self, value):
        """Validate key format (alphanumeric, underscores, dots)"""
        import re
        if not re.match(r'^[a-zA-Z0-9_.]+$', value):
            raise serializers.ValidationError(
                "Key can only contain letters, numbers, underscores, and dots."
            )
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_email', 'action', 'resource_type',
            'resource_id', 'details', 'ip_address', 'user_agent',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_action(self, value):
        """Validate action is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Action cannot be empty.")
        return value.strip()

    def validate_resource_type(self, value):
        """Validate resource type is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Resource type cannot be empty.")
        return value.strip()


class APIUsageStatsSerializer(serializers.ModelSerializer):
    """Serializer for APIUsageStats model"""
    
    class Meta:
        model = APIUsageStats
        fields = [
            'id', 'endpoint', 'method', 'status_code', 'response_time',
            'user_id', 'ip_address', 'user_agent', 'request_size',
            'response_size', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_endpoint(self, value):
        """Validate endpoint format"""
        if not value.startswith('/'):
            raise serializers.ValidationError("Endpoint must start with '/'.")
        return value

    def validate_method(self, value):
        """Validate HTTP method"""
        valid_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
        if value.upper() not in valid_methods:
            raise serializers.ValidationError(f"Invalid HTTP method. Must be one of: {valid_methods}")
        return value.upper()

    def validate_status_code(self, value):
        """Validate HTTP status code"""
        if not (100 <= value <= 599):
            raise serializers.ValidationError("Status code must be between 100 and 599.")
        return value

    def validate_response_time(self, value):
        """Validate response time is positive"""
        if value < 0:
            raise serializers.ValidationError("Response time cannot be negative.")
        return value


class AuditLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating audit log entries"""
    
    class Meta:
        model = AuditLog
        fields = [
            'action', 'resource_type', 'resource_id', 'details',
            'ip_address', 'user_agent'
        ]

    def create(self, validated_data):
        """Create audit log with current user"""
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.is_authenticated:
            validated_data['user'] = user
        return super().create(validated_data)


class SystemStatsSerializer(serializers.Serializer):
    """Serializer for system statistics"""
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_models = serializers.IntegerField()
    active_models = serializers.IntegerField()
    total_requests_today = serializers.IntegerField()
    total_requests_this_month = serializers.IntegerField()
    average_response_time = serializers.FloatField()
    most_used_endpoints = serializers.ListField(
        child=serializers.DictField()
    )


class ConfigurationUpdateSerializer(serializers.Serializer):
    """Serializer for bulk configuration updates"""
    configurations = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )

    def validate_configurations(self, value):
        """Validate configuration format"""
        for config in value:
            if 'key' not in config or 'value' not in config:
                raise serializers.ValidationError(
                    "Each configuration must have 'key' and 'value' fields."
                )
        return value


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check responses"""
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    version = serializers.CharField()
    database_status = serializers.CharField()
    cache_status = serializers.CharField(required=False)
    external_services = serializers.DictField(required=False)


class LogFilterSerializer(serializers.Serializer):
    """Serializer for filtering audit logs"""
    user_id = serializers.IntegerField(required=False)
    action = serializers.CharField(required=False, max_length=100)
    resource_type = serializers.CharField(required=False, max_length=100)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    ip_address = serializers.IPAddressField(required=False)

    def validate(self, attrs):
        """Validate date range"""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date.")
        
        return attrs