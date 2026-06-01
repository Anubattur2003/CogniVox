"""
Core URL configuration.
Matches FastAPI core and admin endpoints structure.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'config', views.SystemConfigurationViewSet, basename='systemconfiguration')
router.register(r'audit-logs', views.AuditLogViewSet, basename='auditlog')
router.register(r'api-usage', views.APIUsageStatsViewSet, basename='apiusagestats')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # System endpoints
    path('health/', views.health_check, name='health_check'),
    path('stats/', views.system_stats, name='system_stats'),
    path('cache/clear/', views.clear_cache, name='clear_cache'),
    path('config/<str:key>/', views.get_config, name='get_config'),
]