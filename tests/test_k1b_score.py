"""K1b phase 5: the class table row by row, layout refusals, report text, reference scorer on random fixtures."""

import json
import random

import pytest

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.k1b.report import CONFIDENT_WRONG, DISCLAIMER, render_score_report
from hadavin_sdk.k1b.score import audit_result, score
from tests.k1b_support import (
    cause,
    make_bundle,
    make_cause_list,
    record,
    write_answers,
    write_outputs,
)
from tests.reference_scorer import reference_counts

NS = {"causes": [], "not_sure": True}
OK_CAUSE = cause("api", "bad_deploy")
CAFE = "café"


def diag(*causes):
    return {"causes": list(causes), "not_sure": False}


class Fx:
    """One bundle set, one Cause List and one answers file; ``write`` puts outputs for them in place."""

    def __init__(self, tmp, cases):
        self.tmp = tmp
        self.bundles = tmp / "bundles"
        for cid in cases:
            make_bundle(self.bundles, cid)
        self.cause = make_cause_list(
            tmp / "cause", services=("api", "db", CAFE), faults=("bad_deploy", "oom")
        )
        self.cases = cases
        self.out = tmp / "out"

    def answers(self, spec):
        self.answers_path = write_answers(self.tmp / "answers.json", spec)
        return self

    def write(self, *runs, **kw):
        write_outputs(self.out, self.bundles, self.cause, [dict(r) for r in runs], **kw)
        return self

    def score(self):
        return score(self.out, self.answers_path, self.cause, self.bundles)


def one(tmp_path, rec, accepted=(("api", "bad_deploy"),), no_evidence=False):
    fx = Fx(tmp_path, ["case-001"]).answers({"case-001": (list(accepted), no_evidence)})
    return fx.write({"case-001": rec}).score().runs[0]


def rec1(**kw):
    return record("case-001", **kw)


NO_EV = {"no_evidence": True, "accepted": ()}
C_OOM = cause("db", "oom")
TABLE = {
    "error status": (rec1(status="error"), "miss", {}),
    "timeout status": (rec1(status="timeout"), "miss", {}),
    "capped status": (rec1(status="capped"), "miss", {}),
    "unreadable": (rec1(diagnosis=None), "miss", {}),
    "not sure": (rec1(diagnosis=NS), "not_sure", {}),
    "converted uncited": (rec1(diagnosis=NS, converted=True), "not_sure", {}),
    "right at rank 1": (rec1(diagnosis=diag(OK_CAUSE)), "hit", {}),
    "right at rank 3": (rec1(diagnosis=diag(C_OOM, C_OOM, OK_CAUSE)), "hit", {}),
    "right only at rank 4": (rec1(diagnosis=diag(C_OOM, C_OOM, C_OOM, OK_CAUSE)), "miss", {}),
    "wrong but on list": (rec1(diagnosis=diag(C_OOM)), "miss", {}),
    "hit at rank 1, off-list at rank 2": (
        rec1(diagnosis=diag(OK_CAUSE, cause("ghost", "oom"))),
        "miss",
        {},
    ),
    "off-list at rank 4 is not scored": (
        rec1(diagnosis=diag(OK_CAUSE, OK_CAUSE, OK_CAUSE, cause("ghost", "oom"))),
        "hit",
        {},
    ),
    "off-list fault type": (rec1(diagnosis=diag(cause("api", "weird"))), "miss", {}),
    "NFC and strip": (
        rec1(diagnosis=diag(cause("café ", " oom"))),
        "hit",
        {"accepted": ((CAFE, "oom"),)},
    ),
    "case differs": (rec1(diagnosis=diag(cause("API", "bad_deploy"))), "miss", {}),
    "no_evidence + not sure": (rec1(diagnosis=NS), "hne", NO_EV),
    "no_evidence + converted": (rec1(diagnosis=NS, converted=True), "miss", NO_EV),
    "no_evidence + answer": (rec1(diagnosis=diag(OK_CAUSE)), "miss", NO_EV),
    "no_evidence + unreadable": (rec1(diagnosis=None), "miss", NO_EV),
    "no_evidence + error": (rec1(status="error"), "miss", NO_EV),
}


