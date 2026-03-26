"""Vercel entry point for the HR service."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

for path in (ROOT / "src", ROOT.parent / "shared" / "src"):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def load_app():
    from hr_service.main import app as hr_app

    return hr_app


app = load_app()
