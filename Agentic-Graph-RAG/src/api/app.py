"""
CogniVox GraphRAG API Service.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
import sys
import logging
import json
import uvicorn
from pathlib import Path
import asyncio
import concurrent.futures
import glob
import time
import shutil
import chromadb
from pathlib import Path as PathlibPath
from urllib.parse import unquote

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import CogniVox components
from src.cli.commands.ingest import ingest_command
from src.cli.commands.query import query_command
from src.cli.commands.visualize import visualize_command
from src.cli.commands.export import export_command
from src.cli.commands.remove import remove_command


# Import QueryProcessor directly for direct access to query results
from src.query_engine import QueryProcessor
from src.gcp_bucket import get_cached_storage_manager
from src.utils.config_loader import ConfigLoader

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cognivox-api")

# Initialize configuration
config_loader = ConfigLoader(config_file="config.yaml")
config = config_loader.get_all()

# Initialize storage manager
storage_manager = get_cached_storage_manager(config)

# Create FastAPI app
app = FastAPI(
    title="CogniVox GraphRAG API",
    description="API for CogniVox Knowledge Graph RAG system",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure with proper origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define API models
class QueryRequest(BaseModel):
    query: str
    mode: str = "hybrid"
    n_results: int = 20
    format: str = "text"  # "text", "json", or "markdown"
    user_id: Optional[str] = None  # Optional user ID for user-specific queries

class QueryResponse(BaseModel):
    query: str
    mode: str
    sources: List[Dict[str, Any]]  # Renamed from 'results' for Memory compatibility
    source_found: bool  # Flag indicating if relevant documents were found
    context: str  # Formatted context from all sources
    answer: str  # Alias for context (backward compatibility with Memory)
    result_count: int
    search_time: float
    user_id: Optional[str] = None

class IngestResponse(BaseModel):
    success: bool
    message: str
    document_ids: List[str] = []
    metadata: Optional[Dict[str, Any]] = None

class StatusResponse(BaseModel):
    status: str
    version: str
    db_status: str
    vector_store_status: str
    document_count: int

class DatabaseCleanupResponse(BaseModel):
    success: bool
    message: str
    cleaned_components: List[str] = []
    errors: List[str] = []
    statistics: Optional[Dict[str, Any]] = None

# API Health check
@app.get("/health", response_model=StatusResponse)
async def health_check():
    """Check the health of the GraphRAG service - Pure RAG version."""
    try:
        from src.config import GRAPH_DB_TYPE, VECTOR_STORE_TYPE
        
        # Simple health check - just verify we can initialize
        try:
            query_processor = QueryProcessor()
            status = "healthy"
            message = "Pure RAG system operational"
        except Exception as init_error:
            status = "degraded"
            message = f"Initialization failed: {str(init_error)}"
        
        return StatusResponse(
            status=status,
            version="1.0.0",
            db_status="connected",
            vector_store_status="connected", 
            document_count=0
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Query API - Pure RAG (Lightweight)
@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the knowledge graph - Pure RAG (retrieval only, no LLM generation)."""
    try:
        # Initialize query processor
        query_processor = QueryProcessor()
        
        # Get query parameters
        query_text = request.query
        mode = request.mode
        n_results = request.n_results
        
        # Clean and validate user_id
        user_id = request.user_id if request.user_id and request.user_id.strip() else None
        invalid_user_ids = {"string", "undefined", "null", "none", "test", "example"}
        if user_id and user_id.lower() in invalid_user_ids:
            user_id = None
        
        logger.info(f"Pure RAG query: '{query_text}' (mode: {mode}, n_results: {n_results})")
        
        # Execute pure RAG query (no LLM generation)
        result = query_processor.query(query_text, mode, n_results, user_id=user_id)
        
        # Return raw results directly
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Process a single PDF file
async def process_single_pdf(pdf_path, force, extraction_method, db_type, chunk_size, chunk_overlap, user_id=None, use_llamaindex=None):
    """Process a single PDF file in a separate thread to avoid blocking."""
    class Args:
        pass
    
    args = Args()
    args.pdf_path = str(pdf_path)
    args.force = force
    args.extraction_method = extraction_method
    args.db_type = db_type
    args.chunk_size = chunk_size
    args.chunk_overlap = chunk_overlap
    args.user_id = user_id  # Add user_id to args
    args.use_llamaindex = use_llamaindex
    
    # Ensure user_type is set to "global" when no user_id is provided
    # This is important for properly filtering documents in the knowledge graph
    if not user_id:
        args.user_type = "global"
    
    # Run ingest_command in a thread pool to avoid blocking
    with concurrent.futures.ThreadPoolExecutor() as executor:
        return await asyncio.get_event_loop().run_in_executor(
            executor, ingest_command, args
        )

