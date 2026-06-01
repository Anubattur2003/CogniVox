"""
Storage adapter for handling PDF document storage.
This adapter provides a consistent interface for storing and retrieving documents
in a local Bucket directory.
"""

import os
import hashlib
import shutil
from pathlib import Path
from typing import Optional, Union, Dict, Any

from src.config import BUCKET_PATH
from src.gcp_bucket import get_cached_storage_manager


class DocumentStorageAdapter:
    """
    Adapter for document storage using local Bucket directory.
    """
    
    def __init__(self):
        """Initialize the document storage adapter."""
        self.bucket_path = BUCKET_PATH
        
        # Ensure bucket directory exists
        self.bucket_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage manager with local configuration
        config = {
            'storage': {
                'bucket_path': str(self.bucket_path)
            }
        }
        
        self.storage_manager = get_cached_storage_manager(config)
        print(f"✅ Successfully initialized local storage adapter using: {self.bucket_path}")

    def save_document(self, file_path: Union[str, Path], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Save a document to the Bucket directory.
        
        Args:
            file_path: Path to the PDF file to save
            user_id: Optional user ID for user-specific storage
            
        Returns:
            Dictionary containing storage information
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not file_path.suffix.lower() == '.pdf':
                raise ValueError(f"Only PDF files are supported, got: {file_path.suffix}")
            
            # Calculate file hash for unique identification
            file_hash = self._compute_file_hash(file_path)
            
            # Use storage manager to upload document with user_id
            result = self.storage_manager.upload_document(
                file_path=file_path,
                document_id=f"{file_hash}.pdf",
                user_id=user_id,
                metadata={
                    "original_filename": file_path.name,
                    "file_hash": file_hash
                }
            )
            
            if result.status == "success":
                # Get the actual storage path from the result document
                # The document's blob_name contains the relative path from bucket root
                if result.document:
                    storage_path = result.document.blob_name
                    full_path = result.document.download_url or result.document.storage_url
                else:
                    # Fallback: construct path manually if document not available
                    if user_id:
                        storage_path = f"users/{user_id}/{file_hash}.pdf"
                    else:
                        storage_path = f"documents/{file_hash}.pdf"
                    full_path = f"file://{self.bucket_path / storage_path}"
                
                return {
                    "storage_path": storage_path,
                    "file_hash": file_hash,
                    "original_filename": file_path.name,
                    "file_size": file_path.stat().st_size,
                    "bucket_name": self.bucket_path.name,
                    "full_path": full_path,
                    "is_local_stored": True,
                    "success": True
                }
            else:
                raise Exception(f"Upload failed: {result.message}")
                
        except Exception as e:
            print(f"❌ Error saving document: {e}")
            raise

    def get_document(self, file_path: Union[str, Path]) -> Optional[bytes]:
        """
        Retrieve a document from storage.
        
        Args:
            file_path: Path to the document in storage
            
        Returns:
            Document content as bytes, or None if not found
        """
        try:
            # Handle both local paths and storage paths
            if isinstance(file_path, str) and file_path.startswith("documents/"):
                # This is a storage path
                actual_path = self.bucket_path / file_path
            else:
                # This might be a direct file path
                actual_path = Path(file_path)
                if not actual_path.is_absolute():
                    actual_path = self.bucket_path / file_path
            
            if actual_path.exists():
                with open(actual_path, 'rb') as f:
                    return f.read()
            
            return None
            
        except Exception as e:
            print(f"❌ Error retrieving document: {e}")
            return None

    def document_exists(self, file_hash: str) -> bool:
        """
        Check if a document exists in storage.
        
        Args:
            file_hash: Hash of the document
            
        Returns:
            True if document exists, False otherwise
        """
        try:
            storage_path = self.bucket_path / "documents" / f"{file_hash}.pdf"
            return storage_path.exists()
        except Exception:
            return False

    def get_file_path(self, file_hash: str) -> Optional[str]:
        """
        Get the storage path for a document.
        
        Args:
            file_hash: Hash of the document
            
        Returns:
            Storage path or None if not found
        """
        storage_path = f"documents/{file_hash}.pdf"
        full_path = self.bucket_path / storage_path
        
        if full_path.exists():
            return storage_path
        
        return None

    def get_download_url(self, storage_uri: str, expiration_minutes: int = 60) -> str:
        """
        Get a download URL for a document.
        
        Args:
            storage_uri: URI of the document (e.g., "file://path/to/file")
            expiration_minutes: URL expiration time (ignored for local files)
            
        Returns:
            Download URL
        """
        # For local files, just return the file:// URI
        if storage_uri.startswith("file://"):
            return storage_uri
        
        # If it's a storage path, convert to file:// URI
        if storage_uri.startswith("documents/"):
            full_path = self.bucket_path / storage_uri
            return f"file://{full_path.absolute()}"
        
        return storage_uri

    def _compute_file_hash(self, file_path: Path) -> str:
        """
        Compute SHA256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA256 hash as hex string
        """
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def cleanup(self):
        """Clean up any resources."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()