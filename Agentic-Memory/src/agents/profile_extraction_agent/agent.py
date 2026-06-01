"""
Profile Extraction Agent for user information management.

This agent is responsible for extracting and updating user profile information
from chat conversations, using LLM reasoning to identify and store personal details.
"""
import os
import time
import json
import logging
from typing import Dict, List, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage

from src.utils.execution_timer import timed_method
from src.agents.base_agent import BaseAgent
from .prompt import profile_update_prompt, profile_extraction_prompt, profile_update_input_prompt, profile_extraction_input_prompt

# Configure logging for profile extraction operations
profile_logger = logging.getLogger('profile_extraction')

class ProfileExtractionAgent(BaseAgent):
    """
    Agent for extracting and managing user profile information from conversations.
    
    This agent uses LLM reasoning to:
    1. Extract personal information from user messages
    2. Update existing profiles with new information
    3. Generate profiles on-the-fly when needed
    4. Manage the storage and retrieval of profile data
    """
    
    def __init__(
        self, 
        model_name: str = None, 
        temperature: float = None, 
        provider: str = None,
        api_key: str = None,
        **kwargs
    ):
        """
        Initialize the Profile Extraction Agent.
        
        Args:
            model_name (str): Name of the model to use (overrides config)
            temperature (float): Temperature parameter for extraction (overrides config)
            provider (str): LLM provider to use (overrides config)
            api_key (str): API key for the provider (overrides config)
            **kwargs: Additional configuration overrides
        """
        super().__init__(
            agent_name="profile_extraction",
            model_name=model_name,
            provider=provider,
            api_key=api_key,
            temperature=temperature,
            **kwargs
        )
        
        # Import system prompts for different extraction tasks
        self.profile_update_prompt = profile_update_prompt
        self.profile_extraction_prompt = profile_extraction_prompt
    
    @timed_method
    def update_user_profile(self, current_profile: Dict[str, Any], 
                           latest_message: str, recent_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update user profile with information from the latest message.
        
        Args:
            current_profile: Existing user profile data
            latest_message: The latest user message to extract information from
            recent_history: Recent conversation history for context (optional)
            
        Returns:
            Dict containing updated profile information
        """
        if not current_profile:
            current_profile = {"created_at": time.time()}
        
        # Prepare the prompt for information extraction
        history_context = ""
        if recent_history:
            history_context = f"""
And these recent messages:
```
{json.dumps(recent_history, indent=2)}
```
"""
        
        # Use the prompt template instead of hardcoded prompt
        prompt = profile_update_input_prompt.format(
            current_profile=json.dumps(current_profile, indent=2),
            history_context=history_context,
            latest_message=latest_message
        )

        try:
            # Use LangChain chat model
            messages = [
                SystemMessage(content=self.profile_update_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Extract JSON response (with fallback parsing)
            extracted_info = self._extract_json_safely(response.content)
                
            # Only update if we have new information
            if extracted_info:
                # Update profile
                updated_profile = {**current_profile, **extracted_info, "last_updated": time.time()}
                profile_logger.info(f"Updated user profile with {len(extracted_info)} new fields")
                return updated_profile
            
            profile_logger.info("No new profile information found in latest message")
            return current_profile
                
        except Exception as e:
            profile_logger.error(f"Error updating user profile: {str(e)}")
            return current_profile
    
    @timed_method
    def extract_personal_information(self, conversation_history: List[Dict[str, Any]], 
                                   query: str = "") -> Dict[str, Any]:
        """
        Extract personal information from conversation history.
        
        Args:
            conversation_history: User conversation history
            query: Current query for context (optional)
            
        Returns:
            Dict containing extracted personal information
        """
        if not conversation_history:
            return {}
            
        # Get max history items from config
        max_history_items = self.agent_config.get("max_history_items", 20)
        
        # Use the prompt template instead of hardcoded prompt
        prompt = profile_extraction_input_prompt.format(
            conversation_history=json.dumps(conversation_history[-max_history_items:], indent=2),
            query=query
        )

        try:
            # Use LangChain chat model for extraction
            messages = [
                SystemMessage(content=self.profile_extraction_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse and return extracted information
            extracted_info = self._extract_json_safely(response.content)
            
            if extracted_info:
                profile_logger.info(f"Extracted {len(extracted_info)} profile fields from conversation")
                return {"extracted_at": time.time(), **extracted_info}
            else:
                profile_logger.info("No personal information found in conversation")
                return {}
                
        except Exception as e:
            profile_logger.error(f"Error extracting personal information: {str(e)}")
            return {}
    
    def _extract_json_safely(self, text: str) -> Dict[str, Any]:
        """
        Safely extract JSON from text response.
        
        Args:
            text: Response text that may contain JSON
            
        Returns:
            Parsed JSON dict or empty dict if parsing fails
        """
        try:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                return {}
        except (json.JSONDecodeError, AttributeError) as e:
            profile_logger.warning(f"Could not parse JSON from response: {str(e)}")
            return {}
    
    def _rule_based_extraction(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Simple rule-based extraction as fallback.
        
        Args:
            history: Conversation history
            
        Returns:
            Extracted information using simple patterns
        """
        profile = {}
        
        # Simple patterns for common information
        name_patterns = [
            r"my name is (\w+)",
            r"i'm (\w+)",
            r"call me (\w+)"
        ]
        
        for entry in history:
            content = entry.get("content", "").lower()
            
            # Try to find name
            import re
            for pattern in name_patterns:
                match = re.search(pattern, content)
                if match and "name" not in profile:
                    profile["name"] = match.group(1).title()
        
        return profile 