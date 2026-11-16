"""Live backend (spec 5.2): the Anthropic Messages API through the standard library only. The only module with the API host, the only one that receives
the API key value (at call time, in a local variable, never stored on the object).

Rules kept here: ``ProxyHandler({})`` (proxy environment variables are ignored), a redirect handler that raises on any 3xx, the default TLS context
(``SSL_CERT_FILE``, ``SSL_CERT_DIR``, ``SSLKEYLOGFILE`` and ``OPENSSL_CONF`` in the environment are REFUSED: the first two replace the trusted
certificate store, ``SSLKEYLOGFILE`` makes the TLS library write session secrets (the key header included) to a file, ``OPENSSL_CONF`` can load
engines or change trust. On Windows the default context also trusts the system certificate store, so a corporate or locally installed root
certificate is trusted: that is the operating system's trust decision, not ours), https only
(plain http only to a loopback name, for the test stub), the host compared twice (the constant and ``model.api_host``) before connecting, ONE
whole-call deadline (a worker thread is joined with the deadline, the body is read in chunks of at most 8 KiB with the socket timeout set to the time
left, and stops with ``over_cap`` at ``response_cap_bytes + 1``), no retry (one attempt per tier), and every exception mapped to the closed codes with
``except Exception``. ``http.client`` adds ``Accept-Encoding: identity`` itself (no compressed reply is asked for; urllib cannot drop the header).
The first action of ``send`` is ``budget.begin_send``. A response body is never stored or logged; the sanitised ``diag`` carries only status,
stop_reason, usage, elapsed time and, for a 4xx, the API's ``error.type`` word."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import ssl
import threading
import time
import urllib.error
import urllib.request
from dataclasses import replace
from urllib.parse import urlsplit

from . import budget, secret_store, strictjson
from . import settings as cfg
from .codes import ConfigError, Refused
from .model import ExtractRequest, ModelResult, clean_diag, failed
from .prompt_file import PROMPT_PATH
from .validators import RECORD_SCHEMA

API_HOST = "api.anthropic.com"
_SCHEME = "https"  # tests point these at a loopback stub; the shipped values are the real endpoint
_PORT = ""
_PATH = "/v1/messages"
_TOOL = "record_invoice"
_START, _END = "<<<INVOICE_START>>>", "<<<INVOICE_END>>>"
_CHUNK = 8192
_ERR_BODY_MAX = 4096  # at most this much of an HTTP error body is read, only to find error.type and the provider-limit signs
_RETRY_AFTER = re.compile(r"[0-9]{1,5}(\.[0-9]{1,3})?", re.ASCII)
_REQUEST_ID = re.compile(r"req_[A-Za-z0-9]{8,64}", re.ASCII)
_KEY_NAME = re.compile(r"[a-z_]{1,40}")
_LIMIT_MESSAGE = "You have reached your specified API usage limits"
_SPEND_CAP_CODE = "enforced_spend_limit_reached"
_GEO_PRICED = frozenset(
    {"us", "eu"}
)  # inference_geo values that the docs tie to a price change; every other value is recorded, not halted on
_GEO_WORD = re.compile(r"[a-z_]{1,30}", re.ASCII)
_IGNORED_BLOCKS = frozenset({"thinking", "redacted_thinking", "text"})
# allowed ``extra_body`` per model id: ``{}`` or exactly the one shape the provider documents for that model (docs-check 2026-11-05, Q2)
_EXTRA_ALLOWED: dict[str, tuple[dict, ...]] = {
    "claude-sonnet-5-5": ({}, {"thinking": {"type": "between_tools"}}),
    "claude-haiku-5-5": ({}, {"thinking": {"type": "disabled"}}),
}
_LOOPBACK = frozenset({"127.0.0.1", "localhost"})
_PROMPT = PROMPT_PATH  # alias of the one constant in ``prompt_file``


class _BlockedError(Exception):
    """A redirect was refused."""


class _OverCapError(Exception):
    """The response body passed ``response_cap_bytes``."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise _BlockedError("redirect refused")


