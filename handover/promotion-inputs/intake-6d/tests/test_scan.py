"""WP6 package 6b (brief-v3 8, 15.4): the inbox scan, the race-safe bounded reader and the in-process ``intake extract`` tests. No HTTP here (6d owns the
route). Every test fails against a stub that skips its check (the mutants of brief 15.7, group WP6)."""

from __future__ import annotations

import ast
import dataclasses
import os
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from conftest import MINI, ROOT, settings_for_tests
from intake import budget, cli, inbox, model, review_page, service, workqueue
from intake.codes import ConfigError, Refused

POSIX = sys.platform != "win32"
OLD = time.time() - 600


class Counting:
    """A model wrapper that counts the calls (the guarded model is the real fake-backend guard)."""

    def __init__(self, m):
        self.m, self.calls = m, 0

    def call(self, req):
        self.calls += 1
        return self.m.call(req)


def put(s, name: str, data: bytes, age_s: float | None = None) -> Path:
    p = inbox.inbox_dir(s) / name
    p.write_bytes(data)
    t = OLD if age_s is None else time.time() - age_s
    os.utime(p, (t, t))
    return p


def mini(s, *names):
    for n in names:
        put(s, n, (MINI / n).read_bytes())


def make(tmp_path, max_files: int | None = None, min_age_s: int | None = None):
    s = settings_for_tests(tmp_path, with_ledger=True)
    if max_files is not None:
        s = dataclasses.replace(s, service=dataclasses.replace(s.service, scan_max_files=max_files))
    if min_age_s is not None:
        s = dataclasses.replace(s, service=dataclasses.replace(s.service, scan_min_age_s=min_age_s))
    return s


def scanner(s):
    m = Counting(model.build_guarded(s))
    return inbox.Scanner(s, m), m


def go(sc):
    """One scan; an exception is a test FAILURE (an assertion-class one, so the mutant run counts it as a kill, not a crash)."""
    try:
        r = sc.try_scan()
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"try_scan raised {type(e).__name__}")
    if r is None:
        pytest.fail("try_scan answered busy")
    return r


INBOX_GONE = "bad_config: the inbox folder is missing or unreadable"


def config_error_code(sc) -> str:
    """The code of the ``ConfigError`` a scan raises; any other outcome is a test FAILURE (assertion class)."""
    try:
        sc.try_scan()
    except ConfigError as e:
        assert type(e) is inbox.InboxUnavailable, type(e).__name__  # the type 6d maps to the fixed 503
        return f"{e.code}: {e.text}"
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"try_scan raised {type(e).__name__}, not a config error")
    pytest.fail("try_scan gave no error")


def reasons(res) -> dict[str, str]:
    return {r.name: r.reason for r in res.refused}


# ---- spec 11 -----------------------------------------------------------------------------------------------------------------------------------
def test_three_new_files_take_two_scans(tmp_path):
    s = make(tmp_path)
    mini(s, "inv-A.txt", "inv-B.txt", "inv-C.txt")
    sc, _ = scanner(s)
    r1 = go(sc)
    assert (r1.examined, len(r1.new), r1.remaining, r1.duplicates) == (3, 2, 1, 0)
    r2 = go(sc)
    assert (len(r2.new), r2.remaining, r2.duplicates) == (1, 0, 2)
    assert {n.item_id for n in r1.new}.isdisjoint({n.item_id for n in r2.new})


def test_refused_or_duplicate_at_front_blocks_nothing(tmp_path):
    s = make(tmp_path)
    mini(s, "inv-A.txt", "inv-B.txt")
    sc, _ = scanner(s)
    assert len(go(sc).new) == 2
    put(s, "0-unlisted.txt", b"not on the list\n")
    put(s, "0b-copy.txt", (MINI / "inv-A.txt").read_bytes())
    mini(s, "inv-C.txt")
    r = go(sc)
    assert len(r.new) == 1 and r.new[0].item_id.startswith("inv-C")
    assert reasons(r) == {"0-unlisted.txt": "not_on_list"} and r.duplicates == 3 and r.remaining == 0


def test_pdf_non_utf8_nul_become_x18(tmp_path):
    s = make(tmp_path, 10)
    put(s, "a.pdf", b"%PDF-1.4 fake")
    put(s, "b.txt", b"\xff\xfe\xfa")
    put(s, "c.txt", b"text\x00more")
    sc, m = scanner(s)
    r = go(sc)
    assert len(r.new) == 3 and all(n.flags == ("X18",) and n.state == "NEEDS_PERSON" for n in r.new) and m.calls == 0


def test_unlisted_txt_refused_not_on_list(tmp_path):
    s = make(tmp_path)
    put(s, "u.txt", b"Invoice from nowhere\n")
    r = go(scanner(s)[0])
    assert reasons(r) == {"u.txt": "not_on_list"} and r.new == () and workqueue.list_items(s) == []


