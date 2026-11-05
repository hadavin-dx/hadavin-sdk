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
from intake import budget, cli, inbox, model, pipeline, reader, review_page, service, workqueue
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


def scanner(s, **kw):
    m = Counting(model.build_guarded(s))
    return inbox.Scanner(s, m, **kw), m


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
    monkeypatch.setattr(budget, "halt_state_readonly", lambda s, **k: (True, "model_mismatch"))
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


def test_refusal_name_is_made_safe_at_the_type_boundary(tmp_path):
    """BL-intake-wp6-6b-009: ``Refusal.name`` never carries a raw control, escape or bidirectional character, whoever builds it (the scan, a later
    consumer, a test), and is cut at MAX_NAME_SHOWN. Before: the raw name went to ``last_refused`` and ``as_json``."""
    nasty = (
        "evil" + chr(0x202E) + chr(0x2066) + chr(7) + chr(0x1B) + "[2Kx.txt"
    )  # right-to-left override, isolate, bell, a terminal erase-line
    try:
        safe = inbox.Refusal.of(nasty, "bad_name").name
    except ValueError:
        pytest.fail("Refusal.of did not make the name safe")
    assert all(ord(c) >= 0x20 and c not in (chr(0x7F), chr(0x202E), chr(0x2066)) for c in safe)
    assert ("\\u202e" in safe) and ("\\x07" in safe)
    long = inbox.Refusal.of("a" * 500 + ".txt", "bad_name").name
    assert len(long) == inbox.MAX_NAME_SHOWN + 3 and long.endswith("...")
    for raw in (nasty, "a" * 500):  # the constructor itself refuses an unsafe name: no raw hostile name can be held in a Refusal
        with pytest.raises(ValueError):
            inbox.Refusal(raw, "bad_name")
    assert inbox.Refusal("fine.txt", "bad_name").name == "fine.txt"
    s = make(tmp_path)
    try:
        put(s, nasty, b"x")
    except OSError:
        pytest.skip("this filesystem refuses the name")
    sc, _ = scanner(s)
    r = go(sc)
    assert [x.name for x in r.refused] == [safe] and [x.name for x in sc.last_refused()] == [safe]
    assert r.as_json()["refused"] == [{"name": safe, "reason": "bad_name"}]


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
                if (dotted in probes or (isinstance(f, ast.Attribute) and f.attr in attrs)) and o not in (
                    "read_plain_file",
                    "_scan",
                    "_lstat",
                    "_open_and_list",
                    "_walk",
                    "_stat_entries",
                ):
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
    assert r.refused == (inbox.Refusal.of(name, "bad_name"),) and r.new == () and workqueue.list_items(s) == []


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


