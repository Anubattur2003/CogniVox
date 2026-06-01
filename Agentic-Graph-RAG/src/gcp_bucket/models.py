"""
Data models for the GCP Storage integration
"""

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, validator, ConfigDict
from dataclasses import dataclass


class OperationStatus(str, Enum):
    """Enumeration for operation status"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"


class StorageClass(str, Enum):
    """Google Cloud Storage classes"""
    STANDARD = "STANDARD"
    NEARLINE = "NEARLINE"
    COLDLINE = "COLDLINE"
    ARCHIVE = "ARCHIVE"


class PDFMetadata(BaseModel):
    """Model for PDF metadata"""
    model_config = ConfigDict(extra='allow')
    
    # Core metadata
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    
    # Custom metadata
    department: Optional[str] = None
    project: Optional[str] = None
    version: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # System metadata
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    file_hash: Optional[str] = None
    upload_timestamp: Optional[datetime] = None


class PDFDocument(BaseModel):
    """Model representing a PDF document"""
    model_config = ConfigDict(extra='forbid')
    
    # Identification
    blob_name: str = Field(..., description="Unique blob name in storage")
    original_filename: str = Field(..., description="Original filename")
    
    # Storage information
    bucket_name: str = Field(..., description="Storage bucket/directory name")
    folder_path: Optional[str] = Field(None, description="Folder path in storage")
    storage_class: StorageClass = Field(StorageClass.STANDARD, description="Storage class")
    
    # File properties
    file_size: int = Field(..., gt=0, description="File size in bytes")
    content_type: str = Field(default="application/pdf", description="MIME type")
    md5_hash: Optional[str] = Field(None, description="MD5 hash of file")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    
    # Metadata
    metadata: PDFMetadata = Field(default_factory=PDFMetadata, description="PDF metadata")
    
    # URLs
    storage_url: Optional[str] = Field(None, description="Storage URL")
    download_url: Optional[str] = Field(None, description="Download URL if available")
    
    @validator('blob_name')
    def validate_blob_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Blob name cannot be empty")
        return v.strip()
    
    @property
    def file_extension(self) -> str:
        """Get file extension"""
        return Path(self.original_filename).suffix.lower()
    
    @property
    def filename(self) -> str:
        """Get just the filename from blob_name"""
        return Path(self.blob_name).name
    
    @property
    def full_path(self) -> str:
        """Get full path in bucket (same as blob_name now)"""
        return self.blob_name


class OperationResult(BaseModel):
    """Model for operation results"""
    model_config = ConfigDict(extra='allow')
    
    status: OperationStatus = Field(..., description="Operation status")
    message: str = Field(..., description="Result message")
    
    # Operation details
    operation_type: str = Field(..., description="Type of operation performed")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Operation timestamp")
    duration_ms: Optional[int] = Field(None, description="Operation duration in milliseconds")
    
    # Data
    data: Optional[Dict[str, Any]] = Field(None, description="Operation result data")
    document: Optional[PDFDocument] = Field(None, description="Associated PDF document")
    
    # Error information
    error_code: Optional[str] = Field(None, description="Error code if failed")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    
    @property
    def is_success(self) -> bool:
        """Check if operation was successful"""
        return self.status == OperationStatus.SUCCESS
    
    @property
    def is_failed(self) -> bool:
        """Check if operation failed"""
        return self.status == OperationStatus.FAILED


class UploadRequest(BaseModel):
    """Model for upload requests"""
    model_config = ConfigDict(extra='forbid')
    
    local_file_path: Union[str, Path] = Field(..., description="Local file path")
    blob_name: Optional[str] = Field(None, description="Custom blob name")
    folder_path: Optional[str] = Field(None, description="Folder path in bucket")
    
    # Upload options
    overwrite: bool = Field(False, description="Whether to overwrite existing files")
    storage_class: StorageClass = Field(StorageClass.STANDARD, description="Storage class")
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(None, description="Custom metadata")
    
    @validator('local_file_path')
    def validate_file_path(cls, v):
        path = Path(v)
        if not path.exists():
            raise ValueError(f"File does not exist: {path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        if path.suffix.lower() != '.pdf':
            raise ValueError(f"File must be a PDF: {path}")
        return path


class DownloadRequest(BaseModel):
    """Model for download requests"""
    model_config = ConfigDict(extra='forbid')
    
    blob_name: str = Field(..., description="Blob name to download")
    local_file_path: Optional[Union[str, Path]] = Field(None, description="Local destination path")
    
    # Download options
    overwrite: bool = Field(False, description="Whether to overwrite existing local files")
    create_dirs: bool = Field(True, description="Create directories if they don't exist") 