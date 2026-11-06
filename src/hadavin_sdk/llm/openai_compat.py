"""Any OpenAI-shaped chat API (OpenAI, Groq, OpenRouter, a local Ollama) over stdlib HTTP, no SDK.

A server that leaves usage out of its replies (some local servers do, Ollama among them) is refused with
``UsageMissing`` in v1: its reply is never estimated, so it cannot be used until it reports token counts.

Ports WARDEN ``OpenAICompatProvider`` (design 4.3). The key goes only to the configured ``base_url`` (https, or a
keyless loopback model; checked in the settings), never through a redirect, and is read on every call (a rotated
key is picked up). ``output_schema`` is forced through ``tool_choice``; a server that ignores it answers in text,
read as JSON, with one more request if it is not.

Neutral protocol: the OpenAI-shaped chat completions HTTP API, which OpenAI, Groq, OpenRouter and local servers (Ollama, vLLM) all speak.
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

from hadavin_sdk import defaults
from hadavin_sdk.llm.common import (
    Answer,
    NetworkLLM,
    json_in_text,
    model_name,
    pinned,
    post_json,
    reply,
    schema_hint,
    stop_reason,
)
from hadavin_sdk.llm.pricing import check_input_plausible, check_output_plausible
from hadavin_sdk.llm.protocol import ProviderError, UsageMissing, add_usage, build_usage
from hadavin_sdk.models import Reply, ToolCall

# OpenAI's own family names without a dated snapshot (`gpt-4o`, `o3`, `chatgpt-4o-latest`) move to new models;
# `gpt-4o-2024-08-06` does not. Other servers name models their own way and are left to `latest`.
_OPENAI_ALIAS = re.compile(r"^(?:gpt-[\w.-]+|o\d[\w.-]*|chatgpt-[\w.-]+)$")
_DATED = re.compile(r"-\d{4}-\d{2}-\d{2}$")
_LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})


def floating(model_id: str, base_url: str) -> bool:
    """Refused: an OpenAI alias with no dated snapshot; on a local server (Ollama), a name with no tag, which
    means `:latest`.

    ponytail: an Ollama tag (`llama3.1:8b`) can still be re-pulled to new weights; pin by digest when a client
    runs a local model in production."""
    name = model_name(model_id)  # `openai/gpt-4o` on a router is still the moving `gpt-4o`
    if _OPENAI_ALIAS.match(name) and not _DATED.search(name):
        return True
    return urlsplit(base_url).hostname in _LOOPBACK and ":" not in model_id


def make(settings: Any, deps: Any) -> OpenAICompatLLM:
    name = settings.api_key_secret_name
    return OpenAICompatLLM(
        settings.base_url,
        (lambda: deps.resolve(name)) if name else None,
        pinned(dict(deps.routes), lambda m: floating(m, settings.base_url)),
        settings.call_timeout_s,
        settings.max_attempts,
        cap_field="max_completion_tokens" if settings.max_completion_tokens else "max_tokens",
    )


def _call(tool_call: dict[str, Any]) -> ToolCall | None:
    """The function call, or None when its arguments are not a JSON object (never guessed at)."""
    fn = tool_call.get("function") or {}
    try:
        args = json.loads(fn.get("arguments") or "{}")
    except ValueError:
        return None
    return ToolCall(name=fn.get("name", ""), input=args) if isinstance(args, dict) else None


class OpenAICompatLLM(NetworkLLM):
    label = "openai_compat"
    REQUESTS_PER_CHAT = defaults.OPENAI_COMPAT_REQUESTS_PER_CHAT  # `common.request_bound` reads it

    def __init__(
        self,
        base_url: str,
        key: Callable[[], str] | None,
        routes: dict[str, Any],
        call_timeout_s: float,
        max_attempts: int,
        sleep: Callable[[float], None] = time.sleep,
        cap_field: str = "max_tokens",
    ) -> None:
        super().__init__(routes, max_attempts, sleep)
        self.url = base_url.rstrip("/") + "/chat/completions"
        self._key, self.timeout_s, self.cap_field = key, call_timeout_s, cap_field

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._key()}"} if self._key else {}

    def _chat(self, route, system, turns, specs, forced, output_schema) -> Reply:
        if forced:  # also in the prompt, for a server that ignores tool_choice
            system = schema_hint(system, output_schema)
        body: dict[str, Any] = {
            "model": route.model_id,
            self.cap_field: route.max_tokens,
            "messages": ([{"role": "system", "content": system}] if system else [])
            + [{"role": role, "content": "\n\n".join(texts)} for role, texts in turns],
        }
        if specs:
            body["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": s["name"],
                        "description": s["description"],
                        "parameters": s["input_schema"],
                    },
                }
                for s in specs
            ]
        if forced:
            body["tool_choice"] = {"type": "function", "function": {"name": forced}}
        started, used = time.monotonic(), None
        for n in range(
            self.REQUESTS_PER_CHAT
        ):  # the forced answer missing: one more request (design 4.3)
            try:
                got = self._retry(
                    lambda: self._parse(post_json(self.url, body, self._headers(), self.timeout_s))
                )
            except UsageMissing:
                raise  # request 2 answered without usage stays visible as itself (its cause is not wrapped)
            except ProviderError as exc:
                if n == 0:
                    raise  # a failed first request is unchanged: the original error, free of charge
                # Request 1 was answered and billed; its counts would be lost. `UsageMissing` already means
                # "book the reserved amount or the worst case" to every caller. The real error stays as the cause.
                raise UsageMissing("absent", "usage") from exc
            # Each request is checked on its own before the sum hides it: a zero on one request that holds text
            # or a tool call, or a zero input on a priced route, is refused here (PL57). Two statements.
            check_input_plausible(got.usage, route)
            check_output_plausible(got.usage, got.text, got.calls)
            used = got.usage if used is None else add_usage(used, got.usage)
            # Done when answered, or when asking again would end the same way (cut off, refused).
            done = stop_reason(got.stop, got.calls) in ("max_tokens", "refusal")
            if done or not forced or any(c.name == forced for c in got.calls):
                break
            if (found := json_in_text(got.text)) is not None:
                got.calls = [ToolCall(name=forced, input=found)]
                break
        # A server that omits usage is refused inside `_parse` (`UsageMissing`); nothing is estimated.
        got.usage = used
        return reply(route, **vars(got), started=started)

    @staticmethod
    def _parse(resp: dict[str, Any]) -> Answer:
        choice = resp["choices"][0]
        message = choice.get("message") or {}
        raw = resp.get("usage")
        if not isinstance(raw, dict):
            raise UsageMissing("absent", "usage")
        return Answer(
            text=message.get("content") or "",
            calls=[c for c in map(_call, message.get("tool_calls") or []) if c is not None],
            usage=build_usage(raw.get("prompt_tokens"), raw.get("completion_tokens")),
            stop=choice.get("finish_reason"),
        )
