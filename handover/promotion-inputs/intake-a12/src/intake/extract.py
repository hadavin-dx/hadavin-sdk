"""``extract(name, data, model, settings) -> ProcessedDoc`` and ``extract_parsed(parsed, model, settings, tiers=TIERS)``: reader + model + validators +
grounding, no queue (the model objects are WP1's ``GuardedModel``) (spec 12; call tree 6.3 and 5.1). The scan reads a file once and passes the ``ParsedDoc`` to ``extract_parsed`` (errata 5 and 32);
the WP2b calibration calls ``extract_parsed(..., tiers=("read",))`` and reads ``ProcessedDoc.calls`` (one entry per model call), or calls
``model.call(ExtractRequest(...), body_check=...)`` directly.

Call tree per document (DF5, one model per step): ONE read by the read tier. A second call only after a transport error (``FALLBACK_CODES`` = timeout,
net, tls, http_429, http_5xx), to the fallback tier (the same model, or one listed as stronger), after ``_wait_s`` seconds (none for timeout, net, tls; the
``Retry-After`` time or ``fallback_wait_s`` for 429 and 5xx; a ``Retry-After`` above ``fallback_wait_max_s`` means no second call). A reply that fails
parsing, validation or grounding, and the codes ``over_cap``, ``max_tokens``, ``bad_reply``, ``provider_limit``, ``gate``, ``budget``, ``halted``, ``http_4xx``
and ``body_unsafe`` make NO second call. Final outcome:
* some tier returned a valid, grounded record: ``fields`` set, ``failing_fields`` empty, ``error`` None;
* else some tier returned a reply that failed validation or grounding: ``fields`` None, ``failing_fields`` = the failing names of the LAST returned
  reply (the pipeline makes X10; no other check runs), ``error`` None;
* else no reply from any tier: ``fields`` None, ``failing_fields`` empty, ``error`` = the last error code (the pipeline makes L02).
A reader-flagged file (X18, X28) makes no model call (its text, kept for the human page for X28, is never sent): ``parsed.flag`` is set and everything
else is empty. ``cost_micro`` is the SUM over both calls (what the guard settled). A model object that raises counts as the error ``budget`` (no
fallback call). ``fields`` is a copy: the caller may not alter what the model object holds."""

from __future__ import annotations

import copy
import hashlib
import os
import threading
import time
from dataclasses import dataclass, field

from . import budget, ground, mask, prompt_file, reader, trace_vocab, validators, workqueue
from .codes import SCAN_STOP_CODES, ConfigError, Refused
from .model import FALLBACK_CODES, PROSE_STOPS, ExtractRequest, ModelResult, clean_diag, gate_check
from .reader import ParsedDoc
from .selfcheck_codes import SelfCheckFailed
from .settings import Settings

_sleep = time.sleep  # a module seam: tests replace it with a recorder, so no test waits for real
TRANSPORT_STREAK = 5  # this many documents in a row ending on a transport code stop the SCAN (not the ledger)
PROMPT_PATH = prompt_file.PROMPT_PATH  # the one constant lives in ``prompt_file`` (alias; tests may patch this name)
TIERS = ("read", "fallback")  # tier names, never model ids


def prompt_sha256() -> str:
    """sha256 of the prompt file, read at call time (a missing file fails the extraction, not the import of ``intake check``)."""
    return hashlib.sha256(
        PROMPT_PATH.read_text(encoding="utf-8").encode("utf-8")
    ).hexdigest()  # the text the backend sends, not the file bytes


@dataclass(frozen=True)
class CallInfo:
    """One model call, for diagnostics and the calibration (never holds a body or a key)."""

    tier: str
    model_id: str | None
    in_tok: int
    out_tok: int
    cost_micro: int
    error: str | None
    failing_fields: tuple[str, ...]  # of a returned reply that failed validation or grounding
    refusal: str | None = None  # which guard rule said no (a fixed code word), when it did
    elapsed_ms: int | None = None  # the backend's own timing, when it measured one


