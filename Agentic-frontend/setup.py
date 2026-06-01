#!/usr/bin/env python3
"""
CogniVox Agentic Frontend Setup Script
=====================================
Robust setup for React/TypeScript frontend with Node.js and npm/yarn.
"""

import os
import sys
import json
import shutil
import platform
import subprocess
from pathlib import Path
from typing import Optional, Dict, List

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

def print_colored(message: str, color: str = Colors.RESET):
    """Print colored message"""
    print(f"{color}{message}{Colors.RESET}")

def print_banner():
    """Print setup banner"""
    print_colored(f"{Colors.CYAN}{Colors.BOLD}")
    print("┌────────────────────────────────────────────────────────┐")
    print("│           CogniVox Agentic Frontend Setup             │")
    print("│              React + TypeScript + Vite                │")
    print("└────────────────────────────────────────────────────────┘")
    print_colored("", Colors.RESET)

class FrontendSetup:
    """Frontend setup manager"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.package_json = self.project_dir / "package.json"
        self.node_modules = self.project_dir / "node_modules"
        self.package_lock = self.project_dir / "package-lock.json"
        
    def check_node_version(self) -> bool:
        """Check if Node.js is installed and version is compatible"""
        print_colored("🔍 Checking Node.js installation...", Colors.BLUE)
        
        try:
            # On Windows, ensure proper command execution
            is_windows = platform.system().lower() == 'windows'
            
            result = subprocess.run(
                ["node", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10,
                shell=is_windows
            )
            
            if result.returncode != 0:
                print_colored("❌ Node.js not found!", Colors.RED)
                self._print_node_install_instructions()
                return False
                
            version = result.stdout.strip()
            print_colored(f"✓ Node.js version: {version}", Colors.GREEN)
            
            # Check minimum version (Node 16+)
            version_number = version.replace('v', '').split('.')[0]
            if int(version_number) < 16:
                print_colored(f"⚠ Warning: Node.js {version} detected. Minimum recommended version is 16.x", Colors.YELLOW)
                
            return True
            
        except subprocess.TimeoutExpired:
            print_colored("❌ Node.js check timed out!", Colors.RED)
            return False
        except Exception as e:
            print_colored(f"❌ Error checking Node.js: {e}", Colors.RED)
            self._print_node_install_instructions()
            return False
    
    def check_npm_version(self) -> bool:
        """Check if npm is installed"""
        print_colored("🔍 Checking npm installation...", Colors.BLUE)
        
        try:
            # On Windows, npm is a batch file that requires shell=True
            is_windows = platform.system().lower() == 'windows'
            
            result = subprocess.run(
                ["npm", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10,
                shell=is_windows
            )
            
            if result.returncode != 0:
                print_colored("❌ npm not found!", Colors.RED)
                print_colored(f"Error output: {result.stderr}", Colors.RED)
                return False
                
            version = result.stdout.strip()
            print_colored(f"✓ npm version: {version}", Colors.GREEN)
            return True
            
        except subprocess.TimeoutExpired:
            print_colored("❌ npm check timed out!", Colors.RED)
            return False
        except Exception as e:
            print_colored(f"❌ Error checking npm: {e}", Colors.RED)
            return False
    
    def check_package_json(self) -> bool:
        """Verify package.json exists and is valid"""
        print_colored("🔍 Checking package.json...", Colors.BLUE)
        
        if not self.package_json.exists():
            print_colored("❌ package.json not found!", Colors.RED)
            return False
            
        try:
            with open(self.package_json, 'r') as f:
                package_data = json.load(f)
                
            print_colored(f"✓ Project: {package_data.get('name', 'Unknown')}", Colors.GREEN)
            print_colored(f"✓ Version: {package_data.get('version', 'Unknown')}", Colors.GREEN)
            
            # Check for key dependencies
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            
            key_deps = ['react', 'react-dom', 'typescript', 'vite']
            missing_deps = []
            
            for dep in key_deps:
                if dep not in dependencies and dep not in dev_dependencies:
                    missing_deps.append(dep)
            
            if missing_deps:
                print_colored(f"⚠ Missing key dependencies: {', '.join(missing_deps)}", Colors.YELLOW)
                
            return True
            
        except json.JSONDecodeError as e:
            print_colored(f"❌ Invalid package.json: {e}", Colors.RED)
            return False
        except Exception as e:
            print_colored(f"❌ Error reading package.json: {e}", Colors.RED)
            return False
    
    def clean_install(self) -> bool:
        """Clean existing installation"""
        print_colored("🧹 Cleaning previous installation...", Colors.YELLOW)
        
        try:
            # Remove node_modules
            if self.node_modules.exists():
                print_colored("  Removing node_modules...", Colors.YELLOW)
                shutil.rmtree(self.node_modules)
                
            # Remove package-lock.json
            if self.package_lock.exists():
                print_colored("  Removing package-lock.json...", Colors.YELLOW)
                self.package_lock.unlink()
                
            print_colored("✓ Clean completed", Colors.GREEN)
            return True
            
        except Exception as e:
            print_colored(f"❌ Clean failed: {e}", Colors.RED)
            return False
    
    def install_dependencies(self) -> bool:
        """Install npm dependencies"""
        print_colored("📦 Installing dependencies...", Colors.BLUE)
        
        try:
            # Use npm ci for faster, reliable installs if package-lock exists
            # Otherwise use npm install
            if self.package_lock.exists():
                cmd = ["npm", "ci"]
                print_colored("  Using npm ci for fast installation...", Colors.BLUE)
            else:
                cmd = ["npm", "install"]
                print_colored("  Using npm install...", Colors.BLUE)
            
            # On Windows, npm is a batch file that requires shell=True
            is_windows = platform.system().lower() == 'windows'
            
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                shell=is_windows
            )
            
            if result.returncode != 0:
                print_colored(f"❌ Installation failed!", Colors.RED)
                print_colored(f"Error: {result.stderr}", Colors.RED)
                return False
                
            print_colored("✓ Dependencies installed successfully", Colors.GREEN)
            return True
            
        except subprocess.TimeoutExpired:
            print_colored("❌ Installation timed out (5 minutes)", Colors.RED)
            print_colored("Try running with --clean flag or check your internet connection", Colors.YELLOW)
            return False
        except Exception as e:
            print_colored(f"❌ Installation error: {e}", Colors.RED)
            return False
    
    def verify_installation(self) -> bool:
        """Verify that installation was successful"""
        print_colored("🔍 Verifying installation...", Colors.BLUE)
        
        # Check if node_modules exists
        if not self.node_modules.exists():
            print_colored("❌ node_modules directory not found", Colors.RED)
            return False
            
        # Check key dependencies
        key_packages = ['react', 'react-dom', 'typescript', 'vite']
        missing_packages = []
        
        for package in key_packages:
            package_dir = self.node_modules / package
            if not package_dir.exists():
                missing_packages.append(package)
        
        if missing_packages:
            print_colored(f"❌ Missing packages: {', '.join(missing_packages)}", Colors.RED)
            return False
            
        # Try to run type checking
        try:
            # On Windows, npm is a batch file that requires shell=True
            is_windows = platform.system().lower() == 'windows'
            
            result = subprocess.run(
                ["npm", "run", "tsc", "--noEmit"], 
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=30,
                shell=is_windows
            )
            
            if result.returncode == 0:
                print_colored("✓ TypeScript compilation check passed", Colors.GREEN)
            else:
                print_colored("⚠ TypeScript compilation issues detected", Colors.YELLOW)
                
        except:
            print_colored("⚠ Could not verify TypeScript setup", Colors.YELLOW)
        
        print_colored("✓ Installation verified", Colors.GREEN)
        return True
    
    def create_env_template(self) -> bool:
        """Create .env template file"""
        print_colored("📄 Creating environment template...", Colors.BLUE)
        
        env_template = self.project_dir / ".env.template"
        env_file = self.project_dir / ".env"
        
        template_content = """# CogniVox Agentic Frontend Environment Configuration
