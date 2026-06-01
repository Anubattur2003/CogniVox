"""
Main URL configuration for agentic_django project.
Compatible with FastAPI endpoint structure.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# Import viewsets for router registration
from agentic_django.core.views import SystemConfigurationViewSet, AuditLogViewSet, APIUsageStatsViewSet
from chat.views import ChatThreadViewSet, ChatSubThreadViewSet

# Register ViewSets with the router
router = DefaultRouter()
router.register(r'admin/config', SystemConfigurationViewSet, basename='system-config')
router.register(r'admin/audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'admin/api-stats', APIUsageStatsViewSet, basename='api-stats')
# Chat endpoints are handled by chat.urls - removed duplicate registration

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),
    
    # API root - matches FastAPI structure
    path('api/', include([
        # Authentication endpoints - matches FastAPI /auth
        path('auth/', include('authentication.urls')),
        
        # Chat endpoints - matches FastAPI /chat  
        path('chat/', include('chat.urls')),
        
        # MCP endpoints - Model Context Protocol        
        path('mcp/', include('mcpserver.urls')),
        
        # Admin endpoints - matches FastAPI /admin
        path('admin/', include('agentic_django.core.urls')),
        
        # Core system endpoints
        path('system/', include('agentic_django.core.urls')),
    ])),
    
    # DRF router URLs
    path('api/', include(router.urls)),
    
    # JWT token endpoints
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Health check endpoint - matches FastAPI /health
    path('health/', include('agentic_django.core.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
# Custom error handlers - commented out since views don't exist
# handler404 = 'agentic_django.core.views.custom_404'
# handler500 = 'agentic_django.core.views.custom_500'
