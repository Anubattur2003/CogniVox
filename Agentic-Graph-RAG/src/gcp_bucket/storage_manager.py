"""
Storage Manager for local document storage
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import logging
import hashlib
import json

from .local_storage_client import LocalStorageClient
from .models import PDFDocument, OperationResult
from .exceptions import StorageError

logger = logging.getLogger(__name__)

# Global cache for storage manager instances
_storage_manager_cache = {}


class StorageManager:
    """
    Storage manager that provides a unified interface for local document storage
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the storage manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Always use local storage now (GCP removed)
        self.use_gcp = False
        
        # Get bucket path from config, default to "Bucket" directory
        storage_config = config.get('storage', {})
        bucket_path = storage_config.get('bucket_path', 'Bucket')
        
        # Ensure bucket path is absolute
        if not Path(bucket_path).is_absolute():
            bucket_path = Path.cwd() / bucket_path
        
        self.bucket_path = Path(bucket_path)
        
        # Initialize local storage client
        self._local_client = LocalStorageClient(
            bucket_path=str(self.bucket_path),
            default_folder="documents"
        )
        
        logger.info(f"Using local storage at: {self.bucket_path}")
    
    def upload_document(self, file_path: Union[str, Path], 
                       document_id: Optional[str] = None,
                       user_id: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> OperationResult:
        """
        Upload a document to storage
        
        Args:
            file_path: Path to the file to upload
            document_id: Optional document ID
            user_id: Optional user ID for user-specific storage
            metadata: Optional metadata
            
        Returns:
            Operation result
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return OperationResult(
                status="failed",
                message=f"File not found: {file_path}",
                operation_type="upload",
                error_code="FILE_NOT_FOUND"
            )
        
        # Determine folder path based on user_id
        folder_path = None
        if user_id:
            folder_path = f"users/{user_id}"
        
        # Use document_id as blob_name if provided, otherwise use filename
        blob_name = document_id if document_id else file_path.name
        
        return self._local_client.upload_pdf(
            file_path=file_path,
            blob_name=blob_name,
            folder_path=folder_path,
            metadata=metadata,
            overwrite=True
        )
    
    def download_document(self, document_path: str, 
                         local_path: Optional[Union[str, Path]] = None,
                         user_id: Optional[str] = None) -> OperationResult:
        """
        Download a document from storage
        
        Args:
            document_path: Path of the document in storage
            local_path: Optional local destination path
            user_id: Optional user ID for user-specific documents
            
        Returns:
            Operation result
        """
        try:
            # Determine the blob name based on user_id
            if user_id:
                blob_name = f"users/{user_id}/{document_path}"
            else:
                # Try to find the document in various locations
                possible_paths = [
                    document_path,
                    f"documents/{document_path}",
                ]
                
                blob_name = None
                for path in possible_paths:
                    if (self.bucket_path / path).exists():
                        blob_name = path
                        break
                
                if blob_name is None:
                    return OperationResult(
                        status="failed",
                        message=f"Document not found: {document_path}",
                        operation_type="download",
                        error_code="FILE_NOT_FOUND"
                    )
            
            return self._local_client.download_pdf(
                blob_name=blob_name,
                local_path=local_path,
                overwrite=True
            )
            
        except Exception as e:
            return OperationResult(
                status="failed",
                message=f"Download failed: {str(e)}",
                operation_type="download",
                error_code="DOWNLOAD_ERROR",
                error_details={"error": str(e)}
            )
    
    def list_documents(self, user_id: Optional[str] = None, 
                      limit: Optional[int] = None) -> List[PDFDocument]:
        """
        List documents in storage
        
        Args:
            user_id: Optional user ID to list user-specific documents
            limit: Optional limit on number of results
            
        Returns:
            List of PDF documents
        """
        try:
            folder_path = None
            if user_id:
                folder_path = f"users/{user_id}"
                logger.info(f"Listing documents in folder: {folder_path}")
                logger.info(f"Full search path: {self.bucket_path / folder_path}")
                logger.info(f"Path exists: {(self.bucket_path / folder_path).exists()}")
            
            documents = self._local_client.list_documents(
                folder_path=folder_path,
                limit=limit
            )
            
            logger.info(f"Found {len(documents)} documents in folder_path: {folder_path}")
            
            # If no documents found for user_id, also check the documents folder for backward compatibility
            if user_id and len(documents) == 0:
                logger.info(f"No documents found in users/{user_id}, checking documents/ folder for backward compatibility")
                global_docs = self._local_client.list_documents(
                    folder_path="documents",
                    limit=limit
                )
                logger.info(f"Found {len(global_docs)} documents in documents/ folder")
                # For backward compatibility, include global documents if user-specific folder is empty
                # In the future, you might want to filter these by user_id metadata if available
                documents = global_docs
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}", exc_info=True)
            return []
    
    def get_document(self, document_path: str, 
                    user_id: Optional[str] = None) -> Optional[PDFDocument]:
        """
        Get a specific document
        
        Args:
            document_path: Path of the document in storage
            user_id: Optional user ID for user-specific documents
            
        Returns:
            PDF document or None if not found
        """
        try:
            # Determine the blob name based on user_id
            if user_id:
                blob_name = f"users/{user_id}/{document_path}"
            else:
                # Try to find the document in various locations
                possible_paths = [
                    document_path,
                    f"documents/{document_path}",
                ]
                
                blob_name = None
                for path in possible_paths:
                    if (self.bucket_path / path).exists():
                        blob_name = path
                        break
                
                if blob_name is None:
                    return None
            
            return self._local_client.get_document(blob_name)
            
        except Exception as e:
            logger.error(f"Failed to get document {document_path}: {e}")
            return None
    
    def delete_document(self, document_path: str, 
                       user_id: Optional[str] = None) -> OperationResult:
        """
        Delete a document from storage
        
        Args:
            document_path: Path of the document in storage (can be full path like "users/12/file.pdf" or just filename)
            user_id: Optional user ID for user-specific documents
            
        Returns:
            Operation result
        """
        try:
            # Check if document_path already contains the full path (starts with "users/" or "documents/")
            if document_path.startswith("users/") or document_path.startswith("documents/"):
                # Already a full path, use it directly
                blob_name = document_path
            elif user_id:
                # Construct path for user-specific document
                blob_name = f"users/{user_id}/{document_path}"
            else:
                # Try to find the document in various locations
                possible_paths = [
                    document_path,
                    f"documents/{document_path}",
                ]
                
                blob_name = None
                for path in possible_paths:
                    if (self.bucket_path / path).exists():
                        blob_name = path
                        break
                
                if blob_name is None:
                    return OperationResult(
                        status="failed",
                        message=f"Document not found: {document_path}",
                        operation_type="delete",
                        error_code="FILE_NOT_FOUND"
                    )
            
            logger.info(f"Deleting document with blob_name: {blob_name}")
            return self._local_client.delete_document(blob_name)
            
        except Exception as e:
            return OperationResult(
                status="failed",
                message=f"Delete failed: {str(e)}",
                operation_type="delete",
                error_code="DELETE_ERROR",
                error_details={"error": str(e)}
            )
    
    def get_document_url(self, document_path: str, 
                        user_id: Optional[str] = None) -> Optional[str]:
        """
        Get a URL for accessing the document
        
        Args:
            document_path: Path of the document in storage
            user_id: Optional user ID for user-specific documents
            
        Returns:
            Document URL or None if not found
        """
        try:
            document = self.get_document(document_path, user_id)
            if document:
                return document.download_url
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document URL for {document_path}: {e}")
            return None


def get_cached_storage_manager(config: Dict[str, Any]) -> StorageManager:
    """
    Get a cached storage manager instance.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        StorageManager instance (cached if possible)
    """
    # Create a hash of the config for caching
    config_str = json.dumps(config, sort_keys=True)
    config_hash = hashlib.md5(config_str.encode()).hexdigest()
    
    # Check if we already have a cached instance for this config
    if config_hash in _storage_manager_cache:
        logger.debug(f"Using cached storage manager for config hash: {config_hash}")
        return _storage_manager_cache[config_hash]
    
    # Create new instance and cache it
    logger.info(f"Creating new storage manager for config hash: {config_hash}")
    storage_manager = StorageManager(config)
    _storage_manager_cache[config_hash] = storage_manager
    
    return storage_manager


def clear_storage_manager_cache():
    """Clear the storage manager cache (useful for testing)"""
    global _storage_manager_cache
    _storage_manager_cache.clear()
    logger.info("Storage manager cache cleared")