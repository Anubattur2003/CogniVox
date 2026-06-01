"""
Main module for CogniVox - forwarding to CLI implementation.

This module is kept for backward compatibility.
New code should import directly from src.cli.main.
"""

import sys
from src.cli.main import main, parse_args

# Re-export symbols for backward compatibility
__all__ = ['main', 'parse_args']

if __name__ == "__main__":
    print("Warning: Using deprecated 'src/main.py'. Please use 'bin/cognivox' instead.")
    sys.exit(main())
