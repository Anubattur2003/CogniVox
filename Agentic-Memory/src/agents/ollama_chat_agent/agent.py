from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import List, Optional, Dict, Any, DefaultDict
import os
from collections import defaultdict
from src.agents.base_agent import BaseAgent
from .prompt import ollama_chat_system_prompt
import logging

# Configure logger
logger = logging.getLogger("cogniVox")

class OllamaChatAgent(BaseAgent):
    def __init__(
        self, 
        model_name: str = None, 
        temperature: float = None, 
        provider: str = None,
        api_key: str = None,
        system_prompt: str = None,
        **kwargs
    ):
        """
        Initialize the Ollama Chat Agent.
        
        Args:
            model_name (str): Name of the model to use (overrides config)
            temperature (float): Temperature parameter for response generation (overrides config)
            provider (str): LLM provider to use (overrides config)
            api_key (str): API key for the provider (overrides config)
            system_prompt (str): The system prompt to set the context for the chat (overrides config)
            **kwargs: Additional configuration overrides
        """
        # Determine the system prompt before calling super
        effective_system_prompt = system_prompt or ollama_chat_system_prompt
        
        super().__init__(
            agent_name="ollama_chat",
            model_name=model_name,
            provider=provider,
            api_key=api_key,
            temperature=temperature,
            system_prompt=effective_system_prompt,
            **kwargs
        )
        
        # Get max history setting
        self.max_history_per_user = self.agent_config.get("max_history_per_user", 50)
        
        # Initialize user-based message histories
        self.user_messages: DefaultDict[str, List[SystemMessage | HumanMessage | AIMessage]] = defaultdict(list)
        
        # Default user for backward compatibility
        self.default_user_id = "default"
        self.initialize_chat(self.system_prompt, self.default_user_id)
        
    def initialize_chat(self, system_prompt: Optional[str] = None, user_id: str = None):
        """
        Initialize or reset the chat with a system prompt for a specific user.
        
        Args:
            system_prompt (str, optional): The system prompt to set the context for the chat.
                                        If None, uses the default prompt set during initialization.
            user_id (str, optional): The user identifier. If None, uses the default user.
        """
        if system_prompt is None:
            system_prompt = self.system_prompt
            
        user_id = user_id or self.default_user_id
        self.user_messages[user_id] = [SystemMessage(content=system_prompt)]
        return self
        
    def chat(self, user_message: str, user_id: str = None, **kwargs) -> Optional[str]:
        """
        Process a user message and return the AI's response.
        
        Args:
            user_message (str): The user's input message
            user_id (str, optional): The user identifier. If None, uses the default user.
            **kwargs: Additional parameters to pass to the LLM invoke method
            
        Returns:
            Optional[str]: The AI's response message
        """
        user_id = user_id or self.default_user_id
        
        # Initialize chat for this user if it doesn't exist
        if not self.user_messages.get(user_id):
            self.initialize_chat(self.system_prompt, user_id)
            
        # Get the message history for this user
        messages = self.user_messages[user_id]
        
        # Trim history if it's too long
        if len(messages) > self.max_history_per_user:
            # Keep system message and most recent messages
            system_msg = messages[0]
            recent_messages = messages[-(self.max_history_per_user-1):]
            messages = [system_msg] + recent_messages
            self.user_messages[user_id] = messages
        
        # Add user message to conversation history
        messages.append(HumanMessage(content=user_message))
        
        try:
            # Get AI response
            response = self.llm.invoke(messages, **kwargs)
            
            # Add AI response to conversation history
            messages.append(response)
            
            return response.content
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            # Remove the user message we just added since response failed
            if messages and isinstance(messages[-1], HumanMessage):
                messages.pop()
            return None
    
    def get_chat_history(self, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Get the chat history in a structured format for a specific user.
        
        Args:
            user_id (str, optional): The user identifier. If None, uses the default user.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries with 'role' and 'content' keys
        """
        user_id = user_id or self.default_user_id
        history = []
        
        messages = self.user_messages.get(user_id, [])
        for message in messages:
            if isinstance(message, SystemMessage):
                role = "system"
            elif isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            else:
                role = "unknown"
                
            history.append({
                "role": role,
                "content": message.content
            })
        return history
    
    def clear_history(self, user_id: str = None):
        """
        Clear the chat history except for the system prompt for a specific user.
        
        Args:
            user_id (str, optional): The user identifier. If None, uses the default user.
        """
        user_id = user_id or self.default_user_id
        
        # Get the system prompt from existing history or use default
        messages = self.user_messages.get(user_id, [])
        system_prompt = messages[0].content if messages else self.system_prompt
        
        self.initialize_chat(system_prompt, user_id)
        return self
    
    def clear_all_histories(self):
        """
        Clear chat histories for all users.
        """
        self.user_messages.clear()
        self.initialize_chat(self.system_prompt, self.default_user_id)
        return self
    
    def get_all_user_ids(self):
        """
        Get all user IDs that have chat histories.
        
        Returns:
            List[str]: List of user IDs
        """
        return list(self.user_messages.keys())
    
    def update_system_prompt(self, system_prompt: str, user_id: str = None):
        """
        Update the system prompt for a specific user or all users.
        
        Args:
            system_prompt (str): The new system prompt
            user_id (str, optional): The user identifier. If None, updates for default user.
        """
        self.system_prompt = system_prompt
        
        if user_id:
            self.initialize_chat(system_prompt, user_id)
        else:
            # Update for default user
            self.initialize_chat(system_prompt, self.default_user_id)
        return self 