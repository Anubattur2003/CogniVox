#!/usr/bin/env python3
"""
FFmpeg Installation Helper for Windows
=====================================
This script helps install ffmpeg on Windows for speech-to-text functionality.
"""

import os
import sys
import requests
import zipfile
import shutil
import subprocess
from pathlib import Path

def check_ffmpeg_installed():
    """Check if ffmpeg is already installed and accessible."""
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg is already installed and accessible!")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False

def download_ffmpeg():
    """Download ffmpeg for Windows."""
    print("🔄 Downloading FFmpeg for Windows...")
    
    # FFmpeg download URL for Windows (static build)
    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    
    try:
        # Create downloads directory
        downloads_dir = Path("downloads")
        downloads_dir.mkdir(exist_ok=True)
        
        zip_path = downloads_dir / "ffmpeg.zip"
        
        # Download ffmpeg
        response = requests.get(ffmpeg_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rDownloading... {percent:.1f}%", end="", flush=True)
        
        print(f"\n✅ Downloaded FFmpeg to {zip_path}")
        return zip_path
        
    except Exception as e:
        print(f"❌ Failed to download FFmpeg: {e}")
        return None

def extract_ffmpeg(zip_path):
    """Extract ffmpeg to a local directory."""
    print("📦 Extracting FFmpeg...")
    
    try:
        extract_dir = Path("ffmpeg")
        extract_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Find the ffmpeg.exe file
        ffmpeg_exe = None
        for root, dirs, files in os.walk(extract_dir):
            if "ffmpeg.exe" in files:
                ffmpeg_exe = Path(root) / "ffmpeg.exe"
                break
        
        if ffmpeg_exe and ffmpeg_exe.exists():
            print(f"✅ Extracted FFmpeg to {ffmpeg_exe}")
            return ffmpeg_exe
        else:
            print("❌ Could not find ffmpeg.exe in extracted files")
            return None
            
    except Exception as e:
        print(f"❌ Failed to extract FFmpeg: {e}")
        return None

def setup_ffmpeg_path(ffmpeg_exe):
    """Setup ffmpeg in PATH or create a local bin directory."""
    print("🔧 Setting up FFmpeg...")
    
    try:
        # Create a local bin directory
        bin_dir = Path("bin")
        bin_dir.mkdir(exist_ok=True)
        
        # Copy ffmpeg to bin directory
        local_ffmpeg = bin_dir / "ffmpeg.exe"
        shutil.copy2(ffmpeg_exe, local_ffmpeg)
        
        # Add to current session PATH
        current_path = os.environ.get("PATH", "")
        bin_dir_abs = bin_dir.absolute()
        os.environ["PATH"] = f"{bin_dir_abs};{current_path}"
        
        print(f"✅ FFmpeg copied to {local_ffmpeg}")
        print(f"✅ Added {bin_dir_abs} to PATH for current session")
        
        # Test if it works
        try:
            result = subprocess.run([str(local_ffmpeg), "-version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ FFmpeg installation verified!")
                return True
        except Exception as test_error:
            print(f"⚠️  FFmpeg test failed: {test_error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to setup FFmpeg: {e}")
        return False

def cleanup_downloads():
    """Clean up downloaded files."""
    try:
        downloads_dir = Path("downloads")
        if downloads_dir.exists():
            shutil.rmtree(downloads_dir)
            print("🧹 Cleaned up download files")
    except Exception as e:
        print(f"⚠️  Failed to cleanup: {e}")

def main():
    """Main installation function."""
    print("🎤 FFmpeg Installation Helper for Windows")
    print("=" * 50)
    
    # Check if already installed
    if check_ffmpeg_installed():
        return True
    
    print("FFmpeg not found. Installing...")
    
    # Download ffmpeg
    zip_path = download_ffmpeg()
    if not zip_path:
        return False
    
    # Extract ffmpeg
    ffmpeg_exe = extract_ffmpeg(zip_path)
    if not ffmpeg_exe:
        return False
    
    # Setup ffmpeg
    success = setup_ffmpeg_path(ffmpeg_exe)
    
    # Cleanup
    cleanup_downloads()
    
    if success:
        print("\n🎉 FFmpeg installation completed!")
        print("\n📝 Next steps:")
        print("1. Restart your terminal/command prompt")
        print("2. Test speech-to-text functionality in CogniVox")
        print("3. FFmpeg is now available for local whisper transcription")
        
        print("\n🔧 Manual PATH setup (if needed):")
        bin_dir_abs = Path("bin").absolute()
        print(f"Add this to your system PATH: {bin_dir_abs}")
    else:
        print("\n❌ FFmpeg installation failed!")
        print("Please download FFmpeg manually from: https://ffmpeg.org/download.html")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 