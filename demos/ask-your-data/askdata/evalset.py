"""Item schemas for the gold and adversarial sets, and the freeze file `lock.json` (design 12.1, 12.2, amendments A-02).

This module only DEFINES and loads the data; the items themselves are written elsewhere. `lock.json` holds the
SHA-256 of every set file, the gate thresholds (frozen BEFORE the dev set is frozen; the harness refuses a run if
they differ from the file), the sealed-run counter and the minimum remaining budget a sealed run needs.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import time
import uuid
from collections.abc import Callable, Iterator
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    StringConstraints,
    ValidationError,
    model_validator,
)

from askdata.settings import RUNTIME, Sealed

Hex64 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Tier = Literal["easy", "medium", "hard", "glossary", "ambiguous", "out_of_scope", "refuse"]


_SEALED = Sealed()  # the documented defaults live in settings.py


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Interpretation(_Strict):
    id: str
    label: str
    gold_sql: str
    assumption_key: str


class ExpectedHashes(_Strict):
    a: Hex64
    b: Hex64


class GoldItem(_Strict):
    id: str
    split: Literal["dev", "test"]
    tier: Tier
    kind: Literal["answerable", "ambiguous", "abstain", "refuse"]
    question: str
    gold_sql: str | None = None
    interpretations: list[Interpretation] = []
    expected_outcome: Literal["answered", "abstained", "refused"]
    order_matters: bool = False
    scale: list[int] | None = None
    expected_sha256: ExpectedHashes | None = (
        None  # result hash of the gold on each seed DB: a drift detector
    )
    authored_by: str = ""
    second_author_checked: bool = False
    notes: str = ""

    @model_validator(mode="after")
    def _shape(self) -> GoldItem:
        if self.kind == "answerable" and (not self.gold_sql or self.expected_outcome != "answered"):
            raise ValueError("an answerable item needs gold_sql and expected_outcome=answered")
        if self.kind == "ambiguous" and not self.interpretations:
            raise ValueError("an ambiguous item needs interpretations")
        if self.kind == "abstain" and self.expected_outcome != "abstained":
            raise ValueError("an abstain item expects abstained")
        if self.kind == "refuse" and self.expected_outcome != "refused":
            raise ValueError("a refuse item expects refused")
        return self


class AdversarialItem(_Strict):
    id: str
    group: Literal["direct_write", "restricted", "sql_trick", "data_injection", "resource_abuse"]
    question: str
    needs_llm: bool
    plant_ids: list[str] = []
    pass_rule: Literal[
        "refused_no_exec",
        "no_restricted_value",
        "no_unsafe_statement",
        "bounded_resources",
        "answers_match_clean",
    ]
    forbidden_strings: list[str] = []
    clean_pair_id: str | None = None

    @model_validator(mode="after")
    def _shape(self) -> AdversarialItem:
        if self.pass_rule == "answers_match_clean" and not self.clean_pair_id:  # noqa: S105
            raise ValueError("answers_match_clean needs clean_pair_id")
        return self


def load_jsonl[T: BaseModel](path: Path, model: type[T]) -> list[T]:
    """Strict load: a bad line, an unknown key or a duplicate id fails loudly."""
    items: list[T] = []
    for n, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            items.append(model.model_validate(json.loads(raw)))
        except (ValueError, ValidationError) as err:
            raise ValueError(f"{Path(path).name} line {n}: {type(err).__name__}") from None
    ids = [i.id for i in items]  # type: ignore[attr-defined]
    if len(set(ids)) != len(ids):
        raise ValueError(f"{Path(path).name}: duplicate item id")
    return items


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Thresholds(_Strict):
    green_max_upper: Decimal = (
        _SEALED.green_max_upper
    )  # one-sided 95 % upper bound of the confident-wrong rate
    amber_max_upper: Decimal = _SEALED.amber_max_upper


class Lock(_Strict):
    files: dict[str, Hex64]
    thresholds: Thresholds = Thresholds()
    test_runs: int = 0
    sealed_min_remaining_usd: Decimal = _SEALED.first_run_min_remaining_usd  # the FIRST sealed run
    second_look_min_remaining_usd: Decimal = (
        _SEALED.second_look_min_remaining_usd
    )  # a --second-look run (A-03)
    last_test_status: Literal["none", "complete", "aborted", "running", "unverified"] = "none"
    # "<config_hash>:<model_id>" of the last finished `eval run --split dev --live --smoke`; a sealed --live run needs
    # the SAME key (a changed prompt, config or model needs a new smoke run).
    smoke_key: str | None = None
    # Written BY HAND into lock.json after a defect in OUR harness or data is proved. It names the run folder the defect
    # was seen in and the gold/adversarial item id, and it is consumed by one `--second-look harness_defect`.
    harness_defect_reason: str | None = None
    harness_defect_run: str | None = None
    harness_defect_item: str | None = None
    # Mirrors of the sealed-run chain (sealed.py): the chain's last `sha`, and an HMAC over test_runs, smoke_key and
    # chain_head when a key is configured. `load()` replays the chain over them after a crash.
    chain_head: str | None = None
    core_hash: str | None = (
        None  # hash of everything but the seal and the hand-written fields, at the last commit
    )
    keyed: bool = (
        False  # the set was frozen with an HMAC key: a keyless gate is refused from then on
    )
    seal: str | None = None
    max_second_looks: int = (
        _SEALED.max_second_looks
    )  # sealed runs allowed beyond the first, however they are justified
    second_look_allowed_for: list[Literal["aborted", "harness_defect"]] = [
        "aborted",
        "harness_defect",
    ]


class LockError(RuntimeError):
    pass


def lock_path(eval_dir: Path) -> Path:
    return Path(eval_dir) / "lock.json"


def read_lock(eval_dir: Path) -> Lock:
    try:
        return Lock.model_validate_json(lock_path(eval_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        raise LockError(f"lock.json missing or invalid: {type(err).__name__}") from None


def write_lock(eval_dir: Path, lock: Lock) -> None:
    path = lock_path(eval_dir)
    tmp = _write_tmp(path, lock)
    for attempt in range(5):  # Windows refuses a replace while a reader holds the file open
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if attempt == 4:
                tmp.unlink(missing_ok=True)
                raise
            time.sleep(0.05)


def _write_tmp(path: Path, lock: Lock) -> Path:
    """The lock text in a uniquely named temp file next to `path` (two writers never share one)."""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(json.loads(lock.model_dump_json()), indent=2, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return tmp


@contextlib.contextmanager
def lock_guard(eval_dir: Path, wait_s: float = RUNTIME.lock_wait_s) -> Iterator[None]:
    """Exclusive OS lock across read lock.json -> decide -> write lock.json (the sealed counter's critical section)."""
    from askdata.meter import _try_lock, _unlock  # the same primitive the meter file uses

    Path(eval_dir).mkdir(parents=True, exist_ok=True)
    with open(lock_path(eval_dir).with_name("lock.json.lock"), "a+b") as f:
        deadline = time.monotonic() + wait_s
        while not _try_lock(f):
            if time.monotonic() > deadline:
                raise LockError("lock.json is busy (another eval run holds it)")
            time.sleep(0.01)
        try:
            yield
        finally:
            _unlock(f)


def freeze(
    eval_dir: Path,
    names: list[str],
    thresholds: Thresholds | None = None,
    *,
    no_clobber: bool = False,
    seal: Callable[[Lock], Lock] | None = None,
    lock_fields: dict | None = None,
) -> Lock:
    """Create lock.json from the current files (the freeze step; run once, before the dev set is frozen for use).
    `no_clobber`: write a temp file, then `os.link` it to lock.json, which fails if lock.json exists, so a crash never
    leaves an empty lock.json and an existing lock (with its sealed counter) is never replaced."""
    lock = Lock(
        files={n: sha256_file(Path(eval_dir) / n) for n in names},
        thresholds=thresholds or Thresholds(),
        **(lock_fields or {}),
    )
    if seal:
        lock = seal(lock)
    if not no_clobber:
        write_lock(eval_dir, lock)
        return lock
    path = lock_path(eval_dir)
    tmp = _write_tmp(path, lock)
    try:
        os.link(tmp, path)
    except FileExistsError:
        raise LockError("lock.json already exists") from None
    finally:
        tmp.unlink(missing_ok=True)
    return lock


def verify_files(eval_dir: Path, lock: Lock) -> list[str]:
    """Names of files that are missing or whose hash changed since the freeze (empty = intact)."""
    bad = []
    for name, digest in lock.files.items():
        p = Path(eval_dir) / name
        if not p.is_file() or sha256_file(p) != digest:
            bad.append(name)
    return bad
