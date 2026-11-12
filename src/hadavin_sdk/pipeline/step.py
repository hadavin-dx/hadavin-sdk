"""The pipeline step contract (AK1-a): what a step takes in, what it gives back, and the one runner that calls it.

Plain words. A *step* is one unit of pipeline work on one *item* (read a document, cut it into passages, make
embeddings). The contract fixes three things:

* **Who owns the item.** Every item carries a *tenant* (one customer; text of one tenant must never reach another) and
  its *readers* (the people or roles allowed to see it). A step may narrow the readers, never widen them, and may not
  change the tenant or the item id.
* **How it ends.** Every item that a step returns ends in exactly ONE final state: ``done``, ``needs_person`` ("a person
  must look") or ``refused``, with a reason from a closed list.
* **What is written down.** The runner writes an audit *intent* event BEFORE the step runs and an *outcome* event after
  it. Audit events hold ids, hashes, counts and closed codes only, never item text and never exception text.

Nothing here sends text anywhere or touches money: the outbound gate is AK1-b (``guard/outbound.py``), and AK1-b adds its
own rows to ``REASON_BY_ERROR`` and its own hooks to ``run_step``. This module imports no network library.

Who owns the final state when the runner cannot give one. ``run_step`` returns exactly one ``StepOutput`` on every path
that RETURNS. Two paths do not return: a bad argument (a programming error, ``TypeError`` or ``ValueError``) and a stop
request (``KeyboardInterrupt``, ``SystemExit``, ``GeneratorExit``, ``asyncio.CancelledError`` and any other
``BaseException`` that is not an ``Exception``). On those paths the CALLER owns the item's final state.

Everything refused here is refused with a fixed message that never contains the offending value, so a refused text
cannot reach a log line through an error message.
"""

from __future__ import annotations

import hashlib
import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final, Protocol

from hadavin_sdk import defaults
from hadavin_sdk.audit.protocol import AuditSink, AuditUnavailable
from hadavin_sdk.models import AuditEvent

log = logging.getLogger(__name__)

# --- shapes of names (protocol shapes: they live here, not in defaults.py) ---------------------------------------------
# Each is matched with `fullmatch` on an exact `str`, so a newline at the end, a `str` subclass and the wrong case are
# refused, and a look-alike letter from another alphabet never matches (the classes list ASCII letters only).
ITEM_ID_PATTERN: Final = r"[a-z][a-z0-9_]{0,23}-[0-9a-f]{32}"  # the shape of `models.new_id`
TENANT_PATTERN: Final = r"[a-z0-9][a-z0-9_-]{0,62}"
READER_PATTERN: Final = r"[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}"
STEP_NAME_PATTERN: Final = r"[a-z][a-z0-9_]{0,39}"

_ITEM_ID = re.compile(ITEM_ID_PATTERN)
_TENANT = re.compile(TENANT_PATTERN)
_READER = re.compile(READER_PATTERN)
_STEP_NAME = re.compile(STEP_NAME_PATTERN)

# The readers of an item: a `frozenset` of 1 to `defaults.PIPELINE_MAX_READERS` names, each matching `READER_PATTERN`.
# `"*"` cannot match, so "everyone" cannot be written. Use `check_readers` to validate one.
type Readers = frozenset[str]


def check_item_id(value: object) -> str:
    """The item id, or ``ValueError``. The message never holds the value."""
    if type(value) is not str or _ITEM_ID.fullmatch(value) is None:
        raise ValueError("item_id: not an id of the form <prefix>-<32 lower-case hex digits>")
    return value


def check_tenant(value: object) -> str:
    """The tenant name, or ``ValueError``. The message never holds the value."""
    if type(value) is not str or _TENANT.fullmatch(value) is None:
        raise ValueError(
            "tenant: not a tenant name (1 to 63 of a-z, 0-9, _ and -, not starting with _ or -)"
        )
    return value


def check_readers(value: object) -> frozenset[str]:
    """The readers, or ``ValueError``. Empty, too many, a non-``str`` or a name outside the shape is refused."""
    if type(value) is not frozenset:
        raise ValueError("readers: must be a frozenset of names")
    if not 1 <= len(value) <= defaults.PIPELINE_MAX_READERS:
        raise ValueError(
            f"readers: between 1 and {defaults.PIPELINE_MAX_READERS} names are required"
        )
    for reader in value:
        if type(reader) is not str or _READER.fullmatch(reader) is None:
            raise ValueError("readers: a name is outside the allowed shape")
    return value


def _check_label(field: str, value: object) -> str:
    """A run id, agent id or principal: made by the runtime, never item text. Exact ``str``, bounded, printable."""
    if (
        type(value) is not str
        or not 1 <= len(value) <= defaults.PIPELINE_LABEL_MAX_CHARS
        or not value.isprintable()
    ):
        raise ValueError(
            f"{field}: must be a printable str of 1 to {defaults.PIPELINE_LABEL_MAX_CHARS} characters"
        )
    return value


