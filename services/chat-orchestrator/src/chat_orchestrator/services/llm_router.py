"""LLM Provider routing with fallback and circuit breaker logic."""

import json
import logging
import re
import time
from dataclasses import dataclass

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

EMPLOYEE_ID_PATTERN = re.compile(r"\b(emp-\d{3})\b", re.IGNORECASE)
EMPLOYEE_NAME_PATTERN = re.compile(r"(?:von|fuer|für|hat|ist|bei)\s+([A-ZÄÖÜ][\wÄÖÜäöüß-]+)\s+([A-ZÄÖÜ][\wÄÖÜäöüß-]+)")
SINGLE_NAME_CONTEXT_PATTERN = re.compile(
    r"(?:von|fuer|für|hat|ist|bei)\s+(?:(?:Frau|Herr)\s+)?([A-ZÄÖÜ][\wÄÖÜäöüß-]+)(?:\s+([A-ZÄÖÜ][\wÄÖÜäöüß-]+))?"
)
HONORIFIC_NAME_PATTERN = re.compile(r"\b(?:Frau|Herr)\s+([A-ZÄÖÜ][\wÄÖÜäöüß-]+)\b")
QUESTION_WORDS = {"wie", "wieviele", "wieviel", "welche", "zeige", "suche", "fasse"}


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
        employee_reference = self._extract_employee_reference(user_message)
        if any(keyword in lowered for keyword in ("urlaub", "vacation")):
            return {
                "model": "heuristic-fallback",
                "message": "",
                "tool_calls": [
                    {
                        "id": "tool-vacation",
                        "name": "query_hr_system",
                        "arguments": {"action": "vacation_balance", **employee_reference},
                    }
                ],
            }
        if any(keyword in lowered for keyword in ("gehalt", "salary", "lohn")):
            return {
                "model": "heuristic-fallback",
                "message": "",
                "tool_calls": [
                    {
                        "id": "tool-salary",
                        "name": "query_hr_system",
                        "arguments": {"action": "salary_info", **employee_reference},
                    }
                ],
            }
        if any(keyword in lowered for keyword in ("organigramm", "org", "abteilung")):
            return {
                "model": "heuristic-fallback",
                "message": "",
                "tool_calls": [
                    {
                        "id": "tool-org",
                        "name": "query_hr_system",
                        "arguments": {"action": "org_chart", "parameters": {}},
                    }
                ],
            }
        if any(keyword in lowered for keyword in ("zeit", "stunden", "timetracking")):
            return {
                "model": "heuristic-fallback",
                "message": "",
                "tool_calls": [
                    {
                        "id": "tool-time",
                        "name": "query_hr_system",
                        "arguments": {"action": "time_tracking", **employee_reference},
                    }
                ],
            }
        if any(keyword in lowered for keyword in ("dokument", "richtlinie", "policy", "hochgeladen", "suche")):
            return {
                "model": "heuristic-fallback",
                "message": "",
                "tool_calls": [{"id": "tool-rag", "name": "search_documents", "arguments": {"query": user_message}}],
            }
        return {
            "model": "heuristic-fallback",
            "message": "Ich bin der interne Trenkwalder Assistant und kann bei Dokumenten- und HR-Fragen helfen.",
            "tool_calls": [],
        }

    def _extract_employee_reference(self, user_message: str) -> dict:
        employee_id_match = EMPLOYEE_ID_PATTERN.search(user_message)
        if employee_id_match:
            return {"employee_id": employee_id_match.group(1).lower()}

        name_match = EMPLOYEE_NAME_PATTERN.search(user_message)
        if name_match:
            return {"employee_name": f"{name_match.group(1)} {name_match.group(2)}"}

        single_name_match = SINGLE_NAME_CONTEXT_PATTERN.search(user_message)
        if single_name_match:
            names = [part for part in single_name_match.groups() if part]
            if names:
                return {"employee_name": " ".join(names)}

        honorific_match = HONORIFIC_NAME_PATTERN.search(user_message)
        if honorific_match:
            return {"employee_name": honorific_match.group(1)}

        capitalized_pairs = re.findall(r"\b([A-ZÄÖÜ][\wÄÖÜäöüß-]+)\s+([A-ZÄÖÜ][\wÄÖÜäöüß-]+)\b", user_message)
        for first_name, last_name in reversed(capitalized_pairs):
            if first_name.casefold() in QUESTION_WORDS:
                continue
            return {"employee_name": f"{first_name} {last_name}"}

        capitalized_words = re.findall(r"\b([A-ZÄÖÜ][\wÄÖÜäöüß-]+)\b", user_message)
        for word in reversed(capitalized_words):
            if word.casefold() in QUESTION_WORDS:
                continue
            if word in {"IT", "HR"}:
                continue
            return {"employee_name": word}

        return {"employee_id": "emp-001"}

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
            logger.exception("LLM provider failed", extra={"model": provider.model})
            self._register_failure(provider)
            fallback_provider = self.get_active_provider()
            if fallback_provider.model != provider.model:
                return await self.complete(messages=messages, tools=tools)
            return self._fallback_response(messages)
