#!/usr/bin/env python3
"""
Setup script for CogniVox Speech-to-Text service.

This script helps users set up the required Whisper model for speech-to-text functionality.
"""
import os
import subprocess
import sys
import time
import requests
import json
import platform

def check_ollama_running():
    """Check if Ollama service is running."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def install_whisper_model():
    """Install the dimavz/whisper-tiny model in Ollama."""
    print("🔄 Installing Whisper model (dimavz/whisper-tiny)...")
    print("This may take a few minutes depending on your internet connection.")
    
    try:
        # Run ollama pull command
        result = subprocess.run(
            ["ollama", "pull", "dimavz/whisper-tiny"],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            print("✅ Whisper model installed successfully!")
            return True
        else:
            print(f"❌ Failed to install Whisper model: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Installation timed out. Please try again.")
        return False
    except FileNotFoundError:
        print("❌ Ollama command not found. Please install Ollama first.")
        print("Visit: https://ollama.ai/download")
        return False
    except Exception as e:
        print(f"❌ Installation failed: {str(e)}")
        return False

def check_model_availability():
    """Check if the Whisper model is available."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in models]
            
            whisper_available = any("whisper" in name.lower() for name in model_names)
            dimavz_available = any("dimavz/whisper-tiny" in name for name in model_names)
            
            print(f"📋 Found {len(models)} models in Ollama:")
            for name in model_names[:5]:  # Show first 5 models
                print(f"   - {name}")
            if len(models) > 5:
                print(f"   ... and {len(models) - 5} more")
            
            if dimavz_available:
                print("✅ dimavz/whisper-tiny model is available!")
                return True
            elif whisper_available:
                print("⚠️  Found other Whisper models, but not dimavz/whisper-tiny")
                return False
            else:
                print("❌ No Whisper models found")
                return False
        else:
            print(f"❌ Failed to check models: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to check model availability: {str(e)}")
        return False

