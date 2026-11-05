"""cli skeleton: init (config check only) and check (key lines, backend, data_hashes; exit 0 / 2 / 3). Prints no secret value."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from conftest import fake_secret_values, key_file, settings_for_tests
from intake import budget, cli, secret_store, settings


def run(monkeypatch, tmp_path, *argv, backend="fake", **local_kw):
    monkeypatch.setenv("HADAVIN_LOCAL", str(tmp_path / "local"))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", backend)
    return cli.main(list(argv))


def test_check_all_ok_on_the_fake_backend(tmp_path, monkeypatch, capsys):
    settings_for_tests(tmp_path)
    assert run(monkeypatch, tmp_path, "check") == 0
    out = capsys.readouterr().out.splitlines()
    sink = out.pop(
        out.index(next(x for x in out if x.startswith("sink_mode: ")))
    )  # a warning line only; its value depends on platform and folder mode
    assert sink.startswith("sink_mode: ")
    assert out == [
        "key ANTHROPIC_API_KEY: skipped (fake)",
        "key HADAVIN_WEBHOOK_SECRET: ok",
        "key HADAVIN_APPROVER_PASSPHRASE: ok",
        "key N8N_ENCRYPTION_KEY: ok",
        "key N8N_BASIC_AUTH_PASSWORD: ok",
        f"secrets_mode: {secret_store.mode_state(tmp_path / 'local')}",
        "secrets_in_repo: ok",
        "secrets_lock: absent",
        f"secrets_location: {secret_store.secrets_location(tmp_path / 'local')}",
        "data_hashes: 4",
        "provider_limit: missing",
        "prices: ok",
        f"prices_as_of: {out[-8].split(': ')[1]}",
        "consent: recorded",
        "halted: no",
        "spend_files: ledger_missing",
        "cap_effective_usd: 100",
        "min_limit_usd: n/a (fake)",  # a tiny fake-stand-in figure would mislead: only the live backend has a minimum
        "queue_files: absent",
        "backend: fake",
    ]
    assert len(out[-8].split(": ")[1]) == 10


def test_check_live_backend_needs_the_api_key(tmp_path, monkeypatch, capsys):
    settings_for_tests(tmp_path, with_api_key=False)
    assert run(monkeypatch, tmp_path, "check", backend="anthropic") == 2
    out = capsys.readouterr().out
    assert "key ANTHROPIC_API_KEY: fail key_name_missing" in out and "backend:" not in out  # a failed key line: no backend line at all
    s = settings_for_tests(tmp_path, backend="anthropic", with_ledger=True)
    assert run(monkeypatch, tmp_path, "check", backend="anthropic") == 2  # no provider limit recorded yet
    budget.confirm_limit(s, "LIMIT SET 100")
    assert run(monkeypatch, tmp_path, "check", backend="anthropic") == 0
    assert "key ANTHROPIC_API_KEY: ok" in capsys.readouterr().out


def test_check_reports_every_failure_code_without_a_value(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path)
    vals = fake_secret_values()
    vals["HADAVIN_WEBHOOK_SECRET"] = "tiny9"
    vals["N8N_ENCRYPTION_KEY"] = ""
    key_file(s).write_text("".join(f"{k}={v}\n" for k, v in vals.items()), encoding="utf-8")
    assert run(monkeypatch, tmp_path, "check") == 2
    cap = capsys.readouterr()
    assert "key HADAVIN_WEBHOOK_SECRET: fail key_short" in cap.out and "key N8N_ENCRYPTION_KEY: fail key_empty" in cap.out
    assert not any(v and v in cap.out + cap.err for v in vals.values())


def test_check_data_hashes_zero_is_a_refusal_and_counts_distinct_valid_lines(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path)
    h = s.intake_home / "synthetic_hashes.txt"
    h.write_text("", encoding="utf-8")
    assert run(monkeypatch, tmp_path, "check") == 2
    assert "data_hashes: 0" in capsys.readouterr().out
    h.unlink()
    assert run(monkeypatch, tmp_path, "check") == 2  # a missing list counts as empty
    h.write_text(("a" * 64) + "\n\n  " + ("a" * 64) + "  \nnot-a-hash\n" + ("B" * 64) + "\n" + ("c" * 64) + "\n", encoding="utf-8")
    assert run(monkeypatch, tmp_path, "check") == 0
    assert "data_hashes: 2" in capsys.readouterr().out  # duplicates, junk and upper-case lines are not counted


def test_check_with_a_missing_secrets_file(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path)
    key_file(s).unlink()
    assert run(monkeypatch, tmp_path, "check") == 2
    assert capsys.readouterr().out.count("fail key_file_missing") == 4


def test_init_checks_the_config_and_creates_only_the_spend_ledger_and_the_queue(tmp_path, monkeypatch, capsys):
    local = tmp_path / "local"
    monkeypatch.setenv("HADAVIN_LOCAL", str(local))
    assert cli.main(["init"]) == 0 and capsys.readouterr().out.split() == ["config:", "ok", "spend", "ledger:", "ok", "queue:", "ok"]
    assert sorted(p.name for p in local.rglob("*") if p.is_file() and not p.name.endswith(("-wal", "-shm"))) == [
        "queue.sqlite3",
        "spend.genesis",
        "spend.sqlite3",
    ]


def test_exit_3_for_unset_local_bad_backend_and_bad_command(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("HADAVIN_LOCAL", raising=False)
    assert cli.main(["check"]) == 3 and "local_unset" in capsys.readouterr().err
    monkeypatch.setenv("HADAVIN_LOCAL", str(tmp_path))
    assert run(monkeypatch, tmp_path, "check", backend="openai") == 3
    with pytest.raises(SystemExit) as ei:
        cli.main(["serve-everything"])
    assert ei.value.code == 3
    with pytest.raises(SystemExit) as ei:
        cli.main([])
    assert ei.value.code == 3


def test_module_entry_point_prints_the_key_lines(tmp_path):
    settings_for_tests(tmp_path)
    env = {**os.environ, "HADAVIN_LOCAL": str(tmp_path / "local"), "INTAKE_MODEL_BACKEND": "fake"}
    r = subprocess.run([sys.executable, "-m", "intake", "check"], env=env, capture_output=True, text=True, timeout=60, check=False)
    assert r.returncode == 0, r.stderr
    assert "key HADAVIN_WEBHOOK_SECRET: ok" in r.stdout and "backend: fake" in r.stdout and "data_hashes: 4" in r.stdout
    assert not any(v in r.stdout + r.stderr for v in fake_secret_values().values())
    assert secret_store.NAMES[0] in r.stdout


def test_check_fails_on_loose_modes_and_prints_the_file_names_only(tmp_path, monkeypatch, capsys):
    settings_for_tests(tmp_path)
    monkeypatch.setattr(secret_store.sys, "platform", "linux")
    monkeypatch.setattr(secret_store, "_stat_mode", lambda p: 0o100644)
    assert run(monkeypatch, tmp_path, "check") == 2
    out = capsys.readouterr().out
    assert "secrets_mode: fail key_mode (folder) secrets.env" in out
    monkeypatch.setattr(secret_store, "_stat_mode", lambda p: 0o100600)
    assert run(monkeypatch, tmp_path, "check") == 0
    assert "secrets_mode: ok" in capsys.readouterr().out


def test_check_prints_the_line_number_of_a_junk_line_and_nothing_else_of_it(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path)
    key_file(s).write_text("# c\nHADAVIN_WEBHOOK_SECRET=" + "a" * 40 + "\njunk " + "q" * 30 + "\n", encoding="utf-8")
    assert run(monkeypatch, tmp_path, "check") == 2
    out = capsys.readouterr().out
    assert "secrets_file: line 3 not NAME=value" in out and "q" * 30 not in out


def test_check_says_not_checked_on_windows_never_ok(tmp_path, monkeypatch, capsys):
    settings_for_tests(tmp_path)
    monkeypatch.setattr(secret_store.sys, "platform", "win32")
    assert run(monkeypatch, tmp_path, "check") == 0
    assert "secrets_mode: not_checked (windows)" in capsys.readouterr().out


def test_check_fails_when_the_key_folder_is_inside_the_repo(monkeypatch, capsys):
    monkeypatch.setenv("HADAVIN_LOCAL", str(secret_store.REPO_ROOT / "inside_the_repo_test_dir"))
    assert cli.main(["check"]) == 2
    assert "secrets_in_repo: fail secrets_in_repo" in capsys.readouterr().out


def test_check_rejects_a_relative_local_with_exit_3(monkeypatch, capsys):
    monkeypatch.setenv("HADAVIN_LOCAL", "relative/dir")
    assert cli.main(["check"]) == 3 and "absolute" in capsys.readouterr().err


def test_check_reports_a_held_lock(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path)
    (key_file(s).parent / secret_store.LOCK_FILE).write_text("x")
    assert run(monkeypatch, tmp_path, "check") == 0
    assert "secrets_lock: present" in capsys.readouterr().out


def test_an_os_error_in_check_is_a_clean_exit_3_without_a_path(tmp_path, monkeypatch, capsys):
    settings_for_tests(tmp_path)

    def boom(*a, **k):
        raise PermissionError(13, "denied", str(tmp_path))

    monkeypatch.setattr(cli, "status", boom)
    assert run(monkeypatch, tmp_path, "check") == 3
    cap = capsys.readouterr()
    assert cap.err.strip() == "error: bad_config: file error" and str(tmp_path) not in cap.out + cap.err and "Traceback" not in cap.err


def test_a_refused_start_prints_no_backend_line(tmp_path, monkeypatch, capsys):
    assert run(monkeypatch, tmp_path, "check", backend="openai") == 3
    assert "backend:" not in capsys.readouterr().out


def test_the_hash_list_loader_is_shared_with_check(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path)
    h = s.intake_home / "synthetic_hashes.txt"
    h.write_bytes(chr(0xFEFF).encode() + ("a" * 64 + "\r\n" + "  " + "b" * 64 + "\n").encode())  # a BOM, CRLF and spaces are tolerated
    assert settings.load_hash_list(h) == frozenset({"a" * 64, "b" * 64})
    assert run(monkeypatch, tmp_path, "check") == 0
    assert "data_hashes: 2" in capsys.readouterr().out


def test_a_failed_check_never_prints_backend_anthropic(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path)
    key_file(s).write_text("junk" + chr(10), encoding="utf-8")
    assert run(monkeypatch, tmp_path, "check", backend="anthropic") == 2
    assert "backend:" not in capsys.readouterr().out
    settings_for_tests(tmp_path)
    (s.intake_home / "synthetic_hashes.txt").write_text("", encoding="utf-8")  # only the list is empty: still exit 2, still no backend line
    assert run(monkeypatch, tmp_path, "check", backend="anthropic") == 2
    assert "backend:" not in capsys.readouterr().out


def test_backend_is_printed_only_when_the_exit_code_is_zero(tmp_path, monkeypatch, capsys):
    settings_for_tests(tmp_path)
    for backend in ("fake", "anthropic"):
        code = run(monkeypatch, tmp_path, "check", backend=backend)
        out = capsys.readouterr().out
        assert (code == 0) == (f"backend: {backend}" in out)
