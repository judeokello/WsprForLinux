"""
Pytest configuration file for W4L tests.

This file sets up the Python path so that tests can import modules from the src/ directory.
"""

import sys
import os
from pathlib import Path

# Add src/ to Python path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path)) 