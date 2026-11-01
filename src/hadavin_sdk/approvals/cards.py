"""Cards a person reads but does not run: the shadow card and the abstain card.

Pure renderers. The text is template-built from the plan and the run, never by the model (the diagnosis is
quoted, cleaned and screened), and it holds no command. ``blocks`` is channel-neutral (text and buttons); each
channel kind turns it into its own markup, so no channel vocabulary lives here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.approvals.requests import WARNING
from hadavin_sdk.guard.injection import Detector, injection_check
from hadavin_sdk.models import GateDecision, Plan, canonical_json, sha256_hex

SHADOW_HEADER = "Agent's view: not checked, do not run"
ABSTAIN_HEADER = "Agent abstained: here is what it looked at"
LABELS = ("agree", "partial", "wrong", "harmful")  # parsed by K6
ABSTAIN_LABELS = (
    ("abstain_ok", "Fine to abstain"),
    ("should_have_answered", "Should have answered"),
)


@dataclass(frozen=True)
class Card:
    text: str
    blocks: list[dict[str, Any]]
    display_hash: str  # sha256 of the text


@dataclass(frozen=True)
class Delivery:
    ok: bool
    ref: str | None = None  # the channel's message id, kept for threads and updates
    reason: str | None = None  # card_too_long, or a short code; never the card


_WOULD_BE = {
    "class.read_only": "If suggested: would be refused in this release (read-only actions are tools)",
    "class.reversible": "If suggested: needs one approval",
    "scope.agent": "Would be refused: action not allowed for this agent or requester",
    "scope.principal": "Would be refused: action not allowed for this agent or requester",
    "input.schema": "Would be refused: inputs fail the contract's schema",
}
_SIGN_OFF = "If suggested: needs sign-off by a person with step-up (not available in this release)"


def would_be_text(rule_id: str) -> str:
    if rule_id.startswith("class.sign_off."):
        return _SIGN_OFF
    return _WOULD_BE.get(rule_id, f"Would be refused: {rule_id}")


def _card(text: str, buttons: list[dict[str, str]]) -> Card:
    text = clean(text)
    blocks: list[dict[str, Any]] = [{"kind": "text", "text": text}]
    if buttons:
        blocks.append({"kind": "buttons", "buttons": buttons})
    return Card(text=text, blocks=blocks, display_hash=sha256_hex(text))


def render_shadow(
    plan: Plan,
    decision: GateDecision,
    cited: list[str],
    *,
    diagnosis: str = "",
    detector: Detector | None = None,
) -> Card:
    """The shadow card. No command is shown: the action and its inputs are fields. ``injection_check`` of the
    diagnosis, not ``summary()``, whose "asks to run" wording clashes with "do not run"."""
    flagged = (
        detector is not None
        and bool(diagnosis)
        and injection_check(detector, diagnosis, "shadow_card").flagged
    )
    lines = [
        SHADOW_HEADER,
        *([WARNING.strip()] if flagged else []),
        f"Diagnosis: {diagnosis or '(none given)'}",
        f"Proposed action: {plan.action_id} v{plan.action_version} on {plan.target.system}",
        f"Inputs: {canonical_json(plan.inputs)}",
        f"Expected: {plan.expected_outcome}",
        f"Evidence (call ids): {', '.join(cited) or 'none'}",
        would_be_text(decision.rule_id),
        f"Plan {plan.hash()[:12]}.",
    ]
    buttons = [
        {"id": f"label_{x}", "label": x.capitalize(), "value": f"label|{plan.run_id}|{x}"}
        for x in LABELS
    ]
    return _card("\n".join(lines), buttons)


def render_abstain(run_id: str, reason: str, cited: list[str]) -> Card:
    """Posted for every run that ends without a plan, so a missed incident can be labelled."""
    lines = [
        ABSTAIN_HEADER,
        f"Reason: {reason}",
        *(f"- {c}" for c in cited),
        *([] if cited else ["- no calls were made"]),
    ]
    buttons = [
        {"id": f"label_{k}", "label": label, "value": f"label|{run_id}|{k}"}
        for k, label in ABSTAIN_LABELS
    ]
    return _card("\n".join(lines), buttons)
