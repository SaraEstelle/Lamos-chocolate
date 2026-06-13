"""
conftest.py
===========
pytest configuration for Lamos Chocolate.

This file is automatically loaded by pytest and tells Python where to find
Django modules (config, apps, etc.).

Without this file, pytest cannot import "config.settings.test" because
the backend/ directory is not in sys.path.
"""

import sys
from pathlib import Path

# Add the current directory (backend/) to Python path
# This allows Python to import:
# - import config
# - import apps
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))
