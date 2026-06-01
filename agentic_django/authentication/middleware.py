"""
Authentication middleware for Django.
Provides security features matching FastAPI implementation.
"""
import time
import logging
from typing import Callable, Optional
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .security import is_token_blacklisted, check_rate_limit
from core.models import AuditLog, APIUsageStats
from core.utils import get_client_ip, create_audit_log

logger = logging.getLogger(__name__)


class ProcessTimeMiddleware(MiddlewareMixin):
    """
    Middleware to add process time header to responses.
    Matches FastAPI process time middleware.
    """
    
    def process_request(self, request: HttpRequest) -> None:
        request.start_time = time.time()
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        if hasattr(request, 'start_time'):
            process_time = time.time() - request.start_time
            response['X-Process-Time'] = str(process_time)
        return response


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Custom JWT authentication middleware.
    Handles token validation and user authentication.
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()
        super().__init__(get_response)
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        # Skip authentication for certain paths
        skip_paths = [
            '/admin/',
            '/api/auth/token/',
            '/api/auth/register/',
            '/health/',
            '/docs/',
            '/redoc/',
            '/openapi.json'
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Extract token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            request.user = AnonymousUser()
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            # Validate token using JWT authentication
            validated_token = self.jwt_auth.get_validated_token(token)
            user = self.jwt_auth.get_user(validated_token)
            
            # Check if user tokens are blacklisted
            if is_token_blacklisted(user.id):
                return JsonResponse(
                    {'error': 'Token has been revoked'},
                    status=401
                )
            
            request.user = user
            request.token = validated_token
            
        except (InvalidToken, TokenError) as e:
            return JsonResponse(
                {'error': 'Invalid or expired token'},
                status=401
            )
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return JsonResponse(
                {'error': 'Authentication failed'},
                status=401
            )
        
        return None


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware.
    Implements rate limiting per user and endpoint.
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        # Skip rate limiting for certain paths
        skip_paths = ['/admin/', '/health/', '/docs/', '/redoc/']
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Get user ID (use IP for anonymous users)
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
        else:
            user_id = f"ip_{get_client_ip(request)}"
        
        # Define rate limits per endpoint
        rate_limits = {
            '/api/auth/': {'limit': 10, 'window': 300},  # 10 requests per 5 minutes
            '/api/chat/submit/': {'limit': 100, 'window': 3600},  # 100 requests per hour
            '/api/models/': {'limit': 50, 'window': 3600},  # 50 requests per hour
            'default': {'limit': 1000, 'window': 3600}  # 1000 requests per hour
        }
        
        # Find matching rate limit
        rate_limit = rate_limits.get('default')
        for path, limit_config in rate_limits.items():
            if request.path.startswith(path):
                rate_limit = limit_config
                break
        
        # Check rate limit
        action = f"{request.method}_{request.path}"
        if not check_rate_limit(
            user_id, 
            action, 
            rate_limit['limit'], 
            rate_limit['window']
        ):
            return JsonResponse(
                {
                    'error': 'Rate limit exceeded',
                    'detail': f"Maximum {rate_limit['limit']} requests per {rate_limit['window']} seconds"
                },
                status=429
            )
        
        return None


class AuditLogMiddleware(MiddlewareMixin):
    """
    Audit logging middleware.
    Logs API requests and responses for security and monitoring.
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request: HttpRequest) -> None:
        # Store request data for logging
        request.audit_data = {
            'method': request.method,
            'path': request.path,
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'timestamp': time.time()
        }
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        # Skip logging for certain paths
        skip_paths = ['/admin/', '/static/', '/media/']
        if any(request.path.startswith(path) for path in skip_paths):
            return response
        
        if hasattr(request, 'audit_data'):
            try:
                # Create audit log entry using correct function signature
                user = request.user if hasattr(request, 'user') else None
                action = f"{request.audit_data['method']} {request.audit_data['path']}"
                
                create_audit_log(
                    user=user,
                    action=action,
                    resource_type='api_request',
                    details={
                        'status_code': response.status_code,
                        'response_time': time.time() - request.audit_data['timestamp']
                    },
                    request=request
                )
                
            except Exception as e:
                logger.error(f"Audit logging error: {str(e)}")
        
        return response


class APIUsageStatsMiddleware(MiddlewareMixin):
    """
    API usage statistics middleware.
    Tracks API usage for analytics and monitoring.
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        # Skip stats for certain paths
        skip_paths = ['/admin/', '/static/', '/media/', '/health/']
        if any(request.path.startswith(path) for path in skip_paths):
            return response
        
        try:
            # Update API usage stats using correct function signature
            from core.utils import record_api_usage
            start_time = getattr(request, 'start_time', time.time())
            record_api_usage(request, response, start_time)
            
        except Exception as e:
            logger.error(f"API usage stats error: {str(e)}")
        
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Security headers middleware.
    Adds security headers to responses.
    """
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Add HSTS header for HTTPS
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


class CORSMiddleware(MiddlewareMixin):
    """
    Custom CORS middleware.
    Handles CORS headers for API requests.
    """
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        # Get allowed origins from settings
        allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', ['http://localhost:3000'])
        origin = request.META.get('HTTP_ORIGIN')
        
        if origin in allowed_origins:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Accept, Authorization, Content-Type, X-Requested-With'
            response['Access-Control-Max-Age'] = '86400'
        
        return response
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        # Handle preflight OPTIONS requests
        if request.method == 'OPTIONS':
            response = HttpResponse()
            origin = request.META.get('HTTP_ORIGIN')
            allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', ['http://localhost:3000'])
            
            if origin in allowed_origins:
                response['Access-Control-Allow-Origin'] = origin
                response['Access-Control-Allow-Credentials'] = 'true'
                response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
                response['Access-Control-Allow-Headers'] = 'Accept, Authorization, Content-Type, X-Requested-With'
                response['Access-Control-Max-Age'] = '86400'
            
            return response
        
        return None


class MaintenanceModeMiddleware(MiddlewareMixin):
    """
    Maintenance mode middleware.
    Returns maintenance response when system is in maintenance mode.
    """
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        # Check if maintenance mode is enabled
        maintenance_mode = cache.get('maintenance_mode', False)
        
        if maintenance_mode:
            # Allow admin access during maintenance
            if request.path.startswith('/admin/'):
                return None
            
            # Allow health checks
            if request.path.startswith('/health/'):
                return None
            
            return JsonResponse(
                {
                    'error': 'System is currently under maintenance',
                    'detail': 'Please try again later'
                },
                status=503
            )
        
        return None