"""
Prerequisites checking and installation
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

# Rich imports for beautiful terminal output
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback to basic console
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
        def rule(self, *args, **kwargs):
            print("="*60)


class PrerequisiteChecker:
    """Check and install prerequisites for fresh repository setup"""
    
    def __init__(self, console: Console):
        self.console = console
        self.checks_passed = {}
        
    def check_python_version(self) -> bool:
        """Check Python version"""
        version_info = sys.version_info
        required_major, required_minor = 3, 8
        
        if version_info.major >= required_major and version_info.minor >= required_minor:
            self.console.print(f"✅ Python {version_info.major}.{version_info.minor}.{version_info.micro}", style="green")
            self.checks_passed['python'] = True
            return True
        else:
            self.console.print(f"❌ Python {required_major}.{required_minor}+ required, found {version_info.major}.{version_info.minor}.{version_info.micro}", style="red")
            self.checks_passed['python'] = False
            return False
    
    def check_uv_installation(self) -> bool:
        """Check if UV package manager is installed"""
        if shutil.which("uv"):
            try:
                result = subprocess.run(["uv", "--version"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.console.print(f"✅ UV Package Manager: {version}", style="green")
                    self.checks_passed['uv'] = True
                    return True
            except Exception:
                pass
        
        self.console.print("❌ UV Package Manager not found", style="red")
        self.checks_passed['uv'] = False
        return False
    
    def install_uv(self) -> bool:
        """Install UV package manager"""
        self.console.print("\n🔧 Installing UV Package Manager...", style="blue")
        
        try:
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=True,
                    console=self.console
                ) as progress:
                    task = progress.add_task("Installing UV...", total=None)
                    
                    if platform.system() == "Windows":
                        # Windows installation using PowerShell
                        cmd = [
                            "powershell", "-ExecutionPolicy", "Bypass", "-Command",
                            "Invoke-RestMethod -Uri https://astral.sh/uv/install.ps1 | Invoke-Expression"
                        ]
                    else:
                        # Unix-like systems
                        cmd = ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    progress.update(task, completed=100)
            else:
                # Fallback without progress display
                self.console.print("Installing UV Package Manager...")
                if platform.system() == "Windows":
                    cmd = [
                        "powershell", "-ExecutionPolicy", "Bypass", "-Command",
                        "Invoke-RestMethod -Uri https://astral.sh/uv/install.ps1 | Invoke-Expression"
                    ]
                else:
                    cmd = ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
            if result.returncode == 0:
                # Add UV to PATH for current session
                if platform.system() == "Windows":
                    uv_path = Path.home() / ".cargo" / "bin"
                else:
                    uv_path = Path.home() / ".cargo" / "bin"
                
                if uv_path.exists():
                    os.environ["PATH"] = str(uv_path) + os.pathsep + os.environ.get("PATH", "")
                
                self.console.print("✅ UV Package Manager installed successfully", style="green")
                return True
            else:
                self.console.print(f"❌ UV installation failed: {result.stderr}", style="red")
                return False
                
        except Exception as e:
            self.console.print(f"❌ UV installation error: {e}", style="red")
            return False
    
    def check_node_installation(self) -> bool:
        """Check if Node.js is installed (optional)"""
        if shutil.which("node") and shutil.which("npm"):
            try:
                node_result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)
                npm_result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=10)
                
                if node_result.returncode == 0 and npm_result.returncode == 0:
                    node_version = node_result.stdout.strip()
                    npm_version = npm_result.stdout.strip()
                    self.console.print(f"✅ Node.js: {node_version}, npm: {npm_version}", style="green")
                    self.checks_passed['node'] = True
                    return True
            except Exception:
                pass
        
        self.console.print("ℹ️  Node.js/npm not found (optional for frontend development)", style="dim")
        self.checks_passed['node'] = True  # Mark as passed since it's optional
        return True  # Return True since it's optional
    
    def check_docker_installation(self) -> bool:
        """Check if Docker is available"""
        if shutil.which("docker"):
            try:
                result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.console.print(f"✅ Docker: {version}", style="green")
                    
                    # Check if Docker daemon is running
                    daemon_result = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10)
                    if daemon_result.returncode == 0:
                        self.console.print("✅ Docker daemon is running", style="green")
                        self.checks_passed['docker'] = True
                        return True
                    else:
                        self.console.print("⚠️  Docker installed but daemon not running", style="yellow")
                        self.checks_passed['docker'] = False
                        return False
            except Exception:
                pass
        
        self.console.print("❌ Docker not found", style="red")
        self.checks_passed['docker'] = False
        return False
    
    def check_git_installation(self) -> bool:
        """Check if Git is installed"""
        if shutil.which("git"):
            try:
                result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.console.print(f"✅ Git: {version}", style="green")
                    self.checks_passed['git'] = True
                    return True
            except Exception:
                pass
        
        self.console.print("❌ Git not found", style="red")
        self.checks_passed['git'] = False
        return False
    
    def check_windows_build_tools(self) -> bool:
        """Check for Windows C++ Build Tools (Windows only, optional)"""
        if platform.system() != "Windows":
            return True
            
        # Check for Visual Studio Build Tools
        vs_paths = [
            Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) / "Microsoft Visual Studio" / "Installer",
            Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "Microsoft Visual Studio" / "Installer"
        ]
        
        for vs_path in vs_paths:
            if vs_path.exists():
                self.console.print("✅ Microsoft Visual Studio Build Tools detected", style="green")
                self.checks_passed['build_tools'] = True
                return True
        
        # Check for Windows SDK
        sdk_path = Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) / "Windows Kits"
        if sdk_path.exists():
            self.console.print("✅ Windows SDK detected", style="green")
            self.checks_passed['build_tools'] = True
            return True
        
        self.console.print("ℹ️  Microsoft C++ Build Tools not found (optional for native dependencies)", style="dim")
        self.checks_passed['build_tools'] = True  # Mark as passed since it's optional
        return True  # Return True since it's optional
    
    def install_windows_build_tools(self) -> bool:
        """Install Windows C++ Build Tools using winget"""
        if platform.system() != "Windows":
            return True
            
        self.console.print("\n🔧 Installing Microsoft C++ Build Tools...", style="blue")
        
        try:
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=True,
                    console=self.console
                ) as progress:
                    task = progress.add_task("Installing C++ Build Tools...", total=None)
                    
                    # Try winget first
                    cmd = ["winget", "install", "Microsoft.VisualStudio.2022.BuildTools", "--silent", "--accept-package-agreements"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                    
                    progress.update(task, completed=100)
            else:
                # Fallback without progress display
                self.console.print("Installing Microsoft C++ Build Tools...")
                cmd = ["winget", "install", "Microsoft.VisualStudio.2022.BuildTools", "--silent", "--accept-package-agreements"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                
            if result.returncode == 0:
                self.console.print("✅ Microsoft C++ Build Tools installed successfully", style="green")
                self.console.print("⚠️  Please restart your terminal for changes to take effect", style="yellow")
                return True
            else:
                # Fallback: provide manual installation instructions
                self.console.print("❌ Automatic installation failed", style="red")
                self.console.print("Please install manually from:", style="yellow")
                self.console.print("https://visualstudio.microsoft.com/visual-cpp-build-tools/", style="cyan")
                return False
                
        except Exception as e:
            self.console.print(f"❌ Build tools installation error: {e}", style="red")
            return False
    
    def run_full_check(self, auto_install: bool = False) -> bool:
        """Run all prerequisite checks"""
        self.console.rule("[bold blue]Prerequisites Check", style="blue")
        
        all_passed = True
        
        # Core checks
        all_passed &= self.check_python_version()
        all_passed &= self.check_git_installation()
        
        # UV check with auto-install option
        if not self.check_uv_installation():
            if auto_install:
                if self.install_uv():
                    self.check_uv_installation()  # Re-check
                else:
                    all_passed = False
            else:
                all_passed = False
        
        # Optional checks (don't affect overall success)
        self.check_node_installation()  # Always returns True now
        self.check_docker_installation()
        
        # Windows-specific optional check
        if platform.system() == "Windows":
            self.check_windows_build_tools()  # Always returns True now
        
        if not all_passed:
            self.console.print("\n⚠️  Some prerequisites are missing. See installation guide below:", style="yellow")
            self.show_installation_guide()
        
        return all_passed
    
    def show_installation_guide(self):
        """Show installation guide for missing prerequisites"""
        guide_content = []
        
        if not self.checks_passed.get('uv', True):
            guide_content.append("🔧 **UV Package Manager:**")
            guide_content.append("   Windows: Run in PowerShell as Administrator:")
            guide_content.append("   `Invoke-RestMethod -Uri https://astral.sh/uv/install.ps1 | Invoke-Expression`")
            guide_content.append("   Linux/macOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`")
            guide_content.append("")
        
        if not self.checks_passed.get('docker', True):
            guide_content.append("🐳 **Docker:**")
            guide_content.append("   Download Docker Desktop: https://www.docker.com/products/docker-desktop")
            guide_content.append("   Linux: `curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh`")
            guide_content.append("")
        
        if guide_content:
            if RICH_AVAILABLE:
                panel = Panel(
                    "\n".join(guide_content),
                    title="Installation Guide",
                    border_style="yellow"
                )
                self.console.print(panel)
            else:
                self.console.print("\n".join(guide_content)) 