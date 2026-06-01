#!/usr/bin/env python3
"""
CogniVox Server Startup Script
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import required modules
import uvicorn
from src.api.app import app

if __name__ == "__main__":
    # Get port from environment or use default (8002 to avoid conflicts)
    port = int(os.getenv("COGNIVOX_API_PORT", 8002))
    host = os.getenv("COGNIVOX_API_HOST", "0.0.0.0")
    
    print(f"Starting CogniVox API server on {host}:{port}")
    print("Press Ctrl+C to stop the server")
    
    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,  # Set to True for development
        log_level="info"
    ) 