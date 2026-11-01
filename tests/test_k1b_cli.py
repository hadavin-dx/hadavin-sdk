"""K1b phase 6: the replay and score commands end to end on the fake llm kind, exit codes, the main wrapper."""

import json

import pytest

from hadavin_sdk import cli
from hadavin_sdk.audit import AuditUnavailable, LocalDirSink
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.k1b.audit_sink import K1bAudit
from tests.k1b_support import dry_run_export, make_bundle


@pytest.fixture
def export(tmp_path, cfg_dir):
    return dry_run_export(tmp_path, cfg_dir)


def _replay(cfg_dir, export, *extra, bundles=None, out=None, usd="5"):
    return cli.main(
        [
            "--config", str(cfg_dir), "replay", "test-agent",
            "--bundles", str(bundles or export["bundles"]),
            "--cause-list", str(export["cause"]),
            "--max-usd", usd, "--out", str(out or export["out"]), *extra,
        ]
    )  # fmt: skip


def _score(cfg_dir, export):
    return cli.main(
        [
            "--config", str(cfg_dir), "score", "--outputs", str(export["out"]),
            "--answers", str(export["answers"]), "--cause-list", str(export["cause"]),
            "--bundles", str(export["bundles"]),
        ]
    )  # fmt: skip


def test_end_to_end_replay_then_score(cfg_dir, export, capsys):
    assert _replay(cfg_dir, export) == 0
    out = export["out"]
    assert (out / "run1" / "case-003.json").is_file() and (out / "replay-report.md").is_file()
    assert (
        json.loads((out / "run1" / "case-003.json").read_text(encoding="utf-8"))["converted"]
        == "uncited"
    )
    assert _score(cfg_dir, export) == 0
    text = (out / "score" / "score-report.md").read_text(encoding="utf-8")
    assert (
        "| 1 | 1 | 1 | 2 | 2 | 1/0/0/0 | 1 | 0 |" in text
    )  # Hit, no-evidence Hit, 2 Misses, 2 Not sure
    assert "SDK version: 0.1.0" in text
    ops = [e.operation for e in LocalDirSink(cfg_dir / "audit").events()]
    assert (
        ops.count("replay_run") == 1
        and ops.count("hard_check_b") == 1
        and ops.count("score_run") == 1
    )
    ev = next(e for e in LocalDirSink(cfg_dir / "audit").events() if e.operation == "score_run")
    assert ev.result == "H=2;Hne=1;M=2;S=2;ic=1;ha=0" and ev.decision == "-" and ev.domain == "k1b"
    assert "ghost" not in text
    capsys.readouterr()


def test_score_again_is_refused_because_the_report_folder_is_not_empty(cfg_dir, export):
    assert _replay(cfg_dir, export) == 0 and _score(cfg_dir, export) == 0
    assert _score(cfg_dir, export) == 2


def test_poisoned_bundle_is_refused_with_nothing_written(cfg_dir, export, capsys):
    assert _replay(cfg_dir, export, bundles=export["poisoned"]) == 2
    assert "after the alert time" in capsys.readouterr().err
    assert not export["out"].exists()
    assert not (cfg_dir / "audit").exists() or LocalDirSink(cfg_dir / "audit").events() == []


def test_replay_into_a_non_empty_folder_is_refused(cfg_dir, export):
    export["out"].mkdir()
    (export["out"] / "x").write_text("1", encoding="utf-8")
    assert _replay(cfg_dir, export) == 2


def test_usd_cap_exits_1_and_report_shows_capped_cases(cfg_dir, export):
    assert _replay(cfg_dir, export, usd="0.01") == 1
    text = (export["out"] / "replay-report.md").read_text(encoding="utf-8")
    assert "**Capped cases: 5.**" in text and "0.1.0" in text
    assert _score(cfg_dir, export) == 0  # capped incidents are Misses; the report still comes out


def test_k2_runs(cfg_dir, export):
    # Recordings hold one attempt per message list; a second run has none, so it fails as an unknown recording.
    assert _replay(cfg_dir, export, "--k", "2") == 3


