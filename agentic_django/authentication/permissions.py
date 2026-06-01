"""
Custom permissions for Django REST Framework.
Matches FastAPI role-based access control system.
"""
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView
from django.contrib.auth.models import User
from core.models import UserRole
from typing import List, Union


class IsAuthenticated(permissions.BasePermission):
    """
    Custom authentication permission that matches FastAPI behavior.
    """
    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated)


class HasRole(permissions.BasePermission):
    """
    Permission class that checks if user has required role(s).
    Matches FastAPI check_roles functionality.
    """
    required_roles: List[UserRole] = []
    
    def __init__(self, roles: Union[UserRole, List[UserRole]]):
        if isinstance(roles, UserRole):
            self.required_roles = [roles]
        else:
            self.required_roles = roles
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get user role from the User model
        try:
            user_role = UserRole(request.user.role)
            return user_role in self.required_roles
        except (AttributeError, ValueError):
            return False


class IsAdmin(permissions.BasePermission):
    """
    Permission class for admin-only access.
    """
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            return request.user.role == UserRole.ADMIN.value
        except AttributeError:
            return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission class that allows access to owners or admins.
    """
    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        # Admin can access everything
        try:
            if request.user.role == UserRole.ADMIN.value:
                return True
        except AttributeError:
            pass
        
        # Owner can access their own objects
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class IsSubscribed(permissions.BasePermission):
    """
    Permission class that checks if user has active subscription.
    """
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has active subscription
        try:
            from core.models import UserSubscription
            subscription = UserSubscription.objects.filter(
                user=request.user,
                is_active=True
            ).first()
            return subscription is not None
        except Exception:
            return False


class HasModelAccess(permissions.BasePermission):
    """
    Permission class that checks if user has access to specific model.
    """
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get model_id from request
        model_id = None
        if hasattr(view, 'kwargs') and 'model_id' in view.kwargs:
            model_id = view.kwargs['model_id']
        elif request.data and 'model_id' in request.data:
            model_id = request.data['model_id']
        elif request.query_params and 'model_id' in request.query_params:
            model_id = request.query_params['model_id']
        
        if not model_id:
            return True  # Let the view handle model validation
        
        try:
            from core.models import UserModelRequest
            user_model = UserModelRequest.objects.filter(
                user=request.user,
                model_id=model_id
            ).first()
            return user_model is not None and user_model.requests_remaining > 0
        except Exception:
            return False


class RateLimitPermission(permissions.BasePermission):
    """
    Permission class that implements rate limiting.
    """
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Implement rate limiting logic here
        # This is a placeholder - you would implement actual rate limiting
        return True


def require_roles(roles: Union[UserRole, List[UserRole]]):
    """
    Decorator function that creates a permission class for specific roles.
    Matches FastAPI check_roles functionality.
    """
    class RolePermission(permissions.BasePermission):
        def has_permission(self, request: Request, view: APIView) -> bool:
            if not request.user or not request.user.is_authenticated:
                return False
            
            required_roles = roles if isinstance(roles, list) else [roles]
            try:
                user_role = UserRole(request.user.role)
                return user_role in required_roles
            except (AttributeError, ValueError):
                return False
    
    return RolePermission


# Permission classes for common role combinations
class AdminOnly(HasRole):
    def __init__(self):
        super().__init__(UserRole.ADMIN)


class UserOrAdmin(permissions.BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            user_role = UserRole(request.user.role)
            return user_role in [UserRole.USER, UserRole.ADMIN]
        except (AttributeError, ValueError):
            return False


class PremiumOrAdmin(permissions.BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            user_role = UserRole(request.user.role)
            return user_role in [UserRole.PREMIUM, UserRole.ADMIN]
        except (AttributeError, ValueError):
            return False