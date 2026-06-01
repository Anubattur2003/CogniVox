"""
General Response Agent

Provides direct, concise answers without complex reasoning chains.
Uses the base ollama chat agent with specialized prompting for straightforward responses.
"""

import logging
import time
from typing import Dict, Any, Optional
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from ..base_agent import BaseAgent
from .prompt import GENERAL_RESPONSE_PROMPT



logger = logging.getLogger(__name__)

class GeneralResponseAgent(BaseAgent):
    """
    Agent focused on providing direct, clear, and concise answers.
    Optimized for quick responses without showing complex reasoning.
    """
    
    def __init__(self, model_name: str = "mistral:latest"):
        """
        Initialize the General Response Agent.
        
        Args:
            model_name: The Ollama model to use for responses
        """
        super().__init__(
            agent_name="general_response_agent",
            model_name=model_name,
            provider="ollama",
            temperature=0.3
        )
        # self.llm is initialized by BaseAgent using the config-aware helper
        logger.info(f"General Response Agent initialized with model: {model_name}")
        
    def process_query(
        self, 
        user_message: str, 
        user_id: str = None, 
        context_prompt: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a user query and return a direct, concise response.
        
        Args:
            user_message: The user's question or request
            user_id: User identifier for context
            context_prompt: Additional context information
            **kwargs: Additional parameters
            
        Returns:
            Dict containing the response and metadata
        """
        try:
            logger.info(f"General Response Agent processing query for user {user_id}")
            

            # Create system and user messages
            prompt_start = time.time()
            system_message = SystemMessage(content=GENERAL_RESPONSE_PROMPT.format(
                context_prompt=context_prompt if context_prompt else "No additional context provided.",
                user_message=""
            ))
            user_msg = HumanMessage(content=user_message)
            prompt_time = time.time() - prompt_start
            logger.info(f"Prompt preparation took {prompt_time:.3f} seconds")
            
            # Get response from chat model
            start_time = time.time()
            logger.info(f"Invoking Mistral model for general response...")
            
            response = self.llm.invoke([system_message, user_msg])
            
            processing_time = time.time() - start_time
            logger.info(f"Mistral model response took {processing_time:.3f} seconds")
            
            if not response or not response.content:
                raise Exception("Failed to generate response from chat model")
            
            response_text = response.content
            
            return {
                "success": True,
                "response": response_text,
                "agent_type": "general_response",
                "model_used": self.model_name,
                "processing_time": processing_time,
                "thinking_steps": [],  # No visible thinking for general mode
                "used_tools": [],  # Direct response, no external tools
                "sources": []  # No sources for simple direct responses
            }
            
        except Exception as e:
            logger.error(f"Error in General Response Agent: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error generating a response. Please try again.",
                "agent_type": "general_response"
            }
    
    def validate_input(self, user_message: str) -> bool:
        """
        Validate input for general response processing.
        
        Args:
            user_message: The user's message
            
        Returns:
            True if input is valid
        """
        return bool(user_message and user_message.strip())
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of this agent.
        
        Returns:
            Dict describing agent capabilities
        """
        return {
            "name": "General Response Agent",
            "description": "Provides direct, concise answers without showing reasoning process",
            "response_type": "direct",
            "supports_thinking": False,
            "supports_tools": False,
            "supports_sources": False,
            "optimal_for": ["quick_answers", "simple_questions", "direct_information"]
        } 