@pytest.mark.parametrize("name", sorted(TABLE))
def test_class_table(tmp_path, name):
    rec, expect, kw = TABLE[name]
    assert one(tmp_path, rec, **kw).classes["case-001"] == expect


def test_counts_unreadable_error_timeout_capped_and_uncited(tmp_path):
    fx = Fx(tmp_path, [f"case-00{i}" for i in range(1, 7)])
    fx.answers({c: ([("api", "bad_deploy")], False) for c in fx.cases})
    recs = {
        "case-001": record("case-001", diag(OK_CAUSE)),
        "case-002": record("case-002", None),
        "case-003": record("case-003", None, status="error"),
        "case-004": record("case-004", None, status="timeout"),
        "case-005": record("case-005", None, status="capped"),
        "case-006": record("case-006", NS, converted=True),
    }
    s = fx.write(recs, hard_a=3).score().runs[0]
    assert (s.hits, s.misses, s.not_sure) == (1, 4, 1)
    assert (s.unreadable, s.error, s.timeout, s.capped, s.uncited, s.hard_check_a) == (
        1,
        1,
        1,
        1,
        1,
        3,
    )
    assert s.n == 6 and s.h == 1 and s.precision == pytest.approx(1 / 5)
    assert audit_result(s) == "H=1;Hne=0;M=4;S=1;ic=1;ha=3"


def test_wrong_cause_is_a_miss_never_not_sure(tmp_path):
    # behaviour behind the CONFIDENT_WRONG sentence, asserted on the scorer, not on the constant
    off_list = diag(cause("api", "not_in_the_list"))
    assert one(tmp_path, rec1(diagnosis=off_list)).classes["case-001"] == "miss"
    wrong = diag(cause("db", "bad_deploy"))
    assert one(tmp_path / "x", rec1(diagnosis=wrong)).classes["case-001"] == "miss"


def test_failed_citation_replay_path_is_not_sure_uncited(tmp_path):
    # what replay writes for an answer whose citations fail: Not sure, converted="uncited"
    s = one(tmp_path, rec1(diagnosis=NS, converted=True))
    assert s.classes["case-001"] == "not_sure" and s.uncited == 1 and s.bad_citations == 0


def test_bad_citation_in_a_hand_made_file_is_reported_not_reclassified(tmp_path):
    # replay never writes this (it converts first); the scorer only counts it
    bad = record("case-001", diag(cause("api", "bad_deploy", "logs/001.jsonl#0")), returned=[])
    s = one(tmp_path, bad)
    assert s.classes["case-001"] == "hit" and s.bad_citations == 1
    shown = record(
        "case-001",
        diag(cause("api", "bad_deploy", "logs/001.jsonl#0")),
        returned=["logs/001.jsonl#0"],
    )
    assert one(tmp_path / "x", shown).bad_citations == 0


def test_two_runs_worst_pass_k_and_bound(tmp_path):
    ids = ["case-001", "case-002", "case-003", "case-004"]
    fx = Fx(tmp_path, ids)
    fx.answers({c: ([("api", "bad_deploy")], False) for c in ids[:3]} | {"case-004": ([], True)})
    run1 = {c: record(c, diag(OK_CAUSE)) for c in ids[:3]} | {"case-004": record("case-004", NS)}
    run2 = run1 | {"case-002": record("case-002", NS), "case-003": record("case-003", diag(C_OOM))}
    res = fx.write(run1, run2).score()
    assert [(r.hits, r.hne, r.misses, r.not_sure) for r in res.runs] == [(3, 1, 0, 0), (1, 1, 1, 1)]
    assert res.pass_k == 2  # case-001 and the no-evidence case-004
    assert res.runs[0].n == 3 and res.runs[0].h == 3
    assert res.runs[0].bound == pytest.approx(0.05 ** (1 / 3), abs=1e-6)
    assert res.runs[1].precision == pytest.approx(0.5)


