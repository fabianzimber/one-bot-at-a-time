"""Vercel entry point for the chat orchestrator service."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

for path in (ROOT / "src", ROOT.parent / "shared" / "src"):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def load_app():
    from chat_orchestrator.main import app as chat_app

    return chat_app


app = load_app()
