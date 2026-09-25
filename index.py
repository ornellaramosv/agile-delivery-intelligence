"""Expose the existing FastAPI application for Vercel."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "apps" / "api"))

from app.main import app
