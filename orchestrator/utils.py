"""
Orchestrator Utilities
======================
CLI argument parsing, console helpers, and utility functions.
"""

import sys
import subprocess
import argparse

try:
    from rich.panel import Panel
    from rich.text import Text
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None


def install_rich_if_missing():
    """Install Rich and requests libraries if not available"""
    try:
        import requests
        REQUESTS_AVAILABLE = True
    except ImportError:
        REQUESTS_AVAILABLE = False
    
    missing_packages = []
    
    if not RICH_AVAILABLE:
        missing_packages.append("rich")
    
    if not REQUESTS_AVAILABLE:
        missing_packages.append("requests")
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}. Installing...")
        try:
            # Try UV first, then fallback to pip
            try:
                subprocess.check_call(["uv", "add"] + missing_packages)
                print(f"Packages {', '.join(missing_packages)} installed successfully with UV. Please run the script again.")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("🔄 UV not found, trying pip...")
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
                print(f"Packages {', '.join(missing_packages)} installed successfully with pip. Please run the script again.")
            sys.exit(0)
        except subprocess.CalledProcessError:
            print(f"Failed to install packages. Please install manually: uv add {' '.join(missing_packages)} or pip install {' '.join(missing_packages)}")
            sys.exit(1)


def show_enhanced_banner():
    """Show the enhanced CogniVox banner"""
    if not RICH_AVAILABLE:
        print("="*60)
        print("          CogniVox Agentic Platform")
        print("             Service Orchestrator")
        print("="*60)
        return
    
    banner = Panel(
        Text.assemble(
            ("╔══════════════════════════════════════════════════════════════╗\n", "cyan bold"),
            ("║                 CogniVox Agentic Platform                    ║\n", "cyan bold"),
            ("║                   Service Orchestrator                       ║\n", "cyan bold"),
            ("║                     Enhanced with Rich                       ║\n", "cyan bold"),
            ("╠══════════════════════════════════════════════════════════════╣\n", "cyan bold"),
            ("║  🔧 Backend API        (Port 8000) - FastAPI + SQLAlchemy   ║\n", "white"),
            ("║  🧠 Memory Service     (Port 8002) - LangChain + LangGraph  ║\n", "white"),
            ("║  📊 Graph RAG Service  (Port 8003) - LlamaIndex + Neo4j     ║\n", "white"),
            ("║  🌐 Frontend           (Port 3000) - React + TypeScript     ║\n", "white"),
            ("╚══════════════════════════════════════════════════════════════╝", "cyan bold"),
        ),
        padding=(1, 2),
        style="bold blue"
    )
    console.print(banner)


def parse_args():
    """Parse command line arguments with enhanced options"""
    parser = argparse.ArgumentParser(
        description="CogniVox Agentic Platform Orchestrator - Enhanced Edition",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Complete environment setup (Docker infrastructure + Application services)")
    setup_parser.add_argument("--services", nargs="+", help="Specific application services to setup", 
                             choices=["backend", "memory", "graphrag", "frontend"])
    setup_parser.add_argument("--clean", action="store_true", help="Clean setup (remove existing virtual environments)")
    setup_parser.add_argument("--auto-install", action="store_true", help="Auto-install missing prerequisites (UV, Node.js, etc.)")
    setup_parser.add_argument("--verbose", action="store_true", help="Verbose output during setup process")
    setup_parser.add_argument("--skip-docker", action="store_true", help="Skip Docker infrastructure setup (databases, LLM services)")
    setup_parser.add_argument("--skip-ollama", action="store_true", help="Skip Ollama LLM models installation")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start services")
    start_parser.add_argument("--services", nargs="+", help="Services to start",
                             choices=["backend", "memory", "graphrag", "frontend"])
    start_parser.add_argument("--dev", action="store_true", help="Development mode with hot reload")
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop services")
    stop_parser.add_argument("--services", nargs="+", help="Services to stop",
                            choices=["backend", "memory", "graphrag", "frontend"])
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check service status with health monitoring")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check prerequisites only")
    check_parser.add_argument("--auto-install", action="store_true", help="Auto-install missing prerequisites")
    
    # Docker command
    docker_parser = subparsers.add_parser("docker", help="Manage Docker infrastructure services")
    docker_subparsers = docker_parser.add_subparsers(dest="docker_command", help="Docker commands")
    
    # Docker start
    docker_start_parser = docker_subparsers.add_parser("start", help="Start Docker services")
    docker_start_parser.add_argument("--services", nargs="+", help="Docker services to start",
                                    choices=["neo4j", "ollama", "mongodb", "postgres", "pgadmin"])
    
    # Docker stop
    docker_stop_parser = docker_subparsers.add_parser("stop", help="Stop Docker services")
    docker_stop_parser.add_argument("--services", nargs="+", help="Docker services to stop",
                                   choices=["neo4j", "ollama", "mongodb", "postgres", "pgadmin"])
    
    # Ollama models
    ollama_parser = subparsers.add_parser("ollama", help="Manage Ollama models")
    ollama_parser.add_argument("--install", action="store_true", help="Install default models")
    ollama_parser.add_argument("--models", nargs="+", help="Specific models to install",
                              default=["qwen3:4b", "llama3.1:latest", "nomic-embed-text:latest", "mistral:latest"])
    
    # Run command (setup + start)
    run_parser = subparsers.add_parser("run", help="Setup and start all services (complete workflow)")
    run_parser.add_argument("--dev", action="store_true", help="Development mode with hot reload")
    run_parser.add_argument("--clean", action="store_true", help="Clean setup first")
    run_parser.add_argument("--skip-setup", action="store_true", help="Skip setup step")
    run_parser.add_argument("--skip-docker", action="store_true", help="Skip Docker services setup")
    run_parser.add_argument("--auto-install", action="store_true", help="Auto-install missing prerequisites")
    run_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    # Credentials command
    creds_parser = subparsers.add_parser("credentials", help="Display all credentials and URLs")
    creds_parser.add_argument("--export", help="Export credentials to file (json/env format)", choices=["json", "env"])
    
    # URLs command
    urls_parser = subparsers.add_parser("urls", help="Display all service URLs")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(dest="config_command", help="Config commands")
    
    # Config create
    config_create_parser = config_subparsers.add_parser("create", help="Create new configuration files")
    config_create_parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    
    # Config validate
    config_validate_parser = config_subparsers.add_parser("validate", help="Validate configuration files")
    
    return parser.parse_args()