def _check_body(body: object) -> None:
    """A body is exact ``bytes`` or an exact ``str`` that encodes as strict UTF-8 (a lone surrogate is refused)."""
    if type(body) is bytes:
        return
    if type(body) is not str:
        raise TypeError("body: must be str or bytes")
    try:
        body.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError("body: not valid UTF-8") from None


def tenant_key(tenant: str, *parts: str) -> str:
    """One string for a tenant and any further names, for every store, cache and index key that holds tenant data.

    ``"t" + len(tenant) + ":" + tenant``, then for each part ``"/" + len(part) + ":" + part``. Every piece is length-
    prefixed, so two different argument lists never give the same key (``("a", "x/y")`` and ``("a", "x", "y")`` differ),
    and the tenant always comes first. A bad tenant, or a part that is not a ``str`` of 1 to
    ``defaults.PIPELINE_KEY_PART_MAX_CHARS`` characters, is ``ValueError`` (the message never holds the value).
    """
    check_tenant(tenant)
    key = f"t{len(tenant)}:{tenant}"
    for part in parts:
        if type(part) is not str or not 1 <= len(part) <= defaults.PIPELINE_KEY_PART_MAX_CHARS:
            raise ValueError(
                f"tenant_key: each part must be a str of 1 to {defaults.PIPELINE_KEY_PART_MAX_CHARS} characters"
            )
        key += f"/{len(part)}:{part}"
    return key


# --- final states and reasons ------------------------------------------------------------------------------------------
class Outcome(StrEnum):
    """The final state of one item at one step. (Not ``models.RunState``: that is a RUN's state in the ``runs`` table.)"""

    DONE = "done"
    NEEDS_PERSON = "needs_person"  # "a person must look"
    REFUSED = "refused"


# Closed. `unreadable` = the file could not be read at all; `meter_unavailable` = the money store could not be reached.
REASONS: Final[Mapping[Outcome, frozenset[str]]] = MappingProxyType(
    {
        Outcome.DONE: frozenset(),
        Outcome.NEEDS_PERSON: frozenset(
            {
                "step_error",
                "low_quality",
                "unreadable",
                "over_budget",
                "meter_unavailable",
                "masking_refused",
                "outbound_refused",
                "audit_unavailable",
                "policy",
            }
        ),
        Outcome.REFUSED: frozenset({"invalid_input", "forbidden", "duplicate"}),
    }
)

# Exception class -> the `needs_person` reason it ends in. `run_step` walks the raised class's MRO and the FIRST class
# found here wins; no match is `step_error`. AK1-b appends the gate's errors (it imports them here, never the reverse).
REASON_BY_ERROR: Final[Mapping[type[BaseException], str]] = MappingProxyType(
    {
        AuditUnavailable: "audit_unavailable",
    }
)


def _check_reason(outcome: Outcome, reason: object) -> None:
    if outcome is Outcome.DONE:
        if reason is not None:
            raise ValueError("reason: a done item carries no reason")
        return
    if type(reason) is not str or reason not in REASONS[outcome]:
        raise ValueError(f"reason: not one of the closed reasons of {outcome.value}")


# --- records -----------------------------------------------------------------------------------------------------------
@dataclass(frozen=True, slots=True, repr=False)
class StepInput:
    """One item going into a step. ``body`` is text or bytes. ``__repr__`` and ``__str__`` never show text."""

    item_id: str
    tenant: str
    readers: frozenset[str]
    body: str | bytes
    run_id: str | None
    agent_id: str

    def __post_init__(self) -> None:
        check_item_id(self.item_id)
        check_tenant(self.tenant)
        check_readers(self.readers)
        _check_body(self.body)
        if self.run_id is not None:
            _check_label("run_id", self.run_id)
        _check_label("agent_id", self.agent_id)

    @property
    def content_sha256(self) -> str:
        """SHA-256 of the body bytes (text is strict UTF-8). A ``str`` body and its UTF-8 ``bytes`` hash the same."""
        return hashlib.sha256(
            self.body if type(self.body) is bytes else self.body.encode("utf-8")
        ).hexdigest()

    def __repr__(self) -> str:
        return (
            f"StepInput(item_id={self.item_id!r}, tenant={self.tenant!r}, readers={len(self.readers)}, "
            f"content_sha256={self.content_sha256!r})"
        )


