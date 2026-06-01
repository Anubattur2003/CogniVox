"""
MCP Coordinator Agent

Manages MCP tool execution and coordinates with multiple MCP servers.
Handles credential loading dynamically.
"""
import logging
import asyncio
import difflib
from typing import Dict, Any, Optional, List
from langchain_core.messages import SystemMessage

from src.agents.base_agent import BaseAgent
from src.mcp.mcp_client import MCPClient
from src.agents.multi_agent.credential_manager import CredentialManager
from src.utils.toon_format import format_system_instruction
from src.utils.agent_logger import get_agent_logger

logger = get_agent_logger("mcp_coordinator")


class MCPCoordinatorAgent(BaseAgent):
    """
    Agent that coordinates MCP tool execution across multiple servers.
    """
    
    def __init__(
        self,
        model_name: str = "qwen3:4b",
        temperature: float = 0.1,
        mcp_client: Optional[MCPClient] = None,
        **kwargs
    ):
        """Initialize the MCP Coordinator Agent."""
        system_instruction = self._create_system_instruction()
        
        super().__init__(
            agent_name="mcp_coordinator",
            model_name=model_name,
            temperature=temperature,
            system_prompt=system_instruction,
            **kwargs
        )
        
        self.mcp_client = mcp_client or MCPClient()
        self.credential_manager = CredentialManager()
    
    def _create_system_instruction(self) -> str:
        """Create structured system instruction using TOON format."""
        instruction_data = {
            "role": "MCP Coordinator Agent",
            "purpose": "Coordinate and execute tools from MCP servers with RBAC enforcement",
            "capabilities": [
                "Tool discovery (user-scoped)",
                "Parallel tool execution (RBAC validated)",
                "Credential management (user-specific)",
                "Result aggregation",
                "RBAC enforcement - only user-owned tools accessible"
            ],
            "rbac_requirements": [
                "All tool operations require valid auth_token",
                "Tools are filtered by user ownership",
                "Tool execution validates user ownership",
                "Credentials are user-specific and isolated"
            ],
            "execution_strategy": {
                "parallel": "Execute independent tools in parallel",
                "sequential": "Execute dependent tools sequentially",
                "conditional": "Execute based on previous results"
            },
            "output_format": {
                "tools_used": "array - list of executed tool names",
                "outputs": "array - tool execution results",
                "success_count": "integer - number of successful executions",
                "error_count": "integer - number of failed executions"
            }
        }
        
        return format_system_instruction(instruction_data)
    
    def list_tools(
        self,
        user_id: str = "default",
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all available MCP tools for a user (RBAC enforced).
        
        Only returns tools from MCP servers owned by the authenticated user.
        
        Args:
            user_id: User identifier (must match authenticated user)
            auth_token: JWT authentication token (required for RBAC)
            
        Returns:
            List of available tools with metadata (user-scoped)
        """
        try:
            # Note: auth_token is optional - Django backend enforces RBAC via IsAuthenticated
            # If auth_token is missing, Django will return 401, which we'll handle gracefully
            if not user_id or user_id == "default":
                logger.warning("MCP Coordinator: Invalid user_id provided")
                return {
                    "tools_used": [],
                    "outputs": [],
                    "success_count": 0,
                    "error_count": 0,
                    "error": "Valid user_id required",
                    "is_list_result": True
                }
            
            if auth_token:
                logger.info(f"MCP Coordinator: Listing tools for user {user_id} with auth_token")
            else:
                logger.warning(f"MCP Coordinator: Listing tools for user {user_id} without auth_token - Django will enforce authentication")
            
            # Django backend filters tools by user ownership via IsAuthenticated permission
            # If auth_token is None or invalid, Django API will return 401 Unauthorized
            available_tools = self.mcp_client.get_user_tools(user_id, auth_token or "")
            
            # Check if we got an error response (empty list could mean auth failure or no tools)
            # The MCP client returns empty list on 401/403, so we need to check if auth_token was provided
            if not auth_token and len(available_tools) == 0:
                # No auth_token provided and no tools - likely authentication issue
                logger.warning(f"MCP Coordinator: No tools found and no auth_token provided - authentication required")
                return {
                    "tools_used": ["list_tools"],
                    "outputs": [{
                        "tool": "list_tools",
                        "success": False,
                        "error": "Authentication required - please provide valid auth_token"
                    }],
                    "success_count": 0,
                    "error_count": 1,
                    "total_tools": 0,
                    "is_list_result": True,
                    "user_id": user_id,
                    "error": "Authentication required"
                }
            
            # Format tools for response (already filtered by user via Django RBAC)
            formatted_tools = []
            for idx, tool in enumerate(available_tools):
                try:
                    # Handle both dict and string responses (defensive programming)
                    if isinstance(tool, str):
                        logger.warning(f"MCP Coordinator: Received string instead of dict for tool at index {idx}: {tool[:50]}")
                        continue
                    
                    if not isinstance(tool, dict):
                        logger.warning(f"MCP Coordinator: Received unexpected type {type(tool)} for tool at index {idx}: {str(tool)[:100]}")
                        continue
                    
                    # Django serializer returns: tool_name, server_name, server_id, input_schema, is_enabled, etc.
                    formatted_tool = {
                        "name": tool.get("tool_name", "Unknown"),
                        "description": tool.get("description") or "No description available",
                        "server": tool.get("server_name", "Unknown"),
                        "server_id": tool.get("server_id"),  # Include for reference
                        "parameters": tool.get("input_schema", {}),  # Django uses input_schema, not parameters
                        "enabled": tool.get("is_enabled", False),
                        "tool_id": tool.get("id")  # Include tool ID for execution
                    }
                    formatted_tools.append(formatted_tool)
                except Exception as e:
                    logger.error(f"MCP Coordinator: Error processing tool at index {idx}: {str(e)}, tool type: {type(tool)}, tool value: {str(tool)[:100]}")
                    continue
            
            logger.info(f"MCP Coordinator: Found {len(formatted_tools)} tools for user {user_id} (RBAC filtered)")
            
            return {
                "tools_used": ["list_tools"],
                "outputs": [{
                    "tool": "list_tools",
                    "success": True,
                    "result": {
                        "tools": formatted_tools,
                        "total_count": len(formatted_tools),
                        "user_id": user_id  # Include user_id for verification
                    }
                }],
                "success_count": 1,
                "error_count": 0,
                "total_tools": len(formatted_tools),
                "is_list_result": True,
                "user_id": user_id  # Track which user requested this
            }
            
        except Exception as e:
            logger.error(f"MCP Coordinator: Failed to list tools: {str(e)}")
            return {
                "tools_used": [],
                "outputs": [],
                "success_count": 0,
                "error_count": 1,
                "error": str(e),
                "is_list_result": True
            }
    
    def execute(
        self,
        query: str,
        tools_to_use: List[Dict[str, Any]] = None,
        resources_to_use: List[Dict[str, Any]] = None,
        prompts_to_use: List[Dict[str, Any]] = None,
        user_id: str = "default",
        auth_token: Optional[str] = None,
        execution_plan: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute MCP tools, resources, and prompts based on the plan (RBAC enforced).
        
        Only executes capabilities from MCP servers owned by the authenticated user.
        Validates ownership before execution.
        
        Args:
            query: Original user query
            tools_to_use: List of tools to execute (from query analysis)
            resources_to_use: List of resources to read (from query analysis)
            prompts_to_use: List of prompts to render (from query analysis)
            user_id: User identifier (must match authenticated user)
            auth_token: JWT authentication token (required for RBAC)
            
        Returns:
            Execution results (only for user-owned capabilities)
        """
        try:
            tools_to_use = tools_to_use or []
            resources_to_use = resources_to_use or []
            prompts_to_use = prompts_to_use or []
            
            # Check if this is a list tools request
            if tools_to_use and len(tools_to_use) == 1:
                tool_plan = tools_to_use[0]
                if tool_plan.get("tool_name") == "list_tools":
                    return self.list_tools(user_id=user_id, auth_token=auth_token)
            
            if not tools_to_use and not resources_to_use and not prompts_to_use:
                logger.info(f"MCP Coordinator: No MCP capabilities to execute for user {user_id}")
                return {
                    "tools_used": [],
                    "resources_used": [],
                    "prompts_used": [],
                    "outputs": [],
                    "success_count": 0,
                    "error_count": 0
                }
            
            if not user_id or user_id == "default":
                logger.warning("MCP Coordinator: Invalid user_id provided")
                return {
                    "tools_used": [],
                    "outputs": [],
                    "success_count": 0,
                    "error_count": 0,
                    "error": "Valid user_id required"
                }
            
            # Get available tools for user (Django backend filters by user ownership via IsAuthenticated)
            # auth_token is optional - Django will enforce authentication
            if auth_token:
                logger.info(f"MCP Coordinator: Fetching user-owned tools for user {user_id} with auth_token")
            else:
                logger.warning(f"MCP Coordinator: Fetching tools for user {user_id} without auth_token - Django will require authentication")
            
            available_tools = self.mcp_client.get_user_tools(user_id, auth_token or "")
            tool_map = {tool.get('tool_name'): tool for tool in available_tools}
            
            logger.info(f"MCP Coordinator: User {user_id} has access to {len(available_tools)} tools")
            
            executed_tools = []
            outputs = []
            success_count = 0
            error_count = 0
            
            # Use execution plan if provided to order tools
            if execution_plan:
                order = execution_plan.get("order", [])
                dependencies = execution_plan.get("dependencies", {})
                parallel = execution_plan.get("parallel", [])
                
                # Sort tools according to execution plan
                if order:
                    tool_plan_map = {plan.get("tool_name"): plan for plan in tools_to_use}
                    ordered_tools = []
                    for tool_name in order:
                        if tool_name in tool_plan_map:
                            ordered_tools.append(tool_plan_map[tool_name])
                    # Add any tools not in order list
                    for plan in tools_to_use:
                        if plan.get("tool_name") not in order:
                            ordered_tools.append(plan)
                    tools_to_use = ordered_tools
                    logger.info(f"MCP Coordinator: Using execution plan order: {order}")
            
            # Execute tools (can be parallelized if independent)
            # RBAC: Only tools in tool_map (user-owned) can be executed
            for tool_plan in tools_to_use:
                tool_name = tool_plan.get("tool_name")
                tool_args = tool_plan.get("arguments", {})
                
                # Ensure arguments is a dict
                if not isinstance(tool_args, dict):
                    logger.warning(f"Tool '{tool_name}' has invalid arguments type: {type(tool_args)}, converting to empty dict")
                    tool_args = {}
                
                # Validate and enrich arguments against tool schema before execution
                tool_args = self._validate_and_enrich_arguments(tool_name, tool_args, tool_map)
                
                # Enhanced fuzzy tool matching with multiple strategies
                tool_info = None
                actual_tool_name = tool_name
                
                # Strategy 1: Exact match (case-sensitive)
                if tool_name in tool_map:
                    tool_info = tool_map[tool_name]
                    logger.debug(f"Exact match found for tool '{tool_name}'")
                else:
                    # Strategy 2: Case-insensitive match
                    tool_name_lower = tool_name.lower()
                    for actual_name, info in tool_map.items():
                        if actual_name.lower() == tool_name_lower:
                            tool_info = info
                            actual_tool_name = actual_name
                            logger.info(f"Case-insensitive matched '{tool_name}' to '{actual_tool_name}'")
                            break
                    
                    # Strategy 3: Levenshtein distance (fuzzy matching)
                    if not tool_info:
                        matches = self._fuzzy_match_tool_name(tool_name, list(tool_map.keys()))
                        if matches:
                            best_match = matches[0]
                            tool_info = tool_map[best_match]
                            actual_tool_name = best_match
                            logger.info(f"Fuzzy matched '{tool_name}' to '{actual_tool_name}' (similarity: {matches[0]}")
                    
                    # Strategy 4: Partial substring match (last resort)
                    if not tool_info:
                        for actual_name, info in tool_map.items():
                            if tool_name_lower in actual_name.lower() or actual_name.lower() in tool_name_lower:
                                tool_info = info
                                actual_tool_name = actual_name
                                logger.info(f"Partial matched '{tool_name}' to '{actual_tool_name}'")
                                break
                
                # Enhanced error message if tool not found
                if not tool_info:
                    available_names = list(tool_map.keys())
                    
                    # Get suggestions using fuzzy matching
                    suggestions = self._get_tool_suggestions(tool_name, available_names)
                    
                    if suggestions:
                        error_msg = f"Tool '{tool_name}' not found for user {user_id}. Did you mean: {', '.join(suggestions[:3])}?"
                    else:
                        # Show first few available tools
                        sample_tools = available_names[:5]
                        error_msg = f"Tool '{tool_name}' not found for user {user_id}. Available tools: {', '.join(sample_tools)}"
                    
                    logger.warning(error_msg)
                    error_count += 1
                    outputs.append({
                        "tool": tool_name,
                        "success": False,
                        "error": error_msg,
                        "suggestions": suggestions[:3] if suggestions else None,
                        "available_tools_sample": sample_tools if not suggestions else None,
                        "user_id": user_id
                    })
                    continue
                
                # Use the actual tool name (may have been corrected)
                tool_name = actual_tool_name
                
                tool_id = tool_info.get('id')
                server_id = tool_info.get('server_id')
                server_name = tool_info.get('server_name', 'Unknown')
                server_is_active = tool_info.get('server_is_active', True)
                server_connection_status = tool_info.get('server_connection_status', 'connected')
                
                # CRITICAL: Validate server status before execution
                if not server_is_active:
                    logger.warning(f"MCP Coordinator: Server '{server_name}' is not active - skipping tool '{tool_name}'")
                    error_count += 1
                    outputs.append({
                        "tool": tool_name,
                        "success": False,
                        "error": f"Server '{server_name}' is not active",
                        "user_id": user_id
                    })
                    continue
                
                if server_connection_status != 'connected':
                    logger.warning(f"MCP Coordinator: Server '{server_name}' is not connected (status: {server_connection_status}) - skipping tool '{tool_name}'")
                    error_count += 1
                    outputs.append({
                        "tool": tool_name,
                        "success": False,
                        "error": f"Server '{server_name}' is not connected (status: {server_connection_status})",
                        "user_id": user_id
                    })
                    continue
                
                # Additional RBAC validation: Log tool ownership
                logger.info("="*80)
                logger.info("🔧 [MEMORY SERVICE] MCP TOOL EXECUTION")
                logger.info(f"   Tool: {tool_name} (ID: {tool_id})")
                logger.info(f"   Server: {server_name} (ID: {server_id})")
                logger.info(f"   User ID: {user_id}")
                logger.info(f"   Arguments: {tool_args}")
                logger.info("="*80)
                
                try:
                    # Execute tool - Django backend validates ownership via IsAuthenticated permission
                    # auth_token is optional - Django will enforce authentication
                    result = self.mcp_client.execute_tool(
                        tool_id=tool_id,
                        arguments=tool_args,
                        auth_token=auth_token  # Optional - Django validates user owns this tool
                    )
                    
                    if result.get("success"):
                        success_count += 1
                        executed_tools.append(tool_name)
                        
                        logger.info("="*80)
                        logger.info("✅ [MEMORY SERVICE] TOOL EXECUTION SUCCESS")
                        logger.info(f"   Tool: {tool_name}")
                        logger.info(f"   Execution Time: {result.get('execution_time', 0.0):.3f}s")
                        logger.info(f"   Result: {result.get('result', {})}")
                        logger.info("="*80)
                        
                        outputs.append({
                            "tool": tool_name,
                            "tool_id": tool_id,
                            "server_id": server_id,
                            "success": True,
                            "result": result.get("result", {}),
                            "execution_time": result.get("execution_time", 0.0),
                            "user_id": user_id  # Track which user executed this
                        })
                    else:
                        error_count += 1
                        error_msg = result.get("error", "Unknown error")
                        
                        logger.error("="*80)
                        logger.error("❌ [MEMORY SERVICE] TOOL EXECUTION FAILED")
                        logger.error(f"   Tool: {tool_name}")
                        logger.error(f"   Error: {error_msg}")
                        logger.error("="*80)
                        
                        outputs.append({
                            "tool": tool_name,
                            "tool_id": tool_id,
                            "success": False,
                            "error": error_msg,
                            "user_id": user_id
                        })
                        
                except Exception as e:
                    logger.error("="*80)
                    logger.error("❌ [MEMORY SERVICE] TOOL EXECUTION EXCEPTION")
                    logger.error(f"   Tool: {tool_name}")
                    logger.error(f"   Exception: {str(e)}", exc_info=True)
                    logger.error("="*80)
                    
                    error_count += 1
                    outputs.append({
                        "tool": tool_name,
                        "tool_id": tool_id,
                        "success": False,
                        "error": str(e),
                        "user_id": user_id
                    })
            
            logger.info(f"MCP Coordinator: Executed {success_count}/{len(tools_to_use)} tools for user {user_id}")
            
            # Execute resources
            executed_resources = []
            available_resources = self.mcp_client.get_user_resources(user_id, auth_token or "")
            resource_map = {r.get('resource_uri'): r for r in available_resources}
            
            for resource_plan in resources_to_use:
                resource_uri = resource_plan.get("resource_uri")
                
                if resource_uri not in resource_map:
                    logger.warning(f"MCP Coordinator: Resource '{resource_uri}' not found for user {user_id}")
                    error_count += 1
                    outputs.append({
                        "resource": resource_uri,
                        "success": False,
                        "error": f"Resource '{resource_uri}' not available"
                    })
                    continue
                
                resource_info = resource_map[resource_uri]
                resource_id = resource_info.get('id')
                server_name = resource_info.get('server_name', 'Unknown')
                server_is_active = resource_info.get('server_is_active', True)
                server_connection_status = resource_info.get('server_connection_status', 'connected')
                
                # CRITICAL: Validate server status before reading
                if not server_is_active:
                    logger.warning(f"MCP Coordinator: Server '{server_name}' is not active - skipping resource '{resource_uri}'")
                    error_count += 1
                    outputs.append({
                        "resource": resource_uri,
                        "success": False,
                        "error": f"Server '{server_name}' is not active"
                    })
                    continue
                
                if server_connection_status != 'connected':
                    logger.warning(f"MCP Coordinator: Server '{server_name}' is not connected (status: {server_connection_status}) - skipping resource '{resource_uri}'")
                    error_count += 1
                    outputs.append({
                        "resource": resource_uri,
                        "success": False,
                        "error": f"Server '{server_name}' is not connected (status: {server_connection_status})"
                    })
                    continue
                
                try:
                    result = self.mcp_client.read_resource(resource_id, auth_token)
                    if result.get("success"):
                        success_count += 1
                        executed_resources.append(resource_uri)
                        outputs.append({
                            "resource": resource_uri,
                            "resource_id": resource_id,
                            "success": True,
                            "content": result.get("content", "")
                        })
                    else:
                        error_count += 1
                        outputs.append({
                            "resource": resource_uri,
                            "success": False,
                            "error": result.get("error", "Unknown error")
                        })
                except Exception as e:
                    logger.error(f"MCP Coordinator: Resource '{resource_uri}' read failed: {str(e)}")
                    error_count += 1
                    outputs.append({
                        "resource": resource_uri,
                        "success": False,
                        "error": str(e)
                    })
            
            # Execute prompts
            executed_prompts = []
            available_prompts = self.mcp_client.get_user_prompts(user_id, auth_token or "")
            prompt_map = {p.get('prompt_name'): p for p in available_prompts}
            
            for prompt_plan in prompts_to_use:
                prompt_name = prompt_plan.get("prompt_name")
                prompt_args = prompt_plan.get("arguments", {})
                
                if prompt_name not in prompt_map:
                    logger.warning(f"MCP Coordinator: Prompt '{prompt_name}' not found for user {user_id}")
                    error_count += 1
                    outputs.append({
                        "prompt": prompt_name,
                        "success": False,
                        "error": f"Prompt '{prompt_name}' not available"
                    })
                    continue
                
                prompt_info = prompt_map[prompt_name]
                prompt_id = prompt_info.get('id')
                server_name = prompt_info.get('server_name', 'Unknown')
                server_is_active = prompt_info.get('server_is_active', True)
                server_connection_status = prompt_info.get('server_connection_status', 'connected')
                
                # CRITICAL: Validate server status before rendering
                if not server_is_active:
                    logger.warning(f"MCP Coordinator: Server '{server_name}' is not active - skipping prompt '{prompt_name}'")
                    error_count += 1
                    outputs.append({
                        "prompt": prompt_name,
                        "success": False,
                        "error": f"Server '{server_name}' is not active"
                    })
                    continue
                
                if server_connection_status != 'connected':
                    logger.warning(f"MCP Coordinator: Server '{server_name}' is not connected (status: {server_connection_status}) - skipping prompt '{prompt_name}'")
                    error_count += 1
                    outputs.append({
                        "prompt": prompt_name,
                        "success": False,
                        "error": f"Server '{server_name}' is not connected (status: {server_connection_status})"
                    })
                    continue
                
                try:
                    result = self.mcp_client.render_prompt(prompt_id, prompt_args, auth_token)
                    if result.get("success"):
                        success_count += 1
                        executed_prompts.append(prompt_name)
                        outputs.append({
                            "prompt": prompt_name,
                            "prompt_id": prompt_id,
                            "success": True,
                            "rendered_prompt": result.get("rendered_prompt", "")
                        })
                    else:
                        error_count += 1
                        outputs.append({
                            "prompt": prompt_name,
                            "success": False,
                            "error": result.get("error", "Unknown error")
                        })
                except Exception as e:
                    logger.error(f"MCP Coordinator: Prompt '{prompt_name}' render failed: {str(e)}")
                    error_count += 1
                    outputs.append({
                        "prompt": prompt_name,
                        "success": False,
                        "error": str(e)
                    })
            
            logger.info(f"MCP Coordinator: Executed {len(executed_tools)} tools, {len(executed_resources)} resources, {len(executed_prompts)} prompts for user {user_id}")
            
            return {
                "tools_used": executed_tools,
                "resources_used": executed_resources,
                "prompts_used": executed_prompts,
                "outputs": outputs,
                "success_count": success_count,
                "error_count": error_count,
                "total_capabilities": len(tools_to_use) + len(resources_to_use) + len(prompts_to_use),
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"MCP Coordinator execution failed: {str(e)}")
            return {
                "tools_used": [],
                "outputs": [],
                "success_count": 0,
                "error_count": 0,
                "error": str(e)
            }
    
    def _validate_and_enrich_arguments(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        tool_map: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate and enrich tool arguments against input schema.
        
        Args:
            tool_name: Name of the tool
            arguments: Current arguments
            tool_map: Map of tool names to tool info
            
        Returns:
            Validated and enriched arguments
        """
        tool_info = tool_map.get(tool_name)
        if not tool_info:
            return arguments
        
        input_schema = tool_info.get("input_schema", {})
        if not isinstance(input_schema, dict):
            return arguments
        
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        validated_args = {}
        
        # Validate existing arguments
        for param_name, param_value in arguments.items():
            if param_name in properties:
                param_info = properties[param_name]
                param_type = param_info.get("type", "string")
                
                # Type conversion if needed
                if param_type == "number" and not isinstance(param_value, (int, float)):
                    try:
                        validated_args[param_name] = float(param_value)
                    except (ValueError, TypeError):
                        validated_args[param_name] = param_value
                elif param_type == "boolean" and not isinstance(param_value, bool):
                    if isinstance(param_value, str):
                        validated_args[param_name] = param_value.lower() in ("true", "1", "yes")
                    else:
                        validated_args[param_name] = param_value
                else:
                    validated_args[param_name] = param_value
            else:
                # Unknown parameter - include it anyway (tool might accept extra params)
                validated_args[param_name] = param_value
        
        # Check for missing required parameters
        missing_required = [p for p in required if p not in validated_args or validated_args[p] is None]
        if missing_required:
            logger.warning(f"Tool '{tool_name}' missing required parameters: {missing_required}")
            # Don't fail - let the tool execution handle it
        
        return validated_args
    
    def _fuzzy_match_tool_name(
        self,
        query_name: str,
        available_names: List[str],
        threshold: float = 0.6
    ) -> List[str]:
        """
        Find tool names similar to query using fuzzy string matching.
        
        Args:
            query_name: Tool name from query
            available_names: List of available tool names
            threshold: Minimum similarity ratio (0-1)
            
        Returns:
            List of matching tool names sorted by similarity (best first)
        """
        # Use difflib for fuzzy matching
        matches = difflib.get_close_matches(
            query_name,
            available_names,
            n=3,  # Return top 3 matches
            cutoff=threshold
        )
        
        return matches
    
    def _get_tool_suggestions(
        self,
        query_name: str,
        available_names: List[str]
    ) -> List[str]:
        """
        Get tool name suggestions for a query that didn't match.
        
        Args:
            query_name: Tool name from query
            available_names: List of available tool names
            
        Returns:
            List of suggested tool names
        """
        # Try fuzzy matching with lower threshold for suggestions
        suggestions = self._fuzzy_match_tool_name(
            query_name,
            available_names,
            threshold=0.4  # Lower threshold for suggestions
        )
        
        # If no fuzzy matches, try semantic matching based on keywords
        if not suggestions:
            query_keywords = set(query_name.lower().replace('_', ' ').split())
            
            scored_tools = []
            for tool_name in available_names:
                tool_keywords = set(tool_name.lower().replace('_', ' ').split())
                # Calculate keyword overlap
                overlap = len(query_keywords & tool_keywords)
                if overlap > 0:
                    scored_tools.append((tool_name, overlap))
            
            # Sort by overlap score
            scored_tools.sort(key=lambda x: x[1], reverse=True)
            suggestions = [name for name, score in scored_tools[:3]]
        
        return suggestions