def install_python_dependencies():
    """Install optional Python whisper as fallback."""
    print("\n🔄 Installing Python whisper as fallback (optional)...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "openai-whisper"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print("✅ Python whisper installed successfully!")
            return True
        else:
            print(f"⚠️  Python whisper installation failed: {result.stderr}")
            print("This is optional - the service will work without it.")
            return False
            
    except Exception as e:
        print(f"⚠️  Python whisper installation failed: {str(e)}")
        print("This is optional - the service will work without it.")
        return False

def install_ffmpeg_cross_platform():
    """Install FFmpeg cross-platform for whisper audio processing."""
    print(f"\n🔄 Installing FFmpeg for {platform.system()}...")
    
    # Check if ffmpeg is already available
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg is already installed!")
            return True
    except:
        pass
    
    # Try to run the cross-platform ffmpeg installer
    try:
        # Run the cross-platform ffmpeg installation script
        result = subprocess.run(
            [sys.executable, "install_ffmpeg_cross_platform.py"],
            timeout=600  # 10 minute timeout for download
        )
        
        if result.returncode == 0:
            print("✅ FFmpeg installation completed!")
            return True
        else:
            print("⚠️  FFmpeg automatic installation failed.")
            print_manual_ffmpeg_instructions()
            return False
            
    except Exception as e:
        print(f"⚠️  FFmpeg installation failed: {str(e)}")
        print_manual_ffmpeg_instructions()
        return False

def print_manual_ffmpeg_instructions():
    """Print platform-specific manual installation instructions."""
    system = platform.system().lower()
    
    if system == 'windows':
        print("Please install FFmpeg manually:")
        print("  Download: https://ffmpeg.org/download.html")
        print("  Or use package manager: choco install ffmpeg")
    elif system == 'linux':
        print("Please install FFmpeg manually:")
        print("  Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg")
        print("  CentOS/RHEL: sudo yum install ffmpeg")
        print("  Fedora: sudo dnf install ffmpeg")
        print("  Arch: sudo pacman -S ffmpeg")
    elif system == 'darwin':  # macOS
        print("Please install FFmpeg manually:")
        print("  Homebrew: brew install ffmpeg")
        print("  MacPorts: sudo port install ffmpeg")
    else:
        print("Please install FFmpeg for your platform: https://ffmpeg.org/download.html")

def test_transcription():
    """Test the transcription service."""
    print("\n🔍 Testing transcription service...")
    
    # Check if the service is running
    try:
        response = requests.get("http://localhost:8002/api/transcribe/status", timeout=5)
        if response.status_code == 200:
            status_data = response.json()
            print(f"📊 Service status: {status_data.get('status', 'unknown')}")
            print(f"📊 Model: {status_data.get('model', 'unknown')}")
            print(f"📊 Model available: {status_data.get('model_available', False)}")
            
            if status_data.get('model_available', False):
                print("✅ Transcription service is ready!")
                return True
            else:
                print("❌ Model not available in transcription service")
                return False
        else:
            print(f"❌ Transcription service not responding: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to test transcription service: {str(e)}")
        print("Make sure the Agentic-Memory service is running on port 8002")
        return False

def main():
    """Main setup function."""
    print("🎤 CogniVox Speech-to-Text Setup")
    print("=" * 40)
    
    # Step 1: Check if Ollama is running
    print("1. Checking Ollama service...")
    if not check_ollama_running():
        print("❌ Ollama service is not running!")
        print("Please start Ollama first:")
        print("   - On macOS/Linux: ollama serve")
        print("   - On Windows: Start Ollama from the system tray")
        sys.exit(1)
    print("✅ Ollama service is running")
    
    # Step 2: Check current model availability
    print("\n2. Checking model availability...")
    if check_model_availability():
        print("Model is already installed!")
    else:
        print("Model needs to be installed.")
        
        # Ask user if they want to install
        response = input("\nWould you like to install dimavz/whisper-tiny now? (y/n): ")
        if response.lower() in ['y', 'yes']:
            if not install_whisper_model():
                print("❌ Setup failed!")
                sys.exit(1)
        else:
            print("❌ Model installation skipped. Setup incomplete.")
            sys.exit(1)
    
    # Step 3: Install FFmpeg (Cross-platform)
    print("\n3. Installing FFmpeg for audio processing...")
    ffmpeg_success = install_ffmpeg_cross_platform()
    
    # Step 4: Optional Python whisper installation
    print("\n4. Installing Python whisper fallback...")
    whisper_success = install_python_dependencies()
    
    # Step 5: Test the service
    print("\n5. Testing transcription service...")
    test_transcription()
    
    print("\n🎉 Setup completed!")
    print("\n📝 Next steps:")
    print("1. Make sure the Agentic-Memory service is running")
    print("2. Test voice input in the frontend")
    print("3. Check logs if you encounter any issues")
    
    print("\n🔧 Troubleshooting:")
    print("- If transcription fails, check Ollama logs (Docker: docker logs agentic-ollama)")
    print("- Ensure audio files are in supported formats (WAV, MP3, etc.)")
    print("- Maximum file size is 25MB")
    print("- If 'ffmpeg not found' error: run 'python install_ffmpeg_cross_platform.py'")
    print("- If Ollama connection fails: check Docker container status")
    print("- FFmpeg must be in PATH or local bin/ directory")
    
    print("\n🐳 Docker Ollama Commands:")
    print("- Check status: docker ps | grep ollama")
    print("- View logs: docker logs agentic-ollama")
    print("- Restart: docker restart agentic-ollama")
    
    print(f"\n🖥️  Platform-Specific Tips ({platform.system()}):")
    system = platform.system().lower()
    if system == 'windows':
        print("- Use PowerShell or Command Prompt as Administrator")
        print("- Check Windows Defender/Antivirus isn't blocking downloads")
        print("- Alternative: choco install ffmpeg (if Chocolatey installed)")
    elif system == 'linux':
        print("- Use package manager: sudo apt install ffmpeg (Ubuntu/Debian)")
        print("- Check if running in container: docker exec -it <container> bash")
        print("- Ensure sufficient permissions for /usr/local/bin")
    elif system == 'darwin':
        print("- Install Homebrew first: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("- Then: brew install ffmpeg")
        print("- Check Xcode Command Line Tools: xcode-select --install")

if __name__ == "__main__":
    main() 