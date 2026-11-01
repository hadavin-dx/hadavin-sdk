"""Replay records: ``replay-records.jsonl``, a file separate from ``qualified.jsonl``.

K3 creates the model and the reader; K1b-full adds the writer. Only the load-time ``suggest`` refusal
(``deferred``) and, from K6, ``promote-check`` read this file. ``assert_qualified`` and ``qualified_runs`` never
do: a replay run's bundle hash can never match a gate run's golden hash, and that function stays untouched
(``tests/test_k3_pilot.py::test_replay_records_not_read_by_assert_qualified``).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, ValidationError

from hadavin_sdk.errors import ConfigError

if TYPE_CHECKING:
    from hadavin_sdk.registry import Registry

FILE = "replay-records.jsonl"
MIN_K = 3
_LOG = logging.getLogger("hadavin_sdk.replay_records")


class ReplayRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = 1
    agent_id: str
    config_hash: str
    model_id: str
    prompt_sha256: str
    bundle_sha256: str
    k: int
    pass_k: float
    pass_rate: float
    upper_error_bound: float | None = None
    threshold: float
    green: bool  # pass_k >= threshold
    ts: datetime


def read_records(root: Path) -> list[ReplayRecord]:
    """Every readable line; a torn line qualifies nothing, a line of the wrong shape fails closed."""
    path = root / FILE
    if not path.exists():
        return []
    out = []
    lines = path.read_bytes().splitlines()
    last = max((i for i, ln in enumerate(lines, 1) if ln.strip()), default=0)
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except ValueError as exc:
            if i != last:  # only the final line can be a torn append
                raise ConfigError(f"{FILE} line {i}: not valid JSON") from exc
            _LOG.warning("%s line %d is not valid JSON (torn append): skipped", FILE, i)
            continue
        try:
            out.append(ReplayRecord.model_validate(data))
        except ValidationError as exc:
            raise ConfigError(f"{FILE} line {i}: not a replay record this version reads") from exc
    return out


def has_green_record(registry: Registry, agent_id: str) -> bool:
    """A green record with pass^k at k >= 3 exists for the agent's current config hash, model and prompt.
    A later gate run never hides it (the gate writes ``qualified.jsonl``, not this file)."""
    agent = registry.agents[agent_id]
    want = (
        agent_id,
        registry.config_hash(agent_id),
        registry.config.routes[agent.model_route].model_id,
        registry.prompt_sha256(agent_id),
    )
    threshold = registry.config.eval_threshold
    return any(
        (r.agent_id, r.config_hash, r.model_id, r.prompt_sha256) == want
        and r.k >= MIN_K
        and r.pass_k
        >= threshold  # recomputed: the record's own green and threshold are not trusted
        for r in read_records(registry.config.root)
    )
