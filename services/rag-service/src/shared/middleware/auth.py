"""Authentication helpers shared across services."""

from collections.abc import Awaitable, Callable

from fastapi import Header, HTTPException, status


def build_internal_api_key_dependency(
    expected_api_key: str,
) -> Callable[[str | None], Awaitable[None]]:
    """Create a dependency that validates internal service traffic.

    The dependency becomes a no-op when no API key is configured. This keeps
    local development and tests frictionless while production can enforce
    service-to-service authentication.
    """

    async def verify_internal_api_key(
        x_internal_api_key: str | None = Header(default=None, alias="x-internal-api-key"),
    ) -> None:
        if not expected_api_key:
            return

        if x_internal_api_key != expected_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing internal API key",
            )

    return verify_internal_api_key
