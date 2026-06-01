#!/usr/bin/env python3
"""
Cross-Platform Speech-to-Text Test Script
=========================================
Test the speech-to-text functionality on Windows and Linux.
"""

import os
import sys
import platform
import requests
import json
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if all dependencies are available."""
    print(f"🖥️  Platform: {platform.system()} {platform.machine()}")
    print("=" * 50)
    
    dependencies = {}
    
    # Check Python version
    print("🐍 Python version:", sys.version.split()[0])
    dependencies['python'] = sys.version_info >= (3, 8)
    
    # Check ffmpeg
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        ffmpeg_available = result.returncode == 0
        print(f"🎬 FFmpeg: {'✅ Available' if ffmpeg_available else '❌ Not found'}")
        dependencies['ffmpeg'] = ffmpeg_available
    except:
        print("🎬 FFmpeg: ❌ Not found")
        dependencies['ffmpeg'] = False
    
    # Check Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        ollama_available = response.status_code == 200
        print(f"🦙 Ollama: {'✅ Available' if ollama_available else '❌ Not accessible'}")
        dependencies['ollama'] = ollama_available
        
        if ollama_available:
            models = response.json().get('models', [])
            whisper_models = [m for m in models if 'whisper' in m.get('name', '').lower()]
            print(f"🎤 Whisper models: {len(whisper_models)} found")
            dependencies['whisper_model'] = len(whisper_models) > 0
        else:
            dependencies['whisper_model'] = False
    except:
        print("🦙 Ollama: ❌ Not accessible")
        dependencies['ollama'] = False
        dependencies['whisper_model'] = False
    
    # Check Memory service
    try:
        response = requests.get("http://localhost:8002/api/transcribe/status", timeout=5)
        memory_available = response.status_code == 200
        print(f"🧠 Memory Service: {'✅ Available' if memory_available else '❌ Not accessible'}")
        dependencies['memory_service'] = memory_available
    except:
        print("🧠 Memory Service: ❌ Not accessible")
        dependencies['memory_service'] = False
    
    return dependencies

def test_transcription_endpoint():
    """Test the transcription endpoint with a dummy audio file."""
    print("\n🧪 Testing transcription endpoint...")
    
    try:
        # Create a tiny dummy audio file (WAV header)
        dummy_wav = create_dummy_wav()
        
        # Test transcription endpoint
        with open(dummy_wav, 'rb') as f:
            files = {'audio_file': ('test.wav', f, 'audio/wav')}
            response = requests.post(
                "http://localhost:8002/api/transcribe",
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Transcription test successful!")
            print(f"   Success: {result.get('success', False)}")
            print(f"   Text: {result.get('text', 'No text')[:100]}")
            print(f"   Model: {result.get('model_used', 'Unknown')}")
            print(f"   Processing time: {result.get('processing_time', 0):.2f}s")
            return True
        else:
            print(f"❌ Transcription test failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Transcription test failed: {e}")
        return False
    finally:
        # Clean up dummy file
        if dummy_wav and Path(dummy_wav).exists():
            Path(dummy_wav).unlink()

def create_dummy_wav():
    """Create a minimal valid WAV file for testing."""
    wav_header = bytes([
        # RIFF header
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x24, 0x00, 0x00, 0x00,  # File size - 8
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        
        # fmt chunk
        0x66, 0x6D, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # Chunk size (16)
        0x01, 0x00,              # Audio format (PCM)
        0x01, 0x00,              # Number of channels (1)
        0x44, 0xAC, 0x00, 0x00,  # Sample rate (44100)
        0x88, 0x58, 0x01, 0x00,  # Byte rate
        0x02, 0x00,              # Block align
        0x10, 0x00,              # Bits per sample (16)
        
        # data chunk
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x00, 0x00, 0x00, 0x00,  # Data size (0 - silence)
    ])
    
    dummy_path = Path("test_dummy.wav")
    with open(dummy_path, 'wb') as f:
        f.write(wav_header)
    
    return dummy_path

def provide_setup_suggestions(dependencies):
    """Provide platform-specific setup suggestions."""
    print("\n📋 Setup Suggestions:")
    print("=" * 30)
    
    system = platform.system().lower()
    
    if not dependencies.get('ffmpeg', False):
        print("🎬 FFmpeg Setup:")
        if system == 'windows':
            print("   Option 1: choco install ffmpeg")
            print("   Option 2: Download from https://ffmpeg.org/download.html")
            print("   Option 3: python install_ffmpeg_cross_platform.py")
        elif system == 'linux':
            print("   Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg")
            print("   CentOS/RHEL: sudo yum install ffmpeg")
            print("   Fedora: sudo dnf install ffmpeg")
            print("   Alternative: python install_ffmpeg_cross_platform.py")
        elif system == 'darwin':
            print("   Homebrew: brew install ffmpeg")
            print("   Alternative: python install_ffmpeg_cross_platform.py")
    
    if not dependencies.get('ollama', False):
        print("\n🦙 Ollama Setup:")
        print("   Check Docker: docker ps | grep ollama")
        print("   Start Ollama: docker restart agentic-ollama")
        print("   Alternative: Install Ollama locally from https://ollama.ai")
    
    if not dependencies.get('whisper_model', False):
        print("\n🎤 Whisper Model Setup:")
        print("   Install model: ollama pull dimavz/whisper-tiny")
        print("   Alternative: python setup_whisper.py")
    
    if not dependencies.get('memory_service', False):
        print("\n🧠 Memory Service Setup:")
        print("   Start service: cd Agentic-Memory && python run.py")
        print("   Check port 8002: netstat -an | grep 8002")

def main():
    """Main test function."""
    print("🎤 CogniVox Speech-to-Text Cross-Platform Test")
    print("=" * 55)
    
    # Check dependencies
    dependencies = check_dependencies()
    
    # Test transcription if possible
    if dependencies.get('memory_service', False):
        test_success = test_transcription_endpoint()
    else:
        print("\n⚠️  Cannot test transcription - Memory service not available")
        test_success = False
    
    # Provide suggestions
    missing_deps = [k for k, v in dependencies.items() if not v]
    if missing_deps:
        provide_setup_suggestions(dependencies)
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"   Platform: {platform.system()}")
    print(f"   Dependencies: {len([v for v in dependencies.values() if v])}/{len(dependencies)} available")
    print(f"   Transcription test: {'✅ Passed' if test_success else '❌ Failed'}")
    
    if test_success:
        print(f"\n🎉 Speech-to-text is working on {platform.system()}!")
    else:
        print(f"\n🔧 Setup required for {platform.system()}")
        print("   Run: python setup_whisper.py")
    
    return test_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1) 