def show_quick_start_guide():
    """Show quick start guide when no command is provided"""
    if not RICH_AVAILABLE:
        print("\n=== Quick Start Guide ===")
        print("🚀 Complete setup (Docker + Apps): uv run python run_all_services.py setup --auto-install")
        print("🎯 Setup and run all: uv run python run_all_services.py run --auto-install")
        print("🔧 Setup apps only: uv run python run_all_services.py setup --skip-docker --auto-install")
        print("🐳 Docker only: uv run python run_all_services.py docker start")
        print("🤖 Install Ollama models: uv run python run_all_services.py ollama --install")
        print("▶️  Start apps: uv run python run_all_services.py start --dev")
        print("📊 Check status: uv run python run_all_services.py status")
        print("🔑 Show credentials: uv run python run_all_services.py credentials")
        print("🌐 Show URLs: uv run python run_all_services.py urls")
        print("⚙️  Create config: uv run python run_all_services.py config create")
        print("🛑 Stop services: uv run python run_all_services.py stop")
        print("🐳❌ Stop Docker: uv run python run_all_services.py docker stop")
        print("\nAlternatively, use the modular version:")
        print("🏗️  Use as module: python -m orchestrator [command]")
        return
    
    quick_start = Panel(
        "[bold cyan]Quick Start Guide:[/bold cyan]\n\n"
        "🚀 [green]Complete setup (Docker + Apps):[/green] `uv run python run_all_services.py setup --auto-install`\n"
        "🎯 [green]Setup and run all:[/green] `uv run python run_all_services.py run --auto-install`\n"
        "🔧 [blue]Setup apps only:[/blue] `uv run python run_all_services.py setup --skip-docker --auto-install`\n"
        "🐳 [cyan]Docker only:[/cyan] `uv run python run_all_services.py docker start`\n"
        "🤖 [purple]Install Ollama models:[/purple] `uv run python run_all_services.py ollama --install`\n"
        "▶️  [yellow]Start apps:[/yellow] `uv run python run_all_services.py start --dev`\n"
        "📊 [magenta]Check status:[/magenta] `uv run python run_all_services.py status`\n"
        "🔑 [cyan]Show credentials:[/cyan] `uv run python run_all_services.py credentials`\n"
        "🌐 [blue]Show URLs:[/blue] `uv run python run_all_services.py urls`\n"
        "⚙️  [yellow]Create config:[/yellow] `uv run python run_all_services.py config create`\n"
        "🛑 [red]Stop services:[/red] `uv run python run_all_services.py stop`\n"
        "🐳❌ [red]Stop Docker:[/red] `uv run python run_all_services.py docker stop`\n\n"
        "🏗️  [bold magenta]Modular version:[/bold magenta] `python -m orchestrator [command]`\n",
        title="CogniVox Orchestrator",
        border_style="blue"
    )
    console.print(quick_start) 