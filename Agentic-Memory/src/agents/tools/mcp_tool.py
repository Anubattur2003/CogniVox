"""
MCP Tool for LangChain Agents.

This tool wraps MCP (Model Context Protocol) servers, allowing agents to
dynamically discover and execute tools from user-configured MCP servers.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.mcp.mcp_client import MCPClient

# Configure logging
logger = logging.getLogger("cogniVox")


class MCPToolInput(BaseModel):
    """Input schema for MCP tool execution."""
    tool_name: str = Field(description="Name of the MCP tool to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")
    user_id: Optional[str] = Field(default=None, description="User ID for authentication")
    auth_token: Optional[str] = Field(default=None, description="JWT authentication token")


class MCPDynamicTool(BaseTool):
    """
    Dynamic tool that can execute any MCP tool from user's configured servers.
    
    This tool discovers available MCP tools at runtime and executes them
    based on the agent's decision.
    """
    
    name: str = "mcp_execute"
    description: str = """Execute tools from MCP (Model Context Protocol) servers.
    
Use this tool when you need to:
- Interact with external APIs and services configured by the user
- Access file systems, databases, or other data sources
- Execute custom scripts or commands
- Use specialized tools not available in the base agent

Available tools are discovered from the user's MCP server configurations.
To execute a tool, provide the tool name and required arguments.

Example: {"tool_name": "read_file", "arguments": {"path": "/path/to/file"}}
"""
    
    args_schema: type[BaseModel] = MCPToolInput
    
    # MCP client for API communication
    mcp_client: MCPClient = Field(default_factory=lambda: MCPClient())
    
    # Cache for user tools
    _user_tools_cache: Dict[str, List[Dict[str, Any]]] = {}
    _auth_token_cache: Dict[str, str] = {}
    
    def __init__(self, mcp_client: Optional[MCPClient] = None, **kwargs):
        """Initialize the MCP tool."""
        if mcp_client is not None:
            kwargs['mcp_client'] = mcp_client
        super().__init__(**kwargs)
    
    def _get_user_tools(self, user_id: str, auth_token: str) -> List[Dict[str, Any]]:
        """
        Get available MCP tools for a user (with caching).
        
        Args:
            user_id: User ID
            auth_token: JWT authentication token
            
        Returns:
            List of available tools
        """
        # Cache tools per user to avoid repeated API calls
        if user_id not in self._user_tools_cache:
            tools = self.mcp_client.get_user_tools(user_id, auth_token)
            self._user_tools_cache[user_id] = tools
            self._auth_token_cache[user_id] = auth_token
            logger.info(f"Cached {len(tools)} MCP tools for user {user_id}")
        
        return self._user_tools_cache.get(user_id, [])
    
    def _find_tool(self, tool_name: str, user_id: str, auth_token: str) -> Optional[Dict[str, Any]]:
        """
        Find a tool by name from user's available tools.
        
        Args:
            tool_name: Name of the tool to find
            user_id: User ID
            auth_token: JWT authentication token
            
        Returns:
            Tool definition or None if not found
        """
        tools = self._get_user_tools(user_id, auth_token)
        
        for tool in tools:
            if tool.get('tool_name') == tool_name:
                return tool
        
        return None
    
    def _run(
        self,
        tool_name: str,
        arguments: Dict[str, Any] = None,
        user_id: str = None,
        auth_token: str = None,
        **kwargs
    ) -> str:
        """
        Execute an MCP tool.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            user_id: User ID for authentication
            auth_token: JWT authentication token
            
        Returns:
            Formatted string with execution results
        """
        if arguments is None:
            arguments = {}
        
        try:
            # Validate required parameters
            if not user_id:
                return "Error: user_id is required for MCP tool execution"
            
            if not auth_token:
                return "Error: auth_token is required for MCP tool execution"
            
            # Find the tool
            tool = self._find_tool(tool_name, user_id, auth_token)
            
            if not tool:
                available_tools = self._get_user_tools(user_id, auth_token)
                tool_names = [t.get('tool_name') for t in available_tools]
                return f"Error: Tool '{tool_name}' not found. Available tools: {', '.join(tool_names)}"
            
            logger.info(f"Executing MCP tool: {tool_name} with arguments: {arguments}")
            
            # Execute the tool
            result = self.mcp_client.execute_tool(
                tool_id=tool['id'],
                arguments=arguments,
                auth_token=auth_token,
                chat_thread_id=kwargs.get('chat_thread_id')
            )
            
            if result.get('success'):
                # Format successful result
                tool_result = result.get('result', {})
                execution_time = result.get('execution_time', 0)
                
                formatted_response = [
                    f"MCP TOOL EXECUTION SUCCESS:",
                    f"Tool: {tool_name}",
                    f"Server: {tool.get('server_name')}",
                    f"Execution Time: {execution_time:.2f}s",
                    f"\nResult:",
                    json.dumps(tool_result, indent=2)
                ]
                
                return "\n".join(formatted_response)
            else:
                # Format error result
                error_msg = result.get('error', 'Unknown error')
                return f"MCP TOOL EXECUTION FAILED:\nTool: {tool_name}\nError: {error_msg}"
                
        except Exception as e:
            logger.error(f"Error in MCP tool execution: {str(e)}")
            return f"Error executing MCP tool: {str(e)}"
    
    async def _arun(
        self,
        tool_name: str,
        arguments: Dict[str, Any] = None,
        user_id: str = None,
        auth_token: str = None,
        **kwargs
    ) -> str:
        """Async version of the tool (delegates to sync version)."""
        return self._run(tool_name, arguments, user_id, auth_token, **kwargs)
    
    def list_available_tools(self, user_id: str, auth_token: str) -> str:
        """
        List all available MCP tools for a user.
        
        Args:
            user_id: User ID
            auth_token: JWT authentication token
            
        Returns:
            Formatted string with available tools
        """
        try:
            tools = self._get_user_tools(user_id, auth_token)
            
            if not tools:
                return "No MCP tools available. Configure MCP servers in settings."
            
            formatted_tools = ["AVAILABLE MCP TOOLS:"]
            
            for tool in tools:
                formatted_tools.append(
                    f"\n• {tool.get('tool_name')} ({tool.get('server_name')})"
                )
                if tool.get('description'):
                    formatted_tools.append(f"  {tool.get('description')}")
                
                # Show required parameters
                input_schema = tool.get('input_schema', {})
                if input_schema and 'properties' in input_schema:
                    params = list(input_schema['properties'].keys())
                    formatted_tools.append(f"  Parameters: {', '.join(params)}")
            
            return "\n".join(formatted_tools)
            
        except Exception as e:
            logger.error(f"Error listing MCP tools: {str(e)}")
            return f"Error listing MCP tools: {str(e)}"
    
    def clear_cache(self, user_id: Optional[str] = None):
        """
        Clear the tools cache.
        
        Args:
            user_id: Optional user ID to clear cache for. If None, clears all.
        """
        if user_id:
            self._user_tools_cache.pop(user_id, None)
            self._auth_token_cache.pop(user_id, None)
            logger.info(f"Cleared MCP tools cache for user {user_id}")
        else:
            self._user_tools_cache.clear()
            self._auth_token_cache.clear()
            logger.info("Cleared all MCP tools cache")


def create_mcp_tool(mcp_client: Optional[MCPClient] = None) -> MCPDynamicTool:
    """
    Factory function to create an MCP tool instance.
    
    Args:
        mcp_client: Optional MCP client instance
        
    Returns:
        MCPDynamicTool instance
    """
    return MCPDynamicTool(mcp_client=mcp_client)

