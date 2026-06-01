"""
Docker Infrastructure Management
==============================
Handles Docker Compose operations, service health monitoring, and Ollama model management.
"""

import os
import time
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import socket

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback console for systems without Rich
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
        def rule(self, *args, **kwargs):
            print("=" * 60)

from ..core.config import DockerServiceConfig

logger = logging.getLogger("orchestrator.docker")


class DockerManager:
    """Manages Docker infrastructure services and operations"""
    
    def __init__(self, console: Console, project_root: Path, docker_compose_file: Path):
        self.console = console
        self.project_root = project_root
        self.docker_compose_file = docker_compose_file
        self.docker_services = {}
        self._setup_docker_services()
    
    def _setup_docker_services(self):
        """Configure Docker infrastructure services"""
        self.docker_services = {
            "neo4j": DockerServiceConfig(
                name="Neo4j Graph Database",
                container_name="agentic-neo4j",
                port=7474,
                health_check="http://127.0.0.1:7474",
                tech_stack="Neo4j Database",
                color="green",
                environment_vars={
                    "NEO4J_AUTH": "neo4j/password"
                },
                always_pull=True
            ),
            "ollama": DockerServiceConfig(
                name="Ollama LLM Service",
                container_name="agentic-ollama",
                port=11434,
                health_check="http://127.0.0.1:11434/api/tags",
                tech_stack="Ollama LLM Server",
                color="purple",
                environment_vars={
                    "OLLAMA_HOST": "0.0.0.0"
                },
                always_pull=True
            ),
            "mongodb": DockerServiceConfig(
                name="MongoDB Database",
                container_name="agentic-mongodb",
                port=27017,
                health_check="mongodb://127.0.0.1:27017",
                tech_stack="MongoDB Database",
                color="green",
                environment_vars={
                    "MONGO_ROOT_USERNAME": "cognivox",
                    "MONGO_ROOT_PASSWORD": "cognivox",
                    "MONGO_APP_DATABASE": "cognivox",
                    "MONGO_APP_USER": "cognivox",
                    "MONGO_APP_PASSWORD": "cognivox",
                    "MONGO_PORT": "27017"
                },
                always_pull=True
            ),
            "postgres": DockerServiceConfig(
                name="PostgreSQL Database",
                container_name="agentic-postgres",
                port=5432,
                health_check="postgresql://127.0.0.1:5432",
                tech_stack="PostgreSQL Database",
                color="blue",
                environment_vars={
                    "POSTGRES_USER": "postgres",
                    "POSTGRES_PASSWORD": "password",
                    "POSTGRES_DB": "admin",
                    "POSTGRES_PORT": "5432"
                },
                always_pull=True
            ),
            "pgadmin": DockerServiceConfig(
                name="PgAdmin Web UI",
                container_name="agentic-pgadmin",
                port=5050,
                health_check="http://127.0.0.1:5050/misc/ping",
                dependencies=["postgres"],
                tech_stack="Database Admin UI",
                color="blue",
                environment_vars={
                    "PGADMIN_DEFAULT_EMAIL": "admin@admin.com",
                    "PGADMIN_DEFAULT_PASSWORD": "admin",
                    "PGADMIN_PORT": "5050"
                },
                always_pull=True
            )
        }

    def start_docker_services(self, services: List[str] = None, force_pull: bool = False) -> bool:
        """Start Docker infrastructure services"""
        if not self.docker_compose_file.exists():
            self.console.print(f"❌ Docker Compose file not found: {self.docker_compose_file}", style="red")
            return False

        # If specific services requested, start only those
        if services:
            service_names = [svc for svc in services if svc in self.docker_services]
            if not service_names:
                self.console.print("❌ No valid Docker services specified", style="red")
                return False
        else:
            # Start all Docker services
            service_names = list(self.docker_services.keys())

        # Pull latest images if needed
        if force_pull or any(self.docker_services[svc].always_pull for svc in service_names):
            self.console.print(f"\n📥 Pulling latest Docker images for: {', '.join(service_names)}", style="cyan")
            if not self.pull_docker_images(service_names):
                self.console.print("⚠️  Some images failed to pull, continuing with available images...", style="yellow")

        self.console.print(f"\n🐳 Starting Docker services: {', '.join(service_names)}", style="blue")
        
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task("Starting Docker services...", total=len(service_names))
                
                for service_name in service_names:
                    progress.update(task, description=f"Starting {service_name}...")
                    
                    cmd = [
                        "docker", "compose",
                        "-f", str(self.docker_compose_file),
                        "up", "-d", service_name
                    ]
                    
                    try:
                        result = subprocess.run(
                            cmd,
                            cwd=self.project_root,
                            capture_output=True,
                            text=True,
                            timeout=120
                        )
                        
                        if result.returncode == 0:
                            progress.update(task, advance=1)
                            self.console.print(f"✅ {self.docker_services[service_name].name} started", style="green")
                        else:
                            self.console.print(f"❌ Failed to start {service_name}: {result.stderr}", style="red")
                            return False
                            
                    except subprocess.TimeoutExpired:
                        self.console.print(f"❌ Timeout starting {service_name}", style="red")
                        return False
                    except Exception as e:
                        self.console.print(f"❌ Error starting {service_name}: {e}", style="red")
                        return False
        else:
            # Fallback without Rich
            for service_name in service_names:
                self.console.print(f"Starting {service_name}...")
                cmd = [
                    "docker", "compose",
                    "-f", str(self.docker_compose_file),
                    "up", "-d", service_name
                ]
                
                try:
                    result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, timeout=120)
                    if result.returncode == 0:
                        self.console.print(f"✅ {self.docker_services[service_name].name} started")
                    else:
                        self.console.print(f"❌ Failed to start {service_name}: {result.stderr}")
                        return False
                except Exception as e:
                    self.console.print(f"❌ Error starting {service_name}: {e}")
                    return False

        # Wait for services to be healthy
        for service_name in service_names:
            service = self.docker_services[service_name]
            self.console.print(f"⏳ Waiting for {service.name} to be healthy...")
            if self.wait_for_docker_service(service):
                self.console.print(f"✅ {service.name} is healthy", style="green")
            else:
                self.console.print(f"⚠️  {service.name} may not be fully ready", style="yellow")

        return True

    def pull_docker_images(self, services: List[str] = None) -> bool:
        """Pull latest Docker images for specified services"""
        if services is None:
            services = list(self.docker_services.keys())
        
        success = True
        
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task("Pulling Docker images...", total=len(services))
                
                for service_name in services:
                    if service_name not in self.docker_services:
                        continue
                        
                    progress.update(task, description=f"Pulling {service_name}...")
                    
                    cmd = [
                        "docker", "compose",
                        "-f", str(self.docker_compose_file),
                        "pull", service_name
                    ]
                    
                    try:
                        result = subprocess.run(
                            cmd,
                            cwd=self.project_root,
                            capture_output=True,
                            text=True,
                            timeout=300  # 5 minutes timeout for image pulls
                        )
                        
                        if result.returncode == 0:
                            progress.update(task, advance=1)
                            self.console.print(f"✅ {self.docker_services[service_name].name} image updated", style="green")
                        else:
                            self.console.print(f"❌ Failed to pull {service_name}: {result.stderr}", style="red")
                            success = False
                            progress.update(task, advance=1)
                            
                    except subprocess.TimeoutExpired:
                        self.console.print(f"❌ Timeout pulling {service_name}", style="red")
                        success = False
                        progress.update(task, advance=1)
                    except Exception as e:
                        self.console.print(f"❌ Error pulling {service_name}: {e}", style="red")
                        success = False
                        progress.update(task, advance=1)
        else:
            # Fallback without Rich
            for service_name in services:
                if service_name not in self.docker_services:
                    continue
                    
                self.console.print(f"Pulling {service_name}...")
                cmd = [
                    "docker", "compose",
                    "-f", str(self.docker_compose_file),
                    "pull", service_name
                ]
                
                try:
                    result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, timeout=300)
                    if result.returncode == 0:
                        self.console.print(f"✅ {self.docker_services[service_name].name} image updated")
                    else:
                        self.console.print(f"❌ Failed to pull {service_name}: {result.stderr}")
                        success = False
                except Exception as e:
                    self.console.print(f"❌ Error pulling {service_name}: {e}")
                    success = False
        
        return success

    def cleanup_conflicting_containers(self, services: List[str] = None) -> bool:
        """Remove conflicting Docker containers while preserving volumes"""
        if services is None:
            services = list(self.docker_services.keys())
        
        self.console.print("\n🧹 Cleaning up conflicting Docker containers...", style="yellow")
        
        success = True
        for service_name in services:
            if service_name not in self.docker_services:
                continue
                
            service = self.docker_services[service_name]
            container_name = service.container_name
            
            try:
                # Check if container exists
                check_cmd = ["docker", "ps", "-aq", "-f", f"name={container_name}"]
                result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=30)
                
                if result.stdout.strip():
                    self.console.print(f"🗑️  Removing existing container: {container_name}", style="yellow")
                    
                    # Stop container if running
                    stop_cmd = ["docker", "stop", container_name]
                    subprocess.run(stop_cmd, capture_output=True, text=True, timeout=30)
                    
                    # Remove container
                    remove_cmd = ["docker", "rm", container_name]
                    remove_result = subprocess.run(remove_cmd, capture_output=True, text=True, timeout=30)
                    
                    if remove_result.returncode == 0:
                        self.console.print(f"✅ Removed container: {container_name}", style="green")
                    else:
                        self.console.print(f"❌ Failed to remove container {container_name}: {remove_result.stderr}", style="red")
                        success = False
                else:
                    self.console.print(f"ℹ️  No existing container found: {container_name}", style="dim")
                    
            except Exception as e:
                self.console.print(f"❌ Error handling container {container_name}: {e}", style="red")
                success = False
        
        return success

    def ensure_external_resources(self) -> bool:
        """Ensure external volumes and network exist"""
        self.console.print("\n🔧 Ensuring external Docker resources exist...", style="blue")
        
        success = True
        
        # Define the volumes that need to exist
        required_volumes = [
            "agentic-neo4j-data",
            "agentic-neo4j-logs", 
            "agentic-neo4j-plugins",
            "agentic-ollama",
            "agentic-mongodb-data",
            "agentic-mongodb-log",
            "agentic-postgres-data",
            "agentic-pgadmin-data"
        ]
        
        # Create volumes if they don't exist
        for volume_name in required_volumes:
            try:
                # Check if volume exists
                check_cmd = ["docker", "volume", "inspect", volume_name]
                result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    # Volume doesn't exist, create it
                    create_cmd = ["docker", "volume", "create", volume_name]
                    create_result = subprocess.run(create_cmd, capture_output=True, text=True, timeout=30)
                    
                    if create_result.returncode == 0:
                        self.console.print(f"✅ Created volume: {volume_name}", style="green")
                    else:
                        self.console.print(f"❌ Failed to create volume {volume_name}: {create_result.stderr}", style="red")
                        success = False
                else:
                    self.console.print(f"ℹ️  Volume already exists: {volume_name}", style="dim")
                    
            except Exception as e:
                self.console.print(f"❌ Error handling volume {volume_name}: {e}", style="red")
                success = False
        
        # Create network if it doesn't exist
        network_name = "agentic-network"
        try:
            # Check if network exists
            check_cmd = ["docker", "network", "inspect", network_name]
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                # Network doesn't exist, create it
                create_cmd = [
                    "docker", "network", "create", 
                    "--driver", "bridge",
                    "--subnet", "192.168.100.0/24",
                    "--gateway", "192.168.100.1",
                    network_name
                ]
                create_result = subprocess.run(create_cmd, capture_output=True, text=True, timeout=30)
                
                if create_result.returncode == 0:
                    self.console.print(f"✅ Created network: {network_name}", style="green")
                else:
                    self.console.print(f"❌ Failed to create network {network_name}: {create_result.stderr}", style="red")
                    success = False
            else:
                self.console.print(f"ℹ️  Network already exists: {network_name}", style="dim")
                
        except Exception as e:
            self.console.print(f"❌ Error handling network {network_name}: {e}", style="red")
            success = False
        
        return success

    def start_docker_services_with_cleanup(self, services: List[str] = None, force_pull: bool = False) -> bool:
        """Start Docker services with automatic cleanup of conflicts"""
        self.console.print("\n🚀 Starting Docker services with conflict resolution...", style="blue")
        
        # Step 1: Ensure external resources exist
        if not self.ensure_external_resources():
            self.console.print("❌ Failed to create external resources", style="red")
            return False
        
        # Step 2: Clean up conflicting containers
        if not self.cleanup_conflicting_containers(services):
            self.console.print("⚠️  Some containers failed to clean up, continuing...", style="yellow")
        
        # Step 3: Start services normally
        return self.start_docker_services(services, force_pull)

    def stop_docker_services(self, services: List[str] = None) -> bool:
        """Stop Docker infrastructure services"""
        if not self.docker_compose_file.exists():
            self.console.print(f"❌ Docker Compose file not found: {self.docker_compose_file}", style="red")
            return False

        # If specific services requested, stop only those
        if services:
            service_names = [svc for svc in services if svc in self.docker_services]
            if not service_names:
                self.console.print("❌ No valid Docker services specified", style="red")
                return False
        else:
            # Stop all Docker services
            service_names = list(self.docker_services.keys())

        self.console.print(f"\n🛑 Stopping Docker services: {', '.join(service_names)}", style="blue")
        
        for service_name in service_names:
            cmd = [
                "docker", "compose",
                "-f", str(self.docker_compose_file),
                "stop", service_name
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    self.console.print(f"✅ {self.docker_services[service_name].name} stopped", style="green")
                else:
                    self.console.print(f"❌ Failed to stop {service_name}: {result.stderr}", style="red")
                    
            except subprocess.TimeoutExpired:
                self.console.print(f"❌ Timeout stopping {service_name}", style="red")
            except Exception as e:
                self.console.print(f"❌ Error stopping {service_name}: {e}", style="red")

        return True

    def wait_for_docker_service(self, service: DockerServiceConfig, timeout: int = 60) -> bool:
        """Wait for a Docker service to be healthy"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if service.health_check.startswith("http"):
                    # HTTP health check
                    if REQUESTS_AVAILABLE:
                        response = requests.get(service.health_check, timeout=5)
                        if response.status_code in [200, 404]:  # 404 can be OK for some services
                            return True
                    else:
                        # Fallback to port check
                        if self._check_port_listening(service.port):
                            return True
                else:
                    # For non-HTTP services, check if port is listening
                    if self._check_port_listening(service.port):
                        return True
                        
            except Exception:
                pass  # Service not ready yet
            
            time.sleep(2)
        
        return False

    def _check_port_listening(self, port: int) -> bool:
        """Check if a port is listening on localhost"""
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=3):
                return True
        except (socket.error, ConnectionRefusedError, OSError):
            return False

    def is_docker_service_running(self, service_name: str) -> bool:
        """Check if a Docker service is running"""
        if service_name not in self.docker_services:
            return False
            
        service = self.docker_services[service_name]
        cmd = ["docker", "ps", "-q", "-f", f"name={service.container_name}"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return bool(result.stdout.strip())
        except Exception:
            return False

    def install_ollama_models(self, models: List[str] = None) -> bool:
        """Install specified Ollama models"""
        if models is None:
            models = [
                "llama3.1:latest",
                "qwen3:4b", 
                "mistral:latest",
                "nomic-embed-text:latest"
            ]
        
        if not self.is_docker_service_running("ollama"):
            self.console.print("❌ Ollama service is not running. Please start it first.", style="red")
            return False

        self.console.print(f"\n🦙 Installing Ollama models: {', '.join(models)}", style="blue")
        
        for model in models:
            self.console.print(f"📥 Installing {model}...")
            
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                    transient=True
                ) as progress:
                    task = progress.add_task(f"Installing {model}...", total=None)
                    
                    cmd = ["docker", "exec", "agentic-ollama", "ollama", "pull", model]
                    
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            encoding='utf-8',
                            errors='replace',
                            timeout=600  # 10 minutes timeout for model downloads
                        )
                        
                        progress.update(task, completed=100)
                        
                        if result.returncode == 0:
                            self.console.print(f"✅ {model} installed successfully", style="green")
                        else:
                            self.console.print(f"❌ Failed to install {model}: {result.stderr}", style="red")
                            
                    except subprocess.TimeoutExpired:
                        self.console.print(f"❌ Timeout installing {model}", style="red")
                    except Exception as e:
                        self.console.print(f"❌ Error installing {model}: {e}", style="red")
            else:
                # Fallback without Rich
                cmd = ["docker", "exec", "agentic-ollama", "ollama", "pull", model]
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
                    if result.returncode == 0:
                        self.console.print(f"✅ {model} installed successfully")
                    else:
                        self.console.print(f"❌ Failed to install {model}: {result.stderr}")
                except Exception as e:
                    self.console.print(f"❌ Error installing {model}: {e}")

        self.console.print("🦙 Ollama model installation complete", style="green")
        return True

    def get_docker_service_status(self) -> Dict[str, bool]:
        """Get status of all Docker services"""
        status = {}
        for service_name in self.docker_services:
            status[service_name] = self.is_docker_service_running(service_name)
        return status

    def initialize_databases(self, reset: bool = False) -> bool:
        """Initialize or reset application databases"""
        self.console.print("\n🗃️  Initializing databases...", style="cyan")
        
        success = True
        
        # PostgreSQL initialization
        if self.is_docker_service_running("postgres"):
            success &= self._initialize_postgresql(reset)
        else:
            self.console.print("⚠️  PostgreSQL container not running, skipping initialization", style="yellow")
            
        # MongoDB initialization
        if self.is_docker_service_running("mongodb"):
            success &= self._initialize_mongodb(reset)
        else:
            self.console.print("⚠️  MongoDB container not running, skipping initialization", style="yellow")
            
        # Neo4j initialization
        if self.is_docker_service_running("neo4j"):
            success &= self._initialize_neo4j(reset)
        else:
            self.console.print("⚠️  Neo4j container not running, skipping initialization", style="yellow")
        
        if success:
            self.console.print("✅ Database initialization completed", style="green")
        else:
            self.console.print("❌ Database initialization failed", style="red")
            
        return success

    def _initialize_postgresql(self, reset: bool = False) -> bool:
        """Initialize PostgreSQL database for the application"""
        self.console.print("🐘 Initializing PostgreSQL...", style="blue")
        
        try:
            # Check if we can connect to PostgreSQL
            check_cmd = [
                "docker", "exec", "agentic-postgres", 
                "pg_isready", "-U", "postgres"
            ]
            
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                self.console.print("❌ PostgreSQL is not ready", style="red")
                return False
            
            # Create application database if it doesn't exist
            create_db_cmd = [
                "docker", "exec", "agentic-postgres",
                "psql", "-U", "postgres", "-c",
                "CREATE DATABASE cognivox OWNER postgres;"
            ]
            
            result = subprocess.run(create_db_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.console.print("✅ Database 'cognivox' created", style="green")
            elif "already exists" in result.stderr:
                self.console.print("ℹ️  Database 'cognivox' already exists", style="blue")
            else:
                self.console.print(f"⚠️  Database creation output: {result.stderr}", style="yellow")
            
            # Run comprehensive backend database initialization
            backend_dir = self.project_root / "Agentic-Backend"
            if backend_dir.exists():
                self.console.print("🔧 Running backend database initialization...", style="blue")
                
                # Run the initialize_db.py script in the backend directory
                init_cmd = [
                    "python", "-m", "app.initialize_db"
                ]
                
                if reset:
                    init_cmd.append("--force")
                    self.console.print("🔄 Forcing database reset...", style="yellow")
                
                result = subprocess.run(
                    init_cmd,
                    cwd=backend_dir,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes for migrations
                )
                
                if result.returncode == 0:
                    self.console.print("✅ Backend database initialization completed", style="green")
                    if result.stdout:
                        # Show relevant output lines
                        for line in result.stdout.split('\n'):
                            if any(marker in line for marker in ['[SUCCESS]', '[INFO]', 'Admin user', 'completed']):
                                self.console.print(f"   {line}", style="dim")
                    return True
                else:
                    self.console.print("❌ Backend database initialization failed", style="red")
                    if result.stderr:
                        self.console.print(f"   Error: {result.stderr}", style="red")
                    if result.stdout:
                        self.console.print(f"   Output: {result.stdout}", style="dim")
                    return False
            else:
                self.console.print("⚠️  Backend directory not found, skipping application database setup", style="yellow")
                return True
            
        except subprocess.TimeoutExpired:
            self.console.print("❌ PostgreSQL initialization timed out", style="red")
            return False
        except Exception as e:
            self.console.print(f"❌ PostgreSQL initialization error: {e}", style="red")
            return False

    def _initialize_mongodb(self, reset: bool = False) -> bool:
        """Initialize MongoDB database for the application"""
        self.console.print("🍃 Initializing MongoDB...", style="green")
        
        try:
            # Check MongoDB connection with authentication (using root credentials)
            check_cmd = [
                "docker", "exec", "agentic-mongodb",
                "mongosh", "-u", "admin", "-p", "secretpassword", "--eval", "db.adminCommand('ping')"
            ]
            
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                self.console.print("❌ MongoDB is not ready", style="red")
                return False
            
            # Create collections and indexes in the application database
            init_cmd = [
                "docker", "exec", "agentic-mongodb",
                "mongosh", "-u", "admin", "-p", "secretpassword", "appdb", "--eval",
                """
                db.createCollection('sessions');
                db.createCollection('conversations'); 
                db.createCollection('memories');
                db.createCollection('threads');
                db.sessions.createIndex({'session_id': 1}, {'unique': true});
                db.conversations.createIndex({'conversation_id': 1});
                db.memories.createIndex({'user_id': 1});
                db.threads.createIndex({'user_id': 1});
                db.threads.createIndex({'thread_id': 1}, {'unique': true});
                """
            ]
            
            if reset:
                self.console.print("🔄 Resetting MongoDB database...", style="yellow")
                reset_cmd = [
                    "docker", "exec", "agentic-mongodb",
                    "mongosh", "-u", "admin", "-p", "secretpassword", "appdb", "--eval", "db.dropDatabase()"
                ]
                subprocess.run(reset_cmd, capture_output=True, text=True, timeout=30)
            
            result = subprocess.run(init_cmd, capture_output=True, text=True, timeout=30)
            self.console.print("✅ MongoDB initialized", style="green")
            return True
            
        except subprocess.TimeoutExpired:
            self.console.print("❌ MongoDB initialization timed out", style="red")
            return False
        except Exception as e:
            self.console.print(f"❌ MongoDB initialization error: {e}", style="red")
            return False

    def _initialize_neo4j(self, reset: bool = False) -> bool:
        """Initialize Neo4j database for the application"""
        self.console.print("🔗 Initializing Neo4j...", style="cyan")
        
        try:
            # Check Neo4j connection
            check_cmd = [
                "docker", "exec", "agentic-neo4j",
                "cypher-shell", "-u", "neo4j", "-p", "password", "RETURN 1"
            ]
            
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                self.console.print("❌ Neo4j is not ready", style="red")
                return False
            
            if reset:
                self.console.print("🔄 Resetting Neo4j database...", style="yellow")
                reset_cmd = [
                    "docker", "exec", "agentic-neo4j",
                    "cypher-shell", "-u", "neo4j", "-p", "password",
                    "MATCH (n) DETACH DELETE n"
                ]
                subprocess.run(reset_cmd, capture_output=True, text=True, timeout=30)
            
            # Create basic constraints and indexes
            init_cmd = [
                "docker", "exec", "agentic-neo4j",
                "cypher-shell", "-u", "neo4j", "-p", "password",
                """
                CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;
                CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE;
                CREATE INDEX IF NOT EXISTS FOR (d:Document) ON d.title;
                """
            ]
            
            result = subprocess.run(init_cmd, capture_output=True, text=True, timeout=30)
            self.console.print("✅ Neo4j initialized", style="green")
            return True
            
        except subprocess.TimeoutExpired:
            self.console.print("❌ Neo4j initialization timed out", style="red")
            return False
        except Exception as e:
            self.console.print(f"❌ Neo4j initialization error: {e}", style="red")
            return False

    def reset_all_databases(self) -> bool:
        """Reset all application databases"""
        return self.initialize_databases(reset=True)

    def run_command(self, command: list, timeout: int = 120, cwd: Path = None) -> Tuple[bool, str, str]:
        """Run a command and return success, stdout, stderr"""
        try:
            if cwd is None:
                cwd = self.project_root
                
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return result.returncode == 0, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e) 