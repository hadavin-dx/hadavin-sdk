"""The inbox scan and the race-safe bounded file reader (brief-v3 4.3, 8). ``read_plain_file`` is the ONE bounded reader in ``src``: the scan and
``intake extract`` both use it (WP2a review m2 class fix). It is the only place that opens an inbox file; the probe calls (``lstat``, ``os.open``, ``fstat``)
sit inside it and the scan loop, never anywhere else (pinned by ``tests/test_scan.py::probe_calls_only_in_reader_and_scan``)."""

from __future__ import annotations

import errno
import hashlib
import heapq
import logging
import os
import re
import stat
import sys
import threading
import time
import traceback
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from . import budget, pipeline, reader, safe_text, workqueue
from . import settings as cfg
from .codes import ConfigError, Refused
from .names import is_forbidden as name_char_forbidden
from .names import safe_name
from .settings import Settings

if (
    sys.platform != "win32"
):  # the lockfile.py pattern: a plain import, no getattr (the capability scan allows only O_NOFOLLOW through getattr)
    from os import O_DIRECTORY, O_NOFOLLOW, O_NONBLOCK

REFUSAL_CODES = (
    "bad_name",
    "outside_inbox",
    "not_a_file",
    "too_large",
    "not_on_list",
    "id_collision",
    "changed_while_read",
    "read_timeout",
    "future_mtime",
    "flag_capped",
)
_SCAN_LOCK = threading.Lock()  # one scan at a time (non-blocking acquire), the pattern of exporter._EXPORT_LOCK
_CHUNK = 65536
MAX_REFUSED = (
    100  # refusals kept and returned per scan (a folder of 10,000 bad files must not grow the reply); ``refused_total`` counts all
)
MAX_LISTED = (
    10_000  # directory entries one scan looks at; a bigger folder is scanned in ROTATING slices (ended "listing_cap"), never switched off
)
MAX_READS = (
    200  # files whose BYTES one scan reads (a skip-cache hit or a refusal from ``lstat`` alone costs none); the rest wait for the next scan
)
MIN_READ_S = (
    1.0  # a read is not started with less than this much scan time left (a cold read then looks like a hang): the scan ends deadline
)
BATCH = 64  # entries whose lstat run together in one timed worker
MAX_FLAGGED_PER_WINDOW = (
    100  # hand-back items (X18, X28) one scanner adds per FLAGGED_WINDOW_S; more are refused flag_capped, counted, not queued
)
FLAGGED_WINDOW_S = 3600
MAX_FLAGGED_OPEN = 500  # hand-back items waiting for a person in the queue; at this size no more are added
MAX_REMEMBERED = (
    2 * MAX_LISTED + 1
)  # remembered files: strictly more than the entries of one slice plus the stale keys pruned before the next scan
SKIP_TTL_S = 300  # a remembered refusal for a read error is tried again after this many seconds (a permission may have been fixed)
SHA_TTL_S = (
    900  # a remembered "this file has this hash" is read again after this many seconds (the change key cannot see a same-tick rewrite)
)
READ_TIMEOUT_S = (
    20.0  # one file read (open, read, second lstat) may take this long; then it is abandoned (a hung share, a stuck filter driver)
)
MAX_ABANDONED = 4  # abandoned reads still hanging: with this many the scan stops (ended "deadline") instead of starting another
FUTURE_MTIME_S = 86400  # a modification time more than this far in the future is refused (future_mtime), a smaller skew is accepted
MAX_NAME_SHOWN = 200  # characters of a file name kept in a Refusal
log = logging.getLogger("intake.inbox")
_FRAME = re.compile(r'File "([^"]*)", line (\d+)')
_TRANSIENT = ("changed_while_read",)  # refusal codes never remembered: the file is expected to settle


class InboxUnavailable(ConfigError):  # noqa: N818 (name fixed by erratum 101a)
    """The inbox folder (missing, unreadable, a link) or its volume (no file ids) cannot be scanned: a folder-level problem, not one file's. It is
    a ``ConfigError`` with code ``bad_config`` so ``intake extract`` still exits 3, but it has its own type so ``serve`` can answer ONLY this one with
    the fixed 503 and leave every other ``ConfigError`` (a damaged queue, say) at 500."""

    def __init__(self, text: str) -> None:
        super().__init__("bad_config", text)


@dataclass(frozen=True)
class Refusal:
    """One refused file. ``name`` must be SAFE: no control, escape, bidirectional or format character (``names.safe_name`` leaves it unchanged) and at
    most ``MAX_NAME_SHOWN`` + 3 characters, or the constructor raises ``ValueError`` (a literal backslash is allowed: ``safe_name`` doubles it). Make a safe name from a raw one with ``Refusal.of``, which shows
    those characters as visible escape text (backslash, x or u, hex digits) and cuts a long name. So a page, a log line or the JSON reply never receives a raw hostile
    name; consumers still escape for their own medium (HTML for 6c). Two names that differ only in such characters can look alike here."""

    name: str
    reason: str  # in REFUSAL_CODES

    def __post_init__(self) -> None:
        if len(self.name) > MAX_NAME_SHOWN + 3 or any(name_char_forbidden(c) for c in self.name):
            raise ValueError("Refusal.name is not safe: build it with Refusal.of")

    @classmethod
    def of(cls, raw_name: str, reason: str) -> Refusal:
        return cls(safe_name(raw_name, MAX_NAME_SHOWN), reason)


