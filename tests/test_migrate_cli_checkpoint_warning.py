"""`hadavin-sdk migrate --runtime-role R` without `--checkpoint-role`: the warning says the truth (the runtime holds
SELECT only on audit_checkpoints, so NO checkpoint is written), not that the runtime still writes them."""

from __future__ import annotations

import os
from types import SimpleNamespace

from hadavin_sdk import cli
from hadavin_sdk.store import migrate as migrate_mod
from hadavin_sdk.store import postgres as postgres_mod


def _run(monkeypatch, capsys, **roles):
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", "postgresql://unused")
    monkeypatch.setattr(migrate_mod, "migrate", lambda *a, **k: [])
    monkeypatch.setattr(postgres_mod, "ca_file", lambda *a, **k: None)
    monkeypatch.setattr(cli, "make", lambda *a, **k: SimpleNamespace(get=lambda n: None))
    store = SimpleNamespace(kind="postgres", iam_auth=False, region=None, sslmode=None)
    cfg = SimpleNamespace(backends=SimpleNamespace(store=store, secrets=None))
    assert cli._migrate(cfg, "rt", **roles) == 0
    return capsys.readouterr().err


def test_without_a_checkpoint_role_the_warning_says_no_checkpoint_is_written(monkeypatch, capsys):
    err = _run(monkeypatch, capsys)
    assert "no checkpoint role was named" in err
    assert "NO checkpoint is written" in err and "SELECT only" in err
    assert "still writes" not in err


def test_with_a_checkpoint_role_there_is_no_such_warning(monkeypatch, capsys):
    assert "no checkpoint role" not in _run(monkeypatch, capsys, checkpoint_role="ck")
    assert os.environ["HADAVIN_MIGRATE_DSN"]
