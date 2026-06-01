"""
API views for MCP management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
import logging

from .models import (
    MCPServerConfig, MCPTool, MCPResource, MCPPrompt, MCPExecutionLog
)
from .serializers import (
    MCPServerConfigSerializer, MCPServerConfigListSerializer,
    MCPToolSerializer, MCPResourceSerializer, MCPPromptSerializer,
    MCPExecutionLogSerializer, MCPToolExecutionSerializer,
    MCPServerTestSerializer
)

logger = logging.getLogger(__name__)


class MCPServerConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing MCP server configurations.
    
    Provides CRUD operations and additional actions for testing and syncing servers.
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MCPServerConfigListSerializer
        return MCPServerConfigSerializer
    
    def get_queryset(self):
        """Return only servers belonging to the current user."""
        return MCPServerConfig.objects.filter(user=self.request.user).prefetch_related(
            'tools', 'resources', 'prompts'
        )
    
    def perform_create(self, serializer):
        """
        Automatically set the user when creating a server.
        Also auto-connect and sync the server.
        """
        server = serializer.save(user=self.request.user)
        
        # Auto-connect and sync the new server
        try:
            from .mcp_client import MCPClientManager
            
            logger.info(f"Auto-connecting new MCP server: {server.name}")
            client_manager = MCPClientManager()
            
            # Test connection first
            test_result = client_manager.test_connection(server)
            
            if test_result['success']:
                logger.info(f"Auto-connection successful for {server.name}")
                server.mark_connected()
                
                # Auto-sync tools, resources, and prompts
                try:
                    logger.info(f"Auto-syncing MCP server: {server.name}")
                    sync_result = client_manager.sync_server(server, self.request.user)
                    logger.info(f"Auto-sync complete: {sync_result.get('tools_count', 0)} tools, "
                              f"{sync_result.get('resources_count', 0)} resources, "
                              f"{sync_result.get('prompts_count', 0)} prompts")
                except Exception as sync_error:
                    logger.warning(f"Auto-sync failed for {server.name}: {str(sync_error)}")
                    # Don't fail the creation, user can manually sync later
            else:
                logger.warning(f"Auto-connection failed for {server.name}: {test_result.get('error')}")
                server.mark_disconnected(test_result.get('error'))
                # Don't fail the creation, user can manually connect later
                
        except Exception as e:
            logger.error(f"Error during auto-connect/sync: {str(e)}", exc_info=True)
            # Don't fail the creation, user can manually connect later
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """
        Test connection to an MCP server.
        
        This will attempt to connect to the server and verify it's accessible.
        """
        server = self.get_object()
        
        try:
            # Import MCP client here to avoid circular imports
            from .mcp_client import MCPClientManager
            
            client_manager = MCPClientManager()
            result = client_manager.test_connection(server)
            
            if result['success']:
                server.mark_connected()
            else:
                server.mark_disconnected(result.get('error'))
            
            serializer = MCPServerTestSerializer(result)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error testing MCP server connection: {str(e)}")
            server.mark_disconnected(str(e))
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """
        Sync tools, resources, and prompts from the MCP server.
        
        This will discover all available tools/resources/prompts and update the database.
        """
        server = self.get_object()
        
        try:
            from .mcp_client import MCPClientManager
            
            client_manager = MCPClientManager()
            result = client_manager.sync_server(server, request.user)
            
            return Response({
                'success': True,
                'message': 'Server synced successfully',
                'tools_synced': result.get('tools_count', 0),
                'resources_synced': result.get('resources_count', 0),
                'prompts_synced': result.get('prompts_count', 0),
            })
            
        except Exception as e:
            logger.error(f"Error syncing MCP server: {str(e)}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def disconnect(self, request, pk=None):
        """Disconnect from an MCP server."""
        server = self.get_object()
        
        try:
            from .mcp_client import MCPClientManager
            
            client_manager = MCPClientManager()
            client_manager.disconnect_server(server.id)
            server.mark_disconnected()
            
            return Response({'success': True, 'message': 'Server disconnected'})
            
        except Exception as e:
            logger.error(f"Error disconnecting MCP server: {str(e)}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle the active status of an MCP server."""
        server = self.get_object()
        
        try:
            # Toggle the is_active flag
            server.is_active = not server.is_active
            server.save(update_fields=['is_active'])
            
            status_text = "enabled" if server.is_active else "disabled"
            logger.info(f"MCP server {server.name} {status_text}")
            
            # If enabling and auto_connect is true, connect and sync
            if server.is_active and server.auto_connect:
                from .mcp_client import MCPClientManager
                
                logger.info(f"Auto-connecting MCP server: {server.name}")
                client_manager = MCPClientManager()
                
                # Test connection
                test_result = client_manager.test_connection(server)
                
                if test_result['success']:
                    logger.info(f"Auto-connection successful for {server.name}")
                    server.mark_connected()
                    
                    # Auto-sync
                    try:
                        sync_result = client_manager.sync_server(server, request.user)
                        logger.info(f"Auto-sync complete for {server.name}")
                    except Exception as sync_error:
                        logger.warning(f"Auto-sync failed: {str(sync_error)}")
                else:
                    logger.warning(f"Auto-connection failed: {test_result.get('error')}")
                    server.mark_disconnected(test_result.get('error'))
            
            # If disabling, disconnect
            elif not server.is_active:
                from .mcp_client import MCPClientManager
                client_manager = MCPClientManager()
                client_manager.disconnect_server(server.id)
                server.mark_disconnected()
            
            serializer = self.get_serializer(server)
            return Response({
                'success': True,
                'message': f'Server {status_text}',
                'server': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error toggling MCP server: {str(e)}", exc_info=True)
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MCPToolViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing MCP tools.
    
    Tools are discovered from servers and cannot be directly created/updated.
    """
    serializer_class = MCPToolSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return tools from servers belonging to the current user."""
        queryset = MCPTool.objects.filter(
            server_config__user=self.request.user
        ).select_related('server_config')
        
        # CRITICAL: Only return tools from active and connected servers
        initial_count = queryset.count()
        queryset = queryset.filter(
            server_config__is_active=True,
            server_config__connection_status='connected'
        )
        filtered_count = queryset.count()
        if initial_count > filtered_count:
            logger.info(f"MCP Tools: Filtered {initial_count - filtered_count} tools from inactive/disconnected servers. Returning {filtered_count} tools from active/connected servers.")
        
        # Filter by server if specified
        server_id = self.request.query_params.get('server_id')
        if server_id:
            queryset = queryset.filter(server_config_id=server_id)
        
        # Filter by enabled status
        is_enabled = self.request.query_params.get('is_enabled')
        if is_enabled is not None:
            queryset = queryset.filter(is_enabled=is_enabled.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        Execute an MCP tool.
        
        This will run the tool with the provided arguments and return the result.
        """
        tool = self.get_object()
        
        # CRITICAL: Validate server is active and connected before execution
        if not tool.server_config.is_active:
            return Response(
                {'success': False, 'error': f'Server "{tool.server_config.name}" is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if tool.server_config.connection_status != 'connected':
            return Response(
                {'success': False, 'error': f'Server "{tool.server_config.name}" is not connected (status: {tool.server_config.connection_status})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = MCPToolExecutionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if server requires approval
        if tool.server_config.require_approval:
            exec_log = MCPExecutionLog.objects.create(
                user=request.user,
                tool=tool,
                tool_name=tool.tool_name,
                server_name=tool.server_config.name,
                input_params=serializer.validated_data['arguments'],
                chat_thread_id=serializer.validated_data.get('chat_thread_id'),
                status='pending'
            )
            return Response({
                'success': True,
                'status': 'pending',
                'message': 'Tool execution requires user approval.',
                'execution_id': exec_log.id
            }, status=status.HTTP_202_ACCEPTED)
        
        try:
            from .mcp_client import MCPClientManager
            import time
            
            # Create execution log
            exec_log = MCPExecutionLog.objects.create(
                user=request.user,
                tool=tool,
                tool_name=tool.tool_name,
                server_name=tool.server_config.name,
                input_params=serializer.validated_data['arguments'],
                chat_thread_id=serializer.validated_data.get('chat_thread_id'),
                status='running'
            )
            
            start_time = time.time()
            
            logger.info("="*80)
            logger.info("🔧 MCP TOOL EXECUTION REQUEST")
            logger.info(f"   Tool: {tool.tool_name} (ID: {tool.id})") 
            logger.info(f"   Server: {tool.server_config.name} (ID: {tool.server_config.id})")
            logger.info(f"   User: {request.user.username} (ID: {request.user.id})")
            logger.info(f"   Arguments: {serializer.validated_data['arguments']}")
            logger.info("="*80)
            
            # Execute tool
            client_manager = MCPClientManager()
            result = client_manager.execute_tool(
                tool.server_config,
                tool.tool_name,
                serializer.validated_data['arguments']
            )
            
            execution_time = time.time() - start_time
            
            logger.info("="*80)
            logger.info("✅ MCP TOOL EXECUTION COMPLETE")
            logger.info(f"   Tool: {tool.tool_name}")
            logger.info(f"   Execution Time: {execution_time:.3f}s")
            logger.info(f"   Result: {result}")
            logger.info("="*80)
            
            # Update execution log
            exec_log.mark_success(result, execution_time)
            
            # Update tool usage stats
            tool.record_usage(execution_time)
            
            return Response({
                'success': True,
                'result': result,
                'execution_time': execution_time,
                'execution_id': exec_log.id
            })
            
        except Exception as e:
            logger.error(f"Error executing MCP tool: {str(e)}")
            exec_log.mark_error(str(e))
            
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['patch'])
    def toggle(self, request, pk=None):
        """Toggle tool enabled status."""
        tool = self.get_object()
        tool.is_enabled = not tool.is_enabled
        tool.save(update_fields=['is_enabled'])
        
        return Response({
            'success': True,
            'is_enabled': tool.is_enabled
        })


class MCPResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing MCP resources.
    
    Resources are discovered from servers and cannot be directly created/updated.
    """
    serializer_class = MCPResourceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return resources from servers belonging to the current user."""
        queryset = MCPResource.objects.filter(
            server_config__user=self.request.user
        ).select_related('server_config')
        
        # CRITICAL: Only return resources from active and connected servers
        initial_count = queryset.count()
        queryset = queryset.filter(
            server_config__is_active=True,
            server_config__connection_status='connected'
        )
        filtered_count = queryset.count()
        if initial_count > filtered_count:
            logger.info(f"MCP Resources: Filtered {initial_count - filtered_count} resources from inactive/disconnected servers. Returning {filtered_count} resources from active/connected servers.")
        
        # Filter by server if specified
        server_id = self.request.query_params.get('server_id')
        if server_id:
            queryset = queryset.filter(server_config_id=server_id)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def read(self, request, pk=None):
        """
        Read the content of an MCP resource.
        """
        resource = self.get_object()
        
        # CRITICAL: Validate server is active and connected before reading
        if not resource.server_config.is_active:
            return Response(
                {'success': False, 'error': f'Server "{resource.server_config.name}" is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if resource.server_config.connection_status != 'connected':
            return Response(
                {'success': False, 'error': f'Server "{resource.server_config.name}" is not connected (status: {resource.server_config.connection_status})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from .mcp_client import MCPClientManager
            
            client_manager = MCPClientManager()
            content = client_manager.read_resource(
                resource.server_config,
                resource.resource_uri
            )
            
            # Record access
            resource.record_access()
            
            return Response({
                'success': True,
                'content': content,
                'resource_uri': resource.resource_uri,
                'mime_type': resource.mime_type
            })
            
        except Exception as e:
            logger.error(f"Error reading MCP resource: {str(e)}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MCPPromptViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing MCP prompts.
    
    Prompts are discovered from servers and cannot be directly created/updated.
    """
    serializer_class = MCPPromptSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return prompts from servers belonging to the current user."""
        queryset = MCPPrompt.objects.filter(
            server_config__user=self.request.user
        ).select_related('server_config')
        
        # CRITICAL: Only return prompts from active and connected servers
        initial_count = queryset.count()
        queryset = queryset.filter(
            server_config__is_active=True,
            server_config__connection_status='connected'
        )
        filtered_count = queryset.count()
        if initial_count > filtered_count:
            logger.info(f"MCP Prompts: Filtered {initial_count - filtered_count} prompts from inactive/disconnected servers. Returning {filtered_count} prompts from active/connected servers.")
        
        # Filter by server if specified
        server_id = self.request.query_params.get('server_id')
        if server_id:
            queryset = queryset.filter(server_config_id=server_id)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def render(self, request, pk=None):
        """
        Render a prompt with the provided arguments.
        """
        prompt = self.get_object()
        
        # CRITICAL: Validate server is active and connected before rendering
        if not prompt.server_config.is_active:
            return Response(
                {'success': False, 'error': f'Server "{prompt.server_config.name}" is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if prompt.server_config.connection_status != 'connected':
            return Response(
                {'success': False, 'error': f'Server "{prompt.server_config.name}" is not connected (status: {prompt.server_config.connection_status})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        arguments = request.data.get('arguments', {})
        
        try:
            from .mcp_client import MCPClientManager
            
            client_manager = MCPClientManager()
            rendered = client_manager.render_prompt(
                prompt.server_config,
                prompt.prompt_name,
                arguments
            )
            
            # Record usage
            prompt.record_usage()
            
            return Response({
                'success': True,
                'rendered_prompt': rendered
            })
            
        except Exception as e:
            logger.error(f"Error rendering MCP prompt: {str(e)}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MCPExecutionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing MCP execution logs.
    
    Provides history of tool executions for debugging and auditing.
    """
    serializer_class = MCPExecutionLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return execution logs for the current user."""
        queryset = MCPExecutionLog.objects.filter(
            user=self.request.user
        ).select_related('user', 'tool')
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by tool
        tool_id = self.request.query_params.get('tool_id')
        if tool_id:
            queryset = queryset.filter(tool_id=tool_id)
        
        # Filter by chat thread
        chat_thread_id = self.request.query_params.get('chat_thread_id')
        if chat_thread_id:
            queryset = queryset.filter(chat_thread_id=chat_thread_id)
        
        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve and execute a pending MCP tool execution.
        """
        exec_log = self.get_object()
        
        if exec_log.status != 'pending':
            return Response(
                {'success': False, 'error': f'Execution log is not in pending status (current status: {exec_log.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        tool = exec_log.tool
        if not tool:
            return Response(
                {'success': False, 'error': 'Tool associated with this execution log no longer exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        server_config = tool.server_config
        if not server_config.is_active:
            return Response(
                {'success': False, 'error': f'Server "{server_config.name}" is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if server_config.connection_status != 'connected':
            return Response(
                {'success': False, 'error': f'Server "{server_config.name}" is not connected (status: {server_config.connection_status})'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            from .mcp_client import MCPClientManager
            import time
            
            # Update execution log to running
            exec_log.mark_running()
            
            start_time = time.time()
            
            logger.info("="*80)
            logger.info("🔧 APPROVED MCP TOOL EXECUTION REQUEST")
            logger.info(f"   Tool: {tool.tool_name} (ID: {tool.id})") 
            logger.info(f"   Server: {server_config.name} (ID: {server_config.id})")
            logger.info(f"   User: {request.user.username} (ID: {request.user.id})")
            logger.info(f"   Arguments: {exec_log.input_params}")
            logger.info("="*80)
            
            # Execute tool
            client_manager = MCPClientManager()
            result = client_manager.execute_tool(
                server_config,
                tool.tool_name,
                exec_log.input_params
            )
            
            execution_time = time.time() - start_time
            
            logger.info("="*80)
            logger.info("✅ APPROVED MCP TOOL EXECUTION COMPLETE")
            logger.info(f"   Tool: {tool.tool_name}")
            logger.info(f"   Execution Time: {execution_time:.3f}s")
            logger.info(f"   Result: {result}")
            logger.info("="*80)
            
            # Update execution log
            exec_log.mark_success(result, execution_time)
            
            # Update tool usage stats
            tool.record_usage(execution_time)
            
            return Response({
                'success': True,
                'status': 'success',
                'result': result,
                'execution_time': execution_time,
                'execution_id': exec_log.id
            })
            
        except Exception as e:
            logger.error(f"Error executing approved MCP tool: {str(e)}")
            exec_log.mark_error(str(e))
            
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a pending MCP tool execution.
        """
        exec_log = self.get_object()
        
        if exec_log.status != 'pending':
            return Response(
                {'success': False, 'error': f'Execution log is not in pending status (current status: {exec_log.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        from django.utils import timezone
        exec_log.status = 'cancelled'
        exec_log.error_message = 'Rejected by user'
        exec_log.completed_at = timezone.now()
        exec_log.save(update_fields=['status', 'error_message', 'completed_at'])
        
        return Response({
            'success': True,
            'status': 'cancelled',
            'message': 'Execution request rejected by user.',
            'execution_id': exec_log.id
        })

