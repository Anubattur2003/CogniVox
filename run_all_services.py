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

# Force stdout/stderr to use UTF-8 encoding (prevents crashes when printing emojis on Windows consoles)
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

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