def test_undefined_values_are_none(tmp_path):
    s = one(tmp_path, rec1(diagnosis=NS), accepted=(), no_evidence=True)
    assert s.n == 0 and s.bound is None and s.precision is None


# ---------------------------------------------------------------- refusals


def _fx(tmp_path):
    fx = Fx(tmp_path, ["case-001", "case-002"])
    fx.answers({c: ([("api", "bad_deploy")], False) for c in fx.cases})
    return fx.write({c: record(c, diag(OK_CAUSE)) for c in fx.cases})


def _refuses(fx, match=None):
    with pytest.raises(ConfigError, match=match):
        fx.score()


def test_clean_fixture_scores(tmp_path):
    assert _fx(tmp_path).score().runs[0].hits == 2


def test_refusals_on_layout(tmp_path):
    fx = _fx(tmp_path)
    (fx.out / "run1" / "case-002.json").unlink()
    _refuses(fx, "differ")
    fx = _fx(tmp_path / "a")
    (fx.out / "run1" / "case-009.json").write_text("{}", encoding="utf-8")
    _refuses(fx, "differ")
    fx = _fx(tmp_path / "b")
    (fx.out / "run1" / "case-001.json.tmp").write_text("{}", encoding="utf-8")
    _refuses(fx, "differ")
    fx = _fx(tmp_path / "c")
    (fx.out / "FAILED.txt").write_text("x", encoding="utf-8")
    _refuses(fx, "did not finish")
    fx = _fx(tmp_path / "d")
    (fx.out / "notes.txt").write_text("x", encoding="utf-8")
    _refuses(fx, "exactly")
    fx = _fx(tmp_path / "e")
    (fx.out / "run1").rename(fx.out / "run2")
    _refuses(fx, "exactly")


def test_refusals_on_run_json_and_files(tmp_path):
    def edit_meta(fx, **change):
        p = fx.out / "run1" / "run.json"
        meta = json.loads(p.read_text(encoding="utf-8"))
        meta.update(change)
        p.write_text(json.dumps(meta), encoding="utf-8")

    for i, change in enumerate(
        [
            {"cause_services_sha256": "0" * 64},
            {"bundle_set_sha256": "0" * 64},
            {"k": 2},
            {"run_index": 3},
            {"schema": 2},
            {"counts": {}},
        ]
    ):
        fx = _fx(tmp_path / f"m{i}")
        edit_meta(fx, **change)
        _refuses(fx, "run.json")
    fx = _fx(tmp_path / "gone")
    (fx.out / "run1" / "run.json").unlink()
    _refuses(fx)
    fx = _fx(tmp_path / "bad")
    (fx.out / "run1" / "case-001.json").write_text("[1]", encoding="utf-8")
    _refuses(fx, "output file 1 has the wrong shape")
    fx = _fx(tmp_path / "id")
    rec = json.loads((fx.out / "run1" / "case-002.json").read_text(encoding="utf-8"))
    rec["case_id"] = "case-001"
    (fx.out / "run1" / "case-002.json").write_text(json.dumps(rec), encoding="utf-8")
    _refuses(fx, "output file 2")


def test_refusals_on_answers_and_cause_list_and_bundles(tmp_path):
    fx = _fx(tmp_path)
    fx.answers({"case-001": ([("api", "bad_deploy")], False)})  # covers 1 of 2 incidents
    _refuses(fx, "answers cover 1")
    fx = _fx(tmp_path / "off")
    fx.answers(
        {c: ([("ghost", "bad_deploy")], False) for c in fx.cases}
    )  # off-list accepted answer
    with pytest.raises(ConfigError) as exc:
        fx.score()
    assert "answer 1" in str(exc.value) and "ghost" not in str(
        exc.value
    )  # ordinals only, never values
    fx = _fx(tmp_path / "many")
    fx.answers({c: ([("api", "bad_deploy")] * 4, False) for c in fx.cases})
    _refuses(fx, "1 to 3")
    fx = _fx(tmp_path / "shape")
    fx.answers_path.write_text(
        '{"cases": {"case-001": {"accepted": 5, "no_evidence": false}}}', encoding="utf-8"
    )
    _refuses(fx, "answer 1 has the wrong shape")
    fx.answers_path.write_text("nope", encoding="utf-8")
    _refuses(fx, "answers file")
    fx = _fx(tmp_path / "cl")
    (fx.cause / "services.json").write_text(
        json.dumps(["api", "db"]), encoding="utf-8"
    )  # list changed
    _refuses(fx, "run.json")
    fx = _fx(tmp_path / "bd")
    (fx.bundles / "case-001" / "deploys.json").write_text("[]", encoding="utf-8")
    _refuses(fx)  # bundle no longer matches its manifest


