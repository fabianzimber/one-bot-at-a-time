"""Tests for LLM router service logic."""

import time

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


def test_extract_employee_reference_supports_name_and_id():
    router = LLMRouter(
        primary="gpt-4o",
        fallback="gpt-4o-mini",
        emergency="gpt-3.5-turbo",
        api_key="test-key",
    )

    assert router._extract_employee_reference("Wie viele Urlaubstage hat emp-007?") == {"employee_id": "emp-007"}
    assert router._extract_employee_reference("Wie viele Urlaubstage hat Felicitas Dowerg?") == {
        "employee_name": "Felicitas Dowerg"
    }


def test_fallback_response_builds_hr_tool_calls_with_name():
    router = LLMRouter(
        primary="gpt-4o",
        fallback="gpt-4o-mini",
        emergency="gpt-3.5-turbo",
        api_key="test-key",
    )

    response = router._fallback_response(
        [{"role": "user", "content": "Wie hoch ist das Jahresgehalt von Rosalie Ritter?"}]
    )

    assert response["tool_calls"][0]["name"] == "query_hr_system"
    assert response["tool_calls"][0]["arguments"]["employee_name"] == "Rosalie Ritter"


def test_fallback_response_uses_tool_payload_when_present():
    router = LLMRouter(
        primary="gpt-4o",
        fallback="gpt-4o-mini",
        emergency="gpt-3.5-turbo",
        api_key="test-key",
    )

    response = router._fallback_response(
        [
            {"role": "user", "content": "Fasse das zusammen."},
            {"role": "tool", "content": '{"data":{"results":[{"chunk_text":"Homeoffice ist zwei Tage pro Woche moeglich."}]}}'},
        ]
    )

    assert "Homeoffice" in response["message"]
    assert response["tool_calls"] == []


def test_register_failure_opens_circuit_after_three_errors():
    router = LLMRouter(
        primary="gpt-4o",
        fallback="gpt-4o-mini",
        emergency="gpt-3.5-turbo",
        api_key="test-key",
    )
    provider = router.providers[0]

    router._register_failure(provider)
    router._register_failure(provider)
    router._register_failure(provider)

    assert provider.enabled is False
    assert provider.disabled_until > time.time()