@dataclass(frozen=True, slots=True, repr=False)
class StepOutput:
    """One item coming out of a step, in one final state. ``body`` is ``None`` unless the outcome is ``done``."""

    item_id: str
    tenant: str
    readers: frozenset[str]
    outcome: Outcome
    reason: str | None
    body: str | bytes | None
    run_id: str | None
    agent_id: str

    def __post_init__(self) -> None:
        check_item_id(self.item_id)
        check_tenant(self.tenant)
        check_readers(self.readers)
        if type(self.outcome) is not Outcome:
            raise ValueError("outcome: must be an Outcome")
        _check_reason(self.outcome, self.reason)
        if self.body is not None:
            if self.outcome is not Outcome.DONE:
                raise ValueError("body: only a done item carries a body")
            _check_body(self.body)
        if self.run_id is not None:
            _check_label("run_id", self.run_id)
        _check_label("agent_id", self.agent_id)

    def __repr__(self) -> str:
        return (
            f"StepOutput(item_id={self.item_id!r}, tenant={self.tenant!r}, readers={len(self.readers)}, "
            f"outcome={self.outcome.value!r}, reason={self.reason!r}, has_body={self.body is not None})"
        )


class Step(Protocol):
    """One unit of pipeline work. ``name`` matches ``STEP_NAME_PATTERN``."""

    name: str

    def run(self, inp: StepInput) -> StepOutput: ...


# --- the runner --------------------------------------------------------------------------------------------------------
def _failed(inp: StepInput, reason: str) -> StepOutput:
    """The item ends `needs_person` with `reason`; the step's body is dropped."""
    return StepOutput(
        item_id=inp.item_id,
        tenant=inp.tenant,
        readers=inp.readers,
        outcome=Outcome.NEEDS_PERSON,
        reason=reason,
        body=None,
        run_id=inp.run_id,
        agent_id=inp.agent_id,
    )


def _reason_for(exc: BaseException) -> str:
    """The reason for a raised error: the first class of its MRO found in `REASON_BY_ERROR`, else `step_error`."""
    for cls in type(exc).__mro__:
        if cls in REASON_BY_ERROR:
            return REASON_BY_ERROR[cls]
    return "step_error"


def _acceptable(inp: StepInput, out: object) -> bool:
    """Is `out` a well-formed output for exactly this item that does not change tenant, run or agent or widen readers?

    The record is checked again here (not only in its constructor) so a record built around the constructor, for
    example with ``object.__new__``, is refused too.
    """
    try:
        if type(out) is not StepOutput:
            return False
        StepOutput.__post_init__(out)
        return (
            out.item_id == inp.item_id
            and out.tenant == inp.tenant
            and out.readers <= inp.readers
            and out.run_id == inp.run_id
            and out.agent_id == inp.agent_id
        )
    except (ValueError, TypeError, AttributeError):
        return False


def run_step(step: Step, inp: StepInput, *, audit: AuditSink, principal: str) -> StepOutput:
    """Run one step on one item and return exactly one ``StepOutput`` (see the module text for the paths that do not).

    In order: write the audit intent event (if that fails the step is NOT called and the item ends `needs_person
    audit_unavailable`); call the step; check the output (a wrong type, another item, another tenant, another run or
    agent, or a reader the input did not have ends `needs_person step_error` with no body); write the outcome event.
    """
    name = step.name
    if type(name) is not str or _STEP_NAME.fullmatch(name) is None:
        raise ValueError("step.name: not a step name")
    if type(inp) is not StepInput:
        raise TypeError("inp: must be a StepInput")
    _check_label("principal", principal)
    object_ref = tenant_key(inp.tenant, inp.item_id)
    try:
        audit.write_intent(
            AuditEvent(
                run_id=inp.run_id or "-",
                domain="pipeline",
                operation=name,
                principal=principal,
                source="step",
                object_ref=object_ref,
                inputs_hash=inp.content_sha256,
            )
        )
    except Exception as exc:  # noqa: BLE001 - any failure to write the intent stops the step (fail closed)
        log.warning("step %s: intent not written (%s)", name, type(exc).__name__)
        return _failed(inp, "audit_unavailable")

    def write_outcome(outcome: Outcome, reason: str | None, readers: int) -> None:
        try:
            audit.write_outcome(
                AuditEvent(
                    run_id=inp.run_id or "-",
                    domain="pipeline",
                    operation=name,
                    principal=principal,
                    source="step",
                    object_ref=object_ref,
                    decision=outcome.value,
                    error_code=reason,
                    result=f"readers={readers}",
                )
            )
        except Exception as exc:  # noqa: BLE001 - off contract: `write_outcome` never raises; a sink must not lose the output
            log.warning("step %s: outcome not written (%s)", name, type(exc).__name__)

    try:
        out = step.run(inp)
    except Exception as exc:  # noqa: BLE001 - a step may raise anything; each class maps to one closed reason
        log.warning("step %s raised %s", name, type(exc).__name__)
        out = _failed(inp, _reason_for(exc))
    except BaseException:
        write_outcome(Outcome.NEEDS_PERSON, "step_error", len(inp.readers))
        raise
    if not _acceptable(inp, out):
        log.warning("step %s: output refused", name)
        out = _failed(inp, "step_error")
    write_outcome(out.outcome, out.reason, len(out.readers))
    return out