# ---- eligibility and refusals -----------------------------------------------------------------------------------------------------------------
def test_min_age_skipped(tmp_path):
    s = make(tmp_path)
    put(s, "inv-A.txt", (MINI / "inv-A.txt").read_bytes(), age_s=0)
    r = go(scanner(s)[0])
    assert (r.examined, r.new, r.refused) == (0, (), ())
    os.utime(inbox.inbox_dir(s) / "inv-A.txt", (OLD, OLD))
    assert len(go(scanner(s)[0]).new) == 1


def test_bad_names(tmp_path):
    s = make(tmp_path)
    for n in ("bad name.txt", ".hidden.txt", "CON.txt", "-lead.txt", "a" * 200 + ".txt"):
        put(s, n, b"x")
    r = go(scanner(s)[0])
    assert set(reasons(r).values()) == {"bad_name"} and len(r.refused) == 5 and r.new == ()


@pytest.mark.skipif(not POSIX, reason="symlinks need privileges on Windows; the junction test covers Windows")
def test_symlink_outside_inbox(tmp_path):
    s = make(tmp_path, min_age_s=0)
    outside = tmp_path / "outside.txt"
    outside.write_bytes((MINI / "inv-A.txt").read_bytes())
    link = inbox.inbox_dir(s) / "l.txt"
    link.symlink_to(outside)
    r = go(scanner(s)[0])
    assert reasons(r) == {"l.txt": "outside_inbox"} and r.new == ()


@pytest.mark.skipif(POSIX, reason="junctions are Windows only")
def test_junction_outside_inbox(tmp_path):
    s = make(tmp_path, min_age_s=0)
    target = tmp_path / "elsewhere"
    target.mkdir()
    (target / "x.txt").write_bytes(b"x")
    j = inbox.inbox_dir(s) / "j.txt"
    subprocess.run(["cmd", "/c", "mklink", "/J", str(j), str(target)], check=True, capture_output=True)  # noqa: S603, S607
    r = go(scanner(s)[0])
    assert reasons(r) == {"j.txt": "outside_inbox"} and r.new == ()


def test_hardlink_outside_inbox(tmp_path):
    s = make(tmp_path, min_age_s=0)
    outside = tmp_path / "outside.txt"
    outside.write_bytes((MINI / "inv-A.txt").read_bytes())
    os.link(outside, inbox.inbox_dir(s) / "h.txt")
    r = go(scanner(s)[0])
    assert reasons(r) == {"h.txt": "outside_inbox"} and r.new == ()


@pytest.mark.skipif(not POSIX, reason="no FIFO in a Windows folder")
def test_fifo_not_a_file(tmp_path):
    s = make(tmp_path)
    p = inbox.inbox_dir(s) / "f.txt"
    os.mkfifo(p)
    os.utime(p, (OLD, OLD))
    done = []
    t = threading.Thread(target=lambda: done.append(go(scanner(s)[0])), daemon=True)
    t.start()
    t.join(2)
    assert done and reasons(done[0]) == {"f.txt": "not_a_file"}


def test_size_boundary(tmp_path):
    s = make(tmp_path)
    cap = s.service.max_file_bytes
    put(s, "exact.txt", b"a" * cap)
    put(s, "over.txt", b"a" * (cap + 1))
    r = go(scanner(s)[0])
    assert reasons(r) == {"over.txt": "too_large"}  # the exact-size file is read (it is then an X28 item: far over 20000 characters)
    assert [n.flags for n in r.new] == [("X28",)]


def test_growing_file_bounded():
    seen = []

    def endless(n):
        seen.append(n)
        return b"x" * n

    with pytest.raises(Refused) as e:
        inbox._read_bounded(endless, 1000)
    assert e.value.code == "too_large" and sum(seen) == 1001
    assert inbox._read_bounded((lambda it: lambda n: next(it))(iter([b"ab", b""])), 5) == b"ab"


def test_growing_file_bounded_through_read_plain_file(tmp_path, monkeypatch):
    """A file that keeps growing while it is read: ``read_plain_file`` stops at cap + 1 bytes and refuses it ``too_large``."""
    p = regular(tmp_path, data=b"tiny")
    asked = []

    class Endless:
        def __init__(self, real):
            self.real = real

        def read(self, n=-1):
            asked.append(n)
            return b"x" * n

        def fileno(self):
            return self.real.fileno()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            self.real.close()

    if POSIX:
        monkeypatch.setattr(inbox.os, "read", lambda fd, n: (asked.append(n), b"x" * n)[1])
    else:
        monkeypatch.setattr(inbox, "open", lambda path, mode="r": Endless(open(path, mode)), raising=False)
    assert code_of(lambda: inbox.read_plain_file(p, 1000)) == "too_large" and sum(asked) == 1001


