"""The signed trigger endpoint: pure functions and a WSGI callable. It starts nothing itself.

A sender posts one JSON object (``key``, ``document``) signed with the HMAC "v0" scheme of
``hadavin_sdk.approvals.hmac_v0`` under the ``X-Hadavin`` header prefix. The checks run in a fixed
order: path and method, Content-Length, size cap, read, signature and timestamp window, JSON and
fields. Nothing of the body is parsed before the signature verifies. The sender is the one whose
secret verified; agent and principal come from configuration, never from the request. The caller's
``start`` decides the answer; this module does not import the runtime, the store or the app.

Every refusal has an empty body. Log lines hold the status and, once verified, the sender id; never
the body, the key, a header value or a secret. A request that was not verified is logged at DEBUG
(anyone who reaches the port decides how many there are), a verified one at INFO. A 409 is logged by
the caller's ``start``, which adds
the run id; this module writes no second line for it.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, Protocol

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.defaults import MAX_DOCUMENT_BYTES

# ---- wire constants (one place) ----
PREFIX: Final = "X-Hadavin"  # header prefix handed to hmac_v0
TIMESTAMP_HEADER: Final = f"{PREFIX}-Request-Timestamp"
SIGNATURE_HEADER: Final = f"{PREFIX}-Signature"
PATH: Final = "/v1/trigger"
METHOD: Final = "POST"
KEY_RE: Final = re.compile(r"[A-Za-z0-9._:-]{1,128}")
ID_RE: Final = re.compile(r"[a-z0-9-]{1,40}")  # tenant and sender ids
RUN_ID_HEX: Final = 32  # "run-" + this many hex digits, the shape of models.RUN_ID_PATTERN
MIN_SECRET_CHARS: Final = 32
MAX_SENDERS: Final = 8
MAX_SECRETS_PER_SENDER: Final = 2  # the old and the new one while a secret is being replaced
# Not seen in an editor and not cut by strip(): byte-order mark, zero-width space, non-joiner, joiner,
# word joiner. A secret file saved with one of them would never verify.
UNSEEN_CHARS: Final = "\ufeff\u200b\u200c\u200d\u2060"
# The most ``max_body_bytes`` may be, whatever settings object the caller hands in: a body is JSON text
# around one document, and escaping can make it several times the document's size.
MAX_BODY_BYTES_LIMIT: Final = 8 * MAX_DOCUMENT_BYTES
MAX_LENGTH_DIGITS: Final = 12  # a longer Content-Length is over any cap; also keeps int() cheap
BODY_FIELDS: Final = frozenset({"key", "document"})
ANSWER_FIELDS: Final = ("run_id", "state")
JSON_TYPE: Final = "application/json"
STATUS_TEXT: Final[Mapping[int, str]] = {
    200: "200 OK",
    202: "202 Accepted",
    400: "400 Bad Request",
    401: "401 Unauthorized",
    404: "404 Not Found",
    405: "405 Method Not Allowed",
    409: "409 Conflict",
    413: "413 Content Too Large",
    503: "503 Service Unavailable",
}
BODY_STATUSES: Final = frozenset({200, 202})  # only these answers carry a body
RETRY_AFTER_SECONDS: Final = 1  # whole seconds a sender waits before it sends again after a 503

_LOG = logging.getLogger("hadavin_sdk.triggers")


class BadRequest(ValueError):
    """The signed body is not the exact JSON shape. The message never quotes the body."""


class SenderSettings(Protocol):
    @property
    def id(self) -> str: ...
    @property
    def agent_id(self) -> str: ...
    @property
    def principal_id(self) -> str: ...


class TriggerSettings(Protocol):
    """The part of the config block ``triggers`` this module reads (duck-typed)."""

    @property
    def tenant(self) -> str: ...
    @property
    def senders(self) -> Sequence[SenderSettings]: ...
    @property
    def max_body_bytes(self) -> int: ...


@dataclass(frozen=True)
class Accepted:
    """A verified, well-formed request, ready for ``Runtime.handle``."""

    sender: str
    agent_id: str
    principal_id: str
    run_id: str
    trigger_ref: str
    document: bytes


Start = Callable[[Accepted], tuple[int, "dict[str, str] | None"]]


def derive_run_id(tenant: str, sender: str, key: str) -> str:
    """The one run id of (tenant, sender, key). The three charsets exclude NUL, the separator, so
    two different triples never give the same hash input."""
    for name, value, rx in (
        ("tenant", tenant, ID_RE),
        ("sender", sender, ID_RE),
        ("key", key, KEY_RE),
    ):
        if not isinstance(value, str) or "\0" in value or rx.fullmatch(value) is None:
            raise ValueError(f"{name} does not match {rx.pattern}")
    joined = f"{tenant}\0{sender}\0{key}".encode()
    return "run-" + hashlib.sha256(joined).hexdigest()[:RUN_ID_HEX]


def trigger_ref(sender: str, key: str, document: bytes) -> str:
    """Names the request and its payload: the same key with another document gives another ref."""
    return f"{sender}/{key}#{hashlib.sha256(document).hexdigest()}"


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out = dict(pairs)
    if len(out) != len(pairs):
        raise BadRequest("duplicate member")
    return out


def parse_body(body: bytes) -> tuple[str, bytes]:
    """(key, document bytes) of a body that is exactly ``{"key": str, "document": str}``."""
    try:
        obj = json.loads(body.decode("utf-8"), object_pairs_hook=_no_duplicates)
    except BadRequest:
        raise
    except (ValueError, RecursionError) as e:  # not UTF-8, not JSON, too deep, oversize number
        raise BadRequest("not a JSON document") from e
    if not isinstance(obj, dict) or set(obj) != BODY_FIELDS:
        raise BadRequest("not an object with exactly key and document")
    key, document = obj["key"], obj["document"]
    if not isinstance(key, str) or not isinstance(document, str):
        raise BadRequest("key and document must be strings")
    if KEY_RE.fullmatch(key) is None:
        raise BadRequest("key does not match the key rule")
    try:
        return key, document.encode("utf-8")
    except UnicodeEncodeError as e:  # a lone surrogate written as a JSON escape
        raise BadRequest("document is not valid text") from e


def verify_any(
    headers: Mapping[str, str],
    body: bytes,
    now_ts: float,
    secrets: Mapping[str, tuple[str, ...]],
) -> str | None:
    """The id of the sender whose secret signed this request, else None.

    Timing: every configured secret is tried on every request and the loop never stops early, so
    the number of HMACs does not depend on which sender or which of its secrets matched; each
    comparison is ``hmac.compare_digest`` inside ``hmac_v0.verify``. NOT constant-time: a missing
    or malformed timestamp or signature header, or a timestamp outside the window, returns early
    inside ``hmac_v0.verify`` (the same for every secret, so it tells nothing about a secret), and
    the total time grows with the number of configured secrets and the body length.

    The clock is cut to whole seconds, so a timestamp exactly ``hmac_v0.MAX_AGE_S`` seconds old or
    ahead is inside the window and one second more is outside, whatever the clock's fraction.
    """
    now = int(now_ts)
    matched: set[str] = set()
    for sender, values in secrets.items():
        for value in values:
            if hmac_v0.verify(headers, body, now, value, PREFIX):
                matched.add(sender)
    # Values are distinct across senders (check_secrets), so two matches mean a broken setup.
    return next(iter(matched)) if len(matched) == 1 else None


def check_secrets(secrets: Mapping[str, tuple[str, ...]]) -> None:
    """Start-up check of the secret VALUES. Errors name the sender, never a value."""
    if not secrets:
        raise ValueError("no trigger sender has a secret")
    if len(secrets) > MAX_SENDERS:
        raise ValueError(f"more than {MAX_SENDERS} trigger senders")
    owner: dict[str, str] = {}
    for sender, values in secrets.items():
        if isinstance(values, str) or not values:
            raise ValueError(f"trigger sender {sender!r}: no secret, or not a tuple of secrets")
        if len(values) > MAX_SECRETS_PER_SENDER:
            raise ValueError(
                f"trigger sender {sender!r}: more than {MAX_SECRETS_PER_SENDER} secrets"
            )
        for value in values:
            if not isinstance(value, str) or not value:
                raise ValueError(f"trigger sender {sender!r}: an empty secret")
            if value != value.strip():
                raise ValueError(
                    f"trigger sender {sender!r}: a secret with leading or trailing whitespace"
                )
            if len(value) < MIN_SECRET_CHARS:
                raise ValueError(
                    f"trigger sender {sender!r}: a secret under {MIN_SECRET_CHARS} characters"
                )
            try:
                value.encode("utf-8")
            except UnicodeEncodeError:  # a lone surrogate: every request would end in a 503
                raise ValueError(
                    f"trigger sender {sender!r}: a secret that cannot be written as UTF-8"
                ) from None
            if any(char in value for char in UNSEEN_CHARS):
                raise ValueError(
                    f"trigger sender {sender!r}: a secret with a byte-order mark or a zero-width"
                    " character"
                )
            if any(unicodedata.category(char) == "Cc" for char in value):
                raise ValueError(f"trigger sender {sender!r}: a secret with a control character")
            if values.count(value) > 1:
                raise ValueError(f"trigger sender {sender!r}: the same secret twice")
            other = owner.setdefault(value, sender)
            if other != sender:
                raise ValueError(f"trigger senders {other!r} and {sender!r} share a secret")


def sender_map(senders: Any) -> dict[str, SenderSettings]:
    """Sender id -> sender, from the config list (a mapping id -> sender is taken as it is)."""
    if isinstance(senders, Mapping):
        return dict(senders)
    out: dict[str, SenderSettings] = {}
    for sender in senders:
        if sender.id in out:
            raise ValueError(f"trigger sender id {sender.id!r} is listed twice")
        out[sender.id] = sender
    return out


def _content_length(raw: object) -> int:
    """The declared length, or -1 when missing, empty, signed, spaced or not ASCII digits."""
    if not isinstance(raw, str) or not (raw.isascii() and raw.isdigit()):
        return -1
    return int(raw) if len(raw) <= MAX_LENGTH_DIGITS else 10**MAX_LENGTH_DIGITS


def make_wsgi(
    settings: TriggerSettings,
    secrets: Mapping[str, tuple[str, ...]],
    start: Start,
    clock: Callable[[], float] = time.time,
) -> Callable[..., list[bytes]]:
    """The WSGI application for ``POST /v1/trigger``. Raises ValueError on a bad setup."""
    tenant = settings.tenant
    senders = sender_map(settings.senders)
    max_body = settings.max_body_bytes
    if not isinstance(tenant, str) or ID_RE.fullmatch(tenant) is None:
        raise ValueError(f"triggers.tenant does not match {ID_RE.pattern}")
    if isinstance(max_body, bool) or not isinstance(max_body, int) or max_body <= 0:
        raise ValueError("triggers.max_body_bytes must be a positive integer")
    if max_body > MAX_BODY_BYTES_LIMIT:
        raise ValueError(f"triggers.max_body_bytes is over {MAX_BODY_BYTES_LIMIT}")
    if len(senders) > MAX_SENDERS:
        raise ValueError(f"more than {MAX_SENDERS} trigger senders")
    for sender in senders:
        if not isinstance(sender, str) or ID_RE.fullmatch(sender) is None:
            raise ValueError(f"trigger sender id {sender!r} does not match {ID_RE.pattern}")
    if set(secrets) != set(senders):
        odd = sorted(set(secrets) ^ set(senders))
        raise ValueError(f"trigger senders and their secrets do not line up: {odd}")
    check_secrets(secrets)
    secrets = {sender: tuple(values) for sender, values in secrets.items()}
    ts_env = "HTTP_" + TIMESTAMP_HEADER.upper().replace("-", "_")
    sig_env = "HTTP_" + SIGNATURE_HEADER.upper().replace("-", "_")

    def decide(environ: Mapping[str, Any]) -> tuple[int, str | None, dict[str, str] | None]:
        """(status, verified sender or None, answer or None), in the fixed check order."""
        if environ.get("PATH_INFO") != PATH:
            return 404, None, None
        if environ.get("REQUEST_METHOD") != METHOD:
            return 405, None, None
        length = _content_length(environ.get("CONTENT_LENGTH"))
        if length <= 0:
            return 400, None, None
        if length > max_body:
            return 413, None, None  # the body is not read
        try:
            body = environ["wsgi.input"].read(length)
        except Exception:  # noqa: BLE001 - a broken or timed-out connection is the sender's fault
            return 400, None, None
        if not isinstance(body, bytes) or len(body) != length:
            return 400, None, None
        ts, sig = environ.get(ts_env), environ.get(sig_env)
        headers = {
            TIMESTAMP_HEADER: ts if isinstance(ts, str) else "",
            SIGNATURE_HEADER: sig if isinstance(sig, str) else "",
        }
        sender = verify_any(headers, body, clock(), secrets)
        if sender is None:
            return 401, None, None
        try:
            key, document = parse_body(body)
        except BadRequest:
            return 400, sender, None
        who = senders[sender]
        accepted = Accepted(
            sender=sender,
            agent_id=who.agent_id,
            principal_id=who.principal_id,
            run_id=derive_run_id(tenant, sender, key),
            trigger_ref=trigger_ref(sender, key, document),
            document=document,
        )
        try:
            status, answer = start(accepted)
        except Exception as e:  # noqa: BLE001 - no ack; the sender retries with the same key
            _LOG.warning("trigger start failed: %s", type(e).__name__)
            return 503, sender, None
        if isinstance(status, bool) or status not in STATUS_TEXT:
            return 503, sender, None
        return status, sender, answer

    def app(environ: Mapping[str, Any], start_response: Callable[..., Any]) -> list[bytes]:
        try:
            status, sender, answer = decide(environ)
        except Exception as e:  # noqa: BLE001 - never a traceback page; nothing of the request
            _LOG.error("trigger endpoint error: %s", type(e).__name__)
            status, sender, answer = 503, None, None
        out = b""
        if status in BODY_STATUSES and isinstance(answer, Mapping):
            picked = {k: str(answer[k]) for k in ANSWER_FIELDS if k in answer}
            out = json.dumps(picked).encode("utf-8")
        response_headers = [("Content-Length", str(len(out)))]
        if out:
            response_headers.append(("Content-Type", JSON_TYPE))
        if status == 405:
            response_headers.append(("Allow", METHOD))
        if status == 503:
            response_headers.append(("Retry-After", str(RETRY_AFTER_SECONDS)))
        if status != 409:  # ``start`` wrote the 409 line, with the run id: one line per request
            level = logging.INFO if sender else logging.DEBUG  # DEBUG: refused before it verified
            _LOG.log(level, "trigger status=%d sender=%s", status, sender or "-")
        start_response(STATUS_TEXT[status], response_headers)
        return [out]

    return app
