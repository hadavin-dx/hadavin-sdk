"""The inbox scan and the race-safe bounded file reader (brief-v3 4.3, 8). ``read_plain_file`` is the ONE bounded reader in ``src``: the scan and
``intake extract`` both use it (WP2a review m2 class fix). It is the only place that opens an inbox file; the probe calls (``lstat``, ``os.open``, ``fstat``)
sit inside it and the scan loop, never anywhere else (pinned by ``tests/test_scan.py::probe_calls_only_in_reader_and_scan``)."""

from __future__ import annotations

import errno
import hashlib
import os
import stat
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from . import budget, pipeline, reader, workqueue
from . import settings as cfg
from .codes import ConfigError, Refused
from .settings import Settings

if (
    sys.platform != "win32"
):  # the lockfile.py pattern: a plain import, no getattr (the capability scan allows only O_NOFOLLOW through getattr)
    from os import O_DIRECTORY, O_NOFOLLOW, O_NONBLOCK

REFUSAL_CODES = ("bad_name", "outside_inbox", "not_a_file", "too_large", "not_on_list", "id_collision", "changed_while_read")
_SCAN_LOCK = threading.Lock()  # one scan at a time (non-blocking acquire), the pattern of exporter._EXPORT_LOCK
_CHUNK = 65536
MAX_REFUSED = (
    100  # refusals kept and returned per scan (a folder of 10,000 bad files must not grow the reply); ``refused_total`` counts all
)


class InboxUnavailable(ConfigError):  # noqa: N818 (name fixed by erratum 101a)
    """The inbox folder (missing, unreadable, a link) or its volume (no file ids) cannot be scanned: a folder-level problem, not one file's. It is
    a ``ConfigError`` with code ``bad_config`` so ``intake extract`` still exits 3, but it has its own type so ``serve`` can answer ONLY this one with
    the fixed 503 and leave every other ``ConfigError`` (a damaged queue, say) at 500."""

    def __init__(self, text: str) -> None:
        super().__init__("bad_config", text)


@dataclass(frozen=True)
class Refusal:
    name: str  # RAW, untrusted file name (may hold control or bidirectional characters): every consumer escapes it (6c pages, 6d logs and JSON)
    reason: str  # in REFUSAL_CODES


@dataclass(frozen=True)
class NewItem:
    item_id: str
    state: str
    flags: tuple[str, ...]


