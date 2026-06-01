#!/usr/bin/env python3
"""
CogniVox Agentic Graph RAG Service Runner
=======================================
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
        logging.FileHandler("graph-rag-service.log", mode='a', encoding='utf-8', errors='replace')
    ]
)
logger = logging.getLogger("graph-rag-service")

class GraphRAGRunner:
    """CogniVox Graph RAG Service Runner with UV support and health monitoring"""
    
    def __init__(self):
        self.service_name = "CogniVox Graph RAG Service"
        self.default_port = 8003
        self.default_host = "0.0.0.0"
        self.venv_path = Path(".venv")
        self.shutdown_event = asyncio.Event()
        

    def print_banner(self):
        """Print service banner"""
        print(f"{Colors.GREEN}{Colors.BOLD}")
        print("┌────────────────────────────────────────────────────────┐")
        print("│       CogniVox Agentic Graph RAG Service              │")
        print("│         LlamaIndex + Neo4j + GraphRAG                 │")
        print("└────────────────────────────────────────────────────────┘")
        print(f"{Colors.RESET}")
        
    def check_environment(self) -> bool:
        """Check if the environment is properly set up"""
        logger.info("Checking environment setup...")
        
        # Check for virtual environment
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
                "import fastapi, uvicorn, llama_index, neo4j, langchain; print('Dependencies OK')"
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
            "Neo4j": "http://localhost:7474",
            "Memory Service": "http://localhost:8002/api/health",
            "Ollama": "http://localhost:11434/api/tags"
        }
        
        all_healthy = True
        for service_name, url in services.items():
            try:
                if service_name == "Memory Service":
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        logger.info(f"[OK] {service_name} - Available")
                    else:
                        logger.warning(f"[WARN] {service_name} - HTTP {response.status_code}")
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
            logger.warning("The Graph RAG service may have limited functionality")
            
        return True  # Continue even if some services are down
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def shutdown(self):
        """Graceful shutdown handler"""
        logger.info("Shutting down Graph RAG service...")
        self.shutdown_event.set()
    
    def check_gpu_availability(self):
        """Check GPU availability for ML operations"""
        try:
            result = subprocess.run([
                sys.executable, "-c", 
                "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'Device Count: {torch.cuda.device_count() if torch.cuda.is_available() else 0}')"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info(f"GPU Status: {result.stdout.strip()}")
            else:
                logger.warning("Could not check GPU status")
                
        except Exception as e:
            logger.warning(f"GPU check failed: {e}")
    
    def run_with_uvicorn(self, host: str, port: int, reload: bool = False, workers: int = 1):
        """Run the service using uvicorn"""
        try:
            logger.info(f"Starting {self.service_name} on {host}:{port}")
            
            # Set environment variables
            os.environ["GRAPHRAG_PORT"] = str(port)
            os.environ["GRAPHRAG_HOST"] = host
            
            # Additional environment variables for service discovery
            backend_port = os.environ.get("BACKEND_PORT", "8000")
            memory_port = os.environ.get("MEMORY_PORT", "8002")
            
            os.environ["BACKEND_SERVICE_URL"] = f"http://localhost:{backend_port}"
            os.environ["MEMORY_SERVICE_URL"] = f"http://localhost:{memory_port}"
            
            logger.info(f"Backend Service URL: {os.environ['BACKEND_SERVICE_URL']}")
            logger.info(f"Memory Service URL: {os.environ['MEMORY_SERVICE_URL']}")
            
            # Check GPU availability
            self.check_gpu_availability()
            
            # Configure uvicorn
            config = uvicorn.Config(
                "src.api.app:app",
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
            logger.info(f"[START] {self.service_name} starting...")
            logger.info(f"[DOCS] API Documentation: http://{host}:{port}/docs")
            logger.info(f"[HEALTH] Health Check: http://{host}:{port}/health")
            
            # Run in event loop
            loop = asyncio.get_event_loop()
            loop.run_until_complete(server.serve())
            
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
        description="CogniVox Agentic Graph RAG Service Runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--host", 
        type=str, 
        default="0.0.0.0",
        help="Host address to bind the server to"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=8003,
        help="Port to run the API server on"
    )
    
    parser.add_argument(
        "--reload", 
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1,
        help="Number of worker processes"
    )
    
    parser.add_argument(
        "--log-level", 
        type=str, 
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level"
    )
    
    parser.add_argument(
        "--skip-checks", 
        action="store_true",
        help="Skip environment and service health checks"
    )
    
    parser.add_argument(
        "--dev", 
        action="store_true",
        help="Run in development mode (enables reload and debug logging)"
    )
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Development mode adjustments
    if args.dev:
        args.reload = True
        args.log_level = "debug"
        logger.setLevel(logging.DEBUG)
    
    # Create runner instance
    runner = GraphRAGRunner()
    
    # Print banner
    runner.print_banner()
    
    # Run pre-flight checks
    if not args.skip_checks:
        logger.info("Running pre-flight checks...")
        
        if not runner.check_environment():
            logger.error("Environment check failed!")
            sys.exit(1)
            
        if not runner.check_external_services():
            logger.error("Service check failed!")
            sys.exit(1)
    else:
        logger.warning("Skipping pre-flight checks...")
    
    # Start the service
    runner.run_with_uvicorn(
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers
    )

if __name__ == "__main__":
    main() 