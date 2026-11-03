"""Every producer of text that reaches a model, a card, a log or a person, and the redaction choke point each one
goes through. Data only: `tests/test_k5_producers.py` parses each function and fails when a producer stops calling its
choke point, when a module that calls a model (`.chat(`) is not listed, or when a message is cut with `[:N]` before it
is redacted. Adding a producer means adding a row here (and a test that the row is true)."""

from __future__ import annotations

# (name, module path under hadavin_sdk, function name, the choke points any one of which the function calls)
PRODUCERS: tuple[tuple[str, str, str, frozenset[str]], ...] = (
    ("tool result", "tools.py", "prepare_output", frozenset({"redact_layered"})),
    ("tool result, layered view", "tools.py", "redact_layered", frozenset({"redact_untrusted"})),
    ("tool error reason", "tools.py", "error_reason", frozenset({"redact_layered"})),
    ("k1b case bundle", "k1b/redaction.py", "redact_bundle", frozenset({"redact_layered"})),
    ("evidence grounding", "runtime/evidence.py", "grounded", frozenset({"redact_text"})),
    ("evidence proposal inputs", "runtime/evidence.py", "validate", frozenset({"redact_value"})),
    (
        "document and model-written arguments",
        "runtime/agent_loop.py",
        "handle",
        frozenset({"redact_untrusted", "redact_value"}),
    ),
    ("judge input", "guard/judge.py", "check", frozenset({"redact_text"})),
    (
        "injection screen log line",
        "guard/injection.py",
        "injection_check",
        frozenset({"safe_head"}),
    ),
    ("extract validation errors", "extract.py", "extract", frozenset({"safe_head"})),
    ("tick error message", "runtime/tick.py", "_message", frozenset({"safe_head"})),
    ("approval card text", "approvals/channel.py", "clean", frozenset({"redact_text"})),
    ("eval case document", "evals.py", "gate", frozenset({"redact_untrusted"})),
)

# Modules that call a model. Each is covered by a row above: k1b/loop.py sends only the masked bundle (`k1b case bundle`).
MODEL_CALLERS = frozenset(
    {"evals.py", "extract.py", "guard/judge.py", "k1b/loop.py", "runtime/agent_loop.py"}
)
