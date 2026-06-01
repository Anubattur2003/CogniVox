"""
Intent Router Agent

Analyzes user queries to intelligently route between GraphRAG and MCP capabilities.
Determines whether a query needs knowledge retrieval, action execution, or both.
"""
import logging
import json
import re
from typing import Dict, Any, List, Tuple, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama

from src.agents.base_agent import BaseAgent
from src.utils.toon_format import format_system_instruction
from src.utils.agent_logger import get_agent_logger

logger = get_agent_logger("intent_router")


class IntentRouter(BaseAgent):
    """
    Routes user queries to appropriate capabilities (GraphRAG, MCP, both, or neither).
    
    Uses pattern analysis and LLM reasoning to determine optimal routing strategy.
    """
    
    def __init__(
        self,
        model_name: str = "qwen3:4b",
        temperature: float = 0.1,
        **kwargs
    ):
        """Initialize the Intent Router."""
        system_instruction = self._create_system_instruction()
        
        # Add result cache for repeated queries
        self._routing_cache = {}
        
        super().__init__(
            agent_name="intent_router",
            model_name=model_name,
            temperature=temperature,
            system_prompt=system_instruction,
            **kwargs
        )
    
    def _create_system_instruction(self) -> str:
        """Create system instruction using TOON format."""
        instruction_data = {
            "role": "Intent Router Agent",
            "purpose": "Analyze queries and route to appropriate capabilities (GraphRAG, MCP, both, or direct response)",
            "capabilities": [
                "Query intent classification",
                "Confidence scoring for routing decisions",
                "Knowledge vs action detection",
                "Hybrid query identification"
            ],
            "routing_rules": {
                "knowledge_queries": "Questions, information lookup, document search → GraphRAG",
                "action_queries": "Commands, executions, data modifications → MCP Tools",
                "hybrid_queries": "Queries needing both context AND action → Both",
                "direct_queries": "Greetings, simple math, general conversation → Direct response"
            },
            "output_format": {
                "use_graphrag": "boolean - whether to use GraphRAG",
                "use_mcp": "boolean - whether to use MCP tools",
                "confidence_graphrag": "float 0-1 - confidence for GraphRAG decision",
                "confidence_mcp": "float 0-1 - confidence for MCP decision",
                "reasoning": "string - explanation of routing decision"
            }
        }
        
        return format_system_instruction(instruction_data)
    
    def analyze_query_intent(
        self,
        query: str,
        available_capabilities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze query and determine routing strategy.
        
        Args:
            query: User query
            available_capabilities: Dict with 'graphrag_available', 'mcp_tools', 'mcp_resources', 'mcp_prompts'
            
        Returns:
            Routing decision with confidence scores and reasoning
        """
        try:
            # Check cache first (normalized query)
            cache_key = query.lower().strip()[:100]  # First 100 chars normalized
            if cache_key in self._routing_cache:
                logger.info(f"⚡ Cache hit for routing decision")
                return self._routing_cache[cache_key].copy()
            
            # Quick pattern-based pre-analysis
            pattern_hints = self._pattern_based_classification(query)
            
            # Check capability availability
            graphrag_available = available_capabilities.get("graphrag_available", True)
            mcp_tools = available_capabilities.get("mcp_tools", [])
            has_mcp = len(mcp_tools) > 0
            
            # OPTIMIZED: Use concise prompt for faster inference
            routing_prompt = self._build_concise_routing_prompt(
                query,
                graphrag_available,
                has_mcp,
                pattern_hints
            )
            
            messages = [
                SystemMessage(content="You analyze queries and output JSON routing decisions."),
                HumanMessage(content=routing_prompt)
            ]
            
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            # Parse routing decision
            try:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    routing_decision = json.loads(json_match.group(0))
                else:
                    # Use pattern hints as fallback
                    routing_decision = pattern_hints
                
                # Ensure required fields
                routing_decision.setdefault("use_graphrag", pattern_hints.get("use_graphrag", False))
                routing_decision.setdefault("use_mcp", pattern_hints.get("use_mcp", False))
                routing_decision.setdefault("confidence_graphrag", 0.7)
                routing_decision.setdefault("confidence_mcp", 0.7)
                routing_decision.setdefault("reasoning", "Routing based on query analysis")
                
            except json.JSONDecodeError:
                routing_decision = pattern_hints
            
            # Apply availability constraints
            if not graphrag_available:
                routing_decision["use_graphrag"] = False
            if not has_mcp:
                routing_decision["use_mcp"] = False
            
            # Cache result
            self._routing_cache[cache_key] = routing_decision.copy()
            
            # Limit cache size
            if len(self._routing_cache) > 100:
                # Remove oldest entry (simple FIFO)
                self._routing_cache.pop(next(iter(self._routing_cache)))
            
            return routing_decision
                
        except Exception as e:
            logger.error(f"Error in intent routing: {str(e)}")
            # Safe fallback: allow both if available
            return {
                "use_graphrag": available_capabilities.get("graphrag_available", True),
                "use_mcp": len(available_capabilities.get("mcp_tools", [])) > 0,
                "confidence_graphrag": 0.5,
                "confidence_mcp": 0.5,
                "reasoning": f"Fallback routing due to error: {str(e)}"
            }
    
    def _pattern_based_classification(self, query: str) -> Dict[str, Any]:
        """
        Fast pattern-based classification for common query types.
        
        Args:
            query: User query
            
        Returns:
            Initial routing suggestion based on patterns
        """
        query_lower = query.lower().strip()
        
        # Knowledge query indicators
        knowledge_keywords = [
            "what", "who", "where", "when", "why", "how",
            "explain", "tell me", "describe", "documentation",
            "information about", "learn about", "read about"
        ]
        
        # Action query indicators
        action_keywords = [
            "create", "delete", "update", "save", "execute",
            "run", "send", "post", "put", "modify", "change",
            "add", "remove", "install"
        ]
        
        # Direct response indicators
        direct_keywords = [
            "hello", "hi", "thanks", "thank you", "bye",
            "help", "what can you do"
        ]
        
        knowledge_score = sum(1 for kw in knowledge_keywords if kw in query_lower)
        action_score = sum(1 for kw in action_keywords if kw in query_lower)
        direct_score = sum(1 for kw in direct_keywords if kw in query_lower)
        
        # Determine routing
        use_graphrag = knowledge_score > 0
        use_mcp = action_score > 0
        
        # If only greetings/simple queries, neither
        if direct_score > 0 and knowledge_score == 0 and action_score == 0:
            use_graphrag = False
            use_mcp = False
        
        # Calculate confidence
        total_score = knowledge_score + action_score + direct_score
        confidence_graphrag = knowledge_score / max(total_score, 1)
        confidence_mcp = action_score / max(total_score, 1)
        
        return {
            "use_graphrag": use_graphrag,
            "use_mcp": use_mcp,
            "confidence_graphrag": min(confidence_graphrag, 0.8),  # Cap pattern-based confidence
            "confidence_mcp": min(confidence_mcp, 0.8),
            "reasoning": "Pattern-based classification (preliminary)"
        }
    
    def _build_routing_prompt(
        self,
        query: str,
        graphrag_available: bool,
        has_mcp: bool,
        mcp_tools: List[Dict],
        pattern_analysis: Dict[str, Any]
    ) -> str:
        """
        Build routing prompt using Chain-of-Thought and Few-Shot techniques.
        
        Args:
            query: User query
            graphrag_available: Whether GraphRAG is available
            has_mcp: Whether MCP capabilities exist
            mcp_tools: Available MCP tools (for context)
            pattern_analysis: Preliminary pattern analysis
            
        Returns:
            Routing prompt string
        """
        # Build capability context
        capabilities_text = []
        if graphrag_available:
            capabilities_text.append("✅ GraphRAG (Knowledge Base): Search documents, retrieve information")
        else:
            capabilities_text.append("❌ GraphRAG: Not available")
        
        if has_mcp:
            tool_count = len(mcp_tools)
            capabilities_text.append(f"✅ MCP Tools ({tool_count} available): Execute actions, interact with systems")
            if tool_count > 0 and tool_count <= 5:
                # Show tool names for context
                tool_names = [t.get("tool_name", "Unknown") for t in mcp_tools[:5]]
                capabilities_text.append(f"   Tools: {', '.join(tool_names)}")
        else:
            capabilities_text.append("❌ MCP Tools: Not available")
        
        capabilities_str = "\n".join(capabilities_text)
        
        prompt = f"""Analyze this user query and determine the optimal routing strategy.

User Query: "{query}"

Available Capabilities:
{capabilities_str}

Pattern Analysis (Preliminary):
- Use GraphRAG: {pattern_analysis.get('use_graphrag', False)}
- Use MCP: {pattern_analysis.get('use_mcp', False)}

STEP-BY-STEP ROUTING ANALYSIS:

1. QUERY TYPE ANALYSIS:
   - Is this a QUESTION seeking information? → GraphRAG likely needed
   - Is this a COMMAND to perform an action? → MCP tools likely needed
   - Is this BOTH (e.g., "Based on docs, create X")? → Both needed
   - Is this a simple greeting/conversation? → Neither needed

2. CAPABILITY MATCHING:
   - Does the query mention searching, reading, or learning? → GraphRAG
   - Does the query mention creating, executing, or modifying? → MCP
   - Check if required capabilities are available

3. CONFIDENCE SCORING:
   - High confidence (0.8-1.0): Clear indicators, unambiguous intent
   - Medium confidence (0.5-0.7): Some indicators, reasonable intent
   - Low confidence (0.0-0.4): Unclear intent, default behavior

FEW-SHOT EXAMPLES:

Example 1:
Query: "What does the documentation say about authentication?"
Analysis: QUESTION about documentation → Knowledge retrieval
Routing: {{"use_graphrag": true, "use_mcp": false, "confidence_graphrag": 0.95, "confidence_mcp": 0.0, "reasoning": "Clear knowledge query"}}

Example 2:
Query: "Create a new user account in the system"
Analysis: COMMAND to create → Action execution
Routing: {{"use_graphrag": false, "use_mcp": true, "confidence_graphrag": 0.0, "confidence_mcp": 0.9, "reasoning": "Clear action command"}}

Example 3:
Query: "Based on the API docs, send a request to the weather service"
Analysis: HYBRID - needs knowledge (API docs) AND action (send request)
Routing: {{"use_graphrag": true, "use_mcp": true, "confidence_graphrag": 0.85, "confidence_mcp": 0.85, "reasoning": "Hybrid query needing both context and action"}}

Example 4:
Query: "Hello, how are you?"
Analysis: GREETING - simple conversation
Routing: {{"use_graphrag": false, "use_mcp": false, "confidence_graphrag": 0.0, "confidence_mcp": 0.0, "reasoning": "Simple greeting, direct response"}}

NOW ANALYZE THE ACTUAL QUERY:

Output ONLY a JSON object with the routing decision. Include:
- use_graphrag (boolean)
- use_mcp (boolean)
- confidence_graphrag (float 0-1)
- confidence_mcp (float 0-1)
- reasoning (string explaining the decision)

JSON OUTPUT:
"""
        return prompt
    
    def _build_concise_routing_prompt(self, query: str, has_graphrag: bool, has_mcp: bool, hints: Dict) -> str:
        \"\"\"Build optimized concise prompt for faster LLM inference.\"\"\"
        capabilities = []
        if has_graphrag:
            capabilities.append(\"GraphRAG: knowledge retrieval\")
        if has_mcp:
            capabilities.append(\"MCP: action execution\")
        
        return f\"\"\"Query: \"{query}\"
Capabilities: {', '.join(capabilities)}

Route to:
- GraphRAG if: questions, information lookup, documentation queries
- MCP if: commands, actions, create/update/delete operations  
- Both if: query needs knowledge AND action
- Neither if: greetings, simple chat

JSON only:
{{\"use_graphrag\": bool, \"use_mcp\": bool, \"confidence_graphrag\": 0.0-1.0, \"confidence_mcp\": 0.0-1.0, \"reasoning\": \"why\"}}\"\"\"
    
    def should_use_graphrag(
        self,
        query: str,
        context: str = ""
    ) -> Tuple[bool, float, str]:
        """
        Quick check if GraphRAG should be used.
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            Tuple of (should_use, confidence, reason)
        """
        query_lower = query.lower()
        
        # Strong indicators for GraphRAG
        knowledge_patterns = [
            r'\bwhat\s+(is|are|does|do)\b',
            r'\bhow\s+to\b',
            r'\bexplain\b',
            r'\bdocumentation\b',
            r'\bpolicy\b',
            r'\bprocedure\b',
            r'\btell\s+me\s+about\b'
        ]
        
        score = sum(1 for pattern in knowledge_patterns if re.search(pattern, query_lower))
        
        if score >= 2:
            return True, 0.9, "Strong knowledge query indicators"
        elif score == 1:
            return True, 0.7, "Knowledge query indicator present"
        else:
            return False, 0.3, "No clear knowledge query indicators"
    
    def should_use_mcp(
        self,
        query: str,
        available_tools: List[Dict]
    ) -> Tuple[bool, float, str]:
        """
        Quick check if MCP tools should be used.
        
        Args:
            query: User query
            available_tools: List of available MCP tools
            
        Returns:
            Tuple of (should_use, confidence, reason)
        """
        if not available_tools:
            return False, 0.0, "No MCP tools available"
        
        query_lower = query.lower()
        
        # Strong indicators for MCP action execution
        action_patterns = [
            r'\b(create|make|build|generate)\b',
            r'\b(delete|remove|clear)\b',
            r'\b(update|modify|change|edit)\b',
            r'\b(save|store|write)\b',
            r'\b(execute|run|perform)\b',
            r'\b(send|post|put|get)\b'
        ]
        
        score = sum(1 for pattern in action_patterns if re.search(pattern, query_lower))
        
        if score >= 2:
            return True, 0.9, "Strong action query indicators"
        elif score == 1:
            return True, 0.7, "Action query indicator present"
        else:
            return False, 0.3, "No clear action query indicators"


# Factory function
def create_intent_router(**kwargs) -> IntentRouter:
    """Create an IntentRouter instance."""
    return IntentRouter(**kwargs)
