"""I4, first version: no value from the owner's key file appears in the outputs tested. For EACH of the five names a fake value built from parts
is searched for in command output (stdout, stderr), error text, ``repr`` of settings and the output of every tool script run here. Later work
packages extend the lists below (logs, CSV, HTML, generated run files, other tools); a tool script that is not listed fails the coverage test."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from conftest import ROOT, fake_secret_values, key_file, settings_for_tests
from intake import budget, cli, secret_store, settings
from intake.codes import SecretError

VALUES = fake_secret_values()
# tools/*.py that exist before this work and never touch the key file
PRE_EXISTING_TOOLS = {"mutate_src.py", "check_core_copies.py", "docfacts.py", "private_file.py"}
# tools/*.py run here (name -> argument lists); every new tool is added by its work package
HYGIENE_RUNS = {
    "make_secrets.py": [[], ["--passphrase-file"], ["--bogus"]],
    "gen_confusables_wp3.py": [[], ["--bogus-file-that-does-not-exist"]],  # WP3: reads a local Unicode data file, no secret
    "make_run_env.py": [[], ["--remove"], ["--bogus"]],
    "n8n_setup.py": [["--wait-s", "0"], ["--bogus"]],  # wait 0: no request is made, so a running n8n is never touched
}


def leaks(*texts: str) -> list[str]:
    blob = "\n".join(texts)
    return [name for name, v in VALUES.items() if v in blob]


def test_every_tool_script_is_covered_by_the_hygiene_runs():
    tools = {p.name for p in (ROOT / "tools").glob("*.py")}
    assert tools - PRE_EXISTING_TOOLS <= set(HYGIENE_RUNS), tools - PRE_EXISTING_TOOLS - set(HYGIENE_RUNS)


@pytest.mark.parametrize("name", list(VALUES))
def test_a_fake_value_for_each_name_is_a_valid_value_so_the_search_means_something(name, tmp_path):
    settings_for_tests(tmp_path)
    assert secret_store.get(name, local=tmp_path / "local") == VALUES[name]


@pytest.mark.parametrize("backend", ["fake", "anthropic"])
def test_check_output_for_ok_and_failing_files(tmp_path, monkeypatch, capsys, backend):
    s = settings_for_tests(tmp_path, backend=backend, with_ledger=True)
    if backend == "anthropic":
        budget.confirm_limit(s, "LIMIT SET 100")  # the live backend needs a recorded provider limit for exit 0
    monkeypatch.setenv("HADAVIN_LOCAL", str(tmp_path / "local"))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", backend)
    for name, v in VALUES.items():
        monkeypatch.setenv(name, v + "ENVONLY")  # a stray environment value must neither be used nor printed
    assert cli.main(["check"]) == 0
    cap = capsys.readouterr()
    assert not leaks(cap.out, cap.err) and not any(v + "ENVONLY" in cap.out + cap.err for v in VALUES.values())
    # failing shapes: every value is wrong in some way, each fake value is still in the file
    bad = {n: " " + v for n, v in VALUES.items()}
    key_file(s).write_text("".join(f"{k}={v}\n" for k, v in bad.items()), encoding="utf-8")
    assert cli.main(["check"]) == 2
    cap = capsys.readouterr()
    assert not leaks(cap.out, cap.err) and "fail key_malformed" in cap.out
    # a line that is not NAME=value contains a value: it must not be echoed
    key_file(s).write_text(f"oops {VALUES['ANTHROPIC_API_KEY']}\n", encoding="utf-8")
    assert cli.main(["check"]) == 2
    cap = capsys.readouterr()
    assert not leaks(cap.out, cap.err)


def test_error_text_and_repr_never_hold_a_value(tmp_path):
    s = settings_for_tests(tmp_path)
    assert not leaks(repr(s), str(s), repr(s.model), repr(settings.load_prices(s.prices_path)))
    for name, v in VALUES.items():
        for mutated in (
            v + " tail",
            " " + v,
            '"' + v,
            v[: max(1, secret_store.MIN_LENGTH.get(name, 20) - 1)] if name != "ANTHROPIC_API_KEY" else v + "!",
        ):
            key_file(s).write_text(f"{name}={mutated}\n", encoding="utf-8")
            with pytest.raises(SecretError) as ei:
                secret_store.get(name, local=tmp_path / "local")
            assert not leaks(str(ei.value), repr(ei.value), ei.value.text, ei.value.code)
        key_file(s).write_text(f"{name}={v}\n{name}={v}x\n", encoding="utf-8")  # duplicate
        with pytest.raises(SecretError) as ei:
            secret_store.get(name, local=tmp_path / "local")
        assert not leaks(str(ei.value))


def _run(args: list[str], env: dict, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(args, env=env, capture_output=True, text=True, timeout=120, cwd=cwd, check=False)


@pytest.mark.parametrize("tool", list(HYGIENE_RUNS))
def test_tool_scripts_never_print_a_value(tool, tmp_path):
    local = tmp_path / "local"
    (local / "secrets").mkdir(parents=True)
    (local / "secrets" / "secrets.env").write_text("".join(f"{k}={v}\n" for k, v in VALUES.items()), encoding="utf-8")
    base = {**os.environ, "HADAVIN_LOCAL": str(local), **VALUES}
    for argv in HYGIENE_RUNS[tool]:
        r = _run([sys.executable, str(ROOT / "tools" / tool), *argv], base)
        assert not leaks(r.stdout, r.stderr), (tool, argv)
        assert "Traceback" not in r.stderr, (tool, argv, r.stderr[-300:])
    # a corrupt key file: the failure text must not echo the file's lines
    (local / "secrets" / "secrets.env").write_text(f"junk line {VALUES['HADAVIN_WEBHOOK_SECRET']}\n", encoding="utf-8")
    for argv in HYGIENE_RUNS[tool]:
        r = _run([sys.executable, str(ROOT / "tools" / tool), *argv], base)
        assert not leaks(r.stdout, r.stderr), (tool, argv)
        assert "Traceback" not in r.stderr
    # no HADAVIN_LOCAL at all
    r = _run([sys.executable, str(ROOT / "tools" / tool), *HYGIENE_RUNS[tool][0]], {k: v for k, v in base.items() if k != "HADAVIN_LOCAL"})
    assert r.returncode == 3 and not leaks(r.stdout, r.stderr)


def test_make_secrets_output_names_only(tmp_path):
    local = tmp_path / "local"
    env = {**os.environ, "HADAVIN_LOCAL": str(local)}
    r = _run([sys.executable, str(ROOT / "tools" / "make_secrets.py")], env)
    assert r.returncode == 0, r.stderr
    values = sum(secret_store.parse(local / "secrets" / "secrets.env").values(), [])
    assert len(values) == 4 and not any(v in r.stdout + r.stderr for v in values)
    assert set(r.stdout.split()) <= {"added", "wrote", "done", "approver-passphrase.txt", *secret_store.NAMES}


def test_module_entry_point_with_values_in_the_environment(tmp_path):
    settings_for_tests(tmp_path)
    env = {**os.environ, "HADAVIN_LOCAL": str(tmp_path / "local"), **{k: v + "ENVONLY" for k, v in VALUES.items()}}
    r = _run([sys.executable, "-m", "intake", "check"], env)
    assert r.returncode == 0 and not leaks(r.stdout, r.stderr) and "ENVONLY" not in r.stdout + r.stderr


def test_settings_load_never_reads_the_key_file(tmp_path, monkeypatch):
    s = settings_for_tests(tmp_path)
    key_file(s).write_bytes(b"\xff\xfe not even utf-8")
    assert settings.load({"HADAVIN_LOCAL": str(tmp_path / "local")}).backend == "fake"  # only secret_store reads that file
