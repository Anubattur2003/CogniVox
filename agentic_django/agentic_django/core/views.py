from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.db import transaction, connection
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
import logging
import requests
from datetime import datetime, timedelta

from core.models import SystemConfiguration, AuditLog, APIUsageStats
from core.serializers import SystemConfigurationSerializer, AuditLogSerializer, APIUsageStatsSerializer
from core.utils import create_audit_log, record_api_usage, get_client_ip

User = get_user_model()
logger = logging.getLogger(__name__)


class SystemConfigurationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing system configuration.
    Admin only access.
    """
    queryset = SystemConfiguration.objects.all()
    serializer_class = SystemConfigurationSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['post'])
    def update_config(self, request):
        """
        Update system configuration values.
        """
        serializer = ConfigUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                config_updates = serializer.validated_data['config_updates']
                updated_configs = []

                for key, value in config_updates.items():
                    config, created = SystemConfiguration.objects.get_or_create(
                        key=key,
                        defaults={'value': str(value), 'description': f'Auto-created config for {key}'}
                    )
                    
                    if not created:
                        config.value = str(value)
                        config.save()
                    
                    updated_configs.append({
                        'key': key,
                        'value': value,
                        'created': created
                    })

                # Create audit log
                create_audit_log(
                    user=request.user,
                    action='CONFIG_UPDATE',
                    resource_type='SystemConfiguration',
                    resource_id='bulk_update',
                    details=f'Updated {len(updated_configs)} configuration values',
                    ip_address=get_client_ip(request)
                )

                # Clear cache to ensure fresh config values
                cache.clear()

                return Response({
                    'message': 'Configuration updated successfully',
                    'updated_configs': updated_configs
                })

        except Exception as e:
            logger.error(f"Error in update_config: {e}")
            return Response(
                {'detail': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs.
    Admin only access.
    """
    queryset = AuditLog.objects.all().order_by('-created_at')
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        """Filter audit logs based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by resource type
        resource_type = self.request.query_params.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__lte=end_date)
            except ValueError:
                pass
        
        return queryset

    @action(detail=False, methods=['post'])
    def filter_logs(self, request):
        """
        Advanced filtering of audit logs.
        """
        serializer = LogFilterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            filters = serializer.validated_data
            queryset = AuditLog.objects.all()

            # Apply filters
            if filters.get('user_ids'):
                queryset = queryset.filter(user_id__in=filters['user_ids'])
            
            if filters.get('actions'):
                queryset = queryset.filter(action__in=filters['actions'])
            
            if filters.get('resource_types'):
                queryset = queryset.filter(resource_type__in=filters['resource_types'])
            
            if filters.get('start_date'):
                queryset = queryset.filter(timestamp__gte=filters['start_date'])
            
            if filters.get('end_date'):
                queryset = queryset.filter(timestamp__lte=filters['end_date'])

            # Order by timestamp
            queryset = queryset.order_by('-timestamp')

            # Paginate results
            page_size = filters.get('page_size', 50)
            page = filters.get('page', 1)
            start = (page - 1) * page_size
            end = start + page_size

            logs = queryset[start:end]
            serializer = AuditLogSerializer(logs, many=True)

            return Response({
                'logs': serializer.data,
                'total_count': queryset.count(),
                'page': page,
                'page_size': page_size
            })

        except Exception as e:
            logger.error(f"Error in filter_logs: {e}")
            return Response(
                {'detail': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class APIUsageStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing API usage statistics.
    Admin only access.
    """
    queryset = APIUsageStats.objects.all().order_by('-date')
    serializer_class = APIUsageStatsSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        """Filter API usage stats based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by endpoint
        endpoint = self.request.query_params.get('endpoint')
        if endpoint:
            queryset = queryset.filter(endpoint=endpoint)
        
        # Filter by method
        method = self.request.query_params.get('method')
        if method:
            queryset = queryset.filter(method=method.upper())
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date).date()
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date).date()
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                pass
        
        return queryset


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_check(request):
    """
    Comprehensive health check endpoint.
    Compatible with FastAPI /health endpoint.
    """
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'version': getattr(settings, 'VERSION', '1.0.0')
        }

        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_data['services']['database'] = 'healthy'
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_data['services']['database'] = 'unhealthy'
            health_data['status'] = 'unhealthy'

        # Check cache connection
        try:
            cache.set('health_check', 'test', 10)
            cache.get('health_check')
            health_data['services']['cache'] = 'healthy'
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            health_data['services']['cache'] = 'unhealthy'

        # Check Ollama connection
        ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                health_data['services']['ollama'] = 'healthy'
            else:
                health_data['services']['ollama'] = 'unhealthy'
                health_data['status'] = 'degraded'
        except requests.RequestException as e:
            logger.error(f"Ollama health check failed: {e}")
            health_data['services']['ollama'] = 'unhealthy'
            health_data['status'] = 'degraded'

        # Check Memory service connection
        memory_url = getattr(settings, 'MEMORY_SERVICE_URL', 'http://localhost:8001')
        try:
            response = requests.get(f"{memory_url}/health", timeout=5)
            if response.status_code == 200:
                health_data['services']['memory_service'] = 'healthy'
            else:
                health_data['services']['memory_service'] = 'unhealthy'
                health_data['status'] = 'degraded'
        except requests.RequestException as e:
            logger.error(f"Memory service health check failed: {e}")
            health_data['services']['memory_service'] = 'unhealthy'
            health_data['status'] = 'degraded'

        # Add system stats
        health_data['stats'] = {
            'total_users': User.objects.count(),
            'active_sessions': cache.get('active_sessions', 0),
            'uptime': getattr(settings, 'START_TIME', datetime.now()).isoformat()
        }

        # Record API usage
        record_api_usage(
            endpoint='/health/',
            method='GET',
            user=request.user if request.user.is_authenticated else None,
            success=True
        )

        return Response(health_data)

    except Exception as e:
        logger.error(f"Error in health_check: {e}")
        return Response(
            {
                'status': 'unhealthy',
                'error': 'Health check failed',
                'timestamp': datetime.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def system_stats(request):
    """
    Get comprehensive system statistics.
    Admin only access.
    """
    try:
        # Calculate date ranges
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # User statistics
        total_users = User.objects.count()
        active_users_week = User.objects.filter(last_login__gte=week_ago).count()
        new_users_month = User.objects.filter(date_joined__gte=month_ago).count()

        # API usage statistics
        api_stats_today = APIUsageStats.objects.filter(date=today)
        total_requests_today = sum(api_stats_today.values_list('total_requests', flat=True))
        successful_requests_today = sum(api_stats_today.values_list('successful_requests', flat=True))

        # Audit log statistics
        audit_logs_week = AuditLog.objects.filter(timestamp__gte=week_ago).count()

        # System configuration count
        config_count = SystemConfiguration.objects.count()

        stats = {
            'users': {
                'total': total_users,
                'active_last_week': active_users_week,
                'new_last_month': new_users_month
            },
            'api_usage': {
                'requests_today': total_requests_today,
                'successful_requests_today': successful_requests_today,
                'success_rate_today': (successful_requests_today / total_requests_today * 100) if total_requests_today > 0 else 0
            },
            'audit_logs': {
                'logs_last_week': audit_logs_week
            },
            'system': {
                'configuration_count': config_count,
                'database_status': 'healthy',  # We got here, so DB is working
                'timestamp': datetime.now().isoformat()
            }
        }

        # Record API usage
        record_api_usage(
            endpoint='/system/stats/',
            method='GET',
            user=request.user,
            success=True
        )

        return Response(stats)

    except Exception as e:
        logger.error(f"Error in system_stats: {e}")
        
        # Record API usage failure
        record_api_usage(
            endpoint='/system/stats/',
            method='GET',
            user=request.user,
            success=False
        )
        
        return Response(
            {'detail': 'Failed to get system statistics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def clear_cache(request):
    """
    Clear application cache.
    Admin only access.
    """
    try:
        cache.clear()
        
        # Create audit log
        create_audit_log(
            user=request.user,
            action='CACHE_CLEARED',
            resource_type='System',
            resource_id='cache',
            details='Application cache cleared',
            ip_address=get_client_ip(request)
        )

        return Response({'message': 'Cache cleared successfully'})

    except Exception as e:
        logger.error(f"Error in clear_cache: {e}")
        return Response(
            {'detail': 'Failed to clear cache'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_config(request, key=None):
    """
    Get system configuration value(s).
    """
    try:
        if key:
            # Get specific config
            try:
                config = SystemConfiguration.objects.get(key=key)
                return Response({
                    'key': config.key,
                    'value': config.value,
                    'description': config.description
                })
            except SystemConfiguration.DoesNotExist:
                return Response(
                    {'detail': f'Configuration key "{key}" not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Get all configs (admin only)
            if not request.user.is_staff:
                return Response(
                    {'detail': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            configs = SystemConfiguration.objects.all()
            serializer = SystemConfigurationSerializer(configs, many=True)
            return Response(serializer.data)

    except Exception as e:
        logger.error(f"Error in get_config: {e}")
        return Response(
            {'detail': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )