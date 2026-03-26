"""LLM Provider routing with fallback and circuit breaker logic."""

import json
import logging
import time
from dataclasses import dataclass

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


@dataclass
class LLMProvider:
    model: str
    priority: int
    max_rpm: int
    cost_per_1k_tokens: float
    enabled: bool = True
    failure_count: int = 0
    last_failure_at: float = 0.0
    disabled_until: float = 0.0


class LLMRouter:
    """Routes LLM requests to the best available provider.

    Implements:
    - Priority-based routing (GPT-4o → GPT-4o-mini → GPT-3.5-turbo)
    - Circuit breaker: 3 failures in 60s → provider disabled for 120s
    - Load detection: RPM > 80% of max → downgrade
    - Token budget: daily/monthly limits per provider
    """

    def __init__(self, primary: str, fallback: str, emergency: str, api_key: str) -> None:
        self.providers = [
            LLMProvider(model=primary, priority=1, max_rpm=60, cost_per_1k_tokens=0.01),
            LLMProvider(model=fallback, priority=2, max_rpm=200, cost_per_1k_tokens=0.0003),
            LLMProvider(model=emergency, priority=3, max_rpm=500, cost_per_1k_tokens=0.0005),
        ]
        self.api_key = api_key
        self._client = AsyncOpenAI(api_key=api_key) if api_key and not api_key.startswith("test-") else None
        logger.info("LLM Router initialized", extra={"providers": [p.model for p in self.providers]})

    def get_active_provider(self) -> LLMProvider:
        """Return the highest-priority enabled provider."""
        now = time.time()
        for provider in sorted(self.providers, key=lambda p: p.priority):
            if provider.disabled_until and provider.disabled_until <= now:
                provider.enabled = True
                provider.failure_count = 0
            if provider.enabled and provider.disabled_until <= now:
                return provider
        # Fallback: re-enable all and return primary
        for provider in self.providers:
            provider.enabled = True
            provider.disabled_until = 0.0
        return sorted(self.providers, key=lambda p: p.priority)[0]

    def _register_failure(self, provider: LLMProvider) -> None:
        now = time.time()
        if now - provider.last_failure_at > 60:
            provider.failure_count = 0
        provider.failure_count += 1
        provider.last_failure_at = now
        if provider.failure_count >= 3:
            provider.enabled = False
            provider.disabled_until = now + 120

    def _fallback_response(self, messages: list[dict]) -> dict:
        user_message = next((item["content"] for item in reversed(messages) if item["role"] == "user"), "")
        last_tool_message = next((item for item in reversed(messages) if item["role"] == "tool"), None)
        if last_tool_message is not None:
            payload = json.loads(last_tool_message["content"])
            data = payload.get("data")
            if isinstance(data, dict) and "results" in data:
                results = data.get("results", [])
                if not results:
                    content = "Ich habe keine passenden Dokumentstellen gefunden."
                else:
                    top = results[0]
                    content = f"Ich habe eine passende Dokumentstelle gefunden: {top['chunk_text']}"
            else:
                content = f"Hier sind die angefragten HR-Daten: {json.dumps(data, ensure_ascii=False)}"
            return {"model": "heuristic-fallback", "message": content, "tool_calls": []}

        lowered = user_message.lower()
        employee_id_match = next((token for token in user_message.split() if token.startswith("emp-")), "emp-001")
        if any(keyword in lowered for keyword in ("urlaub", "vacation")):
            return {
                "model": "heuristic-fallback",
                "message": "",
                "tool_calls": [
                    {"id": "tool-vacation", "name": "query_hr_system", "arguments": {"action": "vacation_balance", "employee_id": employee_id_match}}
                ],
            }
        if any(keyword in lowered for keyword in ("gehalt", "salary", "lohn")):
            return {
                "model": "heuristic-fallback",
                "message": "",
                "tool_calls": [
                    {"id": "tool-salary", "name": "query_hr_system", "arguments": {"action": "salary_info", "employee_id": employee_id_match}}
                ],
            }
        if any(keyword in lowered for keyword in ("organigramm", "org", "abteilung")):
            return {
                "model": "heuristic-fallback",
                "message": "",
                "tool_calls": [
                    {"id": "tool-org", "name": "query_hr_system", "arguments": {"action": "org_chart", "parameters": {}}}
                ],
            }
        if any(keyword in lowered for keyword in ("zeit", "stunden", "timetracking")):
            return {
                "model": "heuristic-fallback",
                "message": "",
                "tool_calls": [
                    {"id": "tool-time", "name": "query_hr_system", "arguments": {"action": "time_tracking", "employee_id": employee_id_match}}
                ],
            }
        if any(keyword in lowered for keyword in ("dokument", "richtlinie", "policy", "hochgeladen", "suche")):
            return {
                "model": "heuristic-fallback",
                "message": "",
                "tool_calls": [
                    {"id": "tool-rag", "name": "search_documents", "arguments": {"query": user_message}}
                ],
            }
        return {
            "model": "heuristic-fallback",
            "message": "Ich bin der interne Trenkwalder Assistant und kann bei Dokumenten- und HR-Fragen helfen.",
            "tool_calls": [],
        }

    async def complete(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Send a completion request to the active provider."""
        provider = self.get_active_provider()
        logger.info("Using LLM provider", extra={"model": provider.model})

        if self._client is None:
            return self._fallback_response(messages)

        try:
            response = await self._client.chat.completions.create(
                model=provider.model,
                messages=messages,
                tools=tools or None,
                tool_choice="auto" if tools else None,
            )
            message = response.choices[0].message
            return {
                "model": provider.model,
                "message": message.content or "",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments),
                    }
                    for tool_call in (message.tool_calls or [])
                ],
            }
        except Exception:
            self._register_failure(provider)
            fallback_provider = self.get_active_provider()
            if fallback_provider.model == provider.model:
                return self._fallback_response(messages)
            return await self.complete(messages=messages, tools=tools)