def test_subfolder_ignored(tmp_path):
    s = make(tmp_path)
    d = inbox.inbox_dir(s)
    (d / "changes").mkdir()
    (d / "sub.txt").mkdir()
    (d / "changes" / "inv-A.txt").write_bytes((MINI / "inv-A.txt").read_bytes())
    for sub in (d / "changes", d / "sub.txt"):
        os.utime(sub, (OLD, OLD))  # old enough, so only the "ignore directories" rule keeps them out
    r = go(scanner(s)[0])
    assert (r.examined, r.new, r.refused, r.duplicates) == (0, (), (), 0)


# ---- race-safe reader (brief 8.2) -------------------------------------------------------------------------------------------------------------
def regular(tmp_path, name="f.txt", data=b"hello"):
    p = tmp_path / name
    p.write_bytes(data)
    return p


def code_of(fn) -> str:
    with pytest.raises(Refused) as e:
        fn()
    return e.value.code


def swap_before_open(monkeypatch, target: Path, action) -> None:
    """Run ``action()`` once, in the window between ``read_plain_file``'s lstat and its open of ``target`` (the race)."""
    done = []

    def once():
        if not done:
            done.append(1)
            action()

    if POSIX:
        real = os.open
        monkeypatch.setattr(inbox.os, "open", lambda p, *a, **k: (once() if Path(p) == target else None, real(p, *a, **k))[1])
    else:
        monkeypatch.setattr(inbox, "open", lambda p, mode="r": (once() if Path(p) == target else None, open(p, mode))[1], raising=False)


@pytest.mark.skipif(not POSIX, reason="FIFO and O_NONBLOCK are POSIX")
def test_fifo_swap_does_not_block(tmp_path, monkeypatch):
    p = regular(tmp_path)

    def to_fifo():  # lstat saw a regular file; the open meets a FIFO with no writer
        p.unlink()
        os.mkfifo(p)

    swap_before_open(monkeypatch, p, to_fifo)
    out = []
    t = threading.Thread(target=lambda: out.append(code_of(lambda: inbox.read_plain_file(p, 100))), daemon=True)
    t.start()
    t.join(1)
    assert out == ["not_a_file"] and not inbox._SCAN_LOCK.locked()


@pytest.mark.skipif(not POSIX, reason="O_NOFOLLOW is POSIX")
def test_symlink_swap_refused(tmp_path, monkeypatch):
    p = regular(tmp_path)
    moved = tmp_path / "moved.txt"

    def to_link():  # same inode behind the link, so only O_NOFOLLOW can refuse it
        p.rename(moved)
        p.symlink_to(moved)

    swap_before_open(monkeypatch, p, to_link)
    assert code_of(lambda: inbox.read_plain_file(p, 100)) == "outside_inbox"


def test_inode_swap_refused(tmp_path, monkeypatch):
    p = regular(tmp_path)

    st0 = os.lstat(p)

    def to_other_file():  # same size and modification time, so only the (device, inode) identity can tell the files apart
        other = tmp_path / "other.txt"
        other.write_bytes(b"world")
        os.utime(other, ns=(st0.st_atime_ns, st0.st_mtime_ns))
        os.replace(other, p)

    swap_before_open(monkeypatch, p, to_other_file)
    assert code_of(lambda: inbox.read_plain_file(p, 100)) == "outside_inbox"


