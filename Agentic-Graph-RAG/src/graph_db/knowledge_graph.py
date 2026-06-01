from typing import Dict, List, Optional, Any, Tuple
import json
import os
from pathlib import Path
import re
import concurrent.futures
import time

from tqdm import tqdm

from src.config import GRAPH_DB_TYPE, CHUNK_SIZE, CHUNK_OVERLAP, USE_LLAMAINDEX
from src.pdf_processor import PDFProcessor
from src.graph_db.neo4j_adapter import Neo4jAdapter
from src.graph_db.vector_store import get_vector_store, BaseVectorStore


class KnowledgeGraphManager:
    """
    Manager for the knowledge graph.
    """
    
    def __init__(self, 
                 graph_db_type: str = GRAPH_DB_TYPE, 
                 save_pdf: bool = True,
                 vector_store: Optional[BaseVectorStore] = None,
                 chunk_size: Optional[int] = None,
                 chunk_overlap: Optional[int] = None,
                 use_llamaindex: Optional[bool] = None):
        """
        Initialize the knowledge graph manager.
        
        Args:
            graph_db_type: Type of graph database to use.
            save_pdf: Whether to save processed PDFs.
            vector_store: Vector store instance to use. If None, a new one will be created.
            chunk_size: Size of text chunks (uses default if None).
            chunk_overlap: Overlap between consecutive chunks (uses default if None).
            use_llamaindex: Whether to use LlamaIndex for processing. If None, uses config default.
        """
        self.graph_db_type = graph_db_type
        
        # Use default chunk size and overlap if not specified
        self.chunk_size = chunk_size if chunk_size is not None else CHUNK_SIZE
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else CHUNK_OVERLAP
        
        # Determine whether to use LlamaIndex
        self.use_llamaindex = use_llamaindex if use_llamaindex is not None else USE_LLAMAINDEX
        
        # Initialize components
        self.pdf_processor = PDFProcessor(
            save_pdf=save_pdf,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            use_llamaindex=self.use_llamaindex
        )
        
        # Initialize vector store
        self.vector_store = vector_store if vector_store else get_vector_store()
        
        # Initialize graph database adapter
        if graph_db_type.lower() == "neo4j":
            self.graph_db = Neo4jAdapter()
        else:
            # Default to Neo4j if the requested graph DB is not implemented
            print(f"Graph database type '{graph_db_type}' not implemented, using Neo4j instead.")
            self.graph_db = Neo4jAdapter()
    
    def ingest_pdf(self, pdf_path: str, force: bool = False, extraction_method: str = "auto", user_id: Optional[str] = None) -> bool:
        """
        Ingest a PDF document into the knowledge graph.
        
        Args:
            pdf_path: Path to the PDF file.
            force: If True, re-ingest even if document already exists.
            extraction_method: Method for extracting text:
                - "auto": Try PyPDF2 first, then PDFMiner, then OCR if needed
                - "pdfminer": Use PDFMiner for text extraction
                - "pypdf2": Use PyPDF2 for text extraction
                - "ocr": Use EasyOCR for image-based text extraction
            user_id: Optional user ID to associate with this document.
                     If provided, the document will be isolated to this user.
                     If not provided, the document will be available to all users (global).
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Ensure user_id is None if empty string
            user_id = user_id if user_id and user_id.strip() else None
            
            # Check if file exists
            if not os.path.exists(pdf_path):
                print(f"PDF file not found: {pdf_path}")
                return False
                
            # Process the PDF with user_id
            print(f"Processing PDF: {pdf_path}")
            processed_pdf = self.pdf_processor.process_pdf(pdf_path, extraction_method=extraction_method, user_id=user_id)
            
            # Check if processing was successful (look for error in metadata)
            if "error" in processed_pdf.get("metadata", {}):
                error_msg = processed_pdf["metadata"]["error"]
                print(f"Error processing PDF: {error_msg}")
                return False
                
            # Check if any chunks were generated
            if not processed_pdf.get("chunks", []):
                print(f"No text chunks were generated from {pdf_path}. Nothing to ingest.")
                return False
            
            # Store user_id in metadata if provided (may already be set by processor, but ensure it's there)
            if user_id:
                processed_pdf["metadata"]["user_id"] = user_id
                print(f"Document will be associated with user: {user_id}")
            else:
                # Explicitly mark as global document
                processed_pdf["metadata"]["user_type"] = "global"
                print("Document will be globally accessible (no user_id)")
            
            # Check if document already exists in the vector store
            file_hash = processed_pdf["metadata"]["file_hash"]
            file_path = processed_pdf["metadata"]["file_path"]
            file_size = os.path.getsize(pdf_path)
            file_mod_time = os.path.getmtime(pdf_path)
            
            # Check if document exists in the graph database
            existing_document = False
            if isinstance(self.graph_db, Neo4jAdapter):
                query_params = {"file_hash": file_hash}
                if user_id:
                    query_params["user_id"] = user_id
                    
                existing_doc_node = self.graph_db.find_document_by_hash(file_hash, user_id)
                if existing_doc_node:
                    existing_document = True
                    
                    # Check if the document needs to be updated
                    update_needed = force
                    
                    if not update_needed:
                        # Get the modification time and file size from the existing document if available
                        existing_file_size = existing_doc_node.get("file_size")
                        existing_mod_time = existing_doc_node.get("last_modified")
                        
                        # Check if file size or modification time has changed
                        if existing_file_size is not None and existing_mod_time is not None:
                            if file_size != existing_file_size or abs(file_mod_time - existing_mod_time) > 1:  # Allow 1 second difference
                                update_needed = True
                                print(f"Document has been modified since last ingestion. Will update.")
                        else:
                            # If we don't have size/modification time metadata, assume update needed
                            update_needed = True
                            print(f"Document metadata incomplete. Will update to ensure latest version.")
                    
                    if not update_needed:
                        print(f"Document already exists and appears unchanged. Use --force to re-ingest.")
                        print(f"Skipping ingestion for: {pdf_path}")
                        return True  # Return True as this is not an error condition
                    else:
                        print(f"Document exists but needs updating. Removing old version...")
                        # Delete existing document from vector store and graph
                        self.remove_existing_document(file_hash, user_id)
            
            # Add metadata to chunks for vector store
            for chunk in processed_pdf["chunks"]:
                if "metadata" not in chunk:
                    chunk["metadata"] = {}
                
                # Make sure chunk metadata includes all necessary document metadata
                for key in ["file_hash", "title"]:
                    if key in processed_pdf["metadata"] and key not in chunk["metadata"]:
                        chunk["metadata"][key] = processed_pdf["metadata"][key]
                
                # Use stored path for document_path if available, otherwise use original file_path
                if "stored_path" in processed_pdf["metadata"]:
                    chunk["metadata"]["document_path"] = processed_pdf["metadata"]["stored_path"]
                elif "physical_path" in processed_pdf["metadata"]:
                    chunk["metadata"]["document_path"] = processed_pdf["metadata"]["physical_path"]
                elif "file_path" in processed_pdf["metadata"]:
                    chunk["metadata"]["document_path"] = processed_pdf["metadata"]["file_path"]
                
                # Keep original file_path for backward compatibility if not already set
                if "file_path" not in chunk["metadata"] and "file_path" in processed_pdf["metadata"]:
                    chunk["metadata"]["file_path"] = processed_pdf["metadata"]["file_path"]
                
                # Add user_id or user_type to chunk metadata - ensure exactly one is set
                if user_id:
                    chunk["metadata"]["user_id"] = user_id
                    # Remove user_type if it exists to prevent conflicts
                    if "user_type" in chunk["metadata"]:
                        del chunk["metadata"]["user_type"]
                else:
                    chunk["metadata"]["user_type"] = "global"
                    # Remove user_id if it exists to prevent conflicts
                    if "user_id" in chunk["metadata"]:
                        del chunk["metadata"]["user_id"]
            
            # Document doesn't exist or needs updating
            # Store document chunks in the vector store
            print("Storing document chunks in vector store...")
            vector_store_ids = self.vector_store.add_documents(processed_pdf["chunks"])
            
            # Add file size and modification time to metadata for future comparison
            processed_pdf["metadata"]["file_size"] = file_size
            processed_pdf["metadata"]["last_modified"] = file_mod_time
            
            # Store document in the graph database
            print("Storing document in graph database...")
            success = False
            try:
                result = self.graph_db.store_document_knowledge_graph(processed_pdf, vector_store_ids)
                
                # Check if the result is a dictionary with status information
                if isinstance(result, dict) and result.get("status") == "already_exists":
                    # Handle case where document already exists in the database
                    print(f"Document with hash {result['file_hash']} already exists in the graph")
                    if existing_document:  # This was already checked, so we're actually updating
                        print("Document should have been removed earlier. Attempting to clean up and retry...")
                        self.remove_existing_document(file_hash, user_id)
                        success = self.graph_db.store_document_knowledge_graph(processed_pdf, vector_store_ids)
                        if not isinstance(success, bool) or not success:
                            print("Failed to store document even after cleanup. May require manual intervention.")
                            return False
                    else:
                        # This should not typically happen because we check for existence earlier
                        print("Unexpected existing document found. May require manual cleanup.")
                        return False
                else:
                    # Normal case - result is True or False
                    success = result
            except Exception as e:
                print(f"Error storing document in knowledge graph: {e}")
                # If we got a constraint error, try cleaning up and retrying
                if "already exists with label" in str(e) and "Chunk" in str(e):
                    print("Attempting to clean up and retry...")
                    # Try to delete any partially created document
                    try:
                        self.graph_db.delete_document(file_hash, user_id)
                        print("Cleaned up partial document. Retrying storage operation...")
                        success = self.graph_db.store_document_knowledge_graph(processed_pdf, vector_store_ids)
                        if isinstance(success, dict):
                            # Convert the dictionary result to a boolean
                            success = False  # If we get a dict back again, something is wrong
                    except Exception as retry_error:
                        print(f"Error during retry: {retry_error}")
            
            if success:
                operation = "updated" if existing_document else "ingested"
                print(f"Successfully {operation} PDF: {pdf_path}")
            else:
                print(f"Failed to ingest PDF into graph database: {pdf_path}")
                
            return success
            
        except Exception as e:
            print(f"Error ingesting PDF: {e}")
            return False
    
    def remove_existing_document(self, file_hash: str, user_id: Optional[str] = None) -> bool:
        """
        Remove an existing document from both vector store and graph database.
        
        Args:
            file_hash: Hash of the document to remove.
            user_id: Optional user ID associated with the document.
                     If provided, only document for this specific user will be removed.
                     If not provided, the global document will be removed.
            
        Returns:
            True if successful, False if any step failed.
        """
        success = True
        
        # Delete from vector store - must succeed
        vector_store_success = False
        try:
            # ChromaDB where clause requires $and operator for multiple conditions
            if user_id:
                # Query for documents with the specific user_id using $and operator
                where_clause = {
                    "$and": [
                        {"file_hash": file_hash},
                        {"user_id": user_id}
                    ]
                }
                print(f"Removing vector store document with hash {file_hash} for user {user_id}")
            else:
                # First try without user_id filter to get all chunks with this hash
                where_clause = {"file_hash": file_hash}
                print(f"Removing all vector store documents with hash {file_hash}")
            
            # Get all chunks with the specified criteria
            # Note: ChromaDB always returns ids automatically, don't include it in include parameter
            result = self.vector_store.collection.get(
                where=where_clause,
                include=["metadatas"]
            )
            
            # If we're looking for global documents, filter out user-specific ones
            if not user_id and result["ids"]:
                # Filter to only include documents without user_id
                filtered_ids = []
                for i, metadata in enumerate(result["metadatas"]):
                    if "user_id" not in metadata or metadata["user_id"] is None or metadata["user_id"] == "":
                        filtered_ids.append(result["ids"][i])
                
                if filtered_ids:
                    print(f"Found {len(filtered_ids)} global documents to remove")
                    self.vector_store.collection.delete(ids=filtered_ids)
                    vector_store_success = True
                elif len(result["ids"]) == 0:
                    # No documents found - consider this success (nothing to delete)
                    print("No vector store documents found to remove")
                    vector_store_success = True
            elif result["ids"]:
                # Delete all matched documents
                self.vector_store.collection.delete(ids=result["ids"])
                print(f"Removed {len(result['ids'])} documents from vector store")
                vector_store_success = True
            else:
                # No documents found - consider this success (nothing to delete)
                print("No vector store documents found to remove")
                vector_store_success = True
                
        except Exception as e:
            print(f"Error removing document from vector store: {e}")
            import traceback
            traceback.print_exc()
            vector_store_success = False
        
        # Delete from graph database - must succeed
        db_success = False
        try:
            if isinstance(self.graph_db, Neo4jAdapter):
                # Use the improved delete_document method
                db_success = self.graph_db.delete_document(file_hash, user_id)
                if db_success:
                    if user_id:
                        print(f"Existing document for user {user_id} removed from graph database.")
                    else:
                        print("Existing document removed from graph database.")
                else:
                    if user_id:
                        print(f"Error: Could not find or remove document for user {user_id} from graph database.")
                    else:
                        print("Error: Could not find or remove document from graph database.")
        except Exception as e:
            print(f"Error removing document from graph database: {e}")
            import traceback
            traceback.print_exc()
            db_success = False
        
        # Both deletions must succeed for the operation to be considered successful
        if vector_store_success and db_success:
            print("Document successfully removed from both vector store and graph database.")
            return True
        else:
            if not vector_store_success:
                print("Failed to remove document from vector store.")
            if not db_success:
                print("Failed to remove document from graph database.")
            print("Document deletion failed - partial deletion may have occurred.")
            return False
    
    def update_document_enabled_status(self, file_hash: str, enabled: bool, user_id: Optional[str] = None) -> bool:
        """
        Update the enabled status of a document.
        
        Args:
            file_hash: Hash of the document to update.
            enabled: True to enable, False to disable.
            user_id: Optional user ID. If provided, only update document for this specific user.
            
        Returns:
            True if document was updated, False otherwise.
        """
        try:
            if isinstance(self.graph_db, Neo4jAdapter):
                return self.graph_db.update_document_enabled_status(file_hash, enabled, user_id)
            else:
                print("Warning: update_document_enabled_status only supported for Neo4j")
                return False
        except Exception as e:
            print(f"Error updating document enabled status: {e}")
            return False
    
    def semantic_search(self, query: str, n_results: int = 20, user_id: Optional[str] = None) -> List[Dict]:
        """
        Perform a semantic search in the vector store with enhanced preprocessing and result ranking.
        
        Args:
            query: Query text.
            n_results: Number of results to return.
            user_id: Optional user ID for user-specific queries.
                     If provided, results will include both global documents
                     and documents specific to this user.
                     If not provided, only global documents will be queried.
            
        Returns:
            List of search results.
        """
        # Ensure user_id is None if empty string
        user_id = user_id if user_id and user_id.strip() else None
        
        # Preprocess the query to improve search quality
        preprocessed_query = self._preprocess_query(query)
        print(f"Original query: '{query}'")
        print(f"Preprocessed query: '{preprocessed_query}'")
        
        # Generate embedding for the query
        try:
            # Choose the appropriate embeddings generator based on PDFProcessor mode
            embedding = None
            
            if self.pdf_processor.use_llamaindex:
                # LlamaIndex mode - use the llamaindex_processor's embeddings_generator
                if hasattr(self.pdf_processor, 'llamaindex_processor') and \
                   hasattr(self.pdf_processor.llamaindex_processor, 'embeddings_generator'):
                    embedding = self.pdf_processor.llamaindex_processor.embeddings_generator.generate_embedding(preprocessed_query)
                else:
                    print("Warning: LlamaIndex embeddings generator not available, falling back to legacy mode")
                    # Fallback to legacy embeddings if available
                    if hasattr(self.pdf_processor, 'embeddings_generator'):
                        embedding = self.pdf_processor.embeddings_generator.generate_embedding(preprocessed_query)
            else:
                # Legacy mode - use the direct embeddings_generator
                if hasattr(self.pdf_processor, 'embeddings_generator'):
                    embedding = self.pdf_processor.embeddings_generator.generate_embedding(preprocessed_query)
                else:
                    print("Error: No embeddings generator available in legacy mode")
            
            # Check if embedding generation was successful
            if not embedding:
                print("Error: Failed to generate embedding for query")
                return []
            
            # Request more results than needed to allow for filtering and reranking
            search_multiplier = 3
            expanded_n_results = n_results * search_multiplier
            
            # Parallel search for user-specific and global documents
            all_results = []
            
            def search_user_docs():
                """Search user-specific documents"""
                if user_id:
                    where_clause = {"user_id": user_id}
                    print(f"Searching for user-specific documents. User ID: {user_id}")
                    start_time = time.time()
                    results = self.vector_store.search(preprocessed_query, embedding, expanded_n_results, where_clause)
                    print(f"User-specific search completed in {time.time() - start_time:.2f}s with {len(results)} results")
                    return results
                return []
            
            def search_global_docs():
                """Search global documents"""
                start_time = time.time()
                print("Searching for global documents only")
                global_where_clause = {"user_type": "global"}
                results = self.vector_store.search(preprocessed_query, embedding, expanded_n_results, global_where_clause)
                print(f"Global search completed in {time.time() - start_time:.2f}s with {len(results)} results")
                return results
            
            def search_legacy_docs():
                """Search legacy documents (backward compatibility)"""
                start_time = time.time()
                compat_results = self.vector_store.search(preprocessed_query, embedding, expanded_n_results, None)
                
                # Apply strict filtering for compatibility results - only include truly legacy docs
                filtered_compat = []
                for result in compat_results:
                    metadata = result.get("metadata", {})
                    # Only include if it has NEITHER user_id NOR user_type - true legacy docs
                    if "user_id" not in metadata and "user_type" not in metadata:
                        filtered_compat.append(result)
                
                print(f"Legacy search completed in {time.time() - start_time:.2f}s with {len(filtered_compat)} results")
                return filtered_compat
            
            # Execute all searches in parallel for better performance
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                user_future = executor.submit(search_user_docs)
                global_future = executor.submit(search_global_docs) 
                legacy_future = executor.submit(search_legacy_docs)
                
                # Collect all results
                user_results = user_future.result(timeout=30)
                global_results = global_future.result(timeout=30)
                legacy_results = legacy_future.result(timeout=30)
                
                all_results.extend(user_results)
                all_results.extend(global_results)
                all_results.extend(legacy_results)
            
            # Apply strict post-processing filter to ensure proper isolation
            filtered_results = []
            for result in all_results:
                include_result = False
                metadata = result.get("metadata", {})
                
                if user_id:
                    # When user_id is provided, only include:
                    # 1. Documents with matching user_id
                    # 2. Documents marked as global
                    # 3. Legacy documents with no user attribution
                    if "user_id" in metadata and metadata["user_id"] == user_id:
                        include_result = True
                    elif metadata.get("user_type") == "global":
                        include_result = True
                    elif "user_id" not in metadata and "user_type" not in metadata:
                        include_result = True
                else:
                    # When no user_id is provided, only include global results:
                    # 1. Marked as global (user_type=global)
                    # 2. Have no user_id or user_type (backward compatibility)
                    if metadata.get("user_type") == "global":
                        include_result = True
                    elif "user_id" not in metadata and "user_type" not in metadata:
                        include_result = True
                    # NEVER include documents with a specific user_id when no user_id provided
                    elif "user_id" in metadata:
                        include_result = False
                
                if include_result:
                    filtered_results.append(result)
            
            # Filter out disabled documents by checking Neo4j
            if isinstance(self.graph_db, Neo4jAdapter):
                enabled_filtered_results = []
                for result in filtered_results:
                    metadata = result.get("metadata", {})
                    file_hash = metadata.get("file_hash")
                    if file_hash:
                        # Check if document is enabled in Neo4j
                        doc_node = self.graph_db.find_document_by_hash(file_hash, user_id)
                        if doc_node:
                            # Check enabled status (default to True if not set for backward compatibility)
                            enabled = doc_node.get("enabled", True)
                            if enabled:
                                enabled_filtered_results.append(result)
                        else:
                            # If document not found in Neo4j, exclude it
                            # Documents must exist in Neo4j to be queryable
                            # This ensures disabled documents (created as minimal nodes) are excluded
                            pass  # Don't include documents not in Neo4j
                    else:
                        # If no file_hash, include it (shouldn't happen but be safe)
                        enabled_filtered_results.append(result)
                filtered_results = enabled_filtered_results
            
            # Remove duplicates by ID
            unique_results = {}
            for result in filtered_results:
                result_id = result["id"]
                if result_id not in unique_results:
                    unique_results[result_id] = result
            
            filtered_results = list(unique_results.values())
            
            # Enhanced ranking: Score results based on multiple factors
            ranked_results = self._rerank_semantic_results(filtered_results, query, preprocessed_query)
            
            # Format results
            formatted_results = []
            for result in ranked_results[:n_results]:
                formatted_result = {
                    "text": result["text"],
                    "metadata": result["metadata"],
                    "distance": result["distance"],  # Lower distances are better
                    "match_type": "semantic",  # Explicitly mark match type
                    "relevance_score": result.get("relevance_score", 1.0 - result["distance"])  # Include the enhanced score
                }
                
                # Include user_id field in results if it exists in metadata
                metadata = result.get("metadata", {})
                if user_id and "user_id" in metadata and metadata["user_id"] == user_id:
                    formatted_result["user_source"] = metadata["user_id"]
                elif "user_type" in metadata and metadata["user_type"] == "global":
                    formatted_result["user_source"] = "global"
                elif "user_id" not in metadata and "user_type" not in metadata:
                    formatted_result["user_source"] = "legacy"
                
                formatted_results.append(formatted_result)
            
            # Log filtered result counts
            print(f"Original results: {len(all_results)}, Filtered results: {len(filtered_results)}, Returned results: {len(formatted_results)}")
            
            return formatted_results
        except Exception as e:
            print(f"Error in semantic search: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess the query to improve search quality.
        
        Args:
            query: Original query string
            
        Returns:
            Preprocessed query string
        """
        if not query:
            return ""
        
        # Truncate overly long queries to prevent embedding issues
        max_query_length = 300
        if len(query) > max_query_length:
            print(f"Query too long ({len(query)} chars), truncating to {max_query_length} chars")
            query = query[:max_query_length] + "..."
            
        # Remove multiple spaces and trim
        query = " ".join(query.split()).strip()
        
        # Convert to lowercase for more consistent matching
        query = query.lower()
        
        # Escape special characters in the query to prevent regex issues
        special_chars = r'[\\^$.|?*+(){}[\]]'
        if re.search(special_chars, query):
            cleaned_query = re.sub(special_chars, lambda m: '\\' + m.group(0), query)
            print(f"Escaped special characters in query: {cleaned_query}")
            query = cleaned_query
        
        # Remove common question words and filler phrases that might skew the embeddings
        question_starters = [
            "what is", "what are", "what should", "what would", "what could", 
            "how to", "how do", "how does", "how can", "how should",
            "can you tell me", "tell me about", "explain", "i want to know", 
            "could you explain", "please tell me"
        ]
        
        cleaned_query = query
        for starter in question_starters:
            if cleaned_query.startswith(starter):
                cleaned_query = cleaned_query[len(starter):].strip()
                break
                
        # Don't return an empty query if we removed everything
        if not cleaned_query:
            return query
            
        return cleaned_query
        
    def _rerank_semantic_results(self, results: List[Dict], original_query: str, preprocessed_query: str) -> List[Dict]:
        """
        Rerank semantic search results based on multiple factors.
        
        Args:
            results: List of search results
            original_query: Original user query
            preprocessed_query: Preprocessed query used for the search
            
        Returns:
            Reranked results list
        """
        if not results:
            return []
            
        # Extract key terms from the query (excluding stopwords)
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
                     'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for', 'with', 
                     'by', 'about', 'like', 'through', 'over', 'before', 'after',
                     'between', 'under', 'above', 'of', 'during', 'since', 'what', 
                     'who', 'where', 'when', 'how', 'why', 'which', 'whom', 'whose'}
                     
        query_terms = [term.lower() for term in original_query.split() if term.lower() not in stop_words and len(term) > 2]
        
        # Weight for exact term matches
        term_match_weight = 0.2
        # Weight for semantic similarity (vector distance)
        semantic_weight = 0.8
        
        for result in results:
            # Start with base score from vector similarity
            base_score = 1.0 - result["distance"]
            
            # Calculate term match boost
            text = result["text"].lower()
            term_matches = sum(1 for term in query_terms if term in text)
            term_match_ratio = term_matches / len(query_terms) if query_terms else 0
            
            # Calculate content length penalty (prefer shorter, more focused content)
            length = len(text.split())
            length_factor = min(1.0, 150 / max(length, 50))  # Normalize with diminishing returns
            
            # Calculate final score
            result["relevance_score"] = (base_score * semantic_weight) + (term_match_ratio * term_match_weight) + (length_factor * 0.1)
            
            # Add small boost for results containing exact phrases from the query (2+ word phrases)
            if len(query_terms) >= 2:
                for i in range(len(query_terms) - 1):
                    phrase = f"{query_terms[i]} {query_terms[i+1]}"
                    if phrase in text:
                        result["relevance_score"] += 0.1
                        break
        
        # Sort by the new relevance score (higher is better)
        return sorted(results, key=lambda x: x.get("relevance_score", 0.0), reverse=True)
    
    def _escape_regex_special_chars(self, keyword: str) -> str:
        """
        Escape special regex characters in a keyword to ensure safe use in regex patterns.
        
        Args:
            keyword: The keyword string to escape
            
        Returns:
            String with regex special characters escaped
        """
        # Characters that need to be escaped in regex patterns
        special_chars = r'\.^$*+?()[]{}|'
        
        # Escape each special character
        escaped_keyword = ''
        for char in keyword:
            if char in special_chars:
                escaped_keyword += '\\' + char
            else:
                escaped_keyword += char
                
        return escaped_keyword
    
    def keyword_search(self, keyword: str, n_results: int = 20, user_id: Optional[str] = None) -> List[Dict]:
        """
        Perform a keyword-based search in the graph database.
        
        Args:
            keyword: Keyword to search for.
            n_results: Number of results to return.
            user_id: Optional user ID for user-specific queries.
                     If provided, results will include both global documents
                     and documents specific to this user.
                     If not provided, only global documents will be queried.
            
        Returns:
            List of search results.
        """
        # Ensure user_id is None if empty string
        user_id = user_id if user_id and user_id.strip() else None
        
        # Clean and validate input
        if not keyword or not isinstance(keyword, str):
            return []
            
        keyword = keyword.strip()
        if not keyword:
            return []
            
        # Depending on the database type, use different search approaches
        if isinstance(self.graph_db, Neo4jAdapter):
            try:
                # Escape any regex special characters in the keyword
                escaped_keyword = self._escape_regex_special_chars(keyword)
                
                # Set up query parameters
                query_params = {
                    "keyword": f"(?i).*{escaped_keyword}.*",  # Case-insensitive regex pattern
                    "limit": n_results * 3  # Request more results to account for filtering
                }
                
                all_results = []
                
                def search_user_keyword():
                    """Search user-specific documents for keyword"""
                    if user_id:
                        start_time = time.time()
                        print(f"Searching for keyword in user-specific documents (user_id: {user_id})")
                        user_query = """
                        MATCH (c:Chunk)
                        WHERE c.user_id = $user_id AND c.text =~ $keyword
                        RETURN c.unique_chunk_id AS chunk_id, c.text AS text, c.vector_id AS vector_id, 
                               c.user_id AS user_id, c.page_number AS page_number, 
                               null AS distance, 'keyword' AS source, 'keyword' AS match_type
                        ORDER BY c.page_number
                        LIMIT $limit
                        """
                        user_query_params = query_params.copy()
                        user_query_params["user_id"] = user_id
                        
                        results = self.graph_db.graph.run(user_query, **user_query_params).data()
                        print(f"User keyword search completed in {time.time() - start_time:.2f}s with {len(results)} results")
                        return results
                    return []
                
                def search_global_keyword():
                    """Search global documents for keyword"""
                    start_time = time.time()
                    print("Searching for keyword in global documents")
                    global_query = """
                    MATCH (c:Chunk)
                    WHERE c.user_type = 'global' AND c.text =~ $keyword
                    RETURN c.unique_chunk_id AS chunk_id, c.text AS text, c.vector_id AS vector_id, 
                           'global' AS user_id, c.page_number AS page_number, 
                           null AS distance, 'keyword' AS source, 'keyword' AS match_type
                    ORDER BY c.page_number
                    LIMIT $limit
                    """
                    results = self.graph_db.graph.run(global_query, **query_params).data()
                    print(f"Global keyword search completed in {time.time() - start_time:.2f}s with {len(results)} results")
                    return results
                
                def search_legacy_keyword():
                    """Search legacy documents for keyword"""
                    start_time = time.time()
                    compat_query = """
                    MATCH (c:Chunk)
                    WHERE c.user_id IS NULL AND c.user_type IS NULL AND c.text =~ $keyword
                    RETURN c.unique_chunk_id AS chunk_id, c.text AS text, c.vector_id AS vector_id, 
                           'legacy' AS user_id, c.page_number AS page_number, 
                           null AS distance, 'keyword' AS source, 'keyword' AS match_type
                    ORDER BY c.page_number
                    LIMIT $limit
                    """
                    try:
                        results = self.graph_db.graph.run(compat_query, **query_params).data()
                        print(f"Legacy keyword search completed in {time.time() - start_time:.2f}s with {len(results)} results")
                        return results
                    except Exception as e:
                        print(f"Error in compatibility query: {e}")
                        return []
                
                # Execute keyword searches in parallel with optimized timeouts
                print(f"🔍 Starting optimized keyword search for '{keyword}' (user_id: {user_id})")
                search_start = time.time()
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    user_future = executor.submit(search_user_keyword)
                    global_future = executor.submit(search_global_keyword)
                    legacy_future = executor.submit(search_legacy_keyword)
                    
                    # Collect results with reduced timeouts and early termination
                    try:
                        user_results = user_future.result(timeout=3)  # Further reduced from 8s to 3s
                        # Early termination if user has enough results
                        if user_id and len(user_results) >= n_results:
                            print(f"⚡ Early termination: found {len(user_results)} user results")
                            all_results.extend(user_results[:n_results])
                            # Cancel remaining futures
                            global_future.cancel()
                            legacy_future.cancel()
                        else:
                            all_results.extend(user_results)
                            
                            global_results = global_future.result(timeout=3)  # Reduced to 3s
                            all_results.extend(global_results)
                            
                            # Only search legacy if still need more results
                            if len(all_results) < n_results:
                                legacy_results = legacy_future.result(timeout=3)  # Reduced to 3s
                                all_results.extend(legacy_results)
                            else:
                                legacy_future.cancel()
                                
                    except concurrent.futures.TimeoutError:
                        print(f"⏰ Keyword search timeout for '{keyword}'")
                        # Collect any available results
                        if user_future.done():
                            all_results.extend(user_future.result())
                        if global_future.done():
                            all_results.extend(global_future.result())
                        if legacy_future.done():
                            all_results.extend(legacy_future.result())
                
                search_duration = time.time() - search_start
                print(f"🎯 Keyword search '{keyword}' completed in {search_duration:.2f}s with {len(all_results)} results")
                
                # Apply strict post-processing filter to ensure proper isolation
                filtered_results = []
                for result in all_results:
                    include_result = False
                    result_user_id = result.get("user_id")
                    
                    if user_id:
                        # Include if user_id matches, or is global/legacy
                        if result_user_id == user_id or result_user_id == "global" or result_user_id == "legacy":
                            include_result = True
                        # Never include other users' documents
                        else:
                            include_result = False
                    else:
                        # Only include global or legacy results when no user_id provided
                        if result_user_id == "global" or result_user_id == "legacy":
                            include_result = True
                        # Never include user-specific documents when no user_id is provided
                        else:
                            include_result = False
                    
                    if include_result:
                        filtered_results.append(result)
                
                # Filter out disabled documents by checking Neo4j
                if isinstance(self.graph_db, Neo4jAdapter):
                    enabled_filtered_results = []
                    for result in filtered_results:
                        # Get file_hash from chunk by querying Neo4j
                        chunk_id = result.get("chunk_id")
                        if chunk_id:
                            try:
                                # Query to get document hash from chunk
                                doc_query = """
                                MATCH (d:Document)-[:CONTAINS]->(p:Page)-[:CONTAINS]->(c:Chunk {unique_chunk_id: $chunk_id})
                                RETURN d.file_hash AS file_hash
                                LIMIT 1
                                """
                                doc_result = self.graph_db.graph.run(doc_query, chunk_id=chunk_id).data()
                                if doc_result:
                                    file_hash = doc_result[0].get("file_hash")
                                    if file_hash:
                                        # Check if document is enabled
                                        doc_node = self.graph_db.find_document_by_hash(file_hash, user_id)
                                        if doc_node:
                                            enabled = doc_node.get("enabled", True)
                                            if enabled:
                                                enabled_filtered_results.append(result)
                                        else:
                                            # If document not found in Neo4j, exclude it
                                            # Documents must exist in Neo4j to be queryable
                                            pass  # Don't include documents not in Neo4j
                                    else:
                                        enabled_filtered_results.append(result)
                                else:
                                    # If can't find document, exclude it
                                    # Documents must exist in Neo4j to be queryable
                                    pass  # Don't include documents not in Neo4j
                            except Exception as e:
                                # If error checking, exclude it to be safe
                                print(f"Error checking enabled status for chunk {chunk_id}: {e}")
                                pass  # Don't include documents with errors
                        else:
                            # If no chunk_id, include it
                            enabled_filtered_results.append(result)
                    filtered_results = enabled_filtered_results
                
                # Remove duplicates based on chunk_id
                unique_results = {}
                for result in filtered_results:
                    chunk_id = result["chunk_id"]
                    if chunk_id not in unique_results:
                        unique_results[chunk_id] = result
                
                print(f"Keyword search original results: {len(all_results)}, Unique results: {len(unique_results)}")
                
                # Sort results
                sorted_results = sorted(unique_results.values(), key=lambda x: x["page_number"])
                
                # Format results for return
                formatted_results = []
                for result in sorted_results[:n_results]:
                    formatted_result = {
                        "text": result["text"],
                        "metadata": {
                            "chunk_id": result["chunk_id"],
                            "page_number": result["page_number"]
                        },
                        "source": result["source"],
                        "match_type": result["match_type"]
                    }
                    
                    # Add user source info
                    if result["user_id"] == "global":
                        formatted_result["user_source"] = "global"
                    elif result["user_id"] == "legacy":
                        formatted_result["user_source"] = "legacy"
                    elif user_id and result["user_id"] == user_id:
                        formatted_result["user_source"] = result["user_id"]
                    
                    formatted_results.append(formatted_result)
                
                print(f"Keyword search returning {len(formatted_results)} results")
                return formatted_results
                
            except Exception as e:
                print(f"Error in keyword search: {e}")
                import traceback
                traceback.print_exc()
                return []
        else:
            print("Unsupported graph database type for keyword search")
            return []
    
    def hybrid_search(self, query: str, n_results: int = 20, user_id: Optional[str] = None) -> List[Dict]:
        """
        Perform a hybrid search that combines semantic and keyword searching.
        
        Args:
            query: Query text.
            n_results: Number of results to return.
            user_id: Optional user ID for user-specific queries.
            
        Returns:
            List of search results.
        """
        # Ensure user_id is None if empty string
        user_id = user_id if user_id and user_id.strip() else None
        
        print(f"Performing search with mode: hybrid")
        print(f"Hybrid search with semantic weight: 0.6, keyword weight: 0.4")
        
        # Analyze the query to extract important terms
        important_terms = self._extract_important_terms(query)
        print(f"Important terms detected: {important_terms}")
        
        try:
            # Try semantic search first
            print("Performing semantic search as part of hybrid search")
            print(f"Original query: '{query}'")
            
            # Set semantic multiplier - how many more results to get from semantic vs keyword
            semantic_multiplier = 2
            
            try:
                # Try semantic search with timeout protection
                semantic_results = self.semantic_search(query, n_results * semantic_multiplier, user_id)
            except Exception as e:
                print(f"Semantic search failed, falling back to keyword search: {str(e)}")
                semantic_results = []  # Fallback to empty results if semantic search fails
                semantic_multiplier = 0  # Don't include semantic results in the mix
            
            # Extract keywords for keyword search - use both automatic extraction and query analysis
            # Define stop words for filtering
            stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
                         'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for', 'with', 
                         'by', 'about', 'like', 'through', 'over', 'before', 'after',
                         'between', 'under', 'above', 'of', 'during', 'since', 'what', 
                         'who', 'where', 'when', 'how', 'why', 'which', 'whom', 'whose'}
            
            # Extract keywords that are at least 3 characters and not stop words
            potential_keywords = [word.lower() for word in query.split() 
                              if len(word) > 2 and word.lower() not in stop_words]
            
            # Combine with important terms from query analysis and remove duplicates
            all_keywords = list(set(potential_keywords + important_terms))
            
            # Prioritize longer keywords and important terms
            keywords = sorted(all_keywords, key=lambda k: (k in important_terms, len(k)), reverse=True)
            
            # Get keyword search results for top keywords
            print("Performing keyword search as part of hybrid search")
            keyword_results = []
            
            # Use more keywords if we have important terms from analysis
            max_keywords = 5 if important_terms else 3
            
            for keyword in keywords[:max_keywords]:
                print(f"Searching for keyword: {keyword}")
                # Escape any special regex characters to prevent search errors
                results = self.keyword_search(keyword, n_results, user_id)
                
                # Add source keyword info to facilitate later reranking
                for result in results:
                    if "source_keywords" not in result:
                        result["source_keywords"] = []
                    result["source_keywords"].append(keyword)
                    
                keyword_results.extend(results)
            
            # No keywords found - use the whole query as fallback
            if not keywords and query.strip():
                # Use the first 3 words of the query if it's long
                fallback_keyword = ' '.join(query.split()[:3])
                print(f"No keywords extracted. Using fallback: {fallback_keyword}")
                results = self.keyword_search(fallback_keyword, n_results, user_id)
                
                # Add source keyword info
                for result in results:
                    if "source_keywords" not in result:
                        result["source_keywords"] = []
                    result["source_keywords"].append(fallback_keyword)
                    
                keyword_results.extend(results)
            
            # Combine results with appropriate weights
            all_results = []
            
            # Add semantic results
            for result in semantic_results:
                result["match_type"] = "semantic"
                result["hybrid_search_score"] = (1.0 - result.get("distance", 0.5)) * 0.6
                
                # Add relevance score if not already present
                if "relevance_score" not in result:
                    result["relevance_score"] = 1.0 - result.get("distance", 0.5)
                    
                all_results.append(result)
            
            # Add keyword results
            for result in keyword_results:
                # Ensure it has a match_type field
                if "match_type" not in result:
                    result["match_type"] = "keyword"
                    
                # Calculate a normalized score for keyword results
                base_score = result.get("score", 0.5) / 10.0
                
                # Apply a boost for results matching important terms
                term_boost = 0.0
                if "source_keywords" in result:
                    for keyword in result["source_keywords"]:
                        if keyword in important_terms:
                            term_boost += 0.15
                
                # Cap the total boost to avoid overweighting
                term_boost = min(term_boost, 0.3)
                
                # Set the hybrid search score
                result["hybrid_search_score"] = (base_score + term_boost) * 0.4
                
                # Add a proper relevance score for consistency
                if "relevance_score" not in result:
                    result["relevance_score"] = base_score + term_boost
                    
                all_results.append(result)
            
            # Enhanced deduplication: Use a scoring mechanism to choose between duplicates
            unique_results = {}
            for result in all_results:
                # Create a unique key based on content
                text = result.get("text", "")
                metadata = result.get("metadata", {})
                
                # For chunk_id, try different possible fields
                chunk_id = None
                if isinstance(metadata, dict):
                    chunk_id = metadata.get("chunk_id") or metadata.get("id") or metadata.get("unique_chunk_id")
                
                # If we have a valid chunk ID, use it
                if chunk_id:
                    key = chunk_id
                else:
                    # Fallback to using text hash as key
                    key = hash(text[:200])  # Using hash of first 200 chars is more efficient
                
                # More sophisticated duplicate handling: Choose the result with the better score
                # or keep both semantic and keyword if they're both valuable
                if key in unique_results:
                    existing = unique_results[key]
                    
                    # If one is semantic and one is keyword, combine their scores
                    if existing["match_type"] != result["match_type"]:
                        # Keep the better match_type but combine scores
                        if existing["hybrid_search_score"] < result["hybrid_search_score"]:
                            # New result is better, but keep combined score
                            combined_score = existing["hybrid_search_score"] + result["hybrid_search_score"]
                            result["hybrid_search_score"] = combined_score
                            result["relevance_score"] = max(existing["relevance_score"], result["relevance_score"])
                            result["combined_match"] = True
                            unique_results[key] = result
                        else:
                            # Existing is better, update its score
                            existing["hybrid_search_score"] += result["hybrid_search_score"]
                            existing["relevance_score"] = max(existing["relevance_score"], result["relevance_score"])
                            existing["combined_match"] = True
                    else:
                        # Same match type, keep the one with the better score
                        if existing["hybrid_search_score"] < result["hybrid_search_score"]:
                            unique_results[key] = result
                else:
                    # No duplicate, add the result
                    unique_results[key] = result
            
            # Convert to list
            unique_results_list = list(unique_results.values())
            
            # Final reranking: balance between semantic relevance, keyword matches, and content quality
            reranked_results = self._rerank_hybrid_results(unique_results_list, query, important_terms)
            
            # Apply strict post-search user filtering to ensure proper isolation
            final_results = []
            final_sources = []
            
            for result in reranked_results[:n_results]:
                user_source = None
                
                # For semantic results
                if result.get("match_type") == "semantic" or result.get("source") == "semantic":
                    # Try to get user_id from metadata
                    if "metadata" in result:
                        user_source = result["metadata"].get("user_id")
                        if not user_source and result["metadata"].get("user_type") == "global":
                            user_source = "global"
                    
                    # Try direct user_source property
                    if not user_source and "user_source" in result:
                        user_source = result["user_source"]
                
                # For keyword results
                elif result.get("match_type") == "keyword" or result.get("source") == "keyword":
                    # Try direct user_id property
                    user_source = result.get("user_id")
                    
                    # Try user_source property
                    if not user_source and "user_source" in result:
                        user_source = result["user_source"]
                    
                    # Try metadata
                    if not user_source and "metadata" in result:
                        user_source = result["metadata"].get("user_id")
                        if not user_source and result["metadata"].get("user_type") == "global":
                            user_source = "global"
                
                # Default to unknown if we couldn't find a source
                if not user_source:
                    # Look for any indication of source in the result
                    if result.get("user_type") == "global":
                        user_source = "global"
                    else:
                        user_source = "unknown"
                
                # Apply strict user filtering - only include if:
                # 1. User_id matches the requested user_id
                # 2. Result is global
                # 3. Result is legacy (no user attribution)
                # 4. No user_id was provided in the request (and result is global/legacy)
                include_result = False
                
                if user_id:
                    # When user_id provided, include if:
                    if user_source == user_id or user_source == "global" or user_source == "legacy":
                        include_result = True
                else:
                    # When no user_id provided, only include global/legacy results
                    if user_source == "global" or user_source == "legacy":
                        include_result = True
                
                if include_result:
                    # Remove internal scoring fields before returning
                    if "hybrid_search_score" in result:
                        del result["hybrid_search_score"]
                    if "source_keywords" in result:
                        del result["source_keywords"]
                    if "combined_match" in result:
                        del result["combined_match"]
                        
                    final_results.append(result)
                    final_sources.append(user_source)
                
            print(f"Hybrid search found {len(final_results)} results with sources: {final_sources}")
            
            return final_results
        except Exception as e:
            print(f"Error in hybrid search: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def parallel_hybrid_search(self, query: str, n_results: int = 20, user_id: Optional[str] = None) -> List[Dict]:
        """
        OPTIMIZED: Simplified hybrid search for better performance and reliability.
        Uses sequential processing instead of complex parallel timeout handling.
        """
        print(f"Performing simplified hybrid search with semantic weight: 0.6, keyword weight: 0.4")
        
        # Ensure user_id is None if empty string
        user_id = user_id if user_id and user_id.strip() else None
        
        start_time = time.time()
        
        # OPTIMIZATION: Use simple sequential approach for better reliability
        try:
            # Step 1: Quick semantic search
            semantic_results = self.semantic_search(query, min(n_results * 2, 10), user_id)
            print(f"Semantic search found {len(semantic_results)} results")
            
            # Step 2: Quick keyword search on important terms only
            keywords = [word for word in query.split() if len(word) > 3][:3]  # Limit to 3 keywords
            keyword_results = []
            
            for keyword in keywords[:2]:  # Only search top 2 keywords
                try:
                    kw_results = self.keyword_search(keyword, 3, user_id)  # Limit to 3 results per keyword
                    keyword_results.extend(kw_results)
                except Exception as e:
                    print(f"Keyword search failed for '{keyword}': {e}")
                    continue
            
            print(f"Keyword search found {len(keyword_results)} results")
            
            # Step 3: Simple combination and deduplication
            all_results = []
            seen_texts = set()
            
            # Add semantic results first (higher priority)
            for result in semantic_results:
                text = result.get('text', '')[:100]  # First 100 chars for dedup
                if text not in seen_texts:
                    result['match_type'] = 'semantic'
                    result['relevance_score'] = 1.0 - result.get('distance', 0)
                    all_results.append(result)
                    seen_texts.add(text)
            
            # Add keyword results 
            for result in keyword_results:
                text = result.get('text', '')[:100]
                if text not in seen_texts:
                    result['match_type'] = 'keyword'
                    result['relevance_score'] = result.get('score', 0.5)
                    all_results.append(result)
                    seen_texts.add(text)
            
            # Sort by relevance and limit results
            all_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            final_results = all_results[:n_results]
            
            duration = time.time() - start_time
            print(f"Simplified hybrid search completed in {duration:.2f}s with {len(final_results)} results")
            return final_results
            
        except Exception as e:
            print(f"Hybrid search failed: {e}")
            # Fallback to semantic search only
            try:
                return self.semantic_search(query, n_results, user_id)
            except Exception:
                return []
    
    def _analyze_query_intent(self, query: str) -> Dict:
        """
        Analyze the query to determine intent and optimal search strategy weights.
        
        Args:
            query: The user's query
            
        Returns:
            Dictionary with analysis results
        """
        # Default weights
        semantic_weight = 0.6
        keyword_weight = 0.4
        
        # Simple keyword analysis
        keywords = [word.lower() for word in query.split() if len(word) > 3]
        
        return {
            "semantic_weight": semantic_weight,
            "keyword_weight": keyword_weight,
            "extracted_keywords": keywords[:5],  # Limit to 5 keywords
            "query_complexity": "simple" if len(keywords) <= 3 else "complex"
        }
    
    def _rerank_hybrid_results(self, results: List[Dict], query: str, important_terms: List[str]) -> List[Dict]:
        """
        Rerank hybrid search results using a balanced scoring approach.
        
        Args:
            results: List of search results
            query: Original query
            important_terms: Important terms identified in the query
            
        Returns:
            Reranked results list
        """
        if not results:
            return []
            
        # Extract query terms (excluding stopwords)
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
                     'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for', 'with', 
                     'by', 'about', 'like', 'through', 'over', 'before', 'after',
                     'between', 'under', 'above', 'of', 'during', 'since', 'what', 
                     'who', 'where', 'when', 'how', 'why', 'which', 'whom', 'whose'}
                     
        query_terms = [term.lower() for term in query.split() if term.lower() not in stop_words and len(term) > 2]
        
        for result in results:
            # Start with base score (either from hybrid_search_score or relevance_score)
            final_score = result.get("hybrid_search_score", result.get("relevance_score", 0.5))
            
            # Text content for analysis
            text = result.get("text", "").lower()
            
            # Check for proximity of query terms in the text (reward closer occurrences)
            term_positions = {}
            for term in query_terms:
                positions = []
                start = 0
                while True:
                    pos = text.find(term, start)
                    if pos == -1:
                        break
                    positions.append(pos)
                    start = pos + 1
                if positions:
                    term_positions[term] = positions
            
            # If we found multiple terms, check if they appear close together
            if len(term_positions) >= 2:
                min_distance = float('inf')
                for term1, pos1_list in term_positions.items():
                    for term2, pos2_list in term_positions.items():
                        if term1 != term2:
                            for pos1 in pos1_list:
                                for pos2 in pos2_list:
                                    min_distance = min(min_distance, abs(pos1 - pos2))
                
                # If terms are close together (within ~10 words), boost the score
                if min_distance < 50:  # Rough approximation of 10 words
                    proximity_boost = max(0, 0.15 * (1 - min_distance/100))
                    final_score += proximity_boost
            
            # Analyze content quality
            # Prefer medium-length content (not too short, not too long)
            words = text.split()
            word_count = len(words)
            
            # Ideal length around 100-200 words
            if 75 <= word_count <= 250:
                final_score += 0.05
            elif word_count < 40:
                final_score -= 0.05  # Penalize very short snippets
            elif word_count > 500:
                final_score -= 0.1   # Penalize very long content
                
            # Boost documents that match important terms
            for term in important_terms:
                if term in text:
                    final_score += 0.1
                    
            # Boost results that match multiple query terms
            matched_terms = sum(1 for term in query_terms if term in text)
            term_coverage = matched_terms / len(query_terms) if query_terms else 0
            final_score += term_coverage * 0.15
            
            # Store the final score
            result["final_score"] = final_score
        
        # Sort by final score
        return sorted(results, key=lambda x: x.get("final_score", 0), reverse=True)
    
    def export_knowledge_graph(self, output_format: str = "json", output_path: Optional[str] = None) -> Optional[str]:
        """
        Export the knowledge graph to a file.
        
        Args:
            output_format: Format to export to ("json", "graphml", "rdf").
            output_path: Path to save the export to. If None, a default path will be used.
            
        Returns:
            Path to the exported file, or None if export failed.
        """
        if isinstance(self.graph_db, Neo4jAdapter):
            try:
                # Default output path if not provided
                if not output_path:
                    output_path = f"knowledge_graph_export.{output_format.lower()}"
                    
                output_path = Path(output_path)
                
                # Export format handlers
                if output_format.lower() == "json":
                    # Get all documents, pages, and chunks
                    query = """
                    MATCH (d:Document)
                    OPTIONAL MATCH (d)-[:CONTAINS]->(p:Page)
                    OPTIONAL MATCH (p)-[:CONTAINS]->(c:Chunk)
                    RETURN d, collect(distinct p) as pages, collect(distinct c) as chunks
                    """
                    
                    results = self.graph_db.graph.run(query).data()
                    
                    # Convert to a more JSON-friendly format
                    export_data = []
                    for result in results:
                        document = dict(result["d"])
                        pages = [dict(p) for p in result["pages"] if p]
                        chunks = [dict(c) for c in result["chunks"] if c]
                        
                        # Group chunks by page
                        pages_with_chunks = {}
                        for page in pages:
                            page_id = page.get("id")
                            pages_with_chunks[page_id] = {
                                "page_data": page,
                                "chunks": []
                            }
                            
                        for chunk in chunks:
                            page_id = chunk.get("page_id")
                            if page_id in pages_with_chunks:
                                pages_with_chunks[page_id]["chunks"].append(chunk)
                        
                        # Structure the document
                        doc_data = {
                            "document": document,
                            "pages": [
                                {
                                    **page_data["page_data"],
                                    "chunks": page_data["chunks"]
                                }
                                for page_id, page_data in pages_with_chunks.items()
                            ]
                        }
                        
                        export_data.append(doc_data)
                    
                    # Write to file
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(export_data, f, indent=2)
                    
                    print(f"Knowledge graph exported to {output_path}")
                    return str(output_path)
                    
                else:
                    print(f"Export format '{output_format}' not implemented yet")
                    return None
                    
            except Exception as e:
                print(f"Error exporting knowledge graph: {e}")
                return None
        else:
            print("Export not implemented for this graph database type")
            return None
    
    def remove_document_by_hash(self, file_hash: str, force: bool = False, user_id: Optional[str] = None) -> bool:
        """
        Remove a document from the knowledge graph using its file hash.
        
        Args:
            file_hash: Hash of the document to remove.
            force: Whether to skip confirmation.
            user_id: Optional user ID associated with the document.
                     If provided, only remove document for this specific user.
                     If not provided, remove global document.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Check if document exists
            if isinstance(self.graph_db, Neo4jAdapter):
                doc_node = self.graph_db.find_document_by_hash(file_hash, user_id)
                if not doc_node:
                    if user_id:
                        print(f"Document with hash {file_hash} for user {user_id} not found.")
                    else:
                        print(f"Document with hash {file_hash} not found.")
                    return False
                
                # Get document title
                title = doc_node.get("title", "Unknown")
                
                # Prompt for confirmation if not forced
                if not force:
                    if user_id:
                        prompt = f"Are you sure you want to remove document '{title}' for user {user_id}? (y/n): "
                    else:
                        prompt = f"Are you sure you want to remove document '{title}'? (y/n): "
                    confirm = input(prompt).lower().strip()
                    if confirm != "y" and confirm != "yes":
                        print("Operation cancelled.")
                        return False
                
                # Remove the document
                return self.remove_existing_document(file_hash, user_id)
            else:
                print("This operation is only supported with Neo4j")
                return False
        except Exception as e:
            print(f"Error removing document by hash: {e}")
            return False
            
    def remove_document_by_path(self, pdf_path: str, force: bool = False, user_id: Optional[str] = None) -> bool:
        """
        Remove a document from the knowledge graph using its file path.
        
        Args:
            pdf_path: Path to the PDF file.
            force: Whether to skip confirmation.
            user_id: Optional user ID associated with the document.
                     If provided, only remove document for this specific user.
                     If not provided, remove global document.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Process the PDF to get its hash
            processed_pdf = self.pdf_processor.process_pdf(pdf_path, extraction_method="auto")
            file_hash = processed_pdf["metadata"]["file_hash"]
            
            # Use the hash to remove the document
            return self.remove_document_by_hash(file_hash, force, user_id)
        except Exception as e:
            print(f"Error removing document by path: {e}")
            return False
    
    def _extract_important_terms(self, query: str) -> List[str]:
        """
        Extract important terms from the query for keyword search.
        This is a simplified version of query analysis that doesn't depend on LLM.
        
        Args:
            query: The query text
            
        Returns:
            List of important terms
        """
        try:
            # Fallback to simpler extraction method
            stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
                        'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for', 'with', 
                        'by', 'about', 'like', 'through', 'over', 'before', 'after',
                        'between', 'under', 'above', 'of', 'during', 'since', 'what', 
                        'who', 'where', 'when', 'how', 'why', 'which', 'whom', 'whose'}
            
            # Split the query, filter out stop words and short words
            terms = [term.lower() for term in query.split() 
                    if term.lower() not in stop_words and len(term) > 3]
            
            # Extract quoted phrases as they're likely important
            quoted_terms = re.findall(r'"([^"]*)"', query)
            if quoted_terms:
                terms.extend(quoted_terms)
            
            # Deduplicate
            unique_terms = list(set(terms))
            
            # Return up to 10 terms to avoid overloading
            return unique_terms[:10]
        except Exception as e:
            print(f"Error extracting important terms: {e}")
            # Return a few words as fallback
            words = query.split()
            return [w.lower() for w in words if len(w) > 3][:5]