@dataclass(frozen=True)
class NewItem:
    item_id: str
    state: str
    flags: tuple[str, ...]


@dataclass(frozen=True)
class ScanResult:
    """``remaining`` = new files that waited for a slot + listed files this scan did not look at (read cap or deadline: an upper bound, they may be
    folders or duplicates). ``examined == len(new) + refused_total + duplicates + waiting``. The fields after ``remaining`` are NOT in ``as_json``
    (spec 11 has exactly five keys); 6d may add them to its reply only as an additive change."""

    examined: int
    new: tuple[NewItem, ...]
    refused: tuple[Refusal, ...]
    duplicates: int
    remaining: int
    refused_total: int = 0  # all refusals of the scan; ``refused`` keeps the first MAX_REFUSED
    skipped_young: int = 0  # files younger than ``scan_min_age_s``: not examined, not in ``remaining``; a later scan takes them
    ended: str = "done"  # "done"; "deadline", "read_cap", "listing_cap" or "abandoned_reads" (stopped cleanly: rescan; "abandoned_reads" = NO PROGRESS, too many hung reads); "error" (the partial result of a scan that raised)
    error: str = ""  # with ended == "error": the code of the exception (or its type name)
    vanished: int = 0  # listed names that were gone when looked at (deleted or renamed during the scan): counted, not examined

    def as_json(self) -> dict:
        """Exactly the five keys of spec 11."""
        return {
            "examined": self.examined,
            "new": [{"item_id": n.item_id, "state": n.state, "flags": list(n.flags)} for n in self.new],
            "refused": [{"name": r.name, "reason": r.reason} for r in self.refused],
            "duplicates": self.duplicates,
            "remaining": self.remaining,
        }


def inbox_dir(s: Settings) -> Path:
    return s.intake_home / "inbox"


def _same_file(a: os.stat_result, b: os.stat_result) -> bool:
    return (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino)


def _read_bounded(read, cap: int) -> bytes:
    """``read(n)`` until ``cap + 1`` bytes or the end: a file that grows or reports size 0 cannot run past the cap."""
    out = bytearray()
    while len(out) <= cap:
        chunk = read(min(_CHUNK, cap + 1 - len(out)))
        if not chunk:
            break
        out += chunk
    if len(out) > cap:
        raise Refused("too_large", "file is over the size limit")
    return bytes(out)


def read_plain_file(path: Path, cap: int, *, dir_fd: int | None = None) -> bytes:
    """THE race-safe bounded reader (brief-v3 8.2). With ``dir_fd`` (POSIX scan) ``path`` is a bare name opened relative to that directory. ``Refused("not_a_file" | "outside_inbox" |
    "too_large")``; ``FileNotFoundError`` and other ``OSError`` pass through (the scan skips or refuses the entry; ``extract`` exits 3 on a missing file)."""
    st0 = (
        os.lstat(path, dir_fd=dir_fd) if dir_fd is not None else os.lstat(path)
    )  # identity reference for the open below; the scan's own lstat only filters
    if stat.S_ISLNK(st0.st_mode) or sys.platform == "win32" and os.path.isjunction(path):
        raise Refused("outside_inbox", "a link is not read")
    if not stat.S_ISREG(st0.st_mode):
        raise Refused("not_a_file", "not a plain file")
    # no file id (FUSE, WebDAV, some NAS): a swap could not be seen, and every file would fail alike, so it is one folder-level error
    if sys.platform == "win32" and st0.st_ino == 0:
        raise InboxUnavailable("this volume has no file ids")
    if sys.platform == "win32":
        with open(path, "rb") as f:
            _check_identity(os.fstat(f.fileno()), st0)
            data = _read_bounded(f.read, cap)
            _check_unchanged(os.fstat(f.fileno()), st0)
            return data
    try:
        fd = os.open(path, os.O_RDONLY | O_NOFOLLOW | O_NONBLOCK, dir_fd=dir_fd)  # NONBLOCK: a FIFO swapped in after lstat returns at once
    except OSError as e:
        if e.errno == errno.ELOOP:  # O_NOFOLLOW met a symlink: swapped in after the lstat
            raise Refused("outside_inbox", "a link is not read") from None
        raise
    try:
        _check_identity(os.fstat(fd), st0)
        data = _read_bounded(lambda n: os.read(fd, n), cap)
        _check_unchanged(os.fstat(fd), st0)
        return data
    finally:
        os.close(fd)


def _check_identity(st: os.stat_result, st0: os.stat_result) -> None:
    if not stat.S_ISREG(st.st_mode):
        raise Refused("not_a_file", "not a plain file")
    if st.st_nlink != 1 or not _same_file(st, st0):  # a hard link, or another file swapped in between lstat and open
        raise Refused("outside_inbox", "the file was swapped or is linked from elsewhere")


def _change_key(st: os.stat_result) -> tuple:
    """What a rewrite moves: size and modification time; on POSIX also the change time (users cannot set it, so a rewrite that restores the old
    modification time is still seen). On Windows ``st_ctime`` is the creation time, so it is left out. Residual (also in ``failure_modes.md``): a rewrite
    that keeps the size and falls inside the same timestamp tick of the file system as the first read is not seen on any platform."""
    key = (st.st_size, st.st_mtime_ns)
    if sys.platform != "win32":
        key += (st.st_ctime_ns,)
    return key


