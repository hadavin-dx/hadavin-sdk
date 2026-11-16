"""tools/n8n_setup.py and tools/make_run_env.py without Docker: no secret in argv, step order, idempotent owner setup, failure text without secrets,
the generated run file holds exactly one name."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys

import pytest

from conftest import fake_secret_values, settings_for_tests
from intake import secret_store
from tools import make_run_env, n8n_setup

VALUES = fake_secret_values()
TOKEN, PASSWORD = VALUES["HADAVIN_WEBHOOK_SECRET"], VALUES["N8N_BASIC_AUTH_PASSWORD"]


class Recorder:
    def __init__(self, rc=0):
        self.calls, self.rc = [], rc

    def __call__(self, cmd, **kw):
        self.calls.append((cmd, kw.get("input")))
        return subprocess.CompletedProcess(cmd, self.rc, stdout="out " + TOKEN, stderr="err " + TOKEN)


@pytest.fixture
def env(tmp_path, monkeypatch):
    settings_for_tests(tmp_path)
    monkeypatch.setenv("HADAVIN_LOCAL", str(tmp_path / "local"))
    monkeypatch.setattr(n8n_setup, "wait_ready", lambda wait_s=0: None)
    monkeypatch.setattr(n8n_setup.time, "sleep", lambda s: None)
    return tmp_path


def run_setup(monkeypatch, rest_replies, rc=0):
    rec = Recorder(rc)
    monkeypatch.setattr(n8n_setup.subprocess, "run", rec)
    seen = []

    def fake_rest(method, path, body=None):
        seen.append((method, path, body))
        return rest_replies.pop(0)

    monkeypatch.setattr(n8n_setup, "rest", fake_rest)
    return rec, seen


def test_steps_in_order_and_secrets_only_on_stdin(env, monkeypatch, capsys):
    rec, seen = run_setup(monkeypatch, [(200, "{}")])
    assert n8n_setup.main([]) == 0
    verbs = [c[0][c[0].index("n8n") + 1] for c in rec.calls]
    assert verbs == ["import:credentials", "import:workflow", "publish:workflow"]
    for cmd, _stdin in rec.calls:
        assert cmd[0] == "docker" and cmd[1] == "exec"
        assert not any(TOKEN in a or PASSWORD in a for a in cmd)  # argv holds no secret
    assert rec.calls[0][0][2] == "-i" and TOKEN in rec.calls[0][1] and rec.calls[0][0].count("--input=/dev/stdin") == 1
    assert rec.calls[2][1] is None and rec.calls[2][0][-1] == "--id=intakewf1000001"
    assert seen[0][1] == "/rest/owner/setup" and seen[0][2]["password"] == PASSWORD and seen[0][2]["email"].endswith("@intake.example.com")
    out = capsys.readouterr()
    assert out.out.split() == [
        "step",
        "n8n-ready",
        "ok",
        "step",
        "owner-setup",
        "ok",
        "step",
        "credentials",
        "ok",
        "step",
        "workflow-import",
        "ok",
        "step",
        "publish",
        "ok",
        "done",
    ]
    assert TOKEN not in out.out + out.err and PASSWORD not in out.out + out.err


def test_workflow_import_payload_has_ids_and_no_secret(env, monkeypatch):
    rec, _ = run_setup(monkeypatch, [(200, "{}")])
    n8n_setup.main([])
    wf = json.loads(rec.calls[1][1])[0]
    assert TOKEN not in rec.calls[1][1] and wf["id"] == n8n_setup.WF_ID
    ids = {n["credentials"][k]["name"]: n["credentials"][k]["id"] for n in wf["nodes"] for k in n.get("credentials", {})}
    assert ids == {"intake-token": n8n_setup.CRED_TOKEN_ID, "intake-smtp": n8n_setup.CRED_SMTP_ID}
    creds = json.loads(rec.calls[0][1])
    assert {c["id"] for c in creds} == {n8n_setup.CRED_TOKEN_ID, n8n_setup.CRED_SMTP_ID}
    assert creds[0]["data"] == {"name": "X-Hadavin-Token", "value": TOKEN}


def test_second_run_owner_already_setup_is_a_no_op(env, monkeypatch, capsys):
    run_setup(monkeypatch, [(400, '{"code":400,"message":"Instance owner already setup"}'), (200, "{}")])
    assert n8n_setup.main([]) == 0 and "owner-setup ok" in capsys.readouterr().out


def test_owner_setup_failure_stops_before_any_import(env, monkeypatch, capsys):
    rec, _ = run_setup(monkeypatch, [(500, "boom " + PASSWORD)])
    assert n8n_setup.main([]) == 3
    assert rec.calls == []
    err = capsys.readouterr().err
    assert "owner-setup failed http=500" in err and PASSWORD not in err


def test_docker_failure_prints_step_and_code_never_the_output(env, monkeypatch, capsys):
    run_setup(monkeypatch, [(200, "{}")], rc=1)
    assert n8n_setup.main([]) == 3
    cap = capsys.readouterr()
    assert "credentials failed rc=1" in cap.err and TOKEN not in cap.out + cap.err


def test_missing_secret_is_refused_not_a_traceback(env, monkeypatch, capsys):
    (env / "local" / "secrets" / "secrets.env").write_text("", encoding="utf-8")
    run_setup(monkeypatch, [])
    assert n8n_setup.main([]) == 2
    assert "key_name_missing" in capsys.readouterr().err


def test_not_ready_is_an_error(monkeypatch, tmp_path, capsys):
    settings_for_tests(tmp_path)
    monkeypatch.setenv("HADAVIN_LOCAL", str(tmp_path / "local"))
    monkeypatch.setattr(n8n_setup, "rest", lambda *a, **k: (0, ""))
    assert n8n_setup.main(["--wait-s", "0"]) == 3 and "n8n-not-ready" in capsys.readouterr().err


def test_bad_arguments_and_unset_local(monkeypatch):
    assert n8n_setup.main(["--bogus"]) == 3
    monkeypatch.delenv("HADAVIN_LOCAL", raising=False)
    assert n8n_setup.main([]) == 3


def test_rest_reaches_only_the_pinned_loopback_url():
    assert n8n_setup.BASE == "http://127.0.0.1:5678"


# ---- make_run_env -----------------------------------------------------------------------------------------------------------------------------
def test_run_env_holds_exactly_one_name_and_no_anthropic_text(env, capsys):
    assert make_run_env.main([]) == 0
    text = (env / "local" / "run" / "n8n.env").read_text(encoding="utf-8")
    assert text == f"N8N_ENCRYPTION_KEY={VALUES['N8N_ENCRYPTION_KEY']}\n"
    assert "ANTHROPIC" not in text.upper() and len([ln for ln in text.splitlines() if ln]) == 1
    out = capsys.readouterr()
    assert out.out.strip() == "wrote n8n.env" and VALUES["N8N_ENCRYPTION_KEY"] not in out.out + out.err


@pytest.mark.skipif(sys.platform == "win32", reason="mode bits only on POSIX")
def test_run_env_mode_is_0600(env):
    make_run_env.main([])
    assert stat.S_IMODE(os.stat(env / "local" / "run" / "n8n.env").st_mode) == 0o600


def test_run_env_replaces_a_stale_file_and_remove_deletes_it(env):
    p = env / "local" / "run" / "n8n.env"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("STALE=1\nOTHER=2\n", encoding="utf-8")
    assert make_run_env.main([]) == 0 and "STALE" not in p.read_text(encoding="utf-8")
    assert make_run_env.main(["--remove"]) == 0 and not p.exists()
    assert make_run_env.main(["--remove"]) == 0  # nothing to remove is fine


def test_run_env_missing_key_is_refused_and_writes_nothing(env, capsys):
    (env / "local" / "secrets" / "secrets.env").write_text(f"ANTHROPIC_API_KEY={VALUES['ANTHROPIC_API_KEY']}\n", encoding="utf-8")
    assert make_run_env.main([]) == 2
    assert not (env / "local" / "run" / "n8n.env").exists()
    assert VALUES["ANTHROPIC_API_KEY"] not in capsys.readouterr().err


def test_run_env_bad_arguments_and_unset_local(monkeypatch):
    assert make_run_env.main(["--bogus"]) == 3
    monkeypatch.delenv("HADAVIN_LOCAL", raising=False)
    assert make_run_env.main([]) == 3


def test_run_env_uses_the_file_only_secret_lookup():
    assert secret_store.N8N_ENCRYPTION_KEY == "N8N_ENCRYPTION_KEY"


def test_a_step_that_fails_while_n8n_starts_is_tried_again_then_succeeds(env, monkeypatch):
    rcs = iter([1, 1, 0, 0, 0])

    def flaky(cmd, **kw):
        return subprocess.CompletedProcess(cmd, next(rcs), stdout="", stderr="")

    run_setup(monkeypatch, [(200, "{}")])
    monkeypatch.setattr(n8n_setup.subprocess, "run", flaky)
    assert n8n_setup.main([]) == 0


def test_a_step_that_keeps_failing_stops_after_the_tries(env, monkeypatch):
    rec, _ = run_setup(monkeypatch, [(200, "{}")], rc=1)
    assert n8n_setup.main([]) == 3
    assert len([c for c in rec.calls if c[0][1] == "exec"]) == 4  # literal: the constant itself is under mutation


def test_already_setup_text_is_pinned_exactly(env, monkeypatch, capsys):
    assert n8n_setup.ALREADY_SETUP == "Instance owner already setup"
    run_setup(monkeypatch, [(400, '{"code":400,"message":"Instance owner already setup"}'), (200, "{}")])
    assert n8n_setup.main([]) == 0
    for other in ("Password too weak", "owner already exists elsewhere"):  # any other 400 is a failure, not a no-op
        run_setup(monkeypatch, [(400, '{"code":400,"message":"' + other + '"}')])
        assert n8n_setup.main([]) == 3 and "owner-setup failed http=400" in capsys.readouterr().err


def test_failure_hints_name_docker_and_hold_no_secret(env, monkeypatch, capsys):
    run_setup(monkeypatch, [(200, "{}")], rc=1)
    n8n_setup.main([])
    err = capsys.readouterr().err
    assert "Docker Desktop" in err and "safe to repeat" in err and TOKEN not in err and PASSWORD not in err


def test_not_ready_hint_names_docker(monkeypatch, tmp_path, capsys):
    settings_for_tests(tmp_path)
    monkeypatch.setenv("HADAVIN_LOCAL", str(tmp_path / "local"))
    monkeypatch.setattr(n8n_setup, "rest", lambda *a, **k: (0, ""))
    assert n8n_setup.main(["--wait-s", "0"]) == 3
    assert "Docker Desktop" in capsys.readouterr().err


def test_a_stopped_container_is_started_again_before_the_retry(env, monkeypatch):
    seen = []

    def fake(cmd, **kw):
        seen.append(cmd[1])
        rc = 1 if cmd[1] == "exec" and seen.count("exec") == 1 else 0
        out = "false" if cmd[1] == "inspect" else ""
        return subprocess.CompletedProcess(cmd, rc, stdout=out, stderr="")

    run_setup(monkeypatch, [(200, "{}")])
    monkeypatch.setattr(n8n_setup.subprocess, "run", fake)
    assert n8n_setup.main([]) == 0
    assert "inspect" in seen and "start" in seen and seen.index("start") < len(seen) - 1  # started, then the step was repeated


def test_readiness_endpoint_is_the_one_waited_on(monkeypatch):
    urls = []
    monkeypatch.setattr(n8n_setup, "rest", lambda m, path, body=None: (urls.append(path), (200, ""))[1])
    n8n_setup.wait_ready(5)
    assert urls == ["/healthz/readiness"]


@pytest.mark.parametrize("arg", ["180", "180.0", "0", "0.5"])
def test_wait_seconds_accepts_integers_and_decimals(arg, monkeypatch, tmp_path, capsys):
    settings_for_tests(tmp_path)
    monkeypatch.setenv("HADAVIN_LOCAL", str(tmp_path / "local"))
    seen = []
    monkeypatch.setattr(n8n_setup, "run", lambda wait_s=0: seen.append(wait_s))
    assert n8n_setup.main(["--wait-s", arg]) == 0 and seen == [float(arg)]


@pytest.mark.parametrize("arg", ["-1", "abc", "nan", "99999", ""])
def test_wait_seconds_rejects_bad_values(arg):
    assert n8n_setup.main(["--wait-s", arg]) == 3


def test_after_already_setup_the_stored_password_must_log_in(env, monkeypatch, capsys):
    rec, seen = run_setup(monkeypatch, [(400, '{"code":400,"message":"Instance owner already setup"}'), (401, "wrong")])
    assert n8n_setup.main([]) == 3
    assert rec.calls == []  # nothing is imported into somebody else's n8n
    err = capsys.readouterr().err
    assert "owner-login failed" in err and "stop_demo.ps1" in err and PASSWORD not in err
    assert [s[1] for s in seen] == ["/rest/owner/setup", "/rest/login"] and seen[1][2]["password"] == PASSWORD


def test_a_fresh_setup_does_not_log_in(env, monkeypatch):
    rec, seen = run_setup(monkeypatch, [(200, "{}")])
    assert n8n_setup.main([]) == 0
    assert [s[1] for s in seen] == ["/rest/owner/setup"]  # only the second run needs the check
