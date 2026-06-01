"""
Summary Generation Agent for creating crisp, concise summaries from detailed responses.
"""
import re
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger("cogniVox")

class SummaryGenerationAgent:
    """
    Agent responsible for generating crisp, concise summaries from detailed responses.
    
    This agent takes detailed AI responses and creates short, meaningful summaries
    that capture the key points in 2-3 sentences maximum.
    """
    
    def __init__(self, max_summary_length: int = 200, max_sentences: int = 3):
        """
        Initialize the Summary Generation Agent.
        
        Args:
            max_summary_length: Maximum character length for summaries
            max_sentences: Maximum number of sentences in a summary
        """
        self.max_summary_length = max_summary_length
        self.max_sentences = max_sentences
        logger.info(f"Summary Generation Agent initialized (max_length: {max_summary_length}, max_sentences: {max_sentences})")
    
    def generate_summary(self, detailed_response: str, original_query: str = "") -> str:
        """
        Generate a crisp, concise summary from a detailed response.
        
        Args:
            detailed_response: The full detailed response from the agent
            original_query: The original user query for context (optional)
            
        Returns:
            A crisp, concise summary (2-3 sentences max)
        """
        try:
            # Clean the response and remove sensitive information
            response_text = detailed_response.strip()
            
            # Sanitize sensitive information before processing
            response_text = self._sanitize_response(response_text)
            
            # If response is already short, return it as is
            if len(response_text) <= 150:
                return response_text
            
            # Extract the first meaningful sentence or two
            sentences = re.split(r'[.!?]+', response_text)
            
            # Filter out empty sentences and clean them
            meaningful_sentences = []
            for sentence in sentences:
                cleaned = sentence.strip()
                if cleaned and len(cleaned) > 10:  # Ignore very short fragments
                    meaningful_sentences.append(cleaned)
            
            if not meaningful_sentences:
                # Fallback to truncation if no meaningful sentences found
                return response_text[:self.max_summary_length].strip() + "..."
            
            # Create summary from first 1-3 sentences
            summary_parts = []
            total_length = 0
            
            for sentence in meaningful_sentences[:self.max_sentences]:
                if total_length + len(sentence) <= self.max_summary_length:
                    summary_parts.append(sentence)
                    total_length += len(sentence)
                else:
                    break
            
            if summary_parts:
                summary = ". ".join(summary_parts)
                if not summary.endswith(('.', '!', '?')):
                    summary += "."
                return summary
            else:
                # Final fallback
                return response_text[:self.max_summary_length].strip() + "..."
                
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            # Fallback to simple truncation
            return self._fallback_summary(detailed_response)
    
    def _sanitize_response(self, text: str) -> str:
        """
        Intelligently clean response to ensure no technical or system information leaks.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Clean, business-appropriate text without any technical details
        """
        if not text:
            return text
        
        # Quick check: if text looks clean already, return it
        if not self._contains_technical_info(text):
            return text
        
        # Apply basic cleanup first (for performance)
        text = self._basic_cleanup(text)
        
        # For more complex cases, ensure it reads like natural business communication
        # Focus on making it sound like information an executive would receive
        return self._ensure_business_appropriate(text)
    
    def _contains_technical_info(self, text: str) -> bool:
        """Check if text contains technical information that needs cleaning."""
        technical_indicators = [
            'gcp://', 'storage.googleapis.com', 'http://', 'https://',
            '_[a-f0-9]{6,}', r'\.pdf', r'\.docx?', r'\.txt',
            '/documents/', '/storage/', '_id', 'uuid', 'hash',
            'Source: gcp', 'Source: http', 'bucket', 'blob'
        ]
        
        text_lower = text.lower()
        for indicator in technical_indicators:
            if re.search(indicator, text_lower):
                return True
        return False
    
    def _basic_cleanup(self, text: str) -> str:
        """Apply basic regex cleanup for common patterns."""
        # Remove obvious technical patterns
        patterns_to_remove = [
            r'gcp://[^\s"\')\]]+',
            r'https://storage\.googleapis\.com/[^\s"\')\]]+',
            r'https://[^\s"\')\]]*\?[^\s"\')\]]*',  # URLs with parameters
            r'_[a-f0-9]{8,}',  # Document IDs
            r'\(Source:\s*[^)]*(?:gcp://|storage\.googleapis\.com|http)[^)]*\)',
            r'Source:\s*[^\s"\']*(?:gcp://|storage\.googleapis\.com|http)[^\s"\']*',
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Clean up artifacts
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\(\s*\)', '', text)
        text = re.sub(r',\s*,', ',', text)
        text = re.sub(r'\.\s*\.', '.', text)
        text = re.sub(r'\s*,\s*\.', '.', text)
        text = re.sub(r'\s+([.,!?])', r'\1', text)
        
        return text.strip()
    
    def _ensure_business_appropriate(self, text: str) -> str:
        """Ensure text sounds like natural business communication."""
        # Replace technical document references with clean names
        # Pattern: document names that look technical
        text = re.sub(r'(["\']?)([^"\']*?)_20\d{2}([^"\']*?)\.pdf(["\']?)', r'\1\2\4', text, flags=re.IGNORECASE)
        text = re.sub(r'(["\']?)([^"\']*?)_[a-f0-9]{6,}([^"\']*?)(["\']?)', r'\1\2\3\4', text)
        
        # Clean up document title patterns
        text = re.sub(r'(\w+)\s*_\s*(\d{4})', r'\1 \2', text)  # "Policy_2022" -> "Policy 2022"
        text = re.sub(r'([A-Z][a-z]+)([A-Z][a-z]+)', r'\1 \2', text)  # "CyberSecurity" -> "Cyber Security"
        
        return text.strip()
    
    def _fallback_summary(self, text: str) -> str:
        """
        Fallback method for summary generation when main method fails.
        
        Args:
            text: The text to summarize
            
        Returns:
            Simple truncated summary
        """
        # Also sanitize the fallback summary
        sanitized_text = self._sanitize_response(text)
        
        if len(sanitized_text) <= self.max_summary_length:
            return sanitized_text
        else:
            return sanitized_text[:self.max_summary_length].strip() + "..."
    
    def validate_summary(self, summary: str) -> Dict[str, Any]:
        """
        Validate a generated summary against quality criteria.
        
        Args:
            summary: The summary to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "is_valid": True,
            "issues": [],
            "length": len(summary),
            "sentence_count": len(re.split(r'[.!?]+', summary.strip()))
        }
        
        # Check length
        if len(summary) > self.max_summary_length:
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"Summary too long ({len(summary)} > {self.max_summary_length})")
        
        # Check sentence count
        sentence_count = len([s for s in re.split(r'[.!?]+', summary.strip()) if s.strip()])
        if sentence_count > self.max_sentences:
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"Too many sentences ({sentence_count} > {self.max_sentences})")
        
        # Check if summary is too short
        if len(summary.strip()) < 10:
            validation_result["is_valid"] = False
            validation_result["issues"].append("Summary too short")
        
        return validation_result
    
    def update_parameters(self, max_summary_length: int = None, max_sentences: int = None):
        """
        Update the agent's parameters.
        
        Args:
            max_summary_length: New maximum character length for summaries
            max_sentences: New maximum number of sentences in a summary
        """
        if max_summary_length is not None:
            self.max_summary_length = max_summary_length
            logger.info(f"Updated max_summary_length to {max_summary_length}")
        
        if max_sentences is not None:
            self.max_sentences = max_sentences
            logger.info(f"Updated max_sentences to {max_sentences}") 