def _url() -> str:
    return f"{_SCHEME}://{API_HOST}{(':' + _PORT) if _PORT else ''}{_PATH}"


def _hosts_ok(s: cfg.Settings) -> bool:
    parts = urlsplit(_url())
    scheme_ok = parts.scheme == "https" or (parts.scheme == "http" and parts.hostname in _LOOPBACK)
    return scheme_ok and parts.hostname == API_HOST == s.model.api_host


def _cert_env_clean() -> bool:
    """False when the environment could redirect trust or leak TLS secrets (constant names: the secret-scope scan allows no variable lookups)."""
    return not (
        os.environ.get("SSL_CERT_FILE")
        or os.environ.get("SSL_CERT_DIR")
        or os.environ.get("SSLKEYLOGFILE")
        or os.environ.get("OPENSSL_CONF")
    )


def validate_extra_body(model_id: str, extra: dict) -> None:
    """``model.extra_body`` for one tier. The allowlist is keyed by MODEL ID (not tier) and lives only here: Sonnet 5.5 accepts ``{}`` or
    ``{thinking: {type: between_tools}}`` (thinking off up front; ``disabled`` and ``enabled`` are HTTP 400 there); Haiku 5.5 accepts ``{}`` or
    ``{thinking: {type: disabled}}``; every other id accepts ``{}`` only. ``output_config``/``effort``, ``temperature``, ``top_p``, ``top_k``,
    ``inference_geo`` and any key off the list are refused. Raises ``ConfigError('bad_config')``."""
    if not isinstance(extra, dict) or not isinstance(model_id, str) or extra not in _EXTRA_ALLOWED.get(model_id, ({},)):
        raise ConfigError("bad_config", "model.extra_body holds a key or value that is not allowed for this model")


def parse_retry_after(v: str | None) -> int | None:
    """``Retry-After`` seconds: digits with an optional short decimal part only (an HTTP date, a sign or a long value is ignored), rounded up, capped
    at 3600. The docs say only "number of seconds": integer versus decimal is unverified, so both shapes are read."""
    if not isinstance(v, str):
        return None
    s = v.strip()
    if not _RETRY_AFTER.fullmatch(s):
        return None
    return min(math.ceil(float(s)), 3600)  # mut:ra_parse


def retry_after_of(e: BaseException) -> tuple[int | None, bool, bool]:
    """(seconds, header present, header unusable). Every ``Retry-After`` value is parsed; the MAX is used; if ANY value is unparseable the header is
    unusable (the caller then makes no second call: a present but unreadable wait is never read as "no wait asked")."""
    h = getattr(e, "headers", None)
    try:
        vals = [v for v in (h.get_all("retry-after") or []) if isinstance(v, str)] if h is not None and hasattr(h, "get_all") else []
    except Exception:  # noqa: BLE001
        vals = []
    if not vals:
        v = _header(e, "retry-after")
        vals = [v] if v is not None else []
    if not vals:
        return None, False, False
    parsed = [parse_retry_after(v) for v in vals]
    if any(p is None for p in parsed):
        return None, True, True
    return max(parsed), True, False  # mut:ra_max


def _header(e: BaseException, name: str) -> str | None:
    h = getattr(e, "headers", None)  # a mapping (http.client.HTTPMessage) or None
    v = h.get(name) if h is not None else None
    return v if isinstance(v, str) else None


def _request_id(v: str | None) -> str | None:
    return v if isinstance(v, str) and _REQUEST_ID.fullmatch(v) else None


def _set_timeout(resp, left: float) -> None:
    try:
        resp.fp.raw._sock.settimeout(left)  # noqa: SLF001 (no public way to bound each read by the time left)
    except AttributeError:
        pass  # the worker-thread join still bounds the whole call


def map_exception(e: BaseException) -> str:
    """Every network exception to a code of the closed set."""
    if isinstance(e, _OverCapError):
        return "over_cap"
    if isinstance(e, urllib.error.HTTPError):
        c = e.code
        e.close()  # the error body is never stored or logged
        return "http_429" if c == 429 else "http_5xx" if 500 <= c <= 599 else "http_4xx" if 400 <= c <= 499 else "net"
    if isinstance(e, ssl.SSLError):
        return "tls"
    if isinstance(e, TimeoutError):
        return "timeout"
    if isinstance(e, urllib.error.URLError):
        r = e.reason
        return "tls" if isinstance(r, ssl.SSLError) else "timeout" if isinstance(r, TimeoutError) else "net"
    return "net"


