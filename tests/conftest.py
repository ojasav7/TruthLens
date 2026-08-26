"""Pytest configuration for TruthLens tests."""

import os
import sys

# Ensure project root is on sys.path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load models at test startup (same as FastAPI lifespan)
from backend.services.model_loader import load_all_models
load_all_models()
