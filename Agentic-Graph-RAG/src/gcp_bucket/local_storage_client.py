"""
Local Storage Client that mimics GCP Storage functionality
"""

import os
import hashlib
import mimetypes
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from contextlib import contextmanager

from .models import (
    PDFDocument, OperationResult, OperationStatus, 
    UploadRequest, DownloadRequest,
    StorageClass, PDFMetadata
)
from .exceptions import (
    StorageError, AuthenticationError, ResourceNotFoundError,
    NetworkError
)


class LocalStorageClient:
    """
    Local storage client that provides the same interface as GCP Storage
    """
    
    def __init__(self, bucket_path: str, default_folder: str = "documents"):
        """
        Initialize the local storage client
        
        Args:
            bucket_path: Local path to the "bucket" directory
            default_folder: Default folder for documents
        """
        self.bucket_path = Path(bucket_path)
        self.bucket_name = self.bucket_path.name
        self.default_folder = default_folder
        
        # Ensure bucket directory exists
        self.bucket_path.mkdir(parents=True, exist_ok=True)
        
        # Create metadata directory for storing document metadata
        self.metadata_path = self.bucket_path / ".metadata"
        self.metadata_path.mkdir(exist_ok=True)
    
    def upload_pdf(self, file_path: Union[str, Path], 
                   blob_name: Optional[str] = None,
                   folder_path: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None,
                   overwrite: bool = False) -> OperationResult:
        """
        Upload a PDF file to local storage
        
        Args:
            file_path: Path to the file to upload
            blob_name: Optional blob name (filename in storage)
            folder_path: Optional folder path within bucket
            metadata: Optional metadata
            overwrite: Whether to overwrite existing files
            
        Returns:
            Operation result
        """
        try:
            file_path = Path(file_path)
            
            # Validate file exists and is PDF
            if not file_path.exists():
                return OperationResult(
                    status=OperationStatus.FAILED,
                    message=f"File not found: {file_path}",
                    operation_type="upload",
                    error_code="FILE_NOT_FOUND"
                )
            
            if not file_path.suffix.lower() == '.pdf':
                return OperationResult(
                    status=OperationStatus.FAILED,
                    message=f"Only PDF files are supported, got: {file_path.suffix}",
                    operation_type="upload",
                    error_code="INVALID_FILE_TYPE"
                )
            
            # Determine storage path
            if blob_name is None:
                blob_name = file_path.name
            
            if folder_path:
                storage_path = self.bucket_path / folder_path / blob_name
            else:
                storage_path = self.bucket_path / self.default_folder / blob_name
            
            # Check if file already exists
            if storage_path.exists() and not overwrite:
                return OperationResult(
                    status=OperationStatus.FAILED,
                    message=f"File already exists: {storage_path.name}",
                    operation_type="upload",
                    error_code="FILE_EXISTS"
                )
            
            # Create directory structure
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file to storage location
            shutil.copy2(file_path, storage_path)
            
            # Prepare metadata
            file_metadata = self._prepare_metadata(file_path, metadata)
            
            # Create PDF document metadata
            pdf_metadata = PDFMetadata(
                title=file_metadata.get("title"),
                author=file_metadata.get("author"),
                subject=file_metadata.get("subject"),
                creator=file_metadata.get("creator"),
                file_size=storage_path.stat().st_size,
                file_hash=file_metadata.get("file_hash"),
                upload_timestamp=datetime.now(timezone.utc)
            )
            
            # Save metadata to JSON file
            relative_path = storage_path.relative_to(self.bucket_path)
            # Use os.sep to handle both Windows and Unix path separators
            metadata_file = self.metadata_path / f"{str(relative_path).replace(os.sep, '_')}.json"
            
            document_data = {
                "blob_name": str(relative_path).replace(os.sep, '/'),
                "original_filename": file_path.name,
                "bucket_name": self.bucket_name,
                "folder_path": folder_path,
                "file_size": storage_path.stat().st_size,
                "content_type": "application/pdf",
                "md5_hash": file_metadata.get("file_hash"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "metadata": file_metadata,
                "storage_url": f"file://{storage_path.absolute()}",
                "download_url": f"file://{storage_path.absolute()}"
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(document_data, f, indent=2, default=str)
            
            # Create PDFDocument
            document = PDFDocument(
                blob_name=str(relative_path).replace(os.sep, '/'),
                original_filename=file_path.name,
                bucket_name=self.bucket_name,
                folder_path=folder_path,
                file_size=storage_path.stat().st_size,
                content_type="application/pdf",
                md5_hash=file_metadata.get("file_hash"),
                metadata=pdf_metadata,
                storage_url=f"file://{storage_path.absolute()}",
                download_url=f"file://{storage_path.absolute()}"
            )
            
            return OperationResult(
                status=OperationStatus.SUCCESS,
                message=f"File uploaded successfully to {relative_path}",
                operation_type="upload",
                document=document,
                data={"storage_path": str(storage_path)}
            )
            
        except Exception as e:
            return OperationResult(
                status=OperationStatus.FAILED,
                message=f"Upload failed: {str(e)}",
                operation_type="upload",
                error_code="UPLOAD_ERROR",
                error_details={"error": str(e)}
            )
    
    def download_pdf(self, blob_name: str, 
                     local_path: Optional[Union[str, Path]] = None,
                     overwrite: bool = False) -> OperationResult:
        """
        Download a PDF file from local storage
        
        Args:
            blob_name: Name of the blob to download
            local_path: Optional local destination path
            overwrite: Whether to overwrite existing files
            
        Returns:
            Operation result
        """
        try:
            storage_path = self.bucket_path / blob_name
            
            if not storage_path.exists():
                return OperationResult(
                    status=OperationStatus.FAILED,
                    message=f"File not found: {blob_name}",
                    operation_type="download",
                    error_code="FILE_NOT_FOUND"
                )
            
            if local_path is None:
                local_path = Path.cwd() / storage_path.name
            else:
                local_path = Path(local_path)
            
            # Check if destination exists
            if local_path.exists() and not overwrite:
                return OperationResult(
                    status=OperationStatus.FAILED,
                    message=f"Destination file already exists: {local_path}",
                    operation_type="download",
                    error_code="FILE_EXISTS"
                )
            
            # Create destination directory
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(storage_path, local_path)
            
            return OperationResult(
                status=OperationStatus.SUCCESS,
                message=f"File downloaded successfully to {local_path}",
                operation_type="download",
                data={
                    "local_path": str(local_path),
                    "file_size": local_path.stat().st_size
                }
            )
            
        except Exception as e:
            return OperationResult(
                status=OperationStatus.FAILED,
                message=f"Download failed: {str(e)}",
                operation_type="download",
                error_code="DOWNLOAD_ERROR",
                error_details={"error": str(e)}
            )
    
    def list_documents(self, folder_path: Optional[str] = None, 
                       limit: Optional[int] = None) -> List[PDFDocument]:
        """
        List documents in storage
        
        Args:
            folder_path: Optional folder path to search in
            limit: Optional limit on number of results
            
        Returns:
            List of PDF documents
        """
        documents = []
        
        if folder_path:
            search_path = self.bucket_path / folder_path
        else:
            search_path = self.bucket_path
        
        print(f"Searching for documents in: {search_path}")
        print(f"Search path exists: {search_path.exists()}")
        print(f"Bucket path: {self.bucket_path}")
        
        if not search_path.exists():
            print(f"Warning: Search path does not exist: {search_path}")
            return documents
        
        count = 0
        pdf_files_found = list(search_path.rglob("*.pdf"))
        print(f"Found {len(pdf_files_found)} PDF files in {search_path}")
        
        for pdf_file in pdf_files_found:
            if limit and count >= limit:
                break
            
            if pdf_file.parent == self.metadata_path:
                continue  # Skip metadata directory
            
            try:
                document = self._file_to_document(pdf_file)
                documents.append(document)
                count += 1
                print(f"Added document: {document.original_filename} from {pdf_file}")
            except Exception as e:
                # Log error but continue with other files
                print(f"Error processing {pdf_file}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Sort by creation time (newest first)
        documents.sort(key=lambda d: d.created_at, reverse=True)
        
        print(f"Returning {len(documents)} documents")
        return documents
    
    def get_document(self, blob_name: str) -> PDFDocument:
        """
        Get a specific document by blob name
        
        Args:
            blob_name: Blob name of the document
            
        Returns:
            PDF document
            
        Raises:
            ResourceNotFoundError: If document not found
        """
        storage_path = self.bucket_path / blob_name
        
        if not storage_path.exists():
            raise ResourceNotFoundError(
                f"Document not found: {blob_name}",
                resource_type="document",
                resource_id=blob_name
            )
        
        return self._file_to_document(storage_path)
    
    def delete_document(self, blob_name: str) -> OperationResult:
        """
        Delete a document from storage
        
        Args:
            blob_name: Blob name of the document to delete
            
        Returns:
            Operation result
        """
        try:
            storage_path = self.bucket_path / blob_name
            
            if not storage_path.exists():
                return OperationResult(
                    status=OperationStatus.FAILED,
                    message=f"File not found: {blob_name}",
                    operation_type="delete",
                    error_code="FILE_NOT_FOUND"
                )
            
            # Delete the file
            storage_path.unlink()
            
            # Delete metadata file if it exists
            relative_path = storage_path.relative_to(self.bucket_path)
            metadata_file = self.metadata_path / f"{str(relative_path).replace(os.sep, '_')}.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            return OperationResult(
                status=OperationStatus.SUCCESS,
                message=f"Document deleted successfully: {blob_name}",
                operation_type="delete",
                data={"deleted_blob": blob_name}
            )
            
        except Exception as e:
            return OperationResult(
                status=OperationStatus.FAILED,
                message=f"Delete failed: {str(e)}",
                operation_type="delete",
                error_code="DELETE_ERROR",
                error_details={"error": str(e)}
            )
    
    def _prepare_metadata(self, file_path: Path, 
                          custom_metadata: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """
        Prepare metadata for the file
        
        Args:
            file_path: Path to the file
            custom_metadata: Optional custom metadata
            
        Returns:
            Prepared metadata dictionary
        """
        metadata = {
            "original_filename": file_path.name,
            "file_size": str(file_path.stat().st_size),
            "file_hash": self._calculate_file_hash(file_path),
            "upload_timestamp": datetime.now(timezone.utc).isoformat(),
            "content_type": "application/pdf"
        }
        
        # Add custom metadata if provided
        if custom_metadata:
            for key, value in custom_metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    metadata[f"custom_{key}"] = str(value)
        
        return metadata
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _file_to_document(self, file_path: Path) -> PDFDocument:
        """Convert local file to PDFDocument model"""
        relative_path = file_path.relative_to(self.bucket_path)
        
        # Try to load metadata from JSON file
        metadata_file = self.metadata_path / f"{str(relative_path).replace(os.sep, '_')}.json"
        document_data = {}
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    document_data = json.load(f)
            except Exception:
                pass  # Use defaults if metadata can't be loaded
        
        # Extract folder path
        folder_path = None
        if relative_path.parent != Path('.'):
            folder_path = str(relative_path.parent)
        
        # Create metadata
        file_metadata = PDFMetadata()
        if "metadata" in document_data:
            meta = document_data["metadata"]
            file_metadata.file_size = int(meta.get("file_size", file_path.stat().st_size))
            file_metadata.file_hash = meta.get("file_hash")
            if meta.get("upload_timestamp"):
                try:
                    file_metadata.upload_timestamp = datetime.fromisoformat(
                        meta["upload_timestamp"].replace('Z', '+00:00')
                    )
                except:
                    pass
        
        return PDFDocument(
            blob_name=str(relative_path).replace(os.sep, '/'),
            original_filename=document_data.get("original_filename", file_path.name),
            bucket_name=self.bucket_name,
            folder_path=folder_path,
            file_size=file_path.stat().st_size,
            content_type="application/pdf",
            md5_hash=document_data.get("md5_hash"),
            created_at=datetime.fromtimestamp(file_path.stat().st_ctime, tz=timezone.utc),
            updated_at=datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc),
            metadata=file_metadata,
            storage_url=f"file://{file_path.absolute()}",
            download_url=f"file://{file_path.absolute()}"
        )
