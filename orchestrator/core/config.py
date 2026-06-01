"""
Configuration classes for services
"""

import time
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from pathlib import Path

# Try to import requests for health checks
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@dataclass
class ServiceConfig:
    """Configuration for a microservice"""
    name: str
    directory: str
    run_command: List[str]
    port: int
    health_endpoint: str = "/health"
    dependencies: List[str] = field(default_factory=list)
    color: str = "white"
    tech_stack: str = "Python Service"
    process: Optional[subprocess.Popen] = None
    terminal_process: Optional[subprocess.Popen] = None  # For terminal launcher
    use_terminal: bool = True  # Default to using separate terminals
    last_health_check: Optional[float] = None
    always_update: bool = False  # Whether to always update dependencies before starting
    update_command: List[str] = field(default_factory=list)  # Custom update command if needed
    
    @property
    def health_url(self) -> str:
        """Get the full health check URL"""
        return f"http://127.0.0.1:{self.port}{self.health_endpoint}"
    
    def is_running(self) -> bool:
        """Check if service is running - prioritize health check over process tracking"""
        # First, try health check - if service responds, it's running regardless of how it started
        if self._check_health():
            return True
        
        # If health check fails, fall back to process tracking for orchestrator-started services
        if self.use_terminal:
            # For terminal mode, check if terminal process exists
            return self.terminal_process and self.terminal_process.poll() is None
        else:
            # For subprocess mode, check if process is running
            return self.process and self.process.poll() is None
    
    def _check_health(self) -> bool:
        """Check service health via HTTP endpoint with rate limiting"""
        # Rate limit health checks to avoid spam
        current_time = time.time()
        if (self.last_health_check and 
            current_time - self.last_health_check < 60):  # 60 second minimum interval
            return True  # Assume healthy if checked recently
            
        self.last_health_check = current_time
        if not REQUESTS_AVAILABLE:
            # Fallback: check if port is listening (service could be running independently)
            return self._check_port_listening()
        
        try:
            health_url = f"http://127.0.0.1:{self.port}{self.health_endpoint}"
            response = requests.get(health_url, timeout=5)
            is_healthy = response.status_code == 200
            if is_healthy:
                self.last_health_check = time.time()
            return is_healthy
        except requests.exceptions.ConnectionError:
            # Service not responding - check if port is at least listening
            return self._check_port_listening()
        except requests.exceptions.Timeout:
            # Service too slow to respond, but port might be listening
            return self._check_port_listening()
        except requests.exceptions.RequestException:
            # Other network issues - check port
            return self._check_port_listening()
        except Exception:
            # Any other error - check port
            return self._check_port_listening()
    
    def _check_port_listening(self) -> bool:
        """Check if service port is listening (fallback detection)"""
        try:
            import socket
            with socket.create_connection(("127.0.0.1", self.port), timeout=3):
                return True
        except (socket.error, ConnectionRefusedError, OSError):
            return False


class DockerServiceConfig:
    """Docker service configuration for infrastructure services"""
    def __init__(self, name: str, container_name: str, port: int, health_check: str,
                 dependencies: List[str] = None, tech_stack: str = "Docker", 
                 color: str = "cyan", environment_vars: Dict[str, str] = None,
                 always_pull: bool = True):
        self.name = name
        self.container_name = container_name
        self.port = port
        self.health_check = health_check
        self.dependencies = dependencies or []
        self.tech_stack = tech_stack
        self.color = color
        self.environment_vars = environment_vars or {}
        self.is_running = False
        self.setup_completed = False
        self.setup_time = 0.0
        self.last_health_check = None
        self.always_pull = always_pull  # Whether to always pull latest image before starting 