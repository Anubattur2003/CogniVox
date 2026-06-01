#!/usr/bin/env python3
"""
CogniVox Agentic Frontend Service Runner
========================================
Robust runner for React/TypeScript frontend with health checks and monitoring.
"""

import os
import sys
import json
import signal
import logging
import argparse
import platform
import subprocess
from pathlib import Path
from typing import Optional
import time
import requests
import threading

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
        logging.FileHandler("frontend-service.log", mode='a')
    ]
)
logger = logging.getLogger("frontend-service")

class FrontendRunner:
    """CogniVox Frontend Service Runner with health monitoring"""
    
    def __init__(self):
        self.service_name = "CogniVox Frontend"
        self.default_port = 3000
        self.default_host = "localhost"
        self.project_dir = Path(__file__).parent
        self.package_json = self.project_dir / "package.json"
        self.node_modules = self.project_dir / "node_modules"
        self.env_file = self.project_dir / ".env"
        self.process = None
        self.shutdown_requested = False
        
    def print_banner(self):
        """Print service banner"""
        print(f"{Colors.CYAN}{Colors.BOLD}")
        print("┌────────────────────────────────────────────────────────┐")
        print("│            CogniVox Agentic Frontend Service          │")
        print("│               React + TypeScript + Vite               │")
        print("└────────────────────────────────────────────────────────┘")
        print(f"{Colors.RESET}")
        
    def check_environment(self) -> bool:
        """Check if the environment is properly set up"""
        logger.info("Checking environment setup...")
        
        # Check if package.json exists
        if not self.package_json.exists():
            logger.error("package.json not found!")
            logger.error("Please ensure you're in the frontend directory")
            return False
            
        # Check if node_modules exists
        if not self.node_modules.exists():
            logger.error("node_modules not found!")
            logger.error("Please run 'python setup.py' first")
            return False
            
        # Check Node.js
        try:
            result = subprocess.run(
                ["node", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error("Node.js not found!")
                return False
                
            logger.info(f"[OK] Node.js version: {result.stdout.strip()}")
            
        except Exception as e:
            logger.error(f"Node.js check failed: {e}")
            return False
            
        # Check npm
        try:
            result = subprocess.run(
                ["npm", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error("npm not found!")
                return False
                
            logger.info(f"[OK] npm version: {result.stdout.strip()}")
            
        except Exception as e:
            logger.error(f"npm check failed: {e}")
            return False
            
        logger.info("[OK] Environment check passed")
        return True
    
    def check_backend_services(self) -> bool:
        """Check if backend services are available"""
        logger.info("Checking backend services...")
        
        # Read environment configuration
        env_config = self.load_env_config()
        
        services = {
            "Backend API": env_config.get("VITE_API_BASE_URL", "http://localhost:8000"),
            "Memory API": env_config.get("VITE_MEMORY_API_URL", "http://localhost:8002"),
            "GraphRAG API": env_config.get("VITE_GRAPHRAG_API_URL", "http://localhost:8003")
        }
        
        all_healthy = True
        for service_name, url in services.items():
            try:
                # Try health check endpoint
                health_url = f"{url}/health" if not url.endswith('/') else f"{url}health"
                response = requests.get(health_url, timeout=5)
                
                if response.status_code == 200:
                    logger.info(f"[OK] {service_name} - Available at {url}")
                else:
                    logger.warning(f"[WARN] {service_name} - HTTP {response.status_code} at {url}")
                    all_healthy = False
                    
            except requests.exceptions.ConnectionError:
                logger.warning(f"[WARN] {service_name} - Not available at {url}")
                all_healthy = False
            except Exception as e:
                logger.warning(f"[WARN] {service_name} - Check failed: {e}")
                all_healthy = False
        
        if not all_healthy:
            logger.warning("Some backend services are not available")
            logger.warning("The frontend may have limited functionality")
            logger.info("Make sure to start backend services first")
            
        return True  # Continue even if backend services are down
    
    def load_env_config(self) -> dict:
        """Load environment configuration"""
        env_vars = {}
        
        if self.env_file.exists():
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
                            
            except Exception as e:
                logger.warning(f"Could not load .env file: {e}")
                
        return env_vars
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown_requested = True
            if self.process:
                self.process.terminate()
                
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def wait_for_server(self, host: str, port: int, timeout: int = 60) -> bool:
        """Wait for the development server to start"""
        logger.info(f"Waiting for development server to start on {host}:{port}...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"http://{host}:{port}", timeout=2)
                if response.status_code == 200:
                    logger.info("[OK] Development server is ready!")
                    return True
            except:
                pass
                
            time.sleep(2)
            
        logger.warning("Development server did not start within timeout period")
        return False
    
    def run_dev_server(self, host: str, port: int, open_browser: bool = False) -> bool:
        """Run the development server"""
        try:
            logger.info(f"Starting {self.service_name} development server...")
            
            # Set environment variables
            env = os.environ.copy()
            env.update(self.load_env_config())
            
            # Add service discovery environment variables
            env["VITE_FRONTEND_PORT"] = str(port)
            env["VITE_FRONTEND_HOST"] = host
            
            # Prepare npm command
            cmd = ["npm", "run", "dev"]
            
            # Add Vite-specific options
            cmd.extend(["--", "--host", host, "--port", str(port)])
            
            if not open_browser:
                cmd.extend(["--no-open"])
                
            logger.info(f"Running command: {' '.join(cmd)}")
            
            # Start the process
            self.process = subprocess.Popen(
                cmd,
                cwd=self.project_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitor output in a separate thread
            output_thread = threading.Thread(
                target=self._monitor_output,
                args=(self.process,),
                daemon=True
            )
            output_thread.start()
            
            # Wait for server to be ready
            self.wait_for_server(host, port)
            
            logger.info(f"[START] {self.service_name} running at http://{host}:{port}")
            logger.info("Press Ctrl+C to stop the server")
            
            # Wait for process to finish or shutdown signal
            return_code = self.process.wait()
            
            if return_code != 0 and not self.shutdown_requested:
                logger.error(f"Development server exited with code {return_code}")
                return False
                
            return True
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            return True
        except Exception as e:
            logger.error(f"Failed to start development server: {e}")
            return False
        finally:
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            logger.info("Development server stopped")
    
    def _monitor_output(self, process):
        """Monitor process output and log it"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    # Filter and format Vite output
                    line = line.strip()
                    if "Local:" in line or "Network:" in line:
                        logger.info(f"📡 {line}")
                    elif "ready in" in line.lower():
                        logger.info(f"⚡ {line}")
                    elif "error" in line.lower():
                        logger.error(f"❌ {line}")
                    elif "warning" in line.lower():
                        logger.warning(f"⚠ {line}")
                    elif line and not line.startswith('>'):
                        logger.info(f"🔧 {line}")
                        
        except Exception as e:
            logger.debug(f"Output monitoring error: {e}")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="CogniVox Agentic Frontend Service Runner",
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
        default=3000,
        help="Port to run the development server on"
    )
    
    parser.add_argument(
        "--open", 
        action="store_true",
        help="Open browser automatically"
    )
    
    parser.add_argument(
        "--skip-checks", 
        action="store_true",
        help="Skip environment and service health checks"
    )
    
    parser.add_argument(
        "--log-level", 
        type=str, 
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level"
    )
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Set logging level
    log_level = getattr(logging, args.log_level.upper())
    logging.getLogger().setLevel(log_level)
    
    # Create runner instance
    runner = FrontendRunner()
    
    # Print banner
    runner.print_banner()
    
    # Setup signal handlers
    runner.setup_signal_handlers()
    
    # Run pre-flight checks
    if not args.skip_checks:
        logger.info("Running pre-flight checks...")
        
        if not runner.check_environment():
            logger.error("Environment check failed!")
            sys.exit(1)
            
        if not runner.check_backend_services():
            logger.error("Service check failed!")
            sys.exit(1)
    else:
        logger.warning("Skipping pre-flight checks...")
    
    # Start the development server
    success = runner.run_dev_server(
        host=args.host,
        port=args.port,
        open_browser=args.open
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 