def _check_unchanged(st: os.stat_result, st0: os.stat_result) -> None:
    """A file rewritten while it was read may be half written: refuse it; a later scan sees the settled file."""
    if _change_key(st) != _change_key(st0):
        raise Refused("changed_while_read", "the file changed while it was being read")


def scan_deadline_s(s: Settings) -> int:
    """``scan_max_files`` x 2 x ``model.deadline_s`` + 30: the default for ``service.Limits.scan_s`` and for ``Scanner.try_scan``'s deadline."""
    return s.service.scan_max_files * 2 * s.model.deadline_s + 30


def _lstat(name: str, dir_fd: int | None, inbox: Path) -> tuple[Path, os.stat_result]:
    """(path, lstat) of one inbox entry; on POSIX the name is relative to the directory descriptor."""
    path = Path(name) if dir_fd is not None else inbox / name
    return path, (os.lstat(name, dir_fd=dir_fd) if dir_fd is not None else os.lstat(path))


def _file_key(name: str, st: os.stat_result) -> tuple:
    """Which file, in which state: the NAME (a rename from .pdf to .txt is a new verdict), device and file id, plus the change key."""
    return (name, st.st_dev, st.st_ino, *_change_key(st))


def _read_unchanged(
    name: str, dir_fd: int | None, inbox: Path, st: os.stat_result | None, cap: int, expect_key: tuple | None = None
) -> bytes:
    """The ONE scan read: ``read_plain_file`` and then a second ``lstat``. The reader's own lstat is its reference, so a file replaced after the
    caller's ``st`` would get a fresh one and no age check (its shape is frozen): compare with the caller's ``st`` here, so a replaced or rewritten
    file waits for a later scan (``changed_while_read``). With ``st=None`` (the second look at a waiting file) the first ``lstat`` is taken here and
    compared with ``expect_key``."""
    path = Path(name) if dir_fd is not None else inbox / name
    if st is None:
        _, st = _lstat(name, dir_fd, inbox)
        if _file_key(name, st) != expect_key:
            raise Refused("changed_while_read", "the file changed while it waited")
    data = read_plain_file(path, cap, dir_fd=dir_fd)
    _, after = _lstat(name, dir_fd, inbox)
    if not _same_file(after, st) or _change_key(after) != _change_key(st):
        raise Refused("changed_while_read", "the file changed while it was being read")
    return data


class _ReadTimeout(Exception):  # noqa: N818 (internal signal, never leaves this module)
    pass


class _WorkerFailed(Exception):  # noqa: N818 (the worker could not be started: resource exhaustion, NOT a verdict on a file)
    pass


class _ListingDeadline(Exception):  # noqa: N818
    pass


def _timed(fn, timeout: float, abandoned: list, *, close_fd: int | None = None, on_orphan=None):
    """Run ``fn`` in a daemon thread with a time limit. On time-out the thread is ABANDONED (it ends when the operating system lets it; ``close_fd``
    is closed by the thread itself, ``on_orphan(result)`` runs there if it finishes after the abandon) and ``_ReadTimeout`` is raised. An exception
    of ``fn`` is re-raised here unchanged. If the thread cannot be started, ``close_fd`` is closed and ``_WorkerFailed`` is raised."""
    box: dict = {}
    lock = threading.Lock()

    def work() -> None:
        try:
            box["v"] = fn()
        except BaseException as e:  # noqa: BLE001 (handed to the caller whole)
            box["e"] = e
        finally:
            if close_fd is not None:
                os.close(close_fd)
        with lock:
            orphan = box.get("orphan", False)
        if orphan and "v" in box and on_orphan is not None:
            on_orphan(box["v"])

    th = threading.Thread(target=work, daemon=True)
    try:
        th.start()
    except Exception:  # noqa: BLE001 (no thread available)
        if close_fd is not None:
            os.close(close_fd)
        raise _WorkerFailed from None
    th.join(timeout)
    with lock:
        if "v" not in box and "e" not in box:
            box["orphan"] = True
            abandoned.append(th)
            raise _ReadTimeout
    if "e" in box:
        raise box["e"]
    return box["v"]


def _timed_fd(make, dir_fd: int | None, timeout: float, abandoned: list):
    """``make(fd)()`` in a timed worker; the worker gets its own duplicate of the folder descriptor, so a later reuse of the number cannot send an
    abandoned worker elsewhere. A failing ``dup`` is ``_WorkerFailed`` (resource exhaustion), never a file verdict."""
    fd = None
    if dir_fd is not None:
        try:
            fd = os.dup(dir_fd)
        except OSError:
            raise _WorkerFailed from None
    return _timed(lambda: make(fd)(), timeout, abandoned, close_fd=fd)


def _walk(src, expired):
    """Stream the folder: (modification time, name) per entry; ``expired()`` is looked at every 1024 entries."""
    n = 0
    with os.scandir(src) as it:
        for e in it:
            n += 1
            if n % 1024 == 0 and expired():
                raise _ListingDeadline
            try:
                m = e.stat(follow_symlinks=False).st_mtime_ns
            except OSError:
                m = 0
            yield (m, e.name)


