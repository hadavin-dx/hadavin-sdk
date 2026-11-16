"""demo_ctl register round 1: resolved paths, symlinks, junctions, hardlinks, the folder allowlist, the size cap, the atomic and locked write.
Needs the demo-only folder (cut job skips this module)."""

from __future__ import annotations

import os
import subprocess
import sys
import threading

import pytest

from conftest import MINI, ROOT
from intake import reader, settings
from tools import demo_ctl


def mk(tmp_path):
    local = tmp_path / "local"
    (local / "intake" / "inbox").mkdir(parents=True, exist_ok=True)
    return settings.load({"HADAVIN_LOCAL": str(local), "INTAKE_MODEL_BACKEND": "fake"})


def listed(s):
    return settings.load_hash_list(s.intake_home / "synthetic_hashes.txt")


def h(raw: bytes) -> str:
    return reader.send_text_hash(reader.read("x.txt", raw).text)


def test_a_symlink_to_a_real_inbox_file_is_skipped(tmp_path):
    s = mk(tmp_path)
    real = s.intake_home / "inbox" / "real.txt"
    real.write_bytes(b"a real invoice\n")
    d = tmp_path / "docs"
    d.mkdir()
    (d / "ok.txt").write_bytes(b"Invoice INV-1\n")
    try:
        os.symlink(real, d / "link.txt")
    except OSError:
        pytest.skip("symlinks need a privilege here")
    assert demo_ctl.register(s, d) == (1, 1)
    assert h(b"a real invoice\n") not in listed(s)


def test_a_hardlink_to_a_real_file_is_skipped(tmp_path):
    s = mk(tmp_path)
    real = s.intake_home / "inbox" / "real.txt"
    real.write_bytes(b"a real invoice\n")
    d = tmp_path / "docs"
    d.mkdir()
    (d / "ok.txt").write_bytes(b"Invoice INV-1\n")
    os.link(real, d / "hard.txt")
    assert demo_ctl.register(s, d) == (1, 1)
    assert h(b"a real invoice\n") not in listed(s)


@pytest.mark.skipif(sys.platform != "win32", reason="junctions are a Windows feature")
def test_a_junction_to_the_inbox_is_refused_by_its_resolved_path(tmp_path):
    s = mk(tmp_path)
    (s.intake_home / "inbox" / "real.txt").write_bytes(b"a real invoice\n")
    j = tmp_path / "junction"
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(j), str(s.intake_home / "inbox")], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        pytest.skip("mklink /J not available")
    with pytest.raises(demo_ctl.ConfigError):
        demo_ctl.register(s, j)
    assert listed(s) == frozenset()


def test_a_folder_outside_the_allowed_roots_is_refused(tmp_path):
    s = mk(tmp_path)
    with pytest.raises(demo_ctl.ConfigError) as e:
        demo_ctl.register(s, ROOT / "src")
    assert "outside" in e.value.text
    assert not (s.intake_home / "synthetic_hashes.txt").exists()
    # an explicit allowlist works (the lead names the folder he trusts)
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.txt").write_bytes(b"Invoice INV-1\n")
    assert demo_ctl.register(s, d, allowed_roots=(d,)) == (1, 1)


def test_the_default_roots_cover_the_demo_only_folder_and_the_fixtures():
    assert demo_ctl.DEMO_ONLY == ROOT / "demo_only"
    s_roots = [r.resolve() for r in demo_ctl.ALLOWED_ROOTS]
    assert (ROOT / "tests" / "fixtures").resolve() in s_roots and MINI.resolve().is_relative_to(ROOT / "tests" / "fixtures")


def test_the_temporary_root_itself_is_not_an_allowed_folder(tmp_path):
    import tempfile

    s = mk(tmp_path)
    with pytest.raises(demo_ctl.ConfigError):
        demo_ctl.register(s, tempfile.gettempdir())


def test_files_over_the_size_cap_are_skipped_and_never_read_whole(tmp_path):
    s = mk(tmp_path)
    d = tmp_path / "docs"
    d.mkdir()
    (d / "ok.txt").write_bytes(b"Invoice INV-1\n")
    (d / "huge.txt").write_bytes(b"a" * (s.service.max_file_bytes + 1))
    assert demo_ctl.register(s, d) == (1, 1)


def test_the_write_is_atomic_unique_and_locked(tmp_path):
    s = mk(tmp_path)
    folders = []
    for i in range(8):
        d = tmp_path / f"f{i}"
        d.mkdir()
        (d / "x.txt").write_bytes(f"Invoice INV-{i}\n".encode())
        folders.append(d)
    errors = []

    def run(d):
        try:
            demo_ctl.register(s, d)
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    ts = [threading.Thread(target=run, args=(d,)) for d in folders]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert not errors, errors
    assert len(listed(s)) == 8  # no concurrent register lost another's hashes
    assert not list(s.intake_home.glob("*.tmp"))


def test_a_locked_list_file_is_a_clean_error_and_leaves_no_temp_file(tmp_path, monkeypatch):
    s = mk(tmp_path)
    d = tmp_path / "docs"
    d.mkdir()
    (d / "x.txt").write_bytes(b"Invoice INV-1\n")

    def locked(src, dst):
        raise PermissionError("in use")

    monkeypatch.setattr(os, "replace", locked)
    with pytest.raises(demo_ctl.ConfigError):
        demo_ctl.register(s, d)
    assert not list(s.intake_home.glob("*.tmp"))
