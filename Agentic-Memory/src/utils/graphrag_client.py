"""
GraphRAG Client for connecting to the Agentic-Graph-RAG service.

This module provides a client that handles the connection to 
the GraphRAG service with robust error handling and proper timeouts.
"""
import os
import re
import json
import logging
import requests
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger("cogniVox")

class GraphRAGClient:
    """
    Client for interacting with the Agentic-Graph-RAG service.
    This uses longer timeouts for handling graph-based queries which can take time.
    """
    def __init__(self, base_url=None):
        """Initialize the GraphRAG Service client with configuration."""
        # Try different ways to get the GraphRAG service URL
        if base_url:
            self.base_url = base_url
        else:
            # Try to get from environment variable
            graphrag_url = os.getenv("GRAPHRAG_API_URL")
            graphrag_port = os.getenv("GRAPHRAG_PORT")
            
            if graphrag_url:
                self.base_url = graphrag_url
            elif graphrag_port:
                self.base_url = f"http://localhost:{graphrag_port}"
            else:
                # Default fallback - local development
                self.base_url = "http://localhost:8003"
                
        logger.info(f"GraphRAG service URL: {self.base_url}")
        # OPTIMIZATION: Set increased timeout for complete GraphRAG processing
        self.timeout = 120  # seconds (increased to handle full GraphRAG pipeline)

    def fetch_context(self, query: str, user_id: Optional[str] = None, n_results: int = 20) -> Dict[str, Any]:
        """
        Fetch relevant context from the GraphRAG service for a given query.
        
        Args:
            query: The user query
            user_id: Optional user ID for user-specific knowledge
            n_results: Number of results to return (default: 5)
            
        Returns:
            Dictionary containing context information and source documents or empty dict if no context found
        """
        try:
            # Limit overly long queries to prevent timeouts and embedding issues
            max_query_length = 300
            if len(query) > max_query_length:
                logger.warning(f"Query too long ({len(query)} chars), truncating to {max_query_length} chars")
                query = query[:max_query_length] + "..."
            
            # Prepare the request payload
            payload = {
                "query": query,
                "mode": "hybrid",
                "n_results": n_results,  # Use the provided n_results parameter
                "format": "text",
                "user_id": user_id if user_id else None
            }
                
            logger.info(f"Fetching context from GraphRAG for query: {query}, n_results: {n_results}")
            
            # Make the request to GraphRAG API with longer timeout
            response = requests.post(
                f"{self.base_url}/query", 
                json=payload, 
                timeout=self.timeout
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                try:
                    # Try standard JSON parsing first
                    data = response.json()
                    logger.info(f"Successfully parsed response from GraphRAG")
                except json.JSONDecodeError as json_error:
                    logger.warning(f"JSON parsing error from GraphRAG response: {json_error}")
                    # Try to sanitize and parse the response
                    sanitized_response = self._sanitize_json_string(response.text)
                    try:
                        data = json.loads(sanitized_response)
                        logger.info("Successfully parsed sanitized response")
                    except json.JSONDecodeError:
                        # Fall back to regex extraction if that fails too
                        logger.warning("JSON still invalid after sanitization, using regex extraction")
                        data = self._extract_from_malformed_json(response.text)
                        if not data:
                            logger.error("Could not parse GraphRAG response after multiple attempts")
                            return {"context": "", "sources": []}
                
                # Log the data keys and source count
                logger.info(f"GraphRAG response contains keys: {list(data.keys())}")
                sources_count = len(data.get("sources", []))
                logger.info(f"GraphRAG returned {sources_count} sources")
                
                # CRITICAL: Respect the source_found flag from GraphRAG
                # GraphRAG Pure RAG determines relevance - do NOT override it
                source_found_flag = data.get("source_found", False)
                sources_list = data.get("sources", [])
                
                logger.info(f"GraphRAG response: source_found={source_found_flag}, sources_count={len(sources_list)}")
                
                # If source_found is False, return empty - even if sources exist
                # This means GraphRAG determined the sources are NOT relevant
                if not source_found_flag:
                    logger.info("GraphRAG determined sources are NOT relevant (source_found=False) - returning empty")
                    return {"context": "", "sources": [], "source_found": False}
                    
                # Extract the answer and sources
                answer = data.get("answer", "")
                sources = data.get("sources", [])
                
                # Format the source documents
                formatted_sources = []
                if sources:
                    logger.info(f"Processing {len(sources)} source documents from GraphRAG")
                    for i, source in enumerate(sources):
                        # Use the "text" field for content, but fall back to "content" if it exists
                        content = source.get("text", source.get("content", "")).strip()
                        
                        # Map GraphRAG fields to Memory service format
                        document_path = source.get("document_path", "") or source.get("file_path", "")
                        
                        formatted_source = {
                            "document_title": source.get("document_title", "Unknown document"),
                            "content": content,
                            "relevance": source.get("relevance_score", 0.0),
                            "file_path": document_path,  # Use document_path from GraphRAG
                            "download_url": source.get("download_url"),  # Include download_url from GraphRAG
                            "page": source.get("page")  # Include page number from GraphRAG
                        }
                        
                        formatted_sources.append(formatted_source)
                    
                    logger.info(f"Processed {len(formatted_sources)} of {len(sources)} sources")
                
                # Return with the source_found flag from GraphRAG (not hardcoded)
                return {
                    "context": answer,
                    "sources": formatted_sources,
                    "source_found": source_found_flag  # Respect GraphRAG's determination
                }
            else:
                logger.warning(f"GraphRAG API returned status code {response.status_code}")
                return {"context": "", "sources": [], "source_found": False}
                
        except requests.Timeout:
            logger.warning(f"Timeout while connecting to GraphRAG service (timeout={self.timeout}s)")
            return {"context": "", "sources": [], "source_found": False, "error": "timeout"}
        except requests.ConnectionError:
            logger.warning("Connection error while connecting to GraphRAG service")
            return {"context": "", "sources": [], "source_found": False, "error": "connection"}
        except Exception as e:
            logger.warning(f"Error fetching context from GraphRAG: {str(e)}")
            return {"context": "", "sources": [], "source_found": False, "error": str(e)}

    def check_health(self) -> Dict[str, Any]:
        """Check if the GraphRAG service is healthy."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                return {"status": "connected"}
            else:
                return {"status": f"error: status {response.status_code}"}
        except Exception as e:
            return {"status": f"error: {str(e)}"}
            
    def _sanitize_json_string(self, json_str: str) -> str:
        """
        Sanitize a JSON string to fix common issues before parsing.
        
        Args:
            json_str: The JSON string to sanitize
            
        Returns:
            Sanitized JSON string
        """
        # Remove control characters
        json_str = re.sub(r'[\x00-\x1F\x7F]', '', json_str)
        
        # Find the JSON block in case there's surrounding text
        json_pattern = r'({[\s\S]*})'
        json_match = re.search(json_pattern, json_str)
        if json_match:
            json_str = json_match.group(1)
        
        # Fix missing commas between objects in arrays
        json_str = re.sub(r'}\s*{', '},{', json_str)
        
        # Fix trailing commas in arrays/objects
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # Fix unescaped quotes in strings
        in_string = False
        result = []
        i = 0
        while i < len(json_str):
            char = json_str[i]
            if char == '"':
                # Check if this quote is escaped
                if i > 0 and json_str[i-1] == '\\':
                    # Already escaped quote
                    result.append(char)
                else:
                    # Toggle in_string state and add the quote
                    in_string = not in_string
                    result.append(char)
            elif char == '\\' and in_string:
                # Handle escape sequences
                if i + 1 < len(json_str):
                    next_char = json_str[i+1]
                    # Valid escape sequences in JSON
                    if next_char in '"\\bfnrt/':
                        result.append(char)
                    else:
                        # Invalid escape sequence, add backslash to escape it
                        result.append('\\')
                        result.append('\\')
                else:
                    # Backslash at the end
                    result.append('\\')
                    result.append('\\')
            else:
                result.append(char)
            i += 1
        
        return ''.join(result)
    
    def _extract_from_malformed_json(self, text: str) -> Dict[str, Any]:
        """Extract data from malformed JSON using regex patterns.
        
        Args:
            text: The malformed JSON text
            
        Returns:
            Dictionary with extracted data
        """
        result = {}
        
        # Extract answer
        answer_match = re.search(r'"answer"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', text)
        if answer_match:
            result["answer"] = answer_match.group(1).replace('\\"', '"')
        
        # Extract source_found boolean
        source_match = re.search(r'"source_found"\s*:\s*(true|false)', text)
        if source_match:
            result["source_found"] = source_match.group(1) == "true"
        
        # Try to extract sources array
        sources = []
        source_blocks = re.finditer(r'"document_title"\s*:\s*"([^"]*)".*?"text"\s*:\s*"([^"]*)"', text, re.DOTALL)
        for block in source_blocks:
            if block.group(1) and block.group(2):
                sources.append({
                    "document_title": block.group(1),
                    "text": block.group(2)
                })
        
        if sources:
            result["sources"] = sources
            
        return result 