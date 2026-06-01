"""
URL routing for MCP API endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for viewsets
router = DefaultRouter()
router.register(r'servers', views.MCPServerConfigViewSet, basename='mcp-server')
router.register(r'tools', views.MCPToolViewSet, basename='mcp-tool')
router.register(r'resources', views.MCPResourceViewSet, basename='mcp-resource')
router.register(r'prompts', views.MCPPromptViewSet, basename='mcp-prompt')
router.register(r'logs', views.MCPExecutionLogViewSet, basename='mcp-log')

urlpatterns = [
    path('', include(router.urls)),
]