# Document Ingest API - For file uploads
@app.post("/ingest", response_model=IngestResponse)
async def ingest(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Multiple PDF files can be uploaded simultaneously"),
    force: bool = False,
    extraction_method: str = "auto",
    max_workers: int = 4,  # Control parallelism
    user_id: Optional[str] = None,  # Optional user ID to associate documents with a specific user
    use_llamaindex: Optional[bool] = None  # Optional flag to use LlamaIndex (overrides config)
):
    """
    Ingest multiple PDF documents into the knowledge graph.
    
    Parameters:
    - files: List of PDF files to ingest. Multiple files can be selected in the file dialog.
    - force: Whether to force re-ingestion if document already exists
    - extraction_method: Method to extract text from PDFs (auto, pypdf2, pdfminer, ocr)
    - max_workers: Maximum number of parallel ingestion processes
    - user_id: Optional user ID to associate documents with a specific user.
               If provided, documents will be isolated to this user.
               If not provided, documents will be globally accessible.
    """
    try:
        # Fix: Convert empty string user_id to None
        user_id = user_id if user_id and user_id.strip() else None
        
        file_paths = []
        
        # Process uploaded files
        if files:
            # Save files temporarily for processing (no immediate GCP upload)
            for file in files:
                if not file.filename.lower().endswith('.pdf'):
                    logger.warning(f"Skipping non-PDF file: {file.filename}")
                    continue
                
                # Save file temporarily for processing
                temp_dir = Path("temp_uploads")
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_file_path = temp_dir / file.filename
                
                with open(temp_file_path, "wb") as f:
                    f.write(file.file.read())
                
                # Add to processing queue (let PDF processor handle storage)
                logger.info(f"Prepared {file.filename} for processing")
                file_paths.append(temp_file_path)
        
        # Validate we have files to process
        if not file_paths:
            raise HTTPException(status_code=400, detail="No valid PDF files provided")
        
        # Start processing in background
        db_type = os.getenv("GRAPH_DB_TYPE", "neo4j")
        chunk_size = None
        chunk_overlap = None
        
        # Log user information if available
        if user_id:
            logger.info(f"Ingesting documents for user: {user_id}")
        
        # Define task to process files in parallel
        async def process_files_in_parallel():
            try:
                # Process files in batches to control parallelism
                results = []
                for i in range(0, len(file_paths), max_workers):
                    batch = file_paths[i:i+max_workers]
                    tasks = [
                        process_single_pdf(
                            path, force, extraction_method, db_type, chunk_size, chunk_overlap, user_id, use_llamaindex
                        ) for path in batch
                    ]
                    batch_results = await asyncio.gather(*tasks)
                    results.extend(batch_results)
                
                logger.info(f"Completed ingestion of {len(file_paths)} documents")
                return results
            finally:
                # Clean up temporary files
                for file_path in file_paths:
                    try:
                        if file_path.exists() and "temp_uploads" in str(file_path):
                            file_path.unlink(missing_ok=True)
                    except Exception as e:
                        logger.warning(f"Failed to clean up temporary file {file_path}: {e}")
                
                # Remove temp directory if empty
                try:
                    temp_dir = Path("temp_uploads")
                    if temp_dir.exists() and not any(temp_dir.iterdir()):
                        temp_dir.rmdir()
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory: {e}")
        
        # Add the parallel processing task to background tasks
        background_tasks.add_task(process_files_in_parallel)
        
        file_names = [str(f.name) for f in file_paths]
        response_metadata = {
            "file_count": len(file_paths),
            "source": "upload"
        }
        
        # Include user_id in metadata if provided
        if user_id:
            response_metadata["user_id"] = user_id
            
        return IngestResponse(
            success=True,
            message=f"Processing {len(file_paths)} documents in the background",
            document_ids=file_names,
            metadata=response_metadata
        )
    except Exception as e:
        logger.error(f"Ingest failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Directory-based ingest API
@app.post("/ingest/directory", response_model=IngestResponse)
async def ingest_directory(
    background_tasks: BackgroundTasks,
    directory_path: str = None,
    recursive: bool = True,
    force: bool = False,
    extraction_method: str = "auto",
    max_workers: int = 4,  # Control parallelism
    user_id: Optional[str] = None,  # Optional user ID to associate documents with a specific user
    use_llamaindex: Optional[bool] = None  # Optional flag to use LlamaIndex (overrides config)
):
    """
    Ingest all PDF documents from a directory into the knowledge graph.
    
    Parameters:
    - directory_path: Path to a directory containing PDF files to process
    - recursive: Whether to search for PDFs in subdirectories
    - force: Whether to force re-ingestion if document already exists
    - extraction_method: Method to extract text from PDFs (auto, pypdf2, pdfminer, ocr)
    - max_workers: Maximum number of parallel ingestion processes
    - user_id: Optional user ID to associate documents with a specific user.
               If provided, documents will be isolated to this user.
               If not provided, documents will be globally accessible.
    """
    try:
        # Fix: Convert empty string user_id to None
        user_id = user_id if user_id and user_id.strip() else None
        
        if not directory_path:
            raise HTTPException(status_code=400, detail="Directory path is required")
            
        file_paths = []
        
        # Process directory of PDFs
        dir_path = Path(directory_path)
        if not dir_path.exists():
            raise HTTPException(status_code=400, detail=f"Directory not found: {directory_path}")
        
        # Use glob pattern to find PDFs, recursively if specified
        pattern = "**/*.pdf" if recursive else "*.pdf"
        pdf_files = list(dir_path.glob(pattern))
        
        if pdf_files:
            logger.info(f"Found {len(pdf_files)} PDF files in directory")
        file_paths.extend(pdf_files)
        
        # Validate we have files to process
        if not file_paths:
            raise HTTPException(status_code=400, detail="No PDF files found in the specified directory")
        
        # Start processing in background
        db_type = os.getenv("GRAPH_DB_TYPE", "neo4j")
        chunk_size = None
        chunk_overlap = None
        
        # Log user information if available
        if user_id:
            logger.info(f"Ingesting directory documents for user: {user_id}")
        
        # Define task to process files in parallel
        async def process_files_in_parallel():
            try:
                # Process files in batches to control parallelism
                results = []
                for i in range(0, len(file_paths), max_workers):
                    batch = file_paths[i:i+max_workers]
                    tasks = [
                        process_single_pdf(
                            path, force, extraction_method, db_type, chunk_size, chunk_overlap, user_id, use_llamaindex
                        ) for path in batch
                    ]
                    batch_results = await asyncio.gather(*tasks)
                    results.extend(batch_results)
                
                logger.info(f"Completed ingestion of {len(file_paths)} documents")
                return results
            finally:
                # Clean up temporary files
                for file_path in file_paths:
                    try:
                        if file_path.exists() and "temp_uploads" in str(file_path):
                            file_path.unlink(missing_ok=True)
                    except Exception as e:
                        logger.warning(f"Failed to clean up temporary file {file_path}: {e}")
                
                # Remove temp directory if empty
                try:
                    temp_dir = Path("temp_uploads")
                    if temp_dir.exists() and not any(temp_dir.iterdir()):
                        temp_dir.rmdir()
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory: {e}")
        
        # Add the parallel processing task to background tasks
        background_tasks.add_task(process_files_in_parallel)
        
        file_names = [str(f.name) for f in file_paths]
        response_metadata = {
            "file_count": len(file_paths),
            "source": "directory",
            "directory": directory_path
        }
        
        # Include user_id in metadata if provided
        if user_id:
            response_metadata["user_id"] = user_id
            
        return IngestResponse(
            success=True,
            message=f"Processing {len(file_paths)} documents in the background",
            document_ids=file_names,
            metadata=response_metadata
        )
    except Exception as e:
        logger.error(f"Ingest failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Storage Management API
@app.get("/documents/list")
async def list_documents(user_id: Optional[str] = None, limit: int = 50):
    """
    List documents in storage.
    
    Parameters:
    - user_id: Optional user ID to list user-specific documents
    - limit: Maximum number of documents to return
    """
    try:
        # Fix: Convert empty string user_id to None
        user_id = user_id if user_id and user_id.strip() else None
        
        logger.info(f"Listing documents for user_id: {user_id}, limit: {limit}")
        
        documents = storage_manager.list_documents(user_id=user_id, limit=limit)
        
        logger.info(f"Found {len(documents)} documents from storage_manager")
        
        # Convert to simple dict format for API response
        # Also fetch enabled status from Neo4j for each document (if available)
        document_list = []
        
        # Try to initialize Neo4j connection, but don't fail if it's unavailable
        kg_manager = None
        try:
            from src.graph_db import KnowledgeGraphManager
            from src.graph_db.neo4j_adapter import Neo4jAdapter
            kg_manager = KnowledgeGraphManager()
            logger.info("Successfully initialized KnowledgeGraphManager")
        except Exception as neo4j_error:
            logger.warning(f"Neo4j not available for enabled status check: {neo4j_error}")
            # Continue without Neo4j - will use default enabled=True
        
        for doc in documents:
            # Extract file hash from blob_name (filename without .pdf extension)
            blob_name = doc.filename
            file_hash = blob_name.replace('.pdf', '') if blob_name.endswith('.pdf') else blob_name
            
            # Get enabled status from Neo4j (if available)
            enabled = True  # Default to enabled for backward compatibility
            if kg_manager is not None:
                try:
                    if isinstance(kg_manager.graph_db, Neo4jAdapter):
                        doc_node = kg_manager.graph_db.find_document_by_hash(file_hash, user_id)
                        if doc_node:
                            # Get enabled status (default to True if not set)
                            enabled = doc_node.get("enabled", True)
                        else:
                            # If document doesn't exist in Neo4j, default to enabled
                            # (it will be created as enabled when first disabled/enabled)
                            enabled = True
                except Exception as e:
                    logger.warning(f"Failed to fetch enabled status for {file_hash}: {e}")
                    # Use default enabled=True if query fails
            
            document_list.append({
                "filename": doc.original_filename,
                "blob_name": doc.filename,  # Use filename property for display
                "file_size": doc.file_size,
                "created_at": doc.created_at.isoformat(),
                "download_url": doc.download_url,
                "storage_path": doc.full_path,
                "enabled": enabled  # Include enabled status from Neo4j
            })
        
        logger.info(f"Returning {len(document_list)} documents in response")
        
        return {
            "documents": document_list,
            "count": len(document_list),
            "user_id": user_id,
            "storage_type": "local"
        }
        
    except Exception as e:
        logger.error(f"List documents failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}/download")
async def download_document(document_id: str, user_id: Optional[str] = None):
    """
    Download a document from storage.
    
    Parameters:
    - document_id: ID/name of the document to download
    - user_id: Optional user ID for user-specific documents
    """
    try:
        # Fix: Convert empty string user_id to None
        user_id = user_id if user_id and user_id.strip() else None
        
        # Get download path
        temp_dir = Path("temp_downloads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        local_path = temp_dir / document_id
        
        result = storage_manager.download_document(
            document_path=document_id,
            local_path=local_path,
            user_id=user_id
        )
        
        if result.is_success:
            return FileResponse(
                path=str(local_path),
                filename=document_id,
                media_type="application/pdf"
            )
        else:
            raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
            
    except Exception as e:
        logger.error(f"Download document failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Remove document API
@app.delete("/documents/{document_id}")
async def remove(document_id: str, force: bool = False, user_id: Optional[str] = None):
    """Remove a document from the knowledge graph."""
    try:
        # Fix: Convert empty string user_id to None
        user_id = user_id if user_id and user_id.strip() else None
        
        # Extract filename from path if it contains slashes (e.g., "users/12/filename.pdf" -> "filename.pdf")
        # Also handle cases where document_id might be just the hash without extension
        if '/' in document_id:
            filename = document_id.split('/')[-1]
            # Remove .pdf extension if present to get the hash
            file_hash = filename.replace('.pdf', '') if filename.endswith('.pdf') else filename
        else:
            file_hash = document_id.replace('.pdf', '') if document_id.endswith('.pdf') else document_id
        
        logger.info(f"Removing document: {document_id} (hash: {file_hash}) for user: {user_id}")
        
        class Args:
            pass
        
        args = Args()
        args.file_hash = file_hash
        args.force = True  # Always force deletion for API calls (no user prompt)
        args.user_id = user_id
        args.db_type = os.getenv("GRAPH_DB_TYPE", "neo4j")
        
        # Remove the document from graph
        success = remove_command(args)
        
        # Also remove from storage if the graph removal was successful
        if success:
            try:
                # Use the original document_id (which might be a path) for storage deletion
                # If document_id is just a filename, storage_manager will construct the path
                # If it's already a full path (e.g., "users/12/file.pdf"), use it as-is
                storage_result = storage_manager.delete_document(
                    document_path=document_id,
                    user_id=user_id
                )
                if not storage_result.is_success:
                    logger.warning(f"Failed to remove document from storage: {storage_result.message}")
                    # Don't fail the whole operation if storage deletion fails
            except Exception as e:
                logger.warning(f"Error removing document from storage: {e}")
                # Don't fail the whole operation if storage deletion fails
        
        if not success:
            if user_id:
                raise HTTPException(status_code=404, detail=f"Document {document_id} for user {user_id} not found")
            else:
                raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
        
        return {"success": True, "message": f"Document {document_id} removed successfully"}
    except Exception as e:
        logger.error(f"Remove failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Enable document API
@app.post("/documents/{document_id}/enable")
async def enable_document(document_id: str, user_id: Optional[str] = None):
    """
    Enable a document for querying.
    
    Parameters:
    - document_id: ID/name of the document to enable (URL encoded)
    - user_id: Optional user ID for user-specific documents
    """
    try:
        user_id = user_id if user_id and user_id.strip() else None
        
        # URL decode the document_id in case it was encoded
        document_id = unquote(document_id)
        
        # Extract filename from path if it contains slashes
        filename = document_id.split('/')[-1] if '/' in document_id else document_id
        # Remove .pdf extension if present to get the hash
        file_hash = filename.replace('.pdf', '') if filename.endswith('.pdf') else filename
        
        logger.info(f"Enabling document {filename} (hash: {file_hash}) for user_id: {user_id}")
        
        # Update enabled status in knowledge graph
        from src.graph_db import KnowledgeGraphManager
        kg_manager = KnowledgeGraphManager()
        success = kg_manager.update_document_enabled_status(file_hash, enabled=True, user_id=user_id)
        
        if success:
            return {"success": True, "message": f"Document {filename} enabled successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Document {filename} not found or cannot be enabled")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enable document failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Disable document API
@app.post("/documents/{document_id}/disable")
async def disable_document(document_id: str, user_id: Optional[str] = None):
    """
    Disable a document from querying.
    
    Parameters:
    - document_id: ID/name of the document to disable (URL encoded)
    - user_id: Optional user ID for user-specific documents
    """
    try:
        user_id = user_id if user_id and user_id.strip() else None
        
        # URL decode the document_id in case it was encoded
        document_id = unquote(document_id)
        
        # Extract filename from path if it contains slashes
        filename = document_id.split('/')[-1] if '/' in document_id else document_id
        # Remove .pdf extension if present to get the hash
        file_hash = filename.replace('.pdf', '') if filename.endswith('.pdf') else filename
        
        logger.info(f"Disabling document {filename} (hash: {file_hash}) for user_id: {user_id}")
        
        # Update enabled status in knowledge graph
        from src.graph_db import KnowledgeGraphManager
        kg_manager = KnowledgeGraphManager()
        success = kg_manager.update_document_enabled_status(file_hash, enabled=False, user_id=user_id)
        
        if success:
            return {"success": True, "message": f"Document {filename} disabled successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Document {filename} not found or cannot be disabled")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Disable document failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get visualization API
@app.get("/visualize")
async def visualize(output_format: str = "html", node_limit: int = 100):
    """Generate a visualization of the knowledge graph."""
    try:
        class Args:
            pass
        
        args = Args()
        args.output_format = output_format
        args.node_limit = node_limit
        args.all = False
        args.output_path = None
        
        # Generate visualization
        result = visualize_command(args)
        
        if not result:
            raise HTTPException(status_code=500, detail="Visualization generation failed")
        
        # For html format, we would return the HTML content
        if output_format == "html":
            return {"success": True, "visualization_path": result}
        else:
            return {"success": True, "message": f"Visualization generated at {result}"}
    except Exception as e:
        logger.error(f"Visualization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Export API
@app.get("/export")
async def export(format: str = "json"):
    """Export the knowledge graph."""
    try:
        class Args:
            pass
        
        args = Args()
        args.format = format
        args.output_path = None  # Let the function generate a path
        
        # Export the knowledge graph
        result = export_command(args)
        
        if not result:
            raise HTTPException(status_code=500, detail="Export failed")
        
        return {"success": True, "export_path": result}
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Database Cleanup API
@app.post("/database/cleanup", response_model=DatabaseCleanupResponse)
async def cleanup_database(
    confirm: bool = False,
    include_local_data: bool = True,
    include_gcp_data: bool = True,
    include_temp_files: bool = True,
    nuclear_mode: bool = False
):
    """
    Clean up all data sources including ChromaDB vector store, Neo4j database, local data, and GCP data.
    
    Parameters:
    - confirm: Required confirmation flag to prevent accidental database cleanup
    - include_local_data: Whether to clean local document storage
    - include_gcp_data: Whether to clean GCP bucket data
    - include_temp_files: Whether to clean temporary files
    """
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Database cleanup requires confirmation. Set 'confirm=true' to proceed."
        )
    
    cleaned_components = []
    errors = []
    statistics = {}
    
    try:
        logger.info("Starting comprehensive database cleanup...")
        
        if nuclear_mode:
            logger.warning("NUCLEAR MODE ENABLED: Will attempt aggressive physical file deletion")
            statistics['nuclear_mode'] = True
        
        # 1. Clean ChromaDB Vector Store (Isolated approach for 24/7 server)
        try:
            logger.info("Cleaning ChromaDB vector store...")
            
            # Get vector count before cleanup (safely)
            vector_count_before = 'unknown'
            collections_deleted = 0
            vectors_deleted = 0
            
            # Strategy 1: Completely isolated cleanup with client management
            try:
                if nuclear_mode:
                    logger.info("Using NUCLEAR MODE ChromaDB cleanup - attempting physical file deletion...")
                else:
                    logger.info("Using isolated ChromaDB cleanup approach...")
                import chromadb
                from chromadb.config import Settings
                from src.config import VECTOR_STORE_PATH
                import gc
                import time
                
                # Get existing vector store to check count (without triggering recreation)
                try:
                    from src.graph_db.vector_store import get_vector_store
                    vector_store = get_vector_store()
                    if hasattr(vector_store, 'collection'):
                        vector_count_before = vector_store.collection.count()
                        statistics['chromadb_vectors_before'] = vector_count_before
                        logger.info(f"Found {vector_count_before} vectors before cleanup")
                        
                        # Important: Close the vector store to release locks
                        if hasattr(vector_store, 'client'):
                            try:
                                vector_store.client.clear_system_cache()
                            except:
                                pass
                        del vector_store
                        
                except Exception as e:
                    logger.warning(f"Could not get vector count: {e}")
                    statistics['chromadb_vectors_before'] = 'unknown'
                
                # Force garbage collection to release references
                gc.collect()
                time.sleep(0.1)
                
                # Create a completely isolated client for cleanup
                cleanup_client = chromadb.PersistentClient(
                    path=str(VECTOR_STORE_PATH),
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True  # Allow reset operations
                    )
                )
                
                # Method 1: Try complete reset (most thorough)
                try:
                    logger.info("Attempting complete ChromaDB reset...")
                    cleanup_client.reset()
                    logger.info("Successfully reset entire ChromaDB database")
                    collections_deleted = 1  # Reset counts as deleting all collections
                    vectors_deleted = vector_count_before if isinstance(vector_count_before, int) else 0
                    
                    # After reset, try physical file cleanup for complete removal
                    if nuclear_mode:
                        try:
                            logger.info("NUCLEAR MODE: Attempting aggressive physical file cleanup after reset...")
                            
                            # Close the client first
                            try:
                                cleanup_client.clear_system_cache()
                            except:
                                pass
                            del cleanup_client
                            
                            # Force aggressive garbage collection
                            gc.collect()
                            time.sleep(1.0)  # Give more time in nuclear mode
                            
                            # Try to forcefully close any global vector store instances
                            try:
                                import sys
                                # Force cleanup of any cached instances
                                if 'src.graph_db.vector_store' in sys.modules:
                                    module = sys.modules['src.graph_db.vector_store']
                                    if hasattr(module, '_vector_store_cache'):
                                        module._vector_store_cache = None
                                gc.collect()
                            except Exception as cache_e:
                                logger.warning(f"Could not clear vector store cache: {cache_e}")
                            
                            # Now try to delete physical files with multiple strategies
                            from src.config import VECTOR_STORE_PATH
                            chroma_path = PathlibPath(VECTOR_STORE_PATH)
                            
                            if chroma_path.exists():
                                # Strategy 1: Try simple removal
                                try:
                                    shutil.rmtree(chroma_path)
                                    chroma_path.mkdir(parents=True, exist_ok=True)
                                    logger.info("NUCLEAR SUCCESS: Removed and recreated ChromaDB directory")
                                    statistics['chromadb_physical_cleanup'] = True
                                    
                                except PermissionError as pe:
                                    logger.warning(f"NUCLEAR MODE: Simple removal failed: {pe}")
                                    
                                    # Strategy 2: Individual file removal with retries
                                    files_deleted = 0
                                    files_failed = 0
                                    
                                    for file_path in chroma_path.rglob('*'):
                                        if file_path.is_file():
                                            for attempt in range(10):  # More retries in nuclear mode
                                                try:
                                                    # Try to change permissions
                                                    try:
                                                        import stat
                                                        file_path.chmod(stat.S_IWRITE)
                                                    except:
                                                        pass
                                                    
                                                    file_path.unlink()
                                                    files_deleted += 1
                                                    logger.debug(f"NUCLEAR: Deleted {file_path}")
                                                    break
                                                    
                                                except (PermissionError, OSError) as e:
                                                    if attempt == 9:  # Last attempt
                                                        logger.warning(f"NUCLEAR: Failed to delete {file_path}: {e}")
                                                        files_failed += 1
                                                    else:
                                                        # Longer delays in nuclear mode
                                                        gc.collect()
                                                        time.sleep(0.5 * (attempt + 1))
                                    
                                    # Try to remove directories
                                    for dir_path in sorted(chroma_path.rglob('*'), key=lambda p: len(str(p)), reverse=True):
                                        if dir_path.is_dir():
                                            try:
                                                dir_path.rmdir()
                                            except OSError:
                                                pass
                                    
                                    # Try to remove main directory
                                    try:
                                        chroma_path.rmdir()
                                        chroma_path.mkdir(parents=True, exist_ok=True)
                                        logger.info(f"NUCLEAR: Removed directory after cleaning {files_deleted} files")
                                        statistics['chromadb_physical_cleanup'] = True
                                    except OSError:
                                        logger.warning(f"NUCLEAR: Cleaned {files_deleted} files, {files_failed} failed, directory remains")
                                        statistics['chromadb_physical_cleanup'] = False if files_deleted == 0 else 'partial'
                            
                            # Recreate client for any remaining operations
                            cleanup_client = chromadb.PersistentClient(
                                path=str(VECTOR_STORE_PATH),
                                settings=Settings(
                                    anonymized_telemetry=False,
                                    allow_reset=True
                                )
                            )
                            
                        except Exception as nuclear_e:
                            logger.error(f"NUCLEAR MODE failed: {nuclear_e}")
                            statistics['chromadb_physical_cleanup'] = False
                            # Recreate client anyway
                            cleanup_client = chromadb.PersistentClient(
                                path=str(VECTOR_STORE_PATH),
                                settings=Settings(
                                    anonymized_telemetry=False,
                                    allow_reset=True
                                )
                            )
                    else:
                        # Standard mode - just note that physical files remain
                        logger.info("Standard mode: Physical files retained for performance (use nuclear_mode=true for file deletion)")
                        statistics['chromadb_physical_cleanup'] = 'skipped'
                    
                except Exception as reset_e:
                    logger.warning(f"Complete reset failed: {reset_e}, trying collection-by-collection cleanup...")
                    
                    # Method 2: Collection-by-collection cleanup
                    try:
                        collections = cleanup_client.list_collections()
                        if collections:
                            logger.info(f"Found {len(collections)} ChromaDB collections to clean")
                        
                        for collection in collections:
                            try:
                                collection_name = collection.name
                                
                                # Get collection and clear all data
                                coll = cleanup_client.get_collection(collection_name)
                                
                                # Get all IDs and delete them
                                try:
                                    # Try to get all documents in batches to avoid memory issues
                                    batch_size = 1000
                                    total_deleted = 0
                                    
                                    while True:
                                        result = coll.get(limit=batch_size)
                                        if not result or not result.get('ids'):
                                            break
                                            
                                        ids_to_delete = result['ids']
                                        coll.delete(ids=ids_to_delete)
                                        total_deleted += len(ids_to_delete)
                                        
                                        # Small pause to avoid overwhelming the system
                                        time.sleep(0.01)
                                    
                                    if total_deleted > 0:
                                        vectors_deleted += total_deleted
                                        
                                except Exception as clear_e:
                                    # If clearing fails, try deleting the entire collection
                                    logger.warning(f"Could not clear collection '{collection_name}': {clear_e}")
                                    cleanup_client.delete_collection(collection_name)
                                
                                collections_deleted += 1
                                
                            except Exception as ce:
                                logger.warning(f"Failed to process collection {collection.name}: {ce}")
                        
                    except Exception as coll_e:
                        logger.warning(f"Collection cleanup failed: {coll_e}")
                        raise coll_e
                
                # Clean up client properly
                try:
                    cleanup_client.clear_system_cache()
                except:
                    pass
                del cleanup_client
                
                # Force aggressive garbage collection
                gc.collect()
                time.sleep(0.2)
                
                # Mark as successfully cleaned
                cleaned_components.append("ChromaDB Vector Store")
                statistics['chromadb_status'] = 'cleaned'
                statistics['chromadb_method'] = 'isolated_cleanup'
                statistics['chromadb_collections_deleted'] = collections_deleted
                statistics['chromadb_vectors_deleted'] = vectors_deleted
                
                logger.info(f"Successfully cleaned ChromaDB: {collections_deleted} collections, {vectors_deleted} vectors processed")
                
            except Exception as rt_e:
                logger.warning(f"Isolated cleanup failed: {rt_e}, trying fallback methods...")
                
                # Strategy 2: Fallback - Try direct collection manipulation
                try:
                    # Import after the failed attempt to ensure clean state
                    import chromadb
                    from chromadb.config import Settings
                    
                    # Create new isolated client
                    fallback_client = chromadb.PersistentClient(
                        path=str(VECTOR_STORE_PATH),
                        settings=Settings(anonymized_telemetry=False)
                    )
                    
                    # Try to list and delete collections one by one
                    try:
                        collections = fallback_client.list_collections()
                        for collection in collections:
                            try:
                                fallback_client.delete_collection(collection.name)
                                collections_deleted += 1
                            except Exception as del_e:
                                logger.warning(f"Could not delete collection {collection.name}: {del_e}")
                    except Exception as list_e:
                        logger.warning(f"Could not list collections: {list_e}")
                    
                    del fallback_client
                    gc.collect()
                    
                    if collections_deleted > 0:
                        cleaned_components.append("ChromaDB Vector Store (Fallback)")
                        statistics['chromadb_status'] = 'partially_cleaned'
                        statistics['chromadb_method'] = 'fallback_collection_deletion'
                        statistics['chromadb_collections_deleted'] = collections_deleted
                    else:
                        raise Exception("No collections could be cleaned")
                        
                except Exception as fb_e:
                    logger.error(f"All ChromaDB cleanup methods failed: {fb_e}")
                    raise fb_e
                        
        except Exception as e:
            error_msg = f"ChromaDB cleanup failed: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # 2. Clean Neo4j Database
        try:
            logger.info("Cleaning Neo4j database...")
            from src.graph_db.neo4j_adapter import Neo4jAdapter
            
            neo4j_adapter = Neo4jAdapter()
            
            # Get counts before cleanup
            try:
                result = neo4j_adapter.graph.run("MATCH (n) RETURN count(n) as node_count").data()
                statistics['neo4j_nodes_before'] = result[0]['node_count'] if result else 0
                
                result = neo4j_adapter.graph.run("MATCH ()-[r]->() RETURN count(r) as rel_count").data()
                statistics['neo4j_relationships_before'] = result[0]['rel_count'] if result else 0
            except:
                statistics['neo4j_nodes_before'] = 'unknown'
                statistics['neo4j_relationships_before'] = 'unknown'
            
            # Delete all nodes and relationships
            cleanup_query = """
            MATCH (n)
            DETACH DELETE n
            """
            neo4j_adapter.graph.run(cleanup_query)
            
            # Verify cleanup
            result = neo4j_adapter.graph.run("MATCH (n) RETURN count(n) as remaining_nodes").data()
            remaining_nodes = result[0]['remaining_nodes'] if result else 0
            
            cleaned_components.append("Neo4j Graph Database")
            statistics['neo4j_status'] = 'cleaned'
            statistics['neo4j_remaining_nodes'] = remaining_nodes
            
        except Exception as e:
            error_msg = f"Neo4j cleanup failed: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # 3. Clean Local Document Storage
        if include_local_data:
            try:
                logger.info("Cleaning local document storage...")
                from src.config import LOCAL_DOCUMENT_PATH, PDF_DIR
                
                local_files_cleaned = 0
                
                # Clean local document storage
                if LOCAL_DOCUMENT_PATH.exists():
                    for file_path in LOCAL_DOCUMENT_PATH.rglob("*.pdf"):
                        try:
                            file_path.unlink()
                            local_files_cleaned += 1
                        except Exception as e:
                            logger.warning(f"Failed to delete {file_path}: {e}")
                
                # Clean PDF directory
                if PDF_DIR.exists() and PDF_DIR != LOCAL_DOCUMENT_PATH:
                    for file_path in PDF_DIR.rglob("*.pdf"):
                        try:
                            file_path.unlink()
                            local_files_cleaned += 1
                        except Exception as e:
                            logger.warning(f"Failed to delete {file_path}: {e}")
                
                cleaned_components.append("Local Document Storage")
                statistics['local_files_cleaned'] = local_files_cleaned
                
            except Exception as e:
                error_msg = f"Local storage cleanup failed: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # 4. Clean Local Storage Data
        if include_gcp_data:  # Keep parameter name for backward compatibility
            try:
                logger.info("Cleaning local storage data...")
                
                # List all documents before cleanup
                try:
                    documents = storage_manager.list_documents()
                    local_files_before = len(documents)
                    statistics['storage_files_before'] = local_files_before
                    logger.info(f"Found {local_files_before} files in local storage")
                        
                    local_files_cleaned = 0
                    local_errors = []
                    
                    # Delete all documents with progress reporting
                    for document in documents:
                        try:
                            result = storage_manager.delete_document(document.blob_name)
                            if result.status == "success":
                                local_files_cleaned += 1
                                if local_files_cleaned % 50 == 0:  # Progress every 50 files
                                    logger.info(f"Local storage cleanup progress: {local_files_cleaned}/{local_files_before}")
                            else:
                                error_msg = f"Failed to delete {document.original_filename}: {result.message}"
                                logger.error(error_msg)
                                local_errors.append(error_msg)
                        except Exception as e:
                            error_msg = f"Error deleting {document.original_filename}: {str(e)}"
                            logger.error(error_msg)
                            local_errors.append(error_msg)
                    
                    logger.info(f"Local storage cleanup completed: {local_files_cleaned} files deleted")
                    cleaned_components.append("Local Storage Documents")
                    statistics['storage_files_cleaned'] = local_files_cleaned
                    
                    if local_errors:
                        logger.warning(f"Local storage cleanup had {len(local_errors)} errors")
                        errors.extend(local_errors[:3])  # Limit error messages to first 3
                        if len(local_errors) > 3:
                            errors.append(f"... and {len(local_errors) - 3} more storage errors")
                    
                except Exception as list_error:
                    logger.error(f"Failed to list storage documents: {list_error}")
                    errors.append(f"Storage listing failed: {str(list_error)}")
                    statistics['storage_status'] = 'list_failed'
                
            except Exception as e:
                error_msg = f"Local storage cleanup failed: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # 5. Clean Temporary Files
        if include_temp_files:
            try:
                logger.info("Cleaning temporary files...")
                
                temp_files_cleaned = 0
                temp_dirs_cleaned = 0
                temp_dirs = ["temp_uploads", "temp_downloads", "downloads", "temp"]
                
                for temp_dir in temp_dirs:
                    temp_path = PathlibPath(temp_dir)
                    if temp_path.exists():
                        try:
                            # Count files before deletion
                            file_count = len([f for f in temp_path.rglob("*") if f.is_file()])
                            
                            shutil.rmtree(temp_path)
                            temp_files_cleaned += file_count
                            temp_dirs_cleaned += 1
                        except PermissionError as pe:
                            logger.warning(f"Permission error removing {temp_path}: {pe}")
                            # Try to clean individual files
                            files_in_dir = 0
                            for file_path in temp_path.rglob("*"):
                                if file_path.is_file():
                                    try:
                                        file_path.unlink()
                                        files_in_dir += 1
                                    except Exception as fe:
                                        logger.warning(f"Failed to delete {file_path}: {fe}")
                            temp_files_cleaned += files_in_dir
                        except Exception as e:
                            logger.warning(f"Failed to remove {temp_path}: {e}")
                
                # Clean any .tmp files in the current directory and subdirectories
                tmp_files_found = list(PathlibPath(".").rglob("*.tmp"))
                
                tmp_files_deleted = 0
                for tmp_file in tmp_files_found:
                    try:
                        tmp_file.unlink()
                        tmp_files_deleted += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete {tmp_file}: {e}")
                
                temp_files_cleaned += tmp_files_deleted
                
                logger.info(f"Temporary cleanup completed: {temp_dirs_cleaned} directories, {temp_files_cleaned} files")
                cleaned_components.append("Temporary Files")
                statistics['temp_files_cleaned'] = temp_files_cleaned
                statistics['temp_dirs_cleaned'] = temp_dirs_cleaned
                
            except Exception as e:
                error_msg = f"Temporary files cleanup failed: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Prepare response
        success = len(errors) == 0
        
        if success:
            message = f"Database cleanup completed successfully. Cleaned: {', '.join(cleaned_components)}"
        else:
            message = f"Database cleanup completed with {len(errors)} error(s). Cleaned: {', '.join(cleaned_components)}"
        
        logger.info(f"Database cleanup finished. Components cleaned: {len(cleaned_components)}, Errors: {len(errors)}")
        
        return DatabaseCleanupResponse(
            success=success,
            message=message,
            cleaned_components=cleaned_components,
            errors=errors,
            statistics=statistics
        )
        
    except Exception as e:
        logger.error(f"Database cleanup failed with critical error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Critical error during database cleanup: {str(e)}")

# Database Shutdown API for safe cleanup
@app.post("/database/shutdown")
async def shutdown_database_connections():
    """Safely shutdown database connections to prepare for cleanup."""
    try:
        logger.info("Shutting down database connections...")
        
        shutdown_results = {
            'chromadb': False,
            'neo4j': False,
            'message': 'Database connections shutdown initiated'
        }
        
        # Close ChromaDB connections
        try:
            import gc
            from src.graph_db.vector_store import get_vector_store
            
            # Get and close vector store
            vector_store = get_vector_store()
            if hasattr(vector_store, 'client'):
                try:
                    del vector_store.collection
                    del vector_store.client
                    shutdown_results['chromadb'] = True
                    logger.info("ChromaDB connections closed")
                except:
                    pass
            del vector_store
            gc.collect()
            
        except Exception as e:
            logger.warning(f"Error closing ChromaDB connections: {e}")
        
        # Close Neo4j connections  
        try:
            query_processor = QueryProcessor()
            if hasattr(query_processor, 'graph_manager') and hasattr(query_processor.graph_manager, 'driver'):
                query_processor.graph_manager.driver.close()
                shutdown_results['neo4j'] = True
                logger.info("Neo4j connections closed")
        except Exception as e:
            logger.warning(f"Error closing Neo4j connections: {e}")
        
        return shutdown_results
        
    except Exception as e:
        logger.error(f"Database shutdown failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database shutdown failed: {str(e)}")

# Database Statistics API
@app.get("/database/statistics")
async def get_database_statistics():
    """Get current database statistics before cleanup."""
    try:
        statistics = {}
        
        # ChromaDB statistics
        try:
            from src.graph_db.vector_store import get_vector_store
            from src.config import VECTOR_STORE_PATH
            
            vector_store = get_vector_store()
            if hasattr(vector_store, 'collection'):
                try:
                    vector_count = vector_store.collection.count()
                    statistics['chromadb_vectors'] = vector_count
                except:
                    statistics['chromadb_vectors'] = 'unavailable'
            
            # Check ChromaDB directory size
            chroma_path = PathlibPath(VECTOR_STORE_PATH)
            if chroma_path.exists():
                chroma_size = sum(f.stat().st_size for f in chroma_path.rglob('*') if f.is_file())
                statistics['chromadb_size_bytes'] = chroma_size
            else:
                statistics['chromadb_size_bytes'] = 0
                
        except Exception as e:
            statistics['chromadb_error'] = str(e)
        
        # Neo4j statistics
        try:
            from src.graph_db.neo4j_adapter import Neo4jAdapter
            
            neo4j_adapter = Neo4jAdapter()
            
            # Get node counts
            result = neo4j_adapter.graph.run("MATCH (n) RETURN count(n) as node_count").data()
            statistics['neo4j_nodes'] = result[0]['node_count'] if result else 0
            
            # Get relationship counts
            result = neo4j_adapter.graph.run("MATCH ()-[r]->() RETURN count(r) as rel_count").data()
            statistics['neo4j_relationships'] = result[0]['rel_count'] if result else 0
            
            # Get document counts by type
            result = neo4j_adapter.graph.run("MATCH (d:Document) RETURN count(d) as doc_count").data()
            statistics['neo4j_documents'] = result[0]['doc_count'] if result else 0
            
            result = neo4j_adapter.graph.run("MATCH (p:Page) RETURN count(p) as page_count").data()
            statistics['neo4j_pages'] = result[0]['page_count'] if result else 0
            
            result = neo4j_adapter.graph.run("MATCH (c:Chunk) RETURN count(c) as chunk_count").data()
            statistics['neo4j_chunks'] = result[0]['chunk_count'] if result else 0
            
        except Exception as e:
            statistics['neo4j_error'] = str(e)
        
        # Local storage statistics
        try:
            from src.config import LOCAL_DOCUMENT_PATH, PDF_DIR
            
            local_files = 0
            local_size = 0
            
            if LOCAL_DOCUMENT_PATH.exists():
                local_pdfs = list(LOCAL_DOCUMENT_PATH.rglob("*.pdf"))
                local_files += len(local_pdfs)
                local_size += sum(f.stat().st_size for f in local_pdfs)
            
            if PDF_DIR.exists() and PDF_DIR != LOCAL_DOCUMENT_PATH:
                pdf_files = list(PDF_DIR.rglob("*.pdf"))
                local_files += len(pdf_files)
                local_size += sum(f.stat().st_size for f in pdf_files)
            
            statistics['local_files'] = local_files
            statistics['local_size_bytes'] = local_size
            
        except Exception as e:
            statistics['local_storage_error'] = str(e)
        
        # Local storage statistics
        try:
            documents = storage_manager.list_documents()
            statistics['storage_files'] = len(documents)
            statistics['storage_total_size'] = sum(doc.file_size for doc in documents if doc.file_size)
                
        except Exception as e:
            statistics['storage_error'] = str(e)
        
        # Temporary files statistics
        try:
            temp_files = 0
            temp_size = 0
            temp_dirs = ["temp_uploads", "temp_downloads", "downloads", "temp"]
            
            for temp_dir in temp_dirs:
                temp_path = PathlibPath(temp_dir)
                if temp_path.exists():
                    temp_files_list = list(temp_path.rglob("*"))
                    temp_files += len([f for f in temp_files_list if f.is_file()])
                    temp_size += sum(f.stat().st_size for f in temp_files_list if f.is_file())
            
            # Count .tmp files
            tmp_files = list(PathlibPath(".").rglob("*.tmp"))
            temp_files += len(tmp_files)
            temp_size += sum(f.stat().st_size for f in tmp_files)
            
            statistics['temp_files'] = temp_files
            statistics['temp_size_bytes'] = temp_size
            
        except Exception as e:
            statistics['temp_files_error'] = str(e)
        
        return {
            "success": True,
            "statistics": statistics,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get database statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Main entrypoint for running the server directly
if __name__ == "__main__":
    # Get port from environment or use default (8002 to avoid conflicts)
    port = int(os.getenv("COGNIVOX_API_PORT", 8002))
    
    # Run the server with string format for reload to work properly
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=port, reload=True)