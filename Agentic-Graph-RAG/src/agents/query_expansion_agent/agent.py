"""
Query Expansion Agent for enhancing user queries for better retrieval.
"""
import json
import logging
from typing import Dict, Any, Optional, List

from ..base_agent import BaseAgent
from .prompt import QUERY_EXPANSION_SYSTEM_PROMPT, create_query_expansion_prompt

logger = logging.getLogger("cogniVox.graphrag")

class QueryExpansionAgent(BaseAgent):
    """
    Agent specialized in expanding user queries for improved information retrieval.
    
    This agent optimizes search by:
    - Adding relevant synonyms and related terms
    - Including technical terminology when appropriate
    - Preserving original query intent
    - Providing search optimization keywords
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.3,  # Balanced temperature for creativity with consistency
        timeout: float = 30.0,     # OPTIMIZATION: 30s timeout for Qwen3:4b
        **kwargs
    ):
        """Initialize the Query Expansion Agent."""
        super().__init__(
            agent_name="query_expansion_agent",
            model_name=model_name,
            temperature=temperature,
            system_prompt=QUERY_EXPANSION_SYSTEM_PROMPT,
            **kwargs
        )

    def expand_query(self, query: str) -> Dict[str, Any]:
        """
        Expand a user query for better information retrieval.
        
        Args:
            query: The original user query
            
        Returns:
            Dictionary containing expanded query and expansion details
        """
        # Handle very short queries with simplified expansion
        if len(query.split()) < 3:
            return self._handle_short_query(query)
            
        try:
            # Create the expansion prompt
            expansion_prompt = create_query_expansion_prompt(query)
            
            # Call the LLM
            response = self.call_llm(expansion_prompt, use_cache=True)
            
            # Parse and validate the response
            expansion_result = self._parse_expansion_response(response, query)
            
            logger.info(f"Query expansion completed for: {query[:50]}...")
            return expansion_result
            
        except Exception as e:
            logger.error(f"Query expansion failed: {e}")
            return self._fallback_expansion(query)

    def get_expanded_query(self, query: str) -> str:
        """
        Get just the expanded query string.
        
        Args:
            query: The original user query
            
        Returns:
            The expanded query string
        """
        result = self.expand_query(query)
        return result.get("expanded_query", query)

    def get_search_keywords(self, query: str) -> List[str]:
        """
        Get optimized search keywords from query expansion.
        
        Args:
            query: The original user query
            
        Returns:
            List of search keywords
        """
        result = self.expand_query(query)
        return result.get("search_keywords", self._extract_keywords_fallback(query))

    def _parse_expansion_response(self, content: str, original_query: str) -> Dict[str, Any]:
        """Parse and validate the expansion response."""
        try:
            # Clean the JSON string
            cleaned_content = self._clean_json_string(content)
            
            # Parse JSON
            data = json.loads(cleaned_content)
            
            # Validate and complete the response
            return self._validate_expansion_response(data, original_query)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {content}")
            return self._fallback_expansion(original_query)
        except Exception as e:
            logger.error(f"Error processing expansion response: {e}")
            return self._fallback_expansion(original_query)

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

    def _validate_expansion_response(self, data: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """Validate and complete the expansion response."""
        # Ensure required fields exist
        data.setdefault("expanded_query", original_query)
        data.setdefault("original_intent_preserved", True)
        data.setdefault("confidence_score", 0.8)
        
        # Ensure expansion_strategy exists
        if "expansion_strategy" not in data:
            data["expansion_strategy"] = {}
        
        strategy = data["expansion_strategy"]
        strategy.setdefault("added_synonyms", [])
        strategy.setdefault("added_context", [])
        strategy.setdefault("technical_terms", [])
        strategy.setdefault("expansion_reasoning", "Query expanded for better retrieval")
        
        # Ensure search_keywords exists
        if "search_keywords" not in data:
            data["search_keywords"] = self._extract_keywords_fallback(original_query)
        
        return data

    def _handle_short_query(self, query: str) -> Dict[str, Any]:
        """Handle very short queries with simplified expansion."""
        # For very short queries, use simple synonym expansion
        expanded = self._simple_expand_query(query)
        keywords = self._extract_keywords_fallback(query)
        
        return {
            "expanded_query": expanded,
            "original_intent_preserved": True,
            "expansion_strategy": {
                "added_synonyms": [],
                "added_context": [],
                "technical_terms": [],
                "expansion_reasoning": "Simple expansion for short query"
            },
            "search_keywords": keywords,
            "confidence_score": 0.7
        }

    def _fallback_expansion(self, query: str) -> Dict[str, Any]:
        """Provide a fallback expansion when LLM expansion fails."""
        expanded = self._simple_expand_query(query)
        keywords = self._extract_keywords_fallback(query)
        
        return {
            "expanded_query": expanded,
            "original_intent_preserved": True,
            "expansion_strategy": {
                "added_synonyms": [],
                "added_context": [],
                "technical_terms": [],
                "expansion_reasoning": "Fallback expansion due to LLM error"
            },
            "search_keywords": keywords,
            "confidence_score": 0.6  # Lower confidence for fallback
        }

    def _simple_expand_query(self, query: str) -> str:
        """Simple query expansion using basic rules."""
        # Basic synonym mapping for common terms
        synonym_map = {
            "what": "what definition meaning explanation",
            "how": "how method process way technique",
            "why": "why reason cause purpose explanation",
            "when": "when time period date timing",
            "where": "where location place position",
            "who": "who person people individual",
            "benefits": "benefits advantages pros positive effects",
            "problems": "problems issues challenges difficulties",
            "process": "process procedure method workflow steps",
            "system": "system framework structure architecture",
            "policy": "policy procedure rule guideline protocol"
        }
        
        words = query.lower().split()
        expanded_words = []
        
        for word in words:
            expanded_words.append(word)
            if word in synonym_map:
                # Add synonyms but don't duplicate the original word
                synonyms = [s for s in synonym_map[word].split() if s != word]
                expanded_words.extend(synonyms[:2])  # Limit to 2 synonyms
        
        return " ".join(expanded_words)

    def _extract_keywords_fallback(self, query: str) -> List[str]:
        """Extract keywords using simple heuristics."""
        # Remove common stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", 
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", 
            "has", "had", "do", "does", "did", "will", "would", "could", "should"
        }
        
        words = query.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Return first 5 keywords to avoid overwhelming search
        return keywords[:5] 