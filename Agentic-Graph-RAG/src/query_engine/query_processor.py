from typing import Dict, List, Optional, Any
import concurrent.futures
import time
import re

from src.graph_db import KnowledgeGraphManager


class QueryProcessor:
    """
    Pure RAG Query Processor - Lightweight retrieval system.
    Returns only retrieved chunks with metadata, no LLM generation.
    """
    
    def __init__(self, knowledge_graph: Optional[KnowledgeGraphManager] = None):
        """
        Initialize the query processor.
        
        Args:
            knowledge_graph: Knowledge graph manager to use. If None, a new one will be created.
        """
        self.knowledge_graph = knowledge_graph if knowledge_graph else KnowledgeGraphManager()
    
    def _parallel_keyword_search(self, keywords: List[str], n_results: int, user_id: Optional[str] = None) -> List[Dict]:
        """
        Execute multiple keyword searches in parallel.
        
        Args:
            keywords: List of keywords to search
            n_results: Number of results per keyword
            user_id: Optional user ID for filtering
            
        Returns:
            Combined and deduplicated results
        """
        def search_keyword(keyword: str) -> List[Dict]:
            """Thread-safe keyword search"""
            try:
                return self.knowledge_graph.keyword_search(keyword, n_results, user_id)
            except Exception as e:
                print(f"Keyword search failed for '{keyword}': {e}")
                return []
        
        all_results = []
        
        # Use ThreadPoolExecutor for parallel keyword searches
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(keywords), 5)) as executor:
            # Submit all keyword searches
            future_to_keyword = {
                executor.submit(search_keyword, keyword): keyword 
                for keyword in keywords[:5]  # Limit to 5 keywords max
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_keyword, timeout=45):
                keyword = future_to_keyword[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                    print(f"Keyword '{keyword}' search completed with {len(results)} results")
                except Exception as e:
                    print(f"Keyword search for '{keyword}' failed: {e}")
        
        # Remove duplicates by result ID
        unique_results = {}
        for result in all_results:
            result_id = result.get("id") or result.get("chunk_id") or result.get("vector_id")
            if result_id and result_id not in unique_results:
                unique_results[result_id] = result
        
        # Sort by score and return top results
        sorted_results = sorted(unique_results.values(), 
                               key=lambda x: x.get("score", 0), 
                               reverse=True)
        
        return sorted_results[:n_results]
    
    def query(self, query_text: str, mode: str = "hybrid", n_results: int = 20, 
              user_id: Optional[str] = None) -> Dict:
        """
        Process a query against the knowledge graph - Pure RAG retrieval.
        
        Args:
            query_text: The query text to process.
            mode: Search mode ("semantic", "keyword", "hybrid", or "auto").
            n_results: Number of results to return.
            user_id: Optional user ID for user-specific queries.
            
        Returns:
            Dictionary with query results (raw chunks only, no LLM generation).
        """
        # Clean the query text
        query_text = query_text.strip()
        if not query_text:
            return {
                "query": "",
                "mode": mode,
                "sources": [],
                "source_found": False,
                "context": "",
                "answer": "",  # Alias for backward compatibility
                "result_count": 0,
                "search_time": 0.0,
                "message": "Empty query provided."
            }
        
        # Normalize the mode value
        mode = self._normalize_mode(mode)
        
        # Auto-detect mode using rule-based logic
        if mode == "auto":
            mode = self._detect_search_mode(query_text)
            print(f"Auto mode: Detected search mode as '{mode}'")
        
        # Perform search based on mode
        print(f"Performing search with mode: {mode}, n_results: {n_results}")
        start_time = time.time()
        
        if mode == "semantic":
            results = self.knowledge_graph.semantic_search(query_text, n_results, user_id)
        elif mode == "keyword":
            # Extract keywords for keyword search
            keywords = self._extract_keywords(query_text)
            print(f"Extracted keywords: {keywords}")
            results = self._parallel_keyword_search(keywords[:3], n_results, user_id)
        else:  # hybrid
            results = self.knowledge_graph.parallel_hybrid_search(query_text, n_results, user_id)
        
        search_time = time.time() - start_time
        print(f"Search completed in {search_time:.2f}s with {len(results)} results")
        
        # Format results for Memory service compatibility
        formatted_sources = []
        context_parts = []
        
        for result in results:
            # Extract metadata based on result type
            metadata = result.get("metadata", {})
            if isinstance(metadata, dict):
                # Semantic search result format
                doc_title = metadata.get("title", "Unknown")
                doc_path = metadata.get("document_path") or metadata.get("file_path", "Unknown")
                page_num = metadata.get("page_number", "Unknown")
            else:
                # Keyword search result format
                doc_title = result.get("document_title", "Unknown")
                doc_path = result.get("file_path") or result.get("document_path", "Unknown")
                page_num = result.get("page_number", "Unknown")
            
            # Get relevance score
            if "relevance_score" in result:
                relevance_score = result.get("relevance_score")
            elif "distance" in result:
                relevance_score = 1.0 - result.get("distance", 0)
            elif "score" in result:
                relevance_score = result.get("score", 0) / 10.0
            else:
                relevance_score = 0.5
            
            # Format source for Memory service
            text_content = result.get("text", "")
            formatted_source = {
                "document_title": doc_title,
                "text": text_content,  # Memory expects 'text' field
                "content": text_content,  # Also include 'content' for compatibility
                "page": page_num,
                "relevance_score": relevance_score,
                "document_path": doc_path,
                "file_path": doc_path,  # Include both for compatibility
                "download_url": result.get("download_url"),
                "match_type": result.get("match_type", mode)
            }
            formatted_sources.append(formatted_source)
            
            # Build context string
            if text_content:
                context_parts.append(
                    f"[{doc_title}, Page {page_num}]\n{text_content}\n"
                )
        
        # Combine all context
        combined_context = "\n".join(context_parts) if context_parts else ""
        
        # Determine if sources were found
        source_found = len(formatted_sources) > 0
        
        # Return pure RAG results - compatible with Memory service
        response = {
            "query": query_text,
            "mode": mode,
            "sources": formatted_sources,  # Renamed from 'results'
            "source_found": source_found,  # Flag for Memory service
            "context": combined_context,  # Formatted context text
            "answer": combined_context,  # Alias for backward compatibility with Memory
            "result_count": len(formatted_sources),
            "search_time": round(search_time, 3)
            }
            
        # Include user_id in response if provided
        if user_id:
            response["user_id"] = user_id
        
        return response
    
    def _normalize_mode(self, mode: str) -> str:
        """Normalize search mode to standard values."""
        mode_lower = mode.lower().strip()
        
        if mode_lower in ["semantic", "semanticsearch", "semantic_search", "vector", "embedding"]:
            return "semantic"
        elif mode_lower in ["keyword", "keywords", "keywordsearch", "keyword_search", "text"]:
            return "keyword"
        elif mode_lower in ["auto", "automatic", "detect"]:
            return "auto"
        elif mode_lower in ["hybrid", "hybridsearch", "hybrid_search", "both"]:
            return "hybrid"
        else:
            print(f"Unknown search mode '{mode}', defaulting to hybrid")
            return "hybrid"
    
    def _detect_search_mode(self, query_text: str) -> str:
        """Rule-based search mode detection."""
        query_lower = query_text.lower()
        
        # Questions asking for definitions/explanations → semantic search
        if query_lower.startswith(("what is", "define", "explain", "describe", "how does", "tell me about")):
            return "semantic"
        
        # Queries with specific terms → keyword search
        if any(term in query_lower for term in ["find", "search", "locate", "where", "show me"]):
            return "keyword"
        
        # Default to hybrid for balanced results
        return "hybrid"
    
    def _extract_keywords(self, query_text: str) -> List[str]:
        """Extract keywords from query for keyword search."""
        stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
                     'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for', 'with', 
                     'by', 'about', 'like', 'through', 'over', 'before', 'after',
                     'between', 'under', 'above', 'of', 'during', 'since', 'what', 
            'who', 'where', 'when', 'how', 'why', 'find', 'search', 'locate', 'show', 'me'
        }
        
        # Extract keywords that are at least 3 characters and not stop words
        keywords = [
            word.lower() for word in query_text.split() 
            if len(word) > 2 and word.lower() not in stop_words
        ]
        
        # Prioritize longer keywords (more specific)
        keywords = sorted(keywords, key=len, reverse=True)
        
        return keywords if keywords else [query_text]
