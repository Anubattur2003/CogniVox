"""
Local Storage integration for CogniVox GraphRAG
"""

__version__ = "1.0.0"
__description__ = "Local Storage integration for GraphRAG"

from .local_storage_client import LocalStorageClient
from .storage_manager import StorageManager, get_cached_storage_manager, clear_storage_manager_cache
from .models import PDFDocument, OperationResult, OperationStatus, StorageClass
from .exceptions import StorageError, AuthenticationError, ResourceNotFoundError

__all__ = [
    "LocalStorageClient",
    "StorageManager",
    "get_cached_storage_manager", 
    "clear_storage_manager_cache",
    "PDFDocument", 
    "OperationResult",
    "OperationStatus",
    "StorageClass",
    "StorageError",
    "AuthenticationError",
    "ResourceNotFoundError"
] 