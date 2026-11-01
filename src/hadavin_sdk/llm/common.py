"""What every network llm kind shares: tool and document shaping, the reply and its cost, a stdlib JSON POST.

Rewritten from WARDEN ``providers.py`` (single-turn ``complete`` → multi-turn ``chat`` with tools and documents).
"""

from __future__ import annotations

import json
import re
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from itertools import islice
from typing import Any
from urllib.parse import urlsplit

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.llm.retry import with_retry
from hadavin_sdk.models import Reply, ToolCall

# The forced tool an `output_schema` becomes: its input schema IS the schema, so the API enforces the shape.
ANSWER_TOOL = "submit_answer"
_EMPTY = {"type": "object", "properties": {}}

# WARDEN register M15: an alias moves when the vendor ships a new model, so a qualified agent would silently
# change model. Only exact ids are accepted. Which names move is each vendor's convention, so each kind exports
# a `floating(model_id) -> bool` rule (lock-in audit 2026-10-31, row 2). Moving everywhere: `latest`, and the
# bare family or router names (`sonnet`, `opus`, `auto`, `default`) that routers such as LiteLLM and
# OpenRouter map to whatever they choose. A router prefix (`openai/`, `openrouter/`) is read past.
_LATEST = re.compile(r"(?i)(?:^|[-:/.])latest$")
_BARE = re.compile(r"(?i)^(?:sonnet|opus|haiku|fable|default|best|opusplan|auto|free)(?:\[1m\])?$")


def model_name(model_id: str) -> str:
    """The name after any router prefix: `openai/gpt-4o` -> `gpt-4o`."""
    return model_id.strip().rsplit("/", 1)[-1]


def floating_anywhere(model_id: str) -> bool:
    name = model_name(model_id)
    return not name or bool(_LATEST.search(model_id.strip()) or _BARE.match(name))


def pinned(
    routes: dict[str, Any], floating: Callable[[str], bool] = floating_anywhere
) -> dict[str, Any]:
    """The routes, if every model id names one model by its kind's rule; an alias that can move is refused."""
    for name, route in routes.items():
        if floating_anywhere(route.model_id) or floating(route.model_id.strip()):
            raise ConfigError(
                f"route {name}: model_id {route.model_id!r} is an alias that moves to new models; "
                "name an exact model id"
            )
    return routes


