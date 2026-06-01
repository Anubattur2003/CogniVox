"""
Command module for PDF ingestion.
"""
import os
from src.config import CHUNK_SIZE, CHUNK_OVERLAP, USE_LLAMAINDEX
from src.graph_db.knowledge_graph import KnowledgeGraphManager


def ingest_command(args):
    """
    Ingest a PDF document into the knowledge graph.
    
    Args:
        args: Command line arguments.
        
    Returns:
        True if successful, False otherwise.
    """
    pdf_path = args.pdf_path
    force = args.force
    db_type = args.db_type
    chunk_size = args.chunk_size if args.chunk_size is not None else CHUNK_SIZE
    chunk_overlap = args.chunk_overlap if args.chunk_overlap is not None else CHUNK_OVERLAP
    extraction_method = args.extraction_method
    user_id = getattr(args, 'user_id', None)  # Get user_id if provided, None otherwise
    user_type = getattr(args, 'user_type', None)  # Get user_type if provided, None otherwise
    
    # Determine whether to use LlamaIndex
    use_llamaindex = None
    if hasattr(args, 'use_llamaindex') and args.use_llamaindex:
        use_llamaindex = True
        # Set this for compatibility with the ingest_command
        args.use_llamaindex = True
    elif hasattr(args, 'use_legacy') and args.use_legacy:
        use_llamaindex = False
        # Set this for compatibility with the ingest_command
        args.use_llamaindex = False
    # If neither is specified, use None (will use config default)
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return False
    
    print(f"Ingesting PDF: {pdf_path}")
    print(f"Using chunk size: {chunk_size}, chunk overlap: {chunk_overlap}")
    print(f"Using extraction method: {extraction_method}")
    
    # Print processing method
    if use_llamaindex is True:
        print("Using LlamaIndex for document processing")
    elif use_llamaindex is False:
        print("Using legacy processors for document processing")
    else:
        print(f"Using {'LlamaIndex' if USE_LLAMAINDEX else 'legacy'} processing (from config)")
    
    if user_id:
        print(f"Ingesting for user: {user_id}")
    elif user_type == "global":
        print(f"Ingesting as global document (no user_id)")
    
    # Initialize knowledge graph manager
    kg_manager = KnowledgeGraphManager(
        graph_db_type=db_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        use_llamaindex=use_llamaindex
    )
    
    # Ingest the PDF
    success = kg_manager.ingest_pdf(
        pdf_path, 
        force, 
        extraction_method=extraction_method, 
        user_id=user_id
    )
    
    if success:
        print(f"Successfully ingested PDF: {pdf_path}")
    else:
        print(f"Failed to ingest PDF: {pdf_path}")
    
    return success 