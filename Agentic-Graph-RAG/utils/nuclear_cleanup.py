#!/usr/bin/env python3
"""
Nuclear ChromaDB Cleanup Utility

This utility should be run when the API server is STOPPED to completely 
remove ChromaDB physical files. It's designed for maintenance windows
when you want to completely reset the vector store.

Usage:
  python utils/nuclear_cleanup.py [--confirm]
"""

import os
import sys
import shutil
import time
import argparse
from pathlib import Path

# Add src to path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def check_server_running():
    """Check if the API server is running"""
    try:
        import requests
        response = requests.get('http://localhost:8001/health', timeout=2)
        return response.status_code == 200
    except:
        return False

def get_chromadb_stats():
    """Get ChromaDB statistics if server is running"""
    try:
        import requests
        response = requests.get('http://localhost:8001/database/statistics', timeout=5)
        if response.status_code == 200:
            stats = response.json()['statistics']
            return stats.get('chromadb_vectors', 'unknown'), stats.get('chromadb_size_bytes', 'unknown')
    except:
        pass
    return 'unknown', 'unknown'

def check_files_directly(chroma_path):
    """Check ChromaDB files directly"""
    if not chroma_path.exists():
        return 0, 0, "No ChromaDB directory"
    
    files = list(chroma_path.rglob("*"))
    file_count = len([f for f in files if f.is_file()])
    total_size = sum(f.stat().st_size for f in files if f.is_file())
    
    return file_count, total_size, f"{file_count} files, {total_size:,} bytes"

def nuclear_cleanup(chroma_path, dry_run=False):
    """Perform nuclear cleanup of ChromaDB files"""
    if not chroma_path.exists():
        print("   ✅ ChromaDB directory doesn't exist - nothing to clean")
        return True, 0, 0
    
    print(f"   🎯 Target directory: {chroma_path}")
    
    # Check what we're about to delete
    files = list(chroma_path.rglob("*"))
    file_count = len([f for f in files if f.is_file()])
    total_size = sum(f.stat().st_size for f in files if f.is_file())
    
    print(f"   📁 Found: {file_count} files, {total_size:,} bytes")
    
    if dry_run:
        print("   🔍 DRY RUN - Would delete:")
        for file_path in files:
            if file_path.is_file():
                print(f"     - {file_path}")
        return True, file_count, total_size
    
    # Actual deletion
    try:
        # Strategy 1: Try complete directory removal
        print("   🗑️  Attempting complete directory removal...")
        shutil.rmtree(chroma_path)
        chroma_path.mkdir(parents=True, exist_ok=True)
        print("   🎉 SUCCESS: Complete directory removal successful")
        return True, file_count, total_size
        
    except Exception as e:
        print(f"   ⚠️  Directory removal failed: {e}")
        print("   🔧 Trying individual file deletion...")
        
        # Strategy 2: Individual file deletion
        files_deleted = 0
        files_failed = 0
        
        for file_path in files:
            if file_path.is_file():
                try:
                    # Try to change permissions first
                    try:
                        import stat
                        file_path.chmod(stat.S_IWRITE)
                    except:
                        pass
                    
                    file_path.unlink()
                    files_deleted += 1
                    print(f"     ✅ Deleted: {file_path.name}")
                    
                except Exception as fe:
                    files_failed += 1
                    print(f"     ❌ Failed: {file_path.name} - {fe}")
        
        # Remove empty directories
        for dir_path in sorted(files, key=lambda p: len(str(p)), reverse=True):
            if dir_path.is_dir():
                try:
                    dir_path.rmdir()
                    print(f"     📁 Removed directory: {dir_path.name}")
                except:
                    pass
        
        # Try to remove main directory
        try:
            chroma_path.rmdir()
            chroma_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Partial success: {files_deleted} files deleted, {files_failed} failed")
            return files_deleted > 0, files_deleted, files_failed
        except:
            print(f"   ⚠️  Partial cleanup: {files_deleted} files deleted, {files_failed} failed, directory remains")
            return files_deleted > 0, files_deleted, files_failed

def main():
    parser = argparse.ArgumentParser(description='Nuclear ChromaDB Cleanup Utility')
    parser.add_argument('--confirm', action='store_true', help='Actually perform the cleanup')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    parser.add_argument('--force', action='store_true', help='Force cleanup even if server is running (not recommended)')
    
    args = parser.parse_args()
    
    print("☢️  NUCLEAR CHROMADB CLEANUP UTILITY")
    print("=" * 50)
    
    # Get ChromaDB path
    try:
        from config import VECTOR_STORE_PATH
        chroma_path = Path(VECTOR_STORE_PATH)
        print(f"📂 ChromaDB Path: {chroma_path}")
    except Exception as e:
        print(f"❌ Could not load config: {e}")
        print("   Make sure you're running this from the project root")
        return 1
    
    # Check if server is running
    server_running = check_server_running()
    print(f"🌐 API Server: {'RUNNING' if server_running else 'STOPPED'}")
    
    if server_running:
        vectors, size = get_chromadb_stats()
        print(f"📊 Current vectors: {vectors}")
        print(f"📊 Current size: {size:,} bytes" if isinstance(size, int) else f"📊 Current size: {size}")
        
        if not args.force:
            print("\n⚠️  WARNING: API server is running!")
            print("   For safe cleanup, stop the server first with Ctrl+C")
            print("   Or use --force to attempt cleanup anyway (may fail)")
            if not args.dry_run:
                return 1
    
    # Check current file state
    file_count, total_size, file_desc = check_files_directly(chroma_path)
    print(f"📁 Current files: {file_desc}")
    
    if file_count == 0:
        print("✅ No ChromaDB files found - already clean!")
        return 0
    
    # Show what will happen
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No files will be deleted")
        success, deleted, failed = nuclear_cleanup(chroma_path, dry_run=True)
        return 0
    
    if not args.confirm:
        print("\n⚠️  This will PERMANENTLY DELETE all ChromaDB files!")
        print("   Use --confirm to actually perform the cleanup")
        print("   Use --dry-run to see what would be deleted")
        return 1
    
    # Perform nuclear cleanup
    print("\n☢️  PERFORMING NUCLEAR CLEANUP...")
    print("   ⚡ This may take a moment...")
    
    start_time = time.time()
    success, deleted, failed = nuclear_cleanup(chroma_path, dry_run=False)
    cleanup_time = time.time() - start_time
    
    print(f"\n📈 CLEANUP RESULTS (completed in {cleanup_time:.2f}s):")
    if success:
        print("   🎉 NUCLEAR CLEANUP SUCCESSFUL!")
        if isinstance(deleted, int) and isinstance(failed, int):
            print(f"   📊 Files processed: {deleted} deleted, {failed} failed")
        else:
            print(f"   📊 Total cleaned: {deleted} files, {failed} bytes")
    else:
        print("   ❌ Nuclear cleanup failed")
        return 1
    
    # Check final state
    final_count, final_size, final_desc = check_files_directly(chroma_path)
    print(f"   📁 Final state: {final_desc}")
    
    if final_count == 0:
        print("   ✅ ALL FILES SUCCESSFULLY DELETED!")
    else:
        print(f"   ⚠️  {final_count} files remain (may be locked)")
    
    print("\n🔄 After cleanup, restart your API server to rebuild ChromaDB from scratch")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 