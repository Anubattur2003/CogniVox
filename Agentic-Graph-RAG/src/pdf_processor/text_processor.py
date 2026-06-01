import re
import math
import json
import requests
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

from src.config import CHUNK_SIZE, CHUNK_OVERLAP, OLLAMA_HOST, TEXT_GENERATION_MODEL


# Default content types and their associated keywords
DEFAULT_CONTENT_TYPES = {
    "technical": [
        "technical", "manual", "guide", "documentation", "report", 
        "scientific", "research", "analysis", "study", "algorithm",
        "methodology", "framework", "technology", "engineering", "data"
    ],
    "legal": [
        "legal", "law", "regulation", "statute", "compliance", 
        "policy", "constitution", "agreement", "contract", "act",
        "legislation", "judicial", "court", "ordinance", "jurisdiction"
    ],
    "narrative": [
        "story", "novel", "fiction", "tale", "narrative", 
        "book", "chapter", "anthology", "poem", "literature",
        "biography", "drama", "prose", "fantasy", "adventure"
    ],
    "academic": [
        "journal", "paper", "thesis", "dissertation", "academic",
        "study", "theory", "hypothesis", "experiment", "professor",
        "university", "college", "educational", "scholarly", "publication"
    ],
    "business": [
        "business", "company", "corporate", "enterprise", "market", 
        "financial", "management", "strategy", "commercial", "industry",
        "revenue", "profit", "executive", "startup", "organization"
    ]
}

# Default content type configurations for chunking
DEFAULT_CONTENT_CONFIG = {
    "technical": {"size_mod": -0.25, "overlap_mod": 0.3},  # Smaller chunks, higher overlap
    "legal": {"size_mod": -0.3, "overlap_mod": 0.4},       # Smallest chunks, highest overlap
    "narrative": {"size_mod": 0.15, "overlap_mod": -0.1},  # Larger chunks, lower overlap
    "academic": {"size_mod": -0.2, "overlap_mod": 0.25},   # Smaller chunks, higher overlap
    "business": {"size_mod": -0.1, "overlap_mod": 0.15}    # Slightly smaller, slightly more overlap
}


