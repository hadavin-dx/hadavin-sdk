"""The sealed-run gate: the ONE place that decides how often the sealed test set was touched and records it.

Bug class this closes: a counter or guard that lives in a plain editable file, written before the work and cleared
only on the happy path. The standard remedies, as used here:

* Write-ahead log with replay (as in databases): every state change is FIRST appended to `sealed-chain.jsonl`
  (`sealed_run`, `sealed_done`, `smoke_pass`, `reconcile`), THEN mirrored into lock.json together with the chain head.
  A crash between the two leaves the chain ahead of the lock; `load()` replays the entries the lock has not seen and
  rewrites it (and logs a `reconcile` entry). Nothing is left in a half state that needs a human.
* Status is DERIVED, never stored as a promise: a run that was started and never reported `sealed_done` is judged by
  the run folder (`report.json` exists means its own verdict, absent means aborted). A killed process cannot leave
  "aborted" standing over results that were written.
* Hash chain with an HMAC key (RFC 2104) when `sealed_key_secret_name` is configured: each line carries
  HMAC-SHA256(key, seq, kind, data, prev). Without the key nobody can forge or re-hash a line, and lock.json carries
  a `seal` = HMAC(key, test_runs, smoke_key, chain_head), so editing `test_runs` or `chain_head` is detected.
  The key comes from the secrets kind, never from a file in the repo.

What this still does NOT stop, stated plainly:
* With NO key configured the chain is a plain SHA-256 chain: anyone who can write the audit folder can recompute it. It
  then only catches accidents and single-line edits. Configure the key for a client run.
* Rollback: putting back an older, internally consistent pair of lock.json and chain (a restore from backup, or a
  copy) shows an older state. Only git history of lock.json (commit it after every sealed run) and an off-machine
  copy of the chain's last `sha` can tell. The chain also lives on the same disk as the code that checks it.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from askdata.evalset import Lock, LockError, read_lock, write_lock

GENESIS = "0" * 64
KINDS = ("sealed_run", "sealed_done", "smoke_pass", "reconcile")
MIN_KEY_CHARS = 16


def _mac(key: bytes | None, seq: int, kind: str, data: dict, prev: str) -> str:
    body = json.dumps(
        {"seq": seq, "kind": kind, "data": data, "prev": prev},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return (
        hmac.new(key, body, hashlib.sha256).hexdigest() if key else hashlib.sha256(body).hexdigest()
    )


def seal_of(key: bytes | None, lock: Lock) -> str | None:
    """HMAC over the lock fields the chain governs; None when no key is configured."""
    if not key:
        return None
    body = json.dumps(
        {"test_runs": lock.test_runs, "smoke_key": lock.smoke_key, "chain_head": lock.chain_head},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hmac.new(key, b"lock:" + body, hashlib.sha256).hexdigest()


class Chain:
    def __init__(self, path: Path, key: bytes | None = None) -> None:
        self.path, self.key = Path(path), key

    def entries(self) -> list[dict]:
        """Every entry, after checking the whole chain. Raises `LockError` if anything does not verify."""
        if not self.path.exists():
            return []
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError:
            raise LockError("the sealed-run chain cannot be read") from None
        out: list[dict] = []
        prev = GENESIS
        for n, raw in enumerate(lines):
            try:
                e = json.loads(raw)
                ok = (
                    e["seq"] == n
                    and e["kind"] in KINDS
                    and e["prev"] == prev
                    and hmac.compare_digest(e["sha"], _mac(self.key, n, e["kind"], e["data"], prev))
                )
            except (ValueError, KeyError, TypeError):
                ok = False
            if not ok:
                raise LockError(
                    f"the sealed-run chain is broken at line {n + 1} (edited, reordered, damaged or the wrong key)"
                )
            prev = e["sha"]
            out.append(e)
        return out

    def append(self, kind: str, data: dict | None = None) -> dict:
        """Verify, then add one entry (fsync). The caller holds the lock.json OS lock."""
        entries = self.entries()
        seq, prev = len(entries), (entries[-1]["sha"] if entries else GENESIS)
        body = {**(data or {}), "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
        entry = {
            "seq": seq,
            "kind": kind,
            "data": body,
            "prev": prev,
            "sha": _mac(self.key, seq, kind, body, prev),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return entry


def _status_of(entries: list[dict], runs_dir: Path) -> str:
    """Status of the LAST sealed run, from the chain and the run folder, never from a flag written before the work."""
    runs = [e for e in entries if e["kind"] == "sealed_run"]
    if not runs:
        return "none"
    run_id = runs[-1]["data"]["run_id"]
    for e in reversed(entries):
        if e["kind"] == "sealed_done" and e["data"].get("run_id") == run_id:
            return e["data"]["status"]
    return (
        report_status(runs_dir, run_id) or "aborted"
    )  # started, wrote no report: no results were seen


def report_status(runs_dir: Path, run_id: str) -> str | None:
    """The run folder's own verdict if its report.json exists ("aborted" only when the report says the run aborted)."""
    try:
        rep = json.loads((Path(runs_dir) / run_id / "report.json").read_text(encoding="utf-8"))
        return "aborted" if rep.get("aborted") else "complete"
    except (OSError, ValueError, AttributeError):
        return None


