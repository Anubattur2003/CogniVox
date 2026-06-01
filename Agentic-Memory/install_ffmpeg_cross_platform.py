#!/usr/bin/env python3
"""
Cross-Platform FFmpeg Installation Helper
=========================================
This script helps install ffmpeg on Windows and Linux for speech-to-text functionality.
"""

import os
import sys
import platform
import requests
import zipfile
import tarfile
import shutil
import subprocess
from pathlib import Path

class FFmpegInstaller:
    def __init__(self):
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        self.is_windows = self.system == 'windows'
        self.is_linux = self.system == 'linux'
        self.is_macos = self.system == 'darwin'
        
    def check_ffmpeg_installed(self):
        """Check if ffmpeg is already installed and accessible."""
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ FFmpeg is already installed and accessible!")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False

    def get_download_info(self):
        """Get platform-specific download information."""
        if self.is_windows:
            return {
                "url": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
                "filename": "ffmpeg.zip",
                "extract_type": "zip",
                "executable": "ffmpeg.exe"
            }
        elif self.is_linux:
            # Use static Linux build
            if "x86_64" in self.arch or "amd64" in self.arch:
                return {
                    "url": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
                    "filename": "ffmpeg.tar.xz",
                    "extract_type": "tar",
                    "executable": "ffmpeg"
                }
            else:
                return {
                    "url": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-i686-static.tar.xz",
                    "filename": "ffmpeg.tar.xz", 
                    "extract_type": "tar",
                    "executable": "ffmpeg"
                }
        elif self.is_macos:
            return {
                "url": "https://evermeet.cx/ffmpeg/ffmpeg-5.1.2.zip",
                "filename": "ffmpeg.zip",
                "extract_type": "zip",
                "executable": "ffmpeg"
            }
        else:
            raise Exception(f"Unsupported platform: {self.system}")

    def install_via_package_manager(self):
        """Try to install via system package manager first."""
        print("🔄 Trying to install via package manager...")
        
        try:
            if self.is_linux:
                # Try different package managers
                package_managers = [
                    ["apt", "update", "&&", "apt", "install", "-y", "ffmpeg"],
                    ["yum", "install", "-y", "ffmpeg"],
                    ["dnf", "install", "-y", "ffmpeg"],
                    ["pacman", "-S", "--noconfirm", "ffmpeg"],
                    ["zypper", "install", "-y", "ffmpeg"]
                ]
                
                for cmd in package_managers:
                    try:
                        # Check if package manager exists
                        pm_check = subprocess.run([cmd[0], "--version"], 
                                                capture_output=True, timeout=5)
                        if pm_check.returncode == 0:
                            print(f"📦 Found {cmd[0]} package manager, installing...")
                            # For apt, split the command properly
                            if cmd[0] == "apt":
                                subprocess.run(["sudo", "apt", "update"], check=True, timeout=30)
                                result = subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"], 
                                                      check=True, timeout=300)
                            else:
                                result = subprocess.run(["sudo"] + cmd, check=True, timeout=300)
                            
                            if result.returncode == 0:
                                print("✅ FFmpeg installed via package manager!")
                                return True
                    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
                        continue
                        
            elif self.is_macos:
                # Try Homebrew
                try:
                    subprocess.run(["brew", "--version"], check=True, capture_output=True, timeout=5)
                    print("🍺 Found Homebrew, installing FFmpeg...")
                    result = subprocess.run(["brew", "install", "ffmpeg"], check=True, timeout=300)
                    if result.returncode == 0:
                        print("✅ FFmpeg installed via Homebrew!")
                        return True
                except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    pass
                    
        except Exception as e:
            print(f"⚠️  Package manager installation failed: {e}")
            
        return False

    def download_ffmpeg(self, download_info):
        """Download ffmpeg binary."""
        print(f"🔄 Downloading FFmpeg for {self.system.title()}...")
        
        try:
            # Create downloads directory
            downloads_dir = Path("downloads")
            downloads_dir.mkdir(exist_ok=True)
            
            file_path = downloads_dir / download_info["filename"]
            
            # Download ffmpeg
            response = requests.get(download_info["url"], stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\rDownloading... {percent:.1f}%", end="", flush=True)
            
            print(f"\n✅ Downloaded FFmpeg to {file_path}")
            return file_path
            
        except Exception as e:
            print(f"❌ Failed to download FFmpeg: {e}")
            return None

    def extract_ffmpeg(self, file_path, download_info):
        """Extract ffmpeg to a local directory."""
        print("📦 Extracting FFmpeg...")
        
        try:
            extract_dir = Path("ffmpeg_extracted")
            extract_dir.mkdir(exist_ok=True)
            
            if download_info["extract_type"] == "zip":
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            elif download_info["extract_type"] == "tar":
                with tarfile.open(file_path, 'r:xz') as tar_ref:
                    tar_ref.extractall(extract_dir)
            
            # Find the ffmpeg executable
            ffmpeg_exe = None
            for root, dirs, files in os.walk(extract_dir):
                if download_info["executable"] in files:
                    ffmpeg_exe = Path(root) / download_info["executable"]
                    break
            
            if ffmpeg_exe and ffmpeg_exe.exists():
                print(f"✅ Extracted FFmpeg to {ffmpeg_exe}")
                return ffmpeg_exe
            else:
                print(f"❌ Could not find {download_info['executable']} in extracted files")
                return None
                
        except Exception as e:
            print(f"❌ Failed to extract FFmpeg: {e}")
            return None

    def setup_ffmpeg_local(self, ffmpeg_exe):
        """Setup ffmpeg in local bin directory."""
        print("🔧 Setting up FFmpeg locally...")
        
        try:
            # Create a local bin directory
            bin_dir = Path("bin")
            bin_dir.mkdir(exist_ok=True)
            
            # Copy ffmpeg to bin directory
            executable_name = "ffmpeg.exe" if self.is_windows else "ffmpeg"
            local_ffmpeg = bin_dir / executable_name
            shutil.copy2(ffmpeg_exe, local_ffmpeg)
            
            # Make executable on Unix systems
            if not self.is_windows:
                os.chmod(local_ffmpeg, 0o755)
            
            # Add to current session PATH
            current_path = os.environ.get("PATH", "")
            bin_dir_abs = bin_dir.absolute()
            
            if self.is_windows:
                os.environ["PATH"] = f"{bin_dir_abs};{current_path}"
            else:
                os.environ["PATH"] = f"{bin_dir_abs}:{current_path}"
            
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

    def cleanup_downloads(self):
        """Clean up downloaded files."""
        try:
            for cleanup_dir in ["downloads", "ffmpeg_extracted"]:
                cleanup_path = Path(cleanup_dir)
                if cleanup_path.exists():
                    shutil.rmtree(cleanup_path)
                    print(f"🧹 Cleaned up {cleanup_dir}")
        except Exception as e:
            print(f"⚠️  Failed to cleanup: {e}")

    def install(self):
        """Main installation function."""
        print(f"🎤 FFmpeg Installation Helper for {self.system.title()}")
        print("=" * 60)
        print(f"Platform: {self.system.title()} {self.arch}")
        
        # Check if already installed
        if self.check_ffmpeg_installed():
            return True
        
        print("FFmpeg not found. Installing...")
        
        # Try package manager first (Linux/macOS)
        if not self.is_windows:
            if self.install_via_package_manager():
                return True
            print("📦 Package manager installation failed, trying manual installation...")
        
        # Manual installation
        try:
            download_info = self.get_download_info()
        except Exception as e:
            print(f"❌ {e}")
            return False
        
        # Download ffmpeg
        file_path = self.download_ffmpeg(download_info)
        if not file_path:
            return False
        
        # Extract ffmpeg
        ffmpeg_exe = self.extract_ffmpeg(file_path, download_info)
        if not ffmpeg_exe:
            return False
        
        # Setup ffmpeg
        success = self.setup_ffmpeg_local(ffmpeg_exe)
        
        # Cleanup
        self.cleanup_downloads()
        
        if success:
            self.print_success_message()
        else:
            self.print_failure_message()
        
        return success

    def print_success_message(self):
        """Print success message with platform-specific instructions."""
        print("\n🎉 FFmpeg installation completed!")
        print("\n📝 Next steps:")
        print("1. Restart your terminal/command prompt")
        print("2. Test speech-to-text functionality in CogniVox")
        print("3. FFmpeg is now available for local whisper transcription")
        
        bin_dir_abs = Path("bin").absolute()
        
        if self.is_windows:
            print(f"\n🔧 Manual PATH setup (if needed):")
            print(f"Add this to your system PATH: {bin_dir_abs}")
        else:
            print(f"\n🔧 Manual PATH setup (if needed):")
            print(f"Add to ~/.bashrc or ~/.zshrc:")
            print(f'export PATH="{bin_dir_abs}:$PATH"')

    def print_failure_message(self):
        """Print failure message with platform-specific instructions."""
        print("\n❌ FFmpeg installation failed!")
        
        if self.is_windows:
            print("Please download FFmpeg manually from: https://ffmpeg.org/download.html")
        elif self.is_linux:
            print("Please install FFmpeg manually:")
            print("  Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg")
            print("  CentOS/RHEL: sudo yum install ffmpeg")
            print("  Fedora: sudo dnf install ffmpeg")
            print("  Arch: sudo pacman -S ffmpeg")
        elif self.is_macos:
            print("Please install FFmpeg manually:")
            print("  Homebrew: brew install ffmpeg")
            print("  MacPorts: sudo port install ffmpeg")

def main():
    """Main function."""
    try:
        installer = FFmpegInstaller()
        success = installer.install()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 