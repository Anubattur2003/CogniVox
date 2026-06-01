"""
Multi-Agent Orchestrator using LangGraph StateGraph

Coordinates multiple specialized agents for robust task execution with parallel processing.
"""
import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.agents.multi_agent.state import AgentState
from src.agents.multi_agent.query_analyzer import QueryAnalysisAgent
from src.agents.multi_agent.graphrag_agent import GraphRAGAgent
from src.agents.multi_agent.mcp_coordinator import MCPCoordinatorAgent
from src.agents.multi_agent.mcp_reasoning_agent import MCPReasoningAgent
from src.agents.multi_agent.response_synthesizer import ResponseSynthesisAgent
from src.agents.multi_agent.reasoning_agent import QueryReasoningAgent
from src.agents.multi_agent.validator import ValidationAgent
from src.mcp.mcp_client import MCPClient
from src.utils.toon_format import format_system_instruction
from src.utils.agent_logger import get_agent_logger

logger = get_agent_logger("orchestrator")


class MultiAgentOrchestrator:
    """
    Multi-agent orchestrator using LangGraph StateGraph.
    
    Coordinates specialized agents:
    - QueryAnalysisAgent: Analyzes queries and determines routing
    - GraphRAGAgent: Handles knowledge base queries
    - MCPCoordinatorAgent: Manages MCP tool execution
    - ResponseSynthesisAgent: Combines results from multiple agents
    - ValidationAgent: Validates final responses
    """
    
    def __init__(
        self,
        model_name: str = "qwen2.5:7b",
        temperature: float = 0.1,
        enable_parallel: bool = True,
        **kwargs
    ):
        """
        Initialize the multi-agent orchestrator.
        
        Args:
            model_name: LLM model name (fallback if not specified in config)
            temperature: Temperature for LLM (fallback)
            enable_parallel: Enable parallel processing for independent tasks
            **kwargs: Additional configuration
        """
        # Load agent-specific configurations from config.yaml
        try:
            from src.utils.config import (
                get_agent_model, 
                get_agent_temperature, 
                get_agent_timeout,
                is_validator_enabled
            )
            
            # Get model configurations for each agent
            qa_model = get_agent_model("query_analyzer", model_name)
            qa_temp = get_agent_temperature("query_analyzer", 0.1)
            qa_timeout = get_agent_timeout("query_analyzer", 60)
            
            mcp_reason_model = get_agent_model("mcp_reasoning", qa_model)  # Same as QA by default
            mcp_reason_temp = get_agent_temperature("mcp_reasoning", 0.1)
            mcp_reason_timeout = get_agent_timeout("mcp_reasoning", 60)
            
            synth_model = get_agent_model("response_synthesizer", model_name)
            synth_temp = get_agent_temperature("response_synthesizer", 0.7)
            synth_timeout = get_agent_temperature("response_synthesizer", 30)
            
            reason_model = get_agent_model("query_reasoning", "qwen2.5:7b")
            reason_temp = get_agent_temperature("query_reasoning", 0.2)
            reason_timeout = get_agent_timeout("query_reasoning", 30)
            
            val_model = get_agent_model("validator", synth_model)  # Same as synthesizer by default
            val_temp = get_agent_temperature("validator", 0.1)
            val_timeout = get_agent_timeout("validator", 30)
            
            self.validator_enabled = is_validator_enabled()
            
            logger.info(f"🚀 Orchestrator config loaded:")
            logger.info(f"   QueryAnalyzer: {qa_model} (temp={qa_temp})")
            logger.info(f"   MCPReasoning: {mcp_reason_model} (temp={mcp_reason_temp})")
            logger.info(f"   QueryReasoning: {reason_model} (temp={reason_temp})")
            logger.info(f"   ResponseSynthesizer: {synth_model} (temp={synth_temp})")
            logger.info(f"   Validator: {val_model} (enabled={self.validator_enabled})")
            
        except Exception as e:
            logger.warning(f"Failed to load agent config, using defaults: {e}")
            qa_model = qa_temp = mcp_reason_model = mcp_reason_temp = model_name
            synth_model = val_model = model_name
            synth_temp = val_temp = temperature
            qa_timeout = mcp_reason_timeout = synth_timeout = val_timeout = 60
            self.validator_enabled = False
        
        self.model_name = model_name
        self.temperature = temperature
        self.enable_parallel = enable_parallel
        
        # Initialize MCP client for dynamic capability discovery
        self.mcp_client = MCPClient()
        
        # Initialize specialized agents with per-agent models
        self.query_analyzer = None  # Will be initialized with MCP capabilities
        self._qa_model = qa_model
        self._qa_temp = qa_temp
        
        self.graphrag_agent = GraphRAGAgent(
            model_name=model_name,  # GraphRAG doesn't use LLM, just HTTP
            temperature=temperature
        )
        
        self.mcp_reasoning_agent = MCPReasoningAgent(
            model_name=mcp_reason_model,
            temperature=mcp_reason_temp
        )
        
        self.mcp_coordinator = MCPCoordinatorAgent(
            model_name=model_name,  # Coordinator doesn't use LLM
            temperature=temperature
        )
        
        self.response_synthesizer = ResponseSynthesisAgent(
            model_name=synth_model,
            temperature=synth_temp
        )
        
        self.query_reasoning_agent = QueryReasoningAgent(
            model_name=reason_model,
            temperature=reason_temp
        )
        
        if self.validator_enabled:
            self.validator = ValidationAgent(
                model_name=val_model,
                temperature=val_temp
            )
            logger.info("✅ Validator enabled")
        else:
            self.validator = None
            logger.info("⚡ Validator disabled for faster responses")
        
        # Build the state graph
        self.graph = self._build_graph()
        
        logger.info("Multi-Agent Orchestrator initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph StateGraph with agent nodes."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_query", self._analyze_query_node)
        workflow.add_node("reason_mcp", self._reason_mcp_node)  # MCP tool reasoning
        workflow.add_node("execute_graphrag", self._execute_graphrag_node)
        workflow.add_node("reason_about_query", self._reason_about_query_node)  # Query-specific reasoning
        workflow.add_node("execute_mcp", self._execute_mcp_node)
        workflow.add_node("synthesize_response", self._synthesize_response_node)
        
        # Conditionally add validator node
        if self.validator_enabled and self.validator is not None:
            workflow.add_node("validate_response", self._validate_response_node)
        
        # Set entry point
        workflow.set_entry_point("analyze_query")
        
        # Add conditional edges based on query analysis
        workflow.add_conditional_edges(
            "analyze_query",
            self._route_after_analysis,
            {
                "graphrag_only": "execute_graphrag",
                "mcp_only": "reason_mcp",  # Add reasoning step before MCP execution
                "both": "execute_graphrag",  # Start with GraphRAG, then MCP
                "neither": "synthesize_response",
                "error": END
            }
        )
        
        # After reasoning, execute MCP
        workflow.add_edge("reason_mcp", "execute_mcp")
        
        # After GraphRAG, apply query-specific reasoning
        workflow.add_edge("execute_graphrag", "reason_about_query")
        
        # After reasoning, check if MCP is also needed
        workflow.add_conditional_edges(
            "reason_about_query",
            self._route_after_reasoning,
            {
                "to_mcp": "reason_mcp",  # Go to MCP reasoning if needed
                "to_synthesize": "synthesize_response",
                "error": END
            }
        )
        
        # After MCP, go to synthesis
        workflow.add_edge("execute_mcp", "synthesize_response")
        
        # After synthesis, conditionally validate or end
        if self.validator_enabled and self.validator is not None:
            workflow.add_edge("synthesize_response", "validate_response")
            workflow.add_edge("validate_response", END)
        else:
            workflow.add_edge("synthesize_response", END)  # Skip validation
        
        return workflow.compile()
    
    def _analyze_query_node(self, state: AgentState) -> Dict[str, Any]:
        """Analyze the query and determine which agents/tools to use."""
        try:
            logger.info("Query Analysis Agent: Analyzing query...")
            
            # Fetch MCP capabilities dynamically for this user
            user_id = state.get("user_id", "default")
            auth_token = state.get("auth_token")
            
            mcp_capabilities = None
            if auth_token:
                try:
                    logger.info(f"Fetching MCP capabilities for user {user_id}")
                    mcp_capabilities = self.mcp_client.get_all_mcp_capabilities(
                        user_id=user_id,
                        auth_token=auth_token
                    )
                    # Safely get counts
                    tools_list = mcp_capabilities.get('tools', [])
                    resources_list = mcp_capabilities.get('resources', [])
                    prompts_list = mcp_capabilities.get('prompts', [])
                    
                    # Ensure we have lists for counting
                    tools_count = len(tools_list) if isinstance(tools_list, list) else 0
                    resources_count = len(resources_list) if isinstance(resources_list, list) else 0
                    prompts_count = len(prompts_list) if isinstance(prompts_list, list) else 0
                    
                    logger.info(f"Found {tools_count} tools, {resources_count} resources, {prompts_count} prompts")
                except Exception as e:
                    logger.warning(f"Failed to fetch MCP capabilities: {str(e)}")
            
            # Create query analyzer with dynamic capabilities
            query_analyzer = QueryAnalysisAgent(
                model_name=self._qa_model,  # Use configured model
                temperature=self._qa_temp,
                mcp_capabilities=mcp_capabilities
            )
            
            analysis = query_analyzer.analyze(
                query=state["user_message"],
                context=state.get("context_prompt", ""),
                user_id=user_id
            )
            
            return {
                "query_analysis": analysis,
                "needs_graphrag": analysis.get("needs_graphrag", False),
                "needs_mcp": analysis.get("needs_mcp", False),
                "agent_plan": analysis.get("plan", {})
            }
        except Exception as e:
            logger.error(f"Query analysis failed: {str(e)}")
            return {
                "query_analysis": {"error": str(e)},
                "needs_graphrag": False,
                "needs_mcp": False,
                "agent_plan": {}
            }
    
    def _reason_mcp_node(self, state: AgentState) -> Dict[str, Any]:
        """Reason about which MCP tools are needed for the query."""
        try:
            logger.info("MCP Reasoning Agent: Thinking about tool selection...")
            
            user_id = state.get("user_id", "default")
            auth_token = state.get("auth_token")
            
            # Get MCP capabilities
            mcp_capabilities = None
            if auth_token:
                try:
                    mcp_capabilities = self.mcp_client.get_all_mcp_capabilities(
                        user_id=user_id,
                        auth_token=auth_token
                    )
                except Exception as e:
                    logger.warning(f"Failed to fetch MCP capabilities for reasoning: {str(e)}")
            
            # Handle cases where servers may not have all three capability types
            # Ensure we have a valid capabilities dict even if some types are missing
            if not mcp_capabilities:
                mcp_capabilities = {"tools": [], "resources": [], "prompts": []}
                logger.warning("No MCP capabilities available for reasoning")
            else:
                # Ensure all three keys exist (may be empty lists)
                mcp_capabilities.setdefault("tools", [])
                mcp_capabilities.setdefault("resources", [])
                mcp_capabilities.setdefault("prompts", [])
            
            tools_count = len(mcp_capabilities.get("tools", []))
            resources_count = len(mcp_capabilities.get("resources", []))
            prompts_count = len(mcp_capabilities.get("prompts", []))
            
            if tools_count == 0 and resources_count == 0 and prompts_count == 0:
                logger.warning("No MCP capabilities available for reasoning")
                return {
                    "mcp_reasoning": {
                        "reasoning": "No MCP capabilities available - no tools, resources, or prompts found",
                        "selected_tools": [],
                        "selected_resources": [],
                        "selected_prompts": [],
                        "execution_plan": {"order": [], "dependencies": {}, "parallel": []},
                        "expected_context": ""
                    }
                }
            
            logger.info(f"MCP Reasoning: Analyzing with {tools_count} tools, {resources_count} resources, {prompts_count} prompts")
            
            # Use reasoning agent to think about tool selection
            reasoning_result = self.mcp_reasoning_agent.reason_about_tools(
                query=state["user_message"],
                available_capabilities=mcp_capabilities,
                context=state.get("context_prompt", "")
            )
            
            # Validate reasoning result - ensure it has required fields
            if not isinstance(reasoning_result, dict):
                logger.error(f"MCP Reasoning returned invalid result type: {type(reasoning_result)}")
                reasoning_result = {
                    "reasoning": "Reasoning failed - invalid result format",
                    "selected_tools": [],
                    "selected_resources": [],
                    "selected_prompts": [],
                    "execution_plan": {"order": [], "dependencies": {}, "parallel": []},
                    "expected_context": ""
                }
            
            # Update query analysis with reasoning results
            query_analysis = state.get("query_analysis", {})
            
            # If reasoning found tools, use them (override LLM selection if better)
            if reasoning_result.get("selected_tools"):
                query_analysis["mcp_tools"] = reasoning_result["selected_tools"]
                query_analysis["mcp_reasoning"] = reasoning_result.get("reasoning", "")
                logger.info(f"MCP Reasoning selected {len(reasoning_result['selected_tools'])} tools")
            
            if reasoning_result.get("selected_resources"):
                query_analysis["mcp_resources"] = reasoning_result["selected_resources"]
            
            if reasoning_result.get("selected_prompts"):
                query_analysis["mcp_prompts"] = reasoning_result["selected_prompts"]
            
            return {
                "mcp_reasoning": reasoning_result,
                "query_analysis": query_analysis,
                "mcp_execution_plan": reasoning_result.get("execution_plan", {}),
                "expected_mcp_context": reasoning_result.get("expected_context", "")
            }
            
        except Exception as e:
            logger.error(f"MCP reasoning failed: {str(e)}")
            return {
                "mcp_reasoning": {
                    "reasoning": f"Reasoning error: {str(e)}",
                    "selected_tools": [],
                    "error": str(e)
                }
            }
    
    def _execute_graphrag_node(self, state: AgentState) -> Dict[str, Any]:
        """Execute GraphRAG knowledge base search."""
        try:
            if not state.get("needs_graphrag", False):
                return {"graphrag_result": None}
            
            logger.info("GraphRAG Agent: Executing knowledge base search...")
            
            result = self.graphrag_agent.search(
                query=state["user_message"],
                user_id=state.get("user_id", "default"),
                n_results=state.get("n_results", 20)
            )
            
            return {
                "graphrag_result": result,
                "graphrag_sources": result.get("sources", []),
                "graphrag_context": result.get("context", "")
            }
        except Exception as e:
            logger.error(f"GraphRAG execution failed: {str(e)}")
            return {
                "graphrag_result": {"error": str(e)},
                "graphrag_sources": [],
                "graphrag_context": ""
            }
    
    def _reason_about_query_node(self, state: AgentState) -> Dict[str, Any]:
        """Apply query-specific reasoning to extract precise answers from GraphRAG results."""
        try:
            # Only reason if we have GraphRAG results
            if not state.get("graphrag_result") or not state.get("graphrag_result", {}).get("source_found"):
                logger.info("Query Reasoning: Skipping - no GraphRAG results available")
                return {"reasoning_result": None}
            
            logger.info("Query Reasoning Agent: Extracting precise answer from GraphRAG results...")
            
            reasoning_result = self.query_reasoning_agent.reason(
                query=state["user_message"],
                graphrag_result=state.get("graphrag_result", {}),
                context=state.get("context_prompt", ""),
                user_id=state.get("user_id", "default")
            )
            
            if reasoning_result.get("confidence", 0) > 0.5:
                logger.info(f"Query Reasoning: Extracted precise answer with confidence {reasoning_result.get('confidence', 0):.2f}")
            else:
                logger.warning(f"Query Reasoning: Low confidence answer ({reasoning_result.get('confidence', 0):.2f})")
            
            return {
                "reasoning_result": reasoning_result
            }
        except Exception as e:
            logger.error(f"Query reasoning failed: {str(e)}")
            return {
                "reasoning_result": {
                    "precise_answer": "Unable to extract precise answer",
                    "reasoning": f"Reasoning error: {str(e)}",
                    "confidence": 0.0,
                    "error": str(e)
                }
            }
    
    def _execute_mcp_node(self, state: AgentState) -> Dict[str, Any]:
        """Execute MCP tools with enhanced context extraction."""
        try:
            if not state.get("needs_mcp", False):
                return {"mcp_result": None}
            
            user_id = state.get("user_id", "default")
            auth_token = state.get("auth_token")
            
            # Debug logging for auth_token
            if auth_token:
                logger.info(f"MCP Coordinator: Executing MCP tools for user {user_id} with auth_token (length: {len(auth_token)})")
            else:
                logger.warning(f"MCP Coordinator: Executing MCP tools for user {user_id} WITHOUT auth_token - RBAC will fail")
            
            # Get tools from reasoning result if available, otherwise from query analysis
            mcp_reasoning = state.get("mcp_reasoning", {})
            query_analysis = state.get("query_analysis", {})
            
            # Prefer reasoning results, fallback to query analysis
            mcp_tools = mcp_reasoning.get("selected_tools", query_analysis.get("mcp_tools", []))
            mcp_resources = mcp_reasoning.get("selected_resources", query_analysis.get("mcp_resources", []))
            mcp_prompts = mcp_reasoning.get("selected_prompts", query_analysis.get("mcp_prompts", []))
            
            # Get execution plan from reasoning if available
            execution_plan = mcp_reasoning.get("execution_plan", {})
            
            # Execute tools, resources, and prompts
            result = self.mcp_coordinator.execute(
                query=state["user_message"],
                tools_to_use=mcp_tools,
                resources_to_use=mcp_resources,
                prompts_to_use=mcp_prompts,
                user_id=user_id,
                auth_token=auth_token,
                execution_plan=execution_plan
            )
            
            # Extract context from tool results
            extracted_context = self._extract_context_from_mcp_results(result)
            
            return {
                "mcp_result": result,
                "mcp_tools_used": result.get("tools_used", []),
                "mcp_outputs": result.get("outputs", []),
                "mcp_resources": result.get("resources_used", []),
                "mcp_prompts": result.get("prompts_used", []),
                "mcp_extracted_context": extracted_context,
                "mcp_reasoning": mcp_reasoning.get("reasoning", "")
            }
        except Exception as e:
            logger.error(f"MCP execution failed: {str(e)}")
            return {
                "mcp_result": {"error": str(e), "success_count": 0, "error_count": 0},
                "mcp_tools_used": [],
                "mcp_outputs": [],
                "mcp_extracted_context": ""
            }
    
    def _extract_context_from_mcp_results(self, mcp_result: Dict[str, Any]) -> str:
        """
        Extract meaningful context from MCP tool execution results.
        
        Args:
            mcp_result: MCP execution result dictionary
            
        Returns:
            Extracted context string for response generation
        """
        if not mcp_result:
            return ""
        
        outputs = mcp_result.get("outputs", [])
        if not outputs:
            return ""
        
        context_parts = []
        
        for output in outputs:
            if not output.get("success"):
                continue
            
            tool_name = output.get("tool", "Unknown")
            result = output.get("result", {})
            
            # Extract meaningful information from result
            if isinstance(result, dict):
                # Try to extract text content, data, or meaningful fields
                if "content" in result:
                    context_parts.append(f"{tool_name} result: {result['content']}")
                elif "data" in result:
                    context_parts.append(f"{tool_name} data: {str(result['data'])[:500]}")
                elif "text" in result:
                    context_parts.append(f"{tool_name} output: {result['text']}")
                else:
                    # Use string representation of result
                    result_str = str(result)
                    if len(result_str) < 1000:
                        context_parts.append(f"{tool_name}: {result_str}")
                    else:
                        context_parts.append(f"{tool_name}: {result_str[:500]}...")
            elif isinstance(result, str):
                context_parts.append(f"{tool_name}: {result[:500]}")
            else:
                context_parts.append(f"{tool_name} executed successfully")
        
        return "\n".join(context_parts)
    
    def _synthesize_response_node(self, state: AgentState) -> Dict[str, Any]:
        """Synthesize response from all agent results."""
        try:
            logger.info("Response Synthesis Agent: Combining results...")
            
            # Enhance MCP result with extracted context and reasoning
            mcp_result = state.get("mcp_result", {})
            if mcp_result:
                mcp_extracted_context = state.get("mcp_extracted_context", "")
                mcp_reasoning = state.get("mcp_reasoning", {})
                
                if mcp_extracted_context:
                    mcp_result["extracted_context"] = mcp_extracted_context
                if isinstance(mcp_reasoning, dict) and mcp_reasoning.get("reasoning"):
                    mcp_result["reasoning"] = mcp_reasoning.get("reasoning", "")
            
            synthesis = self.response_synthesizer.synthesize(
                query=state["user_message"],
                graphrag_result=state.get("graphrag_result"),
                mcp_result=mcp_result,
                reasoning_result=state.get("reasoning_result"),  # Pass precise reasoning
                context=state.get("context_prompt", ""),
                user_id=state.get("user_id", "default")
            )
            
            return {
                "synthesized_response": synthesis.get("response", ""),
                "sources": synthesis.get("sources", []),
                "thinking_steps": synthesis.get("thinking_steps", []),
                "used_tools": synthesis.get("used_tools", [])
            }
        except Exception as e:
            logger.error(f"Response synthesis failed: {str(e)}")
            return {
                "synthesized_response": "I apologize, but I encountered an error processing your request.",
                "sources": [],
                "thinking_steps": [],
                "used_tools": []
            }
    
    def _validate_response_node(self, state: AgentState) -> Dict[str, Any]:
        """Validate the final response."""
        # If validator is disabled, skip validation
        if not self.validator_enabled or self.validator is None:
            return {
                "validated_response": state.get("synthesized_response", ""),
                "validation_passed": True,
                "validation_notes": ["Validation skipped (disabled)"]
            }
        
        try:
            logger.info("Validation Agent: Validating response...")
            
            validation = self.validator.validate(
                query=state["user_message"],
                response=state.get("synthesized_response", ""),
                sources=state.get("sources", [])
            )
            
            return {
                "validated_response": validation.get("response", state.get("synthesized_response", "")),
                "validation_passed": validation.get("passed", True),
                "validation_notes": validation.get("notes", [])
            }
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            return {
                "validated_response": state.get("synthesized_response", ""),
                "validation_passed": True,
                "validation_notes": []
            }
    
    def _route_after_analysis(self, state: AgentState) -> str:
        """Route after query analysis based on needs."""
        needs_graphrag = state.get("needs_graphrag", False)
        needs_mcp = state.get("needs_mcp", False)
        
        if state.get("query_analysis", {}).get("error"):
            return "error"
        
        if needs_graphrag and needs_mcp:
            return "both"
        elif needs_graphrag:
            return "graphrag_only"
        elif needs_mcp:
            return "mcp_only"
        else:
            return "neither"
    
    def _route_after_graphrag(self, state: AgentState) -> str:
        """Route after GraphRAG execution."""
        if state.get("needs_mcp", False):
            return "to_mcp"
        else:
            return "to_synthesize"
    
    def _route_after_reasoning(self, state: AgentState) -> str:
        """Route after query-specific reasoning."""
        if state.get("needs_mcp", False):
            return "to_mcp"
        else:
            return "to_synthesize"
    
    def process(
        self,
        user_message: str,
        user_id: str = "default",
        context_prompt: str = "",
        auth_token: Optional[str] = None,
        n_results: int = 20,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a user query through the multi-agent system.
        
        Args:
            user_message: User's query
            user_id: User identifier
            context_prompt: Additional context
            auth_token: JWT token for MCP authentication
            n_results: Number of GraphRAG results
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with response and metadata
        """
        start_time = time.time()
        
        try:
            # Initialize state with all required fields
            initial_state = {
                "user_message": user_message,
                "user_id": user_id,
                "context_prompt": context_prompt or "",
                "auth_token": auth_token,
                "n_results": n_results,
                "messages": [HumanMessage(content=user_message)],
                # Initialize all other required fields with defaults
                "query_analysis": {},
                "needs_graphrag": False,
                "needs_mcp": False,
                "agent_plan": {},
                "graphrag_result": None,
                "graphrag_sources": [],
                "graphrag_context": "",
                "mcp_result": None,
                "mcp_tools_used": [],
                "mcp_outputs": [],
                "mcp_resources": [],
                "mcp_prompts": [],
                "synthesized_response": "",
                "sources": [],
                "thinking_steps": [],
                "used_tools": [],
                "validated_response": "",
                "validation_passed": True,
                "validation_notes": []
            }
            
            # Log auth_token status for debugging
            if auth_token:
                logger.info(f"Executing multi-agent workflow for user {user_id} with auth_token (length: {len(auth_token)})")
            else:
                logger.warning(f"Executing multi-agent workflow for user {user_id} WITHOUT auth_token - MCP tools will not be available")
            
            # Execute the graph
            final_state = self.graph.invoke(initial_state)
            
            # Extract results
            execution_time = time.time() - start_time
            
            # Collect sources from GraphRAG
            sources = final_state.get("sources", [])
            if not sources and final_state.get("graphrag_sources"):
                sources = final_state.get("graphrag_sources", [])
            
            # Collect used tools
            used_tools = final_state.get("used_tools", [])
            if final_state.get("graphrag_result") and "graphrag_search" not in used_tools:
                used_tools.append("graphrag_search")
            if final_state.get("mcp_tools_used"):
                used_tools.extend(final_state.get("mcp_tools_used", []))
            
            response_data = {
                "success": True,
                "response": final_state.get("validated_response") or final_state.get("synthesized_response", ""),
                "response_time": execution_time,
                "sources": sources,
                "document_relevant": len(sources) > 0 and final_state.get("graphrag_result", {}).get("source_found", False),
                "thinking_steps": final_state.get("thinking_steps", []),
                "used_tools": list(set(used_tools)),  # Remove duplicates
                "agent_type": "multi_agent_orchestrator",
                "query_analysis": final_state.get("query_analysis", {}),
                "graphrag_used": final_state.get("graphrag_result") is not None,
                "mcp_used": final_state.get("mcp_result") is not None and final_state.get("mcp_result", {}).get("success_count", 0) > 0,
                "validation_passed": final_state.get("validation_passed", True)
            }
            
            logger.info(f"Multi-agent workflow completed in {execution_time:.3f}s")
            return response_data
            
        except Exception as e:
            logger.error(f"Multi-agent workflow failed: {str(e)}")
            return {
                "success": False,
                "response": "I apologize, but I encountered an error processing your request.",
                "response_time": time.time() - start_time,
                "sources": [],
                "document_relevant": False,
                "thinking_steps": [],
                "used_tools": [],
                "agent_type": "multi_agent_orchestrator",
                "error": str(e)
            }

