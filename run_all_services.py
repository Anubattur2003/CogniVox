#!/usr/bin/env python3
"""
CogniVox Agentic Platform Orchestrator - Standalone Entry Point
===============================================================
New modular version of the service orchestrator.

Usage:
    python run_all_services_new.py [command] [options]
    
This is the new modular version. To use the orchestrator as a module:
    python -m orchestrator [command] [options]
"""

import sys
from pathlib import Path

# Add the current directory to the path to allow importing orchestrator
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from orchestrator.main import main
except ImportError as e:
    print(f"❌ Failed to import orchestrator: {e}")
    print("Make sure all required dependencies are installed:")
    print("  pip install rich")
    print("  pip install requests")
    sys.exit(1)

if __name__ == "__main__":
    main() 