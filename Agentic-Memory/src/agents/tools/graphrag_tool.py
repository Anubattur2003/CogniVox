"""
GraphRAG Tool for LangChain Agents.

This tool wraps the GraphRAG client as a LangChain tool that can be used
by ReAct agents to retrieve relevant context from knowledge base when needed.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.utils.graphrag_client import GraphRAGClient

# Configure logging
logger = logging.getLogger("cogniVox")

class GraphRAGInput(BaseModel):
    """Input schema for GraphRAG tool."""
    query: str = Field(description="The query to search for in the knowledge base, or JSON string with all parameters")
    user_id: Optional[str] = Field(default=None, description="User ID for personalized knowledge base search")
    n_results: int = Field(default=20, description="Number of results to return (default: 20)")

class GraphRAGTool(BaseTool):
    """
    Tool for retrieving relevant context from the GraphRAG knowledge base.
    
    This tool should be used when:
    - The user asks about specific documents, papers, or technical content
    - The query requires factual information that might be in the knowledge base
    - The user asks about topics that could benefit from domain-specific knowledge
    - The question is about company policies, procedures, or documentation
    
    Do NOT use this tool when:
    - The query is a general conversation or greeting
    - The user asks about current events or real-time information
    - The question is about the user's personal information or preferences
    - Simple mathematical calculations or basic programming questions
    """
    
    name: str = "graphrag_search"
    description: str = """Search the knowledge base for relevant information using GraphRAG.

Use this tool when you need to find specific information from documents, papers, or technical content.
This tool is perfect for:
- Questions about specific topics that might be documented
- Technical queries requiring domain expertise
- Questions about company policies, procedures, or documentation
- Research-related queries

IMPORTANT: Always provide input as a JSON string with query, user_id, and optionally n_results.
Example: {"query": "your search query", "user_id": "user123", "n_results": 5}

The user_id is REQUIRED for personalized knowledge base searches."""
    
    args_schema: type[BaseModel] = GraphRAGInput
    
    # Declare graphrag_client as a Pydantic field to avoid validation errors
    graphrag_client: GraphRAGClient = Field(default_factory=lambda: GraphRAGClient())
    
    # Store the raw result for source extraction
    _last_result: Optional[Dict[str, Any]] = None
    
    def __init__(self, graphrag_client: Optional[GraphRAGClient] = None, **kwargs):
        """Initialize the GraphRAG tool."""
        # Pass graphrag_client through kwargs to parent constructor
        if graphrag_client is not None:
            kwargs['graphrag_client'] = graphrag_client
        super().__init__(**kwargs)
    
    def _run(self, query: str, user_id: str = None, n_results: int = 20, **kwargs) -> str:
        """
        Execute the GraphRAG search.
        
        Args:
            query: The search query or JSON string containing all parameters
            user_id: User ID for personalized search
            n_results: Number of results to return
            
        Returns:
            Formatted string with search results
        """
        try:
            # Handle case where query contains JSON with all parameters
            actual_query = query
            actual_user_id = user_id
            actual_n_results = n_results
            
            # Try to parse query as JSON if user_id is missing
            if user_id is None and isinstance(query, str):
                try:
                    parsed_input = json.loads(query)
                    actual_query = parsed_input.get("query", query)
                    actual_user_id = parsed_input.get("user_id")
                    actual_n_results = parsed_input.get("n_results", 20)
                    logger.info(f"Parsed JSON input: query='{actual_query}', user_id='{actual_user_id}', n_results={actual_n_results}")
                except (json.JSONDecodeError, TypeError):
                    # If JSON parsing fails, assume it's a regular query string
                    logger.warning(f"Could not parse as JSON, treating as regular query: {query}")
            
            # Validate that we have required parameters
            if not actual_user_id:
                logger.error("Missing user_id parameter for GraphRAG search")
                return "Error: user_id is required for personalized GraphRAG search"
            
            logger.info(f"GraphRAG tool executing search for user {actual_user_id}: {actual_query}")
            
            # Use the GraphRAG client to fetch context with user_id
            result = self.graphrag_client.fetch_context(
                query=actual_query,
                user_id=actual_user_id,
                n_results=actual_n_results
            )
            
            # Store the raw result for source extraction
            self._last_result = result
            
            if not result.get("source_found", False) or not result.get("sources"):
                return f"KNOWLEDGE_BASE_EMPTY: No relevant information found. Stop searching and respond immediately."
            
            # Format the response with context and sources
            context = result.get("context", "")
            sources = result.get("sources", [])
            
            formatted_response = []
            
            if context.strip():
                formatted_response.append(f"KNOWLEDGE BASE INFORMATION:\n{context}")
            
            if sources:
                formatted_response.append("\nSOURCE DOCUMENTS:")
                for i, source in enumerate(sources[:3], 1):  # Limit to top 3 sources
                    doc_title = source.get("document_title", "Unknown Document")
                    content = source.get("content", "").strip()
                    relevance = source.get("relevance", 0.0)
                    
                    if content:
                        # Limit content length for better readability
                        if len(content) > 500:
                            content = content[:500] + "..."
                        
                        formatted_response.append(
                            f"\n{i}. {doc_title} (Relevance: {relevance:.2f})\n{content}"
                        )
            
            if formatted_response:
                result_text = "\n".join(formatted_response)
                logger.info(f"GraphRAG tool returning {len(sources)} sources")
                return result_text
            else:
                return f"No relevant content found for query: '{actual_query}'"
                
        except Exception as e:
            logger.error(f"Error in GraphRAG tool: {str(e)}")
            return f"Error searching knowledge base: {str(e)}"
    
    def get_last_sources(self) -> List[Dict[str, Any]]:
        """
        Get the source documents from the last search.
        
        Returns:
            List of source documents with metadata
        """
        if self._last_result and self._last_result.get("sources"):
            return self._last_result["sources"]
        return []
    
    def get_last_result(self) -> Optional[Dict[str, Any]]:
        """
        Get the complete result from the last search.
        
        Returns:
            Complete result dictionary or None
        """
        return self._last_result
    
    def clear_last_result(self) -> None:
        """
        Clear the stored result from the last search.
        
        This should be called at the start of each conversation to prevent
        source documents from previous conversations being carried over.
        """
        self._last_result = None
    
    async def _arun(self, query: str, user_id: str = None, n_results: int = 20, **kwargs) -> str:
        """Async version of the tool (not implemented yet)."""
        # For now, just call the sync version
        return self._run(query, user_id, n_results, **kwargs)

def create_graphrag_tool(graphrag_client: Optional[GraphRAGClient] = None) -> GraphRAGTool:
    """
    Factory function to create a GraphRAG tool instance.
    
    Args:
        graphrag_client: Optional GraphRAG client instance
        
    Returns:
        GraphRAGTool instance
    """
    return GraphRAGTool(graphrag_client=graphrag_client) 