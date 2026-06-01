#!/usr/bin/env python3
"""
CogniVox Agentic Platform Orchestrator - Main Entry Point
=========================================================
Enhanced master orchestrator with Rich UI, automatic prerequisite detection,
and robust setup for fresh repositories.
"""

import sys
import time
import argparse
import subprocess
from pathlib import Path

# Try to import Rich components
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.rule import Rule
    from rich.align import Align
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    # Fallback console for systems without Rich
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
        def rule(self, *args, **kwargs):
            print("=" * 60)
    console = Console()

# Add current directory to Python path for absolute imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import orchestrator components
from orchestrator.core.orchestrator import ServiceOrchestrator


def install_rich_if_missing():
    """Install Rich if it's not available"""
    if not RICH_AVAILABLE:
        print("🎨 Rich UI library not found. Installing...")
        try:
            # Try UV first, then fallback to pip
            try:
                subprocess.check_call(["uv", "add", "rich"])
                print("✅ Rich installed with UV successfully! Please restart the script.")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("🔄 UV not found, trying pip...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
                print("✅ Rich installed with pip successfully! Please restart the script.")
            sys.exit(0)
        except subprocess.CalledProcessError:
            print("❌ Failed to install Rich. Running with basic UI...")
            return False
    return True


def show_enhanced_banner():
    """Display enhanced startup banner"""
    if RICH_AVAILABLE:
        banner_text = """
[bold blue]CogniVox Agentic Platform Orchestrator[/bold blue]
[dim]Enhanced Service Management with Rich UI[/dim]

[yellow]🚀 Comprehensive Service Orchestration:[/yellow]
• [green]Docker Infrastructure Management[/green] (PostgreSQL, MongoDB, Neo4j, Ollama)
• [cyan]Application Service Coordination[/cyan] (Backend, Memory, GraphRAG, Frontend)
• [purple]Interactive Control Panel[/purple] with real-time monitoring
• [blue]Automatic Prerequisite Detection[/blue] and installation
• [magenta]Cross-platform Terminal Support[/magenta] (Windows, Linux, macOS)

[dim]Version 2.0.0 - Modular Architecture[/dim]
        """
        
        panel = Panel(
            banner_text.strip(),
            title="🎯 CogniVox Platform",
            border_style="blue",
            padding=(1, 2)
        )
        console.print(panel)
    else:
        print("=" * 60)
        print("  CogniVox Agentic Platform Orchestrator")
        print("  Enhanced Service Management")
        print("=" * 60)


def parse_args():
    """Parse command line arguments with comprehensive options"""
    parser = argparse.ArgumentParser(
        description="CogniVox Agentic Platform Service Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s check                          # Check prerequisites
  %(prog)s setup                          # Complete environment setup
  %(prog)s start                          # Start all services with interactive menu
  %(prog)s start --services backend       # Start specific services
  %(prog)s start --force-update           # Start services with dependency updates
  %(prog)s start --force-pull --force-update # Force update everything
  %(prog)s docker start --force-pull      # Start Docker with latest images
  %(prog)s docker start --cleanup         # Start Docker with automatic cleanup
  %(prog)s docker cleanup                 # Clean up Docker conflicts only
  %(prog)s docker cleanup --containers-only # Remove only containers
  %(prog)s ollama --install               # Install Ollama models
  %(prog)s credentials --export json      # Export credentials
  %(prog)s run --force-update --force-pull # Complete setup with all updates
        """
    )
    
    # Main command subparsers
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check system prerequisites")
    check_parser.add_argument("--auto-install", action="store_true", 
                             help="Automatically install missing prerequisites")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup development environment")
    setup_parser.add_argument("--services", nargs="+", 
                             choices=["backend", "memory", "graphrag", "frontend"],
                             help="Specific services to setup")
    setup_parser.add_argument("--clean", action="store_true", 
                             help="Clean install (remove existing dependencies)")
    setup_parser.add_argument("--auto-install", action="store_true",
                             help="Auto-install missing prerequisites")
    setup_parser.add_argument("--verbose", action="store_true",
                             help="Verbose output during setup")
    setup_parser.add_argument("--skip-docker", action="store_true",
                             help="Skip Docker infrastructure setup")
    setup_parser.add_argument("--skip-ollama", action="store_true",
                             help="Skip Ollama models installation")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start services")
    start_parser.add_argument("--services", nargs="+",
                             choices=["backend", "memory", "graphrag", "frontend"],
                             help="Specific services to start")
    start_parser.add_argument("--dev", action="store_true",
                             help="Start in development mode")
    start_parser.add_argument("--force-update", action="store_true",
                             help="Force update all dependencies before starting")
    start_parser.add_argument("--force-pull", action="store_true",
                             help="Force pull latest Docker images before starting")
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop services")
    stop_parser.add_argument("--services", nargs="+",
                            choices=["backend", "memory", "graphrag", "frontend"],
                            help="Specific services to stop")
    
    # Status command
    subparsers.add_parser("status", help="Check service status")
    
    # Docker command
    docker_parser = subparsers.add_parser("docker", help="Manage Docker services")
    docker_subparsers = docker_parser.add_subparsers(dest="docker_command")
    
    docker_start = docker_subparsers.add_parser("start", help="Start Docker services")
    docker_start.add_argument("--services", nargs="+",
                             choices=["postgresql", "mongodb", "neo4j", "ollama", "pgadmin"],
                             help="Specific Docker services to start")
    docker_start.add_argument("--force-pull", action="store_true",
                             help="Force pull latest Docker images before starting")
    docker_start.add_argument("--cleanup", action="store_true",
                             help="Clean up conflicting containers before starting")
    
    docker_stop = docker_subparsers.add_parser("stop", help="Stop Docker services")
    docker_stop.add_argument("--services", nargs="+",
                            choices=["postgresql", "mongodb", "neo4j", "ollama", "pgadmin"],
                            help="Specific Docker services to stop")
    
    docker_cleanup = docker_subparsers.add_parser("cleanup", help="Clean up Docker conflicts")
    docker_cleanup.add_argument("--services", nargs="+",
                               choices=["postgresql", "mongodb", "neo4j", "ollama", "pgadmin"],
                               help="Specific Docker services to clean")
    docker_cleanup.add_argument("--containers-only", action="store_true",
                               help="Only remove containers, don't create resources")
    
    # Ollama command
    ollama_parser = subparsers.add_parser("ollama", help="Manage Ollama models")
    ollama_parser.add_argument("--install", action="store_true",
                              help="Install Ollama models")
    ollama_parser.add_argument("--models", nargs="+",
                              help="Specific models to install")
    
    # Credentials command
    cred_parser = subparsers.add_parser("credentials", help="Manage credentials")
    cred_parser.add_argument("--export", choices=["json", "env"],
                            help="Export credentials to file")
    
    # URLs command
    subparsers.add_parser("urls", help="Show service URLs")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(dest="config_command")
    
    config_create = config_subparsers.add_parser("create", help="Create configuration files")
    config_create.add_argument("--force", action="store_true",
                              help="Overwrite existing configuration files")
    
    config_subparsers.add_parser("validate", help="Validate configuration")
    
    # Control command (direct access to interactive panel)
    subparsers.add_parser("control", help="Launch interactive control panel directly")
    
    # Run command (comprehensive workflow)
    run_parser = subparsers.add_parser("run", help="Complete setup and run workflow")
    run_parser.add_argument("--skip-docker", action="store_true",
                           help="Skip Docker infrastructure")
    run_parser.add_argument("--skip-ollama", action="store_true", 
                           help="Skip Ollama models")
    run_parser.add_argument("--dev", action="store_true",
                           help="Development mode")
    run_parser.add_argument("--auto-install", action="store_true",
                           help="Auto-install prerequisites")
    run_parser.add_argument("--force-update", action="store_true",
                           help="Force update all dependencies")
    run_parser.add_argument("--force-pull", action="store_true",
                           help="Force pull latest Docker images")
    
    # Database management commands
    db_parser = subparsers.add_parser("db", help="Database management operations")
    db_subparsers = db_parser.add_subparsers(dest="db_action", help="Database action")
    
    # Database init command
    init_parser = db_subparsers.add_parser("init", help="Initialize databases")
    init_parser.add_argument("--reset", action="store_true", help="Reset existing data")
    
    # Database reset command
    reset_parser = db_subparsers.add_parser("reset", help="Reset all databases")
    
    # Database status command
    status_parser = db_subparsers.add_parser("status", help="Check database status")
    
    # Default to start if no command provided
    args = parser.parse_args()
    if args.command is None:
        args.command = "start"
        # Add flag to indicate this was a default command
        args._is_default = True
    else:
        args._is_default = False
        
    return args


def main():
    """Enhanced main function with comprehensive service management"""
    
    # Show enhanced banner
    show_enhanced_banner()
    
    try:
        # Install Rich if missing
        install_rich_if_missing()
        
        args = parse_args()
        
        # Create orchestrator
        orchestrator = ServiceOrchestrator()
        
        # Setup signal handlers
        orchestrator.setup_signal_handlers()
        
        # Handle terminal mode setting (default to terminal mode)
        for service in orchestrator.services.values():
            service.use_terminal = True
        
        if args.command == "check":
            orchestrator.prerequisite_checker.run_full_check(auto_install=args.auto_install)
            sys.exit(0)
            
        elif args.command == "setup":
            console.print("🔧 [bold green]Setting up CogniVox Agentic Platform...[/bold green]")
            
            # Step 1: Prerequisites
            if not orchestrator.prerequisite_checker.run_full_check(auto_install=args.auto_install):
                console.print("❌ Prerequisites check failed", style="red")
                return 1
            
            # Step 2: Docker services
            if not orchestrator.start_docker_services():
                console.print("❌ Docker services startup failed", style="red")
                return 1
            
            # Step 3: Wait for Docker services to be ready
            console.print("⏱️  Waiting for Docker services to be ready...")
            time.sleep(10)
            
            # Step 4: Initialize databases
            console.print("🗃️  Initializing databases...")
            if not orchestrator.initialize_databases():
                console.print("❌ Database initialization failed", style="red")
                return 1
            
            # Step 5: Install Ollama models
            if not orchestrator.install_ollama_models():
                console.print("❌ Ollama models installation failed", style="red")
                return 1
            
            # Step 6: Setup application environments
            if hasattr(args, 'services') and args.services:
                services_to_setup = args.services
            else:
                services_to_setup = None
                
            if not orchestrator.setup_environment(
                services=services_to_setup,
                clean=getattr(args, 'clean', False),
                auto_install=getattr(args, 'auto_install', False),
                verbose=getattr(args, 'verbose', False)
            ):
                console.print("❌ Environment setup failed", style="red")
                return 1
            
            console.print("✅ [bold green]Setup completed successfully![/bold green]")
            return 0
            
        elif args.command == "start":
            # Add special welcome for default command usage
            if getattr(args, '_is_default', False):
                console.print("\n👋 [bold cyan]Welcome to CogniVox Agentic Platform![/bold cyan]", style="cyan")
                console.print("💡 No command specified - launching the Interactive Control Panel for easy management.", style="dim")
                console.print("📚 Tip: Use --help to see all available commands for direct operation.", style="dim")
                console.print("")
            
            # Handle missing services attribute
            services = getattr(args, 'services', None)
            
            if services:
                # Show control panel with option to start specific services
                console.print(f"\n🎯 [bold cyan]Interactive Control Panel[/bold cyan] - Services: {', '.join(services)}", style="cyan")
                console.print("💡 Use the control panel to manage your services robustly!", style="dim")
                
                # Optionally auto-start the specified services
                if Confirm.ask(f"Auto-start {', '.join(services)} now?", default=True):
                    all_started = True
                    for service in services:
                        if not orchestrator.start_service(service, args.dev, force_update=getattr(args, 'force_update', False)):
                            all_started = False
                    
                    if all_started:
                        console.print("✅ Services started successfully!", style="green")
                    else:
                        console.print("⚠️  Some services failed to start", style="yellow")
                
                # Always show interactive menu regardless of auto-start result
                time.sleep(1)  # Brief pause
                orchestrator.show_interactive_menu()
                
                # Clean shutdown when menu exits
                orchestrator.stop_all_services()
                sys.exit(0)
            else:
                # Show control panel immediately for full service management
                console.print("\n🎯 [bold cyan]Interactive Control Panel[/bold cyan] - Full Platform Management", style="cyan")
                console.print("💡 Welcome! Use the control panel to robustly manage all CogniVox services.", style="dim")
                console.print("📋 You can start services individually or all at once from the menu.", style="dim")
                
                # Optionally auto-start Docker infrastructure
                if Confirm.ask("Auto-start Docker infrastructure first?", default=True):
                    console.print("🐳 Starting Docker infrastructure...", style="blue")
                    force_pull = getattr(args, 'force_pull', False)
                    # Use cleanup method to avoid conflicts
                    docker_success = orchestrator.start_docker_services_with_cleanup(force_pull=force_pull)
                    if docker_success:
                        console.print("✅ Docker infrastructure ready!", style="green")
                    else:
                        console.print("⚠️  Docker infrastructure failed, you can retry from the menu", style="yellow")
                
                # Optionally auto-start all application services
                if Confirm.ask("Auto-start all application services now?", default=False):
                    console.print("🚀 Starting all application services...", style="blue")
                    force_update = getattr(args, 'force_update', False)
                    app_success = orchestrator.start_all_services(args.dev, force_update=force_update)
                    if app_success:
                        console.print("✅ All application services started!", style="green")
                    else:
                        console.print("⚠️  Some application services failed, you can retry from the menu", style="yellow")
                
                # Always show interactive menu - this is the main interface
                time.sleep(1)  # Brief pause
                console.print("\n🎮 [bold green]Entering Interactive Control Panel...[/bold green]", style="green")
                time.sleep(1)
                
                orchestrator.show_interactive_menu()
                
                # Clean shutdown when menu exits
                console.print("\n🛑 Exiting control panel - shutting down all services...", style="yellow")
                orchestrator.stop_all_services()
                sys.exit(0)
                
        elif args.command == "stop":
            services = getattr(args, 'services', None)
            if services:
                for service in services:
                    orchestrator.stop_service(service)
            else:
                orchestrator.stop_all_services()
                # Also stop Docker services
                console.print("\n🐳 Stopping Docker infrastructure...", style="cyan")
                orchestrator.stop_docker_services()
            sys.exit(0)
            
        elif args.command == "status":
            orchestrator.check_service_status()
            sys.exit(0)
            
        elif args.command == "docker":
            if args.docker_command == "start":
                services = args.services if hasattr(args, 'services') and args.services else None
                force_pull = getattr(args, 'force_pull', False)
                cleanup = getattr(args, 'cleanup', False)
                
                if cleanup:
                    success = orchestrator.start_docker_services_with_cleanup(services, force_pull)
                else:
                    success = orchestrator.start_docker_services(services, force_pull)
                sys.exit(0 if success else 1)
                
            elif args.docker_command == "stop":
                services = args.services if hasattr(args, 'services') and args.services else None
                success = orchestrator.stop_docker_services(services)
                sys.exit(0 if success else 1)
                
            elif args.docker_command == "cleanup":
                services = args.services if hasattr(args, 'services') and args.services else None
                containers_only = getattr(args, 'containers_only', False)
                
                console.print("🧹 [bold yellow]Docker Cleanup Operation[/bold yellow]", style="yellow")
                
                if not containers_only:
                    # Ensure external resources first
                    console.print("🔧 Creating external volumes and network...", style="blue")
                    if not orchestrator.ensure_external_resources():
                        console.print("❌ Failed to create external resources", style="red")
                        sys.exit(1)
                
                # Clean up containers
                console.print("🗑️  Cleaning up conflicting containers...", style="yellow")
                if orchestrator.cleanup_conflicting_containers(services):
                    console.print("✅ Docker cleanup completed successfully", style="green")
                    sys.exit(0)
                else:
                    console.print("❌ Docker cleanup failed", style="red")
                    sys.exit(1)
                    
            else:
                console.print("Use: docker start|stop|cleanup [--services SERVICE1 SERVICE2...]", style="yellow")
                sys.exit(1)
                
        elif args.command == "ollama":
            if args.install:
                if not orchestrator.start_docker_services(["ollama"]):
                    console.print("❌ Failed to start Ollama service", style="red")
                    sys.exit(1)
                # Wait for Ollama to be ready
                time.sleep(5)
                success = orchestrator.install_ollama_models(args.models)
                sys.exit(0 if success else 1)
            else:
                console.print("Use: ollama --install [--models MODEL1 MODEL2...]", style="yellow")
                sys.exit(1)
        
        elif args.command == "credentials":
            if args.export:
                success = orchestrator.export_credentials(args.export)
                sys.exit(0 if success else 1)
            else:
                orchestrator.show_all_credentials()
                sys.exit(0)
        
        elif args.command == "urls":
            orchestrator.show_urls_only()
            sys.exit(0)
        
        elif args.command == "config":
            if args.config_command == "create":
                console.print("🔧 Creating configuration files...", style="blue")
                success = True
                
                # Create credentials file
                if not orchestrator.credentials_file.exists() or args.force:
                    success &= orchestrator.create_credentials_file()
                else:
                    console.print(f"⚠️  Credentials file already exists: {orchestrator.credentials_file}", style="yellow")
                
                # Create .env file
                if not orchestrator.env_file.exists() or args.force:
                    success &= orchestrator.create_env_file()
                else:
                    console.print(f"⚠️  Environment file already exists: {orchestrator.env_file}", style="yellow")
                
                if success:
                    console.print("✅ Configuration files created successfully!", style="green")
                else:
                    console.print("❌ Some configuration files failed to create", style="red")
                
                sys.exit(0 if success else 1)
                
            elif args.config_command == "validate":
                success = orchestrator.validate_configuration()
                sys.exit(0 if success else 1)
            else:
                console.print("Use: config create|validate", style="yellow")
                sys.exit(1)
            
        elif args.command == "control":
            # Directly launch the interactive control panel
            console.print("\n🎮 [bold green]Launching Interactive Control Panel...[/bold green]", style="green")
            time.sleep(1)
            orchestrator.show_interactive_menu()
            # No need to stop_all_services here, as the menu handles its own exit
            sys.exit(0)

        elif args.command == "db":
            # Database management commands
            if args.db_action == "init":
                console.print("🗃️  [bold cyan]Initializing databases...[/bold cyan]")
                if orchestrator.initialize_databases(reset=args.reset):
                    console.print("✅ Database initialization completed", style="green")
                    return 0
                else:
                    console.print("❌ Database initialization failed", style="red")
                    return 1
                    
            elif args.db_action == "reset":
                if Confirm.ask("🗃️  Reset all databases? This will delete all data!"):
                    if orchestrator.reset_all_databases():
                        console.print("✅ All databases reset", style="green")
                        return 0
                    else:
                        console.print("❌ Database reset failed", style="red")
                        return 1
                else:
                    console.print("Database reset cancelled", style="yellow")
                    return 0
                    
            elif args.db_action == "status":
                console.print("📊 [bold cyan]Database Status:[/bold cyan]")
                postgres_status = orchestrator.is_docker_service_running("postgres")
                mongodb_status = orchestrator.is_docker_service_running("mongodb")
                neo4j_status = orchestrator.is_docker_service_running("neo4j")
                
                console.print(f"• PostgreSQL: {('[green]🟢 Running[/green]' if postgres_status else '[red]🔴 Stopped[/red]')} (Port 5432)")
                console.print(f"• MongoDB: {('[green]🟢 Running[/green]' if mongodb_status else '[red]🔴 Stopped[/red]')} (Port 27017)")
                console.print(f"• Neo4j: {('[green]🟢 Running[/green]' if neo4j_status else '[red]🔴 Stopped[/red]')} (Port 7474/7687)")
                return 0
            else:
                console.print("❌ Unknown database action", style="red")
                return 1

        elif args.command == "run":
            # Welcome message for comprehensive workflow
            console.print("\n🎯 [bold cyan]CogniVox Complete Setup & Control Panel[/bold cyan]", style="cyan")
            console.print("💡 This will guide you through the complete platform setup.", style="dim")
            console.print("📋 You can choose to proceed automatically or manage everything via the control panel.", style="dim")
            
            setup_success = True
            
            # Step 2: Docker Infrastructure (optional)
            if Confirm.ask("\n🐳 Start Docker infrastructure services?", default=True):
                console.print("\n🐳 Starting Docker infrastructure...")
                force_pull = getattr(args, 'force_pull', False)
                # Use cleanup method to avoid conflicts
                if orchestrator.start_docker_services_with_cleanup(force_pull=force_pull):
                    console.print("✅ Docker infrastructure started", style="green")
                    
                    # Wait for services to be ready
                    console.print("⏱️  Waiting for Docker services to be ready...")
                    time.sleep(5)
                    
                    # Optional: Initialize databases
                    if Confirm.ask("\n🗃️  Initialize/reset databases?", default=True):
                        if orchestrator.initialize_databases(reset=True):
                            console.print("✅ Databases initialized", style="green")
                        else:
                            console.print("⚠️  Database initialization failed, continuing...", style="yellow")
                    
                    # Optional: Install Ollama models
                    if Confirm.ask("\n🤖 Install Ollama models?", default=True):
                        if orchestrator.install_ollama_models():
                            console.print("✅ Ollama models installed", style="green")
                        else:
                            console.print("⚠️  Ollama installation failed, continuing...", style="yellow")
                else:
                    console.print("❌ Docker infrastructure failed to start", style="red")
                    if not Confirm.ask("Continue anyway?"):
                        return 1
            else:
                console.print("⚠️  Skipping Docker infrastructure", style="yellow")
            
            # Application setup phase (optional)
            console.rule("[bold blue]Phase 3: Application Setup")
            if Confirm.ask("Setup application environments now?", default=True):
                app_setup_success = orchestrator.setup_environment(auto_install=args.auto_install)
                if not app_setup_success:
                    console.print("❌ Application setup failed - you can retry from the control panel", style="red")
                    setup_success = False
                else:
                    console.print("✅ Application environments ready", style="green")
            else:
                console.print("⚠️  Skipping application setup - you can configure from the control panel", style="yellow")
            
            # Application services phase (optional)
            console.rule("[bold green]Phase 4: Application Services")
            if Confirm.ask("Start all application services now?", default=False):
                force_update = getattr(args, 'force_update', False)
                start_success = orchestrator.start_all_services(args.dev, force_update=force_update)
                if not start_success:
                    console.print("⚠️  Some services failed to start - you can manage them from the control panel", style="yellow")
                else:
                    console.print("✅ All application services started!", style="green")
            else:
                console.print("⚠️  Skipping service startup - you can start them from the control panel", style="yellow")
            
            # Always show interactive control panel
            console.rule("[bold magenta]Phase 5: Interactive Control Panel")
            console.print("🎮 [bold green]Entering Interactive Control Panel...[/bold green]", style="green")
            console.print("💡 From here you can manage all services, view logs, and monitor the platform.", style="dim")
            time.sleep(2)
            
            orchestrator.show_interactive_menu()
            
            # Clean shutdown when menu exits
            console.print("\n🛑 Exiting control panel - shutting down all services...", style="yellow")
            orchestrator.stop_all_services()
            sys.exit(0)
        
        else:
            console.print(f"❌ Unknown command: {args.command}", style="red")
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print("\n🛑 Operation cancelled by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    main() 