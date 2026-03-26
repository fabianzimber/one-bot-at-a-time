"""Tests for LLM router service logic."""

from chat_orchestrator.services.llm_router import LLMRouter


def test_get_active_provider_reenable_respects_priority():
    router = LLMRouter(
        primary="gpt-4o",
        fallback="gpt-4o-mini",
        emergency="gpt-3.5-turbo",
        api_key="test-key",
    )

    # Ensure order in list is not tied to priority.
    router.providers = [router.providers[2], router.providers[0], router.providers[1]]
    for provider in router.providers:
        provider.enabled = False

    provider = router.get_active_provider()

    assert provider.model == "gpt-4o"
    assert provider.priority == 1
