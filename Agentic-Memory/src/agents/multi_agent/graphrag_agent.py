"""
GraphRAG Agent

Specialized agent for knowledge base queries using GraphRAG.
"""
import logging
from typing import Dict, Any, Optional, List
from langchain_core.messages import SystemMessage

from src.agents.base_agent import BaseAgent
from src.utils.graphrag_client import GraphRAGClient
from src.utils.toon_format import format_system_instruction
from src.utils.agent_logger import get_agent_logger

logger = get_agent_logger("graphrag")


class GraphRAGAgent(BaseAgent):
    """
    Specialized agent for GraphRAG knowledge base operations.
    """
    
    def __init__(
        self,
        model_name: str = "qwen3:4b",
        temperature: float = 0.1,
        graphrag_client: Optional[GraphRAGClient] = None,
        **kwargs
    ):
        """Initialize the GraphRAG Agent."""
        system_instruction = self._create_system_instruction()
        
        super().__init__(
            agent_name="graphrag_agent",
            model_name=model_name,
            temperature=temperature,
            system_prompt=system_instruction,
            **kwargs
        )
        
        self.graphrag_client = graphrag_client or GraphRAGClient()
    
    def _create_system_instruction(self) -> str:
        """Create structured system instruction using TOON format."""
        instruction_data = {
            "role": "GraphRAG Knowledge Base Agent",
            "purpose": "Search and retrieve information from knowledge base",
            "capabilities": [
                "Semantic search",
                "Hybrid search (semantic + keyword)",
                "Document retrieval",
                "Context extraction"
            ],
            "search_modes": {
                "semantic": "Vector similarity search",
                "keyword": "Text-based search",
                "hybrid": "Combined semantic and keyword"
            },
            "output_format": {
                "context": "string - extracted context",
                "sources": "array - source documents",
                "source_found": "boolean - whether relevant sources found",
                "search_time": "float - search execution time"
            }
        }
        
        return format_system_instruction(instruction_data)
    
    def search(
        self,
        query: str,
        user_id: str = "default",
        n_results: int = 20,
        mode: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        Search the knowledge base using GraphRAG.
        
        Args:
            query: Search query
            user_id: User identifier
            n_results: Number of results
            mode: Search mode (semantic, keyword, hybrid)
            
        Returns:
            Search results with context and sources
        """
        try:
            logger.info(f"GraphRAG Agent: Searching knowledge base for '{query[:50]}...'")
            
            result = self.graphrag_client.fetch_context(
                query=query,
                user_id=user_id,
                n_results=n_results
            )
            
            # Format sources for consistency
            sources = result.get("sources", [])
            formatted_sources = []
            for source in sources:
                formatted_sources.append({
                    "document_title": source.get("document_title", "Unknown"),
                    "content": source.get("content", ""),
                    "page": source.get("page"),
                    "relevance": source.get("relevance", 0.0),
                    "file_path": source.get("file_path", ""),
                    "download_url": source.get("download_url", "")
                })
            
            return {
                "context": result.get("context", ""),
                "sources": formatted_sources,
                "source_found": result.get("source_found", False),
                "search_time": result.get("search_time", 0.0),
                "mode": mode,
                "n_results": len(formatted_sources)
            }
            
        except Exception as e:
            logger.error(f"GraphRAG search failed: {str(e)}")
            return {
                "context": "",
                "sources": [],
                "source_found": False,
                "search_time": 0.0,
                "error": str(e)
            }

