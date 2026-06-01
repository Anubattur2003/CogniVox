import os
import logging
import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
import uuid

import chromadb
import numpy as np
from chromadb.config import Settings
from tqdm import tqdm

from src.config import VECTOR_STORE_PATH, VECTOR_STORE_TYPE

# Setup logging
logger = logging.getLogger(__name__)

# Global ChromaDB client singleton with thread lock
_chroma_client = None
_chroma_client_lock = threading.Lock()


class BaseVectorStore(ABC):
    """
    Abstract base class for vector stores.
    """
    
    @abstractmethod
    def add_documents(self, documents: List[Dict]) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document dictionaries containing text and embeddings.
            
        Returns:
            List of document IDs.
        """
        pass
    
    @abstractmethod
    def search(self, query: str, embedding: List[float], n_results: int = 20, where: Optional[Dict] = None) -> List[Dict]:
        """
        Search for similar documents.
        
        Args:
            query: Query text.
            embedding: Query embedding.
            n_results: Number of results to return.
            where: Optional filter to apply to the search (e.g., user_id filter).
            
        Returns:
            List of similar documents.
        """
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the vector store.
        
        Args:
            document_id: ID of the document to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[Dict]:
        """
        Get a document by ID.
        
        Args:
            document_id: ID of the document to retrieve.
            
        Returns:
            Document dictionary if found, None otherwise.
        """
        pass
    
    @abstractmethod
    def document_exists(self, file_hash: str) -> bool:
        """
        Check if a document with the given file hash exists.
        
        Args:
            file_hash: Hash of the file to check.
            
        Returns:
            True if the document exists, False otherwise.
        """
        pass


class ChromaVectorStore(BaseVectorStore):
    """
    Vector store implementation using ChromaDB.
    """
    
    def __init__(self, collection_name: str = "documents", persist_directory: str = None):
        """
        Initialize the ChromaDB vector store.
        
        Args:
            collection_name: Name of the collection to use.
            persist_directory: Directory to persist the database, if None uses VECTOR_STORE_PATH.
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or str(VECTOR_STORE_PATH)
        self._dimension_checked = False
        self._expected_dimension = None
        
        # Use singleton client to avoid concurrent access issues
        self.client = self._get_or_create_client(self.persist_directory)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Successfully initialized collection: {collection_name}")
    
    @staticmethod
    def _get_or_create_client(persist_directory: str):
        """
        Get or create a singleton ChromaDB client to avoid concurrent access issues.
        Thread-safe using a lock.
        """
        global _chroma_client, _chroma_client_lock
        
        with _chroma_client_lock:
            if _chroma_client is None:
                logger.info(f"Creating new ChromaDB client at: {persist_directory}")
                _chroma_client = chromadb.PersistentClient(
                    path=persist_directory,
                    settings=Settings(
                        anonymized_telemetry=False  # Disable telemetry for offline operation
                    )
                )
            else:
                logger.debug("Reusing existing ChromaDB client")
            
            return _chroma_client
        
    def add_documents(self, documents: List[Dict]) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document dictionaries containing text and embeddings.
            
        Returns:
            List of document IDs.
        """
        if not documents:
            logger.warning("No documents to add")
            return []
        
        # Generate IDs for documents if they don't have them
        document_ids = []
        embeddings = []
        metadatas = []
        texts = []
        
        for doc in documents:
            # Skip documents without embeddings
            if "embedding" not in doc or not doc["embedding"]:
                logger.warning(f"Skipping document without embedding: {doc.get('text', '')[:50]}...")
                continue
                
            doc_id = str(uuid.uuid4())
            document_ids.append(doc_id)
            
            embeddings.append(doc["embedding"])
            texts.append(doc["text"])
            
            # Get metadata with safe defaults if fields are missing
            metadata = doc.get("metadata", {})
            
            # Prepare metadata (ensure it's flattened for ChromaDB)
            metadata_dict = {
                "file_hash": metadata.get("file_hash", "unknown"),
                "file_path": metadata.get("file_path", "unknown"),
                "document_path": metadata.get("document_path", metadata.get("file_path", "unknown")),  # Prefer document_path over file_path
                "page_number": metadata.get("page_number", 0),
                "title": metadata.get("title", "unknown"),
                "chunk_id": metadata.get("chunk_id", 0),
                "total_chunks": metadata.get("chunk_count", 1),  # Using chunk_count from TextProcessor as total_chunks
            }
            
            # Explicitly add user_id and user_type to metadata if present
            if "user_id" in metadata and metadata["user_id"]:
                metadata_dict["user_id"] = metadata["user_id"]
            elif "user_type" in metadata:
                metadata_dict["user_type"] = metadata["user_type"]
                
            metadatas.append(metadata_dict)
        
        if not document_ids:
            logger.warning("No valid documents to add after filtering")
            return []
        
        # Check embedding dimension on first use
        if embeddings and not self._dimension_checked:
            current_dim = len(embeddings[0])
            
            # Try to get existing collection info
            try:
                existing_count = self.collection.count()
                if existing_count > 0:
                    # Collection has data, test dimension compatibility
                    try:
                        test_result = self.collection.query(
                            query_embeddings=[embeddings[0]],
                            n_results=min(1, existing_count)
                        )
                        self._expected_dimension = current_dim
                        self._dimension_checked = True
                        logger.info(f"Collection dimension validated: {current_dim}")
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "dimension" in error_msg or "expected" in error_msg:
                            # Extract expected dimension from error message
                            import re
                            match = re.search(r'dimension of (\d+)', error_msg)
                            expected = match.group(1) if match else "unknown"
                            
                            error_message = (
                                f"Embedding dimension mismatch: Collection expects {expected}D embeddings, "
                                f"but current model produces {current_dim}D embeddings. "
                                f"Please reset the database by deleting: {self.persist_directory}"
                            )
                            logger.error(error_message)
                            raise ValueError(error_message)
                        else:
                            raise
                else:
                    # Empty collection, set dimension
                    self._expected_dimension = current_dim
                    self._dimension_checked = True
                    logger.info(f"Collection initialized with dimension: {current_dim}")
            except ValueError:
                # Re-raise ValueError (dimension mismatch)
                raise
            except Exception as e:
                logger.warning(f"Could not check collection: {e}")
        
        # Add documents to ChromaDB
        try:
            self.collection.add(
                ids=document_ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            logger.info(f"Successfully added {len(document_ids)} documents to vector store")
        except Exception as e:
            error_msg = str(e).lower()
            if "dimension" in error_msg:
                logger.error(f"Dimension mismatch error: {e}")
                logger.error(f"To fix: Delete vector store directory: {self.persist_directory}")
            raise
        
        # PersistentClient persists automatically
        
        return document_ids
    
    def search(self, query: str, embedding: List[float], n_results: int = 20, where: Optional[Dict] = None) -> List[Dict]:
        """
        Search for similar documents using vector similarity.
        
        Args:
            query: Query text.
            embedding: Query embedding.
            n_results: Number of results to return.
            where: Optional filter to apply to the search (e.g., user_id filter).
            
        Returns:
            List of similar documents.
        """
        # Create query parameters
        query_params = {
            "query_embeddings": [embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"]
        }
        
        # Parse the where clause for user_id and user_type conditions
        user_specific_search = False
        user_id = None
        
        if where and "user_id" in where and where["user_id"]:
            user_specific_search = True
            user_id = where["user_id"]
            query_params["where"] = where
            print(f"Searching for user-specific documents. User ID: {user_id}")
        elif where and "user_type" in where and where["user_type"] == "global":
            query_params["where"] = where
            print(f"Searching for global documents only")
        
        # Execute the search query - if no where clause is specified, get all documents
        results = self.collection.query(**query_params)
        
        # Format and filter results
        formatted_results = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                doc_id = results["ids"][0][i]
                text = results["documents"][0][i]
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                
                # Apply strict post-filtering for user isolation
                include_doc = False
                
                # If user_id is specified, include both user-specific and global docs
                if user_specific_search:
                    if metadata.get("user_id") == user_id:
                        include_doc = True
                    elif metadata.get("user_type") == "global":
                        include_doc = True
                    elif "user_id" not in metadata and "user_type" not in metadata:
                        # Legacy documents with no user attribution
                        include_doc = True
                # If no user_id, only include global documents
                else:
                    if metadata.get("user_type") == "global":
                        include_doc = True
                    elif "user_id" not in metadata and "user_type" not in metadata:
                        # Legacy documents with no user attribution
                        include_doc = True
                    elif "user_id" in metadata:
                        # Explicitly exclude documents with user_id
                        include_doc = False
                
                if include_doc:
                    formatted_results.append({
                        "id": doc_id,
                        "text": text,
                        "metadata": metadata,
                        "distance": distance,
                    })
            
        # Limit results to requested number after filtering
        formatted_results = sorted(formatted_results, key=lambda x: x["distance"])[:n_results]
        
        # Report how many results were returned after filtering
        print(f"Vector store returned {len(formatted_results)} results after user filtering")
        user_sources = [r.get("metadata", {}).get("user_id", "global") for r in formatted_results]
        print(f"Result sources: {user_sources}")
        
        return formatted_results
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the vector store.
        
        Args:
            document_id: ID of the document to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            self.collection.delete(ids=[document_id])
            # PersistentClient persists automatically
            return True
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
    
    def get_document(self, document_id: str) -> Optional[Dict]:
        """
        Get a document by ID.
        
        Args:
            document_id: ID of the document to retrieve.
            
        Returns:
            Document dictionary if found, None otherwise.
        """
        try:
            result = self.collection.get(ids=[document_id], include=["documents", "metadatas", "embeddings"])
            
            if not result["ids"]:
                return None
                
            return {
                "id": result["ids"][0],
                "text": result["documents"][0],
                "metadata": result["metadatas"][0],
                "embedding": result["embeddings"][0],
            }
        except Exception as e:
            print(f"Error getting document: {e}")
            return None
    
    def document_exists(self, file_hash: str) -> bool:
        """
        Check if a document with the given file hash exists.
        
        Args:
            file_hash: Hash of the file to check.
            
        Returns:
            True if the document exists, False otherwise.
        """
        try:
            result = self.collection.get(
                where={"file_hash": file_hash},
                include=["metadatas"]
            )
            return len(result["ids"]) > 0
        except Exception as e:
            print(f"Error checking document existence: {e}")
            return False


def get_vector_store(store_type: str = VECTOR_STORE_TYPE) -> BaseVectorStore:
    """
    Factory function to get the appropriate vector store.
    
    Args:
        store_type: Type of vector store to use.
        
    Returns:
        Vector store instance.
    """
    if store_type.lower() == "chroma":
        return ChromaVectorStore()
    else:
        # Default to ChromaDB if the requested store is not implemented
        print(f"Vector store type '{store_type}' not implemented, using ChromaDB instead.")
        return ChromaVectorStore()
