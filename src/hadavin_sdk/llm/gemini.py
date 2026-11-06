"""Google Gemini (AI Studio API key) over stdlib HTTP, no SDK. Ports WARDEN ``GeminiProvider`` (design 4.3).

The base URL is fixed here, never read from the environment: the Google SDK reads GOOGLE_GEMINI_BASE_URL and
the Vertex switches itself, and the key went wherever they named (WARDEN reviews, 2026-09-30). The key travels in
the ``x-goog-api-key`` header, never the URL, and is read on every call (a rotated key is picked up).
``output_schema`` is forced through function calling mode ``ANY``.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any
from urllib.parse import quote

from hadavin_sdk.llm.common import Answer, NetworkLLM, pinned, post_json, reply
from hadavin_sdk.llm.protocol import UsageMissing, build_usage, checked_count
from hadavin_sdk.models import Reply, ToolCall, Usage

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


def floating(model_id: str) -> bool:
    """Refused: `*-latest` (generic) and a name with no version at all (`gemini-pro`, `gemini-flash`).

    ponytail: a versioned name without a stable suffix (`gemini-2.0-flash` vs `gemini-2.0-flash-001`) may still
    be an auto-updated alias; check Google's versioning page per model at P9 and tighten when one moves."""
    return not any(c.isdigit() for c in model_id)


def make(settings: Any, deps: Any) -> GeminiLLM:
    return GeminiLLM(
        lambda: deps.resolve(settings.api_key_secret_name),
        pinned(dict(deps.routes), floating),
        settings.call_timeout_s,
        settings.max_attempts,
    )


class GeminiLLM(NetworkLLM):
    label = "gemini"
    REQUESTS_PER_CHAT = 1  # one request a chat; `common.request_bound` reads it

    def __init__(
        self,
        key: Callable[[], str],
        routes: dict[str, Any],
        call_timeout_s: float,
        max_attempts: int,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        super().__init__(routes, max_attempts, sleep)
        self._key, self.timeout_s, self.base_url = key, call_timeout_s, BASE_URL

    def _chat(self, route, system, turns, specs, forced, output_schema) -> Reply:
        body: dict[str, Any] = {
            "contents": [
                {
                    "role": "model" if role == "assistant" else "user",
                    "parts": [{"text": t} for t in texts],
                }
                for role, texts in turns
            ],
            "generationConfig": {"maxOutputTokens": route.max_tokens},
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        if specs:
            body["tools"] = [
                {
                    "functionDeclarations": [
                        {
                            "name": s["name"],
                            "description": s["description"],
                            "parametersJsonSchema": s["input_schema"],
                        }
                        for s in specs
                    ]
                }
            ]
        if forced:
            body["toolConfig"] = {
                "functionCallingConfig": {"mode": "ANY", "allowedFunctionNames": [forced]}
            }
        url = f"{self.base_url}/models/{quote(route.model_id, safe='')}:generateContent"
        started = time.monotonic()
        got = self._retry(
            lambda: self._parse(
                post_json(url, body, {"x-goog-api-key": self._key()}, self.timeout_s)
            )
        )
        return reply(route, **vars(got), started=started)

    @staticmethod
    def _usage(raw: dict[str, Any], *, blocked: bool) -> Usage:
        """Input is `promptTokenCount`. Output is the candidates plus the thoughts (thinking is billed as output
        and `candidatesTokenCount` leaves it out), or, when `totalTokenCount` is present, the larger of that and
        `total - prompt` (PL58: an output the provider billed outside the two fields is still counted). A missing
        `candidatesTokenCount` is 0 only for a blocked prompt (no candidates plus a `blockReason`); anywhere else
        a candidate may have been billed for what it wrote, so it is refused."""
        prompt = checked_count(raw.get("promptTokenCount"), "input_tokens")
        cand_raw = raw.get("candidatesTokenCount")
        cand = 0 if cand_raw is None and blocked else checked_count(cand_raw, "output_tokens")
        thoughts_raw = raw.get("thoughtsTokenCount")
        thoughts = 0 if thoughts_raw is None else checked_count(thoughts_raw, "output_tokens")
        out = cand + thoughts
        if raw.get("totalTokenCount") is not None:
            # The total counts the prompt too, so it may pass the per-class cap legitimately: only its form is
            # checked here, and the output derived from it goes through `build_usage` and its cap below.
            total = raw["totalTokenCount"]
            if type(total) is not int or total < 0:
                raise UsageMissing("invalid", "output_tokens")
            out = max(out, total - prompt)
        return build_usage(prompt, out)

    @staticmethod
    def _parse(resp: dict[str, Any]) -> Answer:
        raw = resp.get("usageMetadata")
        if not isinstance(raw, dict):
            raise UsageMissing("absent", "usage")
        if not resp.get("candidates"):
            if (resp.get("promptFeedback") or {}).get(
                "blockReason"
            ):  # the prompt itself was blocked
                return Answer(
                    text="",
                    calls=[],
                    usage=GeminiLLM._usage(raw, blocked=True),
                    stop="SAFETY",
                )
            raise ValueError("gemini answered with no candidates")  # a ProviderError, never a guess
        candidate = resp["candidates"][0]
        if (
            candidate.get("finishReason") == "MALFORMED_FUNCTION_CALL"
        ):  # the model failed, it did not decide
            raise ValueError("gemini answered with a malformed function call")
        parts = (candidate.get("content") or {}).get("parts") or []
        return Answer(
            # Thought parts are the model's working, never its answer.
            text="".join(p.get("text", "") for p in parts if not p.get("thought")),
            calls=[
                ToolCall(name=p["functionCall"]["name"], input=p["functionCall"].get("args") or {})
                for p in parts
                if "functionCall" in p
            ],
            usage=GeminiLLM._usage(raw, blocked=False),
            stop=candidate.get("finishReason"),
        )
