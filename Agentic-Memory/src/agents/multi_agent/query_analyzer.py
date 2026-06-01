"""
Query Analysis Agent

Analyzes user queries to determine which agents and tools should be used.
Uses TOON format for structured system instructions.
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama

from src.agents.base_agent import BaseAgent
from src.utils.toon_format import format_system_instruction
from src.utils.agent_logger import get_agent_logger

logger = get_agent_logger("query_analyzer")


class QueryAnalysisAgent(BaseAgent):
    """
    Agent that analyzes queries and determines routing strategy.
    """
    
    def __init__(
        self,
        model_name: str = "qwen2.5:7b",
        temperature: float = 0.1,
        mcp_capabilities: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize the Query Analysis Agent.
        
        Args:
            model_name: LLM model name
            temperature: Temperature for LLM
            mcp_capabilities: Optional dict with available MCP tools, resources, prompts
            **kwargs: Additional arguments
        """
        # Create TOON-formatted system instruction with dynamic MCP capabilities
        system_instruction = self._create_system_instruction(mcp_capabilities)
        
        super().__init__(
            agent_name="query_analyzer",
            model_name=model_name,
            temperature=temperature,
            system_prompt=system_instruction,
            **kwargs
        )
        
        self.mcp_capabilities = mcp_capabilities
    
    def _create_system_instruction(self, mcp_capabilities: Optional[Dict[str, Any]] = None) -> str:
        """
        Create structured system instruction using TOON format.
        
        Args:
            mcp_capabilities: Optional dict with tools, resources, and prompts available
        """
        instruction_data = {
            "role": "Query Analysis Agent",
            "purpose": "Analyze user queries and intelligently determine which agents, tools, resources, and prompts to use",
            "capabilities": [
                "Query intent classification",
                "Dynamic tool/resource/prompt selection",
                "Routing decision making",
                "Intelligent plan generation"
            ],
            "analysis_criteria": {
                "graphrag_indicators": [
                    "Questions about documents or knowledge base",
                    "Technical queries requiring domain expertise",
                    "Company policies or procedures",
                    "Research-related questions"
                ],
                "mcp_indicators": [
                    "External API calls needed",
                    "File system operations",
                    "Database queries",
                    "Custom tool execution",
                    "Data retrieval from resources",
                    "Prompt template rendering needed"
                ],
                "direct_response_indicators": [
                    "General conversation",
                    "Simple questions",
                    "Greetings",
                    "Opinion requests"
                ]
            },
            "output_format": {
                "needs_graphrag": "boolean",
                "needs_mcp": "boolean",
                "confidence": "float 0-1",
                "reasoning": "string",
                "plan": "object with agent execution order",
                "mcp_tools": "array of tool execution plans with tool_name and arguments",
                "mcp_resources": "array of resource access plans with resource_uri",
                "mcp_prompts": "array of prompt rendering plans with prompt_name and arguments"
            },
            "dynamic_mcp_selection": {
                "principle": "Select MCP capabilities based on query intent and available capabilities",
                "tool_selection": "Choose tools whose descriptions/names match the query intent",
                "resource_selection": "Choose resources that can provide relevant data for the query",
                "prompt_selection": "Choose prompts that can help structure or format the response",
                "reasoning_required": "Always explain why each MCP capability was selected"
            }
        }
        
        # Dynamically add available MCP capabilities if provided
        if mcp_capabilities:
            # Safely extract lists, ensuring they're actually lists
            available_tools = mcp_capabilities.get("tools", [])
            available_resources = mcp_capabilities.get("resources", [])
            available_prompts = mcp_capabilities.get("prompts", [])
            
            # Ensure we have lists, not integers or other types
            if not isinstance(available_tools, list):
                logger.warning(f"Expected tools to be a list, got {type(available_tools)}: {available_tools}")
                available_tools = []
            if not isinstance(available_resources, list):
                logger.warning(f"Expected resources to be a list, got {type(available_resources)}: {available_resources}")
                available_resources = []
            if not isinstance(available_prompts, list):
                logger.warning(f"Expected prompts to be a list, got {type(available_prompts)}: {available_prompts}")
                available_prompts = []
            
            # Format tools for the agent with detailed schema information
            formatted_tools = []
            for tool in available_tools[:50]:  # Limit to 50 to avoid token overflow
                if isinstance(tool, dict):
                    input_schema = tool.get("input_schema", {})
                    properties = input_schema.get("properties", {}) if isinstance(input_schema, dict) else {}
                    required = input_schema.get("required", []) if isinstance(input_schema, dict) else []
                    
                    # Format parameters with types and requirements
                    formatted_params = {}
                    for param_name, param_info in properties.items():
                        if isinstance(param_info, dict):
                            param_type = param_info.get("type", "string")
                            param_desc = param_info.get("description", "")
                            is_required = param_name in required
                            formatted_params[param_name] = {
                                "type": param_type,
                                "description": param_desc,
                                "required": is_required
                            }
                    
                    formatted_tools.append({
                        "name": tool.get("tool_name", "Unknown"),
                        "description": tool.get("description", ""),
                        "parameters": formatted_params,
                        "required_parameters": required,
                        "server": tool.get("server_name", "Unknown")
                    })
            
            # Format resources for the agent
            formatted_resources = []
            for resource in available_resources[:50]:
                if isinstance(resource, dict):
                    formatted_resources.append({
                        "uri": resource.get("resource_uri", ""),
                        "name": resource.get("resource_name", "Unknown"),
                        "description": resource.get("description", ""),
                        "type": resource.get("resource_type", ""),
                        "server": resource.get("server_name", "Unknown")
                    })
            
            # Format prompts for the agent
            formatted_prompts = []
            for prompt in available_prompts[:50]:
                if isinstance(prompt, dict):
                    formatted_prompts.append({
                        "name": prompt.get("prompt_name", "Unknown"),
                        "description": prompt.get("description", ""),
                        "arguments": prompt.get("arguments", {}),
                        "server": prompt.get("server_name", "Unknown")
                    })
            
            # Ensure formatted lists are actually lists before calculating total_count
            safe_formatted_tools = formatted_tools if isinstance(formatted_tools, list) else []
            safe_formatted_resources = formatted_resources if isinstance(formatted_resources, list) else []
            safe_formatted_prompts = formatted_prompts if isinstance(formatted_prompts, list) else []
            
            instruction_data["available_mcp_capabilities"] = {
                "tools": safe_formatted_tools,
                "resources": safe_formatted_resources,
                "prompts": safe_formatted_prompts,
                "total_count": len(safe_formatted_tools) + len(safe_formatted_resources) + len(safe_formatted_prompts)
            }
            instruction_data["dynamic_mcp_selection"]["note"] = (
                f"Use the available MCP capabilities listed above to intelligently select "
                f"which tools, resources, or prompts can help answer the user's query. "
                f"Match query intent with capability descriptions and names."
            )
        else:
            instruction_data["available_mcp_capabilities"] = {
                "tools": [],
                "resources": [],
                "prompts": [],
                "note": "MCP capabilities will be discovered dynamically when needed"
            }
        
        return format_system_instruction(instruction_data)
    
    def analyze(
        self,
        query: str,
        context: str = "",
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Analyze a query and determine routing strategy.
        
        Args:
            query: User query
            context: Additional context
            user_id: User identifier
            
        Returns:
            Analysis result with routing decisions
        """
        import json
        import re
        
        try:
            # Build dynamic prompt with available MCP capabilities
            mcp_info = ""
            if self.mcp_capabilities:
                # Safely extract and validate MCP capabilities
                # Handle case where Django API might return unexpected structure
                tools = self.mcp_capabilities.get("tools", [])
                resources = self.mcp_capabilities.get("resources", [])
                prompts = self.mcp_capabilities.get("prompts", [])
                
                # Ensure we have lists - defensive check for any non-list types
                if not isinstance(tools, list):
                    logger.warning(f"mcp_capabilities.tools is not a list (type: {type(tools)}, value: {tools}), converting to empty list")
                    tools = []
                if not isinstance(resources, list):
                    logger.warning(f"mcp_capabilities.resources is not a list (type: {type(resources)}, value: {resources}), converting to empty list")
                    resources = []
                if not isinstance(prompts, list):
                    logger.warning(f"mcp_capabilities.prompts is not a list (type: {type(prompts)}, value: {prompts}), converting to empty list")
                    prompts = []
                
                if tools or resources or prompts:
                    mcp_info = "\n\nAvailable MCP Capabilities:\n"
                    
                    if tools:
                        # Additional safety check before len()
                        try:
                            tools_count = len(tools) if isinstance(tools, list) else 0
                            mcp_info += f"\nTools ({tools_count} available):\n"
                        except (TypeError, AttributeError) as e:
                            logger.error(f"Error getting tools count: {e}, tools type: {type(tools)}")
                            mcp_info += f"\nTools (available):\n"
                        for tool in tools[:20]:  # Limit to 20 for prompt size
                            if isinstance(tool, dict):
                                tool_name = tool.get("tool_name", "Unknown")
                                tool_desc = tool.get("description", "No description")
                                input_schema = tool.get("input_schema", {})
                                
                                mcp_info += f"- {tool_name}: {tool_desc}\n"
                                
                                # Format input schema details
                                if isinstance(input_schema, dict):
                                    properties = input_schema.get("properties", {})
                                    required = input_schema.get("required", [])
                                    
                                    if properties:
                                        mcp_info += "  Input Parameters:\n"
                                        for param_name, param_info in properties.items():
                                            if isinstance(param_info, dict):
                                                param_type = param_info.get("type", "string")
                                                param_desc = param_info.get("description", "")
                                                is_required = param_name in required
                                                required_marker = " (required)" if is_required else " (optional)"
                                                mcp_info += f"    - {param_name} ({param_type}){required_marker}"
                                                if param_desc:
                                                    mcp_info += f": {param_desc}"
                                                mcp_info += "\n"
                    
                    if resources:
                        # Additional safety check before len()
                        try:
                            resources_count = len(resources) if isinstance(resources, list) else 0
                            mcp_info += f"\nResources ({resources_count} available):\n"
                        except (TypeError, AttributeError) as e:
                            logger.error(f"Error getting resources count: {e}, resources type: {type(resources)}")
                            mcp_info += f"\nResources (available):\n"
                        for resource in resources[:20]:
                            if isinstance(resource, dict):
                                res_name = resource.get("resource_name", "Unknown")
                                res_uri = resource.get("resource_uri", "")
                                res_desc = resource.get("description", "No description")
                                mcp_info += f"- {res_name} ({res_uri}): {res_desc}\n"
                    
                    if prompts:
                        # Additional safety check before len()
                        try:
                            prompts_count = len(prompts) if isinstance(prompts, list) else 0
                            mcp_info += f"\nPrompts ({prompts_count} available):\n"
                        except (TypeError, AttributeError) as e:
                            logger.error(f"Error getting prompts count: {e}, prompts type: {type(prompts)}")
                            mcp_info += f"\nPrompts (available):\n"
                        for prompt in prompts[:20]:
                            if isinstance(prompt, dict):
                                prompt_name = prompt.get("prompt_name", "Unknown")
                                prompt_desc = prompt.get("description", "No description")
                                mcp_info += f"- {prompt_name}: {prompt_desc}\n"
                    
                    mcp_info += "\n\nCRITICAL: When selecting tools, you MUST use the EXACT tool names listed above. Do NOT invent or modify tool names."
                    mcp_info += "\nAvailable tool names are: " + ", ".join([t.get("tool_name", "") for t in tools[:20] if isinstance(t, dict)])
                    mcp_info += "\nSelect the most relevant MCP capabilities based on the query. Match query intent with capability descriptions."
            
            prompt = f"""Analyze the following query and intelligently determine which agents, tools, resources, and prompts should be used.

Query: {query}
Context: {context if context else "None"}{mcp_info}

⚠️ CRITICAL DECISION PRIORITY - READ THIS FIRST ⚠️

DECISION PRIORITY ORDER (MOST IMPORTANT):
1. FIRST: Determine if this is a KNOWLEDGE BASE / INFORMATION query (needs_graphrag)
   ✅ Questions asking for INFORMATION, FACTS, POLICIES, PROCEDURES, DOCUMENTATION → needs_graphrag=true
   ✅ Query patterns: questions starting with "what", "how many", "how much", "tell me", "explain", "describe"
   ✅ Content types: policies, procedures, rules, documentation, facts, definitions, explanations
   ✅ Intent: User wants to RETRIEVE or LEARN information from stored knowledge
   ✅ GraphRAG searches the knowledge base for stored information
   ⚠️ DO NOT use MCP tools for simple information queries - use GraphRAG instead

2. SECOND: Determine if this needs MCP TOOLS for ACTIONS (needs_mcp)
   ✅ Actions that require external tools: save, create, update, delete, execute, navigate, call APIs, etc.
   ✅ Query patterns: commands/requests to perform actions, modify data, interact with external systems
   ✅ Content types: operations, transactions, system interactions, data modifications
   ✅ Intent: User wants to PERFORM an ACTION or EXECUTE an operation using external tools
   ✅ Only set needs_mcp=true if you can identify SPECIFIC tools that match the intent
   ✅ If MCP capabilities are listed above, intelligently match them to the query intent
   ⚠️ DO NOT set needs_mcp=true for information queries - those need GraphRAG

3. BOTH can be true: Some queries need BOTH knowledge base search AND tool execution
   ✅ Pattern: Information retrieval followed by action (e.g., "find policy X and save it to system Y")
   ✅ Set both needs_graphrag=true AND needs_mcp=true when query has both information and action components

CRITICAL: Use semantic understanding to detect user intent. Consider various phrasings and natural language patterns.
Analyze the QUERY INTENT, not just keywords - understand what the user is really trying to accomplish.

Provide your analysis in JSON format with:
- needs_graphrag: boolean (true if knowledge base search needed - for information/facts/policies)
- needs_mcp: boolean (true if MCP tools/resources/prompts needed - for actions/operations)
- confidence: float (confidence in analysis, 0-1)
- reasoning: string (explanation of decision, including why GraphRAG or MCP capabilities were selected)
- plan: object with execution plan
- mcp_tools: array of MCP tool execution plans with tool_name, arguments, and reason (only if needs_mcp=true)
- mcp_resources: array of MCP resource access plans with resource_uri and reason (only if needs_mcp=true)
- mcp_prompts: array of MCP prompt rendering plans with prompt_name, arguments, and reason (only if needs_mcp=true)

CRITICAL INSTRUCTIONS:
- Return ONLY valid JSON, no markdown, no explanations, just the JSON object.
- ANALYZE USER INTENT DEEPLY: What is the user really trying to accomplish?
  * Information retrieval (asking questions, seeking facts, learning) → needs_graphrag=true
  * Action execution (performing operations, modifying data, interacting with systems) → needs_mcp=true
  * Both information and action → needs_graphrag=true AND needs_mcp=true
- INTENT-BASED DECISION: Focus on the INTENT behind the query, not just keywords
  * Questions seeking information → GraphRAG
  * Commands requesting actions → MCP tools
  * Mixed queries → Both GraphRAG and MCP
- UNDERSTAND TOOL CAPABILITIES: Read each tool's description and input schema carefully. What does each tool do? What problems does it solve?
- MATCH TOOLS TO INTENT: Select tools whose purpose aligns with the user's intent. Think about what information each tool will provide.
- If needs_mcp=true, you MUST select at least one tool from the available MCP capabilities listed above.
- DO NOT set needs_mcp=true without selecting tools - if you detect MCP is needed, you must choose specific tools.
- DO NOT set needs_mcp=true for simple information queries - use GraphRAG instead
- For tool discovery queries (is_tool_discovery=true), set mcp_tools with list_tools tool and empty arguments
- TOOL NAME REQUIREMENT: You MUST use the EXACT tool name from the list above. Do NOT invent, modify, or guess tool names. Check the "Available tool names are:" list.
- When selecting tools, you MUST provide the correct arguments based on the tool's input schema:
  * Check the "Input Parameters" section for each tool to see required and optional parameters
  * Required parameters MUST be included in the arguments object
  * Optional parameters can be included if relevant to the query
  * Parameter types must match (string, number, boolean, object, array)
  * Extract parameter values from the user query or use reasonable defaults
  * Think about what values make sense for each parameter given the user's intent
- For each selected tool, provide a clear "reason" explaining why this tool is needed and what information it will provide
- Use semantic understanding, not just keyword matching - detect intent even with varied phrasings
- Consider tool dependencies - some tools may need to be executed in a specific order

Response format patterns (use these as guidance, adapt to actual query):

For information/knowledge queries:
- needs_graphrag: true
- needs_mcp: false
- Include reasoning explaining why knowledge base search is needed
- Set plan with graphrag agent in order

For tool discovery queries:
- needs_graphrag: false
- needs_mcp: true
- is_tool_discovery: true
- Include list_tools in mcp_tools with empty arguments
- Include reasoning explaining discovery intent

For action/operation queries requiring tool execution:
- Set needs_graphrag=false, needs_mcp=true
- Include specific tools in mcp_tools array with extracted arguments matching input schema
- Include reasoning explaining tool selection and how arguments were extracted from query
- Ensure all required parameters are included in arguments object

IMPORTANT: When constructing arguments:
- Check the tool's Input Parameters section above
- Include ALL required parameters
- Use values extracted from the user query when possible
- For optional parameters, only include if relevant
- Ensure parameter types match the schema (string, number, boolean, etc.)
- If a required parameter value cannot be determined, still include it but note in reason field"""
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            # Parse JSON response with improved extraction
            try:
                # Try to find JSON object in the response
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
                    analysis = json.loads(json_match)
                else:
                    # If no JSON found, try parsing the whole response
                    analysis = json.loads(response_text)
                
                # Ensure required fields
                analysis.setdefault("needs_graphrag", False)
                analysis.setdefault("needs_mcp", False)
                analysis.setdefault("confidence", 0.5)
                analysis.setdefault("reasoning", "Analysis completed")
                analysis.setdefault("plan", {"agents": [], "order": []})
                analysis.setdefault("mcp_tools", [])
                analysis.setdefault("mcp_resources", [])
                analysis.setdefault("mcp_prompts", [])
                
                # Handle tool discovery queries dynamically (if user asks to list tools)
                query_lower = query.lower()
                discovery_keywords = ["list tools", "available tools", "what tools", "show tools", "what can you do", "capabilities"]
                server_listing_keywords = ["list servers", "list mcp servers", "available servers", "mcp server names", "server names", "list all servers"]
                
                # Check for tool discovery
                if any(keyword in query_lower for keyword in discovery_keywords):
                    analysis["needs_mcp"] = True
                    if not analysis.get("mcp_tools"):
                        analysis["mcp_tools"] = [{
                            "tool_name": "list_tools",
                            "arguments": {},
                            "reason": "User wants to discover available tools"
                        }]
                    logger.info("Detected tool discovery query - routing to MCP list_tools")
                
                # Check for server listing queries
                elif any(keyword in query_lower for keyword in server_listing_keywords):
                    analysis["needs_mcp"] = True
                    if not analysis.get("mcp_tools"):
                        # Use list_tools as it will show server information
                        analysis["mcp_tools"] = [{
                            "tool_name": "list_tools",
                            "arguments": {},
                            "reason": "User wants to list MCP servers"
                        }]
                    logger.info("Detected server listing query - routing to MCP list_tools")
                
                # If MCP is needed but no tools selected, check if it's a listing query
                elif analysis.get("needs_mcp") and not analysis.get("mcp_tools"):
                    # Check for any listing-related keywords
                    listing_patterns = ["list", "show", "what", "available", "names of"]
                    if any(pattern in query_lower for pattern in listing_patterns):
                        analysis["mcp_tools"] = [{
                            "tool_name": "list_tools",
                            "arguments": {},
                            "reason": "User query suggests listing/discovery - using list_tools"
                        }]
                        logger.info("Detected listing pattern in query - routing to MCP list_tools")
                
                # Validate tool arguments against input schemas
                if analysis.get("mcp_tools"):
                    analysis["mcp_tools"] = self._validate_tool_arguments(analysis["mcp_tools"])
                
                logger.info(f"Query analysis: GraphRAG={analysis['needs_graphrag']}, MCP={analysis['needs_mcp']}, Tool Discovery={analysis.get('is_tool_discovery', False)}, MCP tools={len(analysis.get('mcp_tools', []))}")
                return analysis
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse analysis JSON: {e}")
                logger.debug(f"Response text: {response_text[:500]}")
                
                # Improved fallback analysis based on semantic query content
                query_lower = query.lower().strip()
                
                # Detect tool discovery intent with broader patterns
                tool_discovery_keywords = [
                    "what tools", "list tools", "available tools", "show tools",
                    "what can you do", "what capabilities", "what features",
                    "show me tools", "tell me about tools", "discover tools",
                    "explore tools", "tool catalog", "tool inventory"
                ]
                
                is_tool_discovery = any(keyword in query_lower for keyword in tool_discovery_keywords)
                
                # Enhanced GraphRAG detection - prioritize information queries
                # Pattern-based detection: questions seeking information, facts, policies, procedures
                graphrag_keywords = [
                    "how many", "how much", "what is", "what are", "what was", "what were",
                    "tell me about", "explain", "describe", "information about", "details about",
                    "policy", "policies", "procedure", "procedures", "rule", "rules",
                    "document", "documents", "knowledge", "search", "find", "lookup",
                    "benefit", "benefits", "allowance", "allowances", "entitlement", "entitlements"
                ]
                
                # Also detect question patterns (starts with question words)
                is_question = query_lower.strip().startswith(("what", "how", "when", "where", "why", "who", "which", "tell me", "explain"))
                
                # Detect GraphRAG needs: information-seeking queries (keywords OR question patterns)
                needs_graphrag = (any(keyword in query_lower for keyword in graphrag_keywords) or is_question) and not is_tool_discovery
                
                needs_mcp = is_tool_discovery or any(keyword in query_lower for keyword in [
                    "mcp", "tool", "execute", "run", "call", "use tool"
                ])
                
                mcp_tools = []
                if is_tool_discovery:
                    mcp_tools = [{"tool_name": "list_tools", "arguments": {}, "reason": "User wants to discover available tools"}]
                elif needs_mcp and not is_tool_discovery:
                    mcp_tools = [{"tool_name": "unknown", "arguments": {}, "reason": "Fallback detection - needs further analysis"}]
                
                return {
                    "needs_graphrag": needs_graphrag,
                    "needs_mcp": needs_mcp,
                    "is_tool_discovery": is_tool_discovery,
                    "confidence": 0.3,
                    "reasoning": f"Fallback analysis due to JSON parsing error: {str(e)}",
                    "plan": {
                        "agents": ["mcp"] if needs_mcp else (["graphrag"] if needs_graphrag else ["synthesize"]),
                        "order": (["mcp", "synthesize"] if needs_mcp else (["graphrag", "synthesize"] if needs_graphrag else ["synthesize"]))
                    },
                    "mcp_tools": mcp_tools
                }
                
        except Exception as e:
            logger.error(f"Query analysis failed: {str(e)}")
            return {
                "needs_graphrag": False,
                "needs_mcp": False,
                "is_tool_discovery": False,
                "confidence": 0.0,
                "reasoning": f"Analysis error: {str(e)}",
                "plan": {"agents": [], "order": []},
                "mcp_tools": [],
                "error": str(e)
            }
    
    def _find_tool_by_name(self, tool_name: str, tool_map: Dict[str, Dict[str, Any]]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Find tool by name with fuzzy matching.
        
        Args:
            tool_name: Tool name to find
            tool_map: Dictionary mapping tool names to tool info
            
        Returns:
            Tuple of (corrected_tool_name, tool_info) or (None, None) if not found
        """
        # Try exact match first (case-insensitive)
        tool_name_lower = tool_name.lower()
        for actual_name, tool_info in tool_map.items():
            if actual_name.lower() == tool_name_lower:
                return actual_name, tool_info
        
        # Try fuzzy match - check if tool_name is contained in actual name or vice versa
        for actual_name, tool_info in tool_map.items():
            actual_lower = actual_name.lower()
            # Check if one contains the other (for partial matches)
            if tool_name_lower in actual_lower or actual_lower in tool_name_lower:
                logger.info(f"Fuzzy matched '{tool_name}' to '{actual_name}'")
                return actual_name, tool_info
        
        # Try word-based matching
        tool_words = set(tool_name_lower.split('_'))
        best_match = None
        best_score = 0
        
        for actual_name, tool_info in tool_map.items():
            actual_words = set(actual_name.lower().split('_'))
            common_words = tool_words.intersection(actual_words)
            if common_words:
                score = len(common_words) / max(len(tool_words), len(actual_words))
                if score > best_score and score > 0.5:  # At least 50% match
                    best_score = score
                    best_match = actual_name
        
        if best_match:
            logger.info(f"Word-based matched '{tool_name}' to '{best_match}' (score: {best_score:.2f})")
            return best_match, tool_map[best_match]
        
        return None, None
    
    def _validate_tool_arguments(self, tool_plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and enrich tool arguments based on input schemas.
        Also corrects tool names using fuzzy matching.
        
        Args:
            tool_plans: List of tool execution plans from LLM
            
        Returns:
            Validated and enriched tool plans with proper arguments
        """
        if not self.mcp_capabilities:
            return tool_plans
        
        tools = self.mcp_capabilities.get("tools", [])
        if not isinstance(tools, list):
            return tool_plans
        
        tool_map = {tool.get("tool_name"): tool for tool in tools if isinstance(tool, dict)}
        
        validated_plans = []
        for plan in tool_plans:
            tool_name = plan.get("tool_name")
            if not tool_name:
                continue
            
            # Try to find tool with fuzzy matching
            corrected_name, tool_info = self._find_tool_by_name(tool_name, tool_map)
            
            if not tool_info:
                logger.warning(f"Tool '{tool_name}' not found in available tools. Available tools: {list(tool_map.keys())[:10]}")
                # Don't add invalid tools to the plan
                continue
            
            # Update tool name if it was corrected
            if corrected_name != tool_name:
                logger.info(f"Corrected tool name '{tool_name}' to '{corrected_name}'")
                plan["tool_name"] = corrected_name
                plan["reason"] = plan.get("reason", "") + f" (Corrected from '{tool_name}')"
            
            # Get input schema
            input_schema = tool_info.get("input_schema", {})
            if not isinstance(input_schema, dict):
                validated_plans.append(plan)
                continue
            
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])
            
            # Get existing arguments
            arguments = plan.get("arguments", {})
            if not isinstance(arguments, dict):
                arguments = {}
            
            # Ensure required parameters are present
            missing_required = []
            for param_name in required:
                if param_name not in arguments or arguments[param_name] is None or arguments[param_name] == "":
                    missing_required.append(param_name)
            
            if missing_required:
                logger.warning(f"Tool '{tool_name}' missing required parameters: {missing_required}")
                plan["reason"] = plan.get("reason", "") + f" (Warning: Missing required params: {missing_required})"
            
            # Validate parameter types
            for param_name, param_value in arguments.items():
                if param_name in properties:
                    param_info = properties[param_name]
                    param_type = param_info.get("type", "string")
                    
                    # Basic type validation
                    if param_type == "number" and not isinstance(param_value, (int, float)):
                        try:
                            arguments[param_name] = float(param_value)
                        except (ValueError, TypeError):
                            logger.warning(f"Tool '{tool_name}' parameter '{param_name}' should be {param_type}, got {type(param_value)}")
                    elif param_type == "boolean" and not isinstance(param_value, bool):
                        if isinstance(param_value, str):
                            arguments[param_name] = param_value.lower() in ("true", "1", "yes")
                        else:
                            logger.warning(f"Tool '{tool_name}' parameter '{param_name}' should be {param_type}, got {type(param_value)}")
            
            plan["arguments"] = arguments
            validated_plans.append(plan)
        
        return validated_plans
    

