"""
Context Relevance Agent for intelligent context selection.

This agent is responsible for finding the most contextually relevant messages
from chat history based on user queries.
"""
import os
import time
import json
import logging
from typing import Dict, List, Any, Tuple, Optional
from langchain_core.messages import SystemMessage, HumanMessage

from src.utils.execution_timer import timed_method
from src.agents.base_agent import BaseAgent
from src.gpu_manager.decorators import gpu_required
from src.gpu_manager.text_utils import text_encoder
from .prompt import context_relevance_system_prompt, context_relevance_selection_prompt

# Configure logging for context relevance operations
context_logger = logging.getLogger('context_relevance')

class ContextRelevanceAgent(BaseAgent):
    """
    Agent for finding the most contextually relevant messages from conversation history.
    
    This agent uses LLM reasoning to:
    1. Analyze the semantic relationship between a query and conversation history
    2. Identify and rank messages by relevance to the current query
    3. Select a subset of most relevant messages to provide as context
    4. Explain the reasoning behind message selection
    """
    
    def __init__(
        self, 
        model_name: str = None, 
        temperature: float = None, 
        provider: str = None,
        api_key: str = None,
        use_gpu_similarity: bool = None,
        system_prompt: str = context_relevance_system_prompt,
        **kwargs
    ):
        """
        Initialize the Context Relevance Agent.
        
        Args:
            model_name (str): Name of the model to use (overrides config)
            temperature (float): Temperature parameter for relevance assessment (overrides config)
            provider (str): LLM provider to use (overrides config)
            api_key (str): API key for the provider (overrides config)
            use_gpu_similarity (bool): Whether to use GPU for similarity calculations (overrides config)
            system_prompt (str): The system prompt for context relevance
            **kwargs: Additional configuration overrides
        """
        super().__init__(
            agent_name="context_relevance",
            model_name=model_name,
            provider=provider,
            api_key=api_key,
            temperature=temperature,
            **kwargs
        )
        
        # Determine GPU similarity setting
        if use_gpu_similarity is not None:
            self.use_gpu_similarity = use_gpu_similarity
        else:
            self.use_gpu_similarity = (
                self.agent_config.get("use_gpu_similarity", True) and 
                self.config.get_gpu_config().get("enable_gpu_acceleration", False)
            )
        
        # System prompt for context relevance
        self.system_prompt = system_prompt
    
    @timed_method
    def extract_relevant_context(self, query: str, history: List[Dict[str, Any]], 
                               max_items: int = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Extract the most contextually relevant items from history based on the query.
        
        Args:
            query: The user query to find relevant context for
            history: List of conversation history items
            max_items: Maximum number of items to return (overrides config)
            
        Returns:
            Tuple containing:
            - List of the most relevant history messages
            - Decision information from the agent
        """
        if not history or not query:
            return [], {"reasoning": "No history or query provided"}
            
        # Use configured max_items if not provided
        if max_items is None:
            max_items = self.agent_config.get("max_relevant_items", 5)
        
        # First try semantic similarity for faster relevance scoring
        if self.use_gpu_similarity:
            try:
                semantic_results = self._get_semantic_relevance(query, history, max_items)
                if semantic_results:
                    context_logger.info(f"Selected {len(semantic_results)} items using GPU-accelerated semantic similarity")
                    return semantic_results, {
                        "reasoning": "Selected items using semantic similarity with GPU acceleration",
                        "method": "semantic_similarity",
                        "items_count": len(semantic_results)
                    }
            except Exception as e:
                context_logger.warning(f"Error in semantic similarity: {str(e)}, falling back to LLM")
        
        # Prepare the prompt for context relevance decision using the template
        prompt = context_relevance_selection_prompt.format(
            query=query,
            history=json.dumps(history[-20:], indent=2),  # Limit to last 20 items for prompt size
            max_items=max_items
        )

        try:
            # Use LangChain chat model
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse the response
            try:
                decision = self._extract_json_safely(response.content)
                
                # Extract the relevant items from history
                relevant_items = []
                if "relevant_indices" in decision:
                    for idx in decision["relevant_indices"]:
                        if 0 <= idx < len(history):
                            item = history[idx]
                            # Ensure item has required keys
                            if not isinstance(item, dict):
                                item = {"content": str(item), "role": "system"}
                            elif "role" not in item:
                                item = {**item, "role": "system"}
                            elif "content" not in item:
                                item = {**item, "content": ""}
                            relevant_items.append(item)
                
                # If no relevant items found, fall back to most recent items that might be relevant
                if not relevant_items:
                    context_logger.warning("No relevant items identified by LLM, falling back to keyword-based selection")
                    relevant_items = self._keyword_based_fallback(query, history, max_items)
                    decision["reasoning"] = "LLM selection failed, used keyword-based fallback"
                
                context_logger.info(f"Selected {len(relevant_items)} relevant context items using LLM analysis")
                return relevant_items, decision
                
            except (json.JSONDecodeError, KeyError) as e:
                context_logger.warning(f"Could not parse LLM response: {str(e)}, falling back to keyword-based selection")
                relevant_items = self._keyword_based_fallback(query, history, max_items)
                return relevant_items, {"reasoning": "LLM response parsing failed, used keyword-based fallback"}
            
        except Exception as e:
            context_logger.error(f"Error in LLM-based context relevance: {str(e)}")
            # Fall back to keyword-based selection
            relevant_items = self._keyword_based_fallback(query, history, max_items)
            return relevant_items, {"reasoning": "LLM error, used keyword-based fallback"}
    
    @gpu_required(owner_param=None, device_param="device_id")
    def _get_semantic_relevance(self, query: str, history: List[Dict[str, Any]], 
                               max_items: int, device_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Use GPU-accelerated semantic similarity to find relevant context.
        
        Args:
            query: The user query
            history: List of history items
            max_items: Maximum number of items to return
            device_id: GPU device ID (injected by decorator)
            
        Returns:
            List of most semantically relevant items
        """
        try:
            # Extract text content from history items
            history_texts = []
            for item in history:
                if isinstance(item, dict):
                    content = item.get("content", "") or item.get("message", "")
                else:
                    content = str(item)
                history_texts.append(content)
            
            # Compute similarities using GPU-accelerated encoding
            similarities = text_encoder.compute_similarities(
                query, 
                history_texts,
                device_id=device_id
            )
            
            # Get top relevant items based on similarity scores
            top_indices = similarities.argsort()[-max_items:][::-1]  # Descending order
            
            relevant_items = []
            for idx in top_indices:
                if idx < len(history):
                    item = history[idx]
                    # Ensure proper format
                    if not isinstance(item, dict):
                        item = {"content": str(item), "role": "system"}
                    elif "role" not in item:
                        item = {**item, "role": "system"}
                    elif "content" not in item:
                        item = {**item, "content": ""}
                    relevant_items.append(item)
            
            return relevant_items
            
        except Exception as e:
            context_logger.error(f"Error in GPU semantic similarity: {str(e)}")
            return []
    
    def _keyword_based_fallback(self, query: str, history: List[Dict[str, Any]], 
                              max_items: int) -> List[Dict[str, Any]]:
        """
        Fallback method using keyword matching for context relevance.
        
        Args:
            query: The user query
            history: List of history items
            max_items: Maximum number of items to return
            
        Returns:
            List of potentially relevant items based on keyword matching
        """
        # Extract keywords from query (simple approach)
        query_words = set(query.lower().split())
        
        # Score each history item based on keyword overlap
        scored_items = []
        for i, item in enumerate(history):
            if isinstance(item, dict):
                content = item.get("content", "") or item.get("message", "")
            else:
                content = str(item)
            
            content_words = set(content.lower().split())
            overlap = len(query_words.intersection(content_words))
            
            if overlap > 0:
                scored_items.append((overlap, i, item))
        
        # Sort by score and get top items
        scored_items.sort(reverse=True, key=lambda x: x[0])
        
        relevant_items = []
        for _, _, item in scored_items[:max_items]:
            # Ensure proper format
            if not isinstance(item, dict):
                item = {"content": str(item), "role": "system"}
            elif "role" not in item:
                item = {**item, "role": "system"}
            elif "content" not in item:
                item = {**item, "content": ""}
            relevant_items.append(item)
        
        # If no keyword matches, fall back to most recent items
        if not relevant_items:
            relevant_items = self._most_recent_fallback(history, max_items)
        
        return relevant_items
    
    def _most_recent_fallback(self, history: List[Dict[str, Any]], max_items: int) -> List[Dict[str, Any]]:
        """
        Final fallback: return the most recent items from history.
        
        Args:
            history: List of history items
            max_items: Maximum number of items to return
            
        Returns:
            List of most recent items
        """
        recent_items = history[-max_items:] if history else []
        
        # Ensure proper format for all items
        formatted_items = []
        for item in recent_items:
            if not isinstance(item, dict):
                item = {"content": str(item), "role": "system"}
            elif "role" not in item:
                item = {**item, "role": "system"}
            elif "content" not in item:
                item = {**item, "content": ""}
            formatted_items.append(item)
        
        return formatted_items
    
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
            context_logger.warning(f"Could not parse JSON from response: {str(e)}")
            return {} 