class SealedGate:
    """Everything that reads or moves the sealed counter, smoke key and run status. Callers hold `lock_guard`."""

    def __init__(self, eval_dir: Path, chain_path: Path, runs_dir: Path, key: bytes | None) -> None:
        self.eval_dir, self.runs_dir, self.key = Path(eval_dir), Path(runs_dir), key
        self.chain = Chain(chain_path, key)

    # ---- every write: chain first, then the lock mirror (crash between the two is replayed by load)
    def _commit(self, lock: Lock, kind: str, data: dict, **fields) -> Lock:
        entry = self.chain.append(kind, data)
        new = lock.model_copy(update={**fields, "chain_head": entry["sha"]})
        new = new.model_copy(update={"seal": seal_of(self.key, new)})
        write_lock(self.eval_dir, new)
        return new

    def freeze_seal(self, lock: Lock) -> Lock:
        """Seal a freshly frozen lock (the freeze step passes this in so lock.json is never written unsealed)."""
        if self.chain.entries():
            raise LockError(
                "a sealed-run chain already exists here; it is not reset by a new freeze"
            )
        return lock.model_copy(update={"seal": seal_of(self.key, lock)})

    def load(self) -> Lock:
        """lock.json verified against the chain, with crash recovery. Raises `LockError` on a mismatch."""
        lock = read_lock(self.eval_dir)
        entries = self.chain.entries()
        if self.key and (
            lock.seal is None or not hmac.compare_digest(lock.seal, seal_of(self.key, lock) or "")
        ):
            raise LockError(
                "lock.json does not match its seal (test_runs, smoke_key or chain_head was edited)"
            )
        shas = [e["sha"] for e in entries]
        if lock.chain_head is None:
            seen = 0
        elif lock.chain_head in shas:
            seen = shas.index(lock.chain_head) + 1
        else:
            raise LockError("lock.json names a chain position that is not in the sealed-run chain")
        recovered = entries[seen:]
        test_runs = lock.test_runs + sum(1 for e in recovered if e["kind"] == "sealed_run")
        smoke = next(
            (e["data"]["key"] for e in reversed(entries) if e["kind"] == "smoke_pass"), None
        )
        if test_runs != sum(1 for e in entries if e["kind"] == "sealed_run"):
            raise LockError(
                f"lock.json says {lock.test_runs} sealed run(s) but the chain records "
                f"{sum(1 for e in entries if e['kind'] == 'sealed_run')}: lock.json was edited, replaced or re-frozen; "
                "the chain wins and the counter is not reset"
            )
        if (
            recovered
        ):  # roll the lock forward over what a crash left unmirrored, and say so in the chain
            lock = self._commit(
                lock,
                "reconcile",
                {"replayed": [e["seq"] for e in recovered]},
                test_runs=test_runs,
                smoke_key=smoke,
            )
        status = _status_of(self.chain.entries(), self.runs_dir)
        return lock.model_copy(update={"smoke_key": smoke, "last_test_status": status})

    def begin(self, lock: Lock, run_id: str) -> Lock:
        """A sealed run starts: chain (write-ahead) then lock. Consumes a hand-written harness defect."""
        return self._commit(
            lock,
            "sealed_run",
            {"run_id": run_id, "n": lock.test_runs + 1},
            test_runs=lock.test_runs + 1,
            harness_defect_reason=None,
            harness_defect_run=None,
            harness_defect_item=None,
        )

    def finish(self, run_id: str, status: str) -> None:
        lock = self.load()
        # the report on disk outranks the caller's idea of the status: results that exist are never 'aborted'
        status = report_status(self.runs_dir, run_id) or status
        self._commit(lock, "sealed_done", {"run_id": run_id, "status": status})

    def record_smoke(self, key: str) -> None:
        lock = self.load()
        self._commit(lock, "smoke_pass", {"key": key}, smoke_key=key)

    def reconcile(self) -> tuple[int, int]:
        """The explicit, audited form of the recovery `load()` does: returns (lock test_runs before, after)."""
        before = read_lock(self.eval_dir).test_runs
        return before, self.load().test_runs


def key_from(provider, name: str | None) -> bytes | None:
    """The HMAC key from the secrets kind. A configured name that cannot be read is an error, not 'no key'."""
    if not name:
        return None
    try:
        value = provider.get(name)
    except Exception:  # noqa: BLE001 - the provider's message may name a path
        raise LockError("the sealed-run key secret cannot be read") from None
    if len(value) < MIN_KEY_CHARS:
        raise LockError(f"the sealed-run key must be at least {MIN_KEY_CHARS} characters")
    return value.encode("utf-8")
