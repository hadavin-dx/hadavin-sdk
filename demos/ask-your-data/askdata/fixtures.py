"""Fixture builder for the core `FakeLLM` (design 8.4): NOT a recorder, it never needs a key or a network.

A test (or the offline demo) declares the replies it wants for a question; the builder computes the digest the fake
model looks up, `sha256(json.dumps(messages, sort_keys=True))`, from the very same `llm_io.build_messages` the
pipeline uses, including the retry feedback (the validator's rule hint or the SQLSTATE hint of the step before).
Whenever the prompt, catalog, glossary or a question changes the digests change: rebuild the fixtures
(`fixtures_current` is the check CI can run).
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from askdata import llm_io
from askdata.policy import decide, rule_hint
from askdata.validate import RULES, Rejected, validate
from hadavin_sdk.config import Route

ROUTE = Route(
    model_id="fake-model-1", input_usd_per_mtok="2", output_usd_per_mtok="10", max_tokens=1024
)  # type: ignore[arg-type]


@dataclass(frozen=True)
class Step:
    """One scripted model reply. Exactly one of `sql`, `abstain` or `raw` shapes it."""

    sql: str | None = None
    abstain: str | None = None  # an abstain_reason
    clarify: str | None = None
    assumptions: tuple[str, ...] = ()
    raw: dict[str, Any] | None = None  # verbatim Reply fields, e.g. a text-only or cut-off answer
    fails_with: str | None = (
        None  # the SQLSTATE the database will return for this reply (decides the next hint)
    )
    tokens: tuple[int, int] = (1000, 100)
    extras: dict[str, Any] = field(default_factory=dict)

    def reply(self) -> dict[str, Any]:
        if self.raw is not None:
            data = {"text": "", "tool_calls": [], "stop_reason": "end_turn", **self.raw}
        else:
            body: dict[str, Any] = {
                "decision": "abstain" if self.abstain else "answer",
                "assumptions": list(self.assumptions),
            }
            if self.abstain:
                body.update(abstain_reason=self.abstain, clarifying_question=self.clarify)
            else:
                body["sql"] = self.sql
            data = {
                "text": "",
                "tool_calls": [{"name": "submit_answer", "input": body | self.extras}],
                "stop_reason": "tool_use",
            }
        return {
            **data,
            "input_tokens": self.tokens[0],
            "output_tokens": self.tokens[1],
            "latency_ms": 5,
        }


def digest(messages: list[dict[str, Any]]) -> str:
    return hashlib.sha256(json.dumps(messages, sort_keys=True).encode("utf-8")).hexdigest()


def write_script(
    recorded_dir: Path, part_a: str, question: str, steps: list[Step], validator: Any = validate
) -> list[str]:
    """Write one recording per step; returns the digests. The builder walks the same retry path the pipeline will."""
    recorded_dir = Path(recorded_dir)
    recorded_dir.mkdir(parents=True, exist_ok=True)
    prev: str | None = None
    hint: str | None = None
    out = []
    for step in steps:
        key = digest(llm_io.build_messages(part_a, question, prev, hint))
        n = len(list(recorded_dir.glob(f"{key}-*.json"))) + 1
        (recorded_dir / f"{key}-{n}.json").write_text(
            json.dumps(step.reply(), sort_keys=True), encoding="utf-8", newline="\n"
        )
        out.append(key)
        prev, hint = _next(step, validator)
    return out


def _next(step: Step, validator: Any) -> tuple[str | None, str | None]:
    if step.sql is None:
        return None, llm_io.SCHEMA_HINT
    try:
        validator(step.sql)
    except Rejected as rej:
        return step.sql, rule_hint(rej.rule, RULES)
    if step.fails_with is not None:
        dec = decide(step.fails_with)
        return step.sql, dec.hint
    return step.sql, None


def fixtures_current(recorded_dir: Path, build: Any) -> bool:
    """True if rebuilding into an empty folder with `build(dir)` gives exactly the files in `recorded_dir`."""
    with tempfile.TemporaryDirectory() as tmp:
        build(Path(tmp))
        fresh = {p.name: p.read_bytes() for p in Path(tmp).glob("*.json")}
    have = {p.name: p.read_bytes() for p in Path(recorded_dir).glob("*.json")}
    return fresh == have
