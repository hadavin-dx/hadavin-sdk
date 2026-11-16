"""The model port, the guard and the backend factory (spec 5.1, 5.4, 5.5).

``GuardedModel.call(req)`` is the only object entry that checks the data gate, reserves, sends and settles one tier call; both backends sit behind it.
Order inside ``call`` (a refusal before ``reserve`` costs nothing): data gate -> ``ModelPort.preflight()`` (key, host, consent) -> prices and the
minimum-cap check (re-evaluated on EVERY call) -> body -> ``reserve`` -> ``send`` -> ``settle`` (always, in ``finally``) -> circuit-breaker bookkeeping.
The gate is read at the entry of EVERY tier call, so a fallback call after a STOP is refused, and it is not re-checked inside ``send``.

Outcome and fallback tables (DF5, one model per step): the fallback tier is called ONLY after ``FALLBACK_CODES``, the five transport codes (and the
caller waits first, ``extract._wait_s``). A reply that fails parsing, validation or grounding, and every other code (``NO_FALLBACK_CODES``), goes to a person.

``diag['model_mismatch']`` is a spend-guard signal only: the reply is still returned, so the review page and the evaluation report must NOT treat it as
authoritative (WP6 and WP8 do not show or count it). ``ModelResult.diag`` is a SANITISED diagnostic side channel for the live calibration (status, stop_reason, usage, elapsed time, and for a 4xx only the
API's ``error.type`` word): never a body, a message or a key. ``format_diag`` renders it as one line."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, replace
from typing import Protocol

from . import budget as budget_mod
from . import settings as cfg
from .codes import CODES, MODEL_ERRORS, ConfigError, Refused

FALLBACK_CODES = frozenset({"timeout", "net", "tls", "http_429", "http_5xx"})
NO_FALLBACK_CODES = (
    MODEL_ERRORS - FALLBACK_CODES
)  # gate, budget, halted, http_4xx, body_unsafe, over_cap, max_tokens, bad_reply, provider_limit: one source of truth
_WORD = re.compile(r"[a-z][a-z_]{0,63}")
_REQUEST_ID = re.compile(r"req_[A-Za-z0-9]{8,64}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_KEY_NAMES = re.compile(r"[a-z_,]{1,300}")


@dataclass(frozen=True)
class ExtractRequest:
    doc_sha: str  # sha256 of the RAW bytes (source_sha256)
    tier: str  # "read" or "fallback" (never a model id)
    model_text: str = field(repr=False)  # the only text placed between the delimiters and sent (the masked document text)


@dataclass(frozen=True)
class ModelResult:
    fields: dict | None
    model_id: str | None
    in_tok: int
    out_tok: int
    cost_micro: int
    error: str | None
    diag: dict | None = None  # sanitised calibration facts (see ``clean_diag``); never a body
    cache_write_tok: int = 0  # DF5: usage classes beyond input and output; ``thinking_tok`` is a share of ``out_tok`` (never priced twice)
    cache_read_tok: int = 0
    thinking_tok: int = 0

    def __post_init__(self) -> None:
        if self.error is not None and self.error not in MODEL_ERRORS:
            raise ValueError("error must be one code of the closed set")


def clean_diag(d: dict | None) -> dict | None:
    """Keep only the sanitised keys: ``status`` int, ``stop_reason`` and ``error_type`` words (lower-case letters and underscore), ``in_tok``,
    ``out_tok`` and ``elapsed_ms`` ints. Anything else (a body, a message) is dropped."""
    if not isinstance(d, dict):
        return None
    out: dict = {}
    for k in (
        "status",
        "in_tok",
        "out_tok",
        "elapsed_ms",
        "model_mismatch",
        "cache_write_tok",
        "cache_read_tok",
        "thinking_tok",
        "usage_odd",
        "retry_after_bad",
        "odd_429",
    ):
        v = d.get(k)
        if isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 10**9:
            out[k] = v
    v = d.get("retry_after_s")  # seconds the provider asked us to wait (capped at one hour by the parser)
    if isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 3600:
        out["retry_after_s"] = v
    v = d.get("prompt_sha_sent")  # sha256 of the prompt text inside the bytes that were sent
    if isinstance(v, str) and _SHA256.fullmatch(v):
        out["prompt_sha_sent"] = v
    v = d.get("inference_geo")  # recorded for the canary, never acted on here
    if isinstance(v, str) and _WORD.fullmatch(v):
        out["inference_geo"] = v
    v = d.get("request_id")
    if isinstance(v, str) and _REQUEST_ID.fullmatch(v):
        out["request_id"] = v
    for k in ("usage_keys", "err_keys"):  # sorted key NAMES of the usage object / error body, for the live canary (never values)
        v = d.get(k)
        if isinstance(v, str) and _KEY_NAMES.fullmatch(v):
            out[k] = v
    for k in ("stop_reason", "error_type"):
        v = d.get(k)
        if isinstance(v, str) and _WORD.fullmatch(v):
            out[k] = v
    if d.get("refusal") in CODES:  # which guard rule said no (a fixed code word, never free text)
        out["refusal"] = d["refusal"]
    return out or None


def format_diag(r: ModelResult) -> str:
    """One line for ``intake extract --calibrate``: the error code, model id and the sanitised diagnostics. Never a body, a header or a key."""
    d = clean_diag(r.diag) or {}
    parts = [f"error={r.error or 'none'}", f"model_id={r.model_id if r.model_id and _safe_id(r.model_id) else 'n/a'}"]
    parts += [
        f"{k}={d[k]}"
        for k in ("status", "stop_reason", "error_type", "refusal", "in_tok", "out_tok", "elapsed_ms", "model_mismatch")
        if k in d
    ]
    return " ".join(parts)


def _safe_id(v: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9._:-]{1,100}", v))


def failed(code: str, model_id: str | None = None, diag: dict | None = None) -> ModelResult:
    return ModelResult(None, model_id, 0, 0, 0, code, clean_diag(diag))


def fallback_allowed(error: str | None) -> bool:
    """True for the five transport codes after which the fallback tier is called (a reply failing validation or grounding goes to a person)."""
    return error in FALLBACK_CODES


class BodyCheck(Protocol):
    """What the guard needs to prove that the bytes about to be sent belong to the document the data gate hashed (spec 5.4). ``mask.BodyCheck`` is the
    real one; tests use a stand-in check under ``tests/``. ``last_code`` is the self-check code of the last refusal (design B4)."""

    document_text: str
    source_sha256: str
    key: bytes
    last_code: str | None

    def refuse(self, code: str) -> None: ...

    def __call__(self, body: bytes) -> str | None: ...  # None = the body is what it must be


class ModelPort(Protocol):
    live: bool  # True when the backend reaches a real provider: the guard then applies the owner sentence and the provider limit

    def preflight(self) -> str | None: ...  # an error code of the closed set, or None

    def request_body(self, req: ExtractRequest) -> bytes: ...

    def send(
        self, body: bytes, reservation: budget_mod.Reservation
    ) -> ModelResult: ...  # first action: budget.begin_send(reservation, body)


# ---- data gate (spec 5.4) -------------------------------------------------------------------------------------------------------------------
def listed_hashes(s: cfg.Settings) -> frozenset[str]:
    """The hashes on the made-up list, re-read on every call through the ONE loader (``settings.load_hash_list``, also used by ``check``): lowercase
    64-hex lines only. A missing, empty, whitespace-only or junk-only file is the empty set."""
    return cfg.load_hash_list(s.intake_home / "synthetic_hashes.txt")


def gate_check(s: cfg.Settings, send_text: str) -> None:
    """The data gate: sha256 of ``send_text`` (UTF-8, lowercase hex) must be a line of the list. An empty list refuses everything
    (``real_file_refused``); a hash not on a non-empty list, or a text that cannot be encoded (lone surrogate), is ``not_on_list``. A refusal costs nothing."""
    hashes = listed_hashes(s)
    if not hashes:
        raise Refused("real_file_refused", "the made-up list is empty or missing")
    try:
        digest = hashlib.sha256(send_text.encode("utf-8")).hexdigest()
    except (UnicodeEncodeError, AttributeError):
        raise Refused("not_on_list", "the text cannot be hashed") from None
    if digest not in hashes:
        raise Refused("not_on_list", "the text is not on the made-up list")


def _run_check(fn, *args):
    """``fn(*args)``; anything it raises (except ``ConfigError``, which must reach the caller) becomes ``body_unsafe``: a check that cannot run is a
    check that failed. It runs before ``reserve``, so this handler can never swallow a ``settle_failed``."""
    try:
        return fn(*args)
    except ConfigError:
        raise
    except Exception:
        return "body_unsafe"


# ---- the guard ------------------------------------------------------------------------------------------------------------------------------
PROSE_STOPS = frozenset(
    {"end_turn", "refusal", "pause_turn"}
)  # stop reasons of a well-formed reply that did not call the tool (not a breaker input)


class GuardedModel:
    def __init__(self, backend: ModelPort, budget, settings: cfg.Settings) -> None:
        self.backend = backend
        self.budget = budget
        self.settings = settings
        self.live = bool(getattr(backend, "live", False))
        if self.live and settings.backend == "fake":  # a live backend must never run under the fake cap
            raise Refused("bad_config", "a live backend needs INTAKE_MODEL_BACKEND=anthropic")
        cfg.require_safe_backend(settings)  # the fake backend only in a temporary folder, whoever built the guard
        # startup check once, here: refuses ledger_inconsistent and cap_too_small_for_worst_case; a missing owner sentence, provider limit,
        # prices or ledger defers (every call then refuses with that code and returns the error 'budget'; the minimum check also runs on every call)
        self.deferred = budget.startup_check(backend)

    def call(self, req: ExtractRequest, *, body_check: BodyCheck) -> ModelResult:
        """One tier call. Every refusal before ``reserve`` returns an error code (never raises). ``ConfigError('settle_failed')`` is the ONE exception that
        leaves this method: the ledger could not record a settlement, the process must stop (exit 3) and must not make another call.
        ``body_check`` is required: the request must belong to its document (``doc_sha``), the gate hashes ITS document text, and the exact bytes pass
        ``body_check(body)`` before ``reserve``; any failure is ``body_unsafe`` (cost 0, no reservation, no fallback)."""
        s = self.settings
        if req.doc_sha != body_check.source_sha256:
            _run_check(body_check.refuse, "doc_sha_mismatch")
            return failed("body_unsafe")
        try:
            gate_check(s, body_check.document_text)
        except Refused as e:
            return failed("gate", diag={"refusal": e.code})
        if req.tier not in budget_mod.TIERS:
            return failed("budget")
        try:
            pre = self.backend.preflight()
        except Exception:
            pre = "budget"
        if pre is not None:
            return failed(pre if pre in ("gate", "budget") else "budget", diag={"refusal": getattr(self.backend, "last_refusal", None)})
        try:
            self.budget.current_prices()
            self.budget.minimum_check(self.backend)  # cap >= 18 x worst case, on every call
            body = self.backend.request_body(req)
            if _run_check(body_check, body) is not None:
                return failed("body_unsafe")
            res = self.budget.reserve(req.doc_sha, req.tier, body, self.live)
        except ConfigError:
            raise
        except Refused as e:
            return failed("halted" if e.code == "budget_halted" else "budget", diag={"refusal": e.code})
        except Exception:
            return failed("budget")
        result: ModelResult | None = None
        usage = None
        halt_reason = None
        settle_error = None
        stop = None
        model_id = None
        try:
            try:
                result = self.backend.send(body, res)
                if not isinstance(result, ModelResult):
                    result = failed("bad_reply")
                elif result.error == "body_unsafe":  # a guard decision: a backend cannot make it after ``reserve``
                    result = failed("bad_reply", result.model_id, result.diag)
                elif result.error is None and not isinstance(result.fields, dict):
                    result = failed("bad_reply", result.model_id, result.diag)
                tokens = (result.in_tok, result.out_tok)
                if result.error in (None, "max_tokens", "bad_reply") and budget_mod.valid_usage(tokens) is not None:  # mut:usage_guard
                    usage = tokens  # the provider billed these tokens even for a cut-off or refused reply: settle at the actual usage
                odd = bool((result.diag or {}).get("usage_odd"))  # a service tier, speed or region that changes the price
                mismatch = bool((result.diag or {}).get("model_mismatch"))  # the provider answered as another model
                if odd:  # mut:odd_first
                    usage = None  # unknown price (outranks model_mismatch, Z3): settle at reserved and halt
                    halt_reason = "estimate_exceeded"
                elif mismatch:
                    usage, halt_reason = None, "model_mismatch"  # unknown price: settle at reserved and halt
                stop = (result.diag or {}).get("stop_reason")
                settle_error = result.error
                if halt_reason is None and result.error in ("bad_reply", "max_tokens"):
                    if result.error == "bad_reply" and usage is not None and stop in PROSE_STOPS:  # mut:prose_not_breaker
                        settle_error = (
                            budget_mod.STOP_PROSE
                        )  # a well-formed reply that did not call the tool: its own counter, not the breaker
                    elif result.error == "max_tokens" or stop:  # mut:hostile_class
                        settle_error = budget_mod.HOSTILE_SHAPE  # max_tokens, wrong-shape tool call, unlisted stop reason: its own counter
                if result.error == "provider_limit":  # the provider's own spending limit: settle at reserved, halt, stop the scan
                    usage, halt_reason = None, "provider_limit"
                model_id = result.model_id
            except Refused:
                result = failed("budget")
            except Exception:
                result = failed("net")
        finally:
            try:
                cost = self.budget.settle(
                    res, usage, model_id, settle_error or (result.error if result else None), self.live, halt_reason, stop
                )
            except Refused:  # already settled elsewhere (an orphan sweep): it was counted at its reserved amount, so the call still returns
                cost = res.micro
        return replace(result, cost_micro=cost)


# ---- factory --------------------------------------------------------------------------------------------------------------------------------
def backend_for(s: cfg.Settings) -> ModelPort:
    """The backend named by ``INTAKE_MODEL_BACKEND`` (no folder check; ``check`` uses this)."""
    if s.backend == "fake":
        from .model_fake import FakeBackend

        return FakeBackend(s)
    from .model_anthropic import AnthropicBackend  # lazy: avoids a circular import and keeps the vendor module out of the fake path

    return AnthropicBackend(s)


def make_backend(s: cfg.Settings) -> ModelPort:
    """``serve`` and ``extract`` use this: the fake backend is refused on a ``HADAVIN_LOCAL`` outside the temporary folder (``fake_on_real_folder``)."""
    cfg.require_safe_backend(s)
    return backend_for(s)


def build_guarded(s: cfg.Settings | None = None) -> GuardedModel:
    s = s or cfg.load()
    return GuardedModel(make_backend(s), budget_mod.Budget(s), s)
