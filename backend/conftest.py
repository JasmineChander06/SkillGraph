"""Pytest configuration ensuring backend directory is on sys.path."""

import sys
from pathlib import Path

# Ensure the backend directory is first on sys.path so 'from app...' resolves to backend/app
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
