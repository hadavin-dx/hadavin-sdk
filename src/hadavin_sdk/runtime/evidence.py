"""Evidence checks on a proposal (K5): it cites calls of its own run, and its identifier inputs are grounded.

* **Cited** (`uncited`): the proposal's `evidence` is a non-empty list of call ids that exist in this run.
* **Grounded** (`ungrounded`): each input the contract flags `identifier: true` (a resource name, an id, a
  revision) appears, compared in redacted (placeholder) form after normalisation, in at least one cited tool
  result or in the incident document. Free-text and enum inputs, and inputs not flagged, are not checked.

This catches a real call id cited for a wrong target name. It does not prove the diagnosis right: it is a
string match, no judge. `evidence` is stripped before the plan is built, so it is never a plan input, never on a
card and never graded.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from hadavin_sdk.actions.contract import ActionContract
from hadavin_sdk.guard import runmap
from hadavin_sdk.models import Run, ToolCall
from hadavin_sdk.registry import AgentRecord
from hadavin_sdk.store.protocol import Store

_NUMERIC = re.compile(r"(?:v|rev|revision|#)?\s*(\d+)")
# A value is found only as a whole token: not inside 10.0.0.17, deploy-17, 1.17, production, a path or an e-mail.
_BEFORE = r"(?<![\w.\-/:@])"
_AFTER = r"(?![\w\-/:@])(?!\.\w)"  # a full stop that ends a sentence is fine


@dataclass(frozen=True)
class Checked:
    call: ToolCall  # `evidence` removed
    cited: list[str]
    reason: str | None  # None: the proposal may go on; else the NEEDS_PERSON reason


Validator = Callable[[Run, AgentRecord, ActionContract, ToolCall, str, dict[str, str]], Checked]


def normalise(text: str) -> str:
    return unicodedata.normalize("NFC", text).casefold().strip()


def contains(text: str, value: str) -> bool:
    """`value` is in `text` after normalising both. A numeric id (`17`, `v17`, `REVISION 17`, `#17`) matches as a
    whole number, so `17` is not found inside `170`."""
    want = normalise(value)
    if not want:
        return False
    hay = normalise(text)
    if m := _NUMERIC.fullmatch(want):
        # `17` also matches `rev 17`, `v17` and `#17` in the text
        pattern = rf"{_BEFORE}(?:(?:v|rev|revision|#)\s?)?{re.escape(m.group(1))}{_AFTER}"
    else:
        pattern = rf"{_BEFORE}{re.escape(want)}{_AFTER}"
    return re.search(pattern, hay) is not None


def identifier_inputs(contract: ActionContract) -> list[str]:
    props = (contract.input_schema or {}).get("properties") or {}
    return [
        k for k, sub in props.items() if isinstance(sub, dict) and sub.get("identifier") is True
    ]


def grounded(
    contract: ActionContract,
    inputs: dict[str, Any],
    texts: list[str],
    mapping: dict[str, str],
) -> bool:
    for name in identifier_inputs(contract):
        value = inputs.get(name)
        if not isinstance(value, str):
            continue
        redacted = runmap.redact_text(
            value, mapping
        )  # a raw value the model typed is compared as placeholder
        if not any(contains(t, redacted) for t in texts):
            return False
    return True


def make_validator(store: Store) -> Validator:
    def validate(
        run: Run,
        agent: AgentRecord,
        contract: ActionContract,
        call: ToolCall,
        document: str,
        mapping: dict[str, str],
    ) -> Checked:
        inputs = dict(call.input)
        evidence = inputs.pop("evidence", None)
        # A raw value the model typed (an address, a name) is redacted before it can reach a plan, a card or an
        # executor; a placeholder it wrote is left as it is.
        inputs = runmap.redact_value(inputs, mapping)
        stripped = ToolCall(name=call.name, input=inputs)
        if (
            not agent.tools_allowed
        ):  # nothing was investigated: identifiers must come from the document
            ok = grounded(contract, inputs, [document], mapping)
            return Checked(stripped, [], None if ok else "ungrounded")
        # An ERROR result is not evidence: it cannot be cited, and it grounds nothing.
        rows = {c.call_id: c for c in store.list_tool_calls(run.run_id) if not c.error}
        if (
            not isinstance(evidence, list)
            or not evidence
            or not all(isinstance(e, str) and e in rows for e in evidence)
        ):
            return Checked(stripped, [], "uncited")
        cited = list(dict.fromkeys(evidence))
        texts = [rows[c].output for c in cited] + [document]
        ok = grounded(contract, inputs, texts, mapping)
        return Checked(stripped, cited, None if ok else "ungrounded")

    return validate
