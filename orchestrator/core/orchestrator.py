"""
Main ServiceOrchestrator class for the CogniVox Agentic Platform
"""

import os
import sys
import time
import signal
import platform
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Try to import requests for health checks
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Rich UI imports
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.align import Align
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
    from rich.prompt import Prompt, Confirm
    from rich.rule import Rule
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Local imports
from .config import ServiceConfig, DockerServiceConfig
from .prerequisites import PrerequisiteChecker
from .credentials_manager import CredentialsManager
from ..services.docker_manager import DockerManager
from ..services.app_service_manager import AppServiceManager
from ..services.terminal_launcher import TerminalLauncher

# Initialize console
if RICH_AVAILABLE:
    console = Console()
else:
    # Fallback console for systems without Rich
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
        def rule(self, *args, **kwargs):
            print("=" * 60)

    console = Console()


class ServiceOrchestrator:
    """Enhanced service orchestration with Rich UI, credential management, and Docker integration"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.console = console
        self.shutdown_requested = False
        self.prerequisite_checker = PrerequisiteChecker(self.console)
        
        # Docker compose file
        self.docker_compose_file = self.project_root / "docker-compose.agentic-services.yml"
        
        # Initialize specialized managers
        self.credentials_manager = CredentialsManager(self.console, self.project_root)
        self.docker_manager = DockerManager(self.console, self.project_root, self.docker_compose_file)
        self.app_service_manager = AppServiceManager(self.console, self.project_root)
        
        # Temporary files cleanup list
        self.temp_files = []
        
        # Setup services and Docker configurations
        self.setup_services()
        self.setup_docker_services()
        
        # Credential management
        self.credentials_file = self.project_root / "credentials.json"
        self.env_file = self.project_root / ".env"
        self.default_credentials = {}
        self.setup_credentials()

    def setup_services(self):
        """Setup application service configurations"""
        self.services = {
            "backend": ServiceConfig(
                name="Backend API",
                directory="Agentic-Backend",
                run_command=["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
                port=8000,
                health_endpoint="/health",
                dependencies=["postgres", "mongodb"],
                color="green",
                tech_stack="FastAPI + SQLAlchemy"
            ),
            "memory": ServiceConfig(
                name="Memory Service",
                directory="Agentic-Memory",
                run_command=["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"],
                port=8002,
                health_endpoint="/api/health",
                dependencies=["postgres"],
                color="purple",
                tech_stack="LangChain + LangGraph"
            ),
            "graphrag": ServiceConfig(
                name="Graph RAG Service",
                directory="Agentic-Graph-RAG",
                run_command=["uv", "run", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8003", "--reload"],
                port=8003,
                health_endpoint="/health",
                dependencies=["backend", "neo4j", "ollama"],
                color="cyan",
                tech_stack="LlamaIndex + Neo4j"
            ),
            "frontend": ServiceConfig(
                name="Frontend",
                directory="Agentic-frontend",
                run_command=["npm", "run", "dev"],
                port=3000,
                health_endpoint="/api/health",
                dependencies=["backend"],
                color="blue",
                tech_stack="React + TypeScript"
            )
        }

    def setup_docker_services(self):
        """Setup Docker infrastructure service configurations"""
        self.docker_services = {
            "postgres": DockerServiceConfig(
                name="PostgreSQL Database",
                container_name="agentic-postgres",
                port=5432,
                health_check="pg_isready -U postgres",
                tech_stack="PostgreSQL 15",
                color="blue"
            ),
            "mongodb": DockerServiceConfig(
                name="MongoDB Database", 
                container_name="agentic-mongodb",
                port=27017,
                health_check="mongosh --eval 'db.adminCommand(\"ping\")'",
                tech_stack="MongoDB 7",
                color="green"
            ),
            "neo4j": DockerServiceConfig(
                name="Neo4j Graph Database",
                container_name="agentic-neo4j", 
                port=7474,
                health_check="cypher-shell -u neo4j -p password 'RETURN 1'",
                tech_stack="Neo4j 5",
                color="cyan"
            ),
            "ollama": DockerServiceConfig(
                name="Ollama LLM Service",
                container_name="agentic-ollama",
                port=11434,
                health_check="curl -f http://localhost:11434/api/version",
                tech_stack="Ollama",
                color="purple"
            ),
            "pgadmin": DockerServiceConfig(
                name="PgAdmin",
                container_name="agentic-pgadmin",
                port=5050, 
                health_check="curl -f http://localhost:5050/misc/ping",
                dependencies=["postgres"],
                tech_stack="PgAdmin 4",
                color="blue"
            )
        }

    def print_banner(self):
        """Print enhanced orchestrator banner"""
        banner_text = """
