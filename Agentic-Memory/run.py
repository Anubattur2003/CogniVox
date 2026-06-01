#!/usr/bin/env python3
"""
CogniVox Agentic Memory Service Runner
=====================================
Robust runner with health checks, monitoring, and UV environment support.
"""

import os
import sys
import asyncio
import signal
import logging
import argparse
import platform
import subprocess
from pathlib import Path
from typing import Optional
import uvicorn
import time
import requests
import shutil

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("memory-service.log", mode='a', encoding='utf-8', errors='replace')
    ]
)
logger = logging.getLogger("memory-service")

class MemoryRunner:
    """CogniVox Memory Service Runner with UV support and health monitoring"""
    
    def __init__(self):
        self.service_name = "CogniVox Memory Service"
        self.default_port = 8002
        self.default_host = "0.0.0.0"
        self.venv_path = Path(".venv")
        self.shutdown_event = asyncio.Event()
        self.use_uv = self.detect_uv()
        
    def detect_uv(self) -> bool:
        """Detect if UV package manager is available and should be used"""
        # Check if UV is installed
        uv_available = shutil.which("uv") is not None
        
        # Check if this is a UV project (has pyproject.toml or uv.lock)
        uv_project = Path("pyproject.toml").exists() or Path("uv.lock").exists()
        
        # Check if .venv exists and use UV if both conditions are met
        venv_exists = self.venv_path.exists()
        
        use_uv = uv_available and (uv_project or venv_exists)
        
        if use_uv:
            logger.info("UV package manager detected and will be used")
        else:
            logger.info("Using traditional virtual environment")
            
        return use_uv
        
    def print_banner(self):
        """Print service banner"""
        print(f"{Colors.MAGENTA}{Colors.BOLD}")
        print("┌────────────────────────────────────────────────────────┐")
        print("│         CogniVox Agentic Memory Service               │")
        print("│         LangChain + LangGraph + MongoDB               │")
        print("└────────────────────────────────────────────────────────┘")
        print(f"{Colors.RESET}")
        
    def check_environment(self) -> bool:
        """Check if the environment is properly set up with UV support"""
        logger.info("Checking environment setup...")
        
        if self.use_uv:
            # Check UV availability and dependencies
            try:
                # Test UV and key dependencies
                result = subprocess.run([
                    "uv", "run", "python", "-c", 
                    "import fastapi, uvicorn, pymongo, motor, langchain, langgraph; print('Dependencies OK')"
                ], capture_output=True, text=True, timeout=15)
                
                if result.returncode != 0:
                    logger.error("Missing dependencies. Please run setup.py first")
                    logger.error(f"Error: {result.stderr}")
                    return False
                    
                logger.info("[OK] UV environment check passed")
                return True
                
            except Exception as e:
                logger.error(f"UV environment check failed: {e}")
                logger.error("Please run 'python setup.py' to install dependencies")
                return False
        else:
            # Traditional virtual environment check
            if platform.system() == "Windows":
                python_exe = self.venv_path / "Scripts" / "python.exe"
            else:
                python_exe = self.venv_path / "bin" / "python"
            
            if not python_exe.exists():
                logger.error(f"Virtual environment not found at {self.venv_path}")
                logger.error("Please run 'python setup.py' first")
                return False
                
            # Check key dependencies
            try:
                result = subprocess.run([
                    str(python_exe), "-c", 
                    "import fastapi, uvicorn, pymongo, motor, langchain, langgraph; print('Dependencies OK')"
                ], capture_output=True, text=True, timeout=15)
                
                if result.returncode != 0:
                    logger.error("Missing dependencies. Please run setup.py first")
                    logger.error(f"Error: {result.stderr}")
                    return False
                    
                logger.info("[OK] Environment check passed")
                return True
                
            except Exception as e:
                logger.error(f"Environment check failed: {e}")
                return False
    
    def check_external_services(self) -> bool:
        """Check if external services are available"""
        logger.info("Checking external services...")
        
        services = {
            "GraphRAG": "http://localhost:8003/health",
            "Ollama": "http://localhost:11434/api/tags"
        }
        
        all_healthy = True
        for service_name, url in services.items():
            try:
                if service_name == "GraphRAG":
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        logger.info(f"[OK] {service_name} - Available")
                    else:
                        logger.warning(f"[WARN] {service_name} - Not ready")
                        all_healthy = False
                elif service_name == "Ollama":
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        logger.info(f"[OK] {service_name} - Available")
                    else:
                        logger.warning(f"[WARN] {service_name} - HTTP {response.status_code}")
                        all_healthy = False
                        
            except Exception as e:
                logger.warning(f"[WARN] {service_name} - Check failed: {e}")
                all_healthy = False
        
        if not all_healthy:
            logger.warning("Some external services are not available")
            logger.warning("The memory service may have limited functionality")
            
        return True  # Continue even if some services are down
    
    def setup_environment_variables(self, port: int):
        """Setup required environment variables"""
        # Set basic service configuration
        os.environ["PORT"] = str(port)
        os.environ["MEMORY_PORT"] = str(port)
        
        # MongoDB configuration (Updated with correct credentials)
        os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
        os.environ.setdefault("MONGO_DB_NAME", "appdb")
        os.environ.setdefault("MONGO_USERNAME", "appuser")  # Corrected username
        os.environ.setdefault("MONGO_PASSWORD", "apppassword")  # Corrected password
        os.environ.setdefault("MONGO_AUTH_SOURCE", "appdb")
        
        # Ollama configuration
        os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
        os.environ.setdefault("DEFAULT_MODEL", "llama3.1")
        
        # GraphRAG service configuration
        graphrag_port = os.environ.get("GRAPHRAG_PORT", "8003")
        os.environ.setdefault("GRAPHRAG_API_URL", f"http://localhost:{graphrag_port}")
        
        # GPU acceleration settings for RTX 3050
        os.environ.setdefault("ENABLE_GPUS", "TRUE")
        os.environ.setdefault("GPU_COUNT", "1")
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
        os.environ.setdefault("GPU_MEMORY_LIMIT", "4GB")
        os.environ.setdefault("GPU_MEMORY_THRESHOLD_MB", "500")
        
        logger.info(f"MongoDB URL: {os.environ['MONGO_URL']}")
        logger.info(f"MongoDB Database: {os.environ['MONGO_DB_NAME']}")
        logger.info(f"Ollama URL: {os.environ['OLLAMA_BASE_URL']}")
        logger.info(f"Default Model: {os.environ['DEFAULT_MODEL']}")
        logger.info(f"GraphRAG API URL: {os.environ['GRAPHRAG_API_URL']}")
        logger.info(f"GPU Acceleration: {os.environ['ENABLE_GPUS']} (Device: {os.environ['CUDA_VISIBLE_DEVICES']})")
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def shutdown(self):
        """Graceful shutdown handler"""
        logger.info("Shutting down Memory service...")
        self.shutdown_event.set()
    
    def run_with_uvicorn(self, host: str, port: int, reload: bool = False, workers: int = 1):
        """Run the service using uvicorn with UV support"""
        try:
            logger.info(f"Starting {self.service_name} on {host}:{port}")
            
            # Setup environment variables
            self.setup_environment_variables(port)
            
            if self.use_uv:
                # Use UV to run uvicorn
                logger.info("Using UV package manager to run service...")
                cmd = [
                    "uv", "run", "uvicorn", "src.main:app",
                    "--host", host,
                    "--port", str(port),
                    "--log-level", "info"
                ]
                
                if reload:
                    cmd.append("--reload")
                if workers > 1:
                    cmd.extend(["--workers", str(workers)])
                
                # Setup signal handlers
                self.setup_signal_handlers()
                
                logger.info(f"[START] Memory service starting with UV...")
                logger.info(f"[DOCS] API Documentation: http://{host}:{port}/docs")
                logger.info(f"[HEALTH] Health Check: http://{host}:{port}/api/health")
                
                # Run the command
                process = subprocess.run(cmd)
                
            else:
                # Traditional uvicorn approach
                logger.info("Using traditional virtual environment...")
                
                # Configure uvicorn
                config = uvicorn.Config(
                    "src.main:app",
                    host=host,
                    port=port,
                    reload=reload,
                    workers=workers,
                    log_level="info",
                    access_log=True,
                    use_colors=True
                )
                
                server = uvicorn.Server(config)
                
                # Setup signal handlers
                self.setup_signal_handlers()
                
                # Start the server
                logger.info(f"[START] Memory service starting...")
                logger.info(f"[DOCS] API Documentation: http://{host}:{port}/docs")
                logger.info(f"[HEALTH] Health Check: http://{host}:{port}/api/health")
                
                server.run()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            sys.exit(1)
        finally:
            logger.info("Service stopped")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="CogniVox Agentic Memory Service Runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int, 
        default=8002,
        help="Port to run the API server on"
    )
    
    parser.add_argument(
        "--host", 
        type=str, 
        default="0.0.0.0",
        help="Host address to bind the server to"
    )
    
    parser.add_argument(
        "--reload", "-r",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=1,
        help="Number of worker processes"
    )
    
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip environment and service checks"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def main():
    """Main function to run the Memory service"""
    args = parse_args()
    
    # Set verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    runner = MemoryRunner()
    runner.print_banner()
    
    # Pre-flight checks
    if not args.skip_checks:
        if not runner.check_environment():
            logger.error("Environment check failed. Use --skip-checks to bypass.")
            sys.exit(1)
            
        if not runner.check_external_services():
            logger.error("External service check failed. Use --skip-checks to bypass.")
            sys.exit(1)
    else:
        logger.warning("Skipping pre-flight checks")
    
    # Start the service
    try:
        runner.run_with_uvicorn(
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers
        )
    except Exception as e:
        logger.error(f"Failed to start Memory service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 