def _usage(d: dict) -> tuple[int, int]:
    u = d.get("usage") if isinstance(d.get("usage"), dict) else {}
    i, o = u.get("input_tokens"), u.get("output_tokens")
    return (i if isinstance(i, int) and not isinstance(i, bool) else 0, o if isinstance(o, int) and not isinstance(o, bool) else 0)


def _count(v) -> int | None:
    """A token count: None (absent or null) is 0; a plain non-negative int is itself; anything else is None (= not a measurement)."""
    if v is None:
        return 0
    return v if isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 10**9 else None


def _usage_extra(u: dict, out_tok: int, geo_permille: int) -> tuple[int, int, int, bool, str]:
    """Cache write, cache read, thinking tokens, the odd-usage flag and the sorted usage key names. ``thinking`` is a share of ``out_tok`` (never priced
    twice). A malformed count, thinking above output, a service tier or speed other than ``standard``, or an inference geography other than ``global``
    while no geo multiplier is configured, sets the flag: the guard then halts (``estimate_exceeded``), because the price effect is unknown."""
    odd = False
    cw, cr = _count(u.get("cache_creation_input_tokens")), _count(u.get("cache_read_input_tokens"))
    det = u.get("output_tokens_details")
    th = _count(det.get("thinking_tokens")) if isinstance(det, dict) else (0 if det is None else None)
    if cw is None or cr is None or th is None or th > out_tok:
        odd = True
    cache_n = (cw or 0) + (cr or 0)  # the request sends no cache_control, so any cache count is unpriced until B1 prices the classes
    if cache_n > 0:  # mut:cache_odd
        odd = True
    for k in ("service_tier", "speed"):
        if u.get(k) is not None and u.get(k) != "standard":  # mut:odd_tier
            odd = True
    if u.get("inference_geo") in _GEO_PRICED and geo_permille == 1000:  # mut:geo_priced
        odd = True  # a region that changes the price while no multiplier is configured; other values are only recorded (``inference_geo`` in diag)
    cc = u.get(
        "cache_creation"
    )  # the nested per-lifetime cache write counts: same rule as the flat fields (any non-zero or unreadable count is odd)
    if cc is not None and (not isinstance(cc, dict) or any(_count(v) is None or _count(v) > 0 for v in cc.values())):  # mut:nested_cache
        odd = True
    keys = ",".join(sorted(k for k in u if isinstance(k, str) and _KEY_NAME.fullmatch(k)))[:300]
    return (cw or 0, cr or 0, 0 if th is None or th > out_tok else th, odd, keys)


