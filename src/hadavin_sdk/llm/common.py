"""What every network llm kind shares: tool and document shaping, the reply and its cost, a stdlib JSON POST.

Rewritten from WARDEN ``providers.py`` (single-turn ``complete`` → multi-turn ``chat`` with tools and documents).
"""

from __future__ import annotations

import json
import re
import time
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal, localcontext
from typing import Any
from urllib.parse import urlsplit

from hadavin_sdk import defaults
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.guard import http as http_guard
from hadavin_sdk.llm.protocol import ProviderError
from hadavin_sdk.llm.retry import REFUSED_STATUSES, with_retry
from hadavin_sdk.models import Reply, ToolCall
from hadavin_sdk.store.protocol import MAX_SPEND_DECIMALS, clean_spend_amount

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
    """A display figure for ``Reply.input_tokens`` / ``output_tokens`` when the provider reported no usage (3
    chars a token, never 0). It is NOT a bound and never prices a call: a reply without usage has cost None."""
    return max(1, len(text) // 3)


_WORST_PLACES = Decimal(1).scaleb(-12)  # 12 decimal places, the most a spend amount may carry


def _json_bytes(value: Any) -> int:
    text = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return len(text.encode("utf-8", "surrogatepass"))


def worst_case_usd(
    route: Any,
    system: str,
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
    documents: list[bytes] | None = None,
    output_schema: dict[str, Any] | None = None,
    requests: int = 1,
) -> Decimal:
    """The most one ``chat`` call on `route` (a ``config.Route``) can cost, its retries included: what a meter
    books before the call. Input: the UTF-8 bytes of the system prompt, of the JSON text of the messages and of
    the tools, every document byte, the JSON text of the output schema TWICE (an adapter sends it as a forced tool
    and as a hint in the system prompt) and ``defaults.WORST_CASE_OVERHEAD_BYTES`` for adapter framing, at one
    token per byte (a token is never shorter than a byte). Output: ``route.max_tokens``. Times `requests` (the
    client's ``max_attempts``), rounded UP to 12 decimal places."""
    size = len(system.encode("utf-8", "surrogatepass")) + _json_bytes(messages)
    if tools is not None:
        size += _json_bytes(tools)
    size += sum(len(d.decode("utf-8", "replace").encode("utf-8")) for d in documents or [])
    if output_schema is not None:
        size += 2 * _json_bytes(output_schema)
    size += defaults.WORST_CASE_OVERHEAD_BYTES
    with localcontext(defaults.money_context()):
        one = (
            Decimal(size) * route.input_usd_per_mtok
            + Decimal(route.max_tokens) * route.output_usd_per_mtok
        ) / Decimal(1_000_000)
        return (one * requests).quantize(_WORST_PLACES, rounding=ROUND_CEILING)


def worst_case_for(
    routes: Mapping[str, Any], llm: object
) -> Callable[
    [
        str,
        str,
        list[dict[str, Any]],
        list[dict[str, Any]] | None,
        list[bytes] | None,
        dict[str, Any] | None,
    ],
    Decimal,
]:
    """The ``worst_case`` function a model gate is built with at one install site: `routes` are the configured
    routes (name -> ``config.Route``; none at all is a ValueError here), `llm` the client the gate wraps. The
    gate calls it with six positional arguments and the route as a NAME. Requests of one call: the client's
    ``max_attempts`` (1 for a client without one, or with one that is not a whole number of at least 1), times 2
    when an output schema is given (a forced answer can cost a second request round in the openai_compat kind).
    A name `routes` does not hold (only a test double: the config refuses an unknown route at load) is priced at
    the LARGEST worst case over all routes. If the price cannot be worked out, it raises
    ``limits.SpendRefused("bad_amount")``: no call is made, and no guess is ever returned."""
    if not routes:
        raise ValueError("worst_case_for needs at least one route")

    def worst_case(
        route: str,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        documents: list[bytes] | None,
        output_schema: dict[str, Any] | None,
    ) -> Decimal:
        try:
            attempts = getattr(llm, "max_attempts", 1)
            requests = attempts if type(attempts) is int and attempts >= 1 else 1
            if output_schema is not None:
                requests *= 2
            known = routes.get(route) if isinstance(route, str) else None
            return max(
                worst_case_usd(
                    r,
                    system,
                    messages,
                    tools=tools,
                    documents=documents,
                    output_schema=output_schema,
                    requests=requests,
                )
                for r in ([known] if known is not None else routes.values())
            )
        except Exception:  # noqa: BLE001 - no price, no call
            from hadavin_sdk.limits import (
                SpendRefused,
            )  # here: limits imports the registry, which imports llm

            raise SpendRefused("bad_amount") from None

    return worst_case


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
        out.append((m["role"], texts))
    return out


def schema_hint(system: str, output_schema: dict[str, Any]) -> str:
    """For a model the API cannot force to a tool: the schema goes in the system prompt instead."""
    return (
        f"{system}\n\nAnswer with one JSON object matching this JSON schema, and nothing else:\n"
        f"{json.dumps(output_schema, sort_keys=True)}"
    )


def json_in_text(text: str) -> dict[str, Any] | None:
    """The first JSON object in a text answer (bare, fenced or after a sentence), or None."""
    start = text.find("{")
    while start != -1:
        try:
            found, _ = json.JSONDecoder().raw_decode(text, start)
        except ValueError:
            start = text.find("{", start + 1)
            continue
        return found if isinstance(found, dict) else None
    return None


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


def _token_count(n: object) -> int:
    """A provider's token count: None or 0 means "not reported" (the caller estimates); anything but an int
    >= 0 is a ProviderError, never a negative cost. The call is then an unknown cost: its caller ends the run."""
    if n is None:
        return 0
    if type(n) is not int or n < 0:
        raise ProviderError(
            "bad_usage: the provider reported a token count that is not an integer >= 0"
        )
    return n


def round_up_cost(cost: Decimal) -> Decimal:
    """A priced cost as a valid spend amount: finite, >= 0, < 10**9, at most 12 decimal places (rounded UP, a
    cost is never rounded down). Anything else is a ProviderError("bad_amount"), so no bad cost is ever charged."""
    try:
        with localcontext(defaults.money_context()):
            if cost.is_finite() and cost >= 0:
                cost = cost.quantize(Decimal(1).scaleb(-MAX_SPEND_DECIMALS), rounding=ROUND_CEILING)
        return clean_spend_amount(cost)
    except (ArithmeticError, ValueError) as exc:
        raise ProviderError("bad_amount: the reply cost is not a valid amount") from exc


def reply(
    route: Any,
    *,
    text: str,
    calls: list[ToolCall],
    tokens: tuple[int | None, int | None],
    stop: str | None,
    started: float,
    sent: str,
    attempts: int = 1,
    prior_known: bool = True,
) -> Reply:
    """The Reply, priced from the route. ``cost_usd`` is None (the true cost is not known; the model gate then
    does not settle) when the provider reported no usage for the answer, or when an earlier attempt of the call
    may have been billed (``prior_known`` False: a timeout, reset or 5xx; an attempt refused before any
    response costs 0 and keeps it True). Token counts missing from the usage are estimated for display only.
    ``attempts`` is the number of requests the call took (audit). A cut-off answer keeps its cost but loses its
    tool calls: their input may be incomplete."""
    measured = tokens[0] is not None and tokens[1] is not None
    tokens_in = _token_count(tokens[0]) or estimate_tokens(sent)
    tokens_out = _token_count(tokens[1]) or estimate_tokens(
        text + json.dumps([c.input for c in calls])
    )
    cost: Decimal | None = None
    if measured and prior_known:
        try:
            with localcontext(defaults.money_context()):
                cost = (
                    Decimal(tokens_in) * route.input_usd_per_mtok
                    + Decimal(tokens_out) * route.output_usd_per_mtok
                ) / Decimal(1_000_000)
        except ArithmeticError as exc:  # no price is ever guessed: the call is a refusal, its cost forfeits at the worst case
            raise ProviderError("bad_amount: the reply price overflowed") from exc
        cost = round_up_cost(cost)
    stop = stop_reason(stop, calls)
    return Reply(
        text=text,
        tool_calls=[] if stop == "max_tokens" else calls,
        input_tokens=tokens_in,
        output_tokens=tokens_out,
        cost_usd=cost,
        attempts=attempts,
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
    # Filled by ``NetworkLLM._retry``: requests the call took, and whether every earlier attempt was known free.
    attempts: int = 1
    prior_known: bool = True


def priced(routes: dict[str, Any]) -> dict[str, Any]:
    """The routes, if every price is a plain Decimal that `config.Route` accepts (finite, not negative, at most the
    ceiling, at most 6 decimals: that one rule is reused, not copied) and is above 0. `Route.model_construct` and a
    hand-built route skip the config check, and a zero price makes every reply cost 0 so no spend cap could fire:
    a real (non-fake) client refuses them at build and again before each call. Names route and field, never the
    price."""
    from hadavin_sdk.config import (
        Route,
    )  # here: config imports the backends, which import this package

    for name, route in routes.items():
        for field in ("input_usd_per_mtok", "output_usd_per_mtok"):
            v = getattr(route, field, None)
            try:
                if type(v) is not Decimal:  # no float, str, bool or Decimal subclass
                    raise ValueError("a price must be a Decimal")
                Route._price(v)
                if v == 0:
                    raise ValueError("a price must be above 0")
            except (ValueError, ArithmeticError, AttributeError) as exc:
                raise ConfigError(f"route {name!r}: {field}: {exc}") from None
    return routes


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
        self.routes, self.max_attempts, self._sleep = priced(routes), max_attempts, sleep

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
        r = self.routes[route]  # read once: the object checked is the object priced
        priced({route: r})  # `llm.routes = ...` after build must not skip the check
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
        record: list[bool] = []
        got = with_retry(
            call,
            record=record,
            label=self.label,
            max_attempts=self.max_attempts,
            sleep=self._sleep,
            retryable=self.retryable,
            detail=self.detail,
            http_status=self.http_status,
            refused_statuses=self.refused_statuses,
        )
        got.attempts, got.prior_known = len(record) + 1, all(record)
        return got

    # The kind's own SDK errors (llm/retry.py stays vendor-neutral): None means no opinion / no code.
    retryable: Callable[[BaseException], bool | None] | None = None
    detail: Callable[[BaseException], str] | None = None
    # Where the kind's SDK keeps the HTTP status when it is not `status_code` / `code` (feeds only the mark
    # `refused_before_response`, llm/retry.py).
    http_status: Callable[[BaseException], int | None] | None = None
    # The statuses this kind counts as refused before any response (a kind behind routers or proxies narrows it).
    refused_statuses: frozenset[int] = REFUSED_STATUSES


# No redirects: one would carry the API key to a host nobody configured. A loopback model is reached directly
# (an HTTP_PROXY would otherwise carry the plain-http prompt off the machine).
_OPENER = http_guard.ENV_PROXY_OPENER
_LOCAL_OPENER = http_guard.LOCAL_OPENER
_LOOPBACK = http_guard.LOOPBACK


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
        return json.loads(resp.read())