def _open_and_list(inbox: Path, cursor, limit: int, expired):
    """In a timed worker: the folder checks, the open and the STREAMED listing. Returns ``(root, dir_fd, slice, total, after)``: ``slice`` = the
    ``limit`` smallest (modification time, name) pairs after ``cursor`` (oldest first; a second pass over all entries only when none is after it),
    ``total`` = entries seen, ``after`` = entries after the cursor. Memory is ``limit`` pairs, never the whole folder."""
    missing = InboxUnavailable("the inbox folder is missing or unreadable")  # a folder-level problem, not a per-file one
    root: Path | None = None
    if sys.platform == "win32":
        try:
            root = inbox.resolve()  # BEFORE the link tests: a junction swapped in after them then shows as a file outside ``root``
        except (OSError, RuntimeError):
            raise missing from None
        if not os.path.isdir(inbox) or inbox.is_symlink() or os.path.isjunction(inbox):
            raise missing
    try:
        dir_fd = os.open(inbox, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW) if sys.platform != "win32" else None
    except OSError:  # missing, not a directory, or a symlink
        raise missing from None
    try:
        src = dir_fd if dir_fd is not None else inbox
        cnt = {"total": 0, "after": 0}

        def stream(cur):
            try:
                for k in _walk(src, expired):
                    cnt["total"] += 1
                    if cur is None or k > cur:
                        cnt["after"] += 1
                        yield k
            except OSError:
                raise missing from None

        got = heapq.nsmallest(limit, stream(cursor))
        if not got and cursor is not None:  # nothing after the cursor: the pass is over, start the next one
            cnt["total"] = cnt["after"] = 0
            got = heapq.nsmallest(limit, stream(None))
        return root, dir_fd, got, cnt["total"], cnt["after"]
    except BaseException:
        if dir_fd is not None:
            os.close(dir_fd)
        raise


def _stat_entries(names: list, fd: int | None, inbox: Path, root: Path | None, out: list) -> None:
    """In a timed worker: ``lstat``, the link test and (Windows) the resolved-parent test for each name; results are appended as they come, so a hang
    leaves the finished ones in ``out``. Each result: ``(name, stat, is_link, outside, error)``."""
    for name in names:
        try:
            path, st = _lstat(name, fd, inbox)
            is_link = stat.S_ISLNK(st.st_mode) or (fd is None and os.path.isjunction(path))
            outside = root is not None and not is_link and not stat.S_ISDIR(st.st_mode) and path.resolve().parent != root
            out.append((name, st, is_link, outside, None))
        except Exception as e:  # noqa: BLE001 (handed to the scan loop, which classifies it per file)
            out.append((name, None, False, False, e))


def _code(e: Refused) -> str:
    """The refusal code of a per-file ``Refused``. The reader raises only codes of ``REFUSAL_CODES``; anything else is a bug and passes up loudly
    (it used to be relabelled ``not_a_file``, which would have hidden it)."""
    if e.code not in REFUSAL_CODES:
        raise e
    return e.code


def _locator(e: BaseException) -> str:
    """file:line of the innermost frame of an exception (no values, no names of inbox files)."""
    frames = [m for m in map(_FRAME.search, traceback.format_exception(e)) if m]
    return "?" if not frames else f"{os.path.basename(frames[-1].group(1))}:{frames[-1].group(2)}"


@dataclass
class _Run:
    """The state of ONE scan, kept outside the scan body so that a scan that raises can still report what it had done (BL-intake-wp6-6b-006)."""

    refused: list[Refusal] = field(default_factory=list)
    refused_total: int = 0
    items: list[NewItem] = field(default_factory=list)
    duplicates: int = 0
    examined: int = 0
    young: int = 0
    vanished: int = 0
    flagged_made: int = 0
    unexamined: int = 0  # listed names after a stop (read cap or deadline), or the in-flight one and those after it when the scan raised
    unlisted: int = 0  # entries of a folder bigger than MAX_LISTED that are outside this scan's slice
    waiting: int = 0  # new files that took no slot in this scan
    reads: int = 0
    ended: str = "done"
    error: str = ""

    def refuse(self, name: str, code: str) -> None:
        self.refused_total += 1
        if len(self.refused) < MAX_REFUSED:
            self.refused.append(Refusal.of(name, code))

    def result(self) -> ScanResult:
        return ScanResult(
            self.examined,
            tuple(self.items),
            tuple(self.refused),
            self.duplicates,
            self.waiting + self.unexamined + self.unlisted,
            self.refused_total,
            self.young,
            self.ended,
            self.error,
            self.vanished,
        )


