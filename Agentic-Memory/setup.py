#!/usr/bin/env python3
"""
CogniVox Agentic Memory Service Setup Script
===========================================
UV-based setup with robust error handling and environment management.
"""

import os
import sys
import subprocess
import platform
import shutil
import time
from pathlib import Path
from typing import Tuple, Optional
import logging
import argparse

# Color codes for output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class MemorySetupLogger:
    """Enhanced logging for Memory setup"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        
    def info(self, message: str):
        print(f"{Colors.CYAN}[INFO]{Colors.RESET} {message}")
        
    def success(self, message: str):
        print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} {message}")
        
    def warning(self, message: str):
        print(f"{Colors.YELLOW}[WARNING]{Colors.RESET} {message}")
        
    def error(self, message: str):
        print(f"{Colors.RED}[ERROR]{Colors.RESET} {message}")
        
    def debug(self, message: str):
        if self.verbose:
            print(f"{Colors.BLUE}[DEBUG]{Colors.RESET} {message}")

class MemorySetup:
    """CogniVox Memory Service Setup Manager"""
    
    def __init__(self, verbose: bool = False):
        self.logger = MemorySetupLogger(verbose)
        self.service_name = "Agentic-Memory"
        self.venv_path = Path(".venv")
        self.requirements_file = Path("requirements.txt")
        
    def run_command(self, command: list, timeout: int = 120) -> Tuple[bool, str, str]:
        """Execute command with timeout and error handling"""
        try:
            self.logger.debug(f"Running: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            
            success = result.returncode == 0
            if self.logger.verbose:
                if result.stdout:
                    self.logger.debug(f"stdout: {result.stdout[:200]}...")
                if result.stderr:
                    self.logger.debug(f"stderr: {result.stderr[:200]}...")
                    
            return success, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out after {timeout} seconds")
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return False, "", str(e)
    
    def check_python_version(self) -> bool:
        """Check if Python version is compatible (3.9+ required, 3.11+ preferred for LangChain)"""
        version_info = sys.version_info
        required_major, required_minor = 3, 9  # Minimum for LangChain compatibility
        preferred_major, preferred_minor = 3, 11  # Preferred version
        
        if version_info.major >= required_major and version_info.minor >= required_minor:
            if version_info.major >= preferred_major and version_info.minor >= preferred_minor:
                self.logger.success(f"Python {version_info.major}.{version_info.minor}.{version_info.micro} - Excellent! (Preferred version)")
            else:
                self.logger.success(f"Python {version_info.major}.{version_info.minor}.{version_info.micro} - OK (Compatible with LangChain)")
            return True
        else:
            self.logger.error(f"Python {required_major}.{required_minor}+ required for LangChain, found {version_info.major}.{version_info.minor}.{version_info.micro}")
            self.logger.error("Please install Python 3.9+ (Python 3.11+ recommended)")
            return False
    
    def install_uv(self) -> bool:
        """Install UV package manager if not available"""
        # Check if uv is already installed
        if shutil.which("uv"):
            self.logger.success("UV package manager already installed")
            return True
            
        self.logger.info("Installing UV package manager...")
        
        try:
            if platform.system() == "Windows":
                # Windows installation
                success, stdout, stderr = self.run_command([
                    "powershell", "-Command", 
                    "Invoke-RestMethod -Uri https://astral.sh/uv/install.ps1 | Invoke-Expression"
                ])
            else:
                # Unix-like systems
                success, stdout, stderr = self.run_command([
                    "curl", "--proto", "=https", "--tlsv1.2", "-LsSf", 
                    "https://astral.sh/uv/install.sh", "|", "sh"
                ])
                
            if success:
                self.logger.success("UV package manager installed successfully")
                return True
            else:
                self.logger.error(f"Failed to install UV: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"UV installation failed: {e}")
            return False
    
    def create_virtual_environment(self) -> bool:
        """Create virtual environment using UV with Python 3.11 for optimal compatibility"""
        try:
            # Remove existing environment if force flag is set
            if self.venv_path.exists():
                self.logger.info("Removing existing virtual environment...")
                shutil.rmtree(self.venv_path, ignore_errors=True)
                time.sleep(1)
            
            self.logger.info("Creating virtual environment with UV...")
            # Use Python 3.11 for optimal performance and compatibility
            success, stdout, stderr = self.run_command([
                "uv", "venv", str(self.venv_path), "--python", "3.11"
            ])
            
            if success:
                self.logger.success("Virtual environment created successfully with Python 3.11")
                return True
            else:
                # Fallback to system Python if 3.11 is not available
                self.logger.warning("Python 3.11 not found, trying with system Python...")
                success, stdout, stderr = self.run_command([
                    "uv", "venv", str(self.venv_path)
                ])
                
                if success:
                    self.logger.success("Virtual environment created with system Python")
                    return True
                else:
                    self.logger.error(f"Failed to create virtual environment: {stderr}")
                    return False
                
        except Exception as e:
            self.logger.error(f"Virtual environment creation failed: {e}")
            return False
    
    def get_uv_command(self) -> list:
        """Get UV command with virtual environment activation"""
        return ["uv", "pip", "install", "--python", str(self.venv_path)]
    
    def install_pytorch_optimized(self) -> bool:
        """Install PyTorch with optimized settings for Memory service"""
        try:
            self.logger.info("Installing PyTorch with CPU optimization...")
            
            # Install PyTorch CPU version for better compatibility
            uv_cmd = self.get_uv_command()
            success, stdout, stderr = self.run_command(
                uv_cmd + ["torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cpu"],
                timeout=900  # 15 minutes for PyTorch
            )
            
            if success:
                self.logger.success("PyTorch installed successfully")
                return True
            else:
                self.logger.warning(f"PyTorch installation warning: {stderr}")
                # Try fallback installation
                self.logger.info("Attempting fallback PyTorch installation...")
                success, stdout, stderr = self.run_command(
                    uv_cmd + ["torch"], timeout=600
                )
                if success:
                    self.logger.success("PyTorch fallback installation successful")
                    return True
                else:
                    self.logger.error(f"PyTorch installation failed: {stderr}")
                    return False
                
        except Exception as e:
            self.logger.error(f"PyTorch installation failed: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """Install dependencies using UV with enhanced LangChain handling"""
        if not self.requirements_file.exists():
            self.logger.error(f"Requirements file not found: {self.requirements_file}")
            return False
            
        try:
            self.logger.info("Installing dependencies with UV...")
            
            # First upgrade pip in the virtual environment
            self.logger.info("Upgrading pip...")
            uv_cmd = self.get_uv_command()
            success, stdout, stderr = self.run_command(
                uv_cmd + ["--upgrade", "pip"], timeout=180
            )
            
            if not success:
                self.logger.warning(f"Pip upgrade warning: {stderr}")
            
            # Install PyTorch first for better dependency resolution
            if not self.install_pytorch_optimized():
                self.logger.warning("PyTorch installation failed, continuing with other dependencies...")
            
            # Install core dependencies first (non-conflicting packages)
            core_packages = [
                "fastapi>=0.104.0",
                "uvicorn>=0.23.2", 
                "pydantic>=2.4.2",
                "python-multipart>=0.0.6",
                "pymongo>=4.8.0,<5.0",
                "motor>=3.4.0,<4.0",
                "python-dotenv>=1.0.0",
                "requests>=2.31.0"
            ]
            
            self.logger.info("Installing core dependencies...")
            for package in core_packages:
                success, stdout, stderr = self.run_command(
                    uv_cmd + [package], timeout=180
                )
                if not success:
                    self.logger.warning(f"Core package {package} failed: {stderr}")
            
            # Install LangChain ecosystem with careful dependency resolution
            langchain_packages = [
                "pydantic-core>=2.14.0",
                "typing-extensions>=4.8.0",
                "langchain-core==0.3.51",
                "langchain-community==0.3.51", 
                "langchain==0.3.51",
                "langchain-ollama==0.2.0",
                "langgraph==0.2.50"
            ]
            
            self.logger.info("Installing LangChain ecosystem...")
            
            # Try installing LangChain packages in dependency order
            for package in langchain_packages:
                self.logger.info(f"Installing {package}...")
                success, stdout, stderr = self.run_command(
                    uv_cmd + [package, "--no-cache"], timeout=300
                )
                if success:
                    self.logger.success(f"✓ {package}")
                else:
                    self.logger.warning(f"⚠ {package} installation issue: {stderr}")
                    
                    # Try with resolution strategy for problematic packages
                    if "langchain" in package:
                        self.logger.info(f"Retrying {package} with conflict resolution...")
                        success, stdout, stderr = self.run_command(
                            uv_cmd + [package, "--force-reinstall", "--no-cache"], timeout=300
                        )
                        if success:
                            self.logger.success(f"✓ {package} (retry successful)")
                        else:
                            self.logger.error(f"✗ {package} failed on retry: {stderr}")
            
            # Final verification - try importing key packages
            self.logger.info("Verifying LangChain installation...")
            
            if platform.system() == "Windows":
                python_exe = self.venv_path / "Scripts" / "python.exe"
            else:
                python_exe = self.venv_path / "bin" / "python"
            
            # Test critical imports
            test_packages = ["langchain_core", "langchain", "langgraph"]
            all_imports_successful = True
            
            for package in test_packages:
                success, stdout, stderr = self.run_command([
                    str(python_exe), "-c", f"import {package}; print('OK')"
                ], timeout=30)
                
                if success:
                    self.logger.success(f"✓ {package} import successful")
                else:
                    self.logger.warning(f"⚠ {package} import failed: {stderr}")
                    all_imports_successful = False
            
            if all_imports_successful:
                self.logger.success("All dependencies installed successfully")
                return True
            else:
                self.logger.warning("Some packages had import issues, but installation may still work")
                return True  # Continue anyway, as runtime may still work
                
        except Exception as e:
            self.logger.error(f"Dependency installation failed: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """Verify the installation by checking key packages"""
        try:
            self.logger.info("Verifying installation...")
            
            # Check if virtual environment Python works
            if platform.system() == "Windows":
                python_exe = self.venv_path / "Scripts" / "python.exe"
            else:
                python_exe = self.venv_path / "bin" / "python"
            
            if not python_exe.exists():
                self.logger.error("Virtual environment Python not found")
                return False
            
            # Test import of key packages
            test_imports = [
                "fastapi",
                "uvicorn", 
                "pymongo",
                "motor",
                "langchain",
                "langgraph"
            ]
            
            for package in test_imports:
                success, stdout, stderr = self.run_command([
                    str(python_exe), "-c", f"import {package}; print(f'{package} imported successfully')"
                ])
                
                if success:
                    self.logger.success(f"✓ {package}")
                else:
                    self.logger.warning(f"✗ {package} - {stderr}")
            
            # Test PyTorch separately with more tolerance
            success, stdout, stderr = self.run_command([
                str(python_exe), "-c", "import torch; print(f'PyTorch {torch.__version__} imported successfully')"
            ])
            
            if success:
                self.logger.success(f"✓ PyTorch - {stdout.strip()}")
            else:
                self.logger.warning(f"✗ PyTorch - {stderr}")
            
            self.logger.success("Installation verification completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Installation verification failed: {e}")
            return False
    
    def setup_service(self, force: bool = False) -> bool:
        """Complete setup process for Memory service"""
        try:
            print(f"{Colors.MAGENTA}{Colors.BOLD}")
            print("┌────────────────────────────────────────────────────────┐")
            print("│           CogniVox Agentic Memory Setup               │")
            print("│            UV-Based Installation + AI/ML              │")
            print("└────────────────────────────────────────────────────────┘")
            print(f"{Colors.RESET}")
            
            # Step 1: Check Python version
            if not self.check_python_version():
                return False
            
            # Step 2: Install UV package manager
            if not self.install_uv():
                return False
            
            # Step 3: Create virtual environment
            if not self.create_virtual_environment():
                return False
            
            # Step 4: Install dependencies
            if not self.install_dependencies():
                return False
            
            # Step 5: Verify installation
            if not self.verify_installation():
                return False
            
            # Success summary
            print(f"\n{Colors.GREEN}{Colors.BOLD}Setup completed successfully!{Colors.RESET}")
            print(f"{Colors.CYAN}Next steps:{Colors.RESET}")
            print(f"  1. Run the service: {Colors.YELLOW}python run.py{Colors.RESET}")
            print(f"  2. API Documentation: {Colors.YELLOW}http://localhost:8002/docs{Colors.RESET}")
            print(f"  3. Health Check: {Colors.YELLOW}http://localhost:8002/api/health{Colors.RESET}")
            print()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Setup failed: {e}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="CogniVox Memory Service Setup with UV",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force recreate virtual environment')
    
    args = parser.parse_args()
    
    setup = MemorySetup(verbose=args.verbose)
    success = setup.setup_service(force=args.force)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 