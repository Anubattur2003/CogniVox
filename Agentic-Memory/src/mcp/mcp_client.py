"""
MCP Client for Agentic-Memory service.

This module provides a client to communicate with the Django MCP API
to retrieve user-specific MCP server configurations and execute tools.
"""
import os
import logging
import requests
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger("cogniVox")


class MCPClient:
    """
    Client for interacting with MCP services via Django API.
    
    RBAC Enforcement:
    - All operations require auth_token for user authentication
    - Django backend filters tools/servers by user ownership
    - Tool execution validates user owns the tool via auth_token
    - Each user can only access their own MCP servers and tools
    """
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv(
            "DJANGO_API_URL",
            "http://localhost:8000"
        )
        self.mcp_endpoint = f"{self.base_url}/api/mcp"
        self.timeout = 60  # Increased timeout for MCP operations
        
        # MCP capability cache (Performance Optimization)
        self._capability_cache: Dict[str, Tuple[dict, datetime]] = {}
        self._cache_ttl_seconds = 300  # 5 minutes default (from config)
        self._load_cache_config()
    
    def _load_cache_config(self):
        """Load cache configuration from config module"""
        try:
            from src.utils.config import get_mcp_cache_config
            cache_config = get_mcp_cache_config()
            self._cache_enabled = cache_config.get("enabled", True)
            self._cache_ttl_seconds = cache_config.get("ttl_seconds", 300)
            self._max_cache_size = cache_config.get("max_cache_size", 100)
            logger.debug(f"MCP cache config loaded: enabled={self._cache_enabled}, ttl={self._cache_ttl_seconds}s")
        except Exception as e:
            logger.warning(f"Failed to load cache config, using defaults: {e}")
            self._cache_enabled = True
            self._cache_ttl_seconds = 300
            self._max_cache_size = 100
    
    def _get_cache_key(self, user_id: str, auth_token: Optional[str], server_id: Optional[int] = None) -> str:
        """Generate cache key for MCP capabilities"""
        token_hash = hash(auth_token) if auth_token else "no_token"
        server_suffix = f"_server_{server_id}" if server_id else "_all"
        return f"{user_id}_{token_hash}{server_suffix}"
    
    def _get_cached_capabilities(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get capabilities from cache if valid"""
        if not self._cache_enabled:
            return None
            
        if cache_key in self._capability_cache:
            cached_data, timestamp = self._capability_cache[cache_key]
            age = (datetime.now() - timestamp).total_seconds()
            
            if age < self._cache_ttl_seconds:
                logger.debug(f"Cache HIT for {cache_key} (age: {age:.1f}s)")
                return cached_data
            else:
                logger.debug(f"Cache EXPIRED for {cache_key} (age: {age:.1f}s)")
                del self._capability_cache[cache_key]
        
        logger.debug(f"Cache MISS for {cache_key}")
        return None
    
    def _cache_capabilities(self, cache_key: str, data: Dict[str, Any]):
        """Cache MCP capabilities"""
        if not self._cache_enabled:
            return
            
        # Enforce max cache size (simple LRU by removing oldest)
        if len(self._capability_cache) >= self._max_cache_size:
            oldest_key = min(self._capability_cache.keys(), 
                           key=lambda k: self._capability_cache[k][1])
            del self._capability_cache[oldest_key]
            logger.debug(f"Cache full, removed oldest entry: {oldest_key}")
        
        self._capability_cache[cache_key] = (data, datetime.now())
        logger.debug(f"Cached capabilities for {cache_key}")
    
    def get_user_servers(self, user_id: str, auth_token: str) -> List[Dict[str, Any]]:
        """
        Get all active MCP servers for a user.
        
        Args:
            user_id: User ID
            auth_token: JWT authentication token
            
        Returns:
            List of server configurations
        """
        try:
            headers = {
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.mcp_endpoint}/servers/",
                headers=headers,
                params={"is_active": "true"},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching MCP servers: {str(e)}")
            return []
    
    def get_user_resources(self, user_id: str, auth_token: Optional[str] = None, server_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all available MCP resources for a user (RBAC enforced at Django level).
        
        Args:
            user_id: User ID (for logging/tracking)
            auth_token: JWT authentication token (optional - Django validates via IsAuthenticated)
            server_id: Optional server ID to filter resources (must be owned by user)
            
        Returns:
            List of resource definitions (user-scoped, RBAC filtered by Django)
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
                logger.debug(f"Requesting MCP resources for user {user_id} with auth_token")
            else:
                logger.warning(f"Requesting MCP resources without auth_token - Django will require authentication")
            
            params = {}
            if server_id:
                params["server_id"] = server_id
            
            logger.debug(f"Calling Django MCP API: {self.mcp_endpoint}/resources/ with params: {params}")
            response = requests.get(
                f"{self.mcp_endpoint}/resources/",
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            
            logger.debug(f"Django MCP API response status: {response.status_code}")
            
            if response.status_code == 401:
                logger.warning(f"Django API returned 401 Unauthorized - authentication required for user {user_id}")
                return []
            elif response.status_code == 403:
                logger.warning(f"Django API returned 403 Forbidden - user {user_id} not authorized")
                return []
            
            response.raise_for_status()
            resources_data = response.json()
            
            if isinstance(resources_data, dict) and 'results' in resources_data:
                resources_data = resources_data['results']
            
            if not isinstance(resources_data, list):
                logger.error(f"Django API returned unexpected type: {type(resources_data)}")
                return []
            
            logger.info(f"Django API returned {len(resources_data)} resources for user {user_id}")
            return resources_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [401, 403]:
                logger.warning(f"Authentication/authorization error fetching MCP resources: {e.response.status_code}")
                return []
            logger.error(f"HTTP error fetching MCP resources: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching MCP resources: {str(e)}")
            return []
    
    def get_user_prompts(self, user_id: str, auth_token: Optional[str] = None, server_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all available MCP prompts for a user (RBAC enforced at Django level).
        
        Args:
            user_id: User ID (for logging/tracking)
            auth_token: JWT authentication token (optional - Django validates via IsAuthenticated)
            server_id: Optional server ID to filter prompts (must be owned by user)
            
        Returns:
            List of prompt definitions (user-scoped, RBAC filtered by Django)
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
                logger.debug(f"Requesting MCP prompts for user {user_id} with auth_token")
            else:
                logger.warning(f"Requesting MCP prompts without auth_token - Django will require authentication")
            
            params = {}
            if server_id:
                params["server_id"] = server_id
            
            logger.debug(f"Calling Django MCP API: {self.mcp_endpoint}/prompts/ with params: {params}")
            response = requests.get(
                f"{self.mcp_endpoint}/prompts/",
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            
            logger.debug(f"Django MCP API response status: {response.status_code}")
            
            if response.status_code == 401:
                logger.warning(f"Django API returned 401 Unauthorized - authentication required for user {user_id}")
                return []
            elif response.status_code == 403:
                logger.warning(f"Django API returned 403 Forbidden - user {user_id} not authorized")
                return []
            
            response.raise_for_status()
            prompts_data = response.json()
            
            if isinstance(prompts_data, dict) and 'results' in prompts_data:
                prompts_data = prompts_data['results']
            
            if not isinstance(prompts_data, list):
                logger.error(f"Django API returned unexpected type: {type(prompts_data)}")
                return []
            
            logger.info(f"Django API returned {len(prompts_data)} prompts for user {user_id}")
            return prompts_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [401, 403]:
                logger.warning(f"Authentication/authorization error fetching MCP prompts: {e.response.status_code}")
                return []
            logger.error(f"HTTP error fetching MCP prompts: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching MCP prompts: {str(e)}")
            return []
    
    def get_all_mcp_capabilities(
        self, 
        user_id: str, 
        auth_token: Optional[str] = None,
        server_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get all MCP capabilities (tools, resources, prompts) for a user.
        Uses caching and parallel fetching for performance.
        
        Args:
            user_id: User ID
            auth_token: JWT authentication token (optional)
            server_id: Optional server ID to filter
            
        Returns:
            Dictionary with tools, resources, and prompts lists
        """
        # Check cache first
        cache_key = self._get_cache_key(user_id, auth_token, server_id)
        cached = self._get_cached_capabilities(cache_key)
        if cached is not None:
            return cached
        
        # Try parallel fetching (async), fall back to sequential if it fails
        try:
            # Use asyncio to fetch all three in parallel
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self._fetch_capabilities_parallel(user_id, auth_token, server_id)
            )
            loop.close()
            
            # Cache the result
            self._cache_capabilities(cache_key, result)
            return result
            
        except Exception as e:
            logger.warning(f"Parallel fetch failed, falling back to sequential: {e}")
            # Fall back to sequential fetching
            tools = self.get_user_tools(user_id, auth_token or "", server_id)
            resources = self.get_user_resources(user_id, auth_token, server_id)
            prompts = self.get_user_prompts(user_id, auth_token, server_id)
            
            # Ensure we have lists (defensive programming)
            if not isinstance(tools, list):
                logger.warning(f"get_user_tools returned non-list: {type(tools)}, converting to empty list")
                tools = []
            if not isinstance(resources, list):
                logger.warning(f"get_user_resources returned non-list: {type(resources)}, converting to empty list")
                resources = []
            if not isinstance(prompts, list):
                logger.warning(f"get_user_prompts returned non-list: {type(prompts)}, converting to empty list")
                prompts = []
            
            result = {
                "tools": tools,
                "resources": resources,
                "prompts": prompts,
                "total_tools": len(tools),
                "total_resources": len(resources),
                "total_prompts": len(prompts)
            }
            
            # Cache the result
            self._cache_capabilities(cache_key, result)
            return result
    
    async def _fetch_capabilities_parallel(
        self,
        user_id: str,
        auth_token: Optional[str],
        server_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        Fetch tools, resources, and prompts in parallel using async.
        This reduces latency from ~7s to ~2-3s.
        """
        # Create async tasks for parallel execution
        tasks = [
            self._fetch_tools_async(user_id, auth_token or "", server_id),
            self._fetch_resources_async(user_id, auth_token, server_id),
            self._fetch_prompts_async(user_id, auth_token, server_id)
        ]
        
        # Run all three requests in parallel
        tools, resources, prompts = await asyncio.gather(*tasks)
        
        # Ensure we have lists
        if not isinstance(tools, list):
            tools = []
        if not isinstance(resources, list):
            resources = []
        if not isinstance(prompts, list):
            prompts = []
        
        return {
            "tools": tools,
            "resources": resources,
            "prompts": prompts,
            "total_tools": len(tools),
            "total_resources": len(resources),
            "total_prompts": len(prompts)
        }
    
    async def _fetch_tools_async(self, user_id: str, auth_token: str, server_id: Optional[int]) -> List[Dict[str, Any]]:
        """Async version of get_user_tools for parallel fetching"""
        try:
            headers = {"Content-Type": "application/json"}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            params = {"is_enabled": "true"}
            if server_id:
                params["server_id"] = server_id
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.mcp_endpoint}/tools/",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status in [401, 403]:
                        return []
                    
                    data = await response.json()
                    if isinstance(data, dict) and 'results' in data:
                        data = data['results']
                    return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Async fetch tools error: {e}")
            return []
    
    async def _fetch_resources_async(self, user_id: str, auth_token: Optional[str], server_id: Optional[int]) -> List[Dict[str, Any]]:
        """Async version of get_user_resources for parallel fetching"""
        try:
            headers = {"Content-Type": "application/json"}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            params = {}
            if server_id:
                params["server_id"] = server_id
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.mcp_endpoint}/resources/",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status in [401, 403]:
                        return []
                    
                    data = await response.json()
                    if isinstance(data, dict) and 'results' in data:
                        data = data['results']
                    return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Async fetch resources error: {e}")
            return []
    
    async def _fetch_prompts_async(self, user_id: str, auth_token: Optional[str], server_id: Optional[int]) -> List[Dict[str, Any]]:
        """Async version of get_user_prompts for parallel fetching"""
        try:
            headers = {"Content-Type": "application/json"}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            params = {}
            if server_id:
                params["server_id"] = server_id
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.mcp_endpoint}/prompts/",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status in [401, 403]:
                        return []
                    
                    data = await response.json()
                    if isinstance(data, dict) and 'results' in data:
                        data = data['results']
                    return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Async fetch prompts error: {e}")
            return []
    
    def get_user_tools(self, user_id: str, auth_token: str, server_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all available MCP tools for a user (RBAC enforced at Django level).
        
        Django backend filters tools by user ownership:
        - Only returns tools from servers owned by the authenticated user
        - Uses auth_token to identify and validate user via IsAuthenticated permission
        - If auth_token is missing/invalid, Django returns 401
        
        Args:
            user_id: User ID (for logging/tracking)
            auth_token: JWT authentication token (optional - Django validates via IsAuthenticated)
            server_id: Optional server ID to filter tools (must be owned by user)
            
        Returns:
            List of tool definitions (user-scoped, RBAC filtered by Django)
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            # Add Authorization header only if auth_token is provided
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
                logger.debug(f"Requesting MCP tools for user {user_id} with auth_token (length: {len(auth_token)})")
            else:
                logger.warning(f"Requesting MCP tools without auth_token - Django will require authentication")
            
            params = {"is_enabled": "true"}
            if server_id:
                params["server_id"] = server_id
            
            logger.debug(f"Calling Django MCP API: {self.mcp_endpoint}/tools/ with params: {params}")
            response = requests.get(
                f"{self.mcp_endpoint}/tools/",
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            
            logger.debug(f"Django MCP API response status: {response.status_code}")
            
            # Handle authentication errors gracefully
            if response.status_code == 401:
                logger.warning(f"Django API returned 401 Unauthorized - authentication required for user {user_id}")
                logger.debug(f"Response body: {response.text[:200]}")
                return []
            elif response.status_code == 403:
                logger.warning(f"Django API returned 403 Forbidden - user {user_id} not authorized")
                logger.debug(f"Response body: {response.text[:200]}")
                return []
            
            response.raise_for_status()
            tools_data = response.json()
            
            # Django REST Framework might return paginated results
            if isinstance(tools_data, dict) and 'results' in tools_data:
                tools_data = tools_data['results']
                logger.debug(f"Django API returned paginated results: {len(tools_data)} tools")
            
            # Ensure we have a list
            if not isinstance(tools_data, list):
                logger.error(f"Django API returned unexpected type: {type(tools_data)}, data: {str(tools_data)[:200]}")
                return []
            
            logger.info(f"Django API returned {len(tools_data)} tools for user {user_id}")
            
            # Log first tool structure for debugging
            if tools_data and len(tools_data) > 0:
                logger.debug(f"First tool structure: {type(tools_data[0])}, keys: {list(tools_data[0].keys()) if isinstance(tools_data[0], dict) else 'N/A'}")
            
            return tools_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [401, 403]:
                logger.warning(f"Authentication/authorization error fetching MCP tools: {e.response.status_code}")
                return []
            logger.error(f"HTTP error fetching MCP tools: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching MCP tools: {str(e)}")
            return []
    
    def read_resource(
        self,
        resource_id: int,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Read an MCP resource (RBAC enforced at Django level).
        
        Args:
            resource_id: ID of the resource to read
            auth_token: JWT authentication token (optional)
            
        Returns:
            Resource content with metadata
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            response = requests.get(
                f"{self.mcp_endpoint}/resources/{resource_id}/read/",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 401:
                return {"success": False, "error": "Authentication required"}
            elif response.status_code == 403:
                return {"success": False, "error": "Authorization failed"}
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error reading MCP resource: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def render_prompt(
        self,
        prompt_id: int,
        arguments: Dict[str, Any],
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Render an MCP prompt (RBAC enforced at Django level).
        
        Args:
            prompt_id: ID of the prompt to render
            arguments: Arguments for the prompt template
            auth_token: JWT authentication token (optional)
            
        Returns:
            Rendered prompt content
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            payload = {"arguments": arguments}
            
            response = requests.post(
                f"{self.mcp_endpoint}/prompts/{prompt_id}/render/",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 401:
                return {"success": False, "error": "Authentication required"}
            elif response.status_code == 403:
                return {"success": False, "error": "Authorization failed"}
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error rendering MCP prompt: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def execute_tool(
        self,
        tool_id: int,
        arguments: Dict[str, Any],
        auth_token: Optional[str] = None,
        chat_thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute an MCP tool (RBAC enforced at Django level).
        
        Django backend validates user ownership via IsAuthenticated permission.
        If auth_token is missing/invalid, Django returns 401.
        
        Args:
            tool_id: ID of the tool to execute
            arguments: Tool arguments
            auth_token: JWT authentication token (optional - Django validates via IsAuthenticated)
            chat_thread_id: Optional chat thread ID for context
            
        Returns:
            Tool execution result
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            # Add Authorization header only if auth_token is provided
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            else:
                logger.warning(f"Executing MCP tool {tool_id} without auth_token - Django will require authentication")
            
            payload = {
                "tool_id": tool_id,
                "arguments": arguments
            }
            
            if chat_thread_id:
                payload["chat_thread_id"] = chat_thread_id
            
            logger.info(f"Executing MCP tool {tool_id} with arguments: {arguments}")
            
            response = requests.post(
                f"{self.mcp_endpoint}/tools/{tool_id}/execute/",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            # Handle authentication errors gracefully
            if response.status_code == 401:
                logger.warning(f"Django API returned 401 Unauthorized - authentication required for tool {tool_id}")
                return {
                    "success": False,
                    "error": "Authentication required - please provide valid auth_token"
                }
            elif response.status_code == 403:
                logger.warning(f"Django API returned 403 Forbidden - user not authorized for tool {tool_id}")
                return {
                    "success": False,
                    "error": "Authorization failed - user does not own this tool"
                }
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"MCP tool execution result: {result.get('success', False)}")
            
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [401, 403]:
                logger.warning(f"Authentication/authorization error executing MCP tool: {e.response.status_code}")
                return {
                    "success": False,
                    "error": f"Authentication/authorization failed: {e.response.status_code}"
                }
            logger.error(f"HTTP error executing MCP tool: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except requests.exceptions.Timeout:
            logger.error(f"MCP tool execution timed out after {self.timeout}s")
            return {
                "success": False,
                "error": "Tool execution timed out"
            }
        except Exception as e:
            logger.error(f"Error executing MCP tool: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_execution_logs(
        self,
        auth_token: str,
        chat_thread_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get MCP execution logs for a user.
        
        Args:
            auth_token: JWT authentication token
            chat_thread_id: Optional chat thread ID to filter
            status: Optional status to filter (success, error, etc.)
            
        Returns:
            List of execution logs
        """
        try:
            headers = {
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            }
            
            params = {}
            if chat_thread_id:
                params["chat_thread_id"] = chat_thread_id
            if status:
                params["status"] = status
            
            response = requests.get(
                f"{self.mcp_endpoint}/logs/",
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching MCP execution logs: {str(e)}")
            return []

