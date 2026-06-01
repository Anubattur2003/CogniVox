"""
MCP Client Manager using FastMCP.

This module handles communication with MCP servers (stdio, SSE, HTTP).
Based on FastMCP 2.0 from https://gofastmcp.com/
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from fastmcp import Client as FastMCPClient
from fastmcp.client.transports import StdioTransport
from mcp.shared.exceptions import McpError
import httpx
from django.utils import timezone
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class MCPClientManager:
    """
    Manager for MCP client connections.
    
    Handles connection lifecycle for multiple MCP servers and provides
    methods for discovering and executing tools, reading resources, and
    rendering prompts.
    """
    
    def __init__(self):
        self.active_clients: Dict[int, FastMCPClient] = {}
        self.client_loop = None
    
    def _get_event_loop(self):
        """Get or create an event loop for async operations."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    
    def _create_client(self, server_config) -> FastMCPClient:
        """
        Create a FastMCP client based on server configuration.
        
        FastMCP 2.0 expects a transport dict with the server configuration.
        See: https://gofastmcp.com/getting-started/welcome
        
        Args:
            server_config: MCPServerConfig model instance
            
        Returns:
            FastMCPClient instance
        """
        try:
            config = server_config.get_connection_config()
            timeout = config.get('timeout', 30)
            
            logger.info(f"Creating MCP client for server: {server_config.name}")
            logger.info(f"Server type: {config['type']}")
            logger.info(f"Full config: {config}")
            
            if config['type'] == 'stdio':
                # Validate stdio configuration
                if not config.get('command'):
                    raise ValueError("stdio server requires a 'command' to be configured")
                
                # Parse command and args following MCPJam Inspector approach
                # MCPJam format: {"command": "npx", "args": ["@playwright/mcp@latest"]}
                # Also supports: {"command": "npx -y @playwright/mcp@latest", "args": []}
                command_str = config['command'].strip()
                
                # Get args list, ensuring it's a list
                args_raw = config.get('args')
                if args_raw is None:
                    args_list = []
                elif isinstance(args_raw, list):
                    args_list = args_raw
                else:
                    # Convert to list if it's not already
                    args_list = [str(args_raw)]
                
                # If args is empty but command has spaces, split command into command + args
                # This handles cases where command is "npx -y @playwright/mcp@latest" with empty args
                # Matching MCPJam Inspector's flexible input handling
                if not args_list and ' ' in command_str:
                    parts = command_str.split()
                    command = parts[0]
                    args_list = parts[1:]
                    logger.info(f"Split command '{command_str}' into command='{command}' and args={args_list}")
                else:
                    command = command_str
                
                # Ensure args_list is a list of strings
                args_list = [str(arg) for arg in args_list] if args_list else []
                
                # Get env vars (environment variables)
                env = config.get('env')
                if env and isinstance(env, dict) and len(env) > 0:
                    env_vars = {str(k): str(v) for k, v in env.items()}
                else:
                    env_vars = None
                
                logger.info(f"Creating stdio transport: command='{command}', args={args_list}, env={'***' if env_vars else None}")
                
                # Create StdioTransport explicitly (matching MCPJam Inspector approach)
                # This avoids FastMCP inferring it as a config transport
                # IMPORTANT: We MUST pass a StdioTransport instance, not a dict
                try:
                    transport = StdioTransport(
                        command=command,
                        args=args_list,
                        env=env_vars
                    )
                    logger.info(f"StdioTransport created successfully: {type(transport)}")
                except Exception as transport_error:
                    logger.error(f"Failed to create StdioTransport: {transport_error}", exc_info=True)
                    raise ValueError(f"Failed to create stdio transport: {transport_error}") from transport_error
                
                # Create FastMCPClient with the explicit transport instance
                # This ensures FastMCP doesn't try to infer the transport type
                try:
                    client = FastMCPClient(transport=transport, timeout=timeout)
                    logger.info(f"FastMCPClient created successfully with transport type: {type(transport)}")
                except Exception as client_error:
                    logger.error(f"Failed to create FastMCPClient: {client_error}", exc_info=True)
                    raise ValueError(f"Failed to create MCP client: {client_error}") from client_error
                
            elif config['type'] in ['sse', 'http']:
                # Validate HTTP/SSE configuration
                if not config.get('url'):
                    raise ValueError(f"{config['type']} server requires a 'url' to be configured")
                
                # For HTTP/SSE servers, pass URL directly as transport
                url = config['url']
                logger.debug(f"HTTP/SSE transport URL: {url}")
                client = FastMCPClient(transport=url, timeout=timeout)
            
            else:
                raise ValueError(f"Unsupported server type: {config['type']}")
            
            logger.info(f"Successfully created FastMCP client for {server_config.name}")
            return client
            
        except Exception as e:
            logger.error(f"Failed to create MCP client for {server_config.name}: {str(e)}", exc_info=True)
            raise
    
    def test_connection(self, server_config) -> Dict[str, Any]:
        """
        Test connection to an MCP server.
        
        Args:
            server_config: MCPServerConfig model instance
            
        Returns:
            Dictionary with success status and server info
        """
        loop = self._get_event_loop()
        return loop.run_until_complete(self._test_connection_async(server_config))
    
    async def _test_connection_async(self, server_config) -> Dict[str, Any]:
        """Async implementation of test_connection."""
        try:
            client = self._create_client(server_config)
            
            async with client:
                # Try to list tools to verify connection
                # FastMCP 2.0 methods are ASYNC even within async with context
                tools = await client.list_tools()
                
                return {
                    'success': True,
                    'message': 'Successfully connected to MCP server',
                    'server_info': {
                        'tool_count': len(tools) if tools else 0,
                        'server_type': server_config.server_type,
                    }
                }
                
        except Exception as e:
            logger.error(f"Error testing MCP connection: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to connect: {str(e)}'
            }
    
    def sync_server(self, server_config, user) -> Dict[str, Any]:
        """
        Sync tools, resources, and prompts from an MCP server.
        
        Args:
            server_config: MCPServerConfig model instance
            user: User instance
            
        Returns:
            Dictionary with sync results
        """
        loop = self._get_event_loop()
        return loop.run_until_complete(self._sync_server_async(server_config, user))
    
    async def _sync_server_async(self, server_config, user) -> Dict[str, Any]:
        """Async implementation of sync_server."""
        from .models import MCPTool, MCPResource, MCPPrompt
        
        try:
            client = self._create_client(server_config)
            
            async with client:
                # Discover tools - FastMCP 2.0 returns mcp.types.Tool objects
                # Tools are usually supported by all MCP servers, but handle errors gracefully
                tools_synced = 0
                try:
                    tools = await client.list_tools()
                    if tools:
                        for tool_info in tools:
                            # FastMCP Tool has: name, description, inputSchema
                            # Use sync_to_async to call Django ORM from async context
                            tool_obj, created = await sync_to_async(MCPTool.objects.update_or_create)(
                                server_config=server_config,
                                tool_name=tool_info.name,
                                defaults={
                                    'description': tool_info.description or '',
                                    'input_schema': tool_info.inputSchema if hasattr(tool_info, 'inputSchema') else {},
                                    'last_synced_at': timezone.now(),
                                }
                            )
                            tools_synced += 1
                except McpError as e:
                    # If tools/list is not supported, log and continue
                    if "Method not found" in str(e) or "method not found" in str(e).lower():
                        logger.warning(f"Server {server_config.name} does not support tools/list method")
                    else:
                        # Re-raise if it's a different error
                        raise
                except Exception as e:
                    logger.error(f"Error listing tools for {server_config.name}: {str(e)}")
                    # Re-raise for tools since they're usually critical
                    raise
                
                # Discover resources - FastMCP 2.0 returns mcp.types.Resource objects
                # Some MCP servers don't support resources, so handle gracefully
                resources_synced = 0
                try:
                    resources = await client.list_resources()
                    if resources:
                        for resource_info in resources:
                            # FastMCP Resource has: uri, name, description, mimeType
                            # Use sync_to_async to call Django ORM from async context
                            resource_obj, created = await sync_to_async(MCPResource.objects.update_or_create)(
                                server_config=server_config,
                                resource_uri=resource_info.uri,
                                defaults={
                                    'resource_name': resource_info.name or str(resource_info.uri),
                                    'description': resource_info.description or '',
                                    'resource_type': '',  # Not provided in MCP spec
                                    'mime_type': resource_info.mimeType or '',
                                    'last_synced_at': timezone.now(),
                                }
                            )
                            resources_synced += 1
                except McpError as e:
                    # Method not found or not supported - this is OK, not all servers support resources
                    if "Method not found" in str(e) or "method not found" in str(e).lower():
                        logger.info(f"Server {server_config.name} does not support resources/list method - skipping")
                    else:
                        # Re-raise if it's a different error
                        raise
                except Exception as e:
                    logger.warning(f"Error listing resources for {server_config.name}: {str(e)}")
                    # Continue with sync even if resources fail
                
                # Discover prompts - FastMCP 2.0 returns mcp.types.Prompt objects
                # Some MCP servers don't support prompts, so handle gracefully
                prompts_synced = 0
                try:
                    prompts = await client.list_prompts()
                    if prompts:
                        for prompt_info in prompts:
                            # FastMCP Prompt has: name, description, arguments
                            # Convert arguments to list of dicts
                            args_list = []
                            if hasattr(prompt_info, 'arguments') and prompt_info.arguments:
                                args_list = [
                                    {
                                        'name': arg.name,
                                        'description': arg.description or '',
                                        'required': arg.required if hasattr(arg, 'required') else False,
                                    }
                                    for arg in prompt_info.arguments
                                ]
                            
                            # Use sync_to_async to call Django ORM from async context
                            prompt_obj, created = await sync_to_async(MCPPrompt.objects.update_or_create)(
                                server_config=server_config,
                                prompt_name=prompt_info.name,
                                defaults={
                                    'description': prompt_info.description or '',
                                    'prompt_template': '',  # Template not provided in list
                                    'arguments': args_list,
                                    'last_synced_at': timezone.now(),
                                }
                            )
                            prompts_synced += 1
                except McpError as e:
                    # Method not found or not supported - this is OK, not all servers support prompts
                    if "Method not found" in str(e) or "method not found" in str(e).lower():
                        logger.info(f"Server {server_config.name} does not support prompts/list method - skipping")
                    else:
                        # Re-raise if it's a different error
                        raise
                except Exception as e:
                    logger.warning(f"Error listing prompts for {server_config.name}: {str(e)}")
                    # Continue with sync even if prompts fail
                
                # Update server sync timestamp
                server_config.last_sync_at = timezone.now()
                await sync_to_async(server_config.mark_connected)()
                
                return {
                    'success': True,
                    'tools_count': tools_synced,
                    'resources_count': resources_synced,
                    'prompts_count': prompts_synced,
                }
                
        except Exception as e:
            logger.error(f"Error syncing MCP server: {str(e)}", exc_info=True)
            await sync_to_async(server_config.mark_disconnected)(str(e))
            raise
    
    def execute_tool(self, server_config, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute an MCP tool.
        
        Args:
            server_config: MCPServerConfig model instance
            tool_name: Name of the tool to execute
            arguments: Tool arguments as dictionary
            
        Returns:
            Tool execution result
        """
        loop = self._get_event_loop()
        return loop.run_until_complete(
            self._execute_tool_async(server_config, tool_name, arguments)
        )
    
    async def _execute_tool_async(self, server_config, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Async implementation of execute_tool."""
        try:
            logger.info(f"🔧 EXECUTING MCP TOOL: {tool_name}")
            logger.info(f"   Server: {server_config.name}")
            logger.info(f"   Arguments: {arguments}")
            
            client = self._create_client(server_config)
            
            async with client:
                # FastMCP 2.0: call_tool is async, returns CallToolResult
                result = await client.call_tool(name=tool_name, arguments=arguments)
                
                # Convert CallToolResult to dict for JSON serialization
                # CallToolResult has: content (list of TextContent/ImageContent), isError (bool)
                result_dict = {
                    'success': not (hasattr(result, 'isError') and result.isError),
                    'content': [],
                    'is_error': hasattr(result, 'isError') and result.isError
                }
                
                # Extract content from result
                if hasattr(result, 'content') and result.content:
                    for content_item in result.content:
                        if hasattr(content_item, 'type'):
                            if content_item.type == 'text':
                                result_dict['content'].append({
                                    'type': 'text',
                                    'text': content_item.text if hasattr(content_item, 'text') else str(content_item)
                                })
                            elif content_item.type == 'image':
                                result_dict['content'].append({
                                    'type': 'image',
                                    'data': content_item.data if hasattr(content_item, 'data') else ''
                                })
                            else:
                                # Unknown content type - convert to string
                                result_dict['content'].append({
                                    'type': 'unknown',
                                    'data': str(content_item)
                                })
                        else:
                            # No type attribute - convert to string
                            result_dict['content'].append({
                                'type': 'text',
                                'text': str(content_item)
                            })
                
                # If content is empty, try to convert entire result to string
                if not result_dict['content']:
                    result_dict['content'].append({
                        'type': 'text',
                        'text': str(result)
                    })
                
                logger.info(f"✅ TOOL EXECUTION SUCCESS: {tool_name}")
                logger.info(f"   Result: {result_dict}")
                
                return result_dict
                
        except Exception as e:
            logger.error(f"❌ TOOL EXECUTION FAILED: {tool_name}")
            logger.error(f"   Error: {str(e)}", exc_info=True)
            raise
    
    def read_resource(self, server_config, resource_uri: str) -> Any:
        """
        Read an MCP resource.
        
        Args:
            server_config: MCPServerConfig model instance
            resource_uri: URI of the resource to read
            
        Returns:
            Resource content
        """
        loop = self._get_event_loop()
        return loop.run_until_complete(
            self._read_resource_async(server_config, resource_uri)
        )
    
    async def _read_resource_async(self, server_config, resource_uri: str) -> Any:
        """Async implementation of read_resource."""
        try:
            client = self._create_client(server_config)
            
            async with client:
                # FastMCP 2.0: read_resource is async
                result = await client.read_resource(uri=resource_uri)
                return result
                
        except Exception as e:
            logger.error(f"Error reading MCP resource: {str(e)}", exc_info=True)
            raise
    
    def render_prompt(self, server_config, prompt_name: str, arguments: Dict[str, Any]) -> str:
        """
        Render an MCP prompt with arguments.
        
        Args:
            server_config: MCPServerConfig model instance
            prompt_name: Name of the prompt to render
            arguments: Prompt arguments as dictionary
            
        Returns:
            Rendered prompt text
        """
        loop = self._get_event_loop()
        return loop.run_until_complete(
            self._render_prompt_async(server_config, prompt_name, arguments)
        )
    
    async def _render_prompt_async(self, server_config, prompt_name: str, arguments: Dict[str, Any]) -> str:
        """Async implementation of render_prompt."""
        try:
            client = self._create_client(server_config)
            
            async with client:
                # FastMCP 2.0: get_prompt is async
                # Returns mcp.types.GetPromptResult with messages
                result = await client.get_prompt(name=prompt_name, arguments=arguments)
                
                # Extract the rendered text from messages
                if hasattr(result, 'messages') and result.messages:
                    first_message = result.messages[0]
                    if hasattr(first_message, 'content'):
                        return str(first_message.content)
                return str(result)
                
        except Exception as e:
            logger.error(f"Error rendering MCP prompt: {str(e)}", exc_info=True)
            raise
    
    def connect_server(self, server_config):
        """
        Establish persistent connection to an MCP server.
        
        Args:
            server_config: MCPServerConfig model instance
        """
        # For stdio servers, we create connections on-demand
        # For HTTP/SSE servers, we can maintain persistent connections
        if server_config.server_type in ['sse', 'http']:
            loop = self._get_event_loop()
            loop.run_until_complete(self._connect_server_async(server_config))
    
    async def _connect_server_async(self, server_config):
        """Async implementation of connect_server."""
        try:
            client = self._create_client(server_config)
            self.active_clients[server_config.id] = client
            server_config.mark_connected()
            logger.info(f"Connected to MCP server: {server_config.name}")
            
        except Exception as e:
            logger.error(f"Error connecting to MCP server: {str(e)}")
            server_config.mark_disconnected(str(e))
            raise
    
    def disconnect_server(self, server_id: int):
        """
        Disconnect from an MCP server.
        
        Args:
            server_id: ID of the server configuration
        """
        if server_id in self.active_clients:
            client = self.active_clients.pop(server_id)
            # FastMCP clients are context managers, they clean up automatically
            logger.info(f"Disconnected from MCP server: {server_id}")
    
    def disconnect_all(self):
        """Disconnect from all active MCP servers."""
        for server_id in list(self.active_clients.keys()):
            self.disconnect_server(server_id)


# Global instance for reuse
_mcp_client_manager = None


def get_mcp_client_manager() -> MCPClientManager:
    """Get or create the global MCP client manager instance."""
    global _mcp_client_manager
    if _mcp_client_manager is None:
        _mcp_client_manager = MCPClientManager()
    return _mcp_client_manager