@pytest.mark.skipif(not POSIX, reason="a directory descriptor is POSIX")
def test_inbox_dir_swap_refused(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    d = inbox.inbox_dir(s)
    evil = tmp_path / "evil"
    evil.mkdir()
    (evil / "inv-A.txt").write_bytes(b"not on the list\n")
    os.utime(evil / "inv-A.txt", (OLD, OLD))
    real = os.scandir

    def swap_after_listing(arg):
        it = real(arg)
        d.rename(tmp_path / "inbox.moved")
        d.symlink_to(evil)
        return it

    monkeypatch.setattr(inbox.os, "scandir", swap_after_listing)
    r = go(scanner(s)[0])
    assert r.refused == () and len(r.new) == 1  # the original file was read through the descriptor; nothing of the other folder


def test_unreadable_file_blocks_nothing(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt", "inv-B.txt")
    put(s, "0-locked.txt", b"locked")
    real = inbox.read_plain_file

    def locked(path, cap, **kw):
        if Path(path).name == "0-locked.txt":
            raise PermissionError(13, "held by another program")
        return real(path, cap, **kw)

    monkeypatch.setattr(inbox, "read_plain_file", locked)
    r = go(scanner(s)[0])
    assert reasons(r) == {"0-locked.txt": "not_a_file"} and len(r.new) == 2


def test_vanished_file_skipped(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    put(s, "0-gone.txt", b"gone")
    real = inbox.read_plain_file

    def gone(path, cap, **kw):
        if Path(path).name == "0-gone.txt":
            raise FileNotFoundError(2, "vanished")
        return real(path, cap, **kw)

    monkeypatch.setattr(inbox, "read_plain_file", gone)
    r = go(scanner(s)[0])
    assert (r.examined, r.refused, len(r.new)) == (1, (), 1)


def test_windows_file_id_checked(tmp_path, monkeypatch):
    """Windows: two files have distinct, non-zero (dev, ino) pairs. A volume that reports no file id is ONE folder-level error (not one refusal per
    file): a swap could not be seen there, and every file would fail alike."""
    if POSIX:
        pytest.skip("Windows only (the POSIX variant is inode_swap_refused)")
    p1, p2 = regular(tmp_path, "id1.txt"), regular(tmp_path, "id2.txt")
    s1, s2 = os.lstat(p1), os.lstat(p2)
    assert s1.st_ino != 0 and s2.st_ino != 0 and (s1.st_dev, s1.st_ino) != (s2.st_dev, s2.st_ino)
    real = os.lstat

    def no_id(path, **kw):
        r = real(path, **kw)
        return os.stat_result((r.st_mode, 0, r.st_dev, r.st_nlink, r.st_uid, r.st_gid, r.st_size, r.st_atime, r.st_mtime, r.st_ctime))

    monkeypatch.setattr(inbox.os, "lstat", no_id)
    try:
        inbox.read_plain_file(p1, 100)
    except ConfigError as e:
        assert type(e) is inbox.InboxUnavailable and (e.code, e.text) == ("bad_config", "this volume has no file ids")
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"a volume without file ids gave {type(e).__name__}, not the folder-level config error")
    else:
        pytest.fail("a volume without file ids was read")
    s = make(tmp_path / "scan")
    mini(s, "inv-A.txt", "inv-B.txt")
    assert config_error_code(scanner(s)[0]) == "bad_config: this volume has no file ids" and not inbox._SCAN_LOCK.locked()


def rewrite_after_read(monkeypatch, p, action):
    real = inbox._read_bounded

    def read_then_act(read, cap):
        out = real(read, cap)
        action()
        return out

    monkeypatch.setattr(inbox, "_read_bounded", read_then_act)


def test_file_changed_during_read_refused(tmp_path, monkeypatch):
    p = regular(tmp_path, data=b"first half")

    def append():
        with open(p, "ab") as f:  # the writer finishes (or continues) after the reader got its bytes
            f.write(b" and more")

    rewrite_after_read(monkeypatch, p, append)
    assert code_of(lambda: inbox.read_plain_file(p, 100)) == "changed_while_read"


def test_same_size_rewrite_with_a_new_mtime_refused(tmp_path, monkeypatch):
    p = regular(tmp_path, data=b"12345")
    st0 = os.lstat(p)

    def rewrite():
        p.write_bytes(b"abcde")  # same size
        os.utime(p, ns=(st0.st_atime_ns, st0.st_mtime_ns + 5_000_000_000))

    rewrite_after_read(monkeypatch, p, rewrite)
    assert code_of(lambda: inbox.read_plain_file(p, 100)) == "changed_while_read"


@pytest.mark.skipif(not POSIX, reason="the change time is a POSIX field (on Windows it is the creation time)")
def test_rewrite_that_restores_the_mtime_refused_by_ctime(tmp_path, monkeypatch):
    p = regular(tmp_path, data=b"12345")
    st0 = os.lstat(p)

    def rewrite():
        time.sleep(
            0.05
        )  # the kernel's change-time clock is coarse (a few ms): without this the rewrite can land in the same tick as the file's creation
        p.write_bytes(b"abcde")
        os.utime(p, ns=(st0.st_atime_ns, st0.st_mtime_ns))  # size and mtime look untouched; only the change time moved

    rewrite_after_read(monkeypatch, p, rewrite)
    assert code_of(lambda: inbox.read_plain_file(p, 100)) == "changed_while_read"


def test_scan_refuses_a_file_replaced_after_the_filter(tmp_path, monkeypatch):
    """The reader takes its own lstat, so the scan compares its filter lstat with a second one after the read (the reader's shape is frozen)."""
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    target = inbox.inbox_dir(s) / "inv-A.txt"
    st0 = os.lstat(target)
    real = inbox.read_plain_file

    def read_then_touch(path, cap, **kw):
        data = real(path, cap, **kw)
        os.utime(target, ns=(st0.st_atime_ns, st0.st_mtime_ns + 7_000_000_000))  # rewritten by someone else after the filter
        return data

    monkeypatch.setattr(inbox, "read_plain_file", read_then_touch)
    r = go(scanner(s)[0])
    assert reasons(r) == {"inv-A.txt": "changed_while_read"} and r.new == () and workqueue.list_items(s) == []


def test_read_plain_file_uses_read_bounded(tmp_path, monkeypatch):
    p = regular(tmp_path)
    seen = []
    real = inbox._read_bounded
    monkeypatch.setattr(inbox, "_read_bounded", lambda read, cap: (seen.append(cap), real(read, cap))[1])
    assert inbox.read_plain_file(p, 77) == b"hello" and seen == [77]


def test_read_plain_file_refuses_a_hard_link(tmp_path):
    p = regular(tmp_path)
    os.link(p, tmp_path / "second-name.txt")
    assert code_of(lambda: inbox.read_plain_file(p, 100)) == "outside_inbox"


def test_read_plain_file_refuses_a_symlink(tmp_path):
    p = regular(tmp_path)
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(p)
    except OSError:
        pytest.skip("this account may not create symlinks (the POSIX run covers it)")
    assert code_of(lambda: inbox.read_plain_file(link, 100)) == "outside_inbox"


def test_read_plain_file_signature():
    import inspect

    ps = inspect.signature(inbox.read_plain_file).parameters
    assert list(ps) == ["path", "cap", "dir_fd"] and ps["dir_fd"].kind is inspect.Parameter.KEYWORD_ONLY


def test_read_plain_file_plain_cases(tmp_path):
    p = regular(tmp_path, data=b"abc")
    assert inbox.read_plain_file(p, 3) == b"abc"
    assert code_of(lambda: inbox.read_plain_file(p, 2)) == "too_large"
    assert code_of(lambda: inbox.read_plain_file(tmp_path, 10)) == "not_a_file"
    with pytest.raises(FileNotFoundError):
        inbox.read_plain_file(tmp_path / "missing.txt", 10)


# ---- scan semantics ---------------------------------------------------------------------------------------------------------------------------
def test_gate_rechecked_before_insert(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt", "inv-B.txt")
    real = inbox.reader.read

    def read_then_empty_the_list(name, data):
        out = real(name, data)
        (s.intake_home / "synthetic_hashes.txt").write_text("", encoding="utf-8")  # STOP pressed after the listing
        return out

    monkeypatch.setattr(inbox.reader, "read", read_then_empty_the_list)
    r = go(scanner(s)[0])
    assert r.new == () and set(reasons(r).values()) == {"not_on_list"} and workqueue.list_items(s) == []


def test_x28_item(tmp_path):
    s = make(tmp_path)
    put(s, "big.txt", (b"line of invoice text\n" * 1200))
    sc, m = scanner(s)
    r = go(sc)
    assert [(n.flags, n.state) for n in r.new] == [(("X28",), "NEEDS_PERSON")] and m.calls == 0


def test_duplicate_same_bytes_two_names(tmp_path):
    s = make(tmp_path)
    data = (MINI / "inv-A.txt").read_bytes()
    put(s, "a1.txt", data)
    put(s, "a2.txt", data)
    r = go(scanner(s)[0])
    assert len(r.new) == 1 and r.duplicates == 1


def test_duplicate_at_insert_takes_no_slot(tmp_path, monkeypatch):
    s = make(tmp_path, 3)
    mini(s, "inv-A.txt", "inv-B.txt")
    sc, _ = scanner(s)
    assert len(go(sc).new) == 2
    mini(s, "inv-C.txt")
    monkeypatch.setattr(inbox.workqueue, "known_sources", lambda *a, **k: frozenset())  # the race: the set missed the stored items
    r = go(sc)
    assert [n.item_id[:5] for n in r.new] == ["inv-C"] and r.duplicates == 2


def test_phase_two_refusals_do_not_keep_their_slot(tmp_path, monkeypatch):
    s = make(tmp_path)  # two slots
    mini(s, "inv-A.txt", "inv-B.txt", "inv-C.txt")
    real = inbox.pipeline.process

    def refuse_a_and_b(s_, parsed, model_, suppliers):
        if parsed.name in ("inv-A.txt", "inv-B.txt"):
            raise Refused("id_collision", "another file has this name")
        return real(s_, parsed, model_, suppliers)

    monkeypatch.setattr(inbox.pipeline, "process", refuse_a_and_b)
    sc, _ = scanner(s)
    r = go(sc)
    assert reasons(r) == {"inv-A.txt": "id_collision", "inv-B.txt": "id_collision"}
    assert [n.item_id[:5] for n in r.new] == ["inv-C"] and r.remaining == 0  # C, which only waited, took the freed slot
    assert go(sc).new == ()  # the next scan: C is a duplicate now, A and B are refused again, nothing waits forever


def test_remaining_counts_only_new(tmp_path):
    s = make(tmp_path)
    mini(s, "inv-A.txt", "inv-B.txt", "inv-C.txt")
    put(s, "zz-unlisted.txt", b"unlisted\n")
    put(s, "zz-copy.txt", (MINI / "inv-A.txt").read_bytes())
    r = go(scanner(s)[0])
    assert len(r.new) == 2 and r.remaining == 1 and r.duplicates == 1 and len(r.refused) == 1


def test_reply_json_keys_exact(tmp_path):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    put(s, "u.txt", b"unlisted\n")
    j = go(scanner(s)[0]).as_json()
    assert set(j) == {"examined", "new", "refused", "duplicates", "remaining"}
    assert set(j["new"][0]) == {"item_id", "state", "flags"} and isinstance(j["new"][0]["flags"], list)
    assert j["refused"] == [{"name": "u.txt", "reason": "not_on_list"}]


def test_busy_second_scan(tmp_path):
    s = make(tmp_path)
    sc, _ = scanner(s)
    assert inbox._SCAN_LOCK.acquire(blocking=False)
    try:
        assert sc.try_scan() is None and sc.running() is True
    finally:
        inbox._SCAN_LOCK.release()
    assert sc.running() is False


def test_lock_released_after_error(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    monkeypatch.setattr(inbox.pipeline, "process", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    sc, _ = scanner(s)
    with pytest.raises(RuntimeError):
        sc.try_scan()
    assert not inbox._SCAN_LOCK.locked() and not sc.running()


def test_halted_refused(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    monkeypatch.setattr(budget, "halt_state_readonly", lambda s: (True, "model_mismatch"))
    sc, m = scanner(s)
    with pytest.raises(Refused) as e:
        sc.try_scan()
    assert e.value.code == "budget_halted" and "model_mismatch" not in str(e.value) and m.calls == 0
    assert workqueue.list_items(s) == [] and not inbox._SCAN_LOCK.locked()


def test_spend_unreadable_refuses_scan(tmp_path):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    sc, m = scanner(s)
    budget.ledger_path(s).unlink()
    with pytest.raises(Refused) as e:
        sc.try_scan()
    assert e.value.code == "ledger_missing" and m.calls == 0 and workqueue.list_items(s) == []


def test_no_model_call_for_flagged_refused_duplicate(tmp_path):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    sc, m = scanner(s)
    go(sc)
    first = m.calls
    assert first > 0
    put(s, "p.pdf", b"%PDF")
    put(s, "u.txt", b"unlisted\n")
    put(s, "copy.txt", (MINI / "inv-A.txt").read_bytes())
    r = go(sc)
    assert len(r.new) == 1 and r.duplicates == 2 and len(r.refused) == 1 and m.calls == first


def test_settle_failed_propagates(tmp_path):
    s = make(tmp_path)
    mini(s, "inv-A.txt")

    class Down:
        def call(self, req):
            raise ConfigError("settle_failed", "the spend ledger could not write")

    with pytest.raises(ConfigError) as e:
        inbox.Scanner(s, Down()).try_scan()
    assert e.value.code == "settle_failed" and not inbox._SCAN_LOCK.locked()
    assert [i.state for i in workqueue.list_items(s)] == ["RECEIVED"]


def test_crash_mid_scan_recovers_l02(tmp_path):
    s = make(tmp_path)
    mini(s, "inv-A.txt")

    class Crash:
        def call(self, req):
            raise KeyboardInterrupt  # the process dies after the insert and before the result

    with pytest.raises(KeyboardInterrupt):
        inbox.Scanner(s, Crash()).try_scan()
    assert [i.state for i in workqueue.list_items(s)] == ["RECEIVED"]  # write-ahead: the item exists
    workqueue.recover_received(s, serve_lock_held=lambda: True)
    items = workqueue.list_items(s)
    assert [(i.state, i.flags) for i in items] == [("NEEDS_PERSON", ("L02",))]


def test_burst_100_files(tmp_path):
    s = make(tmp_path, 100)
    for i in range(50):
        put(s, f"u{i:02d}.pdf", b"pdf%d" % i)
    for i in range(25):
        put(s, f"v{i:02d}.pdf", b"pdf0")  # the same raw bytes as u00.pdf
        put(s, f"r{i:02d}.txt", b"unlisted %d\n" % i)
    sc, m = scanner(s)
    r = go(sc)
    assert (r.examined, len(r.new), len(r.refused), r.duplicates, r.remaining) == (100, 50, 25, 25, 0)
    assert r.examined == len(r.new) + len(r.refused) + r.duplicates
    assert len(workqueue.list_items(s)) == 50 and m.calls == 0
    r2 = go(sc)  # nothing double-applied
    assert (len(r2.new), len(r2.refused), r2.duplicates) == (0, 25, 75) and len(workqueue.list_items(s)) == 50


def test_purged_file_rescanned_as_new(tmp_path):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    sc, _ = scanner(s)
    first = go(sc).new[0]
    old = workqueue.get(s, first.item_id)
    workqueue.purge(s, first.item_id, by="tester")
    second = go(sc)
    assert len(second.new) == 1 and second.duplicates == 0
    new = workqueue.get(s, second.new[0].item_id)
    assert new.uid != old.uid and new.source_sha256 == old.source_sha256


def test_last_refused_replaced_by_each_scan(tmp_path):
    s = make(tmp_path)
    put(s, "u.txt", b"unlisted\n")
    sc, _ = scanner(s)
    go(sc)
    assert sc.last_refused() == (inbox.Refusal("u.txt", "not_on_list"),)
    (inbox.inbox_dir(s) / "u.txt").unlink()
    go(sc)
    assert sc.last_refused() == ()


def test_scan_deadline_s(tmp_path):
    s = make(tmp_path)
    assert inbox.scan_deadline_s(s) == s.service.scan_max_files * 2 * s.model.deadline_s + 30 == 150


def test_scan_memory_and_reply_are_bounded(tmp_path):
    s = make(tmp_path, 2)
    for i in range(150):
        put(s, f"r{i:03d}.txt", b"unlisted %d" % i)
    for i in range(10):
        put(s, f"u{i:02d}.pdf", b"pdf%d" % i)
    sc, _ = scanner(s)
    r = go(sc)
    assert r.examined == 160 and len(r.refused) == inbox.MAX_REFUSED == 100 and r.refused_total == 150
    assert len(sc.last_refused()) == 100 and len(r.new) == 2 and r.remaining == 8
    assert len(go(sc).new) == 2  # the rest are taken by later scans, two at a time


def test_missing_inbox_is_a_config_error(tmp_path):
    s = make(tmp_path)
    inbox.inbox_dir(s).rmdir()
    assert config_error_code(scanner(s)[0]) == INBOX_GONE and not inbox._SCAN_LOCK.locked()


@pytest.mark.skipif(not POSIX, reason="symlink creation needs privileges on Windows")
def test_symlinked_inbox_is_a_config_error(tmp_path):
    s = make(tmp_path)
    d = inbox.inbox_dir(s)
    d.rename(tmp_path / "real-inbox")
    d.symlink_to(tmp_path / "real-inbox")
    assert config_error_code(scanner(s)[0]) == INBOX_GONE


def test_other_config_errors_are_not_inbox_unavailable(tmp_path, monkeypatch):
    """6d maps ONLY ``InboxUnavailable`` to the fixed 503: a damaged queue (``bad_config`` from the queue code) must stay a plain ConfigError (500)."""
    s = make(tmp_path)
    mini(s, "inv-A.txt")

    def damaged(*a, **k):
        raise ConfigError("bad_config", "queue schema version mismatch")

    monkeypatch.setattr(inbox.workqueue, "known_sources", damaged)
    try:
        scanner(s)[0].try_scan()
    except inbox.InboxUnavailable:
        pytest.fail("a damaged queue was reported as an unavailable inbox")
    except ConfigError as e:
        assert e.code == "bad_config" and "queue" in e.text
    else:
        pytest.fail("a damaged queue gave no error")
    assert issubclass(inbox.InboxUnavailable, ConfigError) and not inbox._SCAN_LOCK.locked()


def test_unreadable_inbox_listing_is_a_config_error(tmp_path, monkeypatch):
    s = make(tmp_path)

    def denied(arg):
        raise PermissionError(13, "denied")

    monkeypatch.setattr(inbox.os, "scandir", denied)
    assert config_error_code(scanner(s)[0]) == INBOX_GONE and not inbox._SCAN_LOCK.locked()


@pytest.mark.skipif(POSIX, reason="junctions are Windows only")
def test_junctioned_inbox_is_a_config_error(tmp_path):
    s = make(tmp_path)
    d = inbox.inbox_dir(s)
    d.rename(tmp_path / "real-inbox")
    subprocess.run(["cmd", "/c", "mklink", "/J", str(d), str(tmp_path / "real-inbox")], check=True, capture_output=True)  # noqa: S603, S607
    assert config_error_code(scanner(s)[0]) == INBOX_GONE


def test_refusal_name_stays_raw(tmp_path):
    """``Refusal.name`` is the raw file name, untouched by the scan (control and bidirectional characters included): escaping is the duty of the
    consumers (6c for HTML, 6d for log lines and JSON), and their own tests check it. Altering the name here would hide what the folder really holds."""
    s = make(tmp_path)
    nasty = "evil" + chr(0x202E) + chr(0x2066) + ".txt"  # right-to-left override and isolate: bad_name
    try:
        put(s, nasty, b"x")
    except OSError:
        pytest.skip("this filesystem refuses the name")
    sc, _ = scanner(s)
    r = go(sc)
    assert [x.name for x in r.refused] == [nasty] and [x.name for x in sc.last_refused()] == [nasty]
    assert r.as_json()["refused"] == [{"name": nasty, "reason": "bad_name"}]


# ---- intake extract (in process) ---------------------------------------------------------------------------------------------------------------
def run_cli(monkeypatch, tmp_path, path):
    monkeypatch.setenv("HADAVIN_LOCAL", str(tmp_path / "local"))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "fake")
    return cli.main(["extract", str(path)])


def test_extract_uses_read_plain_file(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path, with_ledger=True)
    seen = []
    real = inbox.read_plain_file

    def spy(path, cap, **kw):
        seen.append((Path(path).name, cap))
        return real(path, cap, **kw)

    monkeypatch.setattr(inbox, "read_plain_file", spy)
    assert run_cli(monkeypatch, tmp_path, MINI / "inv-A.txt") == 0
    assert seen == [("inv-A.txt", s.service.max_file_bytes)] and '"' in capsys.readouterr().out


def test_extract_not_a_file_exit_2(tmp_path, monkeypatch, capsys):
    settings_for_tests(tmp_path, with_ledger=True)
    assert run_cli(monkeypatch, tmp_path, tmp_path) == 2
    assert "not_a_file" in capsys.readouterr().err
    assert run_cli(monkeypatch, tmp_path, tmp_path / "missing.txt") == 3
    assert "Traceback" not in capsys.readouterr().err


# ---- class pin ----------------------------------------------------------------------------------------------------------------------------------
def test_probe_calls_only_in_reader_and_scan():
    """Every file probe, link/junction test, path resolution or directory listing in inbox.py sits in ``read_plain_file`` or ``Scanner._scan``; cli.py has none."""
    tree = ast.parse((ROOT / "src" / "intake" / "inbox.py").read_text(encoding="utf-8"))
    probes = {
        "os.lstat",
        "os.stat",
        "os.open",
        "os.fstat",
        "os.scandir",
        "open",
        "os.path.isjunction",
        "os.path.isdir",
        "os.path.isfile",
        "os.path.exists",
    }
    attrs = {"stat", "lstat", "open", "exists", "is_file", "is_dir", "is_symlink", "resolve", "read_bytes", "read_text"}
    bad = []

    def walk(node, owner):
        for ch in ast.iter_child_nodes(node):
            o = ch.name if isinstance(ch, ast.FunctionDef) else owner
            if isinstance(ch, ast.Call):
                f = ch.func
                dotted = ast.unparse(f)
                if (dotted in probes or (isinstance(f, ast.Attribute) and f.attr in attrs)) and o not in ("read_plain_file", "_scan"):
                    bad.append((o, dotted))
            walk(ch, o)

    walk(tree, "<module>")
    assert bad == []


# ---- added by package 6a2 (checks the 6a/6b duplicate build found missing) ------------------------------------------------------------------------------
def test_known_duplicate_is_counted_before_the_gate(tmp_path):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    assert len(go(scanner(s)[0]).new) == 1
    (s.intake_home / "synthetic_hashes.txt").write_text("", encoding="utf-8")  # the list no longer holds A, but A already has an item
    r = go(scanner(s)[0])
    assert r.duplicates == 1 and r.refused == () and r.new == ()


def test_missing_inbox_is_a_config_error_and_frees_the_lock(tmp_path):
    s = make(tmp_path)
    inbox.inbox_dir(s).rmdir()
    sc, _ = scanner(s)
    try:
        sc.try_scan()
    except ConfigError as e:
        assert e.code == "bad_config"
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"a missing inbox left the scan as {type(e).__name__}")
    else:
        pytest.fail("a missing inbox gave no error")
    assert not sc.running()


def test_an_entry_whose_lstat_fails_is_refused_and_counted(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt", "inv-B.txt")
    real = os.lstat

    def fake(path, *a, **kw):
        if os.path.basename(str(path)) == "inv-B.txt":
            raise PermissionError(13, "denied")
        return real(path, *a, **kw)

    monkeypatch.setattr(os, "lstat", fake)
    r = go(scanner(s)[0])
    assert reasons(r) == {"inv-B.txt": "not_a_file"} and len(r.new) == 1
    assert r.examined == len(r.new) + len(r.refused) + r.duplicates  # zero lost


HOSTILE = ["semi;colon.txt", "caf" + chr(0xE9) + ".txt", "bidi" + chr(0x202E) + "name.txt", "ctl" + chr(1) + "name.txt", "a" * 129 + ".txt"]


@pytest.mark.parametrize("name", HOSTILE)
def test_hostile_names_are_bad_names(tmp_path, name):
    s = make(tmp_path)
    try:
        put(s, name, b"x")
    except (OSError, ValueError):
        pytest.skip("this file system cannot hold that name")
    r = go(scanner(s)[0])
    assert r.refused == (inbox.Refusal(name, "bad_name"),) and r.new == () and workqueue.list_items(s) == []


@pytest.mark.parametrize("damage", ["key_absent", "bad_value", "empty_value"])
def test_spend_unreadable_other_states_refuse_the_scan(tmp_path, damage):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    sql = {
        "key_absent": "DELETE FROM meta WHERE k = 'halted'",
        "bad_value": "UPDATE meta SET v = '2' WHERE k = 'halted'",
        "empty_value": "UPDATE meta SET v = '' WHERE k = 'halted'",
    }[damage]
    c = sqlite3.connect(budget.ledger_path(s), isolation_level=None)
    try:
        c.execute(sql)
    finally:
        c.close()
    sc, m = scanner(s)
    with pytest.raises(Refused) as e:
        sc.try_scan()
    assert e.value.code == "ledger_missing" and m.calls == 0 and workqueue.list_items(s) == []


def test_scan_refusals_map_to_a_status_and_a_sentence():
    assert service.STATUS["budget_halted"] == 503 and service.STATUS["ledger_missing"] == 503
    assert set(inbox.REFUSAL_CODES) <= set(review_page.ERROR_TEXT)
