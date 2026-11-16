"""demo_only/tools/demo_ctl.py reset: wipes the queue, inbox, out and the made-up list; never touches spend, secrets, prices or the owner's sentence;
refuses while the service lock is held (a real lock from intake.lockfile), while the demo-running flag exists, and in a folder that has files but no
made-up-data marker. (register is tested in test_demo_tools.py.)"""

from __future__ import annotations

import hashlib
import os

import pytest

from conftest import MINI, settings_for_tests
from intake import lockfile
from intake.codes import Refused
from tools import demo_ctl

LITERAL_QUEUE_FILES = (
    "queue.sqlite3",
    "queue.sqlite3-wal",
    "queue.sqlite3-shm",
    "synthetic_hashes.txt",
)  # not read from the module under test


def populate(tmp_path, marker=True):
    s = settings_for_tests(tmp_path)
    h = s.intake_home
    (h / "inbox" / "a.txt").write_text("x", encoding="utf-8")
    (h / "inbox" / "sub").mkdir()
    (h / "inbox" / "sub" / "b.txt").write_text("y", encoding="utf-8")
    (h / "out" / "invoices.csv").write_text("c", encoding="utf-8")
    for n in LITERAL_QUEUE_FILES:
        (h / n).write_text("q", encoding="utf-8")
    s.spend_dir.mkdir(parents=True, exist_ok=True)
    (s.spend_dir / "spend.sqlite3").write_text("ledger", encoding="utf-8")
    if marker:
        demo_ctl.mark_demo_home(
            s, {hashlib.sha256(b"x").hexdigest(), hashlib.sha256(b"y").hexdigest()}
        )  # the two files above are the made-up set
    return s


def snapshot(s):
    return {
        "spend": (s.spend_dir / "spend.sqlite3").read_text(encoding="utf-8"),
        "secrets": sorted(
            p.name for p in (s.local / "secrets").iterdir()
        ),  # the key folder is untouched (file names only; no content is read)
        "prices": s.prices_path.read_text(encoding="utf-8"),
        "sentence": s.owner_sentence_path.read_text(encoding="utf-8"),
    }


def test_reset_wipes_and_recreates_and_touches_nothing_else(tmp_path):
    s = populate(tmp_path)
    keep = snapshot(s)
    demo_ctl.reset(s)
    h = s.intake_home
    assert list((h / "inbox").iterdir()) == [] and list((h / "out").iterdir()) == []
    assert not any((h / n).exists() for n in LITERAL_QUEUE_FILES)
    assert (h / "demo_home.marker").is_file()
    assert snapshot(s) == keep


def test_reset_refuses_while_a_real_lock_is_held_and_changes_nothing(tmp_path):
    s = populate(tmp_path)
    handle = lockfile.acquire(s.intake_home / "serve.lock")
    try:
        with pytest.raises(Refused) as ei:
            demo_ctl.reset(s)
        assert ei.value.code == "service_running"
        assert (s.intake_home / "inbox" / "a.txt").exists() and (s.intake_home / "queue.sqlite3").exists()
    finally:
        lockfile.release(handle)
    demo_ctl.reset(s)  # lock released: it works
    assert not (s.intake_home / "queue.sqlite3").exists()


def test_reset_refuses_while_the_demo_running_flag_exists(tmp_path):
    s = populate(tmp_path)
    s.run_dir.mkdir(parents=True, exist_ok=True)
    (s.run_dir / "demo_running.txt").write_text("demo running", encoding="utf-8")
    with pytest.raises(Refused) as ei:
        demo_ctl.reset(s)
    assert ei.value.code == "service_running" and "stop_demo" in ei.value.text and (s.intake_home / "inbox" / "a.txt").exists()


def test_reset_refuses_a_folder_with_files_and_no_marker(tmp_path):
    s = populate(tmp_path, marker=False)
    with pytest.raises(Refused) as ei:
        demo_ctl.reset(s)
    assert ei.value.code == "not_demo_home" and (s.intake_home / "inbox" / "a.txt").exists() and (s.intake_home / "queue.sqlite3").exists()