def test_bad_numbers_are_usage_errors(cfg_dir, export):
    for usd in ("0", "abc", "-1", "NaN"):
        with pytest.raises(SystemExit) as exc:
            _replay(cfg_dir, export, usd=usd)
        assert exc.value.code == 2


def test_audit_failure_exits_3_and_score_prints_nothing(cfg_dir, export, monkeypatch):
    assert _replay(cfg_dir, export) == 0

    class Down:
        def write_intent(self, event):
            raise AuditUnavailable("down")

    from hadavin_sdk.k1b import audit_sink

    monkeypatch.setattr(audit_sink, "build_audit", lambda cfg, secrets: (K1bAudit(Down()), []))
    assert _score(cfg_dir, export) == 3
    assert not (export["out"] / "score").exists()


def test_chain_over_memory_store_warns_and_continues(cfg_dir, export, capsys):
    p = cfg_dir / "config.yaml"
    p.write_text(
        p.read_text(encoding="utf-8").replace(
            "audit: {kind: local_dir, dir: audit}", "audit: chain"
        ),
        encoding="utf-8",
    )
    assert _replay(cfg_dir, export) == 0
    assert "events are lost at exit" in capsys.readouterr().err


# ---------------------------------------------------------------- main wrapper


def test_main_maps_config_error_to_2_and_anything_else_to_3(cfg_dir, monkeypatch, capsys):
    def refuse(*_a, **_k):
        raise ConfigError("nope")

    def crash(*_a, **_k):
        raise RuntimeError("secret-looking text")

    monkeypatch.setattr(cli, "_main", refuse)
    assert cli.main(["x"]) == 2 and "refused: nope" in capsys.readouterr().err
    monkeypatch.setattr(cli, "_main", crash)
    assert cli.main(["x"]) == 3
    err = capsys.readouterr().err
    assert "RuntimeError" in err and "secret-looking" not in err


def test_main_missing_config_is_exit_2(tmp_path, monkeypatch):
    monkeypatch.delenv("HADAVIN_CONFIG_DIR", raising=False)
    assert cli.main(["--config", str(tmp_path / "nope"), "gate", "test-agent"]) == 2


def test_report_and_runbook_line_exist():
    from pathlib import Path

    readme = (Path(__file__).parents[1] / "README.md").read_text(encoding="utf-8")
    assert "FAILED.txt" in readme and "delete the folder" in readme


def test_exempt_keys_still_check_values_and_outcome_keys_still_refuse(tmp_path):
    from hadavin_sdk.k1b.bundle import BundleError, load_bundle
    from tests.k1b_support import default_parts, write_manifest

    k8s = default_parts()["k8s"]["001"]
    deployment = {
        "strategy": {"rollingUpdate": {"maxSurge": 1}},
        "updateStrategy": "x",
        "prefix": "a",
    }
    assert load_bundle(make_bundle(tmp_path / "ok", k8s={"001": {**k8s, "spec": deployment}}))
    bad_specs = {
        "closed_at": {"closed_at": "n"},
        "resolved_at": {"resolved_at": "n"},
        "status": {"status": "x"},
        "nested status": {"strategy": {"status": "x"}},
        "later value under exempt key": {"rollingUpdate": "2026-01-02T00:00:00Z"},
        "later value under prefix": {"prefix": "2026-01-02T00:00:00Z"},
    }
    for name, spec in bad_specs.items():
        d = make_bundle(tmp_path / name.replace(" ", "_"), k8s={"001": {**k8s, "spec": spec}})
        write_manifest(d)
        with pytest.raises(BundleError):
            load_bundle(d)
    alert = {"title": "t", "labels": {"resolved_at": "x"}}
    with pytest.raises(BundleError):
        load_bundle(make_bundle(tmp_path / "alert", alert=alert))


def test_debug_env_prints_the_traceback(monkeypatch, capsys):
    def crash(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli, "_main", crash)
    monkeypatch.setenv("HADAVIN_DEBUG", "1")
    assert cli.main(["x"]) == 3
    assert "Traceback" in capsys.readouterr().err


