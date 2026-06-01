import logging
import sys
import os
import pathlib
from typing import List, Optional, Dict, Any, DefaultDict
from collections import defaultdict
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Add parent directory to Python path to allow importing from src
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent))
from src.agents.base_agent import BaseAgent
from .prompt import query_expansion_system_prompt

# Configure logger
logger = logging.getLogger("cogniVox")

class QueryExpansionAgent(BaseAgent):
    def __init__(
        self,
        model_name: str = None,
        provider: str = None,
        api_key: str = None,
        temperature: float = None,
        base_url: str = None,
        system_prompt: str = query_expansion_system_prompt,
        **kwargs,
    ):
        """Initialize the Query Expansion Agent."""
        super().__init__(
            agent_name="query_expansion",
            model_name=model_name,
            provider=provider,
            api_key=api_key,
            temperature=temperature,
            base_url=base_url,
            system_prompt=system_prompt,
            **kwargs,
        )

        # Initialize message history with system prompt
        self.messages = [SystemMessage(content=self.system_prompt)]
    
    def expand_query(self, query: str, **kwargs) -> str:
        """
        Expand the user's query to cover relevant aspects without changing intent.
        
        Args:
            query (str): The original user query to expand
            **kwargs: Additional parameters to pass to the LLM invoke method
            
        Returns:
            str: The expanded query
        """
        try:
            # Reset message history to only include system prompt
            self.messages = [SystemMessage(content=self.system_prompt)]
            
            # Add user query to conversation
            self.messages.append(HumanMessage(content=query))
            
            # Get AI response
            response = self.llm.invoke(self.messages, **kwargs)
            
            # Return expanded query
            return response.content
        except Exception as e:
            logger.error(f"Error in query expansion: {str(e)}")
            # Return original query if expansion fails
            return query
    
    def update_system_prompt(self, system_prompt: str):
        """
        Update the system prompt for the query expansion agent.
        
        Args:
            system_prompt (str): The new system prompt
        """
        self.system_prompt = system_prompt
        self.messages = [SystemMessage(content=system_prompt)]
        return self
    
    # update_model and update_temperature inherited from BaseAgent 