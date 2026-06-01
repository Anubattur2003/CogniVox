"""
CogniVox GraphRAG Client SDK.

This module provides a client for interacting with the CogniVox GraphRAG API.
"""
import requests
import json
from typing import Dict, List, Any, Optional
import os
from pathlib import Path


class CogniVoxClient:
    """Client for the CogniVox GraphRAG API."""
    
    def __init__(self, base_url: str = None):
        """
        Initialize the CogniVox client.
        
        Args:
            base_url: The base URL of the CogniVox API. If not provided, 
                      will use COGNIVOX_API_URL environment variable or default to localhost.
        """
        self.base_url = base_url or os.getenv("COGNIVOX_API_URL", "http://localhost:8000")
        
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the CogniVox service.
        
        Returns:
            Dict containing health status information.
        """
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def query(
        self, 
        query: str, 
        mode: str = "hybrid", 
        n_results: int = 20, 
        format: str = "text",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query the knowledge graph.
        
        Args:
            query: The query to run
            mode: Search mode (semantic, keyword, hybrid)
            n_results: Number of results to return
            format: Response format (text, json, markdown)
            user_id: Optional user ID to search user-specific documents along with global documents.
                     If not provided, only search global documents.
            
        Returns:
            Dict containing the query response.
        """
        payload = {
            "query": query,
            "mode": mode,
            "n_results": n_results,
            "format": format
        }
        
        # Add user_id to payload if provided and not empty
        if user_id and user_id.strip():
            payload["user_id"] = user_id
        
        response = requests.post(f"{self.base_url}/query", json=payload)
        response.raise_for_status()
        return response.json()
    
    def ingest(
        self, 
        pdf_path: str, 
        force: bool = False, 
        extraction_method: str = "auto",
        user_id: Optional[str] = None,
        use_llamaindex: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Ingest a PDF document into the knowledge graph.
        
        Args:
            pdf_path: Path to the PDF file
            force: Whether to force re-ingestion
            extraction_method: Method for extracting text (auto, pdfminer, pypdf2, ocr)
            user_id: Optional user ID to associate with this document.
                     If provided, the document will be isolated to this user.
                     If not provided, the document will be available to all users (global).
            use_llamaindex: Optional flag to use LlamaIndex processing (overrides config).
            
        Returns:
            Dict containing ingest status information.
        """
        with open(pdf_path, "rb") as f:
            files = {"file": (Path(pdf_path).name, f, "application/pdf")}
            params = {
                "force": force,
                "extraction_method": extraction_method
            }
            
            # Add user_id to params if provided and not empty
            if user_id and user_id.strip():
                params["user_id"] = user_id
                
            # Add use_llamaindex to params if provided
            if use_llamaindex is not None:
                params["use_llamaindex"] = use_llamaindex
                
            response = requests.post(
                f"{self.base_url}/ingest",
                files=files,
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    def ingest_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        force: bool = False,
        extraction_method: str = "auto",
        max_workers: int = 4,
        user_id: Optional[str] = None,
        use_llamaindex: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Ingest all PDF documents from a directory into the knowledge graph.
        
        Args:
            directory_path: Path to a directory containing PDF files to process
            recursive: Whether to search for PDFs in subdirectories
            force: Whether to force re-ingestion if document already exists
            extraction_method: Method for extracting text (auto, pdfminer, pypdf2, ocr)
            max_workers: Maximum number of parallel ingestion processes
            user_id: Optional user ID to associate with these documents.
                     If provided, the documents will be isolated to this user.
                     If not provided, the documents will be available to all users (global).
            use_llamaindex: Optional flag to use LlamaIndex processing (overrides config).
            
        Returns:
            Dict containing ingest status information.
        """
        params = {
            "directory_path": directory_path,
            "recursive": recursive,
            "force": force,
            "extraction_method": extraction_method,
            "max_workers": max_workers
        }
        
        # Add user_id to params if provided and not empty
        if user_id and user_id.strip():
            params["user_id"] = user_id
            
        # Add use_llamaindex to params if provided
        if use_llamaindex is not None:
            params["use_llamaindex"] = use_llamaindex
            
        response = requests.post(
            f"{self.base_url}/ingest/directory",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def remove_document(self, document_id: str, force: bool = False, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Remove a document from the knowledge graph.
        
        Args:
            document_id: ID of the document to remove
            force: Whether to skip confirmation
            user_id: Optional user ID for user-specific document removal.
                     If provided, only the document for this user will be removed.
                     If not provided, only global documents will be removed.
            
        Returns:
            Dict containing removal status information.
        """
        params = {"force": force}
        
        # Add user_id to params if provided and not empty
        if user_id and user_id.strip():
            params["user_id"] = user_id
            
        response = requests.delete(
            f"{self.base_url}/documents/{document_id}",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def visualize(
        self, 
        output_format: str = "html", 
        node_limit: int = 100
    ) -> Dict[str, Any]:
        """
        Generate a visualization of the knowledge graph.
        
        Args:
            output_format: Output format (html, png)
            node_limit: Maximum number of nodes to display
            
        Returns:
            Dict containing visualization information.
        """
        response = requests.get(
            f"{self.base_url}/visualize",
            params={
                "output_format": output_format,
                "node_limit": node_limit
            }
        )
        response.raise_for_status()
        return response.json()
    
    def export(self, format: str = "json") -> Dict[str, Any]:
        """
        Export the knowledge graph.
        
        Args:
            format: Export format (json, graphml, rdf)
            
        Returns:
            Dict containing export information.
        """
        response = requests.get(
            f"{self.base_url}/export",
            params={"format": format}
        )
        response.raise_for_status()
        return response.json()
    
 