@pytest.mark.parametrize("what", ["inbox_file", "out_file", "queue", "list", "suppliers"])
def test_every_kind_of_content_without_a_marker_is_refused(tmp_path, what):
    s = settings_for_tests(tmp_path)
    h = s.intake_home
    for n in ("suppliers.csv", "synthetic_hashes.txt"):
        (h / n).unlink(missing_ok=True)
    put = {
        "inbox_file": h / "inbox" / "a.txt",
        "out_file": h / "out" / "invoices.csv",
        "queue": h / "queue.sqlite3",
        "list": h / "synthetic_hashes.txt",
        "suppliers": h / "suppliers.csv",
    }[what]
    put.write_text("x", encoding="utf-8")
    with pytest.raises(Refused) as ei:
        demo_ctl.reset(s)
    assert ei.value.code == "not_demo_home" and put.exists()


def test_reset_of_an_empty_home_without_a_marker_works_and_writes_the_marker(tmp_path):
    s = settings_for_tests(tmp_path)
    h = s.intake_home
    for n in ("suppliers.csv", "synthetic_hashes.txt"):
        (h / n).unlink(missing_ok=True)
    demo_ctl.reset(s)
    assert (h / "demo_home.marker").is_file()


def test_reset_with_nothing_to_delete_and_twice(tmp_path):
    s = populate(tmp_path)
    for _ in range(2):
        demo_ctl.reset(s)
    assert (s.intake_home / "inbox").is_dir() and (s.intake_home / "out").is_dir()


def test_reset_copies_the_demo_suppliers_file_when_the_layouts_folder_has_one(tmp_path, monkeypatch):
    s = populate(tmp_path)
    src = tmp_path / "layouts_suppliers.csv"
    src.write_text("supplier_name,bank_detail\n", encoding="utf-8")
    monkeypatch.setattr(demo_ctl, "LAYOUTS_SUPPLIERS", src)
    demo_ctl.reset(s)
    assert (s.intake_home / "suppliers.csv").read_text(encoding="utf-8") == "supplier_name,bank_detail\n"


def test_main_requires_yes_and_local_and_reports_a_refusal(tmp_path, monkeypatch, capsys):
    with pytest.raises(SystemExit):
        demo_ctl.main(["reset"])  # --yes is required
    monkeypatch.delenv("HADAVIN_LOCAL", raising=False)
    assert demo_ctl.main(["reset", "--yes"]) == 3
    s = populate(tmp_path, marker=False)
    monkeypatch.setenv("HADAVIN_LOCAL", str(s.local))
    assert demo_ctl.main(["reset", "--yes"]) == 2
    assert "not_demo_home" in capsys.readouterr().err


def _clean_home(tmp_path):
    s = settings_for_tests(tmp_path)
    for n in ("suppliers.csv", "synthetic_hashes.txt", "demo_home.marker"):
        (s.intake_home / n).unlink(missing_ok=True)
    return s


def test_register_in_a_clean_home_writes_the_marker(tmp_path):
    s = _clean_home(tmp_path)
    demo_ctl.register(s, MINI, replace=True)
    assert (s.intake_home / "demo_home.marker").is_file()
    demo_ctl.register(s, MINI)  # a second register keeps working (the marker is already there)


@pytest.mark.parametrize("what", ["inbox_file", "out_file", "queue", "suppliers"])
def test_register_never_declares_a_home_with_real_files_made_up_so_reset_still_refuses(tmp_path, what):
    s = _clean_home(tmp_path)
    h = s.intake_home
    put = {
        "inbox_file": h / "inbox" / "real.txt",
        "out_file": h / "out" / "invoices.csv",
        "queue": h / "queue.sqlite3",
        "suppliers": h / "suppliers.csv",
    }[what]
    put.write_text("real", encoding="utf-8")
    demo_ctl.register(s, MINI, replace=True)  # registering made-up files is fine ...
    assert not (h / "demo_home.marker").exists()  # ... but it must not claim the folder
    with pytest.raises(Refused) as ei:
        demo_ctl.reset(s)
    assert ei.value.code == "not_demo_home"
    assert put.read_text(encoding="utf-8") == "real"  # nothing was deleted


def test_reset_removes_the_register_lock_file_and_register_leaves_it(tmp_path):
    s = _clean_home(tmp_path)
    demo_ctl.register(s, MINI, replace=True)
    lock = s.intake_home / "synthetic_hashes.txt.lock"
    assert lock.exists()
    demo_ctl.reset(s)
    assert not lock.exists()


