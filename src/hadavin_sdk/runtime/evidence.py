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

import functools
import re
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass
from typing import Any

from hadavin_sdk.actions.contract import ActionContract
from hadavin_sdk.guard import runmap
from hadavin_sdk.models import Run, ToolCall
from hadavin_sdk.registry import AgentRecord
from hadavin_sdk.store.protocol import Store

_NUMERIC = re.compile(r"(?:v|rev|revision|#)?\s*(\d+)")
# A value is found only as a whole token: not inside 10.0.0.17, deploy-17, 1.17, production, a path or an e-mail.
# What may stand before it: nothing word-like; or the kind prefix kubectl prints (`deployment/checkout`,
# `pod/x`); or `key:` / `key=` (`addr:10.0.0.5`, `host=db`); or a URL scheme (`http://10.0.0.5/health`).
_KUBECTL_KINDS = (
    "deployment.apps", "deployment", "statefulset", "daemonset", "replicaset", "cronjob", "configmap",
    "ingress", "service", "svc", "namespace", "pods", "pod", "node", "job", "ns", "sts", "ds", "rs", "cm", "hpa",
)  # fmt: skip
_BEFORE = (
    r"(?:(?<![\w.\-/:@])|(?<=://)|(?<=[A-Za-z]:)|(?<=[A-Za-z]=)"
    + "".join(rf"|(?<=\b{k}/)" for k in _KUBECTL_KINDS)
    + ")"
)
# What may follow a NAME: a WHOLE token ends at `:` or `/` (a port, a path), a space or punctuation; not at a
# word character, `-`, `.`+word or `@`. `payments` is not found in `payments-canary`, `prod` not in `prod-db`: the
# front of a longer name counts only when the tool's manifest declares its generated suffix (`generated_suffix`).
_AFTER_NAME = r"(?![\w\-@])(?!\.\w)"
_AFTER = r"(?![\w\-@])(?!\.\w)"  # a full stop that ends a sentence is fine


@dataclass(frozen=True)
class Checked:
    call: ToolCall  # `evidence` removed
    cited: list[str]
    reason: str | None  # None: the proposal may go on; else the NEEDS_PERSON reason


Validator = Callable[[Run, AgentRecord, ActionContract, ToolCall, str, dict[str, str]], Checked]


def normalise(text: str) -> str:
    return runmap.canonical(text).casefold().strip()


# The value being looked for is NEVER put into a regular expression: `re` keeps every pattern it compiles in a
# process-wide cache, and a client's identifier must not outlive its run in memory shared with other clients (R371).
# The patterns below are static; the value is found with `str.find` and the context is checked around the hit.
_BEFORE_RE = re.compile(_BEFORE + r"\Z")
_AFTER_NAME_RE = re.compile(_AFTER_NAME)
_AFTER_RE = re.compile(_AFTER)
_NUM_TOKEN = re.compile(r"(?:(?:v|rev|revision|#)\s?)?(\d+)")
_LOOKBEHIND = (
    48  # the longest thing `_BEFORE` looks back over (`deployment.apps/`) with room to spare
)


def _before_ok(hay: str, pos: int) -> bool:
    return _BEFORE_RE.search(hay[max(0, pos - _LOOKBEHIND) : pos]) is not None


@functools.lru_cache(maxsize=64)
def _suffix_rx(suffix: str) -> re.Pattern[str]:
    """A tool's declared `generated_suffix` (operator configuration, never client data)."""
    return re.compile(suffix)


