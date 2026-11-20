"""The model gate: one wrapper around the model client (step F).

Before any provider contact it checks that every message and document is already masked with the caller's run
map, then reserves the worst-case cost. After the call it settles the real cost and writes one audit row. If the
check or the reservation fails, no call is made. It holds no money logic and no redaction logic of its own:
masking is `guard/runmap.py`, money is the meter, audit is the sink. It only orders the steps.

Not checked: `system` and `tools` (operator text). No logger, no module-level state, and no message text, no
exception text and no exception chain in any audit row or in any exception raised here.
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
MaskCheck = Callable[
    [str, Mapping[str, str]], bool
]  # True = already masked; any raise = not masked

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
    """A message or document is not masked with the caller's run map, or the check itself failed."""

    code = CODE_MASK_REFUSED


class ModelGate:
    """Holds the client, the meter, the audit sink, the worst-case function and the mask check. It has NO
    `chat`: a caller must `bind` it to an agent and a run first, so an unbound gate cannot call a model.
    A client that is already a gate is refused (TypeError): one call must never be reserved twice."""

    def __init__(
        self,
        llm: LLM,
        *,
        meter: Meter,
        audit: AuditSink | None,
        worst_case: WorstCase,
        mask_check: MaskCheck = runmap.is_masked,
    ) -> None:
        if isinstance(llm, ModelGate | BoundGate):
            raise TypeError("the client is already a model gate")
        self._llm, self._meter, self._audit = llm, meter, audit
        self._worst_case, self._mask_check = worst_case, mask_check

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
        written): values the run masks later are known to the next call. None (a site with no run map) means
        "check that no unmasked pattern is present". `principal` defaults to the agent id."""
        return BoundGate(self, agent_id, run_id, mapping, principal or agent_id, source)


class BoundGate:
    """Satisfies `llm.protocol.LLM`. Order: mask check, reserve, provider call, settle, audit row."""

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
        self._worst_case, self._mask_check = gate._worst_case, gate._mask_check
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
        if not self._all_masked(messages, documents):
            self._note(RESULT_REFUSED, CODE_MASK_REFUSED)
            raise UnmaskedInput  # raised outside any `except`: no cause and no context to leak
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
        except (
            BaseException
        ):  # the process is going down: cost unknown, the sweep closes the reservation
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

    def _all_masked(self, messages: list[dict[str, Any]], documents: list[bytes] | None) -> bool:
        """True only when every message content and every document, as it will be sent, is masked. Anything
        the check cannot read (a content that is not `str`, a failing redactor, a text over the cap) is NOT
        masked. Documents are decoded as the adapters decode them (`llm/common.py` `turns`)."""
        mapping = {} if self._mapping is None else self._mapping
        try:
            for message in messages:
                content = message["content"]
                if not isinstance(content, str) or not self._mask_check(content, mapping):
                    return False
            for document in documents or []:
                if not self._mask_check(document.decode("utf-8", "replace"), mapping):
                    return False
        except Exception:  # noqa: BLE001 - fail closed: a check that cannot finish is a refusal
            return False
        return True

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
