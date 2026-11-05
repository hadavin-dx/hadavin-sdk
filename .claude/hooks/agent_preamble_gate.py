"""PreToolUse hook for the Agent tool: general-purpose subagents must carry the studio preamble AND the EGM gate.

Denies (exit 0 + permissionDecision=deny) a spawn of general-purpose / claude / unspecified agent types whose
prompt is >= 300 chars and lacks the preamble marker or the EGM-GATE marker (rule 13 of the preamble), a spawn with no explicit model
(opus, sonnet or haiku; the gate never picks the model, so quality stays the lead's choice), and a spawn
of a general-purpose agent that is worded as an independent review (reviews must use the egm:* reviewer agents; a
general-purpose agent may only be an EVIDENCE RUNNER). Never blocks on its own failure (fail open: a broken hook
must not stop all work); the failure is written to stderr.
"""
import json
import re
import sys
from pathlib import Path

MARKER = "STUDIO-PREAMBLE v1"
EGM_MARKER = "EGM-GATE v1"
RUNNER_MARKER = "EVIDENCE RUNNER"
PREAMBLE = "handover/BRIEF-PREAMBLE.md"
ALLOWED_PREFIXES = ("egm:", "caveman:")
ALLOWED_TYPES = {"explore", "plan", "web-fetch", "claude-code-guide", "statusline-setup"}
GATED_TYPES = {"", "general-purpose", "claude"}
MIN_PROMPT = 300
VALID_MODELS = {"opus", "sonnet", "haiku"}
# A brief that asks a general-purpose agent to act as an independent reviewer (instead of an egm:* agent).
REVIEW_BRIEF = re.compile(
    r"(fresh,?\s+independent[^.]{0,80}review|independent\s+(adversarial\s+)?review\s*\(read-?only|"
    r"^\s*TASK:\s*FRESH)",
    re.IGNORECASE | re.MULTILINE,
)


def decide(payload: dict) -> str | None:
    """Return a deny reason, or None to allow."""
    tool_input = payload.get("tool_input") or {}
    kind = str(tool_input.get("subagent_type") or "").strip().lower()
    prompt = str(tool_input.get("prompt") or "")
    if kind.startswith(ALLOWED_PREFIXES) or kind in ALLOWED_TYPES:
        return None
    if kind not in GATED_TYPES:
        return None
    if len(prompt) < MIN_PROMPT:
        return None
    if MARKER not in prompt:
        return (
            f"Studio rule: this subagent brief must start with the contents of {PREAMBLE} "
            f"(first line '{MARKER}'). Read that file, prepend it to the prompt, then spawn again."
        )
    if EGM_MARKER not in prompt:
        return (
            f"Studio rule (EGM gate, owner 2026-11-01): this brief lacks '{EGM_MARKER}' (rule 13 of {PREAMBLE}). "
            "Re-read the preamble file: it now has rule 13, the EGM sequence every agent must follow."
        )
    if str(tool_input.get("model") or "").strip().lower() not in VALID_MODELS:
        return (
            "Studio rule (model routing, owner 2026-11-04): set the Agent 'model' explicitly "
            "('opus', 'sonnet' or 'haiku'). Without it the agent silently inherits the lead's model. "
            "Quality first: pick the strongest model the job justifies; 'opus' is always accepted. "
            "This gate never picks a weaker model for you."
        )
    if REVIEW_BRIEF.search(prompt) and RUNNER_MARKER not in prompt:
        return (
            "Studio rule (EGM gate): reviews must be run by the egm:* reviewer agents "
            "(egm:egm-design, egm:egm-codebase-details, egm:egm-implementation-readiness, egm:egm-structural, "
            "egm:egm-style, egm:egm-comprehension, egm:egm-zoom-out) or the Skill egm:egm-review-loop / egm:egm-review. "
            "A general-purpose agent may only be an 'EVIDENCE RUNNER' (it runs tests and records raw output; write "
            "'EVIDENCE RUNNER' in the brief). Re-brief it as an evidence runner, then spawn the egm:* reviewers on its output."
        )
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        reason = decide(payload)
    except Exception as exc:  # fail open
        print(f"agent_preamble_gate: {exc!r}", file=sys.stderr)
        return 0
    if reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
