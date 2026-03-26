"""Vercel entry point for the HR service."""

import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parent

for path in (ROOT / "src", ROOT.parent / "shared" / "src"):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

app = import_module("hr_service.main").app