def estimate_tokens(text: str) -> int:
    """For a provider that reports no usage. Deliberately pessimistic (3 chars a token, never 0): a budget fed
    zeros never fires."""
    return max(1, len(text) // 3)


def tools_for(
    tools: list[dict[str, Any]] | None, output_schema: dict[str, Any] | None
) -> tuple[list[dict[str, Any]], str | None]:
    """``(tools as {name, description, input_schema}, the forced tool's name or None)``."""
    if output_schema is not None:
        answer = {
            "name": ANSWER_TOOL,
            "description": "Return the answer in this exact shape.",
            "input_schema": output_schema,
        }
        return [answer], ANSWER_TOOL
    return [
        {
            "name": t["name"],
            "description": t.get("description") or t["name"],
            "input_schema": t.get("input_schema") or _EMPTY,
        }
        for t in tools or []
    ], None


def turns(
    messages: list[dict[str, Any]], documents: list[bytes] | None
) -> list[tuple[str, list[str]]]:
    """``[(role, [text, ...])]``. Documents go first in the first user turn, as text (UTF-8, bad bytes
    replaced; PDF and image blocks are a trigger row)."""
    docs = [
        t for d in documents or [] if (t := d.decode("utf-8", "replace")).strip()
    ]  # APIs refuse blanks
    out: list[tuple[str, list[str]]] = []
    for m in messages:
        texts = [str(m["content"])]
        if docs and m["role"] == "user":
            texts, docs = docs + texts, []
        if out and out[-1][0] == m["role"]:  # providers want alternating roles: one turn holds both
            out[-1][1].extend(texts)
        else:
            out.append((m["role"], texts))
    return out


def schema_hint(system: str, output_schema: dict[str, Any]) -> str:
    """For a model the API cannot force to a tool: the schema goes in the system prompt instead."""
    return (
        f"{system}\n\nAnswer with one JSON object matching this JSON schema, and nothing else:\n"
        f"{json.dumps(output_schema, sort_keys=True)}"
    )


# Model output is untrusted. The stdlib parser recurses on nesting (a deep reply raises RecursionError, which is
# not a ValueError) and a huge reply costs time and memory, so both are bounded BEFORE parsing.
MAX_JSON_CHARS = 1_000_000
MAX_JSON_DEPTH = 64
_SCAN_BUDGET = 2_000_000  # characters all candidates of one json_in_text call may scan in total
_MAX_RESPONSE_BYTES = 16_000_000
_MAX_RESPONSE_CHARS = 16_000_000  # a vendor response (not a model's JSON answer)
_MAX_CANDIDATES = (
    50  # `{` positions tried in one text, so a reply full of braces cannot go quadratic
)


class ReplyUnparseable(ValueError):
    """A model reply too large or too deeply nested to parse safely (treated as an invalid reply)."""


def nesting_ok(
    text: str, start: int = 0, limit: int = MAX_JSON_DEPTH, budget: list[int] | None = None
) -> bool:
    """True if the JSON value starting at ``start`` nests no deeper than ``limit`` (string-aware, linear, stops
    as soon as the value closes or the limit is passed). ``budget`` ([characters left]) is shared across calls and
    spent as the scan reads; an empty budget answers False, so many candidates cannot add up to a CPU burn."""
    depth, in_str, esc = 0, False, False
    for ch in islice(text, start, None):
        if budget is not None:
            budget[0] -= 1
            if budget[0] < 0:
                return False
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "[{":
            depth += 1
            if depth > limit:
                return False
        elif ch in "]}":
            depth -= 1
            if depth <= 0:
                return True
    return True


def loads_bounded(text: str, max_chars: int = MAX_JSON_CHARS) -> Any:
    """``json.loads`` for model output: size and nesting bounded first; ReplyUnparseable (a ValueError) or
    JSONDecodeError for anything else, never RecursionError."""
    if len(text) > max_chars or not nesting_ok(text.lstrip()):
        raise ReplyUnparseable("reply too large or too deeply nested")
    try:
        return json.loads(text)
    except RecursionError as exc:  # belt and braces: the scan above should have refused it
        raise ReplyUnparseable("reply too deeply nested") from exc


def error_body(exc: BaseException) -> dict[str, Any] | None:
    """The JSON object an HTTP error carried: an SDK error's parsed ``body``, or a urllib ``HTTPError``'s body
    (read once, at most 4 KiB, size and nesting bounded). Never raises: a classifier must not fail inside the
    handler of the error it classifies."""
    try:
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            return body
        read = getattr(exc, "read", None)
        if callable(read):
            parsed = loads_bounded(read(4096).decode("utf-8", "replace"), 4096)
            return parsed if isinstance(parsed, dict) else None
    except Exception:  # noqa: BLE001 - unreadable body means "not a spend limit"
        return None
    return None


def json_in_text(text: str) -> dict[str, Any] | None:
    """The first JSON object in a text answer (bare, fenced or after a sentence), or None. Oversized or too
    deeply nested text yields None, never an exception."""
    if len(text) > MAX_JSON_CHARS:
        return None
    start = text.find("{")
    budget = [_SCAN_BUDGET]
    for _ in range(_MAX_CANDIDATES):
        if start == -1 or budget[0] < 0:
            return None
        # A `{` inside a JSON array is a list item, not the answer object.
        if not _inside_array(text, start) and nesting_ok(text, start, budget=budget):
            try:
                found, _ = json.JSONDecoder().raw_decode(text, start)
            except (ValueError, RecursionError):
                pass
            else:
                return found if isinstance(found, dict) else None
        # An object that opens like JSON but never closes is a cut-off answer: the objects nested in it are
        # fragments of it, so none of them is returned.
        if _JSON_OPEN.match(text, start):
            return None
        start = text.find("{", start + 1)
    return None


_JSON_OPEN = re.compile(r'\{\s*["}]')


def _inside_array(text: str, start: int) -> bool:
    """True when the `{` at `start` directly follows `[` or a `,` after a JSON value (`}`, `]` or a string):
    an item of an array. A comma after prose (`Sure, {...}`) does not count."""
    before = text[:start].rstrip()
    if before.endswith("["):
        return True
    return before.endswith(",") and before[:-1].rstrip()[-1:] in ("}", "]", '"')


# Why an answer ended, in each provider's words, folded into Reply.stop_reason (WARDEN providers.py B11, M7):
# `max_tokens` (cut off: incomplete, and asking again ends the same way) and `refusal` (declined or blocked).
_CUT_OFF = frozenset({"max_tokens", "model_context_window_exceeded", "length", "MAX_TOKENS"})
_REFUSED = frozenset(
    {
        "refusal",
        "content_filter",
        "content_filtered",
        "guardrail_intervened",
        "SAFETY",
        "RECITATION",
        "BLOCKLIST",
        "PROHIBITED_CONTENT",
        "SPII",
        "IMAGE_SAFETY",
    }
)


def stop_reason(raw: str | None, calls: list[ToolCall]) -> str:
    """``max_tokens`` | ``refusal`` | ``tool_use`` | ``end_turn``."""
    if raw in _CUT_OFF:
        return "max_tokens"
    if raw in _REFUSED:
        return "refusal"
    return "tool_use" if calls else "end_turn"


def reply(
    route: Any,
    *,
    text: str,
    calls: list[ToolCall],
    tokens: tuple[int | None, int | None],
    stop: str | None,
    started: float,
    sent: str,
) -> Reply:
    """The Reply, priced from the route. Missing usage is estimated from what was sent and received. A cut-off
    answer keeps its cost but loses its tool calls: their input may be incomplete."""
    tokens_in = tokens[0] or estimate_tokens(sent)
    tokens_out = tokens[1] or estimate_tokens(text + json.dumps([c.input for c in calls]))
    cost = (
        Decimal(tokens_in) * route.input_usd_per_mtok
        + Decimal(tokens_out) * route.output_usd_per_mtok
    ) / Decimal(1_000_000)
    stop = stop_reason(stop, calls)
    return Reply(
        text=text,
        tool_calls=[] if stop == "max_tokens" else calls,
        input_tokens=tokens_in,
        output_tokens=tokens_out,
        cost_usd=cost,
        model_id=route.model_id,
        stop_reason=stop,
        latency_ms=int((time.monotonic() - started) * 1000),
    )


@dataclass
class Answer:
    """One parsed provider answer, before pricing."""

    text: str
    calls: list[ToolCall]
    tokens: tuple[int | None, int | None]
    stop: str | None


class NetworkLLM:
    """The ``chat`` every network kind shares: the route, the tool list and bounded retries around one request
    and the parse of its answer, so a malformed answer is a ``ProviderError``, never a stray KeyError that
    would strand the run. A kind writes ``_chat``."""

    label = ""

    def __init__(
        self,
        routes: dict[str, Any],
        max_attempts: int,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.routes, self.max_attempts, self._sleep = routes, max_attempts, sleep

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        system: str,
        route: str,
        tools: list[dict[str, Any]] | None = None,
        documents: list[bytes] | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> Reply:
        r = self.routes[route]
        specs, forced = tools_for(tools, output_schema)
        return self._chat(r, system, turns(messages, documents), specs, forced, output_schema)

    def _chat(
        self,
        route: Any,
        system: str,
        turns: list[tuple[str, list[str]]],
        specs: list[dict[str, Any]],
        forced: str | None,
        output_schema: dict[str, Any] | None,
    ) -> Reply:
        raise NotImplementedError

    def _retry(self, call: Callable[[], Answer]) -> Answer:
        return with_retry(
            call,
            label=self.label,
            max_attempts=self.max_attempts,
            sleep=self._sleep,
            retryable=self.retryable,
            detail=self.detail,
            spend_limit=self.spend_limit,
            deadline_s=self.deadline_s,
        )

    # The kind's own SDK errors (llm/retry.py stays vendor-neutral): None means no opinion / no code.
    retryable: Callable[[BaseException], bool | None] | None = None
    detail: Callable[[BaseException], str] | None = None
    spend_limit: Callable[[BaseException], bool] | None = (
        None  # the kind's own "spend cap reached" test
    )
    deadline_s: float | None = (
        None  # overall wall clock for one call's attempts and sleeps (config)
    )


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect would carry the API key to a host nobody configured: refuse every redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)
# A loopback model is reached directly: an HTTP_PROXY would otherwise carry the plain-http prompt off the machine.
_LOCAL_OPENER = urllib.request.build_opener(_NoRedirect, urllib.request.ProxyHandler({}))
_LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})


def post_json(url: str, body: dict[str, Any], headers: dict[str, str], timeout_s: float) -> Any:
    """One POST; an HTTP error status raises ``urllib.error.HTTPError`` (its ``code`` drives the retry)."""
    req = urllib.request.Request(  # noqa: S310 - https or keyless loopback, checked in the settings
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    opener = _LOCAL_OPENER if urlsplit(url).hostname in _LOOPBACK else _OPENER
    with opener.open(req, timeout=timeout_s) as resp:  # nosec B310
        raw = resp.read(_MAX_RESPONSE_BYTES + 1)  # never the whole of an endless body
        if len(raw) > _MAX_RESPONSE_BYTES:
            raise ReplyUnparseable("response too large")
        try:
            return loads_bounded(raw.decode("utf-8"), _MAX_RESPONSE_CHARS)
        except UnicodeDecodeError as exc:
            raise ReplyUnparseable("response is not UTF-8") from exc
