"""
Command module for removing documents from the knowledge graph.
"""
import os
from src.graph_db.knowledge_graph import KnowledgeGraphManager


def remove_command(args):
    """
    Remove a document from the knowledge graph.
    
    Args:
        args: Command line arguments.
        
    Returns:
        True if successful, False otherwise.
    """
    pdf_path = args.pdf_path if hasattr(args, "pdf_path") else None
    file_hash = args.file_hash if hasattr(args, "file_hash") else None
    force = args.force if hasattr(args, "force") else False
    db_type = args.db_type if hasattr(args, "db_type") else "neo4j"
    user_id = getattr(args, "user_id", None) # Get user_id if provided, None otherwise
    
    # Verify that at least one identifier is provided
    if not pdf_path and not file_hash:
        print("Error: Either --pdf_path or --file_hash must be provided.")
        return False
    
    # Initialize knowledge graph manager
    kg_manager = KnowledgeGraphManager(graph_db_type=db_type)
    
    # Determine removal method
    if pdf_path:
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return False
        
        print(f"Removing document by file path: {pdf_path}")
        if user_id:
            print(f"For user: {user_id}")
        result = kg_manager.remove_document_by_path(pdf_path, force, user_id)
    else:
        print(f"Removing document by file hash: {file_hash}")
        if user_id:
            print(f"For user: {user_id}")
        result = kg_manager.remove_document_by_hash(file_hash, force, user_id)
    
    if result:
        print("Document successfully removed from the knowledge graph.")
        return True
    else:
        print("Failed to remove document from the knowledge graph.")
        return False 