# Copy this file to .env and customize as needed

# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_MEMORY_API_URL=http://localhost:8002
VITE_GRAPHRAG_API_URL=http://localhost:8003

# Development Configuration
VITE_DEV_MODE=true
VITE_DEBUG_ENABLED=false

# Authentication
VITE_AUTH_ENABLED=true

# Build Configuration
VITE_BUILD_TARGET=es2020
"""
        
        try:
            # Create template
            with open(env_template, 'w') as f:
                f.write(template_content)
            
            # Create .env if it doesn't exist
            if not env_file.exists():
                with open(env_file, 'w') as f:
                    f.write(template_content)
                print_colored("✓ Created .env file", Colors.GREEN)
            else:
                print_colored("✓ .env file already exists", Colors.YELLOW)
                
            print_colored("✓ Environment template created", Colors.GREEN)
            return True
            
        except Exception as e:
            print_colored(f"❌ Failed to create environment template: {e}", Colors.RED)
            return False
    
    def _print_node_install_instructions(self):
        """Print Node.js installation instructions"""
        print_colored("\n📋 Node.js Installation Instructions:", Colors.CYAN)
        print_colored("1. Visit: https://nodejs.org/", Colors.CYAN)
        print_colored("2. Download and install Node.js LTS (16.x or higher)", Colors.CYAN)
        if platform.system() == "Windows":
            print_colored("3. Or use Chocolatey: choco install nodejs", Colors.CYAN)
        elif platform.system() == "Darwin":
            print_colored("3. Or use Homebrew: brew install node", Colors.CYAN)
        else:
            print_colored("3. Or use package manager: sudo apt-get install nodejs npm", Colors.CYAN)

def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="CogniVox Agentic Frontend Setup",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--clean", 
        action="store_true",
        help="Clean install (remove node_modules and package-lock.json)"
    )
    
    parser.add_argument(
        "--skip-verify", 
        action="store_true",
        help="Skip installation verification"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Create setup instance
    setup = FrontendSetup()
    
    try:
        # Step 1: Check Node.js
        if not setup.check_node_version():
            sys.exit(1)
            
        # Step 2: Check npm
        if not setup.check_npm_version():
            sys.exit(1)
            
        # Step 3: Verify package.json
        if not setup.check_package_json():
            sys.exit(1)
            
        # Step 4: Clean if requested
        if args.clean:
            if not setup.clean_install():
                sys.exit(1)
                
        # Step 5: Install dependencies
        if not setup.install_dependencies():
            sys.exit(1)
            
        # Step 6: Verify installation
        if not args.skip_verify:
            if not setup.verify_installation():
                sys.exit(1)
                
        # Step 7: Create environment template
        setup.create_env_template()
        
        # Success message
        print_colored(f"\n🎉 Frontend setup completed successfully!", Colors.GREEN)
        print_colored(f"📁 Project directory: {setup.project_dir}", Colors.CYAN)
        print_colored(f"🚀 To start development server: npm run dev", Colors.CYAN)
        print_colored(f"🔧 To build for production: npm run build", Colors.CYAN)
        
    except KeyboardInterrupt:
        print_colored("\n❌ Setup interrupted by user", Colors.RED)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n❌ Setup failed: {e}", Colors.RED)
        sys.exit(1)

if __name__ == "__main__":
    main() 