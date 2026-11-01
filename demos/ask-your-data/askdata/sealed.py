"""The sealed-run gate: the ONE place that decides how often the sealed test set was touched and records it.

Bug class this closes: a counter or guard that lives in a plain editable file, written before the work and cleared
only on the happy path. The standard remedies, as used here:

* Write-ahead log with replay (as in databases): every state change is FIRST appended to `sealed-chain.jsonl`
  (`genesis`, `sealed_run`, `sealed_done`, `smoke_pass`, `reconcile`, `reseal`, `new_set`), THEN mirrored into lock.json
  together with the chain head. A crash between the two leaves the chain ahead of the lock; `load()` replays what the
  lock has not seen and rewrites it (logging a `reconcile` entry). A torn final line (power loss mid-write) is cut off
  and logged the same way.
* Status is DERIVED, never stored as a promise: a run that was started and never reported `sealed_done` is judged by
  the run folder (`report.json` exists means its own verdict, absent means aborted).
* Hash chain with an HMAC key (RFC 2104) when `sealed_key_secret_name` is configured: each line carries
  HMAC-SHA256(key, seq, kind, data, prev), and lock.json carries `seal` = HMAC over the WHOLE lock except `seal`
  (files, thresholds, caps, counter, smoke key, chain head, the hand-written defect fields). The key comes from the
  secrets kind, never from a file in the repo. The one sanctioned hand edit (a proved harness defect) is blessed by the
  key holder with `eval reseal`, which logs a `reseal` entry.
* An ANCHOR outside the two files: at the first freeze a `set_id` is written to `<audit_dir>/sealed-anchor.json` and,
  to a second file `<eval_dir>/anchor.json` that you COMMIT TO GIT. `freeze`
  refuses while any anchor exists unless `--new-set --reason ...` is given, which writes a visible `new_set` entry
  and restarts the count. `load()` refuses a chain whose latest `set_id` differs from an anchor's, and a keyless gate
  once the set has been keyed (anchor, lock and genesis all say so).

What this still does NOT stop, stated plainly:
* With NO key configured the chain is a plain SHA-256 chain: anyone who can write the audit folder can recompute it. It
  then only catches accidents and single-file edits; the counter is tamper-resistant only by git history.
* Rollback: putting back an older, internally consistent set of ALL the files (lock.json, chain, anchors) shows an older
  state. Only git history of lock.json and the committed anchor, and an off-machine copy of the chain's last `sha`,
  can tell. Deleting every anchor AND the chain AND the lock, when no anchor file is committed to git, also resets it.
* The chain lives on the same disk as the code that checks it; it is tamper-EVIDENCE, not a safe.
"""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import json
import os
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from askdata.evalset import Lock, LockError, Thresholds, freeze, lock_path, read_lock, write_lock

GENESIS = "0" * 64
KINDS = (
    "genesis",
    "sealed_run",
    "sealed_done",
    "report",
    "smoke_pass",
    "reconcile",
    "reseal",
    "new_set",
)
RUN_LOCK = "sealed-run.lock"
MIN_REASON_CHARS = 20
MIN_KEY_CHARS = 16
HAND_FIELDS = ("harness_defect_reason", "harness_defect_run", "harness_defect_item")


