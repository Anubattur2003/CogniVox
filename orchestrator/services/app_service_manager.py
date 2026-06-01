"""
Application Service Management
=============================
Handles application service lifecycle, health monitoring, and environment validation.
"""

import os
import sys
import time
import threading
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.table import Table
    from rich.text import Text
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback console for systems without Rich
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
        def rule(self, *args, **kwargs):
            print("=" * 60)

from ..core.config import ServiceConfig
from .terminal_launcher import TerminalLauncher

logger = logging.getLogger("orchestrator.app_services")


class AppServiceManager:
    """Manages application services (Backend, Memory, GraphRAG, Frontend)"""
    
    def __init__(self, console: Console, project_root: Path):
        self.console = console
        self.project_root = project_root
        self.services = {}
        self.shutdown_requested = False
        self._setup_services()
    
    def _setup_services(self):
        """Configure all application services with enhanced metadata"""
        self.services = {
            "backend": ServiceConfig(
                name="Backend API",
                directory="Agentic-Backend",
                run_command=["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
                port=8000,
                health_endpoint="/health",
                dependencies=["postgres", "mongodb"],  # Requires databases
                color="green",
                tech_stack="FastAPI + SQLAlchemy",
                always_update=True,  # Always update backend dependencies
                update_command=["uv", "sync", "--upgrade"]
            ),
            "memory": ServiceConfig(
                name="Memory Service",
                directory="Agentic-Memory",
                run_command=["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"],
                port=8002,
                health_endpoint="/api/health",
                dependencies=["backend", "mongodb", "ollama"],  # Requires backend, DB, and LLM
                color="purple",
                tech_stack="LangChain + LangGraph",
                always_update=True,  # Always update memory service dependencies
                update_command=["uv", "sync", "--upgrade"]
            ),
            "graphrag": ServiceConfig(
                name="Graph RAG Service",
                directory="Agentic-Graph-RAG",
                run_command=["uv", "run", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8003", "--reload"],
                port=8003,
                health_endpoint="/health",
                dependencies=["backend", "neo4j", "ollama"],  # Requires backend, graph DB, and LLM
                color="cyan",
                tech_stack="LlamaIndex + Neo4j",
                always_update=True,  # Always update GraphRAG dependencies
                update_command=["uv", "sync", "--upgrade"]
            ),
            "frontend": ServiceConfig(
                name="Frontend",
                directory="Agentic-frontend",
                run_command=["npm", "run", "dev"],
                port=3000,
                health_endpoint="/",
                dependencies=["backend", "memory", "graphrag"],
                color="blue",
                tech_stack="React + TypeScript + Vite",
                always_update=True,  # Always update frontend dependencies
                update_command=["npm", "update"]
            )
        }

    def start_service(self, service_name: str, dev_mode: bool = False, use_status: bool = True, force_update: bool = False) -> bool:
        """Start a specific service"""
        if service_name not in self.services:
            self.console.print(f"❌ Unknown service: {service_name}", style="red")
            return False

        service = self.services[service_name]
        service_path = self.project_root / service.directory

        if not service_path.exists():
            self.console.print(f"❌ Service directory not found: {service_path}", style="red")
            return False

        # Check if service is already running
        if service.is_running():
            self.console.print(f"⚠️  {service.name} is already running", style="yellow")
            return True

        # Update dependencies if requested or configured
        if force_update or service.always_update:
            self.console.print(f"📦 Updating {service.name} dependencies...", style="cyan")
            if not self.update_service_dependencies(service_name):
                self.console.print(f"⚠️  Failed to update {service.name} dependencies, continuing...", style="yellow")

        # Validate service setup
        if not self.validate_service_setup(service_name):
            self.console.print(f"❌ {service.name} validation failed", style="red")
            return False

        self.console.print(f"🚀 Starting {service.name}...", style="blue")

        try:
            if service.use_terminal:
                # Launch in separate terminal
                terminal_process, temp_file = TerminalLauncher.launch_service_in_terminal(
                    service_name=service_name,
                    service_dir=service.directory,
                    run_command=service.run_command,
                    working_dir=str(self.project_root)
                )
                service.terminal_process = terminal_process
                if temp_file:
                    # Store temp file for cleanup
                    pass
            else:
                # Launch as subprocess
                process = subprocess.Popen(
                    service.run_command,
                    cwd=service_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                service.process = process

            # Wait for service to be healthy
            if self.wait_for_service(service):
                self.console.print(f"✅ {service.name} started successfully", style="green")
                
                # Start monitoring thread
                monitor_thread = threading.Thread(
                    target=self._monitor_service,
                    args=(service,),
                    daemon=True
                )
                monitor_thread.start()
                
                return True
            else:
                self.console.print(f"❌ {service.name} failed to start properly", style="red")
                self.stop_service(service_name)
                return False

        except Exception as e:
            self.console.print(f"❌ Error starting {service.name}: {e}", style="red")
            return False

    def wait_for_service(self, service: ServiceConfig, timeout: int = 60) -> bool:
        """Wait for service to become healthy"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if service.is_running():
                return True
            time.sleep(2)
        
        return False

    def _monitor_service(self, service: ServiceConfig):
        """Monitor service health in background"""
        while not self.shutdown_requested:
            try:
                if not service.is_running():
                    logger.warning(f"{service.name} appears to have stopped")
                    break
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error monitoring {service.name}: {e}")
                break

    def stop_service(self, service_name: str) -> bool:
        """Stop a specific service"""
        if service_name not in self.services:
            self.console.print(f"❌ Unknown service: {service_name}", style="red")
            return False

        service = self.services[service_name]
        
        if not service.is_running():
            self.console.print(f"⚠️  {service.name} is not running", style="yellow")
            return True

        self.console.print(f"🛑 Stopping {service.name}...", style="blue")

        try:
            if service.use_terminal and service.terminal_process:
                # Terminate terminal process
                if service.terminal_process.poll() is None:
                    service.terminal_process.terminate()
                    try:
                        service.terminal_process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        service.terminal_process.kill()
                service.terminal_process = None
            elif service.process:
                # Terminate subprocess
                if service.process.poll() is None:
                    service.process.terminate()
                    try:
                        service.process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        service.process.kill()
                service.process = None

            self.console.print(f"✅ {service.name} stopped", style="green")
            return True

        except Exception as e:
            self.console.print(f"❌ Error stopping {service.name}: {e}", style="red")
            return False

    def start_all_services(self, dev_mode: bool = False, start_order: List[str] = None, force_update: bool = False) -> bool:
        """Start all services in dependency order"""
        if start_order is None:
            # Default dependency-aware start order
            start_order = ["backend", "memory", "graphrag", "frontend"]

        self.console.print("🚀 Starting all application services...", style="blue")
        
        success_count = 0
        for service_name in start_order:
            if service_name in self.services:
                if self.start_service(service_name, dev_mode=dev_mode, force_update=force_update):
                    success_count += 1
                    # Brief delay between service starts
                    time.sleep(2)
                else:
                    self.console.print(f"❌ Failed to start {service_name}, continuing with others...", style="red")

        total_services = len([s for s in start_order if s in self.services])
        if success_count == total_services:
            self.console.print("✅ All application services started successfully", style="green")
            return True
        else:
            self.console.print(f"⚠️  {success_count}/{total_services} application services started", style="yellow")
            return False

    def stop_all_services(self) -> bool:
        """Stop all running services"""
        self.console.print("🛑 Stopping all application services...", style="blue")
        self.shutdown_requested = True
        
        # Stop in reverse order for dependencies
        stop_order = ["frontend", "graphrag", "memory", "backend"]
        
        success_count = 0
        for service_name in stop_order:
            if service_name in self.services:
                if self.stop_service(service_name):
                    success_count += 1
                # Brief delay between service stops
                time.sleep(1)

        total_services = len(stop_order)
        if success_count == total_services:
            self.console.print("✅ All application services stopped", style="green")
            return True
        else:
            self.console.print(f"⚠️  {success_count}/{total_services} application services stopped", style="yellow")
            return False

    def check_service_status(self) -> Dict[str, bool]:
        """Check status of all services"""
        status = {}
        for service_name, service in self.services.items():
            status[service_name] = service.is_running()
        return status

    def show_running_services(self):
        """Display status of all services in a rich table"""
        if not RICH_AVAILABLE:
            self.console.print("\n=== Application Service Status ===")
            for service_name, service in self.services.items():
                status = "✅ Running" if service.is_running() else "❌ Stopped"
                self.console.print(f"{service.name}: {status}")
            return

        table = Table(title="Application Service Status", show_header=True, header_style="bold magenta")
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Port", style="blue")
        table.add_column("Tech Stack", style="yellow")
        table.add_column("Health", style="green")

        for service_name, service in self.services.items():
            is_running = service.is_running()
            status = "✅ Running" if is_running else "❌ Stopped"
            health = f"http://127.0.0.1:{service.port}{service.health_endpoint}" if is_running else "N/A"
            
            table.add_row(
                service.name,
                status,
                str(service.port),
                service.tech_stack,
                health
            )

        self.console.print(table)

    def validate_service_setup(self, service_name: str) -> bool:
        """Validate service environment and dependencies"""
        if service_name not in self.services:
            return False

        service = self.services[service_name]
        service_path = self.project_root / service.directory

        if service_name == "frontend":
            return self._validate_nodejs_service(service_name, service, service_path)
        else:
            return self._validate_python_service(service_name, service, service_path)

    def _validate_nodejs_service(self, service_name: str, service: ServiceConfig, service_path: Path) -> bool:
        """Validate Node.js service setup"""
        import platform
        
        # Check if package.json exists
        package_json = service_path / "package.json"
        if not package_json.exists():
            self.console.print(f"❌ {service.name}: package.json not found", style="red")
            return False

        # Check if Node.js and npm are available
        node_available = self._check_nodejs_availability()
        
        if not node_available:
            self.console.print(f"⚠️  {service.name}: Node.js/npm not found, checking for setup.py...", style="yellow")
            
            # Check if setup.py exists as fallback
            setup_py = service_path / "setup.py"
            if setup_py.exists():
                self.console.print(f"ℹ️  {service.name}: Found setup.py - use 'python setup.py' to setup frontend", style="blue")
                # For now, we'll consider this valid - the setup.py can handle Node.js installation
                return True
            else:
                self.console.print(f"❌ {service.name}: No Node.js/npm and no setup.py found", style="red")
                self.console.print("   Please install Node.js from https://nodejs.org/ or run setup manually", style="yellow")
                return False

        # Check if node_modules exists (dependencies installed)
        node_modules = service_path / "node_modules"
        if not node_modules.exists():
            self.console.print(f"⚠️  {service.name}: dependencies not installed, running npm install...", style="yellow")
            try:
                # Windows compatibility
                is_windows = platform.system().lower() == 'windows'
                result = subprocess.run(
                    ["npm", "install"],
                    cwd=service_path,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    shell=is_windows
                )
                if result.returncode != 0:
                    self.console.print(f"❌ {service.name}: npm install failed: {result.stderr}", style="red")
                    return False
                self.console.print(f"✅ {service.name}: dependencies installed", style="green")
            except Exception as e:
                self.console.print(f"❌ {service.name}: npm install error: {e}", style="red")
                return False

        return True

    def _check_nodejs_availability(self) -> bool:
        """Check if Node.js and npm are available"""
        import platform
        is_windows = platform.system().lower() == 'windows'
        
        try:
            # Check Node.js
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=is_windows
            )
            if result.returncode != 0:
                return False
                
            # Check npm
            result = subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=is_windows
            )
            return result.returncode == 0
            
        except Exception:
            return False

    def _validate_python_service(self, service_name: str, service: ServiceConfig, service_path: Path) -> bool:
        """Validate Python service setup"""
        # Check if requirements.txt exists
        requirements_file = service_path / "requirements.txt"
        if not requirements_file.exists():
            self.console.print(f"❌ {service.name}: requirements.txt not found", style="red")
            return False

        # Check if main run file exists
        run_file = service_path / "run.py"
        if not run_file.exists():
            self.console.print(f"❌ {service.name}: run.py not found", style="red")
            return False

        # Check if virtual environment exists or UV is available
        venv_path = service_path / ".venv"
        if not venv_path.exists():
            # Try to create virtual environment with UV
            self.console.print(f"⚠️  {service.name}: creating virtual environment...", style="yellow")
            try:
                result = subprocess.run(
                    ["uv", "venv"],
                    cwd=service_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    self.console.print(f"✅ {service.name}: virtual environment created", style="green")
                else:
                    self.console.print(f"❌ {service.name}: failed to create venv: {result.stderr}", style="red")
                    return False
            except Exception as e:
                self.console.print(f"❌ {service.name}: venv creation error: {e}", style="red")
                return False

        return True

    def get_service_urls(self) -> Dict[str, str]:
        """Get URLs for all running services"""
        urls = {}
        for name, service in self.services.items():
            if service.is_running():
                urls[name] = f"http://localhost:{service.port}"
        return urls

    def update_service_dependencies(self, service_name: str, verbose: bool = False) -> bool:
        """Update dependencies for a specific service"""
        if service_name not in self.services:
            return False

        service = self.services[service_name]
        service_path = self.project_root / service.directory

        if not service_path.exists():
            if verbose:
                self.console.print(f"❌ Service directory not found: {service_path}", style="red")
            return False

        try:
            if service_name == "frontend":
                return self._update_nodejs_dependencies(service_name, service, service_path, verbose)
            else:
                return self._update_python_dependencies(service_name, service, service_path, verbose)
        except Exception as e:
            if verbose:
                self.console.print(f"❌ Error updating {service_name} dependencies: {e}", style="red")
            return False

    def _update_nodejs_dependencies(self, service_name: str, service: 'ServiceConfig', 
                                   service_path: Path, verbose: bool = False) -> bool:
        """Update Node.js service dependencies"""
        import platform
        
        try:
            # Check if Node.js is available
            if not self._check_nodejs_availability():
                if verbose:
                    self.console.print(f"⚠️  {service.name}: Node.js/npm not available", style="yellow")
                return False
            
            # Update npm dependencies
            if verbose:
                self.console.print(f"📦 Updating {service.name} npm dependencies...", style="blue")
            
            is_windows = platform.system().lower() == 'windows'
            
            # First update npm itself
            npm_update_cmd = ["npm", "update"]
            result = subprocess.run(
                npm_update_cmd,
                cwd=service_path,
                capture_output=True,
                text=True,
                timeout=300,
                shell=is_windows
            )
            
            if result.returncode == 0:
                if verbose:
                    self.console.print(f"✅ {service.name} dependencies updated", style="green")
                return True
            else:
                if verbose:
                    self.console.print(f"❌ Failed to update {service.name} dependencies: {result.stderr}", style="red")
                return False
                
        except Exception as e:
            if verbose:
                self.console.print(f"❌ Error updating {service_name} dependencies: {e}", style="red")
            return False

    def _update_python_dependencies(self, service_name: str, service: 'ServiceConfig', 
                                   service_path: Path, verbose: bool = False) -> bool:
        """Update Python service dependencies"""
        try:
            if verbose:
                self.console.print(f"📦 Updating {service.name} Python dependencies...", style="blue")
            
            # Use custom update command if specified
            if service.update_command:
                result = subprocess.run(
                    service.update_command,
                    cwd=service_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            else:
                # Default update strategy using uv
                if (service_path / "pyproject.toml").exists():
                    result = subprocess.run(
                        ["uv", "sync", "--upgrade"],
                        cwd=service_path,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                elif (service_path / "requirements.txt").exists():
                    result = subprocess.run(
                        ["uv", "pip", "install", "-r", "requirements.txt", "--upgrade"],
                        cwd=service_path,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                else:
                    if verbose:
                        self.console.print(f"⚠️  No dependency file found for {service.name}", style="yellow")
                    return True  # No dependencies to update
            
            if result.returncode == 0:
                if verbose:
                    self.console.print(f"✅ {service.name} dependencies updated", style="green")
                return True
            else:
                if verbose:
                    self.console.print(f"❌ Failed to update {service.name} dependencies: {result.stderr}", style="red")
                return False
                
        except Exception as e:
            if verbose:
                self.console.print(f"❌ Error updating {service_name} dependencies: {e}", style="red")
            return False

    def setup_environment(self, services: List[str], services_config: Dict, clean: bool = False, 
                          auto_install: bool = False, verbose: bool = False) -> bool:
        """Setup and validate environment for specified services"""
        self.console.print(f"🔧 Setting up environment for services: {', '.join(services)}", style="blue")
        
        success = True
        
        # Update services configuration
        self.services = {name: services_config[name] for name in services if name in services_config}
        
        for service_name in services:
            if service_name not in services_config:
                self.console.print(f"❌ Unknown service: {service_name}", style="red")
                success = False
                continue
                
            service = services_config[service_name]
            service_path = self.project_root / service.directory
            
            self.console.print(f"🔍 Validating {service.name}...", style="cyan")
            
            # Check if service directory exists
            if not service_path.exists():
                self.console.print(f"❌ Service directory not found: {service_path}", style="red")
                success = False
                continue
            
            # Validate service setup
            if not self.validate_service_setup(service_name):
                self.console.print(f"❌ {service.name} validation failed", style="red")
                if auto_install:
                    self.console.print(f"🔧 Attempting to fix {service.name}...", style="yellow")
                    if self._attempt_service_fix(service_name, service, service_path, verbose):
                        self.console.print(f"✅ {service.name} setup repaired", style="green")
                    else:
                        self.console.print(f"❌ Failed to repair {service.name}", style="red")
                        success = False
                else:
                    success = False
                continue
            
            self.console.print(f"✅ {service.name} validated successfully", style="green")
        
        if success:
            self.console.print("🎉 All services validated successfully!", style="green")
        else:
            self.console.print("❌ Some services failed validation", style="red")
            
        return success

    def _attempt_service_fix(self, service_name: str, service: 'ServiceConfig', 
                            service_path: Path, verbose: bool = False) -> bool:
        """Attempt to fix service setup issues"""
        try:
            if service_name == "frontend":
                return self._fix_nodejs_service(service_name, service, service_path, verbose)
            else:
                return self._fix_python_service(service_name, service, service_path, verbose)
        except Exception as e:
            if verbose:
                self.console.print(f"Error fixing {service_name}: {e}", style="red")
            return False

    def _fix_nodejs_service(self, service_name: str, service: 'ServiceConfig', 
                           service_path: Path, verbose: bool = False) -> bool:
        """Fix Node.js service issues"""
        import platform
        
        try:
            # Check if Node.js is available
            if not self._check_nodejs_availability():
                self.console.print(f"⚠️  {service.name}: Node.js/npm not available", style="yellow")
                
                # Try using setup.py instead
                setup_py = service_path / "setup.py"
                if setup_py.exists():
                    self.console.print(f"🔧 Using {service.name} setup.py for installation...", style="blue")
                    
                    result = subprocess.run(
                        [sys.executable, "setup.py"],
                        cwd=service_path,
                        capture_output=True,
                        text=True,
                        timeout=600  # Longer timeout for setup.py as it might install Node.js
                    )
                    
                    if result.returncode == 0:
                        if verbose:
                            self.console.print(f"✅ {service.name} setup completed", style="green")
                        return True
                    else:
                        if verbose:
                            self.console.print(f"❌ Setup.py failed: {result.stderr}", style="red")
                        return False
                else:
                    if verbose:
                        self.console.print(f"❌ No setup.py found for {service.name}", style="red")
                        self.console.print("   Please install Node.js manually or run frontend setup", style="yellow")
                    return False
            
            # Node.js is available, use npm install
            self.console.print(f"📦 Installing {service.name} dependencies...", style="blue")
            
            is_windows = platform.system().lower() == 'windows'
            result = subprocess.run(
                ["npm", "install"],
                cwd=service_path,
                capture_output=True,
                text=True,
                timeout=300,
                shell=is_windows
            )
            
            if result.returncode == 0:
                if verbose:
                    self.console.print(f"✅ Dependencies installed for {service.name}", style="green")
                return True
            else:
                if verbose:
                    self.console.print(f"❌ Failed to install dependencies: {result.stderr}", style="red")
                return False
                
        except Exception as e:
            if verbose:
                self.console.print(f"❌ Error fixing {service_name}: {e}", style="red")
            return False

    def _fix_python_service(self, service_name: str, service: 'ServiceConfig', 
                           service_path: Path, verbose: bool = False) -> bool:
        """Fix Python service issues"""
        try:
            # Install dependencies using uv
            self.console.print(f"📦 Installing {service.name} dependencies...", style="blue")
            
            # First check if pyproject.toml or requirements.txt exists
            if (service_path / "pyproject.toml").exists():
                result = subprocess.run(
                    ["uv", "sync"],
                    cwd=service_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            elif (service_path / "requirements.txt").exists():
                result = subprocess.run(
                    ["uv", "pip", "install", "-r", "requirements.txt"],
                    cwd=service_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            else:
                if verbose:
                    self.console.print(f"⚠️ No dependency file found for {service.name}", style="yellow")
                return True  # No dependencies to install
            
            if result.returncode == 0:
                if verbose:
                    self.console.print(f"✅ Dependencies installed for {service.name}", style="green")
                return True
            else:
                if verbose:
                    self.console.print(f"❌ Failed to install dependencies: {result.stderr}", style="red")
                return False
                
        except Exception as e:
            if verbose:
                self.console.print(f"❌ Error fixing {service_name}: {e}", style="red")
            return False 