def contains(text: str, value: str, *, casefold: bool = False, suffix: str | None = None) -> bool:
    """`value` is in `text` as a WHOLE token, compared exactly (case included) unless `casefold`. A numeric id
    (`17`, `v17`, `REVISION 17`, `#17`) matches as a whole number, so `17` is not found inside `170`, and numbers
    ignore case. A name followed by `suffix` (a restricted pattern the tool's manifest declares for a generated
    suffix, such as a pod's `-7f9d8c6b4-xk2lp`) also counts; without one a name never matches the front of a
    longer one."""
    want = runmap.canonical(value).strip()
    hay = runmap.canonical(text)
    if not want:
        return False
    if m := _NUMERIC.fullmatch(want.casefold()):
        digits, low = m.group(1), hay.casefold()
        return any(
            t.group(1) == digits and _before_ok(low, t.start()) and _AFTER_RE.match(low, t.end())
            for t in _NUM_TOKEN.finditer(low)
        )
    if casefold:
        want, hay = want.casefold(), hay.casefold()
    tail = _suffix_rx(suffix) if suffix else None
    i = hay.find(want)
    while i != -1:
        j = i + len(want)
        if _before_ok(hay, i):
            if _AFTER_NAME_RE.match(hay, j):
                return True
            if (
                tail is not None
                and (t := tail.match(hay, j))
                and _AFTER_NAME_RE.match(hay, t.end())
            ):
                return True
        i = hay.find(want, i + 1)
    return False


_EVIDENCE_FIELD = {
    "type": "array",
    "items": {"type": "string"},
    "description": "The call_id of every tool result your proposal rests on.",
}


def with_evidence(schema: dict[str, Any]) -> dict[str, Any]:
    """The schema the model sees for an action tool of a tooled agent: `evidence` is required (K5). The stored
    contract is untouched: `evidence` is stripped from the proposal before the plan is built. The runtime and
    `evals.gate` both offer exactly this."""
    props = {**(schema.get("properties") or {}), "evidence": _EVIDENCE_FIELD}
    required = [*schema.get("required", []), "evidence"]
    return {**schema, "properties": props, "required": list(dict.fromkeys(required))}


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
    *,
    casefold: bool = False,
    suffixes: list[str | None] | None = None,
) -> bool:
    for name in identifier_inputs(contract):
        value = inputs.get(name)
        if not isinstance(value, str):
            continue
        if (
            runmap.canonical(value) != value
        ):  # the value the executor gets is the one that is compared
            return False
        redacted = runmap.redact_text(
            value, mapping
        )  # a raw value the model typed is compared as placeholder
        if not any(
            contains(t, redacted, casefold=casefold, suffix=(suffixes[i] if suffixes else None))
            for i, t in enumerate(texts)
        ):
            return False
    return True


def make_validator(
    store: Store,
    *,
    suffixes: Mapping[str, str] | None = None,
    case_insensitive_targets: Collection[str] = (),
) -> Validator:
    """`suffixes`: tool name -> the `generated_suffix` its manifest declares. `case_insensitive_targets`: the
    `target_system` labels whose names are compared without case."""
    suffix_of = dict(suffixes or {})

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
        declared = (contract.input_schema or {}).get("properties") or {}
        if agent.tools_allowed and any(k not in declared for k in inputs):
            # grounding looks only at declared inputs: an undeclared key would ride into the plan unchecked
            return Checked(ToolCall(name=call.name, input={}), [], "invalid_proposal")
        # A raw value the model typed (an address, a name) is redacted before it can reach a plan, a card or an
        # executor; a placeholder it wrote is left as it is.
        inputs = runmap.redact_value(inputs, mapping)
        stripped = ToolCall(name=call.name, input=inputs)
        if (
            not agent.tools_allowed
        ):  # nothing was investigated: identifiers must come from the document
            ok = grounded(
                contract,
                inputs,
                [document],
                mapping,
                casefold=contract.target_system in case_insensitive_targets,
            )
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
        tails: list[str | None] = [suffix_of.get(rows[c].tool) or None for c in cited] + [None]
        ok = grounded(
            contract,
            inputs,
            texts,
            mapping,
            casefold=contract.target_system in case_insensitive_targets,
            suffixes=tails,
        )
        return Checked(stripped, cited, None if ok else "ungrounded")

    return validate
