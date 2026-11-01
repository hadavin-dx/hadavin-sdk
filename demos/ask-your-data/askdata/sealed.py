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
* Rollback is EASY, even with a key: the old lock.json (its seal is valid) plus the current chain cut back to that
  lock's chain_head is a consistent older state (an HMAC chain prefix verifies; the anchors hold only the set id, keyed
  flag and key id). One cheap detection: a sealed run FOLDER with results that the chain does not record is refused (it
  needs runs/ to be intact). Otherwise only git history of lock.json and the committed anchor, and an off-machine copy of
  the chain's last `sha`, can tell. Deleting every anchor AND the chain AND the lock, when no anchor file is committed to git, also resets it.
* The chain lives on the same disk as the code that checks it; it is tamper-EVIDENCE, not a safe.
"""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import json
import os
import re
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from askdata.evalset import (
    Lock,
    LockError,
    Thresholds,
    freeze,
    lock_path,
    make_lock,
    read_lock,
    replace_with_retry,
    write_lock,
)

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
    "report_lost",
    "rekey",
)
RUN_LOCK = "sealed-run.lock"
RECOVERY_MARKER = "FREEZE-RECOVERY.txt"
# what `evalrun.run_id` produces: UTC time to the microsecond plus the label. Nothing else names a run folder.
RUN_NAME = re.compile(r"[0-9]{8}T[0-9]{12}Z-(dev|sealed|second-look)", re.ASCII)
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
    """SHA-256 of everything in lock.json EXCEPT the seal, this hash, the chain head and the hand-written defect
    fields. It is written into the CHAIN ENTRY of every commit (not only into lock.json): `eval reseal` and every load
    compare lock.json against the value the chain recorded, so a lock rewritten together with its own core_hash is
    still caught."""
    skip = {"seal", "core_hash", "chain_head", *HAND_FIELDS}
    body = json.dumps(
        json.loads(lock.model_dump_json(exclude=skip)), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def files_sha_of(lock: Lock) -> str:
    """SHA-256 of the frozen file names and hashes (also written into every chain entry)."""
    body = json.dumps(lock.files, sort_keys=True, separators=(",", ":"))
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
    def __init__(
        self, path: Path, key: bytes | None = None, old_keys: tuple[bytes, ...] = ()
    ) -> None:
        """`old_keys`: the keys the chain was under BEFORE `key`, oldest first. Entries up to and including a `rekey`
        entry are verified with the key that was current then (the rekey entry itself with the OLD key)."""
        self.path, self.key, self.old_keys = Path(path), key, tuple(old_keys)
        self.active_idx = 0

    def _split(self) -> tuple[list[str], bool, bool]:
        """(complete lines, torn, unterminated). torn: the last line has no newline AND is not valid JSON (a write cut
        short). unterminated: the last line is complete JSON but lacks its newline (the next append would glue to it)."""
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return [], False, False
        except OSError:
            raise LockError("the sealed-run chain cannot be read") from None
        parts = text.split("\n")
        tail = parts.pop()  # "" when the file ends with a newline
        if tail:
            try:
                json.loads(tail)
                parts.append(tail)  # complete but unterminated: judged like any other line
            except ValueError:
                return parts, True, False
            return parts, False, True
        return parts, False, False

    @property
    def torn(self) -> bool:
        return self._split()[1]

    def entries(self) -> list[dict]:
        """Every complete entry, after checking the whole chain. Raises `LockError` if anything does not verify."""
        lines, _, _ = self._split()
        out: list[dict] = []
        prev = GENESIS
        keys = [*self.old_keys, self.key] if self.old_keys else [self.key]
        idx = 0
        for n, raw in enumerate(lines):
            try:
                e = json.loads(raw)
                ok = (
                    e["seq"] == n
                    and e["kind"] in KINDS
                    and e["prev"] == prev
                    and hmac.compare_digest(
                        e["sha"], _mac(keys[idx], n, e["kind"], e["data"], prev)
                    )
                )
                if ok and e["kind"] == "rekey":
                    idx += 1  # everything after a rekey entry is under the next key
                    if idx >= len(keys):
                        raise LockError(
                            "the chain was re-keyed but the new key is not configured (sealed_key_secret_name)"
                        )
            except (ValueError, KeyError, TypeError):
                ok = False
            if not ok:
                raise LockError(
                    f"the sealed-run chain is broken at line {n + 1} (edited, reordered, damaged or the wrong key)"
                )
            prev = e["sha"]
            out.append(e)
        self.active_idx = idx
        return out

    def _rewrite(self, lines: list[str]) -> None:
        """Replace the whole file atomically (temp file, fsync, os.replace): a crash leaves the old file or the new one,
        never an empty or half-written chain."""
        tmp = self.path.with_name(f"{self.path.name}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")
        try:
            with open(tmp, "w", encoding="utf-8", newline="\n") as f:
                f.write("".join(line + "\n" for line in lines))
                f.flush()
                os.fsync(f.fileno())
            replace_with_retry(tmp, self.path)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise

    def repair(self) -> bool:
        """Cut a torn final line off, and add the newline a complete last line lacks. True if a line was cut."""
        lines, torn, unterminated = self._split()
        if torn or unterminated:
            self._rewrite(lines)
        return torn

    def append(self, kind: str, data: dict | None = None, signing_key: bytes | None = None) -> dict:
        """Verify, then add one entry (fsync). The caller holds the lock.json OS lock."""
        self.repair()
        entries = self.entries()
        if kind != "rekey" and self.old_keys and self.active_idx != len(self.old_keys):
            raise LockError(
                "the chain is still under the previous key: run `eval rotate-key` once to re-key it"
            )
        seq, prev = len(entries), (entries[-1]["sha"] if entries else GENESIS)
        body = {**(data or {}), "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
        entry = {
            "seq": seq,
            "kind": kind,
            "data": body,
            "prev": prev,
            "sha": _mac(signing_key or self.key, seq, kind, body, prev),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return entry

    def truncate_to(self, n: int) -> None:
        lines, _, _ = self._split()
        self._rewrite(lines[:n])


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


RESULT_FILES = ("report.json", "report.md", "results.jsonl")


def _problem(entries: list[dict], runs_dir: Path, run_id: str) -> tuple[dict | None, str | None]:
    """(the last `report` entry of the run, what is wrong with its files: None, "deleted" or "changed")."""
    folder = Path(runs_dir) / run_id
    rec = next(
        (
            e
            for e in reversed(entries)
            if e["kind"] == "report" and e["data"].get("run_id") == run_id
        ),
        None,
    )
    if rec is None:
        return None, None
    wanted = {
        "report.json": rec["data"]["sha256"],
        "report.md": rec["data"].get("report_md_sha256"),
        "results.jsonl": rec["data"].get("results_sha256"),
    }
    for name, digest in wanted.items():
        if digest is None:
            continue
        now = file_sha256(folder / name)
        if now is None:
            return rec, "deleted"
        if now != digest:
            return rec, "changed"
    return rec, None


def report_state(entries: list[dict], runs_dir: Path, run_id: str) -> str | None:
    """Verdict of a run folder: None (no results evidence at all), "unverified" (results exist that no chain entry
    vouches for), "lost" (the key holder recorded that the recorded files are gone: `eval report-lost`), or
    "complete"/"aborted" from a report.json whose SHA-256 (and that of report.md and results.jsonl) matches what was
    recorded when it was written. A recorded file that was deleted or changed, and not marked lost, raises `LockError`."""
    folder = Path(runs_dir) / run_id
    rec, problem = _problem(entries, runs_dir, run_id)
    if rec is not None:
        lost = any(
            e["kind"] == "report_lost"
            and e["data"].get("run_id") == run_id
            and e["seq"] > rec["seq"]
            for e in entries
        )
        if lost:
            if problem is not None and any((folder / n).exists() for n in RESULT_FILES):
                raise LockError(
                    f"files appeared in the folder of run {run_id}, which is marked lost, and they do not match what "
                    "the chain recorded: they are not shown or trusted"
                )
            return "lost"
        if problem == "deleted":
            raise LockError(
                f"a recorded file of run {run_id} was deleted after its hash was recorded "
                "(if the run folder was pruned or moved on purpose, the key holder runs `eval report-lost`)"
            )
        if problem == "changed":
            raise LockError(
                f"report.json of run {run_id} differs from the hash recorded when it was written"
            )
        return report_status(runs_dir, run_id)
    return "unverified" if any((folder / n).exists() for n in RESULT_FILES) else None


def verify_reports(entries: list[dict], runs_dir: Path) -> None:
    """Every run whose report hash is in the chain must still have exactly that report (raises `LockError`)."""
    for run_id in {e["data"]["run_id"] for e in entries if e["kind"] == "report"}:
        report_state(entries, runs_dir, run_id)


def unchained_runs(entries: list[dict], runs_dir: Path) -> list[str]:
    """Sealed-looking run folders that hold results but whose run the chain never recorded: the sign of a lock/chain
    that was rolled back while the run folders stayed (a cheap check; it needs the run folders to be intact)."""
    chained = {e["data"]["run_id"] for e in entries if e["kind"] == "sealed_run"}
    out = []
    try:
        names = sorted(p.name for p in Path(runs_dir).iterdir() if p.is_dir())
    except OSError:
        return []
    for name in names:
        m = RUN_NAME.fullmatch(name)
        if (
            m
            and m.group(1) != "dev"
            and name not in chained
            and any((Path(runs_dir) / name / n).exists() for n in RESULT_FILES)
        ):
            out.append(name)
    return out


def verify_run_report(entries: list[dict], run_dir: Path) -> str:
    """For `eval report` and `eval compare`: "vouched" (the chain recorded this report and it matches), "lost" (the key
    holder marked it lost), or "unrecorded" (the chain has no record of it). Raises `LockError` if it was deleted or
    changed."""
    run_id = Path(run_dir).name
    if not any(e["kind"] == "report" and e["data"].get("run_id") == run_id for e in entries):
        return "unrecorded"
    return "lost" if report_state(entries, Path(run_dir).parent, run_id) == "lost" else "vouched"


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
    if state == "lost":
        return "unverified"  # results existed and are gone: never an `aborted` second look
    if state is not None:
        return state
    return "running" if running else "aborted"


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(obj, indent=2, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
        replace_with_retry(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)  # never leave a temp file behind
        raise


class SealedGate:
    """Everything that reads or moves the sealed counter, smoke key and run status. Callers hold `lock_guard`."""

    def __init__(
        self,
        eval_dir: Path,
        chain_path: Path,
        runs_dir: Path,
        key: bytes | None,
        anchors: tuple[Path, ...] | list[Path] = (),
        old_keys: tuple[bytes, ...] = (),
    ) -> None:
        self.eval_dir, self.runs_dir, self.key = Path(eval_dir), Path(runs_dir), key
        self.chain = Chain(chain_path, key, old_keys)
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
        nohead = lock.model_copy(update=fields)
        entry = self.chain.append(
            kind, {**data, "core_hash": core_hash_of(nohead), "files_sha": files_sha_of(nohead)}
        )
        new = self._sealed(nohead.model_copy(update={"chain_head": entry["sha"]}))
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
        lock_runs = (
            read_lock(self.eval_dir).test_runs if lock_path(self.eval_dir).exists() else None
        )
        if reason and not chain_existed:
            if discard_count is None:
                raise LockError(
                    "--new-set with an anchor but NO chain: the count to discard cannot be verified. If you are sure, "
                    "pass --discard-count N with the number of sealed runs you believe were counted (it is logged)"
                )
            if lock_runs is not None and discard_count != lock_runs:
                raise LockError(
                    f"--new-set with no chain: lock.json still says {lock_runs} sealed run(s); "
                    f"pass --discard-count {lock_runs} to discard them on purpose"
                )
        set_id = uuid.uuid4().hex
        prebuilt = make_lock(self.eval_dir, names, thresholds, lock_fields).model_copy(
            update={"keyed": bool(self.key)}
        )
        data = {
            "set_id": set_id,
            "keyed": bool(self.key),
            "key_id": self._key_id(),
            "core_hash": core_hash_of(prebuilt),
            "files_sha": files_sha_of(prebuilt),
        }
        if reason:
            data |= {
                "reason": reason,
                "previous_head": prev[-1]["sha"] if prev else None,
                "discarded_runs": counted if chain_existed else discard_count,
                "lock_test_runs": lock_runs,
            }
        if reason:
            seen_sets = {
                e["data"].get("files_sha") for e in prev if e["kind"] in ("genesis", "new_set")
            }
            if data["files_sha"] in seen_sets:
                raise LockError(
                    "--new-set refused: these frozen files are IDENTICAL to a set that was already frozen and run "
                    "against; a new set must have different test files (its hashes would give the same set a fresh "
                    "count)"
                )
        old = None
        backups: dict[Path, Path] = {}
        appended = lock_created = False
        existed_before: set[Path] = set()  # only anchors this freeze CREATES may be removed
        for anchor in self.anchors:
            try:
                anchor.stat()
            except FileNotFoundError:
                continue
            existed_before.add(anchor)
        try:
            for (
                anchor
            ) in self.anchors:  # path to path: the old anchors are put back if this freeze fails
                backup = anchor.with_name(anchor.name + ".bak")
                try:
                    shutil.copyfile(anchor, backup)
                except FileNotFoundError:
                    continue
                backups[anchor] = backup
            entry = self.chain.append("new_set" if reason else "genesis", data)
            appended = True

            def seal(lock: Lock) -> Lock:
                return self._sealed(lock.model_copy(update={"chain_head": entry["sha"]}))

            if (
                reason and lock_path(self.eval_dir).exists()
            ):  # moved aside only AFTER the append succeeded
                moved = lock_path(self.eval_dir).with_name(
                    f"lock.json.prev-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}"
                )
                os.replace(lock_path(self.eval_dir), moved)
                old = moved  # only now: a failed move leaves nothing to move back
            lock = freeze(
                self.eval_dir, names, thresholds, no_clobber=True, seal=seal, prebuilt=prebuilt
            )
            lock_created = True
            history = _dedupe([s for a in anchors for s in a.get("sets", [])])
            history.append(
                {"set_id": set_id, "created": entry["data"]["ts"], "reason": reason or None}
            )
            self._write_anchors(history, bool(self.key))
            for b in backups.values():
                b.unlink(missing_ok=True)
        except BaseException as original:
            # undo in reverse: the new anchors, the new lock, the move of the old lock, our chain entry, the backups.
            # Every step is tried even when an earlier one fails; failures are surfaced and a marker is written.
            problems: list[str] = []

            def step(name: str, fn) -> None:
                try:
                    fn()
                except Exception as err:  # noqa: BLE001 - keep undoing; report all
                    problems.append(f"{name}: {type(err).__name__}")

            for a in self.anchors:
                if a in backups:
                    step(f"restore {a.name}", lambda a=a: os.replace(backups[a], a))
                elif a not in existed_before:
                    step(f"remove {a.name}", lambda a=a: a.unlink(missing_ok=True))
            if lock_created:
                step(
                    "remove the new lock.json",
                    lambda: lock_path(self.eval_dir).unlink(missing_ok=True),
                )
            if old is not None:
                step(
                    "put the old lock.json back", lambda: os.replace(old, lock_path(self.eval_dir))
                )
            if appended:
                if chain_existed:
                    step("take the chain entry back", lambda: self.chain.truncate_to(len(prev)))
                else:
                    step("remove the new chain", lambda: self.chain.path.unlink(missing_ok=True))
            for b in backups.values():
                step("remove a backup", lambda b=b: b.unlink(missing_ok=True))
            if problems:
                marker = self.eval_dir / RECOVERY_MARKER
                with contextlib.suppress(OSError):
                    marker.write_text(
                        "A freeze failed and its rollback was incomplete.\n"
                        f"Original error: {type(original).__name__}\nRollback problems: {'; '.join(problems)}\n"
                        f"The previous lock.json (if any) is at: {old}\n"
                        "Restore it by hand, delete this file, then run `eval reconcile`.\n",
                        encoding="utf-8",
                    )
                raise LockError(
                    f"freeze failed ({type(original).__name__}) AND the rollback is incomplete: "
                    f"{'; '.join(problems)}; see {RECOVERY_MARKER}"
                ) from original
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
        if (self.eval_dir / RECOVERY_MARKER).exists():
            raise LockError(
                f"a failed freeze left {RECOVERY_MARKER}: finish its recovery by hand first"
            )
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
        recorded = entries[shas.index(lock.chain_head)]["data"].get("core_hash")
        if recorded is None and self.key and check_seal:
            raise LockError(
                "the chain entry at the lock's position has no core_hash (a keyed chain must)"
            )
        if recorded is not None and core_hash_of(lock) != recorded and check_seal:
            raise LockError(
                "lock.json differs from what the sealed-run chain recorded at its position (something other than "
                "the hand-written defect fields was edited)"
            )
        return lock, entries, torn

    def load(self) -> Lock:
        """lock.json verified against the chain, with crash recovery. Raises `LockError` on a mismatch."""
        lock, entries, torn = self._load()
        return self._finish_load(lock, entries, torn)

    def _finish_load(
        self, lock: Lock, entries: list[dict], torn: bool, verify: bool = True
    ) -> Lock:
        if (
            verify
        ):  # BEFORE anything is written: a lock must not be re-sealed over a broken evidence set
            verify_reports(entries, self.runs_dir)
            if stray := unchained_runs(entries, self.runs_dir):
                raise LockError(
                    f"run folder(s) {stray[:3]} hold results that the chain has no sealed run for: lock.json and the "
                    "chain look rolled back while the run folders stayed. Recovery: if the folder is not yours, move "
                    "it out of the runs folder; if lock.json and the chain were restored from a backup, restore BOTH "
                    "from the newer backup (or from git for lock.json plus the audit folder copy)"
                )
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
        try:
            status = _status_of(live, self.runs_dir, self.running())
        except LockError:
            if verify:
                raise
            status = "unverified"  # `eval report-lost` loads without verifying; it is about to mark exactly this
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
        """Right after `write_run`: put the SHA-256 of report.json, report.md and results.jsonl into the chain, so a
        later change or deletion is noticed. (Residual: it hashes what is on disk at this moment.)"""
        lock = self.load()
        folder = self.runs_dir / run_id
        digest = file_sha256(folder / "report.json")
        if digest is None:
            raise LockError("there is no report.json to record")
        self._commit(
            lock,
            "report",
            {
                "run_id": run_id,
                "sha256": digest,
                "report_md_sha256": file_sha256(folder / "report.md"),
                "results_sha256": file_sha256(folder / "results.jsonl"),
            },
        )

    def mark_report_lost(self, run_id: str, reason: str) -> None:
        """The audited way out when a recorded run folder was pruned, moved or lost: a `report_lost` chain entry with a
        reason (20+ characters). The run's status becomes "unverified" (no `aborted` second look). It never touches the
        counter; `eval report` shows the run as LOST with this reason."""
        if len((reason or "").strip()) < MIN_REASON_CHARS:
            raise LockError(f"--reason must be at least {MIN_REASON_CHARS} characters")
        lock, entries, torn = self._load()
        rec, problem = _problem(entries, self.runs_dir, run_id)
        if rec is None:
            raise LockError(f"the chain has no recorded report for run {run_id}")
        if problem is None:
            raise LockError(
                f"the recorded files of run {run_id} are intact: there is nothing to mark lost"
            )
        if any(
            e["kind"] == "report_lost"
            and e["data"].get("run_id") == run_id
            and e["seq"] > rec["seq"]
            for e in entries
        ):
            raise LockError(f"run {run_id} is already marked lost")
        lock = self._finish_load(lock, entries, torn, verify=False)
        self._commit(
            lock, "report_lost", {"run_id": run_id, "reason": reason.strip(), "found": problem}
        )

    def defect_run_ok(self, run_id: str) -> bool:
        """A harness defect may cite only a run of the CURRENT set that finished with a recorded, verified report."""
        entries = self.chain.entries()
        base = (
            max(
                (i for i, e in enumerate(entries) if e["kind"] in ("genesis", "new_set")),
                default=-1,
            )
            + 1
        )
        live = entries[base:]
        if not any(e["kind"] == "sealed_run" and e["data"]["run_id"] == run_id for e in live):
            return False
        rec, problem = _problem(entries, self.runs_dir, run_id)
        return (
            rec is not None
            and problem is None
            and report_state(entries, self.runs_dir, run_id) in ("complete", "aborted")
        )

    def finish(self, run_id: str, status: str) -> None:
        lock = self.load()
        # the report on disk outranks the caller's idea of the status: results that exist are never 'aborted'
        state = report_state(self.chain.entries(), self.runs_dir, run_id)
        status = state if state in ("complete", "aborted", "unverified") else status
        if state is None and status == "complete":
            status = "unverified"  # the caller wrote results that are not there (deleted before they were recorded)
        self._commit(lock, "sealed_done", {"run_id": run_id, "status": status})

    def record_smoke(self, key: str) -> None:
        lock = self.load()
        self._commit(lock, "smoke_pass", {"key": key}, smoke_key=key)

    def reconcile(self) -> tuple[int, int]:
        """The explicit, audited form of the recovery `load()` does: returns (lock test_runs before, after)."""
        before = read_lock(self.eval_dir).test_runs
        return before, self.load().test_runs

    def rotate_key(self) -> None:
        """Re-key the chain: a `rekey` entry signed with the OLD key (it names the new key id), then every later entry
        and the lock's seal under the NEW key, and the anchors' key id updated. Needs `old_keys` (the previous key)
        and `key` (the new one). Audited; the counter and the history are untouched."""
        if not (self.key and self.chain.old_keys):
            raise LockError("rotate-key needs the new key and the previous key configured")
        old = SealedGate(
            self.eval_dir,
            self.chain.path,
            self.runs_dir,
            self.chain.old_keys[-1],
            self.anchors,
            self.chain.old_keys[:-1],
        )
        lock = old.load()  # the lock and chain must verify under the previous key first
        nohead = lock.model_copy()
        entry = self.chain.append(
            "rekey",
            {
                "new_key_id": self._key_id(),
                "core_hash": core_hash_of(nohead),
                "files_sha": files_sha_of(nohead),
            },
            signing_key=self.chain.old_keys[-1],
        )
        write_lock(
            self.eval_dir, self._sealed(nohead.model_copy(update={"chain_head": entry["sha"]}))
        )
        for a in self.anchors:
            body = json.loads(a.read_text(encoding="utf-8"))
            body["key_id"] = self._key_id()
            _write_json(a, body)

    def reseal(self) -> list[str]:
        """Key holder only: bless the hand-written harness-defect fields in lock.json and NOTHING else. The rest of the
        lock must still match the hash stored at the last commit; the counter, chain and anchors must agree; at least
        one hand field must be set. The edit is logged. Run it after reading `git diff lock.json`."""
        if not self.key:
            raise LockError("`eval reseal` needs the sealed-run key (sealed_key_secret_name)")
        disk = read_lock(self.eval_dir)
        entries = self.chain.entries()
        head = next((e for e in entries if e["sha"] == disk.chain_head), None)
        if (
            head is None
            or head["data"].get("core_hash") is None
            or core_hash_of(disk) != head["data"]["core_hash"]
            or files_sha_of(disk) != head["data"].get("files_sha")
        ):
            raise LockError(
                "reseal refused: something other than the hand-written defect fields differs from what the "
                "chain recorded (files, thresholds, caps, counter ...); restore lock.json from the repository first"
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
    value = value.strip()
    if len(value) < MIN_KEY_CHARS:
        raise LockError(f"the sealed-run key must be at least {MIN_KEY_CHARS} characters")
    return value.strip().encode("utf-8")  # a trailing newline in a secret must not change the key
