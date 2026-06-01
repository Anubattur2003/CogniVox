#!/usr/bin/env python3
"""
GCP Storage CLI for CogniVox GraphRAG
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.gcp_bucket import get_cached_storage_manager
from src.utils.config_loader import ConfigLoader


def main():
    parser = argparse.ArgumentParser(description="GCP Storage CLI for CogniVox GraphRAG")
    parser.add_argument("--config", default="config.yaml", help="Configuration file path")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload a PDF document")
    upload_parser.add_argument("file_path", help="Path to PDF file to upload")
    upload_parser.add_argument("--user-id", help="User ID to associate with document")
    upload_parser.add_argument("--doc-id", help="Custom document ID")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List documents")
    list_parser.add_argument("--user-id", help="User ID to filter documents")
    list_parser.add_argument("--limit", type=int, default=20, help="Maximum number of documents")
    
    # Download command
    download_parser = subparsers.add_parser("download", help="Download a document")
    download_parser.add_argument("document_id", help="Document ID to download")
    download_parser.add_argument("--user-id", help="User ID for user-specific documents")
    download_parser.add_argument("--output", help="Output file path")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a document")
    delete_parser.add_argument("document_id", help="Document ID to delete")
    delete_parser.add_argument("--user-id", help="User ID for user-specific documents")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show storage status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize storage manager
    try:
        config_loader = ConfigLoader(config_file=args.config)
        config = config_loader.get_all()
        storage_manager = get_cached_storage_manager(config)
        
        print(f"Storage Type: {'GCP Bucket' if storage_manager.use_gcp else 'Local Storage'}")
        
    except Exception as e:
        print(f"Error initializing storage manager: {e}")
        return
    
    # Execute commands
    try:
        if args.command == "upload":
            result = storage_manager.upload_document(
                file_path=args.file_path,
                document_id=args.doc_id,
                user_id=args.user_id
            )
            
            if result.is_success:
                print(f"✓ Upload successful: {result.message}")
                if result.document:
                    print(f"  File size: {result.document.file_size} bytes")
                    print(f"  Storage path: {result.document.full_path}")
            else:
                print(f"✗ Upload failed: {result.message}")
        
        elif args.command == "list":
            documents = storage_manager.list_documents(
                user_id=args.user_id,
                limit=args.limit
            )
            
            if documents:
                print(f"Found {len(documents)} documents:")
                for doc in documents:
                    print(f"  - {doc.original_filename}")
                    print(f"    Size: {doc.file_size} bytes")
                    print(f"    Created: {doc.created_at}")
                    print(f"    Path: {doc.full_path}")
                    print()
            else:
                print("No documents found")
        
        elif args.command == "download":
            result = storage_manager.download_document(
                document_path=args.document_id,
                local_path=args.output,
                user_id=args.user_id
            )
            
            if result.is_success:
                print(f"✓ Download successful: {result.message}")
                if result.data:
                    print(f"  Local path: {result.data.get('local_path')}")
                    print(f"  File size: {result.data.get('file_size')} bytes")
            else:
                print(f"✗ Download failed: {result.message}")
        
        elif args.command == "delete":
            result = storage_manager.delete_document(
                document_path=args.document_id,
                user_id=args.user_id
            )
            
            if result.is_success:
                print(f"✓ Delete successful: {result.message}")
            else:
                print(f"✗ Delete failed: {result.message}")
        
        elif args.command == "status":
            print(f"Storage Configuration:")
            print(f"  Type: {'GCP Bucket' if storage_manager.use_gcp else 'Local Storage'}")
            
            if storage_manager.use_gcp and storage_manager._gcp_client:
                print(f"  Bucket: {storage_manager._gcp_client.bucket_name}")
                print(f"  Default Folder: {storage_manager._gcp_client.default_folder}")
            elif not storage_manager.use_gcp:
                print(f"  Local Path: {storage_manager.local_path}")
            
            # List some documents
            try:
                documents = storage_manager.list_documents(limit=5)
                print(f"\nRecent Documents ({len(documents)}):")
                for doc in documents[:5]:
                    print(f"  - {doc.original_filename} ({doc.file_size} bytes)")
            except Exception as e:
                print(f"  Error listing documents: {e}")
                
    except Exception as e:
        print(f"Error executing command: {e}")


if __name__ == "__main__":
    main() 