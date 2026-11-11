"""The producers of text that reaches a model, a vendor screen, a card, a log or a person that this registry covers, and the redaction function
each one calls. Data only: `tests/test_k5_producers.py` parses each function and fails when a producer stops calling
its function, when that function no longer reaches `runmap.redact_text` (the one choke point: NFKC, invisible
characters, JSON escapes, the layered decode to a fixed point, the size cap, then the pattern redactor), when a module
that calls a model (`.chat(` or `.apply_guardrail(`) is not listed, or when a message is cut with `[:N]` before it is
redacted. `tests/test_k5_round8.py` pushes a percent-, entity- and assignment-encoded secret through each producer.
Not covered: the ask-your-data demo's own ledger and command line (`OUTSIDE_THE_CHOKE_POINT`), and parsing of the
model's own reply (`k1b/loop.py` `parse_diagnosis`). Adding a producer means adding a row here and a driver in
`tests/test_k5_round9.py`."""

from __future__ import annotations

# (name, module path under hadavin_sdk, function name, the redaction functions any one of which the function calls)
PRODUCERS: tuple[tuple[str, str, str, frozenset[str]], ...] = (
    ("tool result", "tools.py", "prepare_output", frozenset({"redact_layered"})),
    ("tool result, redaction step", "tools.py", "redact_layered", frozenset({"redact_untrusted"})),
    ("tool error reason", "tools.py", "error_reason", frozenset({"redact_bounded"})),
    ("k1b case bundle", "k1b/redaction.py", "redact_bundle", frozenset({"redact_untrusted"})),
    ("k1b stored raw model output", "k1b/loop.py", "run_case", frozenset({"safe_head"})),
    ("evidence grounding", "runtime/evidence.py", "grounded", frozenset({"redact_text"})),
    ("evidence proposal inputs", "runtime/evidence.py", "validate", frozenset({"redact_value"})),
    (
        "document and model-written arguments",
        "runtime/agent_loop.py",
        "handle",
        frozenset({"redact_untrusted", "redact_value"}),
    ),
    ("judge input", "guard/judge.py", "check", frozenset({"redact_text"})),
    ("vendor guardrail input", "guard/bedrock_guardrail.py", "check", frozenset({"redact_text"})),
    (
        "injection screen log line",
        "guard/injection.py",
        "injection_check",
        frozenset({"safe_head"}),
    ),
    ("extract validation errors", "extract.py", "extract", frozenset({"safe_head"})),
    ("tick error message", "runtime/tick.py", "_message", frozenset({"safe_head"})),
    ("approval card text", "approvals/channel.py", "clean", frozenset({"redact_for_people"})),
    ("approval summary", "approvals/requests.py", "summary", frozenset({"clean"})),
    ("eval case document", "evals.py", "gate", frozenset({"redact_untrusted"})),
)

# The functions that stand for the choke point, and the function each must (transitively) reach.
CHOKE_FAMILY = {
    "redact_untrusted": "guard/runmap.py",
    "redact_bounded": "guard/runmap.py",
    "safe_head": "guard/runmap.py",
    "redact_value": "guard/runmap.py",
    "redact_layered": "tools.py",
    "clean": "approvals/channel.py",
    "redact_for_people": "approvals/channel.py",
}
CHOKE_POINT = "redact_text"

# Modules that call a model or a vendor screen (paths under `src/hadavin_sdk`, or `demos/...` from the repo root).
MODEL_CALLERS = frozenset(
    {
        "evals.py",
        "extract.py",
        "guard/judge.py",
        "guard/bedrock_guardrail.py",
        "k1b/loop.py",
        "runtime/agent_loop.py",
        "demos/ask-your-data/askdata/pipeline.py",
    }
)
# Callers whose model input is not produced by the redaction path, and why (reviewed: each is the user's own text).
OUTSIDE_THE_CHOKE_POINT = {
    "demos/ask-your-data/askdata/pipeline.py": "sends only the question the user typed plus a fixed prompt; no document, tool result or client record reaches the model",
    "k1b/loop.py": "sends the masked case bundle (`k1b case bundle` row masks every leaf) and tool results rendered from it",
}
