"""Class: a name swapped with os.replace. A replace changes the NAME, so it would turn a device, a pipe or a socket
into a plain file instead of failing. The counters writer and the flag writer must refuse such a target before any
byte is written or replaced. No real device is used: a pipe and a socket are made in the temporary folder, and the
character-device case is checked through a patched stat answer (the one device made with mknod needs root)."""

from __future__ import annotations

import os
import socket
import stat
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from demo_only.portal_demo import PortalDemo
from lead_desk import regfile
from lead_desk.regfile import NotRegularFile, open_output, refuse_replacing_special
from lead_desk.run_stats import write_stats


def _make(kind: str, base: Path) -> Path:
    path = base / "target"
    if kind == "fifo":
        os.mkfifo(path)
    elif kind == "socket":
        # a socket path is limited to about 100 bytes: a long temporary folder (a long TMPDIR) would fail with "AF_UNIX
        # path too long", so the socket is made by its short relative name from inside the folder
        here = os.getcwd()
        os.chdir(base)
        try:
            s = socket.socket(socket.AF_UNIX)
            try:
                s.bind(path.name)
            finally:
                s.close()
        finally:
            os.chdir(here)
    elif kind == "folder":
        path.mkdir()
    elif kind == "link-to-fifo":
        os.mkfifo(base / "real")
        path.symlink_to(base / "real")
    return path


@pytest.mark.parametrize("kind", ["fifo", "socket", "folder", "link-to-fifo"])
def test_the_counters_writer_leaves_a_special_target_alone(kind: str, tmp_path: Path) -> None:
    path = _make(kind, tmp_path)
    before = stat.S_IFMT(os.lstat(path).st_mode)
    write_stats(path, {"a": 1})
    assert stat.S_IFMT(os.lstat(path).st_mode) == before, "the special file was replaced by a plain file"
    assert not stat.S_ISREG(os.lstat(path).st_mode)


@pytest.mark.parametrize("kind", ["fifo", "socket", "folder", "link-to-fifo"])
def test_the_flag_writer_leaves_a_special_target_alone(kind: str, tmp_path: Path) -> None:
    path = _make(kind, tmp_path)
    before = stat.S_IFMT(os.lstat(path).st_mode)
    with pytest.raises(OSError):
        PortalDemo._write_flag(path, "p")
    assert stat.S_IFMT(os.lstat(path).st_mode) == before
    assert "target" in [p.name for p in tmp_path.iterdir()]
    assert not [p for p in tmp_path.iterdir() if p.name not in ("target", "real")], "a temporary file was left behind"


@pytest.mark.parametrize("kind", ["fifo", "socket", "folder", "link-to-fifo"])
def test_the_check_and_open_output_both_refuse(kind: str, tmp_path: Path) -> None:
    path = _make(kind, tmp_path)
    with pytest.raises(NotRegularFile):
        refuse_replacing_special(path)
    with pytest.raises(NotRegularFile):
        open_output(path, "w", encoding="utf-8")


def test_a_character_device_answer_is_refused_without_a_real_device(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The stat answer is faked on a plain tmp file; the writer must stop and must not replace it."""
    path = tmp_path / "dev"
    path.write_text("keep", encoding="utf-8")
    real = os.stat

    def fake(p: object, *a: object, **k: object) -> os.stat_result:
        r = real(p, *a, **k)
        if str(p) == str(path):
            return os.stat_result((stat.S_IFCHR | 0o600, *tuple(r)[1:]))
        return r

    monkeypatch.setattr(regfile.os, "stat", fake)
    with pytest.raises(NotRegularFile):
        refuse_replacing_special(path)
    write_stats(path, {"a": 1})
    assert path.read_text(encoding="utf-8") == "keep"


def test_a_missing_or_plain_target_is_still_written(tmp_path: Path) -> None:
    """CONTROL (passes on old code too): the normal case must keep working."""
    new = tmp_path / "new.json"
    write_stats(new, {"a": 1})
    assert new.read_text(encoding="utf-8") == '{"a": 1}'
    write_stats(new, {"a": 2})
    assert new.read_text(encoding="utf-8") == '{"a": 2}'
    refuse_replacing_special(tmp_path / "missing")


def test_a_nul_in_the_name_is_refused(tmp_path: Path) -> None:
    with pytest.raises(NotRegularFile):
        refuse_replacing_special("a\0b")
