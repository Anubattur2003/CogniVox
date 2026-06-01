"""
Database cleanup command for CogniVox CLI.
"""
import os
import sys
import shutil
import time
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.gcp_bucket import get_cached_storage_manager
from src.utils.config_loader import ConfigLoader


def cleanup_command(args):
    """
    Clean up all database components.
    
    Args:
        args: Command line arguments with cleanup options.
    """
    print("🧹 CogniVox Database Cleanup")
    print("=" * 50)
    
    if not args.confirm:
        print("⚠️  WARNING: This will permanently delete ALL data!")
        print("   - ChromaDB vector store")
        print("   - Neo4j graph database")
        if args.include_local_data:
            print("   - Local document storage")
        if args.include_gcp_data:
            print("   - GCP bucket data")
        if args.include_temp_files:
            print("   - Temporary files")
        print()
        
        confirm = input("Are you sure you want to proceed? Type 'YES' to confirm: ")
        if confirm != "YES":
            print("❌ Cleanup cancelled.")
            return False
    
    cleaned_components = []
    errors = []
    statistics = {}
    
    try:
        print("🚀 Starting comprehensive database cleanup...")
        
        # Initialize configuration
        config_loader = ConfigLoader(config_file="config.yaml")
        config = config_loader.get_all()
        storage_manager = get_cached_storage_manager(config)
        
        # 1. Clean ChromaDB Vector Store
        try:
            print("\n📊 Cleaning ChromaDB vector store...")
            from src.config import VECTOR_STORE_PATH
            import gc
            import time
            
            # Get vector count before cleanup (safely)
            vector_count_before = 'unknown'
            try:
                from src.graph_db.vector_store import get_vector_store
                vector_store = get_vector_store()
                if hasattr(vector_store, 'collection'):
                    vector_count_before = vector_store.collection.count()
                    statistics['chromadb_vectors_before'] = vector_count_before
                    print(f"   Found {vector_count_before} vectors to clean")
                
                # Properly close the vector store connection
                if hasattr(vector_store, 'client'):
                    try:
                        del vector_store.collection
                        del vector_store.client
                    except:
                        pass
                del vector_store
                
            except Exception as e:
                statistics['chromadb_vectors_before'] = 'unknown'
                print(f"   Could not count vectors safely: {e}")
            
            # Force garbage collection to release any remaining references
            gc.collect()
            time.sleep(0.5)  # Give time for cleanup
            
            # Now attempt to clean ChromaDB with robust error handling
            chroma_path = Path(VECTOR_STORE_PATH)
            
            if chroma_path.exists():
                # Strategy 1: Try direct deletion
                try:
                    shutil.rmtree(chroma_path)
                    print(f"   ✅ Successfully removed ChromaDB directory: {chroma_path}")
                except PermissionError as pe:
                    print(f"   ⚠️  Permission error on direct deletion, trying alternative approach...")
                    
                    # Strategy 2: Try to delete individual files with retries
                    files_deleted = 0
                    files_failed = 0
                    
                    for file_path in chroma_path.rglob('*'):
                        if file_path.is_file():
                            for attempt in range(3):  # 3 retry attempts
                                try:
                                    file_path.unlink()
                                    files_deleted += 1
                                    break
                                except (PermissionError, OSError) as e:
                                    if attempt == 2:  # Last attempt
                                        files_failed += 1
                                    else:
                                        time.sleep(0.1 * (attempt + 1))  # Increasing delay
                    
                    # Try to remove empty directories
                    for dir_path in sorted(chroma_path.rglob('*'), key=lambda p: len(str(p)), reverse=True):
                        if dir_path.is_dir():
                            try:
                                dir_path.rmdir()
                            except OSError:
                                pass  # Directory not empty, that's ok
                    
                    # Try to remove the main directory
                    try:
                        chroma_path.rmdir()
                        print(f"   ✅ Cleaned ChromaDB directory: {files_deleted} files deleted, {files_failed} files failed")
                    except OSError:
                        print(f"   ⚠️  Could not remove main directory, but cleaned {files_deleted} files")
                
                except Exception as e:
                    print(f"   ❌ Unexpected error during ChromaDB cleanup: {e}")
                    raise
            
            # Recreate the directory structure
            chroma_path.mkdir(parents=True, exist_ok=True)
            print("   ✅ Recreated ChromaDB directory structure")
            
            cleaned_components.append("ChromaDB Vector Store")
            statistics['chromadb_status'] = 'cleaned'
            
        except Exception as e:
            error_msg = f"ChromaDB cleanup failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            errors.append(error_msg)
            
            # Try alternative cleanup method - individual collection reset
            try:
                print("   🔄 Attempting alternative ChromaDB cleanup method...")
                import chromadb
                from chromadb.config import Settings
                
                # Create a new client and try to delete collections
                temp_client = chromadb.PersistentClient(
                    path=str(VECTOR_STORE_PATH),
                    settings=Settings(anonymized_telemetry=False)
                )
                
                # List and delete all collections
                collections = temp_client.list_collections()
                for collection in collections:
                    try:
                        temp_client.delete_collection(collection.name)
                        print(f"   ✅ Deleted ChromaDB collection: {collection.name}")
                    except Exception as ce:
                        print(f"   ⚠️  Failed to delete collection {collection.name}: {ce}")
                
                del temp_client
                gc.collect()
                
                cleaned_components.append("ChromaDB Vector Store (Alternative Method)")
                statistics['chromadb_status'] = 'partially_cleaned'
                
                # Remove the error from the list since we succeeded with alternative method
                if error_msg in errors:
                    errors.remove(error_msg)
                
            except Exception as alt_e:
                print(f"   ❌ Alternative ChromaDB cleanup also failed: {alt_e}")
                errors.append(f"Alternative ChromaDB cleanup failed: {str(alt_e)}")
        
        # 2. Clean Neo4j Database
        try:
            print("\n🔗 Cleaning Neo4j database...")
            from src.graph_db.neo4j_adapter import Neo4jAdapter
            
            neo4j_adapter = Neo4jAdapter()
            
            # Get counts before cleanup
            try:
                result = neo4j_adapter.graph.run("MATCH (n) RETURN count(n) as node_count").data()
                node_count = result[0]['node_count'] if result else 0
                statistics['neo4j_nodes_before'] = node_count
                
                result = neo4j_adapter.graph.run("MATCH ()-[r]->() RETURN count(r) as rel_count").data()
                rel_count = result[0]['rel_count'] if result else 0
                statistics['neo4j_relationships_before'] = rel_count
                
                print(f"   Found {node_count} nodes and {rel_count} relationships to clean")
            except Exception as e:
                statistics['neo4j_nodes_before'] = 'unknown'
                statistics['neo4j_relationships_before'] = 'unknown'
                print(f"   Could not count Neo4j entities: {e}")
            
            # Delete all nodes and relationships
            cleanup_query = """
            MATCH (n)
            DETACH DELETE n
            """
            neo4j_adapter.graph.run(cleanup_query)
            
            # Verify cleanup
            result = neo4j_adapter.graph.run("MATCH (n) RETURN count(n) as remaining_nodes").data()
            remaining_nodes = result[0]['remaining_nodes'] if result else 0
            
            if remaining_nodes == 0:
                print("   ✅ Neo4j database cleaned successfully")
            else:
                print(f"   ⚠️  Warning: {remaining_nodes} nodes remaining after cleanup")
            
            cleaned_components.append("Neo4j Graph Database")
            statistics['neo4j_status'] = 'cleaned'
            statistics['neo4j_remaining_nodes'] = remaining_nodes
            
        except Exception as e:
            error_msg = f"Neo4j cleanup failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            errors.append(error_msg)
        
        # 3. Clean Local Document Storage
        if args.include_local_data:
            try:
                print("\n📁 Cleaning local document storage...")
                from src.config import LOCAL_DOCUMENT_PATH, PDF_DIR
                
                local_files_cleaned = 0
                
                # Clean local document storage
                if LOCAL_DOCUMENT_PATH.exists():
                    pdf_files = list(LOCAL_DOCUMENT_PATH.rglob("*.pdf"))
                    print(f"   Found {len(pdf_files)} PDF files in local storage")
                    
                    for file_path in pdf_files:
                        try:
                            file_path.unlink()
                            local_files_cleaned += 1
                        except Exception as e:
                            print(f"   ⚠️  Failed to delete {file_path}: {e}")
                
                # Clean PDF directory
                if PDF_DIR.exists() and PDF_DIR != LOCAL_DOCUMENT_PATH:
                    pdf_files = list(PDF_DIR.rglob("*.pdf"))
                    print(f"   Found {len(pdf_files)} PDF files in PDF directory")
                    
                    for file_path in pdf_files:
                        try:
                            file_path.unlink()
                            local_files_cleaned += 1
                        except Exception as e:
                            print(f"   ⚠️  Failed to delete {file_path}: {e}")
                
                print(f"   ✅ Cleaned {local_files_cleaned} local files")
                cleaned_components.append("Local Document Storage")
                statistics['local_files_cleaned'] = local_files_cleaned
                
            except Exception as e:
                error_msg = f"Local storage cleanup failed: {str(e)}"
                print(f"   ❌ {error_msg}")
                errors.append(error_msg)
        
        # 4. Clean Local Storage Data  
        if args.include_gcp_data:  # Keep parameter name for backward compatibility
            try:
                print("\n📁 Cleaning local storage data...")
                
                # List all documents before cleanup
                documents = storage_manager.list_documents()
                storage_files_before = len(documents)
                statistics['storage_files_before'] = storage_files_before
                print(f"   Found {storage_files_before} files in local storage")
                
                storage_files_cleaned = 0
                storage_errors = []
                
                # Delete all documents
                for document in documents:
                    try:
                        result = storage_manager.delete_document(document.blob_name)
                        if result.status == "success":
                            storage_files_cleaned += 1
                            if storage_files_cleaned % 10 == 0:  # Progress update every 10 files
                                print(f"   Progress: {storage_files_cleaned}/{storage_files_before} files deleted")
                        else:
                            storage_errors.append(f"Failed to delete {document.blob_name}: {result.message}")
                    except Exception as e:
                        storage_errors.append(f"Error deleting {document.blob_name}: {str(e)}")
                
                print(f"   ✅ Cleaned {storage_files_cleaned} storage files")
                cleaned_components.append("Local Storage Documents")
                statistics['storage_files_cleaned'] = storage_files_cleaned
                
                if storage_errors:
                    for error in storage_errors[:3]:  # Show first 3 errors
                        print(f"   ⚠️  {error}")
                    if len(storage_errors) > 3:
                        print(f"   ⚠️  ... and {len(storage_errors) - 3} more storage errors")
                    errors.extend(storage_errors)
                
            except Exception as e:
                error_msg = f"Local storage cleanup failed: {str(e)}"
                print(f"   ❌ {error_msg}")
                errors.append(error_msg)
        # Note: GCP storage has been removed, all storage is now local
        
        # 5. Clean Temporary Files
        if args.include_temp_files:
            try:
                print("\n🗑️  Cleaning temporary files...")
                
                temp_files_cleaned = 0
                temp_dirs = ["temp_uploads", "temp_downloads", "downloads", "temp"]
                
                for temp_dir in temp_dirs:
                    temp_path = Path(temp_dir)
                    if temp_path.exists():
                        try:
                            file_count = len([f for f in temp_path.rglob("*") if f.is_file()])
                            print(f"   Removing directory {temp_path} with {file_count} files")
                            shutil.rmtree(temp_path)
                            temp_files_cleaned += file_count
                        except Exception as e:
                            print(f"   ⚠️  Failed to remove {temp_path}: {e}")
                
                # Clean any .tmp files
                tmp_files = list(Path(".").rglob("*.tmp"))
                if tmp_files:
                    print(f"   Found {len(tmp_files)} .tmp files to clean")
                    for tmp_file in tmp_files:
                        try:
                            tmp_file.unlink()
                            temp_files_cleaned += 1
                        except Exception as e:
                            print(f"   ⚠️  Failed to delete {tmp_file}: {e}")
                
                print(f"   ✅ Cleaned {temp_files_cleaned} temporary files")
                cleaned_components.append("Temporary Files")
                statistics['temp_files_cleaned'] = temp_files_cleaned
                
            except Exception as e:
                error_msg = f"Temporary files cleanup failed: {str(e)}"
                print(f"   ❌ {error_msg}")
                errors.append(error_msg)
        
        # Summary
        print(f"\n{'=' * 50}")
        print("🎉 Database Cleanup Summary")
        print(f"{'=' * 50}")
        
        if cleaned_components:
            print("✅ Cleaned Components:")
            for component in cleaned_components:
                print(f"   • {component}")
        
        if errors:
            print(f"\n⚠️  Errors ({len(errors)}):")
            for error in errors[:5]:  # Limit to first 5 errors
                print(f"   • {error}")
            if len(errors) > 5:
                print(f"   • ... and {len(errors) - 5} more errors")
        
        print(f"\n📊 Statistics:")
        for key, value in statistics.items():
            print(f"   • {key}: {value}")
        
        success = len(errors) == 0
        if success:
            print(f"\n🎯 Database cleanup completed successfully!")
        else:
            print(f"\n⚠️  Database cleanup completed with {len(errors)} error(s)")
        
        return success
        
    except Exception as e:
        print(f"\n💥 Critical error during database cleanup: {str(e)}")
        return False 