def test_runs_that_disagree_are_refused(tmp_path):
    fx = Fx(tmp_path, ["case-001"]).answers({"case-001": ([("api", "bad_deploy")], False)})
    fx.write({"case-001": record("case-001", NS)}, {"case-001": record("case-001", NS)})
    p = fx.out / "run2" / "run.json"
    meta = json.loads(p.read_text(encoding="utf-8"))
    meta["model_id"] = "other-model"
    p.write_text(json.dumps(meta), encoding="utf-8")
    _refuses(fx, "disagree")


def test_outputs_changed_since_replay_is_a_warning(tmp_path):
    fx = _fx(tmp_path)
    assert fx.score().outputs_changed is False  # no outputs.sha256 yet: nothing to compare
    (fx.out / "outputs.sha256").write_text("0" * 64 + "\n", encoding="utf-8")
    res = fx.score()
    assert res.outputs_changed is True
    assert "outputs changed since replay" in render_score_report(res)


# ---------------------------------------------------------------- report text


def test_report_text(tmp_path):
    ids = ["case-001", "case-002", "case-003"]
    fx = Fx(tmp_path, ids)
    fx.answers(
        {
            "case-001": ([("api", "bad_deploy")], False),
            "case-002": ([("api", "bad_deploy")], False),
            "case-003": ([], True),
        }
    )
    fx.write(
        {
            "case-001": record("case-001", diag(OK_CAUSE)),
            "case-002": record("case-002", diag(C_OOM)),
            "case-003": record("case-003", NS),
        }
    )
    text = render_score_report(fx.score())
    lines = text.splitlines()
    assert lines[0].startswith("# ") and lines[2] == DISCLAIMER
    for heading in (
        "## Per run",
        "## Worst per row",
        "pass^k",
        "## Hit-rate range",
        "## Precision",
        "## Cost and settings",
    ):
        assert heading in text
    assert (
        "| Run | Hits | No-evidence Hits | Misses | Not sure | Unreadable/error/timeout/capped |"
        in text
    )
    assert "| 1 | 1 | 1 | 1 | 0 | 0/0/0/0 | 0 | 0 |" in text
    assert "includes no-evidence Hits" in text and CONFIDENT_WRONG in text
    assert (
        "Hit rate at least 2.5% (95%, one-sided), computed over 2 scored incidents excluding 1 no-evidence incidents"
        in text
    )
    assert "precision 50.0%" in text and "Not sure: 0" in text
    assert "SDK version: unreleased build" in text and "USD 0.5" in text
    assert "ghost" not in text and "accepted" not in text  # no answers in the report


def test_report_n_a_values(tmp_path):
    fx = Fx(tmp_path, ["case-001"]).answers({"case-001": ([], True)})
    text = render_score_report(fx.write({"case-001": record("case-001", NS)}).score())
    assert "n/a (no scored incidents)" in text and "precision n/a" in text


# ---------------------------------------------------------------- reference scorer


def _random_record(rng, cid):
    kind = rng.choice(
        [
            "error",
            "timeout",
            "capped",
            "unreadable",
            "unsure",
            "converted",
            "causes",
            "causes",
            "causes",
        ]
    )
    if kind in ("error", "timeout", "capped"):
        return record(cid, None, status=kind)
    if kind == "unreadable":
        return record(cid, None)
    if kind in ("unsure", "converted"):
        return record(cid, NS, converted=kind == "converted")
    pool = [
        ("api", "bad_deploy"),
        ("db", "oom"),
        ("api", "oom"),
        (CAFE, "oom"),
        ("ghost", "oom"),
        ("db", "weird"),
    ]
    return record(cid, diag(*[cause(*rng.choice(pool)) for _ in range(rng.randint(1, 4))]))