def _mac(key: bytes | None, seq: int, kind: str, data: dict, prev: str) -> str:
    body = json.dumps(
        {"seq": seq, "kind": kind, "data": data, "prev": prev},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return (
        hmac.new(key, body, hashlib.sha256).hexdigest() if key else hashlib.sha256(body).hexdigest()
    )


def core_hash_of(lock: Lock) -> str:
    """SHA-256 of everything in lock.json EXCEPT the seal, this hash and the hand-written defect fields. `eval reseal`
    refuses to bless a lock whose core no longer matches the hash stored at the last commit."""
    skip = {"seal", "core_hash", *HAND_FIELDS}
    body = json.dumps(
        json.loads(lock.model_dump_json(exclude=skip)), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def seal_of(key: bytes | None, lock: Lock) -> str | None:
    """HMAC over the WHOLE lock except `seal` itself; None when no key is configured."""
    if not key:
        return None
    body = json.dumps(
        json.loads(lock.model_dump_json(exclude={"seal"})), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hmac.new(key, b"lock:" + body, hashlib.sha256).hexdigest()


class Chain:
    def __init__(self, path: Path, key: bytes | None = None) -> None:
        self.path, self.key = Path(path), key

    def _split(self) -> tuple[list[str], bool]:
        """(complete lines, torn) - torn: the last line has no newline AND is not valid JSON (a write cut short)."""
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return [], False
        except OSError:
            raise LockError("the sealed-run chain cannot be read") from None
        parts = text.split("\n")
        tail = parts.pop()  # "" when the file ends with a newline
        if tail:
            try:
                json.loads(tail)
                parts.append(tail)  # complete but unterminated: judged like any other line
            except ValueError:
                return parts, True
        return parts, False

    @property
    def torn(self) -> bool:
        return self._split()[1]

    def entries(self) -> list[dict]:
        """Every complete entry, after checking the whole chain. Raises `LockError` if anything does not verify."""
        lines, _ = self._split()
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

    def repair(self) -> bool:
        """Cut a torn final line off. True if something was cut."""
        lines, torn = self._split()
        if not torn:
            return False
        with open(self.path, "w", encoding="utf-8", newline="\n") as f:
            f.write("".join(line + "\n" for line in lines))
            f.flush()
            os.fsync(f.fileno())
        return True

    def append(self, kind: str, data: dict | None = None) -> dict:
        """Verify, then add one entry (fsync). The caller holds the lock.json OS lock."""
        self.repair()
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

    def truncate_to(self, n: int) -> None:
        lines, _ = self._split()
        with open(self.path, "w", encoding="utf-8", newline="\n") as f:
            f.write("".join(line + "\n" for line in lines[:n]))
            f.flush()
            os.fsync(f.fileno())


def report_status(runs_dir: Path, run_id: str) -> str | None:
    """The run folder's own verdict if its report.json exists ("aborted" only when the report says the run aborted)."""
    try:
        rep = json.loads((Path(runs_dir) / run_id / "report.json").read_text(encoding="utf-8"))
        return "aborted" if rep.get("aborted") else "complete"
    except (OSError, ValueError, AttributeError):
        return None


def file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def report_state(entries: list[dict], runs_dir: Path, run_id: str) -> str | None:
    """Verdict of a run folder's report.json: None (no report), "unverified" (a report no chain entry vouches for),
    or "complete"/"aborted" from a report whose SHA-256 matches the one recorded when it was written.
    A report that differs from the recorded hash raises `LockError`."""
    path = Path(runs_dir) / run_id / "report.json"
    digest = file_sha256(path)
    if digest is None:
        return None
    rec = next(
        (
            e
            for e in reversed(entries)
            if e["kind"] == "report" and e["data"].get("run_id") == run_id
        ),
        None,
    )
    if rec is None:
        return "unverified"
    if rec["data"]["sha256"] != digest:
        raise LockError(
            f"report.json of run {run_id} differs from the hash recorded when it was written"
        )
    return report_status(runs_dir, run_id)


def _status_of(entries: list[dict], runs_dir: Path, running: bool = False) -> str:
    """Status of the LAST sealed run, from the chain and the run folder, never from a flag written before the work.
    A begun run with nothing to show is "running" while its process holds the run lock, "aborted" once it is gone."""
    runs = [e for e in entries if e["kind"] == "sealed_run"]
    if not runs:
        return "none"
    run_id = runs[-1]["data"]["run_id"]
    for e in reversed(entries):
        if e["kind"] == "sealed_done" and e["data"].get("run_id") == run_id:
            return e["data"]["status"]
    state = report_state(entries, runs_dir, run_id)
    if state is not None:
        return state
    return "running" if running else "aborted"


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, indent=2, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


class SealedGate:
    """Everything that reads or moves the sealed counter, smoke key and run status. Callers hold `lock_guard`."""

    def __init__(
        self,
        eval_dir: Path,
        chain_path: Path,
        runs_dir: Path,
        key: bytes | None,
        anchors: tuple[Path, ...] | list[Path] = (),
    ) -> None:
        self.eval_dir, self.runs_dir, self.key = Path(eval_dir), Path(runs_dir), key
        self.chain = Chain(chain_path, key)
        # An anchor is a small .json file next to the data it protects: inside the eval folder or the audit folder,
        # so a config entry cannot make this code write anywhere else.
        roots = [self.eval_dir.resolve(), Path(chain_path).resolve().parent]
        self.anchors = []
        for a in anchors:
            resolved = Path(a).resolve()
            if resolved.suffix != ".json" or not any(resolved.is_relative_to(r) for r in roots):
                raise LockError(
                    "an anchor must be a .json file inside the eval or the audit folder"
                )
            self.anchors.append(resolved)

    # ---- every write: chain first, then the lock mirror (crash between the two is replayed by load)
    def _key_id(self) -> str | None:
        """A public name for the key (HMAC of a fixed label, truncated), recorded in the genesis entry and the anchors
        so a DIFFERENT key is noticed. It reveals nothing usable about the key."""
        if not self.key:
            return None
        return hmac.new(self.key, b"key-id", hashlib.sha256).hexdigest()[:16]

    def _sealed(self, lock: Lock) -> Lock:
        lock = lock.model_copy(update={"core_hash": core_hash_of(lock)})
        return lock.model_copy(update={"seal": seal_of(self.key, lock)})

    # ---- the run lock: held by the process that is running a sealed run, for the whole run
    def acquire_run(self):
        """Take the OS run lock (kept open until `release_run`). Raises `LockError` if another run holds it."""
        from askdata.meter import _try_lock

        f = open(self.eval_dir / RUN_LOCK, "a+b")  # noqa: SIM115 - held across calls, closed by release_run
        if not _try_lock(f):
            f.close()
            raise LockError("a sealed run is still running")
        return f

    @staticmethod
    def release_run(handle) -> None:
        from askdata.meter import _unlock

        with contextlib.suppress(OSError):
            _unlock(handle)
        handle.close()

    def running(self) -> bool:
        """True while some process holds the run lock (a sealed run is in progress)."""
        try:
            handle = self.acquire_run()
        except LockError:
            return True
        self.release_run(handle)
        return False

    def _commit(self, lock: Lock, kind: str, data: dict, **fields) -> Lock:
        entry = self.chain.append(kind, data)
        new = self._sealed(lock.model_copy(update={**fields, "chain_head": entry["sha"]}))
        write_lock(self.eval_dir, new)
        return new

    # ---- anchors
    def _read_anchors(self) -> list[dict]:
        found = []
        for a in self.anchors:
            if a.exists():
                try:
                    found.append(json.loads(a.read_text(encoding="utf-8")))
                except (OSError, ValueError):
                    raise LockError(f"anchor {a.name} cannot be read") from None
        return found

    def _write_anchors(self, sets: list[dict], keyed: bool) -> None:
        body = {"set_id": sets[-1]["set_id"], "sets": sets, "keyed": keyed, "key_id": self._key_id(),
                "note": "Anchor of the sealed-run chain. Commit this file to git. freeze refuses while it exists."}  # fmt: skip
        for a in self.anchors:
            _write_json(a, body)

    # ---- freeze
    def create(
        self,
        names: list[str],
        thresholds: Thresholds | None = None,
        new_set_reason: str | None = None,
        lock_fields: dict | None = None,
        discard_count: int | None = None,
    ) -> Lock:
        """Freeze: genesis entry, lock.json (no-clobber), anchors. With anchors or a chain already there it refuses,
        unless `new_set_reason` (20+ characters) is given: then a visible `new_set` entry restarts the count. THAT
        COMMAND RESETS THE SEALED COUNTER: while runs were counted it also needs `discard_count` equal to that number,
        and both are written into the chain. Everything is undone if any step fails."""
        anchors = self._read_anchors()
        if any(a.get("keyed") for a in anchors) and not self.key:
            raise LockError("this test set was keyed; a freeze with no key is refused (downgrade)")
        exists = bool(anchors) or self.chain.path.exists()
        reason = (new_set_reason or "").strip()
        if exists and not reason:
            raise LockError(
                "a sealed-run chain or anchor already exists for this project: a new freeze would reset the "
                'sealed counter. If this really is a NEW test set, use `eval freeze --new-set --reason "..."`'
            )
        if reason and not exists:
            raise LockError("--new-set given but there is no earlier set to replace")
        if reason and len(reason) < MIN_REASON_CHARS:
            raise LockError(
                f"--reason must be at least {MIN_REASON_CHARS} characters: it is the audit record of a reset"
            )
        chain_existed = self.chain.path.exists()
        prev = self.chain.entries() if chain_existed else []
        counted = 0
        if prev:
            base = (
                max(
                    (i for i, e in enumerate(prev) if e["kind"] in ("genesis", "new_set")),
                    default=-1,
                )
                + 1
            )
            counted = sum(1 for e in prev[base:] if e["kind"] == "sealed_run")
        if reason and counted and discard_count != counted:
            raise LockError(
                f"--new-set RESETS the sealed counter and {counted} sealed run(s) are counted; "
                f"to discard that count on purpose, also pass --discard-count {counted}"
            )
        set_id = uuid.uuid4().hex
        data = {"set_id": set_id, "keyed": bool(self.key), "key_id": self._key_id()}
        if reason:
            data |= {
                "reason": reason,
                "previous_head": prev[-1]["sha"] if prev else None,
                "discarded_runs": counted,
            }
        old = None
        backups: dict[Path, Path] = {}
        for (
            anchor
        ) in self.anchors:  # path to path: the old anchors can be put back if this freeze fails
            backup = anchor.with_name(anchor.name + ".bak")
            try:
                shutil.copyfile(anchor, backup)
            except FileNotFoundError:
                continue
            backups[anchor] = backup
        entry = self.chain.append("new_set" if reason else "genesis", data)

        def seal(lock: Lock) -> Lock:
            return self._sealed(
                lock.model_copy(update={"chain_head": entry["sha"], "keyed": bool(self.key)})
            )

        try:
            if (
                reason and lock_path(self.eval_dir).exists()
            ):  # moved aside only AFTER the append succeeded
                old = lock_path(self.eval_dir).with_name(
                    f"lock.json.prev-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}"
                )
                os.replace(lock_path(self.eval_dir), old)
            lock = freeze(
                self.eval_dir,
                names,
                thresholds,
                no_clobber=True,
                seal=seal,
                lock_fields=lock_fields,
            )
            history = _dedupe([s for a in anchors for s in a.get("sets", [])])
            history.append(
                {"set_id": set_id, "created": entry["data"]["ts"], "reason": reason or None}
            )
            self._write_anchors(history, bool(self.key))
            for b in backups.values():
                b.unlink(missing_ok=True)
        except BaseException:
            # undo in reverse: the new anchors, the new lock, the move of the old lock, our chain entry
            for a in self.anchors:
                if a in backups:
                    os.replace(backups[a], a)
                else:
                    a.unlink(missing_ok=True)
            if old is not None:
                lock_path(self.eval_dir).unlink(missing_ok=True)
                os.replace(old, lock_path(self.eval_dir))
            elif lock_path(self.eval_dir).exists() and not reason:
                lock_path(self.eval_dir).unlink(missing_ok=True)
            if chain_existed:
                self.chain.truncate_to(len(prev))
            else:
                self.chain.path.unlink(missing_ok=True)
            raise
        return lock

    # ---- load / verify / recover
    def _check_anchors_and_keyed(self, lock: Lock, entries: list[dict]) -> str:
        anchors = self._read_anchors()
        missing = [a.name for a in self.anchors if not a.exists()]
        if entries and missing:
            raise LockError(
                f"the sealed-run anchor {missing[0]} is missing (deleted?): the chain cannot be trusted alone"
            )
        gen = [e for e in entries if e["kind"] in ("genesis", "new_set")]
        if not gen:
            raise LockError("the sealed-run chain has no genesis entry")
        set_id = gen[-1]["data"]["set_id"]
        for a in anchors:
            if a.get("set_id") != set_id:
                raise LockError("the chain's set id differs from an anchor: the chain was replaced")
            if self.key and a.get("key_id") and a["key_id"] != self._key_id():
                raise LockError(
                    "an anchor names a different key than the one in use (key id mismatch)"
                )
        keyed_ever = (
            lock.keyed
            or any(a.get("keyed") for a in anchors)
            or any(e["data"].get("keyed") for e in gen)
        )
        if keyed_ever and not self.key:
            raise LockError("this test set was keyed; a gate with no key is refused (downgrade)")
        return set_id

    def _load(self, check_seal: bool = True) -> tuple[Lock, list[dict], bool]:
        lock = read_lock(self.eval_dir)
        if not self.chain.path.exists():
            raise LockError("the sealed-run chain is missing")
        if (lock.keyed or any(a.get("keyed") for a in self._read_anchors())) and not self.key:
            raise LockError("this test set was keyed; a gate with no key is refused (downgrade)")
        torn = self.chain.repair()
        entries = self.chain.entries()
        self._check_anchors_and_keyed(lock, entries)
        if (
            check_seal
            and self.key
            and (
                lock.seal is None
                or not hmac.compare_digest(lock.seal, seal_of(self.key, lock) or "")
            )
        ):
            raise LockError(
                "lock.json does not match its seal (something in it was edited; if you edited the harness "
                "defect fields by hand, run `eval reseal`)"
            )
        shas = [e["sha"] for e in entries]
        if lock.chain_head is None:
            raise LockError("lock.json names no chain position")
        if lock.chain_head not in shas:
            raise LockError("lock.json names a chain position that is not in the sealed-run chain")
        return lock, entries, torn

    def load(self) -> Lock:
        """lock.json verified against the chain, with crash recovery. Raises `LockError` on a mismatch."""
        lock, entries, torn = self._load()
        return self._finish_load(lock, entries, torn)

    def _finish_load(self, lock: Lock, entries: list[dict], torn: bool) -> Lock:
        seen = [e["sha"] for e in entries].index(lock.chain_head) + 1
        recovered = entries[seen:]
        base = max(i for i, e in enumerate(entries) if e["kind"] in ("genesis", "new_set")) + 1
        live = entries[base - 1 :]
        counted = sum(1 for e in live if e["kind"] == "sealed_run")
        test_runs = lock.test_runs + sum(1 for e in recovered if e["kind"] == "sealed_run")
        smoke = next((e["data"]["key"] for e in reversed(live) if e["kind"] == "smoke_pass"), None)
        if test_runs != counted:
            raise LockError(
                f"lock.json says {lock.test_runs} sealed run(s) but the chain records {counted}: lock.json was "
                "edited, replaced or re-frozen; the chain wins and the counter is not reset"
            )
        if (
            recovered or torn
        ):  # roll the lock forward over what a crash left unmirrored, and say so in the chain
            cleared = (
                {f: None for f in HAND_FIELDS}
                if any(e["kind"] == "sealed_run" for e in recovered)
                else {}
            )  # a replayed run consumed the hand-written defect, exactly as `begin` would have
            lock = self._commit(
                lock,
                "reconcile",
                {"replayed": [e["seq"] for e in recovered], "truncated_torn_tail": torn},
                test_runs=test_runs,
                smoke_key=smoke,
                **cleared,
            )
            entries = self.chain.entries()
            live = entries[base - 1 :]
        status = _status_of(live, self.runs_dir, self.running())
        return lock.model_copy(update={"smoke_key": smoke, "last_test_status": status})

    def begin(self, lock: Lock, run_id: str) -> Lock:
        """A sealed run starts: chain (write-ahead) then lock. Consumes a hand-written harness defect."""
        return self._commit(
            lock,
            "sealed_run",
            {"run_id": run_id, "n": lock.test_runs + 1},
            test_runs=lock.test_runs + 1,
            **{f: None for f in HAND_FIELDS},
        )

    def record_report(self, run_id: str) -> None:
        """Right after `write_run`: put the SHA-256 of report.json into the chain, so a later change is noticed."""
        lock = self.load()
        digest = file_sha256(self.runs_dir / run_id / "report.json")
        if digest is None:
            raise LockError("there is no report.json to record")
        self._commit(lock, "report", {"run_id": run_id, "sha256": digest})

    def finish(self, run_id: str, status: str) -> None:
        lock = self.load()
        # the report on disk outranks the caller's idea of the status: results that exist are never 'aborted'
        state = report_state(self.chain.entries(), self.runs_dir, run_id)
        status = state if state in ("complete", "aborted", "unverified") else status
        self._commit(lock, "sealed_done", {"run_id": run_id, "status": status})

    def record_smoke(self, key: str) -> None:
        lock = self.load()
        self._commit(lock, "smoke_pass", {"key": key}, smoke_key=key)

    def reconcile(self) -> tuple[int, int]:
        """The explicit, audited form of the recovery `load()` does: returns (lock test_runs before, after)."""
        before = read_lock(self.eval_dir).test_runs
        return before, self.load().test_runs

    def reseal(self) -> list[str]:
        """Key holder only: bless the hand-written harness-defect fields in lock.json and NOTHING else. The rest of the
        lock must still match the hash stored at the last commit; the counter, chain and anchors must agree; at least
        one hand field must be set. The edit is logged. Run it after reading `git diff lock.json`."""
        if not self.key:
            raise LockError("`eval reseal` needs the sealed-run key (sealed_key_secret_name)")
        disk = read_lock(self.eval_dir)
        if disk.core_hash is None or core_hash_of(disk) != disk.core_hash:
            raise LockError(
                "reseal refused: something other than the hand-written defect fields changed in lock.json "
                "(files, thresholds, caps, counter ...); restore it from the repository first"
            )
        fields = [f for f in HAND_FIELDS if getattr(disk, f)]
        if not fields:
            raise LockError(
                "reseal refused: no hand-written defect field is set, there is nothing to bless"
            )
        self._finish_load(
            *self._load(check_seal=False)
        )  # counter, chain and anchors must still agree
        disk = read_lock(self.eval_dir)
        self._commit(disk, "reseal", {"hand_fields": fields})
        return fields


def _dedupe(sets: list[dict]) -> list[dict]:
    out: dict[str, dict] = {}
    for s in sets:
        out.setdefault(s["set_id"], s)
    return list(out.values())


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