@dataclass(frozen=True)
class ScanResult:
    examined: int
    new: tuple[NewItem, ...]
    refused: tuple[Refusal, ...]
    duplicates: int
    remaining: int
    refused_total: int = (
        0  # all refusals of the scan; ``refused`` keeps the first MAX_REFUSED (not in as_json: spec 11 has exactly five keys)
    )

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
    modification time is still seen). On Windows ``st_ctime`` is the creation time, so it is left out."""
    key = (st.st_size, st.st_mtime_ns)
    if sys.platform != "win32":
        key += (st.st_ctime_ns,)
    return key


def _check_unchanged(st: os.stat_result, st0: os.stat_result) -> None:
    """A file rewritten while it was read may be half written: refuse it; a later scan sees the settled file."""
    if _change_key(st) != _change_key(st0):
        raise Refused("changed_while_read", "the file changed while it was being read")


def scan_deadline_s(s: Settings) -> int:
    """``scan_max_files`` x 2 x ``model.deadline_s`` + 30: the default for ``service.Limits.scan_s``."""
    return s.service.scan_max_files * 2 * s.model.deadline_s + 30


class Scanner:
    def __init__(self, s: Settings, model) -> None:
        self._s = s
        self._model = model
        self._refused: tuple[Refusal, ...] = ()

    def running(self) -> bool:
        return _SCAN_LOCK.locked()

    def last_refused(self) -> tuple[Refusal, ...]:
        return self._refused

    def try_scan(self) -> ScanResult | None:
        """None = another scan is in flight. ``Refused("budget_halted")`` when halted, ``Refused("ledger_missing")`` when the spend counter cannot be
        read; ``InboxUnavailable`` (a ``ConfigError``) when the inbox folder is missing, unreadable or a link; ``ConfigError("settle_failed")`` passes
        through; a per-file ``OSError`` never leaves this method."""
        if not _SCAN_LOCK.acquire(blocking=False):
            return None
        try:
            return self._scan()
        finally:
            _SCAN_LOCK.release()

    def _scan(self) -> ScanResult:
        s = self._s
        halt = budget.halt_state_readonly(s)  # three-state: an unreadable counter must not let a scan start (the reason is never passed on)
        if halt is None:
            raise Refused("ledger_missing", "the spend counter cannot be read")
        if halt[0]:
            raise Refused("budget_halted", "spending is halted")
        suppliers = pipeline.load_suppliers(s.intake_home / "suppliers.csv")
        known = workqueue.known_sources(s)
        listed_path = s.intake_home / "synthetic_hashes.txt"
        listed = cfg.load_hash_list(listed_path)
        refused: list[Refusal] = []
        refused_total = 0
        new: list[tuple[str, reader.ParsedDoc]] = []  # parsed text kept only for the first scan_max_files new files; the rest are counted
        extras: list[tuple[str, str]] = []  # (name, sha) of new files beyond the first scan_max_files; re-read if a slot frees up
        seen: set[str] = set()
        duplicates = examined = 0

        def refuse(name: str, code: str) -> None:
            nonlocal refused_total
            refused_total += 1
            if len(refused) < MAX_REFUSED:
                refused.append(Refusal(name, code))

        inbox = inbox_dir(s)
        missing = InboxUnavailable("the inbox folder is missing or unreadable")  # a folder-level problem, not a per-file one
        if sys.platform == "win32" and (not os.path.isdir(inbox) or inbox.is_symlink() or os.path.isjunction(inbox)):
            raise missing
        try:
            dir_fd = os.open(inbox, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW) if sys.platform != "win32" else None
        except OSError:  # missing, not a directory, or a symlink
            raise missing from None
        try:
            root = inbox.resolve()
            try:
                with os.scandir(dir_fd if dir_fd is not None else inbox) as it:
                    names = sorted(e.name for e in it)
            except OSError:
                raise missing from None
            for name in names:
                counted = False
                try:
                    path = Path(name) if dir_fd is not None else inbox / name
                    st = os.lstat(name, dir_fd=dir_fd) if dir_fd is not None else os.lstat(path)
                    is_link = stat.S_ISLNK(st.st_mode) or (dir_fd is None and os.path.isjunction(path))
                    if stat.S_ISDIR(st.st_mode) and not is_link:
                        continue  # subfolders (including ``changes``) are ignored, not examined
                    if time.time() - st.st_mtime < s.service.scan_min_age_s:
                        continue  # still being written
                    examined += 1
                    counted = True
                    if not (
                        cfg.is_name_allowed(name, s.service.name_regex) and cfg.is_name_allowed(reader.stem(name), s.service.name_regex)
                    ):
                        refuse(name, "bad_name")
                    elif is_link or st.st_nlink > 1 or (dir_fd is None and path.resolve().parent != root):
                        refuse(name, "outside_inbox")
                    elif not stat.S_ISREG(st.st_mode):  # FIFO, device or socket
                        refuse(name, "not_a_file")
                    elif st.st_size > s.service.max_file_bytes:
                        refuse(name, "too_large")
                    else:
                        data = read_plain_file(path, s.service.max_file_bytes, dir_fd=dir_fd)
                        # The reader's own lstat is its reference, so a file replaced after the filter above would get a fresh one and no age check
                        # (its shape (path, cap, *, dir_fd) is frozen): compare with the filter's lstat here, so a replaced or rewritten file waits.
                        after = os.lstat(name, dir_fd=dir_fd) if dir_fd is not None else os.lstat(path)
                        if not _same_file(after, st) or _change_key(after) != _change_key(st):
                            refuse(name, "changed_while_read")
                            continue
                        sha = hashlib.sha256(data).hexdigest()
                        if sha in known or sha in seen:
                            duplicates += 1
                            continue
                        parsed = reader.read(name, data)
                        if parsed.flag is None and reader.gate_decision(parsed, listed) == "not_on_list":
                            refuse(name, "not_on_list")
                            continue
                        seen.add(sha)
                        if len(new) < s.service.scan_max_files:
                            new.append((name, parsed))
                        else:
                            extras.append((name, sha))  # text dropped: memory stays bounded by scan_max_files
                except FileNotFoundError:  # vanished after the listing: not examined, no refusal
                    examined -= counted
                except Refused as e:
                    refuse(name, e.code if e.code in REFUSAL_CODES else "not_a_file")
                except OSError:  # permission, sharing violation, I/O error: this entry only
                    examined += not counted  # a refused entry is an examined one (examined = new + refused + duplicates)
                    refuse(name, "not_a_file")

            def reload(name: str, sha: str) -> reader.ParsedDoc | None:
                """An extra file whose turn has come (a slot was freed by a refusal): read and parse it again; None = skip it (it was refused or changed)."""
                try:
                    data = read_plain_file(Path(name) if dir_fd is not None else inbox / name, s.service.max_file_bytes, dir_fd=dir_fd)
                except FileNotFoundError:
                    return None
                except Refused as e:
                    refuse(name, e.code if e.code in REFUSAL_CODES else "not_a_file")
                    return None
                except OSError:
                    refuse(name, "not_a_file")
                    return None
                return reader.read(name, data) if hashlib.sha256(data).hexdigest() == sha else None

            items: list[NewItem] = []
            order: list[tuple[str, reader.ParsedDoc | None, str]] = [(n, p, "") for n, p in new] + [(n, None, h) for n, h in extras]
            done = 0
            for name, parsed, sha in order:
                if len(items) >= s.service.scan_max_files:
                    break
                done += 1  # a refused or duplicate file is used up for this scan but takes no slot: the next file fills it
                if parsed is None:
                    parsed = reload(name, sha)
                    if parsed is None:
                        continue
                if parsed.flag is None and reader.gate_decision(parsed, cfg.load_hash_list(listed_path)) == "not_on_list":
                    refuse(name, "not_on_list")  # the list changed since the listing: no item, no slot
                    continue
                try:
                    got = pipeline.process(s, parsed, self._model, suppliers)
                except Refused as e:
                    if e.code not in ("bad_name", "id_collision"):
                        raise
                    refuse(name, e.code)
                    continue
                if isinstance(got, workqueue.Duplicate):
                    duplicates += 1  # lost the race at insert: no slot
                else:
                    items.append(NewItem(got.id, got.state, tuple(got.flags)))
        finally:
            if dir_fd is not None:
                os.close(dir_fd)
        self._refused = tuple(refused)
        return ScanResult(examined, tuple(items), tuple(refused), duplicates, len(order) - done, refused_total)
