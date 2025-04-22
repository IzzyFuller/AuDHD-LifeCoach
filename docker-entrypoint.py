#!/usr/bin/env python
"""
Docker entrypoint script that properly handles Python module imports
"""
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now we can import the module
from audhd_lifecoach.main import start_application

if __name__ == "__main__":
    start_application()