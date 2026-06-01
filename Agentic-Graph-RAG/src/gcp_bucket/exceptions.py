"""
Custom exceptions for the GCP Storage integration
"""

from typing import Optional, Any


class PDFPipelineError(Exception):
    """Base exception class for PDF Pipeline errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        base_msg = self.message
        if self.error_code:
            base_msg = f"[{self.error_code}] {base_msg}"
        if self.details:
            base_msg += f" | Details: {self.details}"
        return base_msg


class StorageError(PDFPipelineError):
    """Raised when there are storage-related errors"""
    
    def __init__(self, message: str, operation: Optional[str] = None, blob_name: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="STORAGE_ERROR", **kwargs)
        self.operation = operation
        self.blob_name = blob_name


class AuthenticationError(PDFPipelineError):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, error_code="AUTH_ERROR", **kwargs)


class ResourceNotFoundError(PDFPipelineError):
    """Raised when a requested resource is not found"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="NOT_FOUND", **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id


class NetworkError(PDFPipelineError):
    """Raised when network-related errors occur"""
    
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="NETWORK_ERROR", **kwargs)
        self.operation = operation 