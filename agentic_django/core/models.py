from django.db import models
from django.utils import timezone


class SystemConfiguration(models.Model):
    """Model for storing system-wide configuration settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_configurations'

    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."


class AuditLog(models.Model):
    """Model for tracking system activities and changes"""
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('api_call', 'API Call'),
    ]

    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    resource_type = models.CharField(max_length=50)  # e.g., 'user', 'model', 'thread'
    resource_id = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']

    def __str__(self):
        user_info = f"by {self.user.email}" if self.user else "by Anonymous"
        return f"{self.action_type.title()} {self.resource_type} {user_info}"


class APIUsageStats(models.Model):
    """Model for tracking API usage statistics"""
    date = models.DateField()
    endpoint = models.CharField(max_length=100)
    method = models.CharField(max_length=10)  # GET, POST, PUT, DELETE
    total_requests = models.IntegerField(default=0)
    successful_requests = models.IntegerField(default=0)
    failed_requests = models.IntegerField(default=0)
    avg_response_time = models.FloatField(null=True, blank=True)
    total_tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'api_usage_stats'
        unique_together = ['date', 'endpoint', 'method']
        ordering = ['-date']

    def __str__(self):
        return f"{self.endpoint} ({self.method}) - {self.date}"