def test_report_write_failure_leaves_started_then_failed_and_no_score_run(
    cfg_dir, export, monkeypatch
):
    assert _replay(cfg_dir, export) == 0
    from hadavin_sdk.k1b import atomic

    def boom(path, text):
        raise OSError("disk full")

    monkeypatch.setattr(atomic, "atomic_write", boom)
    assert _score(cfg_dir, export) == 3
    evs = [
        (e.operation, e.result)
        for e in LocalDirSink(cfg_dir / "audit").events()
        if e.operation.startswith("score")
    ]
    assert evs == [("score_report", "started"), ("score_report", "failed")]
    failed = next(e for e in LocalDirSink(cfg_dir / "audit").events() if e.result == "failed")
    assert failed.error_code == "OSError"


def test_score_run_events_come_after_the_report_exists(cfg_dir, export, monkeypatch):
    assert _replay(cfg_dir, export) == 0
    report = export["out"] / "score" / "score-report.md"
    seen = {}
    real = K1bAudit.emit

    def spy(self, op, run_id, **kw):
        seen[(op, kw.get("result"))] = report.is_file()
        return real(self, op, run_id, **kw)

    monkeypatch.setattr(K1bAudit, "emit", spy)
    assert _score(cfg_dir, export) == 0
    assert seen[("score_report", "started")] is False
    assert seen[("score_report", "written")] is True
    assert [v for k, v in seen.items() if k[0] == "score_run"] == [True]
    ops = [(e.operation, e.result) for e in LocalDirSink(cfg_dir / "audit").events()]
    tail = [o for o in ops if o[0].startswith("score")]
    assert [t[0] for t in tail] == ["score_report", "score_report", "score_run"]
    assert tail[1][1] == "written"


def test_version_is_real_and_matches_pyproject():
    import tomllib
    from pathlib import Path

    import hadavin_sdk

    root = Path(__file__).resolve().parent.parent
    proj = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    assert hadavin_sdk.__version__ == proj != "0.0.0"


def test_uv_lock_version_matches_the_package():
    import re
    from pathlib import Path

    import hadavin_sdk

    lock = (Path(__file__).resolve().parent.parent / "uv.lock").read_text(encoding="utf-8")
    m = re.search(r'name = "hadavin-sdk"\s+version = "([^"]+)"', lock)
    assert m and m.group(1) == hadavin_sdk.__version__


def test_score_and_replay_reports_name_the_cases_to_inspect(cfg_dir, export):
    assert _replay(cfg_dir, export) == 0 and _score(cfg_dir, export) == 0
    replay_report = (export["out"] / "replay-report.md").read_text(encoding="utf-8")
    score_report = (export["out"] / "score" / "score-report.md").read_text(encoding="utf-8")
    for text in (replay_report, score_report):
        assert "Cases to inspect (case ids):" in text
        assert "unreadable case-002" in text and "uncited case-003" in text
        assert "bad_deploy" not in text and "oom" not in text


def test_score_refuses_a_run_json_whose_issue_cases_disagree_with_the_files(cfg_dir, export):
    assert _replay(cfg_dir, export) == 0
    path = export["out"] / "run1" / "run.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["issue_cases"]["unreadable"] = []
    path.write_text(json.dumps(meta), encoding="utf-8")
    assert _score(cfg_dir, export) == 2


def test_cli_refuses_redact_false_without_the_flag_and_records_it_with(cfg_dir, export, capsys):
    p = cfg_dir / "config.yaml"
    p.write_text(p.read_text(encoding="utf-8") + "\nk1b:\n  redact: false\n", encoding="utf-8")
    assert _replay(cfg_dir, export) == 2
    assert "already masked" in capsys.readouterr().err and not export["out"].exists()
    assert _replay(cfg_dir, export, "--i-know-data-is-already-masked") == 0
    run = json.loads((export["out"] / "run1" / "run.json").read_text(encoding="utf-8"))
    assert run["redaction"]["mode"] == "off_acknowledged"
