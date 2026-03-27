"""CORS configuration helper."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_ALLOWED_METHODS = ["GET", "POST", "OPTIONS"]
_ALLOWED_HEADERS = [
    "Content-Type",
    "Authorization",
    "x-internal-api-key",
    "x-request-id",
    "x-forwarded-for",
]


def setup_cors(app: FastAPI, origins: list[str]) -> None:
    """Add CORS middleware with the given allowed origins."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=_ALLOWED_METHODS,
        allow_headers=_ALLOWED_HEADERS,
    )