# ---- added by the 6b fix batch (BL-intake-wp6-6b-003 .. 009; each fails on a69ff07) -----------------------------------------------------------------
class Tick:
    """A hand-set clock: the scan's wall clock or monotonic clock."""

    def __init__(self, t: float = 0.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


class Flaky:
    """A model wrapper that raises the given exception on the given 1-based calls (before the real model is asked: the item is already stored)."""

    def __init__(self, m, faults: dict):
        self.m, self.faults, self.n = m, faults, 0

    def call(self, req):
        self.n += 1
        if self.n in self.faults:
            raise self.faults[self.n]
        return self.m.call(req)


def queue_bytes(s) -> bytes:
    return b"".join(p.read_bytes() for p in sorted(s.intake_home.glob("queue.sqlite3*")))


def drain(sc, limit: int = 80):
    """Rescan until a scan ends with nothing remaining. Returns (item ids reported by every scan, partial or whole, names of the errors, last result)."""
    ids, raised = [], []
    for _ in range(limit):
        try:
            r = sc.try_scan()
        except (ConfigError, RuntimeError, KeyboardInterrupt) as e:
            raised.append(type(e).__name__)
            assert sc.last_partial() is not None, "a scan that raised left no partial result"
            ids += [n.item_id for n in sc.last_partial().new]
            continue
        assert r is not None
        ids += [n.item_id for n in r.new]
        if r.remaining == 0:
            return ids, raised, r
    pytest.fail("the folder did not drain")


# -- 003: a flagged too-long file stores no text
def test_x28_file_stores_no_text(tmp_path):
    s = make(tmp_path)
    put(s, "big.txt", b"REAL-LOOKING PAYMENT DETAILS 12345\n" * 700)
    r = go(scanner(s)[0])
    assert [n.flags for n in r.new] == [("X28",)]
    assert [i.source_text for i in workqueue.list_items(s)] == [""]
    assert b"PAYMENT DETAILS" not in queue_bytes(s)


def test_pipeline_stores_no_text_for_any_flagged_file(tmp_path):
    """The class: ``pipeline.process`` is the one place a flagged file reaches the queue."""
    s = make(tmp_path)
    for name, raw in (("big.txt", b"SECRET WORDS " * 3000), ("odd.pdf", b"%PDF SECRET WORDS")):
        got = pipeline.process(s, reader.read(name, raw), None, {})
        assert got.source_text == "" and b"SECRET WORDS" not in queue_bytes(s)


# -- 004: deadline, read cap, listing cap, skip cache
def test_scan_stops_cleanly_at_the_deadline(tmp_path, monkeypatch):
    s = make(tmp_path)
    for i in range(5):
        put(s, f"p{i}.pdf", b"%%PDF%d" % i)
    clock = Tick()
    real = inbox.reader.read

    def slow(name, data):
        clock.t += 10
        return real(name, data)

    monkeypatch.setattr(inbox.reader, "read", slow)
    sc, _ = scanner(s, monotonic=clock)
    r = sc.try_scan(deadline_s=25)
    assert r is not None and not sc.running() and not inbox._SCAN_LOCK.locked()
    assert (r.ended, r.examined, r.new, r.remaining) == ("deadline", 3, (), 5)  # three looked at and waiting, two never looked at
    ids, raised, last = drain(sc)  # the clock stands still now: nothing more is cut off
    assert last.ended == "done" and raised == [] and len(workqueue.list_items(s)) == 5


def test_default_deadline_is_scan_deadline_s(tmp_path, monkeypatch):
    s = make(tmp_path)
    for i in range(4):
        put(s, f"p{i}.pdf", b"%%PDF%d" % i)
    clock = Tick()
    real = inbox.reader.read
    monkeypatch.setattr(inbox.reader, "read", lambda n, d: (setattr(clock, "t", clock.t + inbox.scan_deadline_s(s) / 2 + 1), real(n, d))[1])
    r = scanner(s, monotonic=clock)[0].try_scan()
    assert r.ended == "deadline" and r.examined == 2 and r.remaining == 4


def test_read_cap_per_scan_and_no_starvation(tmp_path, monkeypatch):
    s = make(tmp_path)
    monkeypatch.setattr(inbox, "MAX_READS", 3)
    for i in range(8):
        put(s, f"p{i}.pdf", b"%%PDF%d" % i)
    sc, _ = scanner(s)
    r = go(sc)
    assert (r.ended, r.examined, len(r.new), r.remaining) == ("read_cap", 3, 2, 6)  # one waits for a slot, five were not looked at
    ids, raised, last = drain(sc)
    assert len(workqueue.list_items(s)) == 8 and len(set(ids + [n.item_id for n in r.new])) == 8 and last.ended == "done"


def test_known_files_are_not_read_again(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    put(s, "copy.txt", (MINI / "inv-A.txt").read_bytes())
    put(s, "u.txt", b"unlisted\n")
    calls = []
    real = inbox.read_plain_file
    monkeypatch.setattr(inbox, "read_plain_file", lambda p, c, **k: (calls.append(Path(p).name), real(p, c, **k))[1])
    sc, _ = scanner(s)
    r1 = go(sc)
    assert (len(r1.new), r1.duplicates, reasons(r1)) == (1, 1, {"u.txt": "not_on_list"}) and sorted(calls) == [
        "copy.txt",
        "inv-A.txt",
        "u.txt",
    ]
    del calls[:]
    r2 = go(sc)
    assert calls == [] and (len(r2.new), r2.duplicates, reasons(r2)) == (0, 2, {"u.txt": "not_on_list"})  # same answer, no bytes read
    # a rewrite is read; the made-up list is looked at afresh, so adding the hash of the (cached) unlisted text admits it with no rewrite
    data = b"unlisted\n"
    with (s.intake_home / "synthetic_hashes.txt").open("a", encoding="utf-8") as f:
        f.write(reader.send_text_hash(reader.read("u.txt", data).text) + "\n")
    r3 = go(sc)
    assert [n.item_id[:1] for n in r3.new] == ["u"] and calls == ["u.txt"]


def test_a_read_error_is_remembered_then_tried_again(tmp_path, monkeypatch):
    s = make(tmp_path)
    put(s, "locked.txt", b"x")
    calls = []

    def deny(path, cap, **kw):
        calls.append(1)
        raise OSError(5, "I/O error")

    monkeypatch.setattr(inbox, "read_plain_file", deny)
    mono = Tick(1000.0)
    sc, _ = scanner(s, monotonic=mono)
    assert reasons(go(sc)) == {"locked.txt": "not_a_file"} and len(calls) == 1
    assert reasons(go(sc)) == {"locked.txt": "not_a_file"} and len(calls) == 1  # remembered: not asked again
    mono.t += inbox.SKIP_TTL_S + 1
    assert reasons(go(sc)) == {"locked.txt": "not_a_file"} and len(calls) == 2  # tried again after the time limit


# -- 005: a burst of 10 and of 100 with the real two slots and faults, rescanned until nothing remains
def test_burst_of_ten_with_faults_loses_and_doubles_nothing(tmp_path, monkeypatch):
    s = make(tmp_path)  # the real default: two slots
    assert s.service.scan_max_files == 2
    mini(s, "inv-A.txt", "inv-B.txt", "inv-C.txt")
    put(s, "inv-A2.txt", (MINI / "inv-A.txt").read_bytes())  # same bytes as inv-A
    for i in range(4):
        put(s, f"p{i}.pdf", b"%%PDF%d" % i)
    put(s, "u1.txt", b"unlisted 1\n")
    put(s, "u2.txt", b"unlisted 2\n")
    # three faults, mid-burst: the ledger fails to settle B (ConfigError after B is stored), the model fails for C (a reply error, so C is stored
    # as a hand-back, not raised) and the handler crashes once before p1 is stored (RuntimeError)
    flaky = Flaky(model.build_guarded(s), {2: ConfigError("settle_failed", "the spend ledger could not write")})
    real_model_call, crashed = flaky.m.call, []

    def model_fails_for_c(req):
        if "C" in req.send_text[:400] and flaky.n >= 3:
            raise RuntimeError("model down")
        return real_model_call(req)

    flaky.m.call = model_fails_for_c
    real_process = inbox.pipeline.process

    def crash_once_on_p1(s_, parsed, model_, suppliers):
        if parsed.name == "p1.pdf" and not crashed:
            crashed.append(1)
            raise RuntimeError("crash")
        return real_process(s_, parsed, model_, suppliers)

    monkeypatch.setattr(inbox.pipeline, "process", crash_once_on_p1)
    sc = inbox.Scanner(s, flaky)
    ids, raised, last = drain(sc)
    assert raised == ["ConfigError", "RuntimeError"]  # both raising faults really happened, mid-burst
    items = workqueue.list_items(s)
    assert len(items) == 7 and len({i.id for i in items}) == 7 and len({i.source_sha256 for i in items}) == 7
    assert len(ids) == len(set(ids)) and set(ids) <= {i.id for i in items}  # nothing reported twice, nothing reported that is not stored
    assert last.examined == len(last.new) + last.refused_total + last.duplicates == 10 and last.remaining == 0  # nothing lost
    assert reasons(last) == {"u1.txt": "not_on_list", "u2.txt": "not_on_list"}
    states = [i.state for i in items]
    assert states.count("RECEIVED") == 1 and any(
        i.flags == ("L02",) for i in items
    )  # B waits for the recovery pass; C is a stored hand-back


def test_burst_of_100_with_two_slots_drains_without_doubles(tmp_path):
    s = make(tmp_path)  # two slots: the two-phase path with 98 waiting files
    for i in range(50):
        put(s, f"u{i:02d}.pdf", b"pdf%d" % i)
    for i in range(25):
        put(s, f"v{i:02d}.pdf", b"pdf0")  # the same raw bytes as u00.pdf
        put(s, f"r{i:02d}.txt", b"unlisted %d\n" % i)
    sc, _ = scanner(s)
    first = go(sc)
    assert len(first.new) == 2 and first.remaining > 0 and first.examined == 100
    ids, raised, last = drain(sc)
    assert raised == [] and len(workqueue.list_items(s)) == 50
    every = ids + [n.item_id for n in first.new]
    assert len(every) == len(set(every)) == 50
    assert last.examined == len(last.new) + last.refused_total + last.duplicates == 100 and last.refused_total == 25 and last.remaining == 0


# -- 006: a scan that raises still reports what it did
@pytest.mark.parametrize(
    ("fault", "code"),
    [
        (ConfigError("settle_failed", "the spend ledger could not write"), "settle_failed"),
        (RuntimeError("boom"), "RuntimeError"),
        (KeyboardInterrupt(), "KeyboardInterrupt"),
    ],
)
def test_error_mid_scan_keeps_what_was_done(tmp_path, monkeypatch, fault, code):
    s = make(tmp_path, 3)
    mini(s, "inv-A.txt", "inv-B.txt")
    put(s, "u.txt", b"unlisted\n")
    real = inbox.pipeline.process

    def fail_on_b(s_, parsed, model_, suppliers):
        if parsed.name == "inv-B.txt":
            raise fault
        return real(s_, parsed, model_, suppliers)

    monkeypatch.setattr(inbox.pipeline, "process", fail_on_b)
    sc, _ = scanner(s)
    with pytest.raises(type(fault)) as e:
        sc.try_scan()
    part = sc.last_partial()
    assert part is e.value.scan_partial and (part.ended, part.error) == ("error", code)
    assert [n.item_id[:5] for n in part.new] == ["inv-A"] and reasons(part) == {
        "u.txt": "not_on_list"
    }  # A is stored and reported, u.txt refused
    assert (
        sc.last_refused() == part.refused and part.remaining == 1 and not inbox._SCAN_LOCK.locked()
    )  # B was in flight: a rescan counts it
    monkeypatch.setattr(inbox.pipeline, "process", real)
    (inbox.inbox_dir(s) / "u.txt").unlink()
    go(sc)
    assert sc.last_partial() is None and sc.last_refused() == ()  # a good scan clears both


def test_failure_before_any_work_clears_the_old_refusals(tmp_path, monkeypatch):
    s = make(tmp_path)
    put(s, "u.txt", b"unlisted\n")
    sc, _ = scanner(s)
    go(sc)
    assert len(sc.last_refused()) == 1
    monkeypatch.setattr(budget, "halt_state_readonly", lambda s, **k: (True, "x"))
    with pytest.raises(Refused):
        sc.try_scan()
    assert sc.last_refused() == () and sc.last_partial().error == "budget_halted" and sc.last_partial().new == ()


# -- 007: a modification time in the future, and an injectable clock
def test_future_modification_time_counts_as_young_then_is_read(tmp_path):
    """A modification time up to a day ahead (a clock jump, a skewed share) is NOT old enough: it is counted as young, never read half written, never lost."""
    s = make(tmp_path)
    put(s, "inv-A.txt", (MINI / "inv-A.txt").read_bytes(), age_s=-3600)  # one hour in the future
    clock = Tick(time.time())
    sc, _ = scanner(s, clock=clock)
    r = go(sc)
    assert (r.new, r.examined, r.skipped_young) == ((), 0, 1)
    clock.t += 7200  # the clock catches up
    assert len(go(sc).new) == 1


def test_young_files_are_counted_and_the_clock_is_injectable(tmp_path):
    s = make(tmp_path)
    mini(s, "inv-A.txt")  # modified at OLD
    clock = Tick(OLD + s.service.scan_min_age_s - 1)
    sc, _ = scanner(s, clock=clock)
    r = go(sc)
    assert (r.examined, r.new, r.skipped_young, r.remaining) == (
        0,
        (),
        1,
        0,
    )  # younger than the limit: counted, not examined, not "remaining"
    clock.t = OLD + s.service.scan_min_age_s + 1
    r = go(sc)
    assert len(r.new) == 1 and r.skipped_young == 0
    clock.t = OLD - 5000  # the clock steps back: the file is "from the future" and counts as young again, it is not lost
    r = go(sc)
    assert r.skipped_young == 1 and r.examined == 0


# -- 008: the second look at a waiting file
@pytest.mark.parametrize("how", ["rewrite", "touch"])
def test_waiting_file_changed_before_its_turn_is_refused(tmp_path, monkeypatch, how):
    s = make(tmp_path)  # two slots
    mini(s, "inv-A.txt", "inv-B.txt", "inv-C.txt")
    real = inbox.pipeline.process

    def refuse_a_and_change_c(s_, parsed, model_, suppliers):
        if parsed.name == "inv-A.txt":
            p = inbox.inbox_dir(s) / "inv-C.txt"
            if how == "rewrite":
                p.write_bytes(b"something else entirely\n")
            os.utime(p, (OLD + 5, OLD + 5))
            raise Refused("id_collision", "another file has this name")  # frees the slot C waits for
        return real(s_, parsed, model_, suppliers)

    monkeypatch.setattr(inbox.pipeline, "process", refuse_a_and_change_c)
    r = go(scanner(s)[0])
    assert reasons(r) == {"inv-A.txt": "id_collision", "inv-C.txt": "changed_while_read"} and [n.item_id[:5] for n in r.new] == ["inv-B"]
    assert r.examined == len(r.new) + r.refused_total + r.duplicates + r.remaining == 3  # nothing falls out of the count


def test_waiting_file_that_vanished_is_not_counted(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt", "inv-B.txt", "inv-C.txt")
    real = inbox.pipeline.process

    def refuse_a_and_delete_c(s_, parsed, model_, suppliers):
        if parsed.name == "inv-A.txt":
            (inbox.inbox_dir(s) / "inv-C.txt").unlink()
            raise Refused("id_collision", "another file has this name")
        return real(s_, parsed, model_, suppliers)

    monkeypatch.setattr(inbox.pipeline, "process", refuse_a_and_delete_c)
    r = go(scanner(s)[0])
    assert r.examined == len(r.new) + r.refused_total + r.duplicates + r.remaining == 2


# -- 009: the group
def test_busy_ledger_is_told_from_a_missing_one(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    monkeypatch.setattr(budget, "BUSY_MS", 50)
    p = budget.ledger_path(s)
    sc, m = scanner(s)  # built first: building a guarded model writes to the ledger
    held = sqlite3.connect(p, isolation_level=None)
    try:
        held.execute("BEGIN EXCLUSIVE")
        assert budget.halt_state_readonly(s) is None  # the old contract stays for every other caller
        with pytest.raises(Refused) as e:
            budget.halt_state_readonly(s, raise_busy=True)
        assert e.value.code == "db_busy"
        with pytest.raises(Refused) as e2:
            sc.try_scan()
        assert e2.value.code == "db_busy" and m.calls == 0 and not inbox._SCAN_LOCK.locked()
        held.execute("ROLLBACK")
    finally:
        held.close()
    p.unlink()
    with pytest.raises(Refused) as e3:
        sc.try_scan()
    assert e3.value.code == "ledger_missing"  # still fails closed, with its own code
    assert service.STATUS["db_busy"] == 503


def test_an_unexpected_refusal_code_is_not_relabelled(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt")

    def odd(path, cap, **kw):
        raise Refused("some_new_code", "a reader bug")

    monkeypatch.setattr(inbox, "read_plain_file", odd)
    sc, _ = scanner(s)
    with pytest.raises(Refused) as e:
        sc.try_scan()
    assert e.value.code == "some_new_code" and sc.last_partial().error == "some_new_code" and not inbox._SCAN_LOCK.locked()


@pytest.mark.skipif(POSIX, reason="the junction race is a Windows one")
def test_root_is_resolved_before_the_junction_test(tmp_path, monkeypatch):
    s = make(tmp_path)
    here = str(inbox.inbox_dir(s))
    order = []
    real_resolve, real_junction = inbox.Path.resolve, inbox.os.path.isjunction

    def resolve(self, *a, **k):
        order.append(("resolve", str(self)))
        return real_resolve(self, *a, **k)

    def isjunction(p):
        order.append(("junction", str(p)))
        return real_junction(p)

    monkeypatch.setattr(inbox.Path, "resolve", resolve)
    monkeypatch.setattr(inbox.os.path, "isjunction", isjunction)
    go(scanner(s)[0])
    assert ("resolve", here) in order and ("junction", here) in order
    assert order.index(("resolve", here)) < order.index(("junction", here))


def test_a_resolve_failure_on_the_folder_is_a_folder_error_not_a_raw_oserror(tmp_path, monkeypatch):
    s = make(tmp_path)
    here = inbox.inbox_dir(s)
    real = inbox.Path.resolve

    def resolve(self, *a, **k):
        if self == here:
            raise OSError(5, "I/O error")
        return real(self, *a, **k)

    monkeypatch.setattr(inbox.Path, "resolve", resolve)
    sc, _ = scanner(s)
    if POSIX:
        go(sc)  # the descriptor-based scan never resolves the folder: nothing to fail
    else:
        assert config_error_code(sc) == INBOX_GONE
    assert not inbox._SCAN_LOCK.locked()


def test_extract_refuses_a_hard_link_with_a_plain_message(tmp_path, monkeypatch, capsys):
    settings_for_tests(tmp_path, with_ledger=True)
    one, two = tmp_path / "one.txt", tmp_path / "two.txt"
    one.write_bytes((MINI / "inv-A.txt").read_bytes())
    os.link(one, two)
    assert run_cli(monkeypatch, tmp_path, two) == 2
    err = capsys.readouterr().err
    assert "refused: outside_inbox" in err and "plain files" in err and "swapped" not in err and "Traceback" not in err


def test_extract_refuses_a_symlink_with_a_plain_message(tmp_path, monkeypatch, capsys):
    settings_for_tests(tmp_path, with_ledger=True)
    target, link = tmp_path / "target.txt", tmp_path / "link.txt"
    target.write_bytes((MINI / "inv-A.txt").read_bytes())
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlink creation needs privileges here")
    assert run_cli(monkeypatch, tmp_path, link) == 2
    err = capsys.readouterr().err
    assert "refused: outside_inbox" in err and "plain files" in err and "Traceback" not in err


def test_waiting_file_with_other_bytes_but_the_same_stat_is_refused(tmp_path, monkeypatch):
    """The second look reads the bytes again and compares them with the first look: bytes that differ under an unchanged ``lstat`` (a rewrite in
    the same timestamp tick) are refused, not dropped without a trace (before: ``reload`` returned None and the file fell out of the count)."""
    s = make(tmp_path)
    mini(s, "inv-A.txt", "inv-B.txt", "inv-C.txt")
    real_read, real_process, reads = inbox.read_plain_file, inbox.pipeline.process, []

    def other_bytes_the_second_time(path, cap, **kw):
        data = real_read(path, cap, **kw)
        if Path(path).name == "inv-C.txt":
            reads.append(1)
            if len(reads) == 2:
                return b"not what was read first\n"
        return data

    def refuse_a(s_, parsed, model_, suppliers):
        if parsed.name == "inv-A.txt":
            raise Refused("id_collision", "another file has this name")  # frees the slot C waits for
        return real_process(s_, parsed, model_, suppliers)

    monkeypatch.setattr(inbox, "read_plain_file", other_bytes_the_second_time)
    monkeypatch.setattr(inbox.pipeline, "process", refuse_a)
    r = go(scanner(s)[0])
    assert reasons(r) == {"inv-A.txt": "id_collision", "inv-C.txt": "changed_while_read"} and len(reads) == 2
    assert r.examined == len(r.new) + r.refused_total + r.duplicates + r.remaining == 3


# ---- batch 2 (round-2 reviews of 4a19991; each test below fails on 4a19991) -------------------------------------------------------------------------
def test_big_folder_is_scanned_in_rotating_slices_not_switched_off(tmp_path, monkeypatch):
    s = make(tmp_path)
    monkeypatch.setattr(inbox, "MAX_LISTED", 5)
    monkeypatch.setattr(inbox, "MAX_REMEMBERED", 11)
    for i in range(12):
        put(s, f"p{i:02d}.pdf", b"%%PDF%d" % i)
    sc, _ = scanner(s)
    r = go(sc)  # before: InboxUnavailable (the inbox switched off by a flood of files)
    assert r.ended == "listing_cap" and r.remaining >= 7 and r.examined == 5
    ids, raised, last = drain(sc, 40)
    assert raised == [] and len(workqueue.list_items(s)) == 12 and last.remaining == 0


def test_folder_size_warnings_carry_counts_not_names(tmp_path, monkeypatch, caplog):
    s = make(tmp_path)
    monkeypatch.setattr(inbox, "MAX_LISTED", 10)
    monkeypatch.setattr(inbox, "MAX_REMEMBERED", 21)
    for i in range(5):
        put(s, f"secret{i}.pdf", b"%%PDF%d" % i)
    sc, _ = scanner(s)
    with caplog.at_level("WARNING", logger="intake.inbox"):
        go(sc)
        assert [m for m in caplog.messages if "50 percent" in m] and not [m for m in caplog.messages if "100 percent" in m]
        for i in range(5, 11):
            put(s, f"secret{i}.pdf", b"%%PDF%d" % i)
        go(sc)
    assert [m for m in caplog.messages if "100 percent" in m] and not any("secret" in m for m in caplog.messages)


def test_create_and_delete_churn_does_not_evict_live_keys(tmp_path, monkeypatch):
    s = make(tmp_path)
    monkeypatch.setattr(inbox, "MAX_LISTED", 10)
    monkeypatch.setattr(inbox, "MAX_REMEMBERED", 21)
    put(s, "keep.txt", b"unlisted and kept\n")
    sc, _ = scanner(s)
    go(sc)
    assert any(k[0] == "keep.txt" for k in sc._skip)
    for rnd in range(40):
        made = [put(s, f"j{rnd:02d}_{i}.txt", b"junk %d %d\n" % (rnd, i)) for i in range(5)]
        go(sc)
        for p in made:
            p.unlink()
    go(sc)
    assert any(k[0] == "keep.txt" for k in sc._skip) and len(sc._skip) <= inbox.MAX_REMEMBERED


def test_a_hung_read_is_abandoned_and_the_scan_returns(tmp_path, monkeypatch):
    s = make(tmp_path)
    monkeypatch.setattr(inbox, "READ_TIMEOUT_S", 0.3)
    put(s, "aaa-hang.txt", b"x")
    mini(s, "inv-A.txt")
    release, calls, real = threading.Event(), [], inbox.read_plain_file

    def hang(path, cap, **kw):
        if Path(path).name == "aaa-hang.txt":
            calls.append(1)
            release.wait(10)
        return real(path, cap, **kw)

    monkeypatch.setattr(inbox, "read_plain_file", hang)
    sc, _ = scanner(s)
    try:
        t0 = time.monotonic()
        r = go(sc)
        assert time.monotonic() - t0 < 5 and not sc.running() and not inbox._SCAN_LOCK.locked()
        assert r.ended == "deadline" and reasons(r) == {"aaa-hang.txt": "read_timeout"} and r.remaining >= 1
        r2 = go(sc)  # remembered: not read again, and the honest file behind it gets its turn
        assert len(calls) == 1 and len(r2.new) == 1  # the pass continued after the hung file
        r3 = go(sc)
        assert len(calls) == 1 and reasons(r3) == {"aaa-hang.txt": "read_timeout"}
    finally:
        release.set()


@pytest.mark.parametrize(
    "cp",
    [
        0xD800,
        0xDFFF,
        0x034F,
        0x115F,
        0x1160,
        0x17B4,
        0x3164,
        0xFE0F,
        0xFFF9,
        0xE0100,
        0xE01EF,
        0x202E,
        0x1B,
        0x7F,
        0x0A,
        0x09,
        0x0D,
        0x206A,
        0x206F,
        0x2065,
        0xFFFC,
        0xFFA0,
        0x2800,
        0xA0,
        0x2000,
        0x200A,
        0x202F,
        0x205F,
        0x3000,
    ],
)
def test_refusal_names_are_ascii_printable_and_encodable(cp):
    safe = inbox.Refusal.of("a" + chr(cp) + "b.txt", "bad_name").name
    try:
        safe.encode("utf-8")
    except UnicodeEncodeError:
        pytest.fail("a lone surrogate reached the name")
    assert chr(cp) not in safe and all(32 <= ord(c) < 127 for c in safe)
    if cp > 0xFFFF:
        assert f"\\U{cp:08x}" in safe


def test_an_escape_sequence_in_a_name_does_not_collide_with_the_plain_name():
    esc = inbox.Refusal.of("a" + chr(0x1B) + "[2Kb.txt", "bad_name").name
    assert esc != inbox.Refusal.of("ab.txt", "bad_name").name and "x1b" in esc


def test_scan_error_text_is_clean_and_an_unattachable_exception_does_not_hide_itself(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt")

    class StubbornError(Exception):
        def __setattr__(self, k, v):
            raise AttributeError(k)

    for boom, want in ((Refused("bad" + chr(7) + "code", "x"), "bad\\x07code"), (StubbornError("real error"), "StubbornError")):
        monkeypatch.setattr(inbox.pipeline, "process", lambda *a, _b=boom, **k: (_ for _ in ()).throw(_b))
        sc, _ = scanner(s)
        try:
            sc.try_scan()
        except type(boom):
            pass
        except Exception as other:  # noqa: BLE001
            pytest.fail(f"the real error was hidden by {type(other).__name__}")  # before: the AttributeError replaced it
        else:
            pytest.fail("no error")
        assert sc.last_partial().error == want


def test_one_poisonous_file_does_not_stop_the_scan_and_is_not_read_again(tmp_path, monkeypatch):
    s = make(tmp_path)
    put(s, "bad.txt", b"x")
    mini(s, "inv-A.txt")
    real, calls = inbox.reader.read, []

    def read(name, data):
        if name == "bad.txt":
            calls.append(1)
            raise ValueError("parser bug")
        return real(name, data)

    monkeypatch.setattr(inbox.reader, "read", read)
    sc, _ = scanner(s)
    r = go(sc)
    assert reasons(r) == {"bad.txt": "not_a_file"} and len(r.new) == 1 and r.examined == len(r.new) + r.refused_total + r.duplicates
    go(sc)
    assert len(calls) == 1  # the poison pill is remembered


def test_a_memory_entry_for_a_hash_expires_and_needs_a_file_id(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    put(s, "copy.txt", (MINI / "inv-A.txt").read_bytes())
    calls, real = [], inbox.read_plain_file
    monkeypatch.setattr(inbox, "read_plain_file", lambda p, c, **k: (calls.append(Path(p).name), real(p, c, **k))[1])
    mono = Tick(1000.0)
    sc, _ = scanner(s, monotonic=mono)
    go(sc)
    del calls[:]
    go(sc)
    assert calls == []  # remembered
    mono.t += inbox.SHA_TTL_S + 1
    go(sc)
    assert sorted(calls) == ["copy.txt", "inv-A.txt"]  # read again after the time limit
    sc._remember(("n.txt", 0, 5, 1, 2, 3), ("refused", "x", 1e18))
    sc._remember(("n.txt", 5, 0, 1, 2, 3), ("refused", "x", 1e18))
    assert not [k for k in sc._skip if k[0] == "n.txt"]  # no device or file id: nothing is served from memory


def test_a_rename_does_not_keep_the_old_verdict(tmp_path):
    s = make(tmp_path)
    put(s, "u.txt", b"unlisted\n")
    sc, _ = scanner(s)
    assert reasons(go(sc)) == {"u.txt": "not_on_list"}
    os.rename(inbox.inbox_dir(s) / "u.txt", inbox.inbox_dir(s) / "u.pdf")
    r = go(sc)
    assert [n.flags for n in r.new] == [("X18",)] and r.refused == ()  # a .pdf is a hand-back, not "not on the list"


def test_a_modification_time_far_in_the_future_is_a_visible_refusal(tmp_path):
    s = make(tmp_path)
    put(s, "inv-A.txt", (MINI / "inv-A.txt").read_bytes(), age_s=-2 * inbox.FUTURE_MTIME_S)
    r = go(scanner(s)[0])
    assert reasons(r) == {"inv-A.txt": "future_mtime"} and r.new == () and r.examined == r.refused_total == 1
    assert "future_mtime" in review_page.ERROR_TEXT


def test_the_scan_reads_the_queue_through_a_read_only_connection(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    sc, _ = scanner(s)
    go(sc)

    def no_write_path(*a, **k):
        raise AssertionError("the scan opened the queue for writing")

    monkeypatch.setattr(workqueue, "opened", no_write_path)
    r = go(sc)  # only duplicates: nothing to insert
    assert r.duplicates == 1 and r.new == ()


def test_a_damaged_queue_file_is_a_closed_code_not_a_raw_sqlite_error(tmp_path):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    sc, _ = scanner(s)
    go(sc)
    for p in s.intake_home.glob("queue.sqlite3*"):
        if p.name != "queue.sqlite3":
            p.unlink()
    (s.intake_home / "queue.sqlite3").write_bytes(b"this is not a database" * 100)
    with pytest.raises((Refused, ConfigError)) as e:
        sc.try_scan()
    assert e.value.code in ("stored_data_bad", "bad_config")


def test_refusals_from_the_insert_step_are_remembered(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    for i in range(4):
        put(s, f"p{i}.pdf", b"%%PDF%d" % i)
    real = inbox.pipeline.process

    def collide(s_, parsed, model_, suppliers):
        if parsed.name.startswith("p"):
            raise Refused("id_collision", "another file has this name")
        return real(s_, parsed, model_, suppliers)

    monkeypatch.setattr(inbox.pipeline, "process", collide)
    calls, real_read = [], inbox.read_plain_file
    monkeypatch.setattr(inbox, "read_plain_file", lambda p, c, **k: (calls.append(Path(p).name), real_read(p, c, **k))[1])
    sc, _ = scanner(s)
    r1 = go(sc)
    assert sorted(x.name for x in r1.refused) == ["p0.pdf", "p1.pdf", "p2.pdf", "p3.pdf"]
    del calls[:]
    r2 = go(sc)
    assert [
        c for c in calls if c.startswith("p")
    ] == [] and r2.refused_total == 4  # remembered: 200 of them could not starve the later files


def test_error_while_listing_keeps_the_count_whole(tmp_path, monkeypatch):
    s = make(tmp_path)
    for i in range(4):
        put(s, f"f{i}.pdf", b"%%PDF%d" % i)
    real = inbox.read_plain_file

    def odd(path, cap, **kw):
        if Path(path).name == "f1.pdf":
            raise Refused("some_new_code", "a reader bug")
        return real(path, cap, **kw)

    monkeypatch.setattr(inbox, "read_plain_file", odd)
    sc, _ = scanner(s)
    with pytest.raises(Refused):
        sc.try_scan()
    part = sc.last_partial()
    assert (part.examined, part.remaining, part.ended) == (1, 4, "error")  # f0 waits for a slot; f1 (in flight), f2, f3 were not looked at


def test_scan_stops_while_too_many_abandoned_reads_still_hang(tmp_path, monkeypatch):
    s = make(tmp_path)
    monkeypatch.setattr(inbox, "READ_TIMEOUT_S", 0.2)
    monkeypatch.setattr(inbox, "MAX_ABANDONED", 2)
    put(s, "aaa-hang1.txt", b"x")
    put(s, "aab-hang2.txt", b"y")
    mini(s, "inv-A.txt")
    release, real = threading.Event(), inbox.read_plain_file

    def hang(path, cap, **kw):
        if "hang" in Path(path).name:
            release.wait(10)
        return real(path, cap, **kw)

    monkeypatch.setattr(inbox, "read_plain_file", hang)
    sc, _ = scanner(s)
    try:
        assert go(sc).ended == "deadline"  # hang1 abandoned
        assert go(sc).ended == "deadline"  # hang2 abandoned
        r = go(sc)  # two reads still hang: no third is started, the scan says so and returns
        assert r.ended == "abandoned_reads" and r.new == () and r.examined == 0
        release.set()
        time.sleep(0.5)
        assert len(go(sc).new) == 1  # the hung threads ended: the honest file is read
    finally:
        release.set()


# ---- batch 4 (round-3 reviews of 925e0cd; each test below fails on 925e0cd) ---------------------------------------------------------------------------
class FakeEntry:
    def __init__(self, name: str, mtime_ns: int) -> None:
        self.name, self._m = name, mtime_ns

    def stat(self, follow_symlinks: bool = True):
        return type("St", (), {"st_mtime_ns": self._m})()


class FakeScan:
    """A folder of ``n`` fake entries, produced lazily; ``seen['n']`` counts how many were pulled (and moves the fake clock by one per entry)."""

    def __init__(self, n: int, seen: dict, clock: Tick | None = None) -> None:
        self.n, self.seen, self.clock = n, seen, clock

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __iter__(self):
        for i in range(self.n):
            self.seen["n"] += 1
            if self.clock is not None:
                self.clock.t = self.seen["n"]
            yield FakeEntry(f"f{(i * 7919) % self.n:08d}.txt", (i * 104729) % 1000)


def test_listing_streams_and_stops_at_the_deadline_without_reading_the_whole_folder(tmp_path, monkeypatch):
    s = make(tmp_path)
    monkeypatch.setattr(inbox, "MAX_LISTED", 100)
    monkeypatch.setattr(inbox, "MAX_REMEMBERED", 201)
    clock, seen = Tick(), {"n": 0}
    sc, _ = scanner(s, monotonic=clock)
    monkeypatch.setattr(inbox.os, "scandir", lambda src: FakeScan(5_000_000, seen, clock))
    r = sc.try_scan(deadline_s=3000)  # one fake time unit per entry
    assert r.ended == "deadline" and r.examined == 0 and not inbox._SCAN_LOCK.locked()
    assert (
        seen["n"] <= 3000 + 2048
    )  # 5,000,000 entries were on offer; the scan pulled only what the deadline allowed (counter, not wall clock)


def test_listing_keeps_only_the_wanted_slice_in_memory(tmp_path, monkeypatch):
    import tracemalloc

    s = make(tmp_path)
    seen = {"n": 0}
    monkeypatch.setattr(inbox.os, "scandir", lambda src: FakeScan(200_000, seen))
    tracemalloc.start()
    try:
        root, fd, got, total, after = inbox._open_and_list(inbox.inbox_dir(s), None, 100, lambda: False)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    if fd is not None:
        os.close(fd)
    assert (len(got), total, after) == (100, 200_000, 200_000) and got == sorted(got)
    assert got[0][0] == 0 and peak < 4_000_000  # a sorted list of 200,000 names would be several times larger
    cursor = got[-1]
    seen["n"] = 0
    root, fd, got2, total2, after2 = inbox._open_and_list(inbox.inbox_dir(s), cursor, 100, lambda: False)
    if fd is not None:
        os.close(fd)
    assert all(k > cursor for k in got2) and total2 == 200_000 and after2 < 200_000


def test_a_hanging_lstat_is_abandoned_and_the_scan_returns(tmp_path, monkeypatch):
    s = make(tmp_path)
    monkeypatch.setattr(inbox, "READ_TIMEOUT_S", 0.3)
    put(s, "aaa-hang.txt", b"x")
    mini(s, "inv-A.txt")
    release, hits, real = threading.Event(), [], os.lstat

    def lstat(path, *a, **kw):
        if os.path.basename(str(path)) == "aaa-hang.txt":
            hits.append(1)
            release.wait(10)
        return real(path, *a, **kw)

    sc, _ = scanner(s)
    monkeypatch.setattr(os, "lstat", lstat)
    try:
        t0 = time.monotonic()
        r = go(sc)
        assert time.monotonic() - t0 < 5 and not inbox._SCAN_LOCK.locked()
        assert r.ended == "deadline" and reasons(r) == {"aaa-hang.txt": "read_timeout"}
        r2 = go(sc)
        assert len(r2.new) == 1 and len(hits) == 1  # the file behind the hung one gets its turn
        r3 = go(sc)
        assert reasons(r3) == {"aaa-hang.txt": "read_timeout"} and len(hits) == 1  # remembered: not looked at again
    finally:
        release.set()


def test_a_hanging_folder_listing_is_abandoned_and_the_lock_is_released(tmp_path, monkeypatch):
    s = make(tmp_path)
    monkeypatch.setattr(inbox, "READ_TIMEOUT_S", 0.3)
    release = threading.Event()
    sc, _ = scanner(s)

    def hang(src):
        release.wait(10)
        raise OSError("dead share")

    monkeypatch.setattr(inbox.os, "scandir", hang)
    try:
        t0 = time.monotonic()
        r = go(sc)
        assert time.monotonic() - t0 < 5 and r.ended == "deadline" and not inbox._SCAN_LOCK.locked()
    finally:
        release.set()


def hostile_variants(raw: bytes) -> list[bytes]:
    bom = chr(0xFEFF).encode("utf-8")
    base = raw.replace(b"\r\n", b"\n")
    return [bom * k + base.replace(b"\n", eol) for k in range(17) for eol in (b"\n", b"\r\n", b"\r")]


def test_hostile_variants_of_one_document_make_one_item_and_one_model_call(tmp_path):
    raw = (MINI / "inv-A.txt").read_bytes()
    (tmp_path / "one").mkdir()
    (tmp_path / "many").mkdir()
    s_one = make(tmp_path / "one")
    put(s_one, "inv-A.txt", raw)
    sc1, m1 = scanner(s_one)
    go(sc1)
    s = make(tmp_path / "many")
    variants = hostile_variants(raw)
    assert len(variants) == 51 and len(set(variants)) == 51
    for i, v in enumerate(variants):
        put(s, f"v{i:02d}.txt", v)
    sc, m = scanner(s)
    ids, raised, last = drain(sc, 60)
    assert len(workqueue.list_items(s)) == 1 and m.calls == m1.calls > 0
    calls = []
    real = inbox.read_plain_file
    inbox.read_plain_file = lambda p, c, **k: (calls.append(1), real(p, c, **k))[1]
    try:
        go(sc)
    finally:
        inbox.read_plain_file = real
    assert calls == []  # remembered: the variants are not read again


def test_fresh_junk_cannot_hold_back_an_older_real_file(tmp_path):
    """Each scan brings 200 NEW hand-back files that sort BEFORE z_real.txt and are newer; reads go oldest first."""
    s = make(tmp_path)
    put(s, "z_real.txt", (MINI / "inv-A.txt").read_bytes())
    sc, _ = scanner(s)
    for rnd in range(2):
        for i in range(200):
            put(s, f"a_junk_{rnd}_{i:03d}.pdf", b"%%PDF %d %d" % (rnd, i), age_s=100 - rnd)
        go(sc)
        if any(i.id.startswith("z_real") for i in workqueue.list_items(s)):
            return
    pytest.fail("z_real.txt was not read within 2 scans")


def test_reads_go_oldest_first_and_a_later_file_is_read(tmp_path, monkeypatch):
    s = make(tmp_path)
    monkeypatch.setattr(inbox, "MAX_READS", 3)
    for i in range(6):
        put(s, f"b{i}.txt", b"junk %d\n" % i, age_s=100 + i)  # b5 is the oldest
    seen, real = [], inbox.read_plain_file
    monkeypatch.setattr(inbox, "read_plain_file", lambda p, c, **k: (seen.append(Path(p).name), real(p, c, **k))[1])
    go(scanner(s)[0])
    assert seen == ["b5.txt", "b4.txt", "b3.txt"]


def test_hand_back_items_are_capped_per_window_and_in_the_queue(tmp_path, monkeypatch):
    s = make(tmp_path)
    monkeypatch.setattr(inbox, "MAX_FLAGGED_PER_WINDOW", 3)
    for i in range(10):
        put(s, f"p{i}.pdf", b"%%PDF%d" % i)
    mono = Tick(1000.0)
    sc, _ = scanner(s, monotonic=mono)
    ids, raised, last = drain(sc, 30)
    assert len(workqueue.list_items(s)) == 3 and last.refused_total == 7 and {x.reason for x in last.refused} == {"flag_capped"}
    mono.t += inbox.FLAGGED_WINDOW_S + 1  # the window passes: room for three more
    drain(sc, 30)
    assert len(workqueue.list_items(s)) == 6


def test_hand_back_items_stop_at_the_open_queue_size(tmp_path, monkeypatch):
    s = make(tmp_path)
    monkeypatch.setattr(inbox, "MAX_FLAGGED_OPEN", 2)
    for i in range(6):
        put(s, f"p{i}.pdf", b"%%PDF%d" % i)
    drain(scanner(s)[0], 30)
    assert len(workqueue.list_items(s)) == 2


def test_a_scan_with_less_than_the_minimum_time_left_starts_no_read(tmp_path):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    r = scanner(s)[0].try_scan(deadline_s=inbox.MIN_READ_S / 2)
    assert r.ended == "deadline" and r.examined == 0 and r.refused == () and r.remaining >= 1


def test_blocked_reads_say_no_progress_and_log_counts(tmp_path, monkeypatch, caplog):
    s = make(tmp_path)
    monkeypatch.setattr(inbox, "MAX_ABANDONED", 1)
    mini(s, "inv-A.txt")
    sc, _ = scanner(s)
    ev = threading.Event()
    sc._abandoned.append(threading.Thread(target=ev.wait, args=(5,), daemon=True))
    sc._abandoned[0].start()
    try:
        with caplog.at_level("WARNING", logger="intake.inbox"):
            r = go(sc)
    finally:
        ev.set()
    assert r.ended == "abandoned_reads" and r.examined == 0 and any("abandoned reads" in m for m in caplog.messages)


def test_a_failing_worker_start_is_not_a_file_verdict_and_leaks_no_descriptor(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt")
    sc, _ = scanner(s)
    open_dups, real_dup, real_close, real_start, starts = set(), os.dup, os.close, threading.Thread.start, []

    def dup(fd):
        n = real_dup(fd)
        open_dups.add(n)
        return n

    def close(fd):
        open_dups.discard(fd)
        return real_close(fd)

    def start(self):
        starts.append(1)
        if len(starts) >= 3:  # the listing and the metadata batch start; the file read cannot
            raise RuntimeError("can't start new thread")
        return real_start(self)

    monkeypatch.setattr(os, "dup", dup)
    monkeypatch.setattr(os, "close", close)
    monkeypatch.setattr(threading.Thread, "start", start)
    r = go(sc)
    assert r.ended == "deadline" and r.refused == () and r.new == () and sc._skip == {}
    assert open_dups == set()  # the duplicated folder descriptor was closed


def test_a_sharing_violation_is_tried_again_not_remembered(tmp_path, monkeypatch):
    s = make(tmp_path)
    put(s, "held.txt", b"x")
    calls = []

    def held(path, cap, **kw):
        calls.append(1)
        raise PermissionError(13, "used by another process")

    monkeypatch.setattr(inbox, "read_plain_file", held)
    sc, _ = scanner(s)
    assert reasons(go(sc)) == {"held.txt": "not_a_file"}
    assert reasons(go(sc)) == {"held.txt": "not_a_file"} and len(calls) == 2  # asked again at the next scan


def test_memory_errors_are_not_swallowed_by_the_poison_pill_catch(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt")

    def oom(name, data):
        raise MemoryError

    monkeypatch.setattr(inbox.reader, "read", oom)
    sc, _ = scanner(s)
    with pytest.raises(MemoryError):
        sc.try_scan()
    assert sc.last_partial().error == "MemoryError"


def test_poison_pill_log_has_type_and_place_but_no_file_name(tmp_path, monkeypatch, caplog):
    s = make(tmp_path)
    put(s, "secret-customer-bad.txt", b"x")

    def boom(name, data):
        raise ValueError("parser bug")

    monkeypatch.setattr(inbox.reader, "read", boom)
    with caplog.at_level("WARNING", logger="intake.inbox"):
        go(scanner(s)[0])
    msg = " ".join(caplog.messages)
    assert "ValueError at" in msg and ".py:" in msg and "secret-customer" not in msg


def test_a_waiting_file_whose_second_look_hits_a_parser_bug_is_refused_not_fatal(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt", "inv-B.txt", "inv-C.txt")
    real_read, real_process, n = inbox.reader.read, inbox.pipeline.process, []

    def read(name, data):
        if name == "inv-C.txt":
            n.append(1)
            if len(n) == 2:
                raise ValueError("parser bug")
        return real_read(name, data)

    def refuse_a(s_, parsed, model_, suppliers):
        if parsed.name == "inv-A.txt":
            raise Refused("id_collision", "another file has this name")
        return real_process(s_, parsed, model_, suppliers)

    monkeypatch.setattr(inbox.reader, "read", read)
    monkeypatch.setattr(inbox.pipeline, "process", refuse_a)
    r = go(scanner(s)[0])
    assert reasons(r) == {"inv-A.txt": "id_collision", "inv-C.txt": "not_a_file"}


@pytest.mark.skipif(not POSIX, reason="Windows cannot create a name that ends in a dot or a space")
def test_names_ending_in_dot_or_space_are_refused_by_the_name_rule(tmp_path):
    s = make(tmp_path)
    put(s, "inv-A.txt.", (MINI / "inv-A.txt").read_bytes())
    put(s, "inv-B.txt ", (MINI / "inv-B.txt").read_bytes())
    r = go(scanner(s)[0])
    assert reasons(r) == {"inv-A.txt.": "bad_name", "inv-B.txt ": "bad_name"} and r.new == ()


def test_a_listed_name_that_is_gone_when_looked_at_is_counted_as_vanished(tmp_path, monkeypatch):
    s = make(tmp_path)
    mini(s, "inv-A.txt", "inv-B.txt")
    real = inbox._lstat

    def lstat(name, dir_fd, inbox_):
        if name == "inv-B.txt":
            raise FileNotFoundError(name)
        return real(name, dir_fd, inbox_)

    monkeypatch.setattr(inbox, "_lstat", lstat)
    r = go(scanner(s)[0])
    assert (r.vanished, r.examined, len(r.new)) == (1, 1, 1)


def test_names_with_a_literal_backslash_cannot_pose_as_an_escape():
    real_esc = inbox.Refusal.of("a" + chr(0x1B) + "b.txt", "bad_name").name
    typed = inbox.Refusal.of("a" + chr(92) + "x1b" + "b.txt", "bad_name").name
    assert real_esc != typed and typed.count(chr(92)) == 2 and inbox.Refusal(typed, "bad_name").name == typed


def test_a_cut_never_splits_an_escape():
    name = inbox.Refusal.of(chr(0x202E) * 100, "bad_name").name
    assert name.endswith("...") and name[:-3] == (chr(92) + "u202e") * 33 and len(name) <= inbox.MAX_NAME_SHOWN + 3


def test_a_rewritten_name_keeps_one_memory_entry(tmp_path):
    s = make(tmp_path)
    put(s, "u.txt", b"unlisted one\n")
    sc, _ = scanner(s)
    go(sc)
    for i in range(3):
        put(s, "u.txt", b"unlisted again %d\n" % i, age_s=500 - i * 10)
        go(sc)
    assert len([k for k in sc._skip if k[0] == "u.txt"]) == 1


def test_a_stored_flagged_file_is_a_duplicate_before_any_insert(tmp_path, monkeypatch):
    """A fresh scanner (no memory) must find a stored hand-back file by its raw hash and never call the insert step for it."""
    s = make(tmp_path)
    put(s, "p0.pdf", b"%%PDF0")
    go(scanner(s)[0])
    calls, real = [], inbox.pipeline.process
    monkeypatch.setattr(inbox.pipeline, "process", lambda *a, **k: (calls.append(1), real(*a, **k))[1])
    r = go(scanner(s)[0])
    assert calls == [] and r.duplicates == 1 and r.new == ()


def test_a_name_seen_every_scan_is_not_read_again_while_one_off_names_churn(tmp_path, monkeypatch):
    s = make(tmp_path)
    monkeypatch.setattr(inbox, "MAX_LISTED", 10)
    monkeypatch.setattr(inbox, "MAX_REMEMBERED", 21)
    put(s, "keep.txt", b"unlisted and kept\n")
    reads, real = [], inbox.read_plain_file
    monkeypatch.setattr(inbox, "read_plain_file", lambda p, c, **k: (reads.append(Path(p).name), real(p, c, **k))[1])
    sc, _ = scanner(s)
    for rnd in range(30):
        made = [put(s, f"j{rnd:02d}_{i}.txt", b"junk %d %d\n" % (rnd, i)) for i in range(5)]
        go(sc)
        for p in made:
            p.unlink()
    assert reads.count("keep.txt") == 1  # least recently used: the name seen every scan stayed in memory


def test_a_hung_second_look_is_refused_and_remembered(tmp_path, monkeypatch):
    s = make(tmp_path)
    monkeypatch.setattr(inbox, "READ_TIMEOUT_S", 0.3)
    mini(s, "inv-A.txt", "inv-B.txt", "inv-C.txt")
    release, real_read, real_process, n = threading.Event(), inbox.read_plain_file, inbox.pipeline.process, []

    def read(path, cap, **kw):
        if Path(path).name == "inv-C.txt":
            n.append(1)
            if len(n) == 2:
                release.wait(10)
        return real_read(path, cap, **kw)

    def refuse_a(s_, parsed, model_, suppliers):
        if parsed.name == "inv-A.txt":
            raise Refused("id_collision", "another file has this name")
        return real_process(s_, parsed, model_, suppliers)

    monkeypatch.setattr(inbox, "read_plain_file", read)
    monkeypatch.setattr(inbox.pipeline, "process", refuse_a)
    sc, _ = scanner(s)
    try:
        r = go(sc)
        assert reasons(r)["inv-C.txt"] == "read_timeout" and r.ended == "deadline"
        assert [v for k, v in sc._skip.items() if k[0] == "inv-C.txt" and v[0] == "refused"] and sc._skip
    finally:
        release.set()