@dataclass(frozen=True)
class ProcessedDoc:
    parsed: ParsedDoc = field(repr=False)  # the full invoice text: never printed
    fields: dict | None = field(repr=False)  # the restored record holds hidden values: never printed
    failing_fields: tuple[str, ...]
    cost_micro: int
    tier: str | None
    model_id: str | None
    prompt_sha256: str
    error: str | None
    calls: tuple[CallInfo, ...] = ()
    # WP2c: what the hiding step did (the pipeline stores and shows these; none of them is ever sent to a log as text)
    document_text: str = field(default="", repr=False)  # the original text the data gate hashed
    mask_summary: dict = field(default_factory=dict)  # counts of hidden values by kind, WARN counts, restore counts (ints only)
    selfcheck: str | None = None  # the self-check code when a hiding check failed (flag M01 or M02 through ``FLAG_OF``), else None
    spans: tuple = field(default=(), repr=False)  # ``mask.Span`` positions into ``document_text``
    trace: tuple = ()  # reserved for derived trace rows; the Tracer writes the stored ones
    key: bytes | None = field(default=None, repr=False)  # the per-item fingerprint key used for this run (the pipeline stores it)
    fell_back: bool = (
        False  # the last call was made by the fallback tier (``tier == "fallback"``); the two last fields are appended at the END
    )
    refusal: str | None = None  # the guard rule that refused the last call, when one did (a fixed code word)
    prose: bool = False  # the last reply was well formed but did not call the tool (the pipeline makes flag L03, not the outage flag L02)
    prompt_sha_sent: str | None = None  # sha256 of the prompt text in the bytes that were sent (None when nothing was sent)
    prompt_sha_file: str = ""  # sha256 of the prompt file as read for this document (what would have been sent)


_STORED_RESULT = {"pass": "pass", "fail": "fail", "warn": "warn", "info": "info", "refused": "fail", "same": "pass", "MISMATCH": "fail"}


class QueueSink:
    """The real sink behind a ``Tracer`` (the contract between the queue and the trace log): ``mask_done`` stores the spans and the key through
    ``workqueue.store_mask`` (a refusal is ``SelfCheckFailed('mask_failed')``, raised to the caller, so no call is made); ``row`` stores one trace row
    and returns False when the queue refuses it (the item is already decided, or the row does not fit the closed vocabulary), True otherwise. The Tracer
    turns a False BEFORE the AI call into ``mask_failed`` and a False AFTER it into one visible WARN (``trace_refused``); this class never decides that.
    Stored results are ``pass``, ``fail``, ``warn`` or ``info`` only: a refused gate or a mismatching restore is ``fail``, a restore that is the same is
    ``pass``. ``document_text`` is the original text the spans point into (the Tracer reads it from here when it is not passed)."""

    def __init__(self, settings, item_uid: int, document_text: str) -> None:
        self._s, self._uid = settings, item_uid
        self.document_text = document_text

    def mask_done(self, masked, key: bytes) -> None:
        spans = [workqueue.MaskSpan(sp.placeholder, sp.kind, sp.start, sp.end, sp.fingerprint, sp.detector) for sp in masked.spans]
        workqueue.store_mask(self._s, self._uid, self.document_text, key, spans)

    def row(self, step, at, counts, fingerprints, result, reason_plain) -> bool:
        stored = _STORED_RESULT.get(result)
        if stored is None or stored not in trace_vocab.RESULTS:
            return False
        try:
            row = workqueue.TraceRow(step, at, counts, fingerprints, stored, reason_plain)
            return workqueue.add_trace(self._s, self._uid, row) is not False
        except (ValueError, Refused):
            return False


def _wait_s(code: str, diag, m, repeat_429: bool = False) -> int | None:
    """Seconds to wait before the second call; ``None`` = make no second call: the provider asked for more than ``fallback_wait_max_s``, sent a
    ``Retry-After`` we cannot read, or sent a 429 we cannot read as an ordinary rate limit (cut, unparsed, unknown shape) or the previous document
    also ended on a 429 (``repeat_429``): the fail-safe direction is to stop spending, not to retry."""
    if code in ("timeout", "net", "tls"):
        return 0  # mut:wait_net
    d = clean_diag(diag) or {}
    if d.get("retry_after_bad"):  # mut:ra_bad_stop
        return None
    if code == "http_429" and (d.get("odd_429") or repeat_429):  # mut:odd_429_stop
        return None
    ra = d.get("retry_after_s")
    if ra is None:
        return m.fallback_wait_s
    return None if ra > m.fallback_wait_max_s else ra  # mut:ra_cap


_NO_NETWORK = frozenset(
    {"gate", "body_unsafe", "budget", "halted"}
)  # a call that never left the machine: it neither adds to nor resets the count