╔══════════════════════════════════════════════════════════════╗
║                 CogniVox Agentic Platform                    ║
║                   Service Orchestrator                       ║
║                     Enhanced with Rich                       ║
╠══════════════════════════════════════════════════════════════╣
║  🔧 Backend API        (Port 8000) - FastAPI + SQLAlchemy   ║
║  🧠 Memory Service     (Port 8002) - LangChain + LangGraph  ║
║  📊 Graph RAG Service  (Port 8003) - LlamaIndex + Neo4j     ║
║  🌐 Frontend           (Port 3000) - React + TypeScript     ║
╚══════════════════════════════════════════════════════════════╝
        """
        
        panel = Panel(
            Align.center(banner_text.strip()),
            style="bold blue",
            border_style="blue"
        )
        console.print(panel)

    def setup_credentials(self):
        """Initialize credential configuration"""
        self.default_credentials = self.credentials_manager.get_default_credentials()
        
        # Load existing credentials if they exist
        if self.credentials_file.exists():
            self.credentials_manager.load_credentials()
        else:
            # Create default credentials file
            self.credentials_manager.create_credentials_file()

    # Delegate credential-related methods to CredentialsManager
    def create_credentials_file(self) -> bool:
        return self.credentials_manager.create_credentials_file()
    
    def load_credentials(self) -> bool:
        return self.credentials_manager.load_credentials()
    
    def create_env_file(self) -> bool:
        return self.credentials_manager.create_env_file()
    
    def export_credentials(self, format_type: str, filename: str = None) -> bool:
        return self.credentials_manager.export_credentials(format_type, filename)
    
    def validate_configuration(self) -> bool:
        return self.credentials_manager.validate_configuration()
    
    def show_all_credentials(self):
        return self.credentials_manager.show_all_credentials()

    # Delegate Docker-related methods to DockerManager
    def start_docker_services(self, services: List[str] = None, force_pull: bool = False) -> bool:
        return self.docker_manager.start_docker_services(services, force_pull)
    
    def start_docker_services_with_cleanup(self, services: List[str] = None, force_pull: bool = False) -> bool:
        return self.docker_manager.start_docker_services_with_cleanup(services, force_pull)
    
    def cleanup_conflicting_containers(self, services: List[str] = None) -> bool:
        return self.docker_manager.cleanup_conflicting_containers(services)
    
    def ensure_external_resources(self) -> bool:
        return self.docker_manager.ensure_external_resources()
    
    def stop_docker_services(self, services: List[str] = None) -> bool:
        return self.docker_manager.stop_docker_services(services)
    
    def wait_for_docker_service(self, service: DockerServiceConfig, timeout: int = 60) -> bool:
        return self.docker_manager.wait_for_docker_service(service, timeout)
    
    def install_ollama_models(self, models: List[str] = None) -> bool:
        return self.docker_manager.install_ollama_models(models)
    
    def is_docker_service_running(self, service_name: str) -> bool:
        return self.docker_manager.is_docker_service_running(service_name)

    # Database management delegate methods
    def initialize_databases(self, reset: bool = False) -> bool:
        return self.docker_manager.initialize_databases(reset)
    
    def reset_all_databases(self) -> bool:
        return self.docker_manager.reset_all_databases()

    # Delegate app service methods to AppServiceManager  
    def setup_environment(self, services: List[str] = None, clean: bool = False, 
                          auto_install: bool = False, verbose: bool = False) -> bool:
        return self.app_service_manager.setup_environment(
            services or list(self.services.keys()), 
            self.services, 
            clean, 
            auto_install, 
            verbose
        )
    
    def validate_service_setup(self, service_name: str) -> bool:
        return self.app_service_manager.validate_service_setup(service_name)

    def start_service(self, service_name: str, dev_mode: bool = False, use_status: bool = True, force_update: bool = False) -> bool:
        """Enhanced service startup with terminal launching"""
        # Delegate to AppServiceManager with all parameters
        return self.app_service_manager.start_service(service_name, dev_mode, use_status, force_update)

    def stop_service(self, service_name: str) -> bool:
        """Stop a running service"""
        if service_name not in self.services:
            console.print(f"❌ Unknown service: {service_name}", style="red")
            return False
            
        service = self.services[service_name]
        
        if not service.is_running():
            console.print(f"[WARN] {service.name} is not running", style="yellow")
            return True
            
        console.print(f"🛑 Stopping {service.name}...", style="yellow")
        
        try:
            # Stop terminal process if using terminal mode
            if service.terminal_process:
                service.terminal_process.terminate()
                try:
                    service.terminal_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    service.terminal_process.kill()
                    console.print(f"[WARN] {service.name} force stopped", style="yellow")
                service.terminal_process = None
            
            # Stop regular process if exists
            if service.process:
                service.process.terminate()
                try:
                    service.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    service.process.kill()
                    console.print(f"[WARN] {service.name} force stopped", style="yellow")
                service.process = None
                
            console.print(f"✅ {service.name} stopped", style="green")
            return True
            
        except Exception as e:
            console.print(f"❌ Error stopping {service.name}: {e}", style="red")
            return False

    def start_all_services(self, dev_mode: bool = False, start_order: List[str] = None, force_update: bool = False) -> bool:
        """Enhanced startup with dependency management and progress tracking"""
        # Delegate to AppServiceManager
        return self.app_service_manager.start_all_services(dev_mode, start_order, force_update)

    def stop_all_services(self) -> bool:
        """Enhanced shutdown with reverse dependency order"""
        console.rule("[bold yellow]Stopping All Services")
        
        # Stop in reverse order
        stop_order = ["frontend", "graphrag", "memory", "backend"]
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                
                main_task = progress.add_task("Stopping services", total=len(stop_order))
                
                for service_name in stop_order:
                    if service_name in self.services:
                        progress.update(main_task, description=f"Stopping {self.services[service_name].name}")
                        self.stop_service(service_name)
                        progress.advance(main_task)
                        time.sleep(1)
        
        except Exception as e:
            console.print(f"⚠️  Error with progress display, continuing with simple stop: {e}", style="yellow")
            # Fallback to simple stop if Progress fails
            return self.stop_all_services_simple()
        
        console.print("✅ All services stopped", style="green")
        self.cleanup_temp_files()
        return True

    def stop_all_services_simple(self) -> bool:
        """Simplified service shutdown without Progress UI"""
        console.print("🛑 Stopping all services...", style="yellow")
        
        # Stop in reverse order
        stop_order = ["frontend", "graphrag", "memory", "backend"]
        
        for service_name in stop_order:
            if service_name in self.services:
                self.stop_service(service_name)
        
        console.print("✅ All services stopped", style="green")
        self.cleanup_temp_files()
        return True

    def check_service_status(self) -> Dict[str, bool]:
        """Check and display comprehensive service status with real-time monitoring"""
        console.rule("[bold cyan]Service Status Check - Real-Time Monitoring")
        
        # Show that we're doing real-time checks
        console.print("🔄 [bold cyan]Performing real-time status checks...[/bold cyan]", style="cyan")
        
        status = {}
        current_time = time.strftime("%H:%M:%S")
        
        # Clear any cached health check data to force fresh checks
        for service in self.services.values():
            service.last_health_check = None
        
        # Application Services Status with real-time checking
        console.print("🔍 Checking application services...", style="dim")
        app_table = Table(title="🚀 Application Services", style="cyan")
        app_table.add_column("Service", style="bold", width=20)
        app_table.add_column("Status", width=15)
        app_table.add_column("Port", width=8)
        app_table.add_column("Technology", width=25)
        app_table.add_column("Health Check", width=20)
        app_table.add_column("Last Checked", width=12)
        
        for service_name, service in self.services.items():
            console.print(f"  Checking {service.name}...", style="dim")
            
            # Force real-time check
            is_running = service.is_running()  # This calls _check_health() internally
            status[service_name] = is_running
            
            # Get health status with more detail
            if is_running:
                try:
                    health_response_time = self._measure_health_check_time(service)
                    if health_response_time:
                        health_status = f"✅ Healthy ({health_response_time}ms)"
                    else:
                        health_status = "✅ Running (no health endpoint)"
                except:
                    health_status = "⚠️ Running (health check failed)"
            else:
                health_status = "❌ Offline"
            
            # Get last check time
            last_check = current_time if is_running else "N/A"
            
            if is_running:
                app_table.add_row(
                    f"[{service.color}]{service.name}[/{service.color}]",
                    "[green]🟢 Running[/green]",
                    str(service.port),
                    service.tech_stack,
                    health_status,
                    last_check
                )
            else:
                app_table.add_row(
                    f"[{service.color}]{service.name}[/{service.color}]",
                    "[red]🔴 Stopped[/red]",
                    str(service.port),
                    service.tech_stack,
                    health_status,
                    last_check
                )
        
        console.print(app_table)
        
        # Docker Infrastructure Services Status with real-time checking
        console.print("\n🔍 Checking Docker infrastructure services...", style="dim")
        docker_table = Table(title="🐳 Docker Infrastructure Services", style="magenta")
        docker_table.add_column("Service", style="bold", width=20)
        docker_table.add_column("Status", width=15) 
        docker_table.add_column("Port", width=8)
        docker_table.add_column("Technology", width=25)
        docker_table.add_column("Health Check", width=20)
        docker_table.add_column("Container", width=20)
        
        for service_name, service in self.docker_services.items():
            console.print(f"  Checking {service.name}...", style="dim")
            
            # Force real-time Docker status check
            is_running = self.docker_manager.is_docker_service_running(service_name)
            status[f"docker_{service_name}"] = is_running
            
            # Enhanced health check for Docker services
            health_status = "❌ Offline"
            if is_running:
                try:
                    # Check if the service port is accessible
                    port_response_time = self._measure_port_response_time(service.port)
                    if port_response_time:
                        health_status = f"✅ Healthy ({port_response_time}ms)"
                    else:
                        health_status = "⚠️ Starting/No Response"
                except:
                    health_status = "⚠️ Container Running"
            
            if is_running:
                docker_table.add_row(
                    f"[{service.color}]{service.name}[/{service.color}]",
                    "[green]🟢 Running[/green]",
                    str(service.port),
                    service.tech_stack,
                    health_status,
                    service.container_name
                )
            else:
                docker_table.add_row(
                    f"[{service.color}]{service.name}[/{service.color}]",
                    "[red]🔴 Stopped[/red]",
                    str(service.port),
                    service.tech_stack,
                    health_status,
                    service.container_name
                )
        
        console.print(docker_table)
        
        # Enhanced Summary with real-time data
        app_running = sum(1 for k, s in status.items() if s and not k.startswith("docker_"))
        docker_running = sum(1 for k, s in status.items() if s and k.startswith("docker_"))
        total_app = len(self.services)
        total_docker = len(self.docker_services)
        
        console.print(f"\n📊 [bold cyan]Real-Time Summary (checked at {current_time}):[/bold cyan] {app_running}/{total_app} Application Services | {docker_running}/{total_docker} Docker Services", style="cyan")
        
        # Add refresh option hint
        console.print("💡 [dim]Tip: All checks are performed in real-time. Use 'Quick Health Check' for faster connectivity tests.[/dim]")
        
        return status

    def _measure_health_check_time(self, service) -> Optional[int]:
        """Measure health check response time in milliseconds"""
        if not REQUESTS_AVAILABLE:
            return None
            
        try:
            import time
            start_time = time.time()
            response = requests.get(service.health_url, timeout=3)
            end_time = time.time()
            
            if response.status_code == 200:
                return int((end_time - start_time) * 1000)
        except:
            pass
        return None
    
    def _measure_port_response_time(self, port: int) -> Optional[int]:
        """Measure port connectivity response time in milliseconds"""
        try:
            import socket
            start_time = time.time()
            with socket.create_connection(("127.0.0.1", port), timeout=3):
                end_time = time.time()
                return int((end_time - start_time) * 1000)
        except:
            pass
        return None

    def show_running_services(self):
        """Show running services with access URLs"""
        panel_content = []
        panel_content.append("🎉 [bold green]CogniVox Agentic Platform is running![/bold green]\n")
        
        # Application Services
        panel_content.append("[bold cyan]🚀 Application Services:[/bold cyan]")
        for service_name, service in self.services.items():
            if service.process and service.process.poll() is None:
                app_config = self.default_credentials["application_services"][service_name]
                if service_name == "frontend":
                    panel_content.append(f"🌐 [bold blue]{service.name}:[/bold blue] {app_config['url']}")
                elif service_name == "backend":
                    panel_content.append(f"🔧 [bold green]{service.name}:[/bold green] {app_config['api_url']}")
                    panel_content.append(f"📚 [bold green]API Docs:[/bold green] {app_config['docs_url']}")
                    panel_content.append(f"📖 [bold green]ReDoc:[/bold green] {app_config['redoc_url']}")
                else:
                    panel_content.append(f"⚡ [bold {service.color}]{service.name}:[/bold {service.color}] {app_config['api_url']}")
        
        # Docker Infrastructure Services
        panel_content.append(f"\n[bold magenta]🐳 Infrastructure Services:[/bold magenta]")
        for service_name, service in self.docker_services.items():
            if service.is_running:
                if service_name == "neo4j":
                    neo4j_config = self.default_credentials["database"]["neo4j"]
                    panel_content.append(f"📊 [bold green]Neo4j Browser:[/bold green] {neo4j_config['browser_url']}")
                    panel_content.append(f"   [dim]Username: {neo4j_config['username']}, Password: {neo4j_config['password']}[/dim]")
                elif service_name == "pgadmin":
                    pgadmin_config = self.default_credentials["admin_interfaces"]["pgadmin"]
                    panel_content.append(f"🔧 [bold blue]PgAdmin:[/bold blue] {pgadmin_config['url']}")
                    panel_content.append(f"   [dim]Email: {pgadmin_config['email']}, Password: {pgadmin_config['password']}[/dim]")
                elif service_name == "ollama":
                    ollama_config = self.default_credentials["llm_services"]["ollama"]
                    panel_content.append(f"🤖 [bold purple]Ollama API:[/bold purple] {ollama_config['api_url']}")
        
        panel_content.append("\n[yellow]Press Ctrl+C to stop all services[/yellow]")
        
        panel = Panel(
            "\n".join(panel_content),
            title="🚀 Services Running",
            border_style="green",
            padding=(1, 2)
        )
        console.print(panel)

    def show_urls_only(self):
        """Show service URLs in a compact format"""
        self.credentials_manager.show_urls_only()

    def cleanup_temp_files(self):
        """Clean up temporary files created during operation"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    console.print(f"🗑️  Cleaned up: {temp_file}", style="dim")
            except Exception as e:
                console.print(f"⚠️  Failed to clean up {temp_file}: {e}", style="yellow")
        self.temp_files.clear()

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            console.print("\n🛑 Received shutdown signal, stopping services...", style="yellow")
            self.shutdown_requested = True
            self.stop_all_services()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def run_command(self, command: list, timeout: int = 120, cwd: Path = None) -> Tuple[bool, str, str]:
        """Execute a command with timeout and return success, stdout, stderr"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)

    def show_interactive_menu(self):
        """Enhanced hierarchical interactive menu with categories and back navigation"""
        self.current_menu_path = []  # Track menu breadcrumb
        
        while not self.shutdown_requested:
            try:
                self._show_main_menu()
            except KeyboardInterrupt:
                if Confirm.ask("\n🛑 Stop all services and exit?"):
                    self.shutdown_requested = True
                    self.stop_all_services()
                    break
            except Exception as e:
                console.print(f"❌ Menu error: {e}", style="red")
                time.sleep(2)

    def _show_main_menu(self):
        """Display the main categorized menu with real-time status"""
        # Clear screen and show header
        try:
            console.clear()
        except:
            console.print("\n" * 50)
        
        # Show breadcrumb if in submenu
        if hasattr(self, 'current_menu_path') and self.current_menu_path:
            breadcrumb = " > ".join(self.current_menu_path)
            console.print(f"📍 Navigation: Home > {breadcrumb}", style="dim")
            console.print()
        
        console.rule("[bold green]🎮 CogniVox Agentic Platform - Control Panel", style="green")
        
        # Real-time status overview (quick check)
        console.print("🔄 [dim]Checking real-time status...[/dim]", end="")
        
        running_services = []
        total_services = len(self.services)
        running_count = 0
        
        # Quick real-time check for display
        for service_name, service in self.services.items():
            if service.is_running():
                running_services.append(f"[green]{service.name}[/green]")
                running_count += 1
            else:
                running_services.append(f"[red]{service.name}[/red]")
        
        # Status summary with Docker services (real-time)
        docker_running = sum(1 for svc in self.docker_services if self.docker_manager.is_docker_service_running(svc))
        docker_total = len(self.docker_services)
        
        # Clear the "checking..." line and show status
        console.print(f"\r📊 System Status: {running_count}/{total_services} Apps | {docker_running}/{docker_total} Infrastructure | {' | '.join(running_services)}")
        console.print()
        
        # Main menu categories
        menu_panel = Panel(
            "[bold cyan]🎯 Main Menu - Select Category:[/bold cyan]\n\n"
            "[green]1.[/green] 📊 [bold blue]Monitoring & Status[/bold blue]\n"
            "     View service status, URLs, and system health [dim](real-time checks)[/dim]\n\n"
            "[green]2.[/green] ⚙️  [bold green]Service Management[/bold green]\n"
            "     Start, stop, restart individual or all services\n\n"
            "[green]3.[/green] 🐳 [bold purple]Infrastructure Management[/bold purple]\n"
            "     Docker services, databases, and Ollama models\n\n"
            "[green]4.[/green] 🔧 [bold orange]Configuration & Tools[/bold orange]\n"
            "     Settings, credentials, and help documentation\n\n"
            "[green]0.[/green] 🚪 [bold red]Exit[/bold red]\n"
            "     Stop all services and exit the platform\n",
            title="🎮 CogniVox Control Panel",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(menu_panel)
        
        # Get user choice
        choice = Prompt.ask(
            "\n[bold cyan]Select a category[/bold cyan]",
            choices=["1", "2", "3", "4", "0"],
            default="1"
        )
        
        # Handle main menu choices
        if choice == "1":
            self._show_monitoring_menu()
        elif choice == "2":
            self._show_service_management_menu()
        elif choice == "3":
            self._show_infrastructure_menu()
        elif choice == "4":
            self._show_configuration_menu()
        elif choice == "0":
            if Confirm.ask("🛑 Stop all services and exit?"):
                self.shutdown_requested = True
                self.stop_all_services()

    def _show_monitoring_menu(self):
        """Display monitoring and status submenu"""
        self.current_menu_path = ["Monitoring & Status"]
        
        while True:
            try:
                console.clear()
            except:
                console.print("\n" * 50)
            
            console.print(f"📍 Navigation: Home > {' > '.join(self.current_menu_path)}", style="dim")
            console.rule("[bold blue]📊 Monitoring & Status", style="blue")
            
            menu_panel = Panel(
                "[bold blue]Monitoring & Status Options:[/bold blue]\n\n"
                "[green]1.[/green] 📊 [bold]Detailed Service Status[/bold]\n"
                "     Complete status check with health monitoring\n\n"
                "[green]2.[/green] 🌐 [bold]Service URLs & Credentials[/bold]\n"
                "     Access URLs and authentication details\n\n"
                "[green]3.[/green] 📋 [bold]System Logs[/bold] [dim](Coming Soon)[/dim]\n"
                "     Real-time service logs and monitoring\n\n"
                "[green]4.[/green] 🔍 [bold]Quick Health Check[/bold]\n"
                "     Fast connectivity test for all services\n\n"
                "[yellow]b.[/yellow] ← [bold]Back to Main Menu[/bold]\n",
                title="📊 Monitoring & Status",
                border_style="blue",
                padding=(1, 2)
            )
            console.print(menu_panel)
            
            choice = Prompt.ask(
                "\n[bold blue]Select an option[/bold blue]",
                choices=["1", "2", "3", "4", "b"],
                default="1"
            )
            
            if choice == "1":
                self._menu_check_status()
                self._wait_for_continue()
            elif choice == "2":
                self._menu_view_urls()
                self._wait_for_continue()
            elif choice == "3":
                self._menu_view_logs()
                self._wait_for_continue()
            elif choice == "4":
                self._menu_quick_health_check()
                self._wait_for_continue()
            elif choice == "b":
                break

    def _show_service_management_menu(self):
        """Display service management submenu"""
        self.current_menu_path = ["Service Management"]
        
        while True:
            try:
                console.clear()
            except:
                console.print("\n" * 50)
            
            console.print(f"📍 Navigation: Home > {' > '.join(self.current_menu_path)}", style="dim")
            console.rule("[bold green]⚙️ Service Management", style="green")
            
            # Quick service overview
            running_services = [name for name, service in self.services.items() if service.is_running()]
            stopped_services = [name for name, service in self.services.items() if not service.is_running()]
            
            console.print(f"🟢 Running: {len(running_services)} | 🔴 Stopped: {len(stopped_services)}")
            console.print()
            
            menu_panel = Panel(
                "[bold green]Service Management Options:[/bold green]\n\n"
                "[green]1.[/green] ▶️  [bold]Start Service[/bold]\n"
                "     Start a stopped service\n\n"
                "[green]2.[/green] 🛑 [bold]Stop Service[/bold]\n"
                "     Stop a running service\n\n"
                "[green]3.[/green] 🔄 [bold]Restart Service[/bold]\n"
                "     Restart a specific service\n\n"
                "[green]4.[/green] 🔄 [bold]Restart All Services[/bold]\n"
                "     Restart all application services\n\n"
                "[green]5.[/green] ⚡ [bold]Bulk Service Operations[/bold]\n"
                "     Start/stop multiple services at once\n\n"
                "[yellow]b.[/yellow] ← [bold]Back to Main Menu[/bold]\n",
                title="⚙️ Service Management",
                border_style="green",
                padding=(1, 2)
            )
            console.print(menu_panel)
            
            choice = Prompt.ask(
                "\n[bold green]Select an option[/bold green]",
                choices=["1", "2", "3", "4", "5", "b"],
                default="1"
            )
            
            if choice == "1":
                self._menu_start_service()
                self._wait_for_continue()
            elif choice == "2":
                self._menu_stop_service()
                self._wait_for_continue()
            elif choice == "3":
                self._menu_restart_service()
                self._wait_for_continue()
            elif choice == "4":
                self._menu_restart_all()
                self._wait_for_continue()
            elif choice == "5":
                self._menu_bulk_operations()
                self._wait_for_continue()
            elif choice == "b":
                break

    def _show_infrastructure_menu(self):
        """Display infrastructure management submenu"""
        self.current_menu_path = ["Infrastructure Management"]
        
        while True:
            try:
                console.clear()
            except:
                console.print("\n" * 50)
            
            console.print(f"📍 Navigation: Home > {' > '.join(self.current_menu_path)}", style="dim")
            console.rule("[bold purple]🐳 Infrastructure Management", style="purple")
            
            # Infrastructure status overview
            docker_running = sum(1 for svc in self.docker_services if self.is_docker_service_running(svc))
            docker_total = len(self.docker_services)
            
            console.print(f"🐳 Docker Services: {docker_running}/{docker_total} running")
            console.print()
            
            menu_panel = Panel(
                "[bold purple]Infrastructure Management Options:[/bold purple]\n\n"
                "[green]1.[/green] 🐳 [bold]Docker Services[/bold]\n"
                "     Manage PostgreSQL, MongoDB, Neo4j, Ollama containers\n\n"
                "[green]2.[/green] 🗃️  [bold]Database Management[/bold]\n"
                "     Initialize, reset, and manage databases\n\n"
                "[green]3.[/green] 🤖 [bold]Ollama AI Models[/bold]\n"
                "     Install, update, and manage AI models\n\n"
                "[green]4.[/green] 📦 [bold]System Dependencies[/bold]\n"
                "     Check and install system prerequisites\n\n"
                "[green]5.[/green] 🧹 [bold]Cleanup & Maintenance[/bold]\n"
                "     Clean temporary files and reset environments\n\n"
                "[yellow]b.[/yellow] ← [bold]Back to Main Menu[/bold]\n",
                title="🐳 Infrastructure Management",
                border_style="purple",
                padding=(1, 2)
            )
            console.print(menu_panel)
            
            choice = Prompt.ask(
                "\n[bold purple]Select an option[/bold purple]",
                choices=["1", "2", "3", "4", "5", "b"],
                default="1"
            )
            
            if choice == "1":
                self._menu_manage_docker()
                self._wait_for_continue()
            elif choice == "2":
                self._menu_database_management()
                self._wait_for_continue()
            elif choice == "3":
                self._menu_manage_ollama()
                self._wait_for_continue()
            elif choice == "4":
                self._menu_system_dependencies()
                self._wait_for_continue()
            elif choice == "5":
                self._menu_cleanup_maintenance()
                self._wait_for_continue()
            elif choice == "b":
                break

    def _show_configuration_menu(self):
        """Display configuration and tools submenu"""
        self.current_menu_path = ["Configuration & Tools"]
        
        while True:
            try:
                console.clear()
            except:
                console.print("\n" * 50)
            
            console.print(f"📍 Navigation: Home > {' > '.join(self.current_menu_path)}", style="dim")
            console.rule("[bold orange]🔧 Configuration & Tools", style="yellow")
            
            menu_panel = Panel(
                "[bold yellow]Configuration & Tools Options:[/bold yellow]\n\n"
                "[green]1.[/green] ⚙️  [bold]Configuration Management[/bold]\n"
                "     Manage settings, credentials, and environment\n\n"
                "[green]2.[/green] 📤 [bold]Export Credentials[/bold]\n"
                "     Export configurations in various formats\n\n"
                "[green]3.[/green] 🔧 [bold]Environment Setup[/bold]\n"
                "     Reinstall dependencies and reset environments\n\n"
                "[green]4.[/green] 📚 [bold]Help & Documentation[/bold]\n"
                "     Platform guide and troubleshooting\n\n"
                "[green]5.[/green] ℹ️  [bold]System Information[/bold]\n"
                "     Platform version and system details\n\n"
                "[yellow]b.[/yellow] ← [bold]Back to Main Menu[/bold]\n",
                title="🔧 Configuration & Tools",
                border_style="yellow",
                padding=(1, 2)
            )
            console.print(menu_panel)
            
            choice = Prompt.ask(
                "\n[bold yellow]Select an option[/bold yellow]",
                choices=["1", "2", "3", "4", "5", "b"],
                default="1"
            )
            
            if choice == "1":
                self._menu_configuration()
                self._wait_for_continue()
            elif choice == "2":
                self._menu_export_credentials()
                self._wait_for_continue()
            elif choice == "3":
                self._menu_environment_setup()
                self._wait_for_continue()
            elif choice == "4":
                self._menu_show_help()
                self._wait_for_continue()
            elif choice == "5":
                self._menu_system_info()
                self._wait_for_continue()
            elif choice == "b":
                break

    def _wait_for_continue(self):
        """Wait for user to continue"""
        Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")

    def _menu_check_status(self):
        """Menu option: Check service status"""
        self.check_service_status()

    def _menu_view_urls(self):
        """Menu option: View service URLs"""
        console.rule("[bold cyan]Service URLs and Credentials")
        self.show_all_credentials()

    def _menu_restart_service(self):
        """Menu option: Restart a specific service"""
        service_choices = list(self.services.keys())
        
        console.print("\n🔄 [bold cyan]Restart Service[/bold cyan]")
        console.print("Available services:")
        for i, service_name in enumerate(service_choices, 1):
            status = "🟢 Running" if self.services[service_name].is_running() else "🔴 Stopped"
            console.print(f"  {i}. {self.services[service_name].name} ({status})")
        
        try:
            choice = Prompt.ask("Select service number", choices=[str(i) for i in range(1, len(service_choices) + 1)])
            service_name = service_choices[int(choice) - 1]
            
            console.print(f"🔄 Restarting {self.services[service_name].name}...")
            self.stop_service(service_name)
            time.sleep(2)
            self.start_service(service_name)
            
        except (ValueError, KeyboardInterrupt):
            console.print("❌ Invalid selection", style="red")

    def _menu_stop_service(self):
        """Menu option: Stop a specific service"""
        running_services = [name for name, service in self.services.items() if service.is_running()]
        
        if not running_services:
            console.print("ℹ️  No services are currently running", style="yellow")
            return
        
        console.print("\n🛑 [bold yellow]Stop Service[/bold yellow]")
        console.print("Running services:")
        for i, service_name in enumerate(running_services, 1):
            console.print(f"  {i}. {self.services[service_name].name}")
        
        try:
            choice = Prompt.ask("Select service number", choices=[str(i) for i in range(1, len(running_services) + 1)])
            service_name = running_services[int(choice) - 1]
            self.stop_service(service_name)
        except (ValueError, KeyboardInterrupt):
            console.print("❌ Invalid selection", style="red")

    def _menu_start_service(self):
        """Menu option: Start a stopped service"""
        stopped_services = [name for name, service in self.services.items() if not service.is_running()]
        
        if not stopped_services:
            console.print("ℹ️  All services are currently running", style="green")
            return
        
        console.print("\n▶️  [bold green]Start Service[/bold green]")
        console.print("Stopped services:")
        for i, service_name in enumerate(stopped_services, 1):
            console.print(f"  {i}. {self.services[service_name].name}")
        
        try:
            choice = Prompt.ask("Select service number", choices=[str(i) for i in range(1, len(stopped_services) + 1)])
            service_name = stopped_services[int(choice) - 1]
            self.start_service(service_name)
        except (ValueError, KeyboardInterrupt):
            console.print("❌ Invalid selection", style="red")

    def _menu_manage_docker(self):
        """Menu option: Manage Docker services with back navigation"""
        self.current_menu_path.append("Docker Services")
        
        while True:
            try:
                console.clear()
            except:
                console.print("\n" * 50)
            
            console.print(f"📍 Navigation: Home > {' > '.join(self.current_menu_path)}", style="dim")
            console.rule("[bold cyan]🐳 Docker Service Management", style="cyan")
            
            # Docker status overview
            docker_running = sum(1 for svc in self.docker_services if self.is_docker_service_running(svc))
            docker_total = len(self.docker_services)
            
            # Show current Docker service status
            console.print(f"📊 Docker Services Status: {docker_running}/{docker_total} running\n")
            
            for service_name, service in self.docker_services.items():
                status = "🟢 Running" if self.is_docker_service_running(service_name) else "🔴 Stopped"
                console.print(f"  • {service.name}: {status} (Port {service.port})")
            
            console.print()
            
            menu_panel = Panel(
                "[bold cyan]Docker Service Management Options:[/bold cyan]\n\n"
                "[green]1.[/green] 🚀 [bold]Start All Docker Services[/bold]\n"
                "     Start all infrastructure containers\n\n"
                "[green]2.[/green] 🛑 [bold]Stop All Docker Services[/bold]\n"
                "     Stop all infrastructure containers\n\n"
                "[green]3.[/green] 📊 [bold]Detailed Docker Status[/bold]\n"
                "     Show comprehensive container information\n\n"
                "[green]4.[/green] ▶️  [bold]Start Specific Service[/bold]\n"
                "     Start an individual Docker service\n\n"
                "[green]5.[/green] 🛑 [bold]Stop Specific Service[/bold]\n"
                "     Stop an individual Docker service\n\n"
                "[green]6.[/green] 🔄 [bold]Restart Docker Services[/bold]\n"
                "     Restart all or specific services\n\n"
                "[green]7.[/green] 🧹 [bold]Clean Up Docker Conflicts[/bold]\n"
                "     Remove conflicting containers while preserving data\n\n"
                "[green]8.[/green] 🚀 [bold]Start with Auto-Cleanup[/bold]\n"
                "     Start services with automatic conflict resolution\n\n"
                "[yellow]b.[/yellow] ← [bold]Back to Infrastructure Menu[/bold]\n",
                title="🐳 Docker Service Management",
                border_style="cyan",
                padding=(1, 2)
            )
            console.print(menu_panel)
            
            choice = Prompt.ask(
                "\n[bold cyan]Select an option[/bold cyan]",
                choices=["1", "2", "3", "4", "5", "6", "7", "8", "b"],
                default="3"
            )
            
            if choice == "1":
                console.print("🚀 Starting all Docker services...")
                # Use cleanup method by default to avoid conflicts
                if self.start_docker_services_with_cleanup():
                    console.print("✅ All Docker services started successfully", style="green")
                else:
                    console.print("❌ Failed to start some Docker services", style="red")
                self._wait_for_continue()
                
            elif choice == "2":
                if Confirm.ask("🛑 Stop all Docker services?"):
                    console.print("🛑 Stopping all Docker services...")
                    if self.stop_docker_services():
                        console.print("✅ All Docker services stopped", style="green")
                    else:
                        console.print("❌ Failed to stop some Docker services", style="red")
                self._wait_for_continue()
                
            elif choice == "3":
                # Show comprehensive Docker service status
                docker_table = Table(title="🐳 Docker Infrastructure Services", style="magenta")
                docker_table.add_column("Service", style="bold", width=20)
                docker_table.add_column("Status", width=15)
                docker_table.add_column("Port", width=8)
                docker_table.add_column("Technology", width=25)
                docker_table.add_column("Container", width=20)
                
                for service_name, service in self.docker_services.items():
                    is_running = self.is_docker_service_running(service_name)
                    status = "[green]🟢 Running[/green]" if is_running else "[red]🔴 Stopped[/red]"
                    
                    docker_table.add_row(
                        f"[{service.color}]{service.name}[/{service.color}]",
                        status,
                        str(service.port),
                        service.tech_stack,
                        service.container_name
                    )
                
                console.print(docker_table)
                self._wait_for_continue()
                
            elif choice == "4":
                stopped_services = [name for name in self.docker_services if not self.is_docker_service_running(name)]
                if stopped_services:
                    console.print("🔍 Select Docker service to start:")
                    for i, name in enumerate(stopped_services, 1):
                        console.print(f"  {i}. {self.docker_services[name].name}")
                    
                    try:
                        service_choice = Prompt.ask("Select service", choices=[str(i) for i in range(1, len(stopped_services) + 1)])
                        service_name = stopped_services[int(service_choice) - 1]
                        
                        console.print(f"🚀 Starting {self.docker_services[service_name].name}...")
                        # Use cleanup method for individual services too
                        if self.start_docker_services_with_cleanup([service_name]):
                            console.print(f"✅ {self.docker_services[service_name].name} started", style="green")
                        else:
                            console.print(f"❌ Failed to start {self.docker_services[service_name].name}", style="red")
                    except (ValueError, KeyboardInterrupt):
                        console.print("❌ Invalid selection", style="red")
                else:
                    console.print("ℹ️  All Docker services are already running", style="green")
                self._wait_for_continue()
                
            elif choice == "5":
                running_services = [name for name in self.docker_services if self.is_docker_service_running(name)]
                if running_services:
                    console.print("🔍 Select Docker service to stop:")
                    for i, name in enumerate(running_services, 1):
                        console.print(f"  {i}. {self.docker_services[name].name}")
                    
                    try:
                        service_choice = Prompt.ask("Select service", choices=[str(i) for i in range(1, len(running_services) + 1)])
                        service_name = running_services[int(service_choice) - 1]
                        
                        console.print(f"🛑 Stopping {self.docker_services[service_name].name}...")
                        if self.stop_docker_services([service_name]):
                            console.print(f"✅ {self.docker_services[service_name].name} stopped", style="green")
                        else:
                            console.print(f"❌ Failed to stop {self.docker_services[service_name].name}", style="red")
                    except (ValueError, KeyboardInterrupt):
                        console.print("❌ Invalid selection", style="red")
                else:
                    console.print("ℹ️  No Docker services are currently running", style="yellow")
                self._wait_for_continue()
                
            elif choice == "6":
                console.print("🔄 [bold cyan]Restart Docker Services[/bold cyan]")
                console.print("1. Restart all services")
                console.print("2. Restart specific service")
                
                restart_choice = Prompt.ask("Select restart option", choices=["1", "2"])
                
                if restart_choice == "1":
                    if Confirm.ask("🔄 Restart all Docker services?"):
                        console.print("🔄 Restarting all Docker services...")
                        self.stop_docker_services()
                        time.sleep(3)
                        if self.start_docker_services():
                            console.print("✅ All Docker services restarted", style="green")
                        else:
                            console.print("❌ Failed to restart some services", style="red")
                elif restart_choice == "2":
                    running_services = [name for name in self.docker_services if self.is_docker_service_running(name)]
                    if running_services:
                        console.print("🔍 Select service to restart:")
                        for i, name in enumerate(running_services, 1):
                            console.print(f"  {i}. {self.docker_services[name].name}")
                        
                        try:
                            service_choice = Prompt.ask("Select service", choices=[str(i) for i in range(1, len(running_services) + 1)])
                            service_name = running_services[int(service_choice) - 1]
                            
                            console.print(f"🔄 Restarting {self.docker_services[service_name].name}...")
                            self.stop_docker_services([service_name])
                            time.sleep(2)
                            if self.start_docker_services([service_name]):
                                console.print(f"✅ {self.docker_services[service_name].name} restarted", style="green")
                            else:
                                console.print(f"❌ Failed to restart {self.docker_services[service_name].name}", style="red")
                        except (ValueError, KeyboardInterrupt):
                            console.print("❌ Invalid selection", style="red")
                    else:
                        console.print("ℹ️  No running services to restart", style="yellow")
                self._wait_for_continue()
                
            elif choice == "7":
                console.print("🧹 [bold yellow]Docker Cleanup Operation[/bold yellow]")
                console.print("This will remove conflicting containers while preserving all data.")
                
                if Confirm.ask("Proceed with Docker cleanup?"):
                    # First ensure external resources exist
                    if self.ensure_external_resources():
                        console.print("✅ External resources prepared", style="green")
                    else:
                        console.print("⚠️  Some external resources failed, continuing...", style="yellow")
                    
                    # Clean up containers
                    if self.cleanup_conflicting_containers():
                        console.print("✅ Docker cleanup completed successfully", style="green")
                    else:
                        console.print("❌ Some containers failed to clean up", style="red")
                else:
                    console.print("Docker cleanup cancelled", style="yellow")
                self._wait_for_continue()
                
            elif choice == "8":
                console.print("🚀 [bold green]Starting Docker services with auto-cleanup...[/bold green]")
                if self.start_docker_services_with_cleanup():
                    console.print("✅ All Docker services started with cleanup", style="green")
                else:
                    console.print("❌ Failed to start some Docker services", style="red")
                self._wait_for_continue()
                
            elif choice == "b":
                break
        
        # Remove from breadcrumb when going back
        self.current_menu_path.pop()

    def _menu_manage_ollama(self):
        """Menu option: Manage Ollama models with back navigation"""
        self.current_menu_path.append("Ollama AI Models")
        
        while True:
            try:
                console.clear()
            except:
                console.print("\n" * 50)
            
            console.print(f"📍 Navigation: Home > {' > '.join(self.current_menu_path)}", style="dim")
            console.rule("[bold purple]🤖 Ollama AI Model Management", style="purple")
            
            # Check if Ollama is running
            ollama_running = self.is_docker_service_running("ollama")
            console.print(f"📊 Ollama Service: {'🟢 Running' if ollama_running else '🔴 Stopped'}")
            console.print()
            
            if not ollama_running:
                console.print("⚠️  [bold yellow]Ollama service is not running![/bold yellow]")
                if Confirm.ask("Start Ollama service now?"):
                    console.print("🚀 Starting Ollama service...")
                    if self.start_docker_services(["ollama"]):
                        console.print("✅ Ollama service started", style="green")
                        time.sleep(3)  # Give it time to start
                        ollama_running = True
                    else:
                        console.print("❌ Failed to start Ollama service", style="red")
                        self._wait_for_continue()
                        continue
                else:
                    console.print("❌ Cannot manage models without Ollama service", style="red")
                    self._wait_for_continue()
                    continue
            
            menu_panel = Panel(
                "[bold purple]Ollama AI Model Management Options:[/bold purple]\n\n"
                "[green]1.[/green] 📋 [bold]List Installed Models[/bold]\n"
                "     Show all currently installed AI models\n\n"
                "[green]2.[/green] 📦 [bold]Install Default Models[/bold]\n"
                "     Install recommended models (llama3.1, qwen3:4b, etc.)\n\n"
                "[green]3.[/green] ⬇️  [bold]Pull Specific Model[/bold]\n"
                "     Download and install a specific model\n\n"
                "[green]4.[/green] 🎯 [bold]Install Custom Models[/bold]\n"
                "     Install multiple custom models\n\n"
                "[green]5.[/green] 🗑️  [bold]Remove Models[/bold] [dim](Coming Soon)[/dim]\n"
                "     Remove unused models to free space\n\n"
                "[green]6.[/green] ℹ️  [bold]Model Information[/bold]\n"
                "     Show detailed model information\n\n"
                "[yellow]b.[/yellow] ← [bold]Back to Infrastructure Menu[/bold]\n",
                title="🤖 Ollama AI Model Management",
                border_style="purple",
                padding=(1, 2)
            )
            console.print(menu_panel)
            
            choice = Prompt.ask(
                "\n[bold purple]Select an option[/bold purple]",
                choices=["1", "2", "3", "4", "5", "6", "b"],
                default="1"
            )
            
            if choice == "1":
                console.print("📋 [bold]Listing Installed Models...[/bold]")
                success, stdout, stderr = self.run_command(["docker", "exec", "agentic-ollama", "ollama", "list"])
                if success:
                    console.print("✅ Installed Models:")
                    console.print(stdout)
                else:
                    console.print(f"❌ Failed to list models: {stderr}", style="red")
                self._wait_for_continue()
                
            elif choice == "2":
                if Confirm.ask("📦 Install default recommended models? This may take several minutes."):
                    console.print("📦 Installing default models (llama3.1:latest, qwen3:4b, mistral:latest, nomic-embed-text:latest)...")
                    if self.install_ollama_models():
                        console.print("✅ Default models installed successfully", style="green")
                    else:
                        console.print("❌ Failed to install some models", style="red")
                self._wait_for_continue()
                
            elif choice == "3":
                model_name = Prompt.ask("🎯 Enter model name to pull (e.g., 'llama3.1', 'mistral:7b')")
                if model_name:
                    console.print(f"⬇️  Pulling model: {model_name}")
                    if self.install_ollama_models([model_name]):
                        console.print(f"✅ Model '{model_name}' installed successfully", style="green")
                    else:
                        console.print(f"❌ Failed to install model '{model_name}'", style="red")
                self._wait_for_continue()
                
            elif choice == "4":
                models_input = Prompt.ask("🎯 Enter model names (comma-separated, e.g., 'llama3.1,mistral:7b')")
                if models_input:
                    models = [model.strip() for model in models_input.split(",") if model.strip()]
                    if models:
                        console.print(f"📦 Installing {len(models)} custom models...")
                        if self.install_ollama_models(models):
                            console.print("✅ Custom models installed successfully", style="green")
                        else:
                            console.print("❌ Failed to install some models", style="red")
                    else:
                        console.print("❌ No valid models specified", style="red")
                self._wait_for_continue()
                
            elif choice == "5":
                console.print("🗑️  [bold yellow]Model Removal[/bold yellow]")
                console.print("🚧 This feature is coming soon!")
                console.print("For now, you can manually remove models using:")
                console.print("  docker exec -it agentic-ollama ollama rm <model_name>")
                self._wait_for_continue()
                
            elif choice == "6":
                console.print("ℹ️  [bold cyan]Model Information[/bold cyan]")
                
                # Get model info
                success, stdout, stderr = self.run_command(["docker", "exec", "agentic-ollama", "ollama", "list"])
                if success:
                    console.print("📊 [bold]Current Models:[/bold]")
                    console.print(stdout)
                    
                    # Additional Ollama info
                    console.print("\n🔧 [bold]Ollama Service Info:[/bold]")
                    console.print(f"🐳 Container: agentic-ollama")
                    console.print(f"🌐 API URL: http://localhost:11434")
                    console.print(f"📡 API Endpoint: http://localhost:11434/api/generate")
                    
                    console.print("\n💡 [bold]Useful Commands:[/bold]")
                    console.print("• List models: docker exec -it agentic-ollama ollama list")
                    console.print("• Pull model: docker exec -it agentic-ollama ollama pull <model>")
                    console.print("• Remove model: docker exec -it agentic-ollama ollama rm <model>")
                    console.print("• Show model info: docker exec -it agentic-ollama ollama show <model>")
                else:
                    console.print(f"❌ Failed to get model information: {stderr}", style="red")
                self._wait_for_continue()
                
            elif choice == "b":
                break
        
        # Remove from breadcrumb when going back
        self.current_menu_path.pop()

    def _menu_database_management(self):
        """Menu option: Database management with back navigation"""
        self.current_menu_path.append("Database Management")
        
        while True:
            try:
                console.clear()
            except:
                console.print("\n" * 50)
            
            console.print(f"📍 Navigation: Home > {' > '.join(self.current_menu_path)}", style="dim")
            console.rule("[bold cyan]🗃️ Database Management", style="cyan")
            
            # Database status overview
            postgres_status = self.is_docker_service_running("postgres")
            mongodb_status = self.is_docker_service_running("mongodb")
            neo4j_status = self.is_docker_service_running("neo4j")
            
            console.print(f"📊 Database Services Status:")
            console.print(f"  • PostgreSQL: {'🟢 Running' if postgres_status else '🔴 Stopped'} (Port 5432)")
            console.print(f"  • MongoDB: {'🟢 Running' if mongodb_status else '🔴 Stopped'} (Port 27017)")
            console.print(f"  • Neo4j: {'🟢 Running' if neo4j_status else '🔴 Stopped'} (Port 7474/7687)")
            console.print()
            
            menu_panel = Panel(
                "[bold cyan]Database Management Options:[/bold cyan]\n\n"
                "[green]1.[/green] 📊 [bold]Database Status Check[/bold]\n"
                "     Detailed status of all database services\n\n"
                "[green]2.[/green] 🗃️  [bold]Initialize Databases[/bold]\n"
                "     Create/reset database schemas and users\n\n"
                "[green]3.[/green] 🔄 [bold]Reset All Databases[/bold]\n"
                "     ⚠️  Completely reset all databases (DATA LOSS!)\n\n"
                "[green]4.[/green] 🔧 [bold]Database Maintenance[/bold]\n"
                "     Backup, restore, and optimization tools\n\n"
                "[green]5.[/green] 🌐 [bold]Database Access URLs[/bold]\n"
                "     Connection strings and admin interfaces\n\n"
                "[green]6.[/green] 📋 [bold]Database Logs[/bold]\n"
                "     View database container logs\n\n"
                "[yellow]b.[/yellow] ← [bold]Back to Infrastructure Menu[/bold]\n",
                title="🗃️ Database Management",
                border_style="cyan",
                padding=(1, 2)
            )
            console.print(menu_panel)
            
            choice = Prompt.ask(
                "\n[bold cyan]Select an option[/bold cyan]",
                choices=["1", "2", "3", "4", "5", "6", "b"],
                default="1"
            )
            
            if choice == "1":
                console.print("📊 [bold cyan]Detailed Database Status:[/bold cyan]")
                
                # Check each database service
                for db_name, service in [("postgres", "PostgreSQL"), ("mongodb", "MongoDB"), ("neo4j", "Neo4j")]:
                    is_running = self.is_docker_service_running(db_name)
                    console.print(f"\n🔍 {service}:")
                    console.print(f"  Status: {'🟢 Running' if is_running else '🔴 Stopped'}")
                    
                    if is_running:
                        # Check if port is accessible
                        try:
                            import socket
                            port = {"postgres": 5432, "mongodb": 27017, "neo4j": 7474}[db_name]
                            with socket.create_connection(("127.0.0.1", port), timeout=2):
                                console.print(f"  Port {port}: ✅ Accessible")
                        except:
                            console.print(f"  Port {port}: ❌ Not accessible")
                    
                    # Show container logs (last few lines)
                    if is_running:
                        success, stdout, stderr = self.run_command(["docker", "logs", f"agentic-{db_name}", "--tail", "3"])
                        if success and stdout:
                            console.print(f"  Last log: {stdout.split(chr(10))[-2] if chr(10) in stdout else stdout[:100]}...")
                
                self._wait_for_continue()
                
            elif choice == "2":
                if Confirm.ask("🗃️  Initialize databases? This will create required schemas and users."):
                    console.print("🗃️  Initializing databases...")
                    if self.initialize_databases(reset=True):
                        console.print("✅ Databases initialized successfully", style="green")
                    else:
                        console.print("❌ Database initialization failed", style="red")
                self._wait_for_continue()
                
            elif choice == "3":
                console.print("⚠️  [bold red]WARNING: This will delete ALL data![/bold red]")
                console.print("This operation will:")
                console.print("• Drop all databases")
                console.print("• Remove all users")
                console.print("• Delete all stored data")
                console.print("• Reset to factory state")
                
                if Confirm.ask("\n❗ Are you sure you want to reset ALL databases?"):
                    if Confirm.ask("❗ This cannot be undone. Continue?"):
                        console.print("🔄 Resetting all databases...")
                        if self.reset_all_databases():
                            console.print("✅ All databases reset successfully", style="green")
                        else:
                            console.print("❌ Database reset failed", style="red")
                self._wait_for_continue()
                
            elif choice == "4":
                console.print("🔧 [bold cyan]Database Maintenance[/bold cyan]")
                console.print("🚧 Advanced maintenance features coming soon!")
                console.print("\nAvailable maintenance operations:")
                console.print("• Backup: Use Docker volume backup")
                console.print("• Restore: Restore from Docker volume backup")
                console.print("• Optimize: Database-specific optimization commands")
                console.print("• Vacuum: PostgreSQL VACUUM and ANALYZE")
                console.print("• Reindex: Rebuild database indexes")
                self._wait_for_continue()
                
            elif choice == "5":
                console.print("🌐 [bold cyan]Database Access Information:[/bold cyan]")
                
                console.print("\n🐘 [bold]PostgreSQL:[/bold]")
                console.print("  • Host: localhost:5432")
                console.print("  • Username: postgres")
                console.print("  • Password: password") 
                console.print("  • Database: cognivox")
                console.print("  • PgAdmin: http://localhost:5050")
                
                console.print("\n🍃 [bold]MongoDB:[/bold]")
                console.print("  • Host: localhost:27017")
                console.print("  • Username: admin")
                console.print("  • Password: password")
                console.print("  • Database: cognivox")
                console.print("  • Connection: mongodb://admin:password@localhost:27017/cognivox")
                
                console.print("\n🕸️  [bold]Neo4j:[/bold]")
                console.print("  • Browser: http://localhost:7474")
                console.print("  • Bolt: bolt://localhost:7687")
                console.print("  • Username: neo4j")
                console.print("  • Password: password")
                
                self._wait_for_continue()
                
            elif choice == "6":
                console.print("📋 [bold cyan]Database Container Logs:[/bold cyan]")
                
                for db_name in ["postgres", "mongodb", "neo4j"]:
                    if self.is_docker_service_running(db_name):
                        console.print(f"\n📋 {db_name.title()} Logs (last 10 lines):")
                        success, stdout, stderr = self.run_command(["docker", "logs", f"agentic-{db_name}", "--tail", "10"])
                        if success:
                            console.print(stdout)
                        else:
                            console.print(f"❌ Failed to get logs: {stderr}")
                    else:
                        console.print(f"\n📋 {db_name.title()}: Service not running")
                
                self._wait_for_continue()
                
            elif choice == "b":
                break
        
        # Remove from breadcrumb when going back
        self.current_menu_path.pop()

    def _menu_view_logs(self):
        """Menu option: View real-time logs (placeholder)"""
        console.print("\n📋 [bold yellow]Real-time Logs[/bold yellow]")
        console.print("🚧 This feature is coming soon!")
        console.print("For now, check the individual terminal windows for each service.")

    def _menu_configuration(self):
        """Menu option: Configuration management"""
        console.print("\n⚙️  [bold cyan]Configuration Management[/bold cyan]")
        console.print("1. Create/regenerate credentials file")
        console.print("2. Create/regenerate .env file")
        console.print("3. Validate configuration")
        console.print("4. Show current configuration")
        
        try:
            choice = Prompt.ask("Select option", choices=["1", "2", "3", "4"])
            
            if choice == "1":
                success = self.create_credentials_file()
                if success:
                    console.print("✅ Credentials file created/updated", style="green")
                else:
                    console.print("❌ Failed to create credentials file", style="red")
            elif choice == "2":
                success = self.create_env_file()
                if success:
                    console.print("✅ Environment file created/updated", style="green")
                else:
                    console.print("❌ Failed to create environment file", style="red")
            elif choice == "3":
                success = self.validate_configuration()
                if success:
                    console.print("✅ Configuration is valid", style="green")
                else:
                    console.print("❌ Configuration validation failed", style="red")
            elif choice == "4":
                self.show_all_credentials()
                
        except (ValueError, KeyboardInterrupt):
            console.print("❌ Invalid selection", style="red")

    def _menu_restart_all(self):
        """Menu option: Restart all services"""
        if Confirm.ask("🔄 Restart all services?"):
            console.print("🔄 Restarting all services...", style="yellow")
            self.stop_all_services()
            time.sleep(3)
            self.start_all_services()

    def _menu_export_credentials(self):
        """Menu option: Export credentials"""
        console.print("\n📤 [bold cyan]Export Credentials[/bold cyan]")
        console.print("1. Export as JSON")
        console.print("2. Export as .env file")
        
        try:
            choice = Prompt.ask("Select format", choices=["1", "2"])
            
            if choice == "1":
                filename = Prompt.ask("Output filename (optional)", default="")
                success = self.export_credentials("json", filename if filename else None)
            elif choice == "2":
                filename = Prompt.ask("Output filename (optional)", default="")
                success = self.export_credentials("env", filename if filename else None)
            else:
                return
                
            if success:
                console.print("✅ Credentials exported successfully", style="green")
            else:
                console.print("❌ Failed to export credentials", style="red")
                
        except (ValueError, KeyboardInterrupt):
            console.print("❌ Invalid selection", style="red")

    def _menu_show_help(self):
        """Menu option: Show help and documentation"""
        help_panel = Panel(
            "[bold cyan]CogniVox Agentic Platform Help[/bold cyan]\n\n"
            "[yellow]Service Architecture:[/yellow]\n"
            "• [green]Backend API[/green] (Port 8000): Core FastAPI application with authentication, database\n"
            "• [purple]Memory Service[/purple] (Port 8002): LangChain/LangGraph-based memory and chat\n"
            "• [cyan]Graph RAG Service[/cyan] (Port 8003): LlamaIndex + Neo4j for document processing\n"
            "• [blue]Frontend[/blue] (Port 3000): React TypeScript application\n\n"
            "[yellow]Infrastructure Services:[/yellow]\n"
            "• PostgreSQL (Port 5432): Main application database\n"
            "• MongoDB (Port 27017): Document and session storage\n"
            "• Neo4j (Port 7474/7687): Graph database for RAG\n"
            "• Ollama (Port 11434): Local LLM service\n"
            "• PgAdmin (Port 5050): Database administration\n\n"
            "[yellow]Key Commands:[/yellow]\n"
            "• Use the menu to manage services while they're running\n"
            "• Check status regularly to ensure all services are healthy\n"
            "• View URLs to access different service interfaces\n"
            "• Use Docker management for infrastructure services\n"
            "• Export credentials for external integrations\n\n"
            "[yellow]Troubleshooting:[/yellow]\n"
            "• If a service fails, try restarting it individually first\n"
            "• Check Docker services are running for dependencies\n"
            "• Validate configuration if services won't start\n"
            "• Use separate terminal windows to view service logs\n\n"
            "[yellow]Documentation:[/yellow]\n"
            "• Check the /documents folder for detailed technical docs\n"
            "• Visit service URLs for API documentation\n",
            title="📚 Help & Documentation",
            border_style="yellow"
        )
        console.print(help_panel)

    def _menu_quick_health_check(self):
        """Menu option: Quick connectivity test for all services with real-time checking"""
        console.print("\n🔍 [bold cyan]Quick Health Check - Real-Time Connectivity Test[/bold cyan]")
        console.print("🔄 Performing fast real-time connectivity tests...\n")
        
        current_time = time.strftime("%H:%M:%S")
        
        # Check application services with timing
        app_healthy = 0
        app_total = len(self.services)
        
        console.print("🚀 [bold]Application Services:[/bold]")
        for service_name, service in self.services.items():
            console.print(f"  Checking {service.name}...", style="dim", end="")
            
            try:
                start_time = time.time()
                if service._check_health():
                    end_time = time.time()
                    response_time = int((end_time - start_time) * 1000)
                    console.print(f"\r✅ {service.name}: [green]Healthy ({response_time}ms)[/green]")
                    app_healthy += 1
                else:
                    console.print(f"\r❌ {service.name}: [red]Unhealthy/Offline[/red]")
            except Exception as e:
                console.print(f"\r❌ {service.name}: [red]Error - {str(e)[:30]}...[/red]")
        
        # Check Docker services with timing
        docker_healthy = 0
        docker_total = len(self.docker_services)
        
        console.print("\n🐳 [bold]Docker Infrastructure Services:[/bold]")
        for service_name, service in self.docker_services.items():
            console.print(f"  Checking {service.name}...", style="dim", end="")
            
            start_time = time.time()
            if self.docker_manager.is_docker_service_running(service_name):
                # Quick port check with timing
                try:
                    import socket
                    with socket.create_connection(("127.0.0.1", service.port), timeout=2):
                        end_time = time.time()
                        response_time = int((end_time - start_time) * 1000)
                        console.print(f"\r✅ {service.name}: [green]Running & Accessible ({response_time}ms)[/green]")
                        docker_healthy += 1
                except:
                    end_time = time.time()
                    response_time = int((end_time - start_time) * 1000)
                    console.print(f"\r⚠️  {service.name}: [yellow]Running but Port Inaccessible ({response_time}ms timeout)[/yellow]")
            else:
                console.print(f"\r❌ {service.name}: [red]Stopped[/red]")
        
        # Summary with timestamp
        console.print(f"\n📊 [bold cyan]Health Summary (checked at {current_time}):[/bold cyan]")
        console.print(f"• Application Services: {app_healthy}/{app_total} healthy")
        console.print(f"• Infrastructure Services: {docker_healthy}/{docker_total} healthy")
        
        if app_healthy == app_total and docker_healthy == docker_total:
            console.print("🎉 [bold green]All systems are healthy![/bold green]")
        else:
            console.print("⚠️  [bold yellow]Some services need attention[/bold yellow]")
        
        console.print("💡 [dim]This was a real-time connectivity test. For detailed status, use 'Detailed Service Status'.[/dim]")

    def _menu_bulk_operations(self):
        """Menu option: Bulk service operations"""
        console.print("\n⚡ [bold cyan]Bulk Service Operations[/bold cyan]")
        console.print("1. Start all stopped services")
        console.print("2. Stop all running services")
        console.print("3. Restart all services")
        console.print("4. Start selected services")
        console.print("5. Stop selected services")
        
        try:
            choice = Prompt.ask("Select bulk operation", choices=["1", "2", "3", "4", "5"])
            
            if choice == "1":
                stopped_services = [name for name, service in self.services.items() if not service.is_running()]
                if stopped_services:
                    console.print(f"Starting {len(stopped_services)} stopped services...")
                    for service_name in stopped_services:
                        console.print(f"🔄 Starting {self.services[service_name].name}")
                        self.start_service(service_name)
                else:
                    console.print("ℹ️  All services are already running", style="green")
                    
            elif choice == "2":
                running_services = [name for name, service in self.services.items() if service.is_running()]
                if running_services and Confirm.ask(f"Stop {len(running_services)} running services?"):
                    for service_name in running_services:
                        console.print(f"🛑 Stopping {self.services[service_name].name}")
                        self.stop_service(service_name)
                        
            elif choice == "3":
                if Confirm.ask("Restart all application services?"):
                    self.stop_all_services()
                    time.sleep(3)
                    self.start_all_services()
                    
            elif choice == "4":
                stopped_services = [name for name, service in self.services.items() if not service.is_running()]
                if stopped_services:
                    console.print("Select services to start (comma-separated numbers):")
                    for i, service_name in enumerate(stopped_services, 1):
                        console.print(f"  {i}. {self.services[service_name].name}")
                    
                    selection = Prompt.ask("Enter numbers")
                    try:
                        indices = [int(x.strip()) - 1 for x in selection.split(",")]
                        for idx in indices:
                            if 0 <= idx < len(stopped_services):
                                service_name = stopped_services[idx]
                                console.print(f"🔄 Starting {self.services[service_name].name}")
                                self.start_service(service_name)
                    except ValueError:
                        console.print("❌ Invalid selection format", style="red")
                else:
                    console.print("ℹ️  No stopped services available", style="yellow")
                    
            elif choice == "5":
                running_services = [name for name, service in self.services.items() if service.is_running()]
                if running_services:
                    console.print("Select services to stop (comma-separated numbers):")
                    for i, service_name in enumerate(running_services, 1):
                        console.print(f"  {i}. {self.services[service_name].name}")
                    
                    selection = Prompt.ask("Enter numbers")
                    try:
                        indices = [int(x.strip()) - 1 for x in selection.split(",")]
                        for idx in indices:
                            if 0 <= idx < len(running_services):
                                service_name = running_services[idx]
                                console.print(f"🛑 Stopping {self.services[service_name].name}")
                                self.stop_service(service_name)
                    except ValueError:
                        console.print("❌ Invalid selection format", style="red")
                else:
                    console.print("ℹ️  No running services available", style="yellow")
                    
        except (ValueError, KeyboardInterrupt):
            console.print("❌ Invalid selection", style="red")

    def _menu_system_dependencies(self):
        """Menu option: Check and install system prerequisites"""
        console.print("\n📦 [bold cyan]System Dependencies[/bold cyan]")
        console.print("Checking system prerequisites...\n")
        
        # Run prerequisite check
        prereq_result = self.prerequisite_checker.check_all_prerequisites()
        
        console.print(f"\n📊 [bold cyan]Prerequisites Summary:[/bold cyan]")
        if prereq_result:
            console.print("✅ [bold green]All prerequisites are satisfied[/bold green]")
        else:
            console.print("⚠️  [bold yellow]Some prerequisites need attention[/bold yellow]")
            
        console.print("\n[bold cyan]Options:[/bold cyan]")
        console.print("1. Recheck prerequisites")
        console.print("2. Show installation guide")
        console.print("3. Check Python virtual environments")
        console.print("4. Check Docker installation")
        
        try:
            choice = Prompt.ask("Select option", choices=["1", "2", "3", "4"])
            
            if choice == "1":
                console.print("🔄 Rechecking prerequisites...")
                self.prerequisite_checker.check_all_prerequisites()
            elif choice == "2":
                console.print("\n📋 [bold cyan]Installation Guide:[/bold cyan]")
                console.print("Please refer to the project README.md for detailed installation instructions.")
                console.print("Key requirements:")
                console.print("• Python 3.11+ with pip/uv")
                console.print("• Docker Desktop")
                console.print("• Node.js 18+ with npm (for frontend)")
                console.print("• Git for version control")
            elif choice == "3":
                console.print("🔍 Checking Python virtual environments...")
                for service_name, service in self.services.items():
                    venv_path = self.project_root / service.directory / ".venv"
                    if venv_path.exists():
                        console.print(f"✅ {service.name}: Virtual environment found")
                    else:
                        console.print(f"❌ {service.name}: No virtual environment")
            elif choice == "4":
                console.print("🐳 Checking Docker installation...")
                success, stdout, stderr = self.run_command(["docker", "--version"])
                if success:
                    console.print(f"✅ Docker: {stdout.strip()}")
                    
                    # Check docker-compose
                    success, stdout, stderr = self.run_command(["docker", "compose", "version"])
                    if success:
                        console.print(f"✅ Docker Compose: {stdout.strip()}")
                    else:
                        console.print("❌ Docker Compose: Not available")
                else:
                    console.print("❌ Docker: Not installed or not accessible")
                    
        except (ValueError, KeyboardInterrupt):
            console.print("❌ Invalid selection", style="red")

    def _menu_cleanup_maintenance(self):
        """Menu option: Cleanup and maintenance operations"""
        console.print("\n🧹 [bold cyan]Cleanup & Maintenance[/bold cyan]")
        console.print("1. Clean temporary files")
        console.print("2. Reset virtual environments")
        console.print("3. Clear Docker cache")
        console.print("4. Clean npm cache (frontend)")
        console.print("5. Full system cleanup")
        
        try:
            choice = Prompt.ask("Select cleanup option", choices=["1", "2", "3", "4", "5"])
            
            if choice == "1":
                console.print("🗑️  Cleaning temporary files...")
                self.cleanup_temp_files()
                console.print("✅ Temporary files cleaned")
                
            elif choice == "2":
                if Confirm.ask("Reset all virtual environments? This will require reinstallation."):
                    console.print("🔄 Resetting virtual environments...")
                    for service_name, service in self.services.items():
                        venv_path = self.project_root / service.directory / ".venv"
                        if venv_path.exists():
                            console.print(f"🗑️  Removing {service.name} virtual environment...")
                            import shutil
                            shutil.rmtree(venv_path)
                    console.print("✅ Virtual environments reset")
                    
            elif choice == "3":
                if Confirm.ask("Clean Docker cache? This may free significant disk space."):
                    console.print("🐳 Cleaning Docker cache...")
                    success, stdout, stderr = self.run_command(["docker", "system", "prune", "-f"])
                    if success:
                        console.print("✅ Docker cache cleaned")
                        if stdout:
                            console.print(f"Details: {stdout}")
                    else:
                        console.print(f"❌ Failed to clean Docker cache: {stderr}", style="red")
                        
            elif choice == "4":
                frontend_dir = self.project_root / "Agentic-frontend"
                if frontend_dir.exists():
                    console.print("📦 Cleaning npm cache...")
                    success, stdout, stderr = self.run_command(["npm", "cache", "clean", "--force"], cwd=frontend_dir)
                    if success:
                        console.print("✅ npm cache cleaned")
                    else:
                        console.print(f"❌ Failed to clean npm cache: {stderr}", style="red")
                else:
                    console.print("❌ Frontend directory not found", style="red")
                    
            elif choice == "5":
                if Confirm.ask("Perform full system cleanup? This will clean everything."):
                    console.print("🧹 Performing full system cleanup...")
                    
                    # Clean temp files
                    self.cleanup_temp_files()
                    
                    # Clean Docker
                    self.run_command(["docker", "system", "prune", "-f"])
                    
                    # Clean npm cache
                    frontend_dir = self.project_root / "Agentic-frontend"
                    if frontend_dir.exists():
                        self.run_command(["npm", "cache", "clean", "--force"], cwd=frontend_dir)
                    
                    console.print("✅ Full system cleanup completed")
                    
        except (ValueError, KeyboardInterrupt):
            console.print("❌ Invalid selection", style="red")

    def _menu_environment_setup(self):
        """Menu option: Environment setup and installation"""
        console.print("\n🔧 [bold cyan]Environment Setup[/bold cyan]")
        console.print("1. Setup all service environments")
        console.print("2. Setup specific service environment")
        console.print("3. Install/update dependencies")
        console.print("4. Verify environment setup")
        
        try:
            choice = Prompt.ask("Select setup option", choices=["1", "2", "3", "4"])
            
            if choice == "1":
                if Confirm.ask("Setup all service environments? This may take several minutes."):
                    console.print("🔧 Setting up all environments...")
                    if self.setup_environment(clean=False, auto_install=True, verbose=True):
                        console.print("✅ All environments setup completed", style="green")
                    else:
                        console.print("❌ Environment setup failed", style="red")
                        
            elif choice == "2":
                service_choices = list(self.services.keys())
                console.print("Available services:")
                for i, service_name in enumerate(service_choices, 1):
                    console.print(f"  {i}. {self.services[service_name].name}")
                
                selection = Prompt.ask("Select service number", choices=[str(i) for i in range(1, len(service_choices) + 1)])
                service_name = service_choices[int(selection) - 1]
                
                console.print(f"🔧 Setting up {self.services[service_name].name} environment...")
                if self.setup_environment([service_name], clean=False, auto_install=True, verbose=True):
                    console.print(f"✅ {self.services[service_name].name} environment setup completed", style="green")
                else:
                    console.print(f"❌ {self.services[service_name].name} environment setup failed", style="red")
                    
            elif choice == "3":
                console.print("📦 Installing/updating dependencies...")
                if self.setup_environment(clean=False, auto_install=True, verbose=True):
                    console.print("✅ Dependencies updated", style="green")
                else:
                    console.print("❌ Dependency update failed", style="red")
                    
            elif choice == "4":
                console.print("🔍 Verifying environment setup...")
                all_valid = True
                for service_name in self.services:
                    if self.validate_service_setup(service_name):
                        console.print(f"✅ {self.services[service_name].name}: Environment valid")
                    else:
                        console.print(f"❌ {self.services[service_name].name}: Environment needs setup")
                        all_valid = False
                
                if all_valid:
                    console.print("🎉 [bold green]All environments are properly configured![/bold green]")
                else:
                    console.print("⚠️  [bold yellow]Some environments need attention[/bold yellow]")
                    
        except (ValueError, KeyboardInterrupt):
            console.print("❌ Invalid selection", style="red")

    def _menu_system_info(self):
        """Menu option: Display system information"""
        console.print("\n ℹ️ [bold cyan]System Information[/bold cyan]")
        
        # Platform info
        console.print(f"🖥️  [bold]Platform:[/bold] {platform.system()} {platform.release()}")
        console.print(f"🏗️  [bold]Architecture:[/bold] {platform.machine()}")
        console.print(f"🐍 [bold]Python:[/bold] {platform.python_version()}")
        
        # Project info
        console.print(f"📁 [bold]Project Root:[/bold] {self.project_root}")
        console.print(f"🔧 [bold]Services:[/bold] {len(self.services)} application services")
        console.print(f"🐳 [bold]Infrastructure:[/bold] {len(self.docker_services)} Docker services")
        
        # Check versions
        console.print("\n🔍 [bold cyan]Tool Versions:[/bold cyan]")
        
        # Docker version
        success, stdout, stderr = self.run_command(["docker", "--version"])
        if success:
            console.print(f"🐳 Docker: {stdout.strip()}")
        else:
            console.print("🐳 Docker: Not available")
        
        # Node.js version
        success, stdout, stderr = self.run_command(["node", "--version"])
        if success:
            console.print(f"📦 Node.js: {stdout.strip()}")
        else:
            console.print("📦 Node.js: Not available")
        
        # UV version
        success, stdout, stderr = self.run_command(["uv", "--version"])
        if success:
            console.print(f"⚡ UV: {stdout.strip()}")
        else:
            console.print("⚡ UV: Not available")
        
        # Git version
        success, stdout, stderr = self.run_command(["git", "--version"])
        if success:
            console.print(f"📝 Git: {stdout.strip()}")
        else:
            console.print("📝 Git: Not available")
        
        # Service status summary
        running_services = sum(1 for service in self.services.values() if service.is_running())
        docker_running = sum(1 for svc in self.docker_services if self.is_docker_service_running(svc))
        
        console.print(f"\n📊 [bold cyan]Current Status:[/bold cyan]")
        console.print(f"🚀 Application Services: {running_services}/{len(self.services)} running")
        console.print(f"🐳 Infrastructure Services: {docker_running}/{len(self.docker_services)} running")
        
        # Memory usage (if available)
        try:
            import psutil
            memory = psutil.virtual_memory()
            console.print(f"💾 Memory Usage: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)")
        except ImportError:
            console.print("💾 Memory Usage: Not available (install psutil for details)")
        
        console.print(f"\n🎯 [bold green]CogniVox Agentic Platform v1.0[/bold green]")
        console.print("🔗 Documentation: Check /documents folder")
        console.print("🐞 Issues: Use GitHub issues for bug reports") 