class TextProcessor:
    """
    Processes text extracted from PDF documents.
    """
    
    def __init__(self, 
                 chunk_size: int = CHUNK_SIZE, 
                 chunk_overlap: int = CHUNK_OVERLAP,
                 content_types: Optional[Dict[str, List[str]]] = None,
                 content_config: Optional[Dict[str, Dict[str, float]]] = None,
                 use_llm_for_chunking: bool = True,
                 ollama_host: str = OLLAMA_HOST, 
                 ollama_model: str = TEXT_GENERATION_MODEL):
        """
        Initialize the text processor.
        
        Args:
            chunk_size: Size of chunks to create from the text.
            chunk_overlap: Size of overlap between consecutive chunks.
            content_types: Custom content types and their keywords (extends/overrides defaults)
            content_config: Custom content type configurations (extends/overrides defaults)
            use_llm_for_chunking: Whether to use LLM for intelligent chunk sizing
            ollama_host: Host for Ollama API
            ollama_model: Model to use for LLM-based chunking decisions
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_llm_for_chunking = use_llm_for_chunking
        self.ollama_host = ollama_host.rstrip("/")
        self.ollama_model = ollama_model
        
        # Use defaults and extend/override with custom values if provided
        self.content_types = DEFAULT_CONTENT_TYPES.copy()
        if content_types:
            self.content_types.update(content_types)
            
        self.content_config = DEFAULT_CONTENT_CONFIG.copy()
        if content_config:
            self.content_config.update(content_config)
        
        # Create text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
    
    def estimate_content_density(self, pdf_data: Dict[str, Any]) -> float:
        """
        Estimate the content density by analyzing text from the first few pages.
        
        Args:
            pdf_data: Dictionary containing PDF metadata and page text.
            
        Returns:
            Density score between 0.0 and 1.0 (higher means denser content).
        """
        if not pdf_data.get("pages"):
            return 0.5  # Default medium density
            
        # Sample text from pages with weighted importance
        # First pages are most important for document classification
        # (often contain TOC, introductions, abstracts, etc.)
        sample_pages = pdf_data.get("pages")[:8]  # Examine up to 8 pages
        sample_text = ""
        
        # Extract text from sample pages with decreasing importance weights
        page_weights = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
        
        weighted_metrics = {
            "sentence_length": 0.0,
            "word_punct_ratio": 0.0,
            "avg_word_length": 0.0,
            "special_chars_ratio": 0.0,
            "numeric_density": 0.0
        }
        
        total_weight = 0.0
        
        for i, page_data in enumerate(sample_pages):
            # Skip if we've run out of weights
            if i >= len(page_weights):
                break
                
            # Extract text based on the page data format
            page_text = ""
            if isinstance(page_data, dict):
                page_text = page_data.get("text", "")
            elif isinstance(page_data, tuple) and len(page_data) == 2:
                _, data = page_data
                if isinstance(data, dict):
                    page_text = data.get("text", "")
                elif isinstance(data, tuple) and len(data) >= 2:
                    page_text = data[1] if isinstance(data[1], str) else ""
                elif isinstance(data, str):
                    page_text = data
            
            # Skip empty pages    
            if not page_text.strip():
                continue
                
            # Calculate metrics for this page
            weight = page_weights[i]
            total_weight += weight
            
            # Only process substantial text
            if len(page_text) > 100:
                # Append to sample text for overall analysis
                sample_text += page_text + " "
                
                # Calculate weighted page metrics
                weighted_metrics["sentence_length"] += weight * self._calculate_avg_sentence_length(page_text)
                weighted_metrics["word_punct_ratio"] += weight * self._calculate_word_to_punctuation_ratio(page_text)
                weighted_metrics["avg_word_length"] += weight * self._calculate_avg_word_length(page_text)
                weighted_metrics["special_chars_ratio"] += weight * self._calculate_special_chars_ratio(page_text)
                weighted_metrics["numeric_density"] += weight * self._calculate_numeric_density(page_text)
        
        if total_weight == 0 or not sample_text:
            return 0.5  # Default medium density
            
        # Normalize metrics by total weight
        for key in weighted_metrics:
            weighted_metrics[key] /= total_weight
            
        # Calculate final metrics with normalized values
        # Normalize metrics to 0-1 range with reasonable caps
        normalized_metrics = {
            "sentence_length": min(1.0, weighted_metrics["sentence_length"] / 25.0),  # Cap at 25 words/sentence
            "word_punct_ratio": min(1.0, weighted_metrics["word_punct_ratio"] / 15.0),  # Cap at 15:1 ratio
            "avg_word_length": min(1.0, (weighted_metrics["avg_word_length"] - 3) / 5),  # Scale 3-8 letter range
            "special_chars_ratio": min(1.0, weighted_metrics["special_chars_ratio"] * 10),  # Amplify importance
            "numeric_density": min(1.0, weighted_metrics["numeric_density"] * 5)  # Amplify importance
        }
        
        # Combine metrics with different weights based on importance for density
        density_score = (
            normalized_metrics["sentence_length"] * 0.35 +
            normalized_metrics["word_punct_ratio"] * 0.25 +
            normalized_metrics["avg_word_length"] * 0.2 +
            normalized_metrics["special_chars_ratio"] * 0.1 +
            normalized_metrics["numeric_density"] * 0.1
        )
        
        # Ensure score is within 0-1 range
        density_score = max(0.0, min(1.0, density_score))
        
        return density_score
        
    def _calculate_avg_sentence_length(self, text: str) -> float:
        """Calculate average sentence length in words."""
        # Simple sentence splitting on .!?
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
            
        word_counts = [len(re.findall(r'\b\w+\b', s)) for s in sentences]
        return sum(word_counts) / len(sentences) if word_counts else 0.0
        
    def _calculate_word_to_punctuation_ratio(self, text: str) -> float:
        """Calculate ratio of words to punctuation marks."""
        words = len(re.findall(r'\b\w+\b', text))
        punctuation = len(re.findall(r'[.,;:!?]', text))
        
        if punctuation == 0:
            return 20.0  # High ratio (few punctuation marks)
            
        return words / punctuation
        
    def _calculate_avg_word_length(self, text: str) -> float:
        """Calculate the average word length in characters."""
        words = re.findall(r'\b\w+\b', text)
        if not words:
            return 0.0
            
        total_length = sum(len(word) for word in words)
        return total_length / len(words)
        
    def _calculate_special_chars_ratio(self, text: str) -> float:
        """Calculate the ratio of special characters to total characters."""
        if not text:
            return 0.0
            
        # Count special characters (excluding letters, digits, spaces)
        special_chars = len(re.findall(r'[^\w\s]', text))
        total_chars = len(text.strip())
        
        if total_chars == 0:
            return 0.0
            
        return special_chars / total_chars
        
    def _calculate_numeric_density(self, text: str) -> float:
        """Calculate the density of numeric content in the text."""
        if not text:
            return 0.0
            
        # Count digits and numeric symbols
        numeric_chars = len(re.findall(r'[0-9\+\-\*\/\=\%]', text))
        total_chars = len(text.strip())
        
        if total_chars == 0:
            return 0.0
            
        return numeric_chars / total_chars

    def analyze_document_with_llm(self, pdf_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use Ollama to analyze document content and determine optimal chunking parameters.
        
        Args:
            pdf_data: Dictionary containing PDF metadata and page text.
            
        Returns:
            Dictionary with analysis results including recommended chunk settings.
        """
        # Get metadata and sample text
        metadata = pdf_data.get("metadata", {})
        title = metadata.get("title", "Untitled Document")
        page_count = metadata.get("page_count", 0)
        
        # Sample text from first few pages for analysis
        sample_text = self._extract_sample_text(pdf_data, max_pages=3, max_chars=2000)
        
        # Create a prompt for the LLM to analyze the document
        prompt = f"""Analyze this document and recommend optimal text chunking parameters.

DOCUMENT INFO:
Title: {title}
Pages: {page_count}

SAMPLE CONTENT:
{sample_text}

Document characteristics vary widely and require very different chunk sizes. Consider:
- Small documents (1-20 pages): Typically need larger chunks (1400-2000 chars)
- Medium documents (20-100 pages): Need moderate chunks (1000-1400 chars) 
- Large documents (over 100 pages): Need smaller chunks (600-1000 chars)
- Technical content with formulas/tables/complex terms needs smaller chunks
- Narrative content with stories/descriptions can use larger chunks
- Legal content needs precise chunks with good overlap

Based on YOUR ANALYSIS of this specific document, recommend:
1. What's the document type (technical, legal, narrative, academic, business, other)?
2. How complex/dense is the content (very dense, dense, medium, sparse, very sparse)?
3. What's the optimal text chunk size (between 600-2000 characters) for knowledge retrieval?
4. What's the optimal chunk overlap (should be approximately 20% of chunk size)?

DO NOT DEFAULT TO 1000/200! Analyze the document's ACTUAL characteristics and provide truly custom values.

Respond in JSON format with these keys:
- document_type: string
- content_density: string
- optimal_chunk_size: integer 
- optimal_chunk_overlap: integer
- explanation: short explanation

ONLY RETURN THE JSON OBJECT.
"""
        try:
            # Make API call to Ollama
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                response_text = response.json().get("response", "")
                
                # Extract JSON from the response
                try:
                    # Find JSON in the response
                    json_match = re.search(r'({[^{}]*(?:{[^{}]*}[^{}]*)*})', response_text)
                    if json_match:
                        json_str = json_match.group(1)
                        analysis = json.loads(json_str)
                        
                        # Validate the expected keys
                        required_keys = ["document_type", "content_density", "optimal_chunk_size", "optimal_chunk_overlap"]
                        if all(k in analysis for k in required_keys):
                            # Ensure values are in acceptable ranges
                            chunk_size = max(600, min(int(analysis["optimal_chunk_size"]), 2000))
                            
                            # Ensure overlap is approximately 20% of chunk size
                            target_overlap = int(chunk_size * 0.2)
                            overlap = max(100, min(int(analysis["optimal_chunk_overlap"]), 400))
                            
                            # If the overlap is far from 20%, adjust it
                            if abs(overlap - target_overlap) > (target_overlap * 0.25):  # Allow 25% deviation
                                overlap = target_overlap
                                analysis["optimal_chunk_overlap"] = overlap
                                print(f"Adjusted overlap to {overlap} (20% of chunk size {chunk_size})")
                            
                            analysis["optimal_chunk_size"] = chunk_size
                            return analysis
                        
                except Exception as e:
                    print(f"Error parsing LLM analysis: {e}")
            
            # If we get here, either the API call failed or parsing failed
            print("LLM analysis failed or returned invalid data, falling back to heuristic approach")
            return {}
                
        except Exception as e:
            print(f"Exception during LLM document analysis: {e}")
            return {}
    
    def _extract_sample_text(self, pdf_data: Dict[str, Any], max_pages: int = 3, max_chars: int = 2000) -> str:
        """
        Extract a representative sample of text from the document.
        
        Args:
            pdf_data: Dictionary containing PDF metadata and page text.
            max_pages: Maximum number of pages to sample.
            max_chars: Maximum characters to include in the sample.
            
        Returns:
            Sample text string.
        """
        if not pdf_data.get("pages"):
            return ""
        
        pages = pdf_data.get("pages", [])[:max_pages]
        sample_text = ""
        
        for page_data in pages:
            page_text = ""
            if isinstance(page_data, dict):
                page_text = page_data.get("text", "")
            elif isinstance(page_data, tuple) and len(page_data) == 2:
                _, data = page_data
                if isinstance(data, dict):
                    page_text = data.get("text", "")
                elif isinstance(data, tuple) and len(data) >= 2:
                    page_text = data[1] if isinstance(data[1], str) else ""
                elif isinstance(data, str):
                    page_text = data
            
            if page_text:
                # Add a page delimiter if not the first page
                if sample_text:
                    sample_text += "\n--- Next Page ---\n"
                    
                # Add the page text, shortened if needed
                sample_text += page_text[:2000]  # Take first 2000 chars from each page
                
                # Check if we've exceeded the maximum characters
                if len(sample_text) >= max_chars:
                    sample_text = sample_text[:max_chars]
                    break
                    
        return sample_text
        
    def calculate_dynamic_chunk_settings(self, pdf_metadata: Dict[str, Any], pdf_data: Optional[Dict[str, Any]] = None) -> Tuple[int, int]:
        """
        Calculate dynamic chunk size and overlap based on PDF characteristics.
        Uses Ollama LLM if enabled, otherwise falls back to heuristic approach.
        
        Args:
            pdf_metadata: Metadata about the PDF document.
            pdf_data: Complete PDF data including pages (optional).
            
        Returns:
            Tuple containing (chunk_size, chunk_overlap).
        """
        # Default values (from config)
        default_chunk_size = self.chunk_size
        default_chunk_overlap = self.chunk_overlap
        
        # If no custom settings requested (chunk_size already specified), return defaults
        if self.chunk_size != CHUNK_SIZE:
            return default_chunk_size, default_chunk_overlap
        
        # Try optimized LLM-based analysis if enabled and data is available
        if self.use_llm_for_chunking and pdf_data:
            try:
                # Import and use the optimized document analysis agent
                from src.api.dependencies import document_analysis_agent
                
                llm_analysis = document_analysis_agent.analyze_document(pdf_data)
                
                if llm_analysis and "chunking_recommendations" in llm_analysis:
                    chunking = llm_analysis["chunking_recommendations"]
                    content_analysis = llm_analysis.get("content_analysis", {})
                    
                    chunk_size = chunking.get("optimal_chunk_size", 1000)
                    chunk_overlap = chunking.get("optimal_chunk_overlap", 200)
                    
                    doc_type = content_analysis.get("content_type", "unknown")
                    density = content_analysis.get("density_level", "unknown") 
                    explanation = chunking.get("reasoning", "Optimized analysis completed")
                    
                    print(f"Using LLM-determined settings for {doc_type}, {density} content - Size: {chunk_size}, Overlap: {chunk_overlap}")
                    if explanation:
                        print(f"Explanation: {explanation}")
                        
                    return chunk_size, chunk_overlap
            except Exception as e:
                print(f"Error in LLM-based chunk setting determination: {e}")
                print("Falling back to heuristic approach")
            
        # Extract relevant metadata
        page_count = pdf_metadata.get("page_count", 0)
        
        if page_count <= 0:
            return default_chunk_size, default_chunk_overlap
        
        # Extract text properties for content analysis
        title = pdf_metadata.get("title", "").lower()
        subject = pdf_metadata.get("subject", "").lower()
        metadata_text = f"{title} {subject}"
            
        # Calculate scores for each content type
        content_scores = {}
        for content_type, keywords in self.content_types.items():
            content_scores[f"{content_type}_score"] = self._calculate_content_property_score(metadata_text, keywords)
            
        # ========== ENHANCED PAGE COUNT SCALING ==========
        # More dramatic scaling based on page count to ensure real variation
        # Small docs (1-20 pages): 1400-2000 chars
        # Medium docs (21-100 pages): 1000-1400 chars
        # Large docs (101+ pages): 600-1000 chars
        
        if page_count <= 5:
            # Very small documents: very large chunks
            base_chunk_size = 1800
        elif page_count <= 20:
            # Small documents: large chunks
            base_chunk_size = 1600
        elif page_count <= 50:
            # Medium-small documents: medium-large chunks
            base_chunk_size = 1400
        elif page_count <= 100:
            # Medium documents: medium chunks
            base_chunk_size = 1200
        elif page_count <= 200:
            # Medium-large documents: medium-small chunks
            base_chunk_size = 1000
        elif page_count <= 400:
            # Large documents: small chunks
            base_chunk_size = 800
        else:
            # Very large documents: very small chunks
            base_chunk_size = 600
        
        # Calculate density factor (if available)
        density_factor = 0.5  # Default midpoint
        density_description = "unknown"
        
        if pdf_data:
            density_score = self.estimate_content_density(pdf_data)
            density_factor = density_score
            
            # Map density score to description for logging
            if density_score > 0.8:
                density_description = "very dense"
            elif density_score > 0.6:
                density_description = "dense"
            elif density_score > 0.4:
                density_description = "medium density"
            elif density_score > 0.2:
                density_description = "sparse"
            else:
                density_description = "very sparse"
        
        # Calculate document properties influence on size
        size_factor = 1.0
        
        # Apply content type factors
        for content_type, config in self.content_config.items():
            score_key = f"{content_type}_score"
            if score_key in content_scores:
                size_factor += content_scores[score_key] * config.get("size_mod", 0)
        
        # Apply density factor - denser content needs smaller chunks
        # Inverse relationship: higher density -> smaller chunks
        size_factor *= (1.5 - density_factor)
        
        # Calculate final chunk size value with all factors applied
        chunk_size = int(base_chunk_size * size_factor)
        
        # Ensure reasonable bounds
        chunk_size = max(600, min(chunk_size, 2000))
        
        # Calculate overlap as 20% of chunk size
        chunk_overlap = int(chunk_size * 0.2)
        
        # Ensure overlap is within reasonable bounds
        chunk_overlap = max(100, min(chunk_overlap, 400))
        
        # Determine dominant content type for logging
        content_type_scores = []
        for content_type in self.content_types.keys():
            score_key = f"{content_type}_score"
            if score_key in content_scores:
                content_type_scores.append((content_type, content_scores[score_key]))
        
        # Add general as fallback
        content_type_scores.append(("general", 0.34))
        
        # Sort by score in descending order
        content_type_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get dominant content type
        dominant_type = content_type_scores[0][0]
        
        # Print info about the decision
        print(f"Using heuristic chunk settings for {page_count} pages ({dominant_type}, {density_description} content) - Size: {chunk_size}, Overlap: {chunk_overlap}")
        
        # Print the top 3 content type scores for debugging
        debug_scores = ", ".join([f"{ctype}={score:.2f}" for ctype, score in content_type_scores[:3]])
        print(f"Content properties: {debug_scores}")
        
        return chunk_size, chunk_overlap
    
    def _calculate_content_property_score(self, text: str, keywords: List[str]) -> float:
        """
        Calculate a score for a content property based on keyword matches.
        
        Args:
            text: Text to analyze
            keywords: List of keywords to check
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not text or not keywords:
            return 0.0
            
        # Count how many keywords appear in the text
        matches = sum(1 for keyword in keywords if keyword in text)
        
        # Calculate score with diminishing returns
        # Formula: 1 - 1/(1+x) which gives a curve that approaches 1 as x increases
        return 1.0 - (1.0 / (1.0 + matches/3))
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize the text.
        
        Args:
            text: The text to clean.
            
        Returns:
            Cleaned text.
        """
        # Remove multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters
        text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
        
        # Normalize whitespace
        text = text.strip()
        
        return text
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces.
        
        Args:
            text: The text to chunk.
            metadata: Metadata to add to each chunk.
            
        Returns:
            List of dictionaries, each containing a chunk of text and metadata.
        """
        # Handle empty or invalid text
        if not text or not isinstance(text, str):
            return []
        
        text = text.strip()
        if len(text) == 0:
            return []
        
        # Clean text before chunking
        cleaned_text = self.clean_text(text)
        if not cleaned_text:
            return []
        
        # Split the text into chunks
        try:
            # If text is very short, just use it as a single chunk
            if len(cleaned_text) < self.chunk_size / 2:
                raw_chunks = [cleaned_text]
            else:
                raw_chunks = self.text_splitter.split_text(cleaned_text)
        except Exception as e:
            print(f"Error splitting text: {e}")
            return []
        
        # Handle the case where no chunks were created
        if not raw_chunks:
            return []
        
        # Add metadata to each chunk
        chunks = []
        for i, chunk in enumerate(raw_chunks):
            # Skip empty chunks
            if not chunk.strip():
                continue
            
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_id": i,
                "chunk_size": len(chunk),
                "chunk_count": len(raw_chunks)
            })
            chunks.append({"text": chunk, "metadata": chunk_metadata})
        
        return chunks
    
    def process_page_text(self, page_number: int, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process text extracted from a single page.
        
        Args:
            page_number: Page number.
            text: Text extracted from the page.
            metadata: Metadata for the page.
            
        Returns:
            List of dictionaries, each containing a chunk of text and metadata.
        """
        # Handle invalid text
        if not text or not isinstance(text, str):
            print(f"Warning: Invalid text on page {page_number}, skipping.")
            return []
        
        # Create page-specific metadata
        page_metadata = metadata.copy()
        page_metadata.update({
            "page_number": page_number
        })
        
        # Chunk the text
        chunks = self.chunk_text(text, page_metadata)
        if not chunks:
            print(f"Warning: No chunks generated from page {page_number}")
        
        return chunks
    
    def process_pdf_text(self, pdf_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process text extracted from all pages of a PDF.
        
        Args:
            pdf_data: Dictionary containing PDF metadata and page text.
            
        Returns:
            List of dictionaries, each containing a chunk of text and metadata.
        """
        chunks = []
        metadata = pdf_data["metadata"]
        
        # Calculate dynamic chunk settings based on PDF metadata and content
        # This will use LLM if enabled, otherwise fall back to heuristic approach
        dynamic_chunk_size, dynamic_chunk_overlap = self.calculate_dynamic_chunk_settings(metadata, pdf_data)
        
        # Only update text_splitter if values are different
        if dynamic_chunk_size != self.chunk_size or dynamic_chunk_overlap != self.chunk_overlap:
            self.chunk_size = dynamic_chunk_size
            self.chunk_overlap = dynamic_chunk_overlap
            
            # Update text splitter with new settings
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        
        if not pdf_data.get("pages"):
            print(f"Warning: No pages found in PDF data for {metadata.get('file_path')}")
            return []
        
        # Process text from all pages
        for page_data in enumerate(pdf_data["pages"]):
            # Extract the page data from different formats
            page_text = ""
            page_number = 0
            
            # Case 1: page_data is a dictionary with text content (new format)
            if isinstance(page_data, dict):
                page_text = page_data.get("text", "")
                page_number = page_data.get("page_number", 0)
                
            # Case 2: page_data is a tuple from enumerate (i, data)
            elif isinstance(page_data, tuple) and len(page_data) == 2:
                i, data = page_data
                
                # Case 2.1: data is a dict with text
                if isinstance(data, dict):
                    page_text = data.get("text", "")
                    page_number = data.get("page_number", i + 1)
                    
                # Case 2.2: data is a tuple of (page_number, text)
                elif isinstance(data, tuple) and len(data) >= 2:
                    page_number = data[0] if isinstance(data[0], int) else i + 1
                    page_text = data[1] if isinstance(data[1], str) else ""
                    
                # Case 2.3: data is a string (text content directly)
                elif isinstance(data, str):
                    page_number = i + 1
                    page_text = data
                    
            # Skip empty or invalid pages
            if not page_text or not isinstance(page_text, str) or not page_text.strip():
                # Only print warning if page had no extraction errors
                if isinstance(page_data, dict) and "error" not in page_data:
                    print(f"Warning: Skipping empty or invalid page {page_number}")
                continue
            
            # Ensure page number is valid
            if not page_number or not isinstance(page_number, int):
                page_number = 1  # Default to page 1 if no valid page number
            
            # Process text for this page
            page_chunks = self.process_page_text(page_number, page_text, metadata)
            chunks.extend(page_chunks)
        
        if not chunks:
            print(f"Warning: No chunks generated from PDF {metadata.get('file_path')}")
        else:
            overlap_percentage = round((self.chunk_overlap / self.chunk_size) * 100)
            print(f"Generated {len(chunks)} text chunks from PDF {metadata.get('file_path')} using chunk size: {self.chunk_size}, overlap: {self.chunk_overlap} ({overlap_percentage}% of chunk size)")
        
        return chunks 