class TransportStreak:
    """The scan's stop rule. EVERY scan loop must make ONE of these, pass it as ``streak=`` to ``pipeline.process`` (or ``extract_parsed``) and stop when
    ``stop`` is true. It counts CALLS (cost is per call): a call that ended on a transport code adds one, any other call that reached the provider resets
    it; a call that never left the machine does nothing. With ``settings`` the count lives in the ledger (``meta``), so a restarted scan or a new
    poll tick continues it; a pause longer than ``model.transport_window_s`` restarts it, and at ``model.transport_streak_limit`` a cooldown refuses new
    reserves (``transport_cooldown``). It stops at once on a ``SCAN_STOP_CODES`` refusal (the wall, or a refusal that repeats for every document:
    no ledger, no prices, no owner sentence). ``prev_429`` is true when the last call that reached the provider ended on an HTTP 429. Thread-safe;
    ``add`` is idempotent per document object."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._s = settings
        self._limit = settings.model.transport_streak_limit if settings is not None else TRANSPORT_STREAK
        self._lock = threading.Lock()
        self._seen: dict[int, object] = {}
        self.n = 0
        self.wall = False
        self.prev_429 = False

    @property
    def stop(self) -> bool:
        return self.wall or self.n >= self._limit  # mut:streak

    def add(self, doc: ProcessedDoc) -> bool:
        with self._lock:
            if id(doc) in self._seen:  # mut:idempotent
                return self.stop
            if len(self._seen) > 1000:
                self._seen.clear()
            self._seen[id(doc)] = doc  # keeps the object alive, so its id cannot be reused
            if doc.error in SCAN_STOP_CODES or (doc.error in _NO_NETWORK and doc.refusal in SCAN_STOP_CODES):  # mut:wall_stop
                self.wall = True
                return self.stop
            sent = [c for c in doc.calls if c.error not in _NO_NETWORK]
            outcomes = [c.error in FALLBACK_CODES for c in sent]
            if outcomes:
                self.prev_429 = sent[-1].error == "http_429"  # mut:prev_429
            try:
                if self._s is not None and outcomes:
                    self.n, _ = budget.transport_record(self._s, outcomes)
                else:
                    for f in outcomes:
                        self.n = self.n + 1 if f else 0
            except Refused:
                self.wall = True  # the ledger cannot be written: the safe direction is to stop
            return self.stop


def judge(fields: dict, send_text: str, currencies) -> tuple[str, ...]:
    """Failing top-level field names of a returned reply: schema validation first, then grounding on the text; ``()`` = valid and grounded."""
    bad = validators.validate_record(fields, currencies)
    if bad:
        return tuple(bad)  # no grounding on a record that failed validation
    return ground.ground(fields, send_text).failing_fields


def extract(name: str, data: bytes, model, settings: Settings, tiers=TIERS) -> ProcessedDoc:
    return extract_parsed(reader.read(name, data), model, settings, tiers, streak=None)  # a one-document helper: no scan, no streak


def extract_parsed(
    parsed: ParsedDoc, model, settings: Settings, tiers=TIERS, tracer=None, key: bytes | None = None, *, streak: TransportStreak | None
) -> ProcessedDoc:
    """Order (design B4): validate ``tiers``; reader flag (no mask, no call); the data gate on the document text; key; ``mask`` once (its result is reused
    for both tiers' requests and for restore); checks a3 and a2; ``tracer.mask_done``; per tier the call with ``mask.BodyCheck``; then restore with checks
    (b), the field rule and (c); then ``judge`` (d) on the RESTORED record and the ORIGINAL text. A hiding-check failure gives ``selfcheck`` = its code and no
    fields; before any call it costs nothing, after a reply the settled call still counts and the fallback tier is not tried."""
    if tuple(tiers) not in (TIERS, TIERS[:1]):  # at most two calls per document (spec 6.3): the full tree or the read tier alone
        raise ValueError("tiers must be ('read',) or ('read', 'fallback')")
    sha = prompt_sha256()
    if parsed.flag is not None:
        return ProcessedDoc(parsed, None, (), 0, None, None, sha, None, prompt_sha_file=sha)
    document_text = parsed.text
    try:  # the data gate runs here, before any model text is built, with the shape the guard's own refusal had
        gate_check(settings, document_text)
    except Refused as e:
        return ProcessedDoc(
            parsed,
            None,
            (),
            0,
            tiers[0],
            None,
            sha,
            "gate",
            (CallInfo(tiers[0], None, 0, 0, 0, "gate", (), e.code),),
            document_text=document_text,
            refusal=e.code,
            prompt_sha_file=sha,
        )
    k = key if key is not None else os.urandom(32)
    try:
        masked = mask.mask(document_text, k)
        mask.check_model_text(masked)  # a3 and a2
        if tracer is not None:
            tracer.mask_done(masked, k, document_text)
    except SelfCheckFailed as e:
        return ProcessedDoc(
            parsed, None, (), 0, None, None, sha, None, document_text=document_text, selfcheck=e.code, key=k, prompt_sha_file=sha
        )
    except OSError:  # the trace sink cannot write: no call is made (mask_failed)
        return ProcessedDoc(
            parsed, None, (), 0, None, None, sha, None, document_text=document_text, selfcheck="mask_failed", key=k, prompt_sha_file=sha
        )
    summary = {**masked.counts, **mask.residual_warn(masked.text, masked)}
    cost = 0
    last_tier, last_model, last_error = None, None, None
    calls: list[CallInfo] = []
    sent_sha: list[str] = []  # the prompt hash reported by the backend for the bytes it actually sent
    prose_stop: list[bool] = []

    def done(fields, bad_fields, tier, model_id, error, code=None) -> ProcessedDoc:
        refusal = calls[-1].refusal if calls else None
        return ProcessedDoc(
            parsed,
            fields,
            bad_fields,
            cost,
            tier,
            model_id,
            sent_sha[-1] if sent_sha else sha,
            error,
            tuple(calls),
            document_text,
            summary,
            code,
            masked.spans,
            (),
            k,
            tier == "fallback",
            refusal,
            bool(prose_stop and prose_stop[-1]),
            sent_sha[-1] if sent_sha else None,
            sha,
        )

    for tier in tiers:
        bc = mask.BodyCheck(parsed, masked, k)
        try:
            r = model.call(ExtractRequest(doc_sha=parsed.source_sha256, tier=tier, model_text=masked.text), body_check=bc)
            cost += r.cost_micro
        except (
            ConfigError
        ):  # settle_failed: the spend ledger could not write; the process must stop (exit 3), no further call, no cost guess
            raise
        except Exception:  # a model object that raises is a refusal here (the guard settles what it reserved): no fallback call
            r = ModelResult(fields=None, model_id=None, in_tok=0, out_tok=0, cost_micro=0, error="budget")
        error = r.error if r.error is not None or isinstance(r.fields, dict) else "bad_reply"
        d = clean_diag(r.diag) or {}
        if d.get("prompt_sha_sent"):
            sent_sha.append(d["prompt_sha_sent"])
        prose_stop.append(error == "bad_reply" and d.get("stop_reason") in PROSE_STOPS)
        info = (d.get("refusal"), d.get("elapsed_ms"))
        if error == "body_unsafe":  # the guard refused the bytes: nothing was reserved or sent; the item gets the check's own code
            calls.append(CallInfo(tier, r.model_id, 0, 0, 0, error, (), *info))
            return done(None, (), tier, None, error, bc.last_code or "mask_failed")
        bad: tuple[str, ...] = ()
        restored_fields = None
        if (
            error is None
        ):  # a reply returned: put the values back (checks b, field rule, c), then judge the restored record on the original text
            try:
                rest = mask.restore(r.fields, masked, k, document_text)
            except SelfCheckFailed as e:
                calls.append(CallInfo(tier, r.model_id, r.in_tok, r.out_tok, r.cost_micro, None, (), *info))
                return done(None, (), tier, r.model_id, None, e.code)
            summary.update(restored=rest.restored, unknown=rest.unknown, left=rest.left)
            restored_fields = rest.fields
            bad = judge(restored_fields, document_text, settings.service.currencies)
        calls.append(CallInfo(tier, r.model_id, r.in_tok, r.out_tok, r.cost_micro, error, bad, *info))
        if error is None and not bad:
            return done(copy.deepcopy(restored_fields), (), tier, r.model_id, None)
        # a reply that failed validation or grounding goes to a person (X10): never a second call
        if error is None:
            return done(None, bad, tier, r.model_id, None)  # mut:x10_stop
        last_tier, last_model, last_error = tier, r.model_id, error
        if error not in FALLBACK_CODES or tier == tiers[-1]:
            break  # a stop or quality code, or nothing left after the last tier
        wait = _wait_s(error, r.diag, settings.model, bool(streak and streak.prev_429))
        if wait is None:
            break  # the provider asked for more than we will wait
        if wait > 0:
            _sleep(wait)  # mut:sleep
    return done(None, (), last_tier, last_model, last_error)
