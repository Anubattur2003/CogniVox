"""
Response Enhancement Agent for making basic responses more detailed and comprehensive.
"""
import re
import logging
from typing import Dict, List, Any

# Configure logging
logger = logging.getLogger("cogniVox")

class ResponseEnhancementAgent:
    """
    Agent responsible for enhancing basic responses to make them more detailed and comprehensive.
    
    This agent takes basic AI responses and adds contextual information, source references,
    and additional details to create more comprehensive answers.
    """
    
    def __init__(self):
        """Initialize the Response Enhancement Agent."""
        logger.info("Response Enhancement Agent initialized")
    
    def enhance_response(self, basic_response: str, used_tools: List[str], 
                        source_documents: List[Dict], **kwargs) -> str:
        """
        Enhance the basic response to make it more detailed and comprehensive.
        
        Args:
            basic_response: The basic response from the agent
            used_tools: List of tools used in generating the response
            source_documents: List of source documents if GraphRAG was used
            **kwargs: Additional context or parameters
            
        Returns:
            Enhanced detailed response
        """
        try:
            enhanced_response = basic_response.strip()
            
            # Enhancement 1: Add GraphRAG context if used
            if "graphrag_search" in used_tools and source_documents:
                enhanced_response = self._add_graphrag_context(enhanced_response, source_documents)
            
            # Enhancement 2: Add tool usage context if multiple tools were used
            if len(used_tools) > 1:
                enhanced_response = self._add_tool_context(enhanced_response, used_tools)
            
            # Enhancement 3: Add confidence indicators based on source quality
            if source_documents:
                enhanced_response = self._add_confidence_context(enhanced_response, source_documents)
            
            # Enhancement 4: Sanitize response to remove sensitive information
            enhanced_response = self._sanitize_response(enhanced_response)
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Error enhancing response: {str(e)}")
            return basic_response
    
    def _add_graphrag_context(self, response: str, source_documents: List[Dict]) -> str:
        """
        Add user-friendly context about information sources (without technical details).
        
        Args:
            response: The basic response
            source_documents: List of source documents
            
        Returns:
            Response enhanced with clean source context
        """
        source_count = len(source_documents)
        
        # Check if response already mentions sources
        response_lower = response.lower()
        has_source_mention = any(keyword in response_lower for keyword in [
            "based on", "according to", "source", "document", "information from"
        ])
        
        # Only add minimal context if not already present
        if not has_source_mention and not response_lower.startswith("based on"):
            # Keep it simple - just mention it's from company documents
            if source_count == 1:
                response = f"Based on the available documentation, {response.lower()}"
            else:
                response = f"Based on the available documentation, {response.lower()}"
        
        # Don't add redundant source information at the end
        # The response should be clean and focused on the answer
        
        return response
    
    def _add_tool_context(self, response: str, used_tools: List[str]) -> str:
        """
        Add minimal context about complex processing (without technical details).
        
        Args:
            response: The basic response
            used_tools: List of tools used
            
        Returns:
            Response enhanced with clean processing context
        """
        # Only add minimal context for very complex multi-tool scenarios
        if len(used_tools) > 3:
            # Don't expose internal tool names - keep it user-friendly
            response += f"\n\n*This response involved comprehensive analysis across multiple data sources.*"
        
        return response
    
    def _add_confidence_context(self, response: str, source_documents: List[Dict]) -> str:
        """
        Add user-friendly confidence indicators (without technical details).
        
        Args:
            response: The basic response
            source_documents: List of source documents
            
        Returns:
            Response enhanced with user-friendly confidence context
        """
        if not source_documents:
            return response
        
        # Calculate average relevance (for internal logic only)
        relevance_scores = [doc.get("relevance", 0.0) for doc in source_documents]
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
        
        # Add user-friendly confidence indicator (no technical details)
        if avg_relevance >= 0.8:
            # High confidence - don't add anything (implicit high confidence)
            pass
        elif avg_relevance >= 0.5:
            # Moderate confidence - minimal note
            pass  # Don't add technical notes for moderate confidence
        elif avg_relevance >= 0.3:
            # Lower confidence - gentle suggestion
            response += f"\n\n*Please verify this information if it's for important decisions.*"
        else:
            # Very low confidence - stronger suggestion
            response += f"\n\n*This information should be verified independently.*"
        
        return response
    
    def _sanitize_response(self, text: str) -> str:
        """
        Intelligently clean response to ensure it's appropriate for business users.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Clean, business-appropriate text without any technical details
        """
        if not text:
            return text
        
        # Apply comprehensive cleaning to ensure professional, user-facing communication
        return self._make_business_appropriate(text)
    
    def _make_business_appropriate(self, text: str) -> str:
        """
        Transform text to be appropriate for business communication.
        
        Removes all technical infrastructure details and focuses on content.
        """
        # Step 1: Remove obvious technical patterns
        technical_patterns = [
            r'gcp://[^\s"\')\]]+',
            r'https://storage\.googleapis\.com/[^\s"\')\]]+', 
            r'https://[^\s"\')\]]*\?[A-Za-z0-9&=_%\-]+',  # URLs with query params
            r'_[a-f0-9]{6,}',  # Document/file IDs
            r'/[^\s"\')*]+\.(?:pdf|docx?|txt)',  # File paths
            r'\(Source:\s*[^)]*(?:gcp://|storage\.|http|\.pdf)[^)]*\)',  # Source citations with tech info
            r'Source:\s*[^\s"\']*(?:gcp://|storage\.|http)[^\s"\']*',  # Standalone source refs
            r'blob_name|bucket|storage|download_url|file_path',  # Technical field names
        ]
        
        for pattern in technical_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Step 2: Clean up document titles to be business-friendly
        # "Cyber_Security_Policy_2022_1a2b3c4d.pdf" -> "Cyber Security Policy"
        text = re.sub(r'([A-Za-z]+)_([A-Za-z]+)', r'\1 \2', text)  # underscores to spaces
        text = re.sub(r'_20\d{2}', '', text)  # remove years
        text = re.sub(r'\.(?:pdf|docx?|txt)', '', text, flags=re.IGNORECASE)  # remove extensions
        
        # Step 3: Clean up formatting artifacts
        text = re.sub(r'\s+', ' ', text)  # multiple spaces to single
        text = re.sub(r'\(\s*\)', '', text)  # empty parentheses
        text = re.sub(r'\[\s*\]', '', text)  # empty brackets
        text = re.sub(r',\s*,', ',', text)  # double commas
        text = re.sub(r'\.\s*\.', '.', text)  # double periods
        text = re.sub(r'\s*,\s*\.', '.', text)  # comma before period
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)  # space before punctuation
        text = re.sub(r'([.,!?;:])\s*([.,!?;:])', r'\1', text)  # double punctuation
        
        # Step 4: Ensure natural language flow
        # Remove awkward phrases that result from sanitization
        text = re.sub(r'\bas documented in the\s*""\s*', 'as documented ', text)
        text = re.sub(r'\bas documented in\s*""\s*', 'according to the documentation ', text)
        text = re.sub(r'\(as shown in\s*\)', '', text)
        text = re.sub(r'according to\s*,', 'according to company policy,', text)
        
        return text.strip()
    
    def enhance_with_metadata(self, response: str, metadata: Dict[str, Any]) -> str:
        """
        Enhance response with additional metadata context.
        
        Args:
            response: The basic response
            metadata: Dictionary containing metadata about the response generation
            
        Returns:
            Response enhanced with metadata context
        """
        try:
            enhanced = response
            
            # Add processing time context if available
            if "processing_time" in metadata and metadata["processing_time"] > 10:
                enhanced += f"\n\n*This comprehensive response required {metadata['processing_time']:.1f} seconds of processing.*"
            
            # Add model context if specified
            if "model_name" in metadata and metadata["model_name"]:
                model_name = metadata["model_name"]
                if "gpt" in model_name.lower() or "claude" in model_name.lower() or "llama" in model_name.lower():
                    # Only mention model for well-known models
                    enhanced += f"\n\n*Generated using {model_name}.*"
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Error enhancing with metadata: {str(e)}")
            return response
    
    def get_enhancement_stats(self, original_response: str, enhanced_response: str) -> Dict[str, Any]:
        """
        Get statistics about the enhancement process.
        
        Args:
            original_response: The original response
            enhanced_response: The enhanced response
            
        Returns:
            Dictionary with enhancement statistics
        """
        return {
            "original_length": len(original_response),
            "enhanced_length": len(enhanced_response),
            "enhancement_ratio": len(enhanced_response) / len(original_response) if original_response else 1.0,
            "added_characters": len(enhanced_response) - len(original_response),
            "has_source_context": "source" in enhanced_response.lower(),
            "has_confidence_indicators": "*note:" in enhanced_response.lower()
        } 