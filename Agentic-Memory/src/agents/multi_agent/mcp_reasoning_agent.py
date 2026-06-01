"""
MCP Reasoning Agent

Thinks deeply about what MCP tools, resources, and prompts are needed
to solve the user's intent. Analyzes available capabilities and matches
them intelligently to user needs.
"""
import logging
from typing import Dict, Any, Optional, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama

from src.agents.base_agent import BaseAgent
from src.utils.toon_format import format_system_instruction
from src.utils.agent_logger import get_agent_logger
from src.agents.utils.argument_parser import get_argument_parser

logger = get_agent_logger("mcp_reasoning")


class MCPReasoningAgent(BaseAgent):
    """
    Agent that reasons about which MCP capabilities are needed for user intent.
    
    This agent:
    1. Understands what each tool/resource/prompt does
    2. Analyzes user intent deeply
    3. Matches capabilities to intent
    4. Plans tool execution strategy
    """
    
    def __init__(
        self,
        model_name: str = "qwen2.5:7b",
        temperature: float = 0.1,
        **kwargs
    ):
        """Initialize the MCP Reasoning Agent."""
        system_instruction = self._create_system_instruction()
        
        super().__init__(
            agent_name="mcp_reasoning",
            model_name=model_name,
            temperature=temperature,
            system_prompt=system_instruction,
            **kwargs
        )
    
    def _create_system_instruction(self) -> str:
        """Create structured system instruction using TOON format."""
        instruction_data = {
            "role": "MCP Reasoning Agent",
            "purpose": "Think deeply about which MCP tools, resources, and prompts are needed to solve user intent",
            "capabilities": [
                "Deep intent analysis",
                "Tool capability understanding",
                "Semantic matching of tools to intent",
                "Execution planning",
                "Context extraction planning"
            ],
            "reasoning_process": {
                "step1": "Understand user intent - what is the user really trying to accomplish?",
                "step2": "Analyze available tools - what does each tool do? What problems does it solve?",
                "step3": "Match tools to intent - which tools can help accomplish the user's goal?",
                "step4": "Plan execution - what order should tools be executed? What arguments are needed?",
                "step5": "Consider context - what information from tool results will be needed for the response?"
            },
            "output_format": {
                "reasoning": "string - detailed reasoning about tool selection",
                "selected_tools": "array - tools to execute with arguments and reasoning",
                "selected_resources": "array - resources to read with reasoning",
                "selected_prompts": "array - prompts to render with reasoning",
                "execution_plan": "object - order and dependencies",
                "expected_context": "string - what context will be extracted from tool results"
            }
        }
        
        return format_system_instruction(instruction_data)
    
    def reason_about_tools(
        self,
        query: str,
        available_capabilities: Dict[str, Any],
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Reason about which tools are needed to solve the user's query.
        
        Args:
            query: User query
            available_capabilities: Dict with tools, resources, prompts
            context: Additional context
            
        Returns:
            Reasoning result with selected tools and execution plan
        """
        import json
        import re
        
        try:
            # Safely extract capabilities (handle missing types gracefully)
            tools = available_capabilities.get("tools", []) if available_capabilities else []
            resources = available_capabilities.get("resources", []) if available_capabilities else []
            prompts = available_capabilities.get("prompts", []) if available_capabilities else []
            
            # Ensure we have lists (defensive check)
            if not isinstance(tools, list):
                logger.warning(f"Tools is not a list: {type(tools)}, converting to empty list")
                tools = []
            if not isinstance(resources, list):
                logger.warning(f"Resources is not a list: {type(resources)}, converting to empty list")
                resources = []
            if not isinstance(prompts, list):
                logger.warning(f"Prompts is not a list: {type(prompts)}, converting to empty list")
                prompts = []
            
            # Build detailed capability descriptions
            capabilities_text = self._format_capabilities_for_reasoning(tools, resources, prompts)
            
            # OPTIMIZED: More concise prompt for faster inference
            reasoning_prompt = f"""Query: {query}
Context: {context if context else 'None'}

Available MCP Tools/Resources/Prompts:
{capabilities_text}

ANALYZE & SELECT:
1. Intent: What does user want? (action verbs, entities, goal)
2. Match: Which tools match the intent? (semantic, not keyword)
3. Args: Extract required parameters from query
4. Validate: Will this accomplish the goal?

RULES:
✓ Match tool PURPOSE to query INTENT
✓ Extract ALL required parameters
✓ Empty selection better than wrong selection
✗ Don't force selection if no good match

JSON OUTPUT:
{{
  "reasoning": "brief explanation",
  "selected_tools": [{{"tool_name": "name", "arguments": {{}}, "reason": "why", "confidence": 0.9}}],
  "selected_resources": [{{"resource_uri": "uri", "reason": "why"}}],
  "selected_prompts": [{{"prompt_name": "name", "arguments": {{}}, "reason": "why"}}]
}}"""
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=reasoning_prompt)
            ]
            
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            # Parse JSON response
            try:
                json_match = None
                
                # Look for JSON in markdown code blocks
                json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_block_match:
                    json_match = json_block_match.group(1)
                else:
                    # Look for JSON object directly
                    json_obj_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_obj_match:
                        json_match = json_obj_match.group(0)
                
                if json_match:
                    reasoning_result = json.loads(json_match)
                else:
                    reasoning_result = json.loads(response_text)
                
                # Ensure required fields
                reasoning_result.setdefault("reasoning", "Tool selection reasoning")
                reasoning_result.setdefault("selected_tools", [])
                reasoning_result.setdefault("selected_resources", [])
                reasoning_result.setdefault("selected_prompts", [])
                reasoning_result.setdefault("execution_plan", {"order": [], "dependencies": {}, "parallel": []})
                reasoning_result.setdefault("expected_context", "")
                
                # Enrich and validate tool arguments using argument parser
                if reasoning_result.get("selected_tools"):
                    reasoning_result["selected_tools"] = self._enrich_tool_arguments_with_parser(
                        reasoning_result["selected_tools"],
                        query,
                        tools
                    )
                
                logger.info(f"MCP Reasoning: Selected {len(reasoning_result['selected_tools'])} tools, "
                          f"{len(reasoning_result['selected_resources'])} resources, "
                          f"{len(reasoning_result['selected_prompts'])} prompts")
                
                return reasoning_result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse reasoning JSON: {e}")
                logger.debug(f"Response text: {response_text[:500]}")
                
                # Fallback: return empty selection
                return {
                    "reasoning": f"JSON parsing failed: {str(e)}",
                    "selected_tools": [],
                    "selected_resources": [],
                    "selected_prompts": [],
                    "execution_plan": {"order": [], "dependencies": {}, "parallel": []},
                    "expected_context": ""
                }
                
        except Exception as e:
            logger.error(f"MCP reasoning failed: {str(e)}")
            return {
                "reasoning": f"Reasoning error: {str(e)}",
                "selected_tools": [],
                "selected_resources": [],
                "selected_prompts": [],
                "execution_plan": {"order": [], "dependencies": {}, "parallel": []},
                "expected_context": "",
                "error": str(e)
            }
    
    def _format_capabilities_for_reasoning(
        self,
        tools: List[Dict[str, Any]],
        resources: List[Dict[str, Any]],
        prompts: List[Dict[str, Any]]
    ) -> str:
        """
        Format capabilities in a way that helps the agent reason about them.
        
        Args:
            tools: List of tool definitions (may be empty)
            resources: List of resource definitions (may be empty)
            prompts: List of prompt definitions (may be empty)
            
        Returns:
            Formatted string with capability descriptions
        """
        formatted = []
        
        # Handle tools (may be empty list)
        if tools and len(tools) > 0:
            formatted.append(f"\n=== TOOLS ({len(tools)} available) ===")
            formatted.append("Tools are callable functions that perform actions or retrieve information.")
            formatted.append("Match the ACTION in the user query to the tool's PURPOSE.\n")
            
            for tool in tools[:30]:  # Limit to 30 for prompt size
                if isinstance(tool, dict):
                    tool_name = tool.get("tool_name", "Unknown")
                    tool_desc = tool.get("description", "No description")
                    server_name = tool.get("server_name", "Unknown")
                    input_schema = tool.get("input_schema", {})
                    
                    formatted.append(f"\nTool: {tool_name}")
                    formatted.append(f"  Server: {server_name}")
                    formatted.append(f"  Purpose: {tool_desc}")
                    
                    # Add input schema details
                    if isinstance(input_schema, dict):
                        properties = input_schema.get("properties", {})
                        required = input_schema.get("required", [])
                        
                        if properties:
                            formatted.append(f"  Inputs:")
                            for param_name, param_info in properties.items():
                                if isinstance(param_info, dict):
                                    param_type = param_info.get("type", "string")
                                    param_desc = param_info.get("description", "")
                                    is_required = param_name in required
                                    req_marker = " (REQUIRED)" if is_required else " (optional)"
                                    formatted.append(f"    - {param_name} ({param_type}){req_marker}: {param_desc}")
        else:
            formatted.append("\n=== TOOLS ===")
            formatted.append("No tools available from MCP servers.")
        
        # Handle resources (may be empty list)
        if resources and len(resources) > 0:
            formatted.append(f"\n=== RESOURCES ({len(resources)} available) ===")
            formatted.append("Resources are data sources that can be read (files, databases, etc.).")
            formatted.append("Use resources when the user needs to READ or ACCESS data.\n")
            
            for resource in resources[:20]:
                if isinstance(resource, dict):
                    res_name = resource.get("resource_name", "Unknown")
                    res_uri = resource.get("resource_uri", "")
                    res_desc = resource.get("description", "No description")
                    server_name = resource.get("server_name", "Unknown")
                    
                    formatted.append(f"\nResource: {res_name}")
                    formatted.append(f"  URI: {res_uri}")
                    formatted.append(f"  Server: {server_name}")
                    formatted.append(f"  Purpose: {res_desc}")
        else:
            formatted.append("\n=== RESOURCES ===")
            formatted.append("No resources available from MCP servers.")
        
        # Handle prompts (may be empty list)
        if prompts and len(prompts) > 0:
            formatted.append(f"\n=== PROMPTS ({len(prompts)} available) ===")
            formatted.append("Prompts are templates that generate text based on arguments.")
            formatted.append("Use prompts when the user needs GENERATED or TEMPLATED content.\n")
            
            for prompt in prompts[:20]:
                if isinstance(prompt, dict):
                    prompt_name = prompt.get("prompt_name", "Unknown")
                    prompt_desc = prompt.get("description", "No description")
                    server_name = prompt.get("server_name", "Unknown")
                    arguments = prompt.get("arguments", [])
                    
                    formatted.append(f"\nPrompt: {prompt_name}")
                    formatted.append(f"  Server: {server_name}")
                    formatted.append(f"  Purpose: {prompt_desc}")
                    if arguments:
                        formatted.append(f"  Arguments: {', '.join([arg.get('name', '') for arg in arguments if isinstance(arg, dict)])}")
        else:
            formatted.append("\n=== PROMPTS ===")
            formatted.append("No prompts available from MCP servers.")
        
        # Add summary
        total_capabilities = len(tools or []) + len(resources or []) + len(prompts or [])
        formatted.append(f"\n=== SUMMARY ===")
        formatted.append(f"Total capabilities available: {total_capabilities}")
        formatted.append(f"  - Tools: {len(tools or [])}")
        formatted.append(f"  - Resources: {len(resources or [])}")
        formatted.append(f"  - Prompts: {len(prompts or [])}")
        formatted.append("\nNOTE: Some MCP servers may only provide tools, only resources, only prompts, or any combination.")
        formatted.append("Only select capabilities that actually match the user's intent.")
        
        return "\n".join(formatted)
    
    def _enrich_tool_arguments_with_parser(
        self,
        tool_plans: List[Dict[str, Any]],
        query: str,
        available_tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrich tool arguments using LLM-based argument parser for better accuracy.
        
        Args:
            tool_plans: List of tool execution plans from reasoning
            query: Original user query
            available_tools: List of available tool definitions
            
        Returns:
            Enriched tool plans with validated and extracted arguments
        """
        tool_map = {tool.get("tool_name"): tool for tool in available_tools if isinstance(tool, dict)}
        enriched_plans = []
        
        # Get argument parser instance
        arg_parser = get_argument_parser(self.llm)
        
        for plan in tool_plans:
            tool_name = plan.get("tool_name")
            if not tool_name:
                continue
            
            tool_info = tool_map.get(tool_name)
            if not tool_info:
                logger.warning(f"Tool '{tool_name}' not found in available tools")
                enriched_plans.append(plan)
                continue
            
            # Get input schema
            input_schema = tool_info.get("input_schema", {})
            if not isinstance(input_schema, dict):
                logger.debug(f"Tool '{tool_name}' has no input schema")
                enriched_plans.append(plan)
                continue
            
            # Get existing arguments from reasoning
            reasoning_arguments = plan.get("arguments", {})
            if not isinstance(reasoning_arguments, dict):
                reasoning_arguments = {}
            
            # Use argument parser to extract/validate arguments
            parsed_arguments, warnings = arg_parser.extract_arguments_from_query(
                query=query,
                tool_name=tool_name,
                tool_schema=input_schema
            )
            
            # Merge reasoning arguments with parsed arguments (reasoning takes precedence)
            final_arguments = {**parsed_arguments, **reasoning_arguments}
            
            # Enrich with defaults
            final_arguments = arg_parser.enrich_arguments_with_defaults(
                final_arguments,
                input_schema
            )
            
            # Attempt type coercion
            final_arguments = arg_parser.coerce_types(
                final_arguments,
                input_schema
            )
            
            # Validate final arguments
            is_valid, errors = arg_parser.validate_arguments(
                final_arguments,
                input_schema
            )
            
            # Log validation results
            if not is_valid:
                logger.warning(f"Tool '{tool_name}' has validation errors: {errors}")
                plan["validation_errors"] = errors
                
                # Add suggestions
                suggestions = arg_parser.suggest_argument_fixes(
                    final_arguments,
                    input_schema,
                    errors
                )
                if suggestions:
                    plan["argument_suggestions"] = suggestions
            else:
                logger.info(f"Tool '{tool_name}' arguments validated successfully")
            
            # Add warnings from parser
            if warnings:
                plan["warnings"] = warnings
            
            # Update plan with final arguments
            plan["arguments"] = final_arguments
            enriched_plans.append(plan)
        
        return enriched_plans
    
    def _enrich_tool_arguments(
        self,
        tool_plans: List[Dict[str, Any]],
        query: str,
        available_tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Fallback: Regex-based argument enrichment (legacy method).
        
        This method is kept as a fallback but _enrich_tool_arguments_with_parser
        should be preferred for better accuracy.
        """
        import re
        
        tool_map = {tool.get("tool_name"): tool for tool in available_tools if isinstance(tool, dict)}
        enriched_plans = []
        
        for plan in tool_plans:
            tool_name = plan.get("tool_name")
            if not tool_name:
                continue
            
            tool_info = tool_map.get(tool_name)
            if not tool_info:
                enriched_plans.append(plan)
                continue
            
            input_schema = tool_info.get("input_schema", {})
            if not isinstance(input_schema, dict):
                enriched_plans.append(plan)
                continue
            
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])
            
            arguments = plan.get("arguments", {})
            if not isinstance(arguments, dict):
                arguments = {}
            
            query_lower = query.lower()
            
            for param_name, param_info in properties.items():
                if isinstance(param_info, dict):
                    param_desc = param_info.get("description", "").lower()
                    is_required = param_name in required
                    
                    if param_name not in arguments or not arguments[param_name]:
                        extracted_value = None
                        
                        if param_name.lower() in query_lower:
                            pattern = rf"{re.escape(param_name)}\s*[:=]?\s*([^\s,]+)"
                            match = re.search(pattern, query, re.IGNORECASE)
                            if match:
                                extracted_value = match.group(1).strip('"\'')
                        
                        if not extracted_value and param_desc:
                            if "url" in param_desc or "uri" in param_desc:
                                url_pattern = r'https?://[^\s]+|www\.[^\s]+'
                                match = re.search(url_pattern, query)
                                if match:
                                    extracted_value = match.group(0)
                            elif "path" in param_desc or "file" in param_desc:
                                path_pattern = r'[/\\][^\s]+|\.\w+'
                                match = re.search(path_pattern, query)
                                if match:
                                    extracted_value = match.group(0)
                        
                        if extracted_value:
                            arguments[param_name] = extracted_value
                            logger.info(f"Extracted argument '{param_name}'='{extracted_value}' from query for tool '{tool_name}'")
            
            missing_required = [p for p in required if p not in arguments or not arguments[p]]
            if missing_required:
                logger.warning(f"Tool '{tool_name}' missing required parameters: {missing_required}")
                plan["reason"] = plan.get("reason", "") + f" (Warning: Missing required params: {missing_required})"
            
            plan["arguments"] = arguments
            enriched_plans.append(plan)
        
        return enriched_plans

