"""demo_only/tools: ``demo_ctl register`` (the only writer of the made-up list) and ``prepare_fake_env`` (temporary folder only). Needs the demo-only
folder, so the cut job skips this module (``NEEDS_DEMO_DATA``)."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from conftest import MINI, ROOT, fake_secret_values
from intake import cli, reader, secret_store, settings
from tools import demo_ctl, prepare_fake_env

TOOLS = ROOT / "demo_only" / "tools"
ENV = dict(os.environ, PYTHONPATH=str(ROOT / "src"))


def run_script(name, *args, env=ENV):
    return subprocess.run([sys.executable, str(TOOLS / name), *map(str, args)], capture_output=True, text=True, env=env, timeout=180)


def key_text(local):
    return secret_store.secrets_path(local).read_text(encoding="utf-8")


def mk(tmp_path, backend="fake"):
    local = tmp_path / "local"
    (local / "intake").mkdir(parents=True, exist_ok=True)
    return settings.load({"HADAVIN_LOCAL": str(local), "INTAKE_MODEL_BACKEND": backend})


def listed(s):
    return settings.load_hash_list(s.intake_home / "synthetic_hashes.txt")


def h(raw: bytes) -> str:
    return reader.send_text_hash(reader.read("x.txt", raw).text)


def test_register_adds_the_send_text_hash_of_every_clean_txt(tmp_path):
    s = mk(tmp_path)
    added, total = demo_ctl.register(s, MINI)
    assert (added, total) == (4, 4)
    assert listed(s) == {h(p.read_bytes()) for p in MINI.glob("*.txt")}
    assert demo_ctl.register(s, MINI) == (0, 4)  # de-duplicated, nothing new
    text = (s.intake_home / "synthetic_hashes.txt").read_text(encoding="utf-8")
    assert text == "".join(x + "\n" for x in sorted(listed(s))) and "\r" not in text
    assert not list(s.intake_home.glob("*.tmp"))


def test_register_skips_flagged_files_other_suffixes_and_subfolders(tmp_path):
    s = mk(tmp_path)
    d = tmp_path / "docs"
    (d / "sub").mkdir(parents=True)
    (d / "ok.TXT").write_bytes(b"Invoice INV-1\n")
    (d / "nul.txt").write_bytes(b"a\x00b")  # X18
    (d / "big.txt").write_bytes(b"a" * 20001)  # X28
    (d / "bad.txt").write_bytes(b"\xff\xfe")  # X18
    (d / "paper.pdf").write_bytes(b"Invoice INV-2\n")  # wrong suffix
    (d / "sub" / "deep.txt").write_bytes(b"Invoice INV-3\n")  # not recursive
    assert demo_ctl.register(s, d) == (1, 1)
    assert listed(s) == {h(b"Invoice INV-1\n")}


def test_register_hashes_send_text_so_crlf_and_bom_variants_collapse(tmp_path):
    s = mk(tmp_path)
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.txt").write_bytes(b"Invoice INV-1\n")
    (d / "b.txt").write_bytes(b"\xef\xbb\xbfInvoice INV-1\r\n")
    assert demo_ctl.register(s, d) == (1, 1)


def test_replace_rewrites_and_the_default_appends(tmp_path):
    s = mk(tmp_path)
    a, b = tmp_path / "a", tmp_path / "b"
    for d, body in ((a, b"Invoice INV-1\n"), (b, b"Invoice INV-2\n")):
        d.mkdir()
        (d / "x.txt").write_bytes(body)
    demo_ctl.register(s, a)
    assert demo_ctl.register(s, b) == (1, 2)
    assert demo_ctl.register(s, a, replace=True) == (1, 1)  # rewritten: only a's hash
    assert listed(s) == {h(b"Invoice INV-1\n")}
    empty = tmp_path / "empty"
    empty.mkdir()
    assert demo_ctl.register(s, empty, replace=True) == (0, 0)  # an empty replace is the STOP state
    assert listed(s) == frozenset()


def test_register_refuses_the_inbox_and_anything_under_it(tmp_path):
    s = mk(tmp_path)
    inbox = s.intake_home / "inbox"
    (inbox / "nested").mkdir(parents=True)
    (inbox / "real.txt").write_bytes(b"a real invoice\n")
    for folder in (inbox, inbox / "nested", inbox / ".." / "inbox", inbox / "nested" / ".."):
        with pytest.raises(demo_ctl.ConfigError):
            demo_ctl.register(s, folder)
    assert listed(s) == frozenset() and not (s.intake_home / "synthetic_hashes.txt").exists()


def test_register_refuses_a_missing_folder_and_a_file(tmp_path):
    s = mk(tmp_path)
    (tmp_path / "f.txt").write_bytes(b"x")
    for p in (tmp_path / "nope", tmp_path / "f.txt"):
        with pytest.raises(demo_ctl.ConfigError):
            demo_ctl.register(s, p)


def test_demo_ctl_script_registers_and_reports(tmp_path):
    local = tmp_path / "local"
    env = dict(ENV, HADAVIN_LOCAL=str(local))
    r = run_script("demo_ctl.py", "register", MINI, env=env)
    assert (r.returncode, r.stdout.strip()) == (0, "registered: 4 new, 4 on the list"), r.stderr
    r = run_script("demo_ctl.py", "register", local / "intake" / "inbox", env=env)
    assert r.returncode == 3 and r.stderr.startswith("error: bad_config") and "Traceback" not in r.stderr
    r = run_script("demo_ctl.py", "register", MINI, env=dict(ENV, HADAVIN_LOCAL=""))
    assert r.returncode == 3 and "local_unset" in r.stderr


# ---- prepare_fake_env -------------------------------------------------------------------------------------------------------------------------
def test_prepare_fake_env_builds_a_runnable_fake_environment(tmp_path, monkeypatch, capsys):
    local = tmp_path / "local"
    home = prepare_fake_env.prepare(local)
    s = settings.load({"HADAVIN_LOCAL": str(local), "INTAKE_MODEL_BACKEND": "fake"})
    assert home == s.intake_home and (home / "inbox").is_dir() and (home / "out").is_dir() and s.spend_dir.is_dir()
    assert (home / "suppliers.csv").read_bytes() == (MINI / "suppliers.csv").read_bytes()
    p = settings.load_prices(s.prices_path)
    assert min(p.read_in, p.read_out, p.fallback_in, p.fallback_out) > 0
    assert len(listed(s)) == 4
    assert json.loads(s.prices_path.read_text(encoding="utf-8"))["model_ids"] == {
        "read": s.model.tier_read,
        "fallback": s.model.tier_fallback,
    }
    # the same configuration passes `intake check` on the fake backend, and nothing it prints holds a secret value
    monkeypatch.setenv("HADAVIN_LOCAL", str(local))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "fake")
    assert cli.main(["check"]) == 0
    out = capsys.readouterr().out
    text = key_text(local)
    for line in text.splitlines():
        assert line.split("=", 1)[1] not in out
    assert "ANTHROPIC_API_KEY" not in text  # the owner's key is never created here


def test_prepare_fake_env_is_repeatable(tmp_path):
    local = tmp_path / "local"
    prepare_fake_env.prepare(local)
    before = key_text(local)
    prepare_fake_env.prepare(local)
    assert key_text(local) == before  # make_secrets never rewrites existing values


def test_prepare_fake_env_refuses_a_folder_outside_the_temporary_folder():
    outside = ROOT / "demo_only" / "tools" / "not-a-temp-home"
    assert not settings.under_temp_folder(outside)
    with pytest.raises(prepare_fake_env.Refused) as e:
        prepare_fake_env.prepare(outside)
    assert e.value.code == "fake_on_real_folder" and not outside.exists()


def test_prepare_fake_env_script_runs_and_refuses(tmp_path):
    local = tmp_path / "local"
    r = run_script("prepare_fake_env.py", local)
    assert (r.returncode, r.stdout.strip()) == (0, "prepared: intake"), r.stderr
    assert all(line.split("=", 1)[1] not in r.stdout + r.stderr for line in key_text(local).splitlines())
    bad = ROOT / "demo_only" / "tools" / "not-a-temp-home"
    r = run_script("prepare_fake_env.py", bad)
    assert r.returncode == 2 and "fake_on_real_folder" in r.stderr and not bad.exists()
    r = run_script("prepare_fake_env.py")
    assert r.returncode == 3 and r.stderr.startswith("usage")


def test_the_generated_secrets_are_random_not_the_test_constants(tmp_path):
    local = tmp_path / "local"
    prepare_fake_env.prepare(local)
    text = key_text(local)
    assert not any(v in text for v in fake_secret_values().values())
