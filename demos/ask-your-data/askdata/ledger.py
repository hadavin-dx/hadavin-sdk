"""The query ledger (amendments A-13): one JSON object per line, UTF-8, keys sorted, ASCII-escaped, append-only.

Every text field passes `clean()` at validation (so what is stored can never carry a terminal escape); hashes are
computed over the raw question before cleaning. A torn tail (a crash mid-append) is closed off by the next append
and skipped on read. The SHA-256 of a line's exact bytes (without the newline) is its identity: the audit outcome
event carries it in `result`.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
)

from askdata.policy import Alarm, ReasonCode
from askdata.safe_text import clean

SCHEMA = "askdata.ledger/1"

Text = Annotated[str, BeforeValidator(lambda v: clean(v) if isinstance(v, str) else v)]
Hex64 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Stamp = Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")]
Money = Annotated[str, StringConstraints(pattern=r"^\d+(\.\d+)?$")]
QueryId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{32}$")]
RuleId = Annotated[str, StringConstraints(pattern=r"^V(0[1-9]|1[0-2])$")]
Count = Annotated[int, Field(ge=0)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ProfileDrop(_Strict):
    column: Text
    reason: Literal["length", "charset", "injection"]
    value_sha256: Hex64  # the dropped value itself is never stored


class Attempt(_Strict):
    n: Annotated[int, Field(ge=1)]
    kind: Literal["generate", "agreement_candidate"] = "generate"
    schema_ok: bool
    sql_text: Annotated[Text, Field(max_length=4000)] | None = None
    validator_rule: RuleId | None = None
    canonical_sql: Annotated[Text, Field(max_length=4000)] | None = None
    sql_sha256: Hex64 | None = None
    intent_event_id: str | None = None
    executed: bool = False
    sqlstate: Annotated[str, Field(min_length=5, max_length=5)] | None = None
    sqlstate_class: Annotated[str, Field(min_length=2, max_length=2)] | None = None
    rows: Count | None = None
    truncated: bool | None = None
    duration_ms: Count = 0
    tokens_in: Count = 0
    tokens_out: Count = 0
    cost_usd: Money = "0"


class Final(_Strict):
    sql_sha256: Hex64
    canonical_sql: Annotated[Text, Field(max_length=4000)]
    wire_sha256: Hex64
    result_sha256: Hex64
    row_count: Count
    truncated: bool


class Budget(_Strict):
    spent_usd: Money
    cap_usd: Money


class LedgerLine(_Strict):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    schema_: Literal["askdata.ledger/1"] = Field(SCHEMA, alias="schema")
    query_id: QueryId
    ts: Stamp
    asker: Annotated[Text, Field(max_length=64)]
    question: Annotated[Text, Field(max_length=500)] | None
    question_sha256: Hex64
    outcome: Literal["answered", "abstained", "refused", "failed"]
    reason_code: ReasonCode | None = None
    rule_id: RuleId | None = None
    attempts: Annotated[list[Attempt], Field(max_length=6)] = []
    final: Final | None = None
    assumptions: list[Annotated[Text, Field(max_length=300)]] = []
    profile_drops: list[ProfileDrop] = []
    intent_event_ids: list[str] = []
    prompt_sha256: Hex64
    config_hash: Hex64
    catalog_sha256: Hex64
    model_id: Text
    route: Text
    tokens_in: Count = 0
    tokens_out: Count = 0
    cost_usd: Money = "0"
    latency_ms: Count = 0
    budget: Budget
    alarm: list[Alarm] = []


def utc_stamp(now: datetime | None = None) -> str:
    return (now or datetime.now(UTC)).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def dump(line: LedgerLine) -> bytes:
    """The exact bytes of a line (no newline): sorted keys, no spaces, ASCII only."""
    obj = line.model_dump(mode="json", by_alias=True)
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def line_sha256(line: LedgerLine) -> str:
    return hashlib.sha256(dump(line)).hexdigest()


@dataclass(frozen=True)
class Stored:
    line: LedgerLine
    sha256: str  # of the exact stored bytes
    number: int  # 1-based physical line number


@dataclass(frozen=True)
class ReadResult:
    items: list[Stored]
    bad: list[int]  # physical line numbers that are torn or do not validate


class QueryLedger:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def append(self, line: LedgerLine) -> str:
        """Write one line (flush and fsync before returning) and return its SHA-256."""
        data = dump(line)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        torn = self.path.exists() and self.path.stat().st_size > 0 and not self._ends_with_newline()
        with open(self.path, "ab") as f:
            f.write(
                (b"\n" if torn else b"") + data + b"\n"
            )  # a torn tail becomes a line of its own
            f.flush()
            os.fsync(f.fileno())
        return hashlib.sha256(data).hexdigest()

    def _ends_with_newline(self) -> bool:
        with open(self.path, "rb") as f:
            f.seek(-1, os.SEEK_END)
            return f.read(1) == b"\n"

    def read(self) -> ReadResult:
        items, bad = [], []
        if not self.path.exists():
            return ReadResult(items, bad)
        raw = self.path.read_bytes().split(b"\n")
        if raw and raw[-1] == b"":
            raw.pop()
        for number, data in enumerate(raw, start=1):
            if not data.strip():
                continue
            try:
                line = LedgerLine.model_validate(json.loads(data.decode("ascii")))
            except (ValueError, ValidationError):
                bad.append(number)
                continue
            items.append(Stored(line, hashlib.sha256(data).hexdigest(), number))
        return ReadResult(items, bad)
