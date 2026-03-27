"""Tests for LLM router service logic."""

import time
from types import SimpleNamespace

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
            {
                "role": "tool",
                "content": '{"data":{"results":[{"chunk_text":"Homeoffice ist zwei Tage pro Woche moeglich."}]}}',
            },
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


class FakeCompletions:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.models: list[str] = []

    async def create(self, *, model: str, messages: list[dict], stream: bool = False, tools=None, tool_choice=None):
        del messages, stream, tools, tool_choice
        self.models.append(model)
        current = self.responses.pop(0)
        if isinstance(current, Exception):
            raise current
        return current


def build_openai_response(message: str) -> object:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=message,
                    tool_calls=[],
                )
            )
        ]
    )


async def test_complete_retries_with_lower_priority_provider_after_primary_failure():
    router = LLMRouter(
        primary="gpt-5.4",
        fallback="gpt-4.1-mini",
        emergency="gpt-4.1-nano",
        api_key="live-key",
    )
    router.providers[0].failure_count = 2
    router.providers[0].last_failure_at = time.time()
    completions = FakeCompletions([RuntimeError("primary unavailable"), build_openai_response("Fallback answer")])
    router._client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    response = await router.complete(messages=[{"role": "user", "content": "Hallo"}], tools=[])

    assert response["model"] == "gpt-4.1-mini"
    assert response["message"] == "Fallback answer"
    assert completions.models == ["gpt-5.4", "gpt-4.1-mini"]


async def test_complete_uses_heuristic_response_when_no_provider_remains_available():
    router = LLMRouter(
        primary="gpt-5.4",
        fallback="gpt-4.1-mini",
        emergency="gpt-4.1-nano",
        api_key="live-key",
    )
    router.providers[0].failure_count = 2
    router.providers[0].last_failure_at = time.time()
    router.providers[1].enabled = False
    router.providers[1].disabled_until = time.time() + 120
    router.providers[2].enabled = False
    router.providers[2].disabled_until = time.time() + 120
    completions = FakeCompletions([RuntimeError("all unavailable")])
    router._client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    response = await router.complete(messages=[{"role": "user", "content": "Wie viele Urlaubstage hat Frau Dowerg?"}])

    assert response["model"] == "heuristic-fallback"
    assert response["tool_calls"][0]["arguments"]["employee_name"] == "Frau Dowerg"


# ── stream_complete tests ───────────────────────────────────────────


class FakeStreamChunk:
    """Mimics an OpenAI streaming chunk object."""

    def __init__(self, content: str | None = None) -> None:
        self.choices = [SimpleNamespace(delta=SimpleNamespace(content=content))]


class FakeAsyncStream:
    """Mimics the async iterable returned by OpenAI stream=True."""

    def __init__(self, chunks: list[FakeStreamChunk]) -> None:
        self._chunks = list(chunks)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._chunks:
            raise StopAsyncIteration
        return self._chunks.pop(0)


class FakeStreamCompletions:
    def __init__(self, stream: FakeAsyncStream | Exception) -> None:
        self._stream = stream
        self.calls = 0

    async def create(self, *, model: str, messages: list[dict], stream: bool = False, tools=None, tool_choice=None):
        del messages, tools, tool_choice
        self.calls += 1
        if isinstance(self._stream, Exception):
            raise self._stream
        return self._stream


async def test_stream_complete_yields_deltas_and_done_sentinel():
    router = LLMRouter(primary="gpt-5.4", fallback="gpt-4.1-mini", emergency="gpt-4.1-nano", api_key="live-key")
    fake_stream = FakeAsyncStream(
        [
            FakeStreamChunk("Hello "),
            FakeStreamChunk("World"),
            FakeStreamChunk(None),  # empty chunk — should be skipped
        ]
    )
    completions = FakeStreamCompletions(fake_stream)
    router._client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    events = [event async for event in router.stream_complete(messages=[{"role": "user", "content": "Hi"}])]

    deltas = [e["delta"] for e in events if "delta" in e]
    assert deltas == ["Hello ", "World"]
    assert events[-1] == {"done": True, "model": "gpt-5.4"}


async def test_stream_complete_falls_back_to_next_provider_on_error():
    router = LLMRouter(primary="gpt-5.4", fallback="gpt-4.1-mini", emergency="gpt-4.1-nano", api_key="live-key")
    # Set up primary to be near circuit-break so failure disables it
    router.providers[0].failure_count = 2
    router.providers[0].last_failure_at = time.time()

    # First call (stream=True) raises, second call (complete() fallback) succeeds
    fallback_response = build_openai_response("Fallback works")

    call_count = 0

    async def fake_create(*, model, messages, stream=False, tools=None, tool_choice=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call is the streaming attempt — fail it
            raise RuntimeError("stream broken")
        # Second call is the non-streaming fallback via complete()
        return fallback_response

    router._client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create)))

    events = [event async for event in router.stream_complete(messages=[{"role": "user", "content": "Hi"}])]

    deltas = [e["delta"] for e in events if "delta" in e]
    assert "Fallback works" in deltas[0]
    assert events[-1]["done"] is True


async def test_stream_complete_uses_heuristic_when_no_client():
    router = LLMRouter(primary="gpt-5.4", fallback="gpt-4.1-mini", emergency="gpt-4.1-nano", api_key="test-key")
    # _client is None because api_key starts with "test-"

    events = [
        event
        async for event in router.stream_complete(
            messages=[{"role": "user", "content": "Wie viel Urlaub hat emp-003?"}]
        )
    ]

    assert events[-1]["done"] is True
    assert events[-1]["model"] == "heuristic-fallback"
    # Should have at least one delta
    assert any("delta" in e for e in events)