@pytest.mark.parametrize("seed", range(20))
def test_reference_scorer_agrees_on_random_fixtures(tmp_path, seed):
    rng = random.Random(seed)  # noqa: S311 - test data only
    ids = [f"case-{i:03d}" for i in range(1, rng.randint(4, 9))]
    fx = Fx(tmp_path, ids)
    on_list = [
        ("api", "bad_deploy"),
        ("db", "oom"),
        ("api", "oom"),
        (CAFE, "oom"),
        ("db", "bad_deploy"),
    ]
    spec = {}
    for cid in ids:
        ne = rng.random() < 0.25
        spec[cid] = ([] if ne else rng.sample(on_list, rng.randint(1, 3)), ne)
    fx.answers(spec)
    k = rng.randint(1, 3)
    fx.write(*[{cid: _random_record(rng, cid) for cid in ids} for _ in range(k)])
    got = [(r.hits, r.hne, r.misses, r.not_sure) for r in fx.score().runs]
    ref = [
        (t["hits"], t["hne"], t["misses"], t["not_sure"])
        for t in reference_counts(fx.out, fx.answers_path, fx.cause)
    ]
    assert got == ref


def test_missing_digest_file_is_noted_and_unreadable_one_counts_as_changed(tmp_path):
    fx = _fx(tmp_path)
    res = fx.score()
    assert res.outputs_changed is False and res.warnings
    assert "no replay digest" in render_score_report(res)
    (fx.out / "outputs.sha256").write_bytes(b"\xff\xfe")
    assert fx.score().outputs_changed is True


def test_tampered_run_json_values_are_refused_not_crashes(tmp_path):
    for i, change in enumerate(
        [
            {"model_id": ["x"]},
            {"model_id": "a\nb"},
            {"agent": None},
            {
                "counts": {
                    "ok": 2,
                    "unreadable": 0,
                    "error": 0,
                    "timeout": 0,
                    "capped": 0,
                    "uncited_conversions": 0,
                    "hard_check_a": True,
                }
            },
            {
                "counts": {
                    "ok": 2,
                    "unreadable": 0,
                    "error": 0,
                    "timeout": 0,
                    "capped": 0,
                    "uncited_conversions": 0,
                    "hard_check_a": -1,
                }
            },
            {
                "counts": {
                    "ok": 1,
                    "unreadable": 0,
                    "error": 0,
                    "timeout": 0,
                    "capped": 0,
                    "uncited_conversions": 0,
                    "hard_check_a": 0,
                }
            },
        ]
    ):
        fx = _fx(tmp_path / f"t{i}")
        p = fx.out / "run1" / "run.json"
        meta = json.loads(p.read_text(encoding="utf-8"))
        meta.update(change)
        p.write_text(json.dumps(meta), encoding="utf-8")
        _refuses(fx, "run1/run.json")


def test_error_status_with_an_answer_is_refused(tmp_path):
    fx = _fx(tmp_path)
    p = fx.out / "run1" / "case-001.json"
    rec = json.loads(p.read_text(encoding="utf-8"))
    rec["status"] = "error"
    p.write_text(json.dumps(rec), encoding="utf-8")
    _refuses(fx, "output file 1 has the wrong shape")


def test_report_notes_unfinished_replay_and_small_precision(tmp_path):
    fx = Fx(tmp_path, ["case-001", "case-002"]).answers(
        {c: ([("api", "bad_deploy")], False) for c in ("case-001", "case-002")}
    )
    fx.write(
        {
            "case-001": record("case-001", diag(OK_CAUSE)),
            "case-002": record("case-002", None, status="capped"),
        }
    )
    text = render_score_report(fx.score())
    assert "did not run every incident to completion (1 capped" in text
    assert "too few to judge" in text
