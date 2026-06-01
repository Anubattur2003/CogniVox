"""
CogniVox Agentic Platform Orchestrator
=====================================
Enhanced master orchestrator with Rich UI, automatic prerequisite detection,
and robust setup for fresh repositories.
"""

__version__ = "2.0.0"
__author__ = "CogniVox Team"
__description__ = "CogniVox Agentic Platform Service Orchestrator"

from .core.orchestrator import ServiceOrchestrator
from .core.config import ServiceConfig, DockerServiceConfig
from .core.prerequisites import PrerequisiteChecker
from .services.terminal_launcher import TerminalLauncher
from .main import main

__all__ = [
    "ServiceOrchestrator",
    "ServiceConfig", 
    "DockerServiceConfig",
    "PrerequisiteChecker",
    "TerminalLauncher",
    "main"
] 