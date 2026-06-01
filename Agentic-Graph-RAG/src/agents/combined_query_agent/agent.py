"""
Combined Query Processing Agent for efficient query expansion and intent classification.
"""
import json
import logging
from typing import Dict, Any, Optional, List

from ..base_agent import BaseAgent
from .prompt import COMBINED_QUERY_SYSTEM_PROMPT, create_combined_query_prompt

logger = logging.getLogger(__name__)

class CombinedQueryAgent(BaseAgent):
    """
    Combined agent that performs both query expansion and intent classification in a single LLM call.
    
    This agent dramatically improves performance by:
    - Eliminating redundant LLM calls (2→1)
    - Reducing total processing time
    - Maintaining high quality results
    - Simplifying the processing pipeline
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.3,  # Balanced for consistent analysis
        timeout: float = 30.0,     # Single call timeout
        **kwargs
    ):
        """Initialize the Combined Query Processing Agent."""
        super().__init__(
            agent_name="combined_query_agent",
            model_name=model_name,
            temperature=temperature,
            system_prompt=COMBINED_QUERY_SYSTEM_PROMPT,
            **kwargs
        )
        self.timeout = timeout

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query with combined expansion and classification.
        
        Args:
            query: The original user query
            
        Returns:
            Dictionary containing both expansion and classification results
        """
        # Handle very short queries with simplified processing
        if len(query.split()) < 2:
            return self._handle_short_query(query)
            
        try:
            # Create the combined processing prompt
            processing_prompt = create_combined_query_prompt(query)
            
            # Single LLM call for both tasks
            response = self.call_llm(processing_prompt, use_cache=True)
            
            # Parse and validate the response
            result = self._parse_combined_response(response, query)
            
            logger.info(f"Combined query processing completed for: {query[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Combined query processing failed: {e}")
            return self._fallback_processing(query)

    def _parse_combined_response(self, content: str, original_query: str) -> Dict[str, Any]:
        """
        Parse the LLM response containing both expansion and classification.
        
        Args:
            content: Raw LLM response content
            original_query: Original user query for fallback
            
        Returns:
            Parsed and validated combined results
        """
        try:
            # Remove Qwen3 thinking tags that can interfere with JSON parsing
            if "<think>" in content and "</think>" in content:
                import re
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            
            # Remove other common thinking patterns
            content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL)
            content = re.sub(r'Let me think.*?(?=\{)', '', content, flags=re.DOTALL | re.IGNORECASE)
            
            # Try to parse JSON response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Clean up common JSON issues
            content = content.strip()
            if not content.startswith("{"):
                # Extract JSON from response
                start = content.find("{")
                end = content.rfind("}") + 1
                if start != -1 and end > start:
                    content = content[start:end]
            
            result = json.loads(content)
            
            # Validate required fields
            required_fields = ["expanded_query", "intent_type", "search_strategy"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure all fields have reasonable defaults
            result.setdefault("search_keywords", self._extract_keywords_fallback(original_query))
            result.setdefault("response_style", "detailed")
            result.setdefault("confidence_score", 0.7)
            result.setdefault("reasoning", "Analysis completed successfully")
            
            # Validate enum values
            valid_intents = ["factual", "procedural", "comparative", "exploratory", "specific_lookup"]
            if result["intent_type"] not in valid_intents:
                result["intent_type"] = "factual"
                
            valid_strategies = ["semantic", "keyword", "hybrid"]
            if result["search_strategy"] not in valid_strategies:
                result["search_strategy"] = "hybrid"
                
            valid_styles = ["brief", "detailed", "structured", "conversational"]
            if result["response_style"] not in valid_styles:
                result["response_style"] = "detailed"
            
            return result
            
        except Exception as e:
            logger.warning(f"Failed to parse combined response: {e}")
            return self._fallback_processing(original_query)

    def _handle_short_query(self, query: str) -> Dict[str, Any]:
        """
        Handle very short queries with simplified processing.
        
        Args:
            query: Short user query
            
        Returns:
            Simplified processing results
        """
        return {
            "expanded_query": f"{query} definition explanation overview",
            "search_keywords": [query.lower()],
            "intent_type": "specific_lookup",
            "response_style": "brief",
            "search_strategy": "hybrid",
            "confidence_score": 0.6,
            "reasoning": "Short query - simplified processing"
        }

    def _fallback_processing(self, query: str) -> Dict[str, Any]:
        """
        Fallback processing when LLM call fails.
        
        Args:
            query: Original user query
            
        Returns:
            Basic processing results
        """
        # Simple keyword extraction
        keywords = self._extract_keywords_fallback(query)
        
        # Basic intent classification based on query patterns
        query_lower = query.lower()
        if any(word in query_lower for word in ["what", "define", "meaning"]):
            intent_type = "factual"
            response_style = "detailed"
        elif any(word in query_lower for word in ["how", "step", "process"]):
            intent_type = "procedural"
            response_style = "structured"
        elif any(word in query_lower for word in ["find", "locate", "show"]):
            intent_type = "specific_lookup"
            response_style = "brief"
        else:
            intent_type = "exploratory"
            response_style = "conversational"
        
        return {
            "expanded_query": f"{query} {' '.join(keywords)}",
            "search_keywords": keywords,
            "intent_type": intent_type,
            "response_style": response_style,
            "search_strategy": "hybrid",
            "confidence_score": 0.5,
            "reasoning": "Fallback processing - LLM call failed"
        }

    def _extract_keywords_fallback(self, query: str) -> List[str]:
        """
        Extract keywords from query as fallback.
        
        Args:
            query: User query
            
        Returns:
            List of extracted keywords
        """
        # Simple keyword extraction
        stop_words = {"a", "an", "the", "and", "or", "but", "is", "are", "was", "were",
                     "be", "been", "being", "in", "on", "at", "to", "for", "with", 
                     "by", "about", "what", "how", "when", "where", "why", "which"}
        
        words = query.lower().split()
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Return top 5 keywords
        return keywords[:5]

    # Convenience methods for backward compatibility
    def expand_query(self, query: str) -> Dict[str, Any]:
        """Get expansion-focused results."""
        result = self.process_query(query)
        return {
            "expanded_query": result["expanded_query"],
            "search_keywords": result["search_keywords"],
            "confidence_score": result["confidence_score"]
        }

    def classify_intent(self, query: str) -> Dict[str, Any]:
        """Get classification-focused results."""
        result = self.process_query(query)
        return {
            "intent_type": result["intent_type"],
            "response_style": result["response_style"],
            "search_strategy": result["search_strategy"],
            "confidence_score": result["confidence_score"]
        }