def parse_reply(raw: bytes, requested_model: str, status: int = 200, geo_permille: int = 1000) -> ModelResult:
    """HTTP 200 body to a ``ModelResult``. Order: (1) not JSON or not an object is ``bad_reply``; (2) usage is read BEFORE any verdict, so a truncated or
    refused reply settles at its real usage; (3) ``stop_reason`` ``max_tokens`` is the error ``max_tokens`` even with a complete-looking block;
    (4) any ``stop_reason`` other than ``tool_use`` (refusal, pause_turn, end_turn, ...) is ``bad_reply`` with the word kept; (5) ``thinking``,
    ``redacted_thinking`` and ``text`` blocks are ignored, any other block type or a ``tool_use`` of another name is ``bad_reply``, and exactly one
    ``tool_use`` named ``record_invoice`` with an object input is required."""
    try:
        d = strictjson.loads(raw)  # NaN, Infinity, duplicate keys, huge integers and lone surrogates are refused
    except ValueError:
        return failed("bad_reply", None, {"status": status})
    if not isinstance(d, dict):
        return failed("bad_reply", None, {"status": status})
    u = d.get("usage") if isinstance(d.get("usage"), dict) else {}
    i, o = _usage(d)
    cw, cr, th, odd, keys = _usage_extra(u, o, geo_permille)
    diag = {"status": status, "stop_reason": d.get("stop_reason"), "in_tok": i, "out_tok": o, "cache_write_tok": cw, "cache_read_tok": cr}
    diag.update(thinking_tok=th, usage_keys=keys)
    geo = u.get("inference_geo")
    if isinstance(geo, str) and _GEO_WORD.fullmatch(geo):
        diag["inference_geo"] = geo
    if odd:
        diag["usage_odd"] = 1
    mid = requested_model
    if (
        d.get("model") != requested_model
    ):  # another or unreadable model id: its price is unknown, so the guard settles at reserved and halts
        diag["model_mismatch"] = 1

    def verdict(code: str | None, fields: dict | None = None) -> ModelResult:
        return ModelResult(fields, mid, i, o, 0, code, clean_diag(diag), cw, cr, th)

    stop = d.get("stop_reason")
    if stop == "max_tokens":  # mut:max_tokens_first
        return verdict("max_tokens")
    if stop != "tool_use":  # mut:stop_check
        return verdict("bad_reply")
    content = d.get("content")
    if not isinstance(content, list):
        return verdict("bad_reply")
    tools = []
    for b in content:
        kind = b.get("type") if isinstance(b, dict) else None
        if kind in _IGNORED_BLOCKS:
            continue
        if kind != "tool_use" or b.get("name") != _TOOL:  # mut:other_block  # a server tool, another tool or an unknown block type
            return verdict("bad_reply")
        tools.append(b)
    if len(tools) != 1 or not isinstance(tools[0].get("input"), dict):  # mut:one_tool
        return verdict("bad_reply")
    return verdict(None, tools[0]["input"])


def _error_signs(status: int, raw: bytes, had_retry_after: bool) -> tuple[bool, str | None, str]:
    """From at most 4 KB of an HTTP 4xx/429 body: (is a provider spending limit, ``error.type`` word, sorted key names for the canary). Only closed
    facts leave this function, never the message. A body cut by the 4 KB cap is not parsed, so it is never a provider limit."""
    if len(raw) > _ERR_BODY_MAX:  # mut:err_cap
        return False, None, ""
    try:
        d = strictjson.loads(raw)
    except ValueError:
        return False, None, ""
    if not isinstance(d, dict):
        return False, None, ""
    err = d.get("error") if isinstance(d.get("error"), dict) else {}
    det_in_err = err.get("details") if isinstance(err.get("details"), dict) else {}
    det_top = d.get("details") if isinstance(d.get("details"), dict) else {}
    code = next((c for c in (det_in_err.get("error_code"), det_top.get("error_code"), err.get("error_code")) if isinstance(c, str)), None)
    etype = err.get("type") if isinstance(err.get("type"), str) else None
    msg = err.get("message")
    names = sorted({k for o in (d, err, det_in_err, det_top) for k in o if isinstance(k, str) and _KEY_NAME.fullmatch(k)})
    limit = (
        (status == 429 and code == _SPEND_CAP_CODE)
        or (status == 429 and etype == "rate_limit_error" and not had_retry_after and code is not None and "spend_limit" in code)
        or (status == 400 and isinstance(msg, str) and msg.startswith(_LIMIT_MESSAGE))
    )
    return limit, etype, ",".join(names)[:300]


