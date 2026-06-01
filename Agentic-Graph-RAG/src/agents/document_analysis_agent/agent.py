"""
Document Analysis Agent for optimizing document processing parameters.
"""
import json
import logging
from typing import Dict, Any, Optional

from ..base_agent import BaseAgent
from .prompt import DOCUMENT_ANALYSIS_SYSTEM_PROMPT, create_document_analysis_prompt

logger = logging.getLogger("cogniVox.graphrag")

class DocumentAnalysisAgent(BaseAgent):
    """
    Agent specialized in analyzing document characteristics and recommending
    optimal chunking parameters for text processing and retrieval.
    
    This agent optimizes document processing by:
    - Analyzing content type, density, and structure
    - Recommending appropriate chunk sizes and overlap
    - Providing processing hints for different document types
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.2,  # Low temperature for consistent analysis
        **kwargs
    ):
        """Initialize the Document Analysis Agent."""
        super().__init__(
            agent_name="document_analysis_agent",
            model_name=model_name,
            temperature=temperature,
            system_prompt=DOCUMENT_ANALYSIS_SYSTEM_PROMPT,
            **kwargs
        )

    def analyze_document(self, pdf_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze document content and determine optimal chunking parameters.
        
        Args:
            pdf_data: Dictionary containing document metadata and sample content
            
        Returns:
            Dictionary with analysis results and chunking recommendations
        """
        try:
            # Create the analysis prompt
            analysis_prompt = create_document_analysis_prompt(pdf_data)
            
            # Call the LLM
            response = self.call_llm(analysis_prompt, use_cache=True)
            
            # Parse and validate the response
            analysis_result = self._parse_analysis_response(response, pdf_data)
            
            logger.info(f"Document analysis completed for: {pdf_data.get('title', 'Unknown')}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            return self._fallback_analysis(pdf_data)

    def _parse_analysis_response(self, content: str, pdf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate the analysis response."""
        try:
            # Clean the JSON string
            cleaned_content = self._clean_json_string(content)
            
            # Parse JSON
            data = json.loads(cleaned_content)
            
            # Validate and complete the response
            return self._validate_analysis_response(data, pdf_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {content}")
            return self._fallback_analysis(pdf_data)
        except Exception as e:
            logger.error(f"Error processing analysis response: {e}")
            return self._fallback_analysis(pdf_data)

    def _clean_json_string(self, json_str: str) -> str:
        """Clean and extract JSON from the response."""
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
        
        return json_str.strip()

    def _validate_analysis_response(self, data: Dict[str, Any], pdf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and complete the analysis response."""
        # Ensure required structure exists
        if "content_analysis" not in data:
            data["content_analysis"] = {}
        if "chunking_recommendations" not in data:
            data["chunking_recommendations"] = {}
        if "processing_hints" not in data:
            data["processing_hints"] = {}

        # Validate content analysis
        content_analysis = data["content_analysis"]
        content_analysis.setdefault("content_type", "mixed")
        content_analysis.setdefault("density_level", "moderate")
        content_analysis.setdefault("structure_type", "semi_structured")
        content_analysis.setdefault("complexity_score", 5)
        content_analysis.setdefault("key_characteristics", ["standard document"])

        # Validate and fix chunking recommendations
        chunking = data["chunking_recommendations"]
        
        # Set defaults based on content type if missing
        content_type = content_analysis.get("content_type", "mixed")
        default_chunk_size, default_overlap = self._get_default_chunking(content_type)
        
        chunk_size = chunking.get("optimal_chunk_size", default_chunk_size)
        chunk_overlap = chunking.get("optimal_chunk_overlap", default_overlap)
        
        # Ensure chunk_size > chunk_overlap
        if chunk_overlap >= chunk_size:
            chunk_overlap = max(100, int(chunk_size * 0.15))  # 15% of chunk size, minimum 100
        
        # Ensure values are within reasonable bounds
        chunk_size = max(600, min(1600, chunk_size))
        chunk_overlap = max(100, min(300, chunk_overlap))
        
        chunking["optimal_chunk_size"] = chunk_size
        chunking["optimal_chunk_overlap"] = chunk_overlap
        chunking.setdefault("confidence_score", 0.8)
        chunking.setdefault("reasoning", f"Optimized for {content_type} content")

        # Validate processing hints
        processing_hints = data["processing_hints"]
        processing_hints.setdefault("priority_sections", ["main content"])
        processing_hints.setdefault("special_handling", ["preserve structure"])
        processing_hints.setdefault("extraction_focus", "comprehensive content extraction")

        return data

    def _get_default_chunking(self, content_type: str) -> tuple:
        """Get default chunking parameters based on content type."""
        defaults = {
            "technical": (800, 200),
            "legal": (800, 250),
            "academic": (1150, 225),
            "business": (1000, 175),
            "narrative": (1400, 125),
            "mixed": (1100, 175)
        }
        return defaults.get(content_type, (1000, 200))

    def _fallback_analysis(self, pdf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide a fallback analysis when LLM analysis fails."""
        pages = pdf_data.get("pages", [])
        total_pages = len(pages)
        
        # Estimate content characteristics based on available metadata
        title = pdf_data.get("title", "").lower()
        
        # Simple heuristics for content type
        if any(word in title for word in ["technical", "api", "documentation", "manual"]):
            content_type = "technical"
            chunk_size, chunk_overlap = 800, 200
        elif any(word in title for word in ["legal", "contract", "policy", "terms"]):
            content_type = "legal"
            chunk_size, chunk_overlap = 800, 250
        elif any(word in title for word in ["research", "paper", "study", "analysis"]):
            content_type = "academic"
            chunk_size, chunk_overlap = 1150, 225
        elif any(word in title for word in ["business", "report", "plan", "strategy"]):
            content_type = "business"
            chunk_size, chunk_overlap = 1000, 175
        else:
            content_type = "mixed"
            chunk_size, chunk_overlap = 1000, 200

        return {
            "content_analysis": {
                "content_type": content_type,
                "density_level": "moderate",
                "structure_type": "semi_structured",
                "complexity_score": 5,
                "key_characteristics": ["fallback analysis", f"{total_pages} pages"]
            },
            "chunking_recommendations": {
                "optimal_chunk_size": chunk_size,
                "optimal_chunk_overlap": chunk_overlap,
                "confidence_score": 0.6,  # Lower confidence for fallback
                "reasoning": f"Fallback analysis based on title heuristics for {content_type} content"
            },
            "processing_hints": {
                "priority_sections": ["main content", "headers"],
                "special_handling": ["preserve document structure"],
                "extraction_focus": "comprehensive text extraction with context preservation"
            }
        }

    def get_chunking_params(self, pdf_data: Dict[str, Any]) -> tuple:
        """
        Get optimal chunking parameters for a document.
        
        Args:
            pdf_data: Document data
            
        Returns:
            Tuple of (chunk_size, chunk_overlap)
        """
        analysis = self.analyze_document(pdf_data)
        recommendations = analysis.get("chunking_recommendations", {})
        
        chunk_size = recommendations.get("optimal_chunk_size", 1000)
        chunk_overlap = recommendations.get("optimal_chunk_overlap", 200)
        
        return chunk_size, chunk_overlap 