"""The model gate: one wrapper around the model client (step F).

Guarantee: values the run has identified as sensitive are replaced by their placeholders in everything sent to a model; detection of new values is done by the producers' pattern redactor.

Before any provider contact the gate enforces the caller's run map on every message and document (a raw copy
of a value the map holds becomes that value's existing placeholder; `runmap.enforce_map`), then reserves the
worst-case cost. The client gets the enforced copies. After the call the gate settles the real cost and writes
one audit row. If the enforce step or the reservation fails, no call is made. The gate holds no money logic and
no redaction logic of its own: it only orders the steps.

Stated limits. The gate runs no pattern: a value that is in no map (also a clean key and a clean value that
only match a pattern once composed, such as `"user_id": "abc123"`) passes as written. With no map
(`mapping=None`: the eval and replay command lines, the judge with its own map) there is no enforce step.
`system` and `tools` are operator text and are not touched.

No logger, no module-level state, and no message text, no exception text and no exception chain in any audit
row or in any exception raised here. The caller's messages, dicts and documents are never changed in place.
"""

from __future__ import annotations

import contextlib
import re
from collections.abc import Callable, Mapping
from decimal import Decimal
from typing import Any, Protocol

from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.guard import runmap
from hadavin_sdk.llm.protocol import LLM, ProviderError, ProviderExhausted
from hadavin_sdk.models import AuditEvent, Reply

# ======================================================================================================
# ASSUMED INTERFACE (ii): switch here when core-b publishes it
# `Meter` mirrors INTERFACE (ii) as the lead published it (ORDER 006; inputs/draft-ticket-F-store-with-
# INTERFACE-ii.md lines 113-135). It is a local structural Protocol: `limits.SpendRefused` does not exist
# yet and is NOT imported; its `.reason` is read with getattr. Nothing outside this block names a meter
# method, an audit string or the worst_case arguments.
# ------------------------------------------------------------------------------------------------------
# reserve: returns a reservation id only after the worst case is booked; ANY exception means no model call.
# settle: returns the overshoot; the first call for a reservation wins. Real cost known -> settle it (0 for
# a request the provider refused). Real cost unknown and the process is going down -> do not settle: the
# worst case stays booked and the store's sweep closes it.
# worst_case: supplied by the installer; it resolves the route name and covers the client's retries.


class Meter(Protocol):
    def reserve(self, agent_id: str, worst_usd: Decimal, *, run_id: str | None = None) -> str: ...

    def settle(self, reservation_id: str, actual_usd: Decimal) -> Decimal: ...


WorstCase = Callable[
    [
        str,  # route
        str,  # system
        list[dict[str, Any]],  # messages
        list[dict[str, Any]] | None,  # tools
        list[bytes] | None,  # documents
        dict[str, Any] | None,  # output_schema
    ],
    Decimal,
]
# (text, the run's map) -> the text with the map's values replaced; any raise means no call
Enforce = Callable[[str, Mapping[str, str]], str]

AUDIT_DOMAIN = "llm"
AUDIT_OPERATION = "chat"
DEFAULT_SOURCE = "gate"
RESULT_OK = "ok"
RESULT_REFUSED = "refused"
RESULT_FAILED = "failed"
CODE_GATE_REFUSED = "gate_refused"
CODE_MASK_REFUSED = "mask_refused"
CODE_RESERVE_REFUSED = "reserve_refused"  # used when the meter's exception has no usable `.reason`
CODE_PROVIDER_ERROR = "provider_error"  # refused before any work: settled at 0
CODE_PROVIDER_EXHAUSTED = "provider_exhausted"  # retries used up: settled at the worst case
CODE_CALL_FAILED = "call_failed"  # any other Exception from the client: settled at the worst case
CODE_CALL_INTERRUPTED = "call_interrupted"  # KeyboardInterrupt, SystemExit: NOT settled
CODE_SETTLE_FAILED = "settle_failed"
# A meter's `.reason` becomes the audit error code only when it is shaped like a code (never free text).
REASON_CODE = re.compile(r"[a-z][a-z0-9_.]{0,63}")
# END OF ASSUMED INTERFACE (ii)
# ======================================================================================================


class GateRefused(RuntimeError):
    """The gate made no model call. Carries a stable `code` and nothing else: never text, never a secret."""

    code = CODE_GATE_REFUSED

    def __init__(self) -> None:
        super().__init__(self.code)


class UnmaskedInput(GateRefused):
    """The run map could not be enforced on what the caller passed (a content that is not `str`, a text over
    the cap, a bad map, any failure of the enforce step). Never raised because a pattern matched."""

    code = CODE_MASK_REFUSED


class ModelGate:
    """Holds the client, the meter, the audit sink, the worst-case function and the enforce step. It has NO
    `chat`: a caller must `bind` it to an agent and a run first, so an unbound gate cannot call a model.
    A client that is already a gate is refused (TypeError): one call must never be reserved twice."""

    def __init__(
        self,
        llm: LLM,
        *,
        meter: Meter,
        audit: AuditSink | None,
        worst_case: WorstCase,
        enforce: Enforce = runmap.enforce_map,
    ) -> None:
        if isinstance(llm, ModelGate | BoundGate):
            raise TypeError("the client is already a model gate")
        self._llm, self._meter, self._audit = llm, meter, audit
        self._worst_case, self._enforce = worst_case, enforce

    def bind(
        self,
        agent_id: str,
        run_id: str,
        *,
        mapping: Mapping[str, str] | None = None,
        principal: str | None = None,
        source: str = DEFAULT_SOURCE,
    ) -> BoundGate:
        """A gate for one call site. `mapping` is the run's LIVE map, kept by reference (never copied, never
        written): a value the run masks later is replaced in earlier text on the next call. None (a site
        with no run map) means no enforce step. `principal` defaults to the agent id."""
        return BoundGate(self, agent_id, run_id, mapping, principal or agent_id, source)


class BoundGate:
    """Satisfies `llm.protocol.LLM`. Order: enforce the map, reserve, provider call, settle, audit row."""

    def __init__(
        self,
        gate: ModelGate,
        agent_id: str,
        run_id: str,
        mapping: Mapping[str, str] | None,
        principal: str,
        source: str,
    ) -> None:
        self._llm, self._meter, self._audit = gate._llm, gate._meter, gate._audit
        self._worst_case, self._enforce = gate._worst_case, gate._enforce
        self._agent_id, self._run_id, self._mapping = agent_id, run_id, mapping
        self._principal, self._source = principal, source

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
        enforced = self._enforced(messages, documents)
        if enforced is None:
            self._note(RESULT_REFUSED, CODE_MASK_REFUSED)
            raise UnmaskedInput  # raised outside any `except`: no cause and no context to leak
        messages, documents = enforced  # from here on only the enforced copies are used
        try:
            reserved = self._worst_case(route, system, messages, tools, documents, output_schema)
            reservation = self._meter.reserve(self._agent_id, reserved, run_id=self._run_id)
        except Exception as exc:
            reason = getattr(exc, "reason", None)
            known = isinstance(reason, str) and REASON_CODE.fullmatch(reason) is not None
            self._note(RESULT_REFUSED, reason if known else CODE_RESERVE_REFUSED)
            raise
        try:
            reply = self._llm.chat(
                messages,
                system=system,
                route=route,
                tools=tools,
                documents=documents,
                output_schema=output_schema,
            )
        except ProviderExhausted:
            self._failed(reservation, reserved, CODE_PROVIDER_EXHAUSTED)
            raise
        except ProviderError:  # refused before any work was done: it cost nothing
            self._failed(reservation, Decimal(0), CODE_PROVIDER_ERROR)
            raise
        except Exception:  # may have been billed (a reply that fails to parse): hold the worst case
            self._failed(reservation, reserved, CODE_CALL_FAILED)
            raise
        except BaseException:  # going down, cost unknown: not settled, the store's sweep closes it
            self._note(RESULT_FAILED, CODE_CALL_INTERRUPTED)
            raise
        try:
            self._meter.settle(reservation, reply.cost_usd)
        except Exception:  # noqa: BLE001 - the call is paid: the reply is never lost to a meter failure
            self._note(RESULT_FAILED, CODE_SETTLE_FAILED)
            return reply
        self._note(RESULT_OK, None)
        return reply

    def _failed(self, reservation: str, usd: Decimal, code: str) -> None:
        """Settle after a failed call and write its row. A failing settle never hides the client's error."""
        try:
            self._meter.settle(reservation, usd)
        except Exception:  # noqa: BLE001 - the worst case stays booked; the caller sees the client's error
            code = CODE_SETTLE_FAILED
        self._note(RESULT_FAILED, code)

    def _enforced(
        self, messages: list[dict[str, Any]], documents: list[bytes] | None
    ) -> tuple[list[dict[str, Any]], list[bytes] | None] | None:
        """New lists holding what will be sent, or None when the step failed (then nothing is sent). A message
        or document in which nothing is replaced is passed on as the same object, so the bytes are the
        caller's; one with a replaced value is a new dict or new bytes. A content that is not `str` is refused
        with or without a map. Documents are read as the adapters read them (`llm/common.py` `turns`: UTF-8,
        bad bytes replaced)."""
        mapping = self._mapping
        try:
            sent: list[dict[str, Any]] = []
            for message in messages:
                content = message["content"] if isinstance(message, dict) else None
                if not isinstance(content, str):
                    return None
                if mapping is not None:
                    fixed = self._enforce(content, mapping)
                    if not isinstance(fixed, str):
                        return None
                    if fixed != content:
                        message = {**message, "content": fixed}
                sent.append(message)
            if documents is None:
                return sent, None
            docs: list[bytes] = []
            for document in documents:
                if not isinstance(document, bytes):
                    return None
                if mapping is not None:
                    text = document.decode("utf-8", "replace")
                    fixed = self._enforce(text, mapping)
                    if not isinstance(fixed, str):
                        return None
                    if fixed != text:
                        document = fixed.encode("utf-8")
                docs.append(document)
        except Exception:  # noqa: BLE001 - fail closed: a step that cannot finish means no call
            return None
        return sent, docs

    def _note(self, result: str, error_code: str | None) -> None:
        """One audit row: codes only. A missing, parking (None) or raising sink never changes the outcome."""
        if self._audit is None:
            return
        with contextlib.suppress(Exception):
            self._audit.write_outcome(
                AuditEvent(
                    run_id=self._run_id,
                    domain=AUDIT_DOMAIN,
                    operation=AUDIT_OPERATION,
                    principal=self._principal,
                    source=self._source,
                    result=result,
                    error_code=error_code,
                )
            )