class Scanner:
    """One scanner per service. Contract for 6d (the route and the logs):

    * ``try_scan(deadline_s=None)`` returns a ``ScanResult`` or ``None`` (another scan runs). A scan stops cleanly at the deadline (monotonic seconds,
      default ``scan_deadline_s``; with less than ``MIN_READ_S`` left it starts no read), after ``MAX_READS`` file reads, or after a slice of
      ``MAX_LISTED`` entries: ``result.ended`` is then "deadline", "read_cap" or "listing_cap" and ``remaining`` > 0, so the caller rescans.
      ``ended == "abandoned_reads"`` means NO PROGRESS: ``MAX_ABANDONED`` earlier reads still hang (a dead share), so the scan starts no new one; 6d must
      not rescan in a tight loop on it (back off, tell the operator; a warning with the count is logged by ``intake.inbox``).
    * The folder is walked as a STREAM: memory is ``MAX_LISTED`` (modification time, name) pairs, never the whole folder, and the deadline is looked at
      while listing. A scan takes the OLDEST ``MAX_LISTED`` entries after the position where the last unfinished pass stopped (a persistent cursor that
      starts over when a pass ends), and reads oldest first, so fresh junk cannot hold a real older file back. A folder over the cap is NOT refused; the
      logger ``intake.inbox`` warns with counts (never names) at 50 and 100 percent. Operator action: move processed and refused files out.
    * Hand-back items (reader flags X18, X28) cost no model call, so they are capped: ``MAX_FLAGGED_PER_WINDOW`` per ``FLAGGED_WINDOW_S`` per scanner
      and ``MAX_FLAGGED_OPEN`` waiting in the queue; a file over the cap is refused ``flag_capped`` (counted, not queued, tried again later).
    * A document is stored once however its bytes differ: duplicates are found on the raw hash AND on the hash of the normalised text (BOM, line
      endings, composed letters), so hostile variants cost one model call.
    * A scan that RAISES (``Refused`` budget_halted / ledger_missing / db_busy, ``ConfigError`` settle_failed, ``InboxUnavailable`` ...) leaves the
      items it had already created in the queue; they are reported by ``last_partial()`` (a ``ScanResult`` with ``ended == "error"``) and as
      ``scan_partial`` on the exception when the exception can carry it. ``last_refused()`` is replaced by every scan (whole or partial) and holds
      the refusals of the latest one. 6d treats ``ended == "error"`` as "always rescan": the in-flight file and every name not yet looked at are in
      ``remaining``.
    * ``skipped_young`` (files too young to read, a modification time up to a day in the future included) is NOT in ``remaining``: 6d rescans while it
      is above zero. ``vanished`` counts listed names that were gone when looked at. ``as_json`` stays at five keys.
    * Folder open, listing, every ``lstat`` batch and every file read run in worker threads with a time limit (``READ_TIMEOUT_S``): a hung call is
      abandoned, the lock is released, a hung file is refused ``read_timeout`` (remembered ``SKIP_TTL_S``) and the scan ends "deadline". RESIDUAL,
      named plainly: the model call and the queue insert inside ``pipeline.process`` are NOT interrupted; they are bounded only by the model's own
      deadline and the database busy time, so a scan can overrun its deadline by one such call and, meanwhile, ``try_scan`` of other callers
      returns None. Abandoned threads of a dead share stay until the operating system lets them go (counted by ``MAX_ABANDONED``).
    * ``clock`` (wall seconds, for file ages) and ``monotonic`` (for the deadline) are injectable for tests."""

    def __init__(
        self, s: Settings, model, *, clock: Callable[[], float] = time.time, monotonic: Callable[[], float] = time.monotonic
    ) -> None:
        self._s = s
        self._model = model
        self._clock = clock
        self._mono = monotonic
        self._refused: tuple[Refusal, ...] = ()
        self._partial: ScanResult | None = None
        # file key -> ("sha", raw sha, gate hash or None, expires) | ("refused", code, expires): what a later scan need not read again (LRU)
        self._skip: dict[tuple, tuple] = {}
        self._by_name: dict[str, tuple] = {}  # name -> its one remembered key
        self._hung: dict[str, float] = {}  # name -> until when it is refused read_timeout without being looked at
        self._cursor: tuple | None = None  # (modification time, name) last finished by an unfinished pass
        self._warned: set[int] = set()
        self._abandoned: list[threading.Thread] = []
        self._flag_times: deque = deque()

    def running(self) -> bool:
        return _SCAN_LOCK.locked()

    def last_refused(self) -> tuple[Refusal, ...]:
        return self._refused

    def last_partial(self) -> ScanResult | None:
        """The partial result of the latest scan if it raised, else None."""
        return self._partial

    def try_scan(self, deadline_s: float | None = None) -> ScanResult | None:
        """None = another scan is in flight. ``Refused("budget_halted")`` when halted, ``Refused("ledger_missing")`` when the spend counter cannot be
        read, ``Refused("db_busy")`` when it is busy; ``InboxUnavailable`` (a ``ConfigError``) when the inbox folder is missing, unreadable or a link;
        ``ConfigError("settle_failed")`` passes through; a per-file error never leaves this method."""
        if not _SCAN_LOCK.acquire(blocking=False):
            return None
        try:
            run = _Run()
            self._partial = None
            try:
                self._scan(run, scan_deadline_s(self._s) if deadline_s is None else deadline_s)
            except BaseException as e:
                run.ended = "error"
                run.error = safe_text.clean(e.code if isinstance(e, Refused | ConfigError) else type(e).__name__)
                self._partial = run.result()
                self._refused = tuple(run.refused)
                try:
                    e.scan_partial = self._partial  # type: ignore[attr-defined]
                except Exception:  # noqa: BLE001, S110 (an exception that cannot carry it must not hide the real error)
                    pass
                raise
            self._refused = tuple(run.refused)
            return run.result()
        finally:
            _SCAN_LOCK.release()

    def _remember(self, key: tuple, entry: tuple) -> None:
        if key[1] == 0 or key[2] == 0:  # no device or file id: a swap could not be seen, nothing is served from memory
            return
        old = self._by_name.get(key[0])
        if old is not None and old != key:  # the same name in another state: the old verdict is stale
            self._skip.pop(old, None)
        if len(self._skip) >= MAX_REMEMBERED and key not in self._skip:
            gone = next(iter(self._skip))  # least recently used
            self._skip.pop(gone)
            if self._by_name.get(gone[0]) == gone:
                del self._by_name[gone[0]]
        self._skip.pop(key, None)
        self._skip[key] = entry
        self._by_name[key[0]] = key

    def _remember_refused(self, key: tuple | None, code: str) -> None:
        if key is not None and code not in _TRANSIENT:
            self._remember(key, ("refused", code, self._mono() + SKIP_TTL_S))

    def _warn_size(self, total: int) -> None:
        for pct in (50, 100):
            if total * 100 >= MAX_LISTED * pct and pct not in self._warned:
                self._warned.add(pct)
                log.warning(
                    "inbox holds %d entries, %d percent of the %d a scan looks at: move processed and refused files out of the folder",
                    total,
                    pct,
                    MAX_LISTED,
                )
            elif total * 100 < MAX_LISTED * pct:
                self._warned.discard(pct)

    def _flag_ok(self, open_flagged: int, run: _Run) -> bool:
        now = self._mono()
        while self._flag_times and self._flag_times[0] <= now - FLAGGED_WINDOW_S:
            self._flag_times.popleft()
        return len(self._flag_times) < MAX_FLAGGED_PER_WINDOW and open_flagged + run.flagged_made < MAX_FLAGGED_OPEN

    def _fail(self, e: Exception, name: str, key: tuple | None, run: _Run) -> None:
        """A per-file failure that is not a time-out: Refused (closed codes only), a sharing violation (refused, tried again at the next scan), another
        OS error (refused, remembered), any other exception = a poison pill (refused, remembered, type name and place logged, stack only at DEBUG).
        Scan-level errors (ConfigError, MemoryError, RecursionError) pass up."""
        if isinstance(e, ConfigError | MemoryError | RecursionError):
            raise e
        if isinstance(e, Refused):
            code = _code(e)
            run.refuse(name, code)
            self._remember_refused(key, code)
        elif isinstance(e, PermissionError):
            run.refuse(name, "not_a_file")  # most likely another program holds it open: NOT remembered, the next scan tries again
        elif isinstance(e, OSError):
            run.refuse(name, "not_a_file")
            self._remember_refused(key, "not_a_file")
        else:
            log.warning("inbox entry could not be processed (%s at %s)", type(e).__name__, _locator(e))
            log.debug("stack of the failure above", exc_info=e)
            run.refuse(name, "not_a_file")
            self._remember_refused(key, "not_a_file")

    def _timeout(self, t_end: float) -> float:
        return min(READ_TIMEOUT_S, max(t_end - self._mono(), MIN_READ_S))

    def _scan(self, run: _Run, deadline_s: float) -> None:
        s = self._s
        # three-state: an unreadable counter must not let a scan start (the reason is never passed on); a BUSY one is told apart (db_busy)
        halt = budget.halt_state_readonly(s, raise_busy=True)
        if halt is None:
            raise Refused("ledger_missing", "the spend counter cannot be read")
        if halt[0]:
            raise Refused("budget_halted", "spending is halted")
        t_end = self._mono() + deadline_s
        suppliers = pipeline.load_suppliers(s.intake_home / "suppliers.csv")
        known = workqueue.known_sources(s, readonly=True)  # a read-only connection: the scan's listing step cannot write the queue
        known_text = workqueue.known_text_hashes(s)
        open_flagged = workqueue.open_flagged_count(s)
        listed_path = s.intake_home / "synthetic_hashes.txt"
        listed = cfg.load_hash_list(listed_path)
        new: list[
            tuple[str, reader.ParsedDoc, tuple]
        ] = []  # parsed text kept only for the first scan_max_files new files; the rest are counted
        extras: list[
            tuple[str, str, tuple]
        ] = []  # (name, sha, file key) of new files beyond the first scan_max_files; re-read if a slot frees up
        seen: set[str] = set()
        seen_text: set[str] = set()
        cap = s.service.max_file_bytes
        inbox = inbox_dir(s)

        now = self._mono()
        self._abandoned = [t for t in self._abandoned if t.is_alive()]
        self._skip = {k: v for k, v in self._skip.items() if v[-1] > now}  # expired entries go
        self._by_name = {k[0]: k for k in self._skip}
        self._hung = {n: e for n, e in self._hung.items() if e > now}

        try:
            root, dir_fd, got, total, after = _timed(
                lambda: _open_and_list(inbox, self._cursor, MAX_LISTED, lambda: self._mono() >= t_end),
                self._timeout(t_end),
                self._abandoned,
                on_orphan=lambda r: r[1] is not None and os.close(r[1]),
            )
        except (_ReadTimeout, _ListingDeadline, _WorkerFailed) as e:
            log.warning("inbox folder could not be listed in time (%s)", type(e).__name__)
            run.ended = "deadline"
            return
        try:
            self._warn_size(total)
            run.unlisted = after - len(got)
            names = [n for _, n in got]
            name_idx = {n: i for i, n in enumerate(names)}
            done_idx = -1
            counted = False
            halt_scan = False
            try:
                for chunk_start in range(0, len(names), BATCH):
                    chunk = names[chunk_start : chunk_start + BATCH]
                    todo = [n for n in chunk if n not in self._hung]
                    statmap: dict[str, tuple] = {}
                    hung_now = None
                    if todo:
                        out: list = []
                        try:
                            _timed_fd(
                                lambda fd, todo=todo, out=out: lambda: _stat_entries(todo, fd, inbox, root, out),
                                dir_fd,
                                self._timeout(t_end),
                                self._abandoned,
                            )
                        except _ReadTimeout:
                            snap = list(out)
                            hung_now = todo[len(snap)] if len(snap) < len(todo) else None
                            out = snap
                        except _WorkerFailed:
                            log.warning("inbox: no worker thread or descriptor for the metadata batch")
                            run.ended, run.unexamined, halt_scan = "deadline", len(names) - chunk_start, True
                            break
                        statmap = {r[0]: r for r in list(out)}
                    for j, name in enumerate(chunk):
                        idx = chunk_start + j
                        run.unexamined = len(names) - idx  # the file in flight counts as not looked at until it is classified
                        if run.reads >= MAX_READS:
                            run.ended, halt_scan = "read_cap", True
                        elif self._mono() >= t_end - MIN_READ_S:
                            run.ended, halt_scan = "deadline", True
                        elif sum(t.is_alive() for t in self._abandoned) >= MAX_ABANDONED:
                            log.warning("inbox reads blocked: %d abandoned reads still hang", len(self._abandoned))
                            run.ended, halt_scan = "abandoned_reads", True
                        if halt_scan:
                            break
                        counted = False
                        key: tuple | None = None
                        stop = False
                        keep = False
                        try:
                            if name in self._hung:
                                run.examined += 1
                                counted = True
                                run.refuse(name, "read_timeout")  # hung a moment ago: refused without being looked at again
                            elif name == hung_now:
                                run.examined += 1
                                counted = True
                                run.refuse(name, "read_timeout")
                                self._hung[name] = self._mono() + SKIP_TTL_S
                                run.ended, stop = "deadline", True
                            elif name not in statmap:  # behind a hung call in this batch: not looked at
                                run.ended, halt_scan = "deadline", True
                                break
                            else:
                                _, st, is_link, outside, exc = statmap[name]
                                if exc is not None:
                                    raise exc
                                if stat.S_ISDIR(st.st_mode) and not is_link:
                                    done_idx = idx
                                    continue  # subfolders (including ``changes``) are ignored, not examined
                                age = self._clock() - st.st_mtime
                                if -FUTURE_MTIME_S <= age < s.service.scan_min_age_s:
                                    # still being written, or dated in the next day (a clock jump): a negative age counts as young
                                    run.young += 1
                                    done_idx = idx
                                    continue
                                run.examined += 1
                                counted = True
                                key = _file_key(name, st)
                                if name.endswith((".", " ")) or not (
                                    cfg.is_name_allowed(name, s.service.name_regex)
                                    and cfg.is_name_allowed(reader.stem(name), s.service.name_regex)
                                ):
                                    run.refuse(name, "bad_name")  # a name ending in dot or space is another file to Windows
                                elif is_link or st.st_nlink > 1 or outside:
                                    run.refuse(name, "outside_inbox")
                                elif not stat.S_ISREG(st.st_mode):  # FIFO, device or socket
                                    run.refuse(name, "not_a_file")
                                elif st.st_size > s.service.max_file_bytes:
                                    run.refuse(name, "too_large")
                                elif age < -FUTURE_MTIME_S:  # more than a day ahead (up to a day is young, above)
                                    run.refuse(name, "future_mtime")
                                elif self._skip_hit(key, run, name, known, known_text, seen, seen_text, listed):
                                    pass
                                else:
                                    run.reads += 1
                                    path_name = name
                                    data = _timed_fd(
                                        lambda fd, path_name=path_name, st=st: lambda: _read_unchanged(path_name, fd, inbox, st, cap),
                                        dir_fd,
                                        self._timeout(t_end),
                                        self._abandoned,
                                    )
                                    sha = hashlib.sha256(data).hexdigest()
                                    if sha in known or sha in seen:
                                        run.duplicates += 1
                                        self._remember(key, ("sha", sha, None, self._mono() + SHA_TTL_S))
                                    else:
                                        parsed = reader.read(name, data)
                                        gate_hash = None if parsed.flag else reader.send_text_hash(parsed.text)
                                        self._remember(key, ("sha", sha, gate_hash, self._mono() + SHA_TTL_S))
                                        if gate_hash is not None and (gate_hash in known_text or gate_hash in seen_text):
                                            run.duplicates += 1  # the same document in other bytes (BOM, line endings, composed letters)
                                        elif parsed.flag is None and reader.gate_decision(parsed, listed) == "not_on_list":
                                            run.refuse(name, "not_on_list")
                                        else:
                                            seen.add(sha)
                                            if gate_hash is not None:
                                                seen_text.add(gate_hash)
                                            if len(new) < s.service.scan_max_files:
                                                new.append((name, parsed, key))
                                            else:
                                                extras.append((name, sha, key))  # text dropped: memory stays bounded by scan_max_files
                        except FileNotFoundError:  # gone when looked at: counted as vanished, not examined
                            run.examined -= counted
                            run.vanished += 1
                        except _ReadTimeout:
                            run.refuse(name, "read_timeout")
                            self._remember_refused(key, "read_timeout")
                            run.ended, stop = "deadline", True
                        except (
                            _WorkerFailed
                        ):  # no thread or descriptor: not a verdict on this file, nothing is remembered, the file is looked at again
                            log.warning("inbox: no worker thread or descriptor for a file read")
                            run.examined -= counted
                            run.ended, stop, keep = "deadline", True, True
                        except Exception as e:  # noqa: BLE001 (classified by _fail: closed codes, sharing violations, poison pills)
                            # a refused entry is an examined one (examined = new + refused + duplicates + waiting)
                            run.examined += not counted
                            self._fail(e, name, key, run)
                        counted = False
                        if keep:
                            break
                        done_idx = idx
                        run.unexamined = len(names) - idx - 1
                        if stop:
                            break
                    else:
                        continue
                    break
                else:
                    run.unexamined = 0
            except BaseException:
                run.examined -= counted  # the file in flight is not classified: it is "not looked at" again, a rescan takes it
                run.waiting = len(new) + len(extras)
                raise
            cursor0 = self._cursor
            complete = run.ended == "done" and run.unlisted == 0
            if complete:
                self._cursor = None  # the pass is complete
            elif done_idx >= 0:
                self._cursor = got[done_idx]
            if run.ended == "done" and run.unlisted:
                run.ended = "listing_cap"

            def reload(name: str, sha: str, key: tuple) -> reader.ParsedDoc | None:
                """A waiting file whose turn has come (a slot was freed by a refusal): look at it again, with the checks of the first look (same file,
                same change key before and after the read) and the same bytes; None = skip it (it vanished, was refused, or changed)."""
                try:
                    data = _timed_fd(
                        lambda fd: lambda: _read_unchanged(name, fd, inbox, None, cap, key), dir_fd, self._timeout(t_end), self._abandoned
                    )
                except FileNotFoundError:
                    run.examined -= 1  # it was counted as waiting: now gone, so not examined after all
                    run.vanished += 1
                    return None
                except _ReadTimeout:
                    run.refuse(name, "read_timeout")
                    self._remember_refused(key, "read_timeout")
                    run.ended = "deadline"
                    return None
                except _WorkerFailed:
                    run.waiting += 1  # still waiting: nothing was learned about the file
                    run.ended = "deadline"
                    return None
                except Exception as e:  # noqa: BLE001 (the same rules as the main path)
                    self._fail(e, name, key, run)
                    return None
                if hashlib.sha256(data).hexdigest() != sha:
                    run.refuse(name, "changed_while_read")
                    return None
                try:
                    return reader.read(name, data)
                except Exception as e:  # noqa: BLE001 (the same rules as the main path)
                    self._fail(e, name, key, run)
                    return None

            order: list[tuple[str, reader.ParsedDoc | None, str, tuple]] = [(n, p, "", k) for n, p, k in new] + [
                (n, None, h, k) for n, h, k in extras
            ]
            run.waiting = len(order)
            for name, parsed, sha, key in order:
                if len(run.items) >= s.service.scan_max_files:
                    break
                if run.ended == "deadline" or self._mono() >= t_end:
                    run.ended = "deadline"
                    break
                run.waiting -= 1  # a refused or duplicate file is used up for this scan but takes no slot: the next file fills it
                if parsed is None:
                    parsed = reload(name, sha, key)
                    if parsed is None:
                        continue
                if parsed.flag is None and reader.gate_decision(parsed, cfg.load_hash_list(listed_path)) == "not_on_list":
                    run.refuse(name, "not_on_list")  # the list changed since the listing: no item, no slot
                    continue
                if parsed.flag is not None and not self._flag_ok(open_flagged, run):
                    run.refuse(name, "flag_capped")  # counted, not queued, not remembered: tried again when there is room
                    continue
                try:
                    got_item = pipeline.process(s, parsed, self._model, suppliers)
                except Refused as e:
                    if e.code not in ("bad_name", "id_collision"):
                        run.waiting += 1  # in flight when it failed (its item may exist, as RECEIVED): a rescan counts it
                        raise
                    run.refuse(name, e.code)
                    self._remember_refused(key, e.code)  # remembered: a folder of such files cannot starve the later ones
                    continue
                except BaseException:
                    run.waiting += 1
                    raise
                if isinstance(got_item, workqueue.Duplicate):
                    run.duplicates += 1  # lost the race at insert: no slot
                else:
                    run.items.append(NewItem(got_item.id, got_item.state, tuple(got_item.flags)))
                    if parsed.flag is not None:
                        self._flag_times.append(self._mono())
                        run.flagged_made += 1
            if not complete and run.waiting:  # an unfinished pass must not move past a file that still waits for a slot
                wi = name_idx[order[len(order) - run.waiting][0]]
                self._cursor = got[wi - 1] if wi > 0 else cursor0
        finally:
            if dir_fd is not None:
                os.close(dir_fd)

    def _skip_hit(
        self, key: tuple, run: _Run, name: str, known, known_text, seen: set[str], seen_text: set[str], listed: frozenset[str]
    ) -> bool:
        """True = the file's outcome is already known from an earlier scan (same name, same file, same state, not too old), so it is NOT read again:
        a duplicate, a file that is still not on the made-up list, or a remembered refusal. The made-up list and the queue are looked at afresh."""
        hit = self._skip.get(key)
        if hit is None:
            return False
        self._skip[key] = self._skip.pop(key)  # least-recently-used order: a file seen every scan stays, one-off names age out
        if hit[0] == "refused":
            run.refuse(name, hit[1])
            return True
        _, sha, gate_hash, _expires = hit
        if sha in known or sha in seen or (gate_hash is not None and (gate_hash in known_text or gate_hash in seen_text)):
            run.duplicates += 1
            return True
        if gate_hash is not None and gate_hash not in listed:
            run.refuse(name, "not_on_list")
            return True
        return False
