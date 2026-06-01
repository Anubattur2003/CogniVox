"""
Dependency injection for Agentic-Graph-RAG API routes.
Pure RAG version - minimal dependencies for lightweight operation.
"""
from functools import lru_cache
from src.agents.document_analysis_agent import DocumentAnalysisAgent

@lru_cache()
def get_document_analysis_agent() -> DocumentAnalysisAgent:
    """
    Get cached instance of DocumentAnalysisAgent.
    Used for PDF processing to determine optimal chunking strategy.
    """
    return DocumentAnalysisAgent()

# Dependency instance for injection (singleton)
document_analysis_agent = get_document_analysis_agent()

# Legacy compatibility function for existing code
def analyze_document_with_llm(pdf_data: dict) -> dict:
    """
    Legacy compatibility function for document analysis during PDF processing.
    
    Args:
        pdf_data: Document data to analyze
        
    Returns:
        Analysis results
    """
    return document_analysis_agent.analyze_document(pdf_data) 