def test_a_file_dropped_into_inbox_after_the_marker_is_never_deleted(tmp_path):
    s = populate(tmp_path)
    real = s.intake_home / "inbox" / "real_invoice.txt"
    real.write_text("a real one", encoding="utf-8")
    with pytest.raises(Refused) as ei:
        demo_ctl.reset(s)
    assert ei.value.code == "not_demo_home" and "real_invoice.txt" in ei.value.text
    assert real.read_text(encoding="utf-8") == "a real one" and (s.intake_home / "queue.sqlite3").exists()


def test_a_file_in_out_other_than_the_demos_own_csv_is_never_deleted(tmp_path):
    s = populate(tmp_path)
    other = s.intake_home / "out" / "notes.txt"
    other.write_text("keep me", encoding="utf-8")
    with pytest.raises(Refused):
        demo_ctl.reset(s)
    assert other.exists()


def test_a_file_in_a_subfolder_of_inbox_is_checked_too(tmp_path):
    s = populate(tmp_path)
    (s.intake_home / "inbox" / "sub" / "c.txt").write_text("not registered", encoding="utf-8")
    with pytest.raises(Refused):
        demo_ctl.reset(s)


def test_files_copied_from_a_registered_folder_pass_reset(tmp_path):
    s = settings_for_tests(tmp_path)
    for n in ("suppliers.csv", "synthetic_hashes.txt", "demo_home.marker"):
        (s.intake_home / n).unlink(missing_ok=True)
    demo_ctl.register(s, MINI, replace=True)  # records the raw hashes of every plain file in the folder
    for src in MINI.glob("*.txt"):
        (s.intake_home / "inbox" / src.name).write_bytes(src.read_bytes())  # the lead copies the registered files into inbox
    assert list((s.intake_home / "inbox").iterdir())
    demo_ctl.reset(s)
    assert list((s.intake_home / "inbox").iterdir()) == []
    assert demo_ctl.marker_hashes(s.intake_home)  # the made-up set survives the reset


def _make_link(link, target):
    import subprocess
    import sys

    if sys.platform == "win32":
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True, text=True, check=False)
        if r.returncode != 0:
            pytest.skip("cannot create a junction here")
    else:
        os.symlink(target, link, target_is_directory=True)


@pytest.mark.parametrize("with_file", [True, False])
def test_a_link_or_junction_in_inbox_makes_reset_refuse_and_deletes_nothing_behind_it(tmp_path, with_file):
    s = populate(tmp_path)
    target = tmp_path / "elsewhere"
    target.mkdir()
    if with_file:
        (target / "keep.txt").write_text("real", encoding="utf-8")
    _make_link(s.intake_home / "inbox" / "link", target)  # an empty target must be refused too: the link itself is the problem
    with pytest.raises(Refused) as ei:
        demo_ctl.reset(s)
    assert "inbox/link" in ei.value.text
    assert target.is_dir() and (not with_file or (target / "keep.txt").read_text(encoding="utf-8") == "real")


def test_the_demo_suppliers_copy_alone_is_not_content_so_register_can_mark_the_home(tmp_path, monkeypatch):
    s = settings_for_tests(tmp_path)
    layouts = tmp_path / "layouts_suppliers.csv"
    layouts.write_bytes((s.intake_home / "suppliers.csv").read_bytes())  # run_demo.ps1 copied exactly this file into the home
    monkeypatch.setattr(demo_ctl, "LAYOUTS_SUPPLIERS", layouts)
    for n in ("synthetic_hashes.txt", "demo_home.marker"):
        (s.intake_home / n).unlink(missing_ok=True)
    demo_ctl.register(s, MINI, replace=True)
    assert (s.intake_home / "demo_home.marker").is_file()
    (s.intake_home / "suppliers.csv").write_text("edited: could be real", encoding="utf-8")
    (s.intake_home / "demo_home.marker").unlink()
    with pytest.raises(Refused):  # a changed suppliers file is content again
        demo_ctl.reset(s)


def test_the_wipe_does_not_use_a_recursive_delete_helper():
    import inspect

    assert "rmtree" not in inspect.getsource(demo_ctl)
