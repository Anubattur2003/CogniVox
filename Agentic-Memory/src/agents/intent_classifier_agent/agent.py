import logging
import sys
import os
import pathlib
from typing import List, Optional, Dict, Any, DefaultDict, Union
from collections import defaultdict
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Add parent directory to Python path to allow importing from src
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent))
from src.agents.base_agent import BaseAgent
from .prompt import intent_classifier_system_prompt

# Configure logger
logger = logging.getLogger("cogniVox")

class IntentClassifierAgent(BaseAgent):
    def __init__(
        self, 
        model_name: str = None, 
        provider: str = None,
        api_key: str = None,
        temperature: float = None, 
        base_url: str = None,
        system_prompt: str = intent_classifier_system_prompt,
        intent_schema: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """
        Initialize the Intent Classifier Agent.
        
        Args:
            model_name (str): Name of the model to use (overrides config)
            provider (str): LLM provider to use (overrides config)
            api_key (str): API key for the provider (overrides config)
            temperature (float): Temperature parameter for response generation (overrides config)
            base_url (str): The base URL of the API server (overrides config)
            system_prompt (str): The system prompt to set the context for intent classification
            intent_schema (Dict[str, str], optional): A dictionary mapping intent names to descriptions
            **kwargs: Additional configuration overrides
        """
        # If intent schema is provided, incorporate it into the system prompt
        if intent_schema:
            self.intent_schema = intent_schema
            schema_description = "Classify the intent according to the following schema:\n"
            for intent, description in intent_schema.items():
                schema_description += f"- {intent}: {description}\n"
            system_prompt = system_prompt + "\n\n" + schema_description
        else:
            self.intent_schema = {}
            
        super().__init__(
            agent_name="intent_classifier",
            model_name=model_name,
            provider=provider,
            api_key=api_key,
            temperature=temperature,
            base_url=base_url,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # Initialize message history
        self.messages = [SystemMessage(content=system_prompt)]
        
    def classify_intent(self, query: str, **kwargs) -> str:
        """
        Analyze a user query and return a recommended response style and format.
        
        Args:
            query (str): The user query to classify
            **kwargs: Additional parameters to pass to the LLM invoke method
            
        Returns:
            str: Description of the ideal response style and format
        """
        try:
            # Reset message history to only include system prompt
            self.messages = [SystemMessage(content=self.system_prompt)]
            
            # Add user query to conversation
            self.messages.append(HumanMessage(content=query))
            
            # Get AI response
            response = self.llm.invoke(self.messages, **kwargs)
            
            # Return the response content as is
            return response.content
        except Exception as e:
            logger.error(f"Error in intent classification: {str(e)}")
            # Return a default response style
            return "Provide a clear, informative response that directly addresses the user's query with appropriate detail level."
    
    def update_intent_schema(self, intent_schema: Dict[str, str]):
        """
        Update the intent classification schema.
        
        Args:
            intent_schema (Dict[str, str]): A dictionary mapping intent names to descriptions
        """
        self.intent_schema = intent_schema
        
        # Regenerate system prompt with new schema
        base_prompt = self.system_prompt.split("\n\nClassify the intent according")[0]
        schema_description = "Classify the intent according to the following schema:\n"
        for intent, description in intent_schema.items():
            schema_description += f"- {intent}: {description}\n"
        
        self.system_prompt = base_prompt + "\n\n" + schema_description
        self.messages = [SystemMessage(content=self.system_prompt)]
        return self
    
    def update_system_prompt(self, system_prompt: str):
        """
        Update the system prompt for the intent classifier agent.
        
        Args:
            system_prompt (str): The new system prompt
        """
        # Preserve intent schema if it exists
        if self.intent_schema:
            schema_description = "Classify the intent according to the following schema:\n"
            for intent, description in self.intent_schema.items():
                schema_description += f"- {intent}: {description}\n"
            self.system_prompt = system_prompt + "\n\n" + schema_description
        else:
            self.system_prompt = system_prompt
            
        self.messages = [SystemMessage(content=self.system_prompt)]
        return self
    
    def update_model(self, model_name: str = None, provider: str = None, api_key: str = None, **kwargs):
        """
        Update the model configuration and reinitialize the LLM.
        
        Args:
            model_name (str): New model name
            provider (str): New provider
            api_key (str): New API key
            **kwargs: Additional configuration updates
        """
        if model_name is not None:
            self.model_name = model_name
        if provider is not None:
            self.provider = provider
        if api_key is not None:
            self.api_key = api_key
        
        self.kwargs.update(kwargs)
        
        try:
            self.llm = self._create_llm()
            logger.info("Intent classifier model updated successfully")
        except Exception as e:
            logger.error(f"Error updating model: {str(e)}")
            raise
    
    def update_temperature(self, temperature: float):
        """
        Update the temperature parameter.
        
        Args:
            temperature (float): The new temperature value
        """
        self.temperature = temperature
        try:
            self.llm = self._create_llm()
            logger.info("Intent classifier temperature updated successfully")
        except Exception as e:
            logger.error(f"Error updating temperature: {str(e)}")
            raise
        return self 