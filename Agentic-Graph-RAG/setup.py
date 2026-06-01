#!/usr/bin/env python3
"""
CogniVox Agentic Graph-RAG Service Setup Script
==============================================
Standard Python venv setup with robust error handling and AI/ML dependencies.
"""

import os
import sys
import subprocess
import platform
import shutil
import time
from pathlib import Path
from typing import Tuple
import venv

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

class GraphRAGSetupLogger:
    """Enhanced logging for Graph-RAG setup"""
    
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

class GraphRAGSetup:
    """CogniVox Graph-RAG Service Setup Manager"""
    
    def __init__(self, verbose: bool = False):
        self.logger = GraphRAGSetupLogger(verbose)
        self.service_name = "Agentic-Graph-RAG"
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
        """Check if Python version meets requirements"""
        try:
            version_info = sys.version_info
            if version_info.major == 3 and version_info.minor >= 8:
                self.logger.success(f"Python {version_info.major}.{version_info.minor}.{version_info.micro} - OK")
                return True
            else:
                self.logger.error(f"Python 3.8+ required, found {version_info.major}.{version_info.minor}.{version_info.micro}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to check Python version: {e}")
            return False
    
    def create_virtual_environment(self) -> bool:
        """Create virtual environment using standard venv"""
        try:
            # Remove existing environment if it exists
            if self.venv_path.exists():
                self.logger.info("Removing existing virtual environment...")
                shutil.rmtree(self.venv_path, ignore_errors=True)
                time.sleep(1)
            
            self.logger.info("Creating virtual environment...")
            venv.create(self.venv_path, with_pip=True)
            
            self.logger.success("Virtual environment created successfully")
            return True
                
        except Exception as e:
            self.logger.error(f"Virtual environment creation failed: {e}")
            return False
    
    def get_pip_command(self) -> list:
        """Get pip command with virtual environment activation"""
        if platform.system() == "Windows":
            return [str(self.venv_path / "Scripts" / "python.exe"), "-m", "pip"]
        else:
            return [str(self.venv_path / "bin" / "python"), "-m", "pip"]
    
    def upgrade_pip(self) -> bool:
        """Upgrade pip to the latest version"""
        try:
            self.logger.info("Upgrading pip...")
            pip_cmd = self.get_pip_command()
            success, stdout, stderr = self.run_command(
                pip_cmd + ["install", "--upgrade", "pip"], timeout=180
            )
            
            if success:
                self.logger.success("Pip upgraded successfully")
                return True
            else:
                self.logger.warning(f"Pip upgrade warning: {stderr}")
                return True  # Continue even if upgrade fails
                
        except Exception as e:
            self.logger.error(f"Pip upgrade failed: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """Install dependencies using pip"""
        if not self.requirements_file.exists():
            self.logger.error(f"Requirements file not found: {self.requirements_file}")
            return False
            
        try:
            self.logger.info(f"Installing dependencies from {self.requirements_file}...")
            
            pip_cmd = self.get_pip_command()
            success, stdout, stderr = self.run_command(
                pip_cmd + ["install", "-r", str(self.requirements_file)], 
                timeout=1200  # 20 minutes for all dependencies
            )
            
            if success:
                self.logger.success("Dependencies installed successfully")
                return True
            else:
                self.logger.error(f"Some dependencies failed: {stderr[:500]}...")
                return False
                
        except Exception as e:
            self.logger.error(f"Dependency installation failed: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """Verify the installation by checking key packages"""
        try:
            self.logger.info("Verifying installation...")
            
            # Get Python executable
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
                "chromadb",
                "neo4j",
                "langchain",
                "langgraph",
                "llama_index"
            ]
            
            for package in test_imports:
                success, stdout, stderr = self.run_command([
                    str(python_exe), "-c", f"import {package}; print('{package} imported successfully')"
                ])
                
                if success:
                    self.logger.success(f"✓ {package}")
                else:
                    self.logger.warning(f"✗ {package} - {stderr}")
            
            # Test PyTorch separately with version info
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
    
    def setup_service(self) -> bool:
        """Complete setup process for Graph-RAG service"""
        try:
            print(f"{Colors.GREEN}{Colors.BOLD}")
            print("┌────────────────────────────────────────────────────────┐")
            print("│          CogniVox Agentic Graph-RAG Setup             │")
            print("│         Python venv + AI/ML + Knowledge Graphs        │")
            print("└────────────────────────────────────────────────────────┘")
            print(f"{Colors.RESET}")
            
            # Step 1: Check Python version
            if not self.check_python_version():
                return False
            
            # Step 2: Create virtual environment
            if not self.create_virtual_environment():
                return False
            
            # Step 3: Upgrade pip
            if not self.upgrade_pip():
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
            print(f"  1. Activate venv: {Colors.YELLOW}.venv\\Scripts\\activate{Colors.RESET} (Windows) or {Colors.YELLOW}source .venv/bin/activate{Colors.RESET} (Unix)")
            print(f"  2. Run the service: {Colors.YELLOW}python run.py{Colors.RESET}")
            print(f"  3. API Documentation: {Colors.YELLOW}http://localhost:8003/docs{Colors.RESET}")
            print()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Setup failed: {e}")
            return False

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="CogniVox Graph-RAG Service Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output')
    
    args = parser.parse_args()
    
    setup = GraphRAGSetup(verbose=args.verbose)
    success = setup.setup_service()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()