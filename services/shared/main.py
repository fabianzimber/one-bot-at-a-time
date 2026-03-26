"""Vercel entry point for the shared service."""

import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parent

path_str = str(ROOT / "src")
if path_str not in sys.path:
    sys.path.insert(0, path_str)

app = import_module("shared.main").app