class AnthropicBackend:
    live = True

    def __init__(self, s: cfg.Settings) -> None:
        if s.backend != "anthropic":  # a live backend under fake settings would run with the fake cap
            raise Refused("bad_config", "AnthropicBackend needs INTAKE_MODEL_BACKEND=anthropic")
        for tier in ("read", "fallback"):
            validate_extra_body(self._model_id_of(s, tier), self._extra_of(s, tier))
        self._s = s  # settings only: the key value is never held on the object
        self.last_refusal: str | None = None  # why the last preflight said no (a code word), for the diagnostics

    # -- port ----------------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _model_id_of(s: cfg.Settings, tier: str) -> str:
        if tier == "read":
            return s.model.tier_read
        if tier == "fallback":
            return s.model.tier_fallback
        raise ConfigError("bad_config", "unknown tier")

    @staticmethod
    def _extra_of(s: cfg.Settings, tier: str) -> dict:
        v = s.model.extra_body.get(tier) if isinstance(s.model.extra_body, dict) else None
        if not isinstance(v, dict):
            raise ConfigError("bad_config", "model.extra_body must hold one object per tier")
        return v

    def _model_id(self, tier: str) -> str:
        return self._model_id_of(self._s, tier)

    def preflight(self) -> str | None:
        """Consent file (a failure is ``gate``), then host and scheme, certificate environment, key lookup and shape, version: any other failure is
        ``budget``. Never reads the key value into this object and never touches the ledger."""
        self.last_refusal = None
        if not budget.consent_recorded(self._s):
            self.last_refusal = "owner_sentence_missing"
            return "gate"
        if not _hosts_ok(self._s) or not _cert_env_clean():
            self.last_refusal = "bad_config"
            return "budget"
        st = secret_store.status(secret_store.API_KEY, self._s.local)
        if st != "ok":
            self.last_refusal = st
            return "budget"
        try:
            cfg.require_anthropic_version(budget.current_prices(self._s))
        except Refused as e:
            self.last_refusal = e.code
            return "budget"
        return None

    def request_body(self, req: ExtractRequest) -> bytes:
        """The exact bytes that are priced and sent. ``model_text`` goes between the delimiters unchanged; the tier's ``model.extra_body`` (allowlisted
        for the model id, checked again here) is part of the body, so it is priced with it. DF5: ``tool_choice`` is ``auto`` (Sonnet 5.5 and Opus 5.5 answer
        a forced tool with HTTP 400) with parallel tool calls off; the prompt asks for exactly one ``record_invoice`` call and ``parse_reply`` requires it.
        No ``temperature``, ``top_p``, ``top_k``, ``fallbacks`` or beta header is ever sent."""
        m = self._s.model
        model_id = self._model_id(req.tier)
        extra = self._extra_of(self._s, req.tier)
        validate_extra_body(model_id, extra)
        tool: dict = {"name": _TOOL, "description": "Record the invoice values.", "input_schema": RECORD_SCHEMA}
        if m.strict_tool:  # mut:strict_flag
            tool["strict"] = True
        body = {
            "model": model_id,
            "max_tokens": m.max_tokens,
            "system": _PROMPT.read_text(encoding="utf-8"),
            "messages": [{"role": "user", "content": _START + req.model_text + _END}],
            "tools": [tool],
            "tool_choice": {"type": "auto", "disable_parallel_tool_use": True},  # mut:tool_choice
        }
        for k, v in extra.items():  # mut:extra_loop (keys are allowlisted per model id and can never replace a key above)
            if k not in body:
                body[k] = v
        return json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")

    def send(self, body: bytes, reservation: budget.Reservation) -> ModelResult:
        budget.begin_send(reservation, body)  # first action, always
        t0 = time.monotonic()
        model_id = self._model_id(reservation.tier)
        try:  # the reservation binds the body's hash; this binds its MEANING to the tier config (model and max_tokens)
            sent = strictjson.loads(body)
            psha = hashlib.sha256(str(sent.get("system", "")).encode("utf-8")).hexdigest()  # the prompt text IN the bytes that are sent
            if sent.get("model") != model_id or sent.get("max_tokens") != self._s.model.max_tokens:
                return failed("budget", model_id, {"refusal": "bad_config"})
        except (ValueError, AttributeError):
            return failed("budget", model_id, {"refusal": "bad_config"})
        try:
            key = secret_store.get(secret_store.API_KEY, local=self._s.local)
            version = cfg.require_anthropic_version(budget.current_prices(self._s))  # an empty version is refused before any network call
        except Refused:
            return failed("budget", model_id)
        if not _hosts_ok(self._s) or not _cert_env_clean():
            return failed("budget", model_id)
        box: dict = {}
        seen: dict = {}
        deadline = t0 + self._s.model.deadline_s

        def work() -> None:
            try:
                box["r"] = self._exchange(body, key, version, deadline, model_id, seen)
            except BaseException as e:  # noqa: BLE001 (mapped below; the thread must not die with a traceback)
                box["e"] = e

        t = threading.Thread(target=work, daemon=True)
        t.start()
        t.join(self._s.model.deadline_s)
        if t.is_alive():
            # a deadline AFTER an HTTP status line (a 4xx body trickling in) is not a plain timeout: the provider answered, so it is never retried
            status = seen.get("status", 0)  # read ONCE: the worker thread may still be running
            if status == 429:  # mut:late_429
                r = failed("http_429", model_id, {"status": 429, "odd_429": 1})  # still a 429 (not a hostile reply), but never retried
            elif 400 <= status <= 499:  # mut:late_status
                r = failed("http_4xx", model_id, {"status": status})
            else:
                r = failed("timeout", model_id)
        elif "e" in box:
            r = failed(map_exception(box["e"]), model_id)
        else:
            r = box["r"]
        elapsed = int((time.monotonic() - t0) * 1000)
        return replace(r, diag=clean_diag({**(r.diag or {}), "elapsed_ms": elapsed, "prompt_sha_sent": psha}))

    # -- the network call ----------------------------------------------------------------------------------------------------------------
    def _exchange(self, body: bytes, key: str, version: str, deadline: float, model_id: str, seen: dict) -> ModelResult:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), _NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context())
        )
        req = urllib.request.Request(  # noqa: S310 (scheme and host are pinned above)
            _url(),
            data=body,
            method="POST",
            headers={"x-api-key": key, "anthropic-version": version, "content-type": "application/json"},
        )
        left = deadline - time.monotonic()
        if left <= 0:
            raise TimeoutError
        cap = self._s.model.response_cap_bytes
        try:
            # B310 reasoned: https scheme and host pinned twice (constant and config), proxies off, redirects raise
            resp = opener.open(req, timeout=left)  # nosec B310
        except urllib.error.HTTPError as e:
            status = e.code
            ra_s, ra_present, ra_bad = retry_after_of(e)
            diag: dict = {
                "status": status,
                "retry_after_s": ra_s,
                "request_id": _request_id(_header(e, "request-id")),
            }
            if ra_bad:  # mut:ra_bad
                diag["retry_after_bad"] = 1
            seen["status"] = status  # the status line arrived: a later deadline is no longer a plain timeout (see ``send``)
            if (
                400 <= status <= 499
            ):  # only closed facts are kept (error.type word, key names, the limit verdict), never the body or the message
                try:
                    _set_timeout(e, max(deadline - time.monotonic(), 0.1))
                    limit, etype, names = _error_signs(status, e.read(_ERR_BODY_MAX + 1), ra_present)
                except Exception:  # noqa: BLE001 (diagnostics only; the mapped code stands)
                    limit, etype, names = False, None, ""
                diag.update(error_type=etype, err_keys=names)
                if status == 429 and etype != "rate_limit_error":  # mut:odd_429
                    diag["odd_429"] = 1  # a 429 we cannot read as an ordinary rate limit (cut, unparsed, unknown shape): never retried
                if limit:  # mut:limit_detect
                    return failed("provider_limit", model_id, {**diag, "refusal": "provider_limit"})
            return failed(map_exception(e), model_id, diag)
        try:
            buf = bytearray()
            while True:
                left = deadline - time.monotonic()
                if left <= 0:
                    raise TimeoutError
                _set_timeout(resp, left)
                chunk = resp.read1(_CHUNK)
                if not chunk:
                    break
                buf += chunk
                if len(buf) > cap:
                    raise _OverCapError
            status = resp.status
            rid = _request_id(resp.headers.get("request-id"))
        finally:
            resp.close()
        if status != 200:
            return failed("bad_reply", model_id, {"status": status, "request_id": rid})
        r = parse_reply(bytes(buf), model_id, status)
        return replace(r, diag=clean_diag({**(r.diag or {}), "request_id": rid})) if rid else r
