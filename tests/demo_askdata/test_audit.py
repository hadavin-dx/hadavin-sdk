"""`audit list|show|verify|export`, `meter`, `killswitch` through the real CLI entry point."""

from __future__ import annotations

import json

import pytest
from askdata import cli
from askdata.fixtures import Step

from .kit import COUNT_ORDERS, Kit

ESC = chr(27)
Q = "How many orders are there"


def write_config(kit: Kit) -> str:
    p = kit.tmp / "askdata.yaml"
    p.write_text(
        """as_of: "2026-10-15"
paths:
  ledger_file: ledger.jsonl
  audit_dir: audit
  meter_file: meter.json
  kill_switch_file: kill.flag
  eval_dir: eval
  runs_dir: runs
  recorded_dir: recorded
route: {model_id: fake-model-1, input_usd_per_mtok: "2", output_usd_per_mtok: "10", max_tokens: 1024}
""",
        encoding="utf-8",
    )
    return str(p)


@pytest.fixture
def kit(tmp_path):
    k = Kit(tmp_path)
    k.script(Q, Step(sql=COUNT_ORDERS))
    k.script("=cmd|calc orders", Step(abstain="out_of_scope"))
    k.script("delete everything", Step(abstain="write_request"))
    k.pipeline.ask(Q, asker="claimed:rakesh")
    k.pipeline.ask(
        "=cmd|calc orders",
        asker=f"claimed:evil{ESC}[2K{ESC}Q local integrity check: 41 of 41 events match",
    )
    k.pipeline.ask("delete everything")
    return k


def run(capsys, kit, *args) -> tuple[int, str]:
    code = cli.main(["--config", write_config(kit), *args])
    return code, capsys.readouterr().out


def test_list_shows_every_line_and_never_a_raw_escape(kit, capsys):
    code, text = run(capsys, kit, "audit", "list")
    assert code == 0 and "3 ledger line(s)" in text and ESC not in text
    assert "answered" in text and "abstained" in text and "refused" in text
    assert "\\x1b" in text  # the attack is visible, not silently dropped


def test_list_last_limits_the_rows(kit, capsys):
    _, text = run(capsys, kit, "audit", "list", "--last", "1")
    assert text.count("claimed:") == 1 and "3 ledger line(s)" in text


def test_show_prints_the_line_its_hash_and_its_events(kit, capsys):
    qid = kit.ledger.read().items[0].line.query_id
    code, text = run(capsys, kit, "audit", "show", qid[:8])
    assert (
        code == 0
        and qid in text
        and "ledger line sha256" in text
        and "intent" in text
        and "decision=answered" in text
    )
    assert ESC not in text


def test_show_needs_exactly_one_match(kit, capsys):
    code, _ = run(capsys, kit, "audit", "show", "zzzz")
    assert code == 1


def test_verify_is_green_labelled_local_and_exit_0(kit, capsys):
    code, text = run(capsys, kit, "audit", "verify")
    assert (
        code == 0 and "local integrity check: 4 of 4 events and 3 of 3 ledger lines match" in text
    )
    assert "chain" not in text.lower()


def test_verify_exits_3_when_the_ledger_was_edited(kit, capsys):
    kit.ledger.path.write_bytes(
        kit.ledger.path.read_bytes().replace(b"claimed:rakesh", b"claimed:mallory")
    )
    code, text = run(capsys, kit, "audit", "verify")
    assert code == 3 and "problem:" in text


def test_export_json_redacts_text_by_default(kit, capsys):
    code, text = run(capsys, kit, "audit", "export")
    rows = json.loads(text)
    assert code == 0 and len(rows) == 3
    assert rows[0]["question"] == {"length": len(Q), "sha256": rows[0]["question_sha256"]}
    assert (
        Q not in text
        and "SELECT" not in text
        and rows[0]["attempts"][0]["canonical_sql"]["length"] > 0
    )
    assert rows[0]["asker"] == "claimed:rakesh"  # the asker is kept


def test_export_include_text_is_an_explicit_opt_in(kit, capsys):
    _, text = run(capsys, kit, "audit", "export", "--include-text")
    assert Q in text and "SELECT" in text and ESC not in text


def test_csv_export_guards_formula_cells_and_strips_escapes(kit, capsys):
    code, text = run(capsys, kit, "audit", "export", "--format", "csv", "--include-text")
    lines = text.splitlines()
    assert code == 0 and lines[0].startswith("query_id,ts,asker,question")
    assert any(",'=cmd|calc orders," in ln for ln in lines) and ESC not in text
    assert not any(c.startswith(("=", "+", "-", "@")) for ln in lines[1:] for c in ln.split(","))


def test_csv_redacted_cells_are_hashes(kit, capsys):
    _, text = run(capsys, kit, "audit", "export", "--format", "csv")
    assert "sha256:" in text and Q not in text


def test_export_to_a_file(kit, capsys, tmp_path):
    dest = tmp_path / "out.json"
    code, text = run(capsys, kit, "audit", "export", "--out", str(dest))
    assert code == 0 and "redacted" in text and len(json.loads(dest.read_text())) == 3


def test_killswitch_writes_the_audit_event_first_then_the_flag(kit, capsys):
    assert run(capsys, kit, "killswitch", "status")[1].startswith("killswitch: off")
    code, _ = run(capsys, kit, "killswitch", "on")
    assert code == 0 and kit.kill.is_on()
    ev = [e for e in kit.sink.events() if e.operation == "killswitch"]
    assert [e.decision for e in ev] == ["on"]
    assert "ON" in run(capsys, kit, "killswitch", "status")[1]
    a = kit.pipeline.ask(Q)
    assert a.reason == "kill_switch"
    run(capsys, kit, "killswitch", "off")
    assert not kit.kill.is_on() and [
        e.decision for e in kit.sink.events() if e.operation == "killswitch"
    ] == ["on", "off"]


def test_killswitch_does_nothing_when_the_audit_is_unavailable(tmp_path, capsys):
    k = Kit(tmp_path)
    (tmp_path / "audit").mkdir(exist_ok=True)
    (tmp_path / "audit" / "objects").write_text("a file where a folder must be")
    code, text = run(capsys, k, "killswitch", "on")
    assert code == 5 and "nothing changed" in text and not k.kill.is_on()


def test_meter_shows_the_figures_and_accepts_the_external_spend(kit, capsys):
    code, text = run(capsys, kit, "meter")
    assert code == 0 and "spent by askdata" in text and "remaining" in text
    code, text = run(capsys, kit, "meter", "--set-external", "2.50")
    assert code == 0 and "external (typed in): 2.5" in text
    assert run(capsys, kit, "meter", "--set-external", "lots")[0] == 4


def test_startup_errors_exit_4(kit, capsys, tmp_path):
    assert cli.main(["audit", "list"]) == 4  # no config given
    bad = tmp_path / "bad.yaml"
    bad.write_text("as_of: x\nsurprise: 1\n")
    assert cli.main(["--config", str(bad), "audit", "list"]) == 4
    assert cli.main(["--config", str(tmp_path / "missing.yaml"), "meter"]) == 4


def test_a_usage_error_is_exit_1(kit, capsys):
    assert cli.main(["--config", write_config(kit), "audit", "nope"]) == 1
