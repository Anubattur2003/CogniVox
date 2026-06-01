"""
Response Mode Router

Routes queries to different specialized agents based on the selected response mode.
Provides a unified interface for handling different types of responses.

Now supports multi-agent orchestration for agentic mode.
"""

import logging
from typing import Dict, Any, Optional
from .general_response_agent import GeneralResponseAgent
from .thinking_response_agent import ThinkingResponseAgent
from .supervisor_react_agent import SupervisorReActAgent
from .multi_agent import MultiAgentOrchestrator

logger = logging.getLogger(__name__)

class ResponseModeRouter:
    """
    Routes queries to appropriate agents based on response mode.
    Supports general, thinking, and agentic response modes.
    """
    
    def __init__(self):
        """Initialize the router with all available agents."""
        self.agents = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all available response agents."""
        try:
            # General response agent for direct, concise answers
            self.agents["general"] = GeneralResponseAgent(model_name="mistral:latest")
            logger.info("Initialized General Response Agent with Mistral:latest model")
            
            # Thinking response agent for visible reasoning
            self.agents["thinking"] = ThinkingResponseAgent(model_name="qwen2.5:7b")
            logger.info("Initialized Thinking Response Agent with Qwen2.5:7b model")
            
            # Multi-agent orchestrator for robust agentic mode
            # This replaces the single SupervisorReActAgent with a multi-agent system
            try:
                self.agents["agentic"] = MultiAgentOrchestrator(
                    model_name="qwen2.5:7b",
                    temperature=0.1,
                    enable_parallel=True
                )
                logger.info("Initialized Multi-Agent Orchestrator for agentic mode")
            except Exception as multi_agent_error:
                logger.warning(f"Failed to initialize Multi-Agent Orchestrator: {multi_agent_error}")
                logger.info("Falling back to Supervisor ReAct Agent")
                # Fallback to single agent
                self.agents["agentic"] = SupervisorReActAgent()
                logger.info("Initialized Agentic Response Agent (Supervisor ReAct - Fallback)")
            
        except Exception as e:
            logger.error(f"Error initializing agents: {str(e)}")
            raise
    
    def route_query(
        self,
        response_mode: str,
        user_message: str,
        user_id: str = None,
        context_prompt: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Route a query to the appropriate agent based on response mode.
        Each agent handles its own validation for optimal performance.
        
        Args:
            response_mode: The selected response mode ("general", "thinking", "agentic")
            user_message: The user's question or request
            user_id: User identifier for context
            context_prompt: Additional context information
            **kwargs: Additional parameters to pass to the agent
            
        Returns:
            Dict containing the response and metadata from the selected agent
        """
        try:
            # Validate response mode
            if response_mode not in self.agents:
                logger.warning(f"Unknown response mode '{response_mode}', defaulting to 'general'")
                response_mode = "general"
            
            # Get the appropriate agent
            agent = self.agents[response_mode]
            
            logger.info(f"Routing query to {response_mode} agent for user {user_id} (prompt-based validation)")
            
            # Track routing time
            import time
            routing_start = time.time()
            
            # Models are kept warm by background service to prevent cold starts
            
            # Route based on response mode
            if response_mode == "agentic":
                # Check if using multi-agent orchestrator or single agent
                if isinstance(agent, MultiAgentOrchestrator):
                    # Multi-agent mode - use process method
                    result = agent.process(
                        user_message=user_message,
                        user_id=user_id,
                        context_prompt=context_prompt,
                        auth_token=kwargs.get("auth_token"),
                        n_results=kwargs.get("n_results", 20)
                    )
                    
                    routing_time = time.time() - routing_start
                    logger.info(f"Multi-agent orchestrator processing took {routing_time:.3f} seconds")
                    
                    # Ensure consistent response format
                    return {
                        "success": result.get("success", True),
                        "response": result.get("response", ""),
                        "response_time": result.get("response_time", 0.0),
                        "variants": {
                            "summary": result.get("response", "")[:200] + "..." if len(result.get("response", "")) > 200 else result.get("response", ""),
                            "detailed": result.get("response", "")
                        },
                        "sources": result.get("sources", []),
                        "document_relevant": result.get("document_relevant", False),
                        "thinking_steps": result.get("thinking_steps", []),
                        "used_tools": result.get("used_tools", []),
                        "agent_type": "multi_agent_orchestrator",
                        "chat_id": kwargs.get("chat_id", "unknown"),
                        "query_analysis": result.get("query_analysis", {}),
                        "graphrag_used": result.get("graphrag_used", False),
                        "mcp_used": result.get("mcp_used", False)
                    }
                else:
                    # Fallback to single agent (SupervisorReActAgent)
                    result = agent.chat(
                        user_message=user_message,
                        user_id=user_id,
                        context_prompt=context_prompt,
                        return_thinking=True
                    )
                    
                    routing_time = time.time() - routing_start
                    logger.info(f"Agentic agent processing took {routing_time:.3f} seconds")
                    
                    # Ensure consistent response format
                    return {
                        "success": True,
                        "response": result.get("response", ""),
                        "response_time": result.get("processing_time", 0.0),
                        "variants": {
                            "summary": result.get("response", "")[:200] + "..." if len(result.get("response", "")) > 200 else result.get("response", ""),
                            "detailed": result.get("response", "")
                        },
                        "sources": result.get("sources", []),
                        "document_relevant": result.get("document_relevant", False),
                        "thinking_steps": result.get("thinking_steps", []),
                        "used_tools": result.get("used_tools", []),
                        "agent_type": "supervisor_react",
                        "chat_id": kwargs.get("chat_id", "unknown")
                    }
                
            else:
                # General and thinking modes use the new simplified interface
                result = agent.process_query(
                    user_message=user_message,
                    user_id=user_id,
                    context_prompt=context_prompt,
                    **kwargs
                )
                
                if not result.get("success", False):
                    raise Exception(result.get("error", "Agent processing failed"))
                
                routing_time = time.time() - routing_start
                logger.info(f"{response_mode} agent processing took {routing_time:.3f} seconds")
                
                # Create response variants for consistency
                response_text = result.get("response", "")
                
                return {
                    "success": True,
                    "response": response_text,
                    "response_time": result.get("processing_time", 0.0),
                    "variants": {
                        "summary": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                        "detailed": response_text
                    },
                    "sources": result.get("sources", []),
                    "document_relevant": result.get("document_relevant", False),  # Pass through relevance flag
                    "thinking_steps": result.get("thinking_steps", []),
                    "used_tools": result.get("used_tools", []),
                    "agent_type": result.get("agent_type", response_mode),
                    "chat_id": kwargs.get("chat_id", "unknown")
                }
                
        except Exception as e:
            logger.error(f"Error routing query with mode '{response_mode}': {str(e)}")
            
            # Fallback response
            return {
                "success": False,
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "response_time": 0.0,
                "variants": {
                    "summary": "Error occurred during processing.",
                    "detailed": "I apologize, but I encountered an error processing your request. Please try again."
                },
                "sources": [],
                "document_relevant": False,  # No relevant documents in error case
                "thinking_steps": [],
                "used_tools": [],
                "agent_type": f"{response_mode}_error",
                "chat_id": kwargs.get("chat_id", "unknown"),
                "error": str(e)
            }
    
    def get_available_modes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available response modes.
        
        Returns:
            Dict mapping mode names to their capabilities
        """
        modes = {}
        
        for mode_name, agent in self.agents.items():
            try:
                if hasattr(agent, 'get_capabilities'):
                    modes[mode_name] = agent.get_capabilities()
                else:
                    # Fallback for agents without get_capabilities method
                    modes[mode_name] = {
                        "name": f"{mode_name.title()} Agent",
                        "description": f"Handles {mode_name} response mode",
                        "response_type": mode_name
                    }
            except Exception as e:
                logger.warning(f"Error getting capabilities for {mode_name}: {str(e)}")
                modes[mode_name] = {
                    "name": f"{mode_name.title()} Agent",
                    "description": f"Handles {mode_name} response mode",
                    "response_type": mode_name,
                    "status": "error"
                }
        
        return modes
    
    def validate_mode(self, response_mode: str) -> bool:
        """
        Validate if a response mode is supported.
        
        Args:
            response_mode: The response mode to validate
            
        Returns:
            True if the mode is supported
        """
        return response_mode in self.agents
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on all agents.
        
        Returns:
            Dict containing health status of all agents
        """
        health_status = {}
        
        for mode_name, agent in self.agents.items():
            try:
                # Simple validation check
                if hasattr(agent, 'validate_input'):
                    is_healthy = agent.validate_input("test")
                else:
                    is_healthy = True
                
                health_status[mode_name] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "agent_type": agent.__class__.__name__
                }
            except Exception as e:
                health_status[mode_name] = {
                    "status": "error",
                    "error": str(e),
                    "agent_type": agent.__class__.__name__
                }
        
        return health_status 