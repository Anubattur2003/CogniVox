from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    USER = 'user', 'User'


class SubscriptionPlan(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()
    max_requests = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_plans'

    def __str__(self):
        return self.name


class User(AbstractUser):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.USER
    )
    subscription_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Use username for authentication
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email

    @property
    def is_subscription_active(self):
        """Check if user's subscription is currently active"""
        if not self.subscription_end_date:
            return False
        return timezone.now() <= self.subscription_end_date

    def get_remaining_requests(self):
        """Get remaining requests for current subscription period"""
        if not self.subscription_plan:
            return 0
        
        # Simplified - no tracking for now
        return self.subscription_plan.max_requests
