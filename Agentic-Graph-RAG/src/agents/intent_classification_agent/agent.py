"""
Intent Classification Agent for determining optimal response styles.
"""
import json
import logging
from typing import Dict, Any, Optional

from ..base_agent import BaseAgent
from .prompt import INTENT_CLASSIFICATION_SYSTEM_PROMPT, create_intent_classification_prompt

logger = logging.getLogger("cogniVox.graphrag")

class IntentClassificationAgent(BaseAgent):
    """
    Agent specialized in classifying user intent and determining optimal response styles.
    
    This agent optimizes responses by:
    - Analyzing query characteristics and user intent
    - Recommending appropriate response format and tone
    - Determining optimal search strategy
    - Providing reasoning for classification decisions
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.3,  # Balanced temperature for consistent classification
        **kwargs
    ):
        """Initialize the Intent Classification Agent."""
        super().__init__(
            agent_name="intent_classification_agent",
            model_name=model_name,
            temperature=temperature,
            system_prompt=INTENT_CLASSIFICATION_SYSTEM_PROMPT,
            **kwargs
        )

    def classify_intent(self, query: str) -> Dict[str, Any]:
        """
        Classify user intent and recommend response style.
        
        Args:
            query: The user query to classify
            
        Returns:
            Dictionary containing response style recommendations and search strategy
        """
        # Handle very short queries with simplified classification
        if len(query.split()) < 2:
            return self._handle_short_query(query)
            
        try:
            # Create the classification prompt
            classification_prompt = create_intent_classification_prompt(query)
            
            # Call the LLM
            response = self.call_llm(classification_prompt, use_cache=True)
            
            # Parse and validate the response
            classification_result = self._parse_classification_response(response, query)
            
            logger.info(f"Intent classification completed for: {query[:50]}...")
            return classification_result
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return self._fallback_classification(query)

    def get_response_style(self, query: str) -> Dict[str, str]:
        """
        Get just the response style recommendations.
        
        Args:
            query: The user query to classify
            
        Returns:
            Dictionary containing response style parameters
        """
        result = self.classify_intent(query)
        return result.get("response_style", self._default_response_style())

    def get_search_strategy(self, query: str) -> Dict[str, str]:
        """
        Get search strategy recommendations.
        
        Args:
            query: The user query to classify
            
        Returns:
            Dictionary containing search strategy parameters
        """
        result = self.classify_intent(query)
        return result.get("search_strategy", self._default_search_strategy())

    def _parse_classification_response(self, content: str, original_query: str) -> Dict[str, Any]:
        """Parse and validate the classification response."""
        try:
            # Clean the JSON string
            cleaned_content = self._clean_json_string(content)
            
            # Parse JSON
            data = json.loads(cleaned_content)
            
            # Validate and complete the response
            return self._validate_classification_response(data, original_query)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {content}")
            return self._fallback_classification(original_query)
        except Exception as e:
            logger.error(f"Error processing classification response: {e}")
            return self._fallback_classification(original_query)

    def _clean_json_string(self, json_str: str) -> str:
        """Clean and extract JSON from the response with Qwen3:4b compatibility."""
        # Remove Qwen3 thinking tags that can interfere with JSON parsing
        if "<think>" in json_str and "</think>" in json_str:
            # Remove thinking sections
            import re
            json_str = re.sub(r'<think>.*?</think>', '', json_str, flags=re.DOTALL)
        
        # Remove other common thinking patterns
        json_str = re.sub(r'<thinking>.*?</thinking>', '', json_str, flags=re.DOTALL)
        json_str = re.sub(r'Let me think.*?(?=\{)', '', json_str, flags=re.DOTALL | re.IGNORECASE)
        
        # Find JSON block if surrounded by markdown
        start_markers = ["```json", "```"]
        end_marker = "```"
        
        for start_marker in start_markers:
            if start_marker in json_str:
                start_idx = json_str.find(start_marker) + len(start_marker)
                end_idx = json_str.find(end_marker, start_idx)
                if end_idx != -1:
                    json_str = json_str[start_idx:end_idx]
                break
        
        # Extract JSON from mixed content - look for first { to last }
        if '{' in json_str and '}' in json_str:
            start_idx = json_str.find('{')
            end_idx = json_str.rfind('}') + 1
            json_str = json_str[start_idx:end_idx]
        
        return json_str.strip()

    def _validate_classification_response(self, data: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """Validate and complete the classification response."""
        # Ensure response_style exists
        if "response_style" not in data:
            data["response_style"] = self._default_response_style()
        else:
            style = data["response_style"]
            style.setdefault("format", "detailed_explanation")
            style.setdefault("detail_level", "moderate")
            style.setdefault("tone", "conversational")
            style.setdefault("structure", "direct_answer")
        
        # Ensure search_strategy exists
        if "search_strategy" not in data:
            data["search_strategy"] = self._default_search_strategy()
        else:
            strategy = data["search_strategy"]
            strategy.setdefault("primary_mode", "hybrid")
            strategy.setdefault("complexity", "moderate")
        
        # Ensure other required fields
        data.setdefault("reasoning", "Query classified based on content analysis")
        data.setdefault("confidence_score", 0.8)
        
        return data

    def _handle_short_query(self, query: str) -> Dict[str, Any]:
        """Handle very short queries with simplified classification."""
        # Analyze the type of short query
        query_lower = query.lower()
        
        # Question words get different treatment
        if any(word in query_lower for word in ["what", "who", "when", "where", "why"]):
            response_format = "detailed_explanation"
            detail_level = "moderate"
        elif any(word in query_lower for word in ["how"]):
            response_format = "step_by_step"
            detail_level = "moderate"
        else:
            response_format = "concise_summary"
            detail_level = "brief"
        
        return {
            "response_style": {
                "format": response_format,
                "detail_level": detail_level,
                "tone": "conversational",
                "structure": "direct_answer"
            },
            "search_strategy": {
                "primary_mode": "hybrid",
                "complexity": "simple"
            },
            "reasoning": "Short query classification based on question type",
            "confidence_score": 0.7
        }

    def _fallback_classification(self, query: str) -> Dict[str, Any]:
        """Provide a fallback classification when LLM classification fails."""
        # Simple heuristics based on query characteristics
        query_lower = query.lower()
        
        # Check for comparison keywords
        if any(word in query_lower for word in ["vs", "versus", "compare", "difference", "better"]):
            response_format = "comparative_analysis"
            structure = "comparative_analysis"
        # Check for procedural keywords
        elif any(word in query_lower for word in ["how to", "steps", "process", "procedure"]):
            response_format = "step_by_step"
            structure = "direct_answer"
        # Check for list-type queries
        elif any(word in query_lower for word in ["list", "types", "kinds", "examples"]):
            response_format = "bullet_points"
            structure = "direct_answer"
        else:
            response_format = "detailed_explanation"
            structure = "contextual_explanation"
        
        return {
            "response_style": {
                "format": response_format,
                "detail_level": "moderate",
                "tone": "conversational",
                "structure": structure
            },
            "search_strategy": {
                "primary_mode": "hybrid",
                "complexity": "moderate"
            },
            "reasoning": "Fallback classification based on keyword heuristics",
            "confidence_score": 0.6  # Lower confidence for fallback
        }

    def _default_response_style(self) -> Dict[str, str]:
        """Get default response style."""
        return {
            "format": "detailed_explanation",
            "detail_level": "moderate",
            "tone": "conversational",
            "structure": "direct_answer"
        }

    def _default_search_strategy(self) -> Dict[str, str]:
        """Get default search strategy."""
        return {
            "primary_mode": "hybrid",
            "complexity": "moderate"
        } 