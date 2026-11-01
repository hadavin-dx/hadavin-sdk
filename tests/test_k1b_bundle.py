"""K1b phase 3: bundle loader (allowlist, timestamps, manifest) and the snapshot tools."""

import json

import pytest

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.k1b.bundle import (
    BundleError,
    bad_citations,
    bundle_set_sha256,
    id_grammar_ok,
    load_bundle,
    load_bundles,
    parse_ts,
)
from hadavin_sdk.k1b.diagnosis import parse_diagnosis
from hadavin_sdk.k1b.tools import ALLOWED_TOOLS, MAX_POINTS, NO_DATA, TOOL_SPECS, Snapshot, render
from tests.k1b_support import ALERT_TIME, default_parts, make_bundle, write_manifest


def _snap(tmp_path, **override):
    return Snapshot(load_bundle(make_bundle(tmp_path, **override)))


# ---------------------------------------------------------------- timestamps


@pytest.mark.parametrize(
    "ts",
    [
        "2026-01-01T10:00:00Z",
        "2026-01-01T10:00:00.5Z",
        "2026-01-01T10:00:00.123456Z",
        "2024-02-29T00:00:00Z",
    ],
)
def test_ts_accepted(ts):
    assert parse_ts(ts) is not None


@pytest.mark.parametrize(
    "ts",
    [
        "2026-01-01T10:00:00",  # naive
        "2026-01-01T10:00:00+00:00",  # offset
        "2026-01-01T10:00:00+05:30",
        "1767261600",  # epoch
        1767261600,
        "2026-01-01",  # date only
        "2026-01-01T24:00:00Z",
        "2026-01-01T10:00:60Z",
        "2026-13-01T10:00:00Z",
        "2026-01-01T10:00:00.1234567Z",  # 7 digits
        "2026-01-01T10:00:00.Z",
        "2026-01-01t10:00:00Z",
        "2026-01-01T10:00:00z",
        "2026-01-01T10:00:00Z\n",
        " 2026-01-01T10:00:00Z",
        "NaN",
        None,
        "2023-02-29T00:00:00Z",
    ],
)
def test_ts_refused(ts):
    assert parse_ts(ts) is None


# ---------------------------------------------------------------- loading


def test_good_bundle_loads_with_ids(tmp_path):
    b = load_bundle(make_bundle(tmp_path))
    assert b.case_id == "case-001"
    assert b.ids == {
        "metrics/001.json#0",
        "metrics/001.json#1",
        "metrics/001.json#2",
        "logs/001.jsonl#0",
        "logs/001.jsonl#1",
        "logs/001.jsonl#2",
        "deploys.json#0",
        "k8s/001.json#spec",
        "k8s/001.json#events.0",
        "runbooks/001.md#0",
        "runbooks/001.md#1",
        "runbooks/001.md#2",
    }


def test_blank_log_lines_do_not_shift_ids(tmp_path):
    d = make_bundle(tmp_path)
    p = d / "logs" / "001.jsonl"
    lines = p.read_text(encoding="utf-8").splitlines()
    p.write_text(lines[0] + "\n\n   \n" + "\n".join(lines[1:]) + "\n", encoding="utf-8")
    write_manifest(d)
    assert "logs/001.jsonl#2" in load_bundle(d).ids


def test_bundle_set_hash_changes_with_content(tmp_path):
    make_bundle(tmp_path)
    make_bundle(tmp_path, "case-002")
    bs = load_bundles(tmp_path)
    assert [b.case_id for b in bs] == ["case-001", "case-002"]
    h1 = bundle_set_sha256(tmp_path, bs)
    (tmp_path / "case-002" / "deploys.json").write_text("[]", encoding="utf-8")
    write_manifest(tmp_path / "case-002")
    assert bundle_set_sha256(tmp_path, load_bundles(tmp_path)) != h1


def test_empty_or_missing_bundles_folder(tmp_path):
    with pytest.raises(ConfigError):
        load_bundles(tmp_path)
    with pytest.raises(ConfigError):
        load_bundles(tmp_path / "nope")


def _w(d, rel, text):
    (d / rel).write_text(text, encoding="utf-8")


def _edit_json(d, rel, fn):
    p = d / rel
    obj = json.loads(p.read_text(encoding="utf-8"))
    fn(obj)
    p.write_text(json.dumps(obj), encoding="utf-8")


def _log_row(d, ts="2026-01-01T10:00:01Z", **kw):
    row = {"ts": ts, "level": "info", "message": "m", "service": "api", **kw}
    with open(d / "logs" / "001.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def _incident(d, fn):
    _edit_json(d, "incident.json", fn)


# Each case edits a good bundle, re-signs the manifest (unless it tests the manifest), and must be refused.
REFUSALS = {
    "post-alert log (answer 1 s after alert)": lambda d: _log_row(
        d, message="root cause was the deploy"
    ),
    "log ts with offset": lambda d: _log_row(d, ts="2026-01-01T09:00:00+00:00"),
    "log extra key": lambda d: _log_row(d, resolved=True),
    "log non-string message": lambda d: _log_row(d, message=5),
    "alert unknown key resolved_at": lambda d: _incident(
        d, lambda o: o["alert"].update(resolved_at="2026-01-01T09:00:00Z")
    ),
    "alert unknown key closed_at": lambda d: _incident(
        d, lambda o: o["alert"].update(closed_at="2026-01-01T09:00:00Z")
    ),
    "alert label key status": lambda d: _incident(
        d, lambda o: o["alert"]["labels"].update(status="resolved")
    ),
    "alert label key rootcause": lambda d: _incident(
        d, lambda o: o["alert"]["labels"].update(RootCause="x")
    ),
    "alert label later timestamp": lambda d: _incident(
        d, lambda o: o["alert"]["labels"].update(note="2026-01-01T10:00:01Z")
    ),
    "alert label value too long": lambda d: _incident(
        d, lambda o: o["alert"]["labels"].update(note="x" * 201)
    ),
    "fired_by too long": lambda d: _incident(d, lambda o: o["alert"].update(fired_by="x" * 201)),
    "alert_time naive": lambda d: _incident(
        d, lambda o: o.update(alert_time="2026-01-01T10:00:00")
    ),
    "incident extra key": lambda d: _incident(d, lambda o: o.update(note="x")),
    "k8s spec closed_at": lambda d: _edit_json(
        d, "k8s/001.json", lambda o: o["spec"].update(closed_at="n")
    ),
    "k8s spec nested fix": lambda d: _edit_json(
        d, "k8s/001.json", lambda o: o["spec"].update(a={"hotfix": 1})
    ),
    "k8s spec later timestamp in list": lambda d: _edit_json(
        d, "k8s/001.json", lambda o: o["spec"].update(a=["2026-01-01T11:00:00Z"])
    ),
    "k8s as_of after alert": lambda d: _edit_json(
        d, "k8s/001.json", lambda o: o.update(as_of="2026-01-01T10:00:01Z")
    ),
    "k8s event after alert": lambda d: _edit_json(
        d, "k8s/001.json", lambda o: o["events"][0].update(ts="2026-01-01T10:01:00Z")
    ),
    "deploy as_of after alert": lambda d: _edit_json(
        d, "deploys.json", lambda o: o[0].update(as_of="2026-01-01T10:00:01Z")
    ),
    "deploy status key": lambda d: _edit_json(
        d, "deploys.json", lambda o: o[0].update(status="failed")
    ),
    "metric point after alert": lambda d: _edit_json(
        d,
        "metrics/001.json",
        lambda o: o["points"].append({"ts": "2026-01-01T10:00:01Z", "value": 1}),
    ),
    "metric bool value": lambda d: _edit_json(
        d, "metrics/001.json", lambda o: o["points"][0].update(value=True)
    ),
    "metric string value": lambda d: _edit_json(
        d, "metrics/001.json", lambda o: o["points"][0].update(value="3")
    ),
    "post-alert runbook": lambda d: _edit_json(
        d, "runbooks/001.meta.json", lambda o: o.update(as_of="2026-01-01T10:00:01Z")
    ),
    "runbook meta extra key": lambda d: _edit_json(
        d, "runbooks/001.meta.json", lambda o: o.update(note="x")
    ),
    "runbook without meta": lambda d: (d / "runbooks" / "001.meta.json").unlink(),
    "meta without runbook": lambda d: (d / "runbooks" / "001.md").unlink(),
    "name carries a service": lambda d: (d / "logs" / "001.jsonl").rename(
        d / "logs" / "payments.jsonl"
    ),
    "two digit file number": lambda d: (d / "logs" / "001.jsonl").rename(d / "logs" / "01.jsonl"),
    "stray tmp file": lambda d: _w(d, "deploys.json.tmp", "x"),
    "unlisted file": lambda d: _w(d, "notes.txt", "answer: db"),
    "file in unknown folder": lambda d: (d / "extra").mkdir() or _w(d, "extra/001.json", "{}"),
    "duplicate JSON key": lambda d: _w(
        d, "deploys.json", '[{"ts":"2026-01-01T08:00:00Z","ts":"2026-01-01T08:00:00Z"}]'
    ),
    "incident not json": lambda d: _w(d, "incident.json", "{nope"),
    "NaN in metric": lambda d: _w(
        d,
        "metrics/001.json",
        '{"query":"cpu","points":[{"ts":"2026-01-01T09:00:00Z","value":NaN}]}',
    ),
}


@pytest.mark.parametrize("name", sorted(REFUSALS))
def test_bundle_refusals(tmp_path, name):
    d = make_bundle(tmp_path)
    REFUSALS[name](d)
    (d / "manifest.json").unlink()
    write_manifest(d)
    with pytest.raises(BundleError):
        load_bundle(d)


def test_manifest_mismatch_unlisted_and_missing(tmp_path):
    d = make_bundle(tmp_path)
    (d / "deploys.json").write_text("[]", encoding="utf-8")  # changed after the manifest
    with pytest.raises(BundleError, match="manifest"):
        load_bundle(d)
    d = make_bundle(tmp_path, "case-002")
    (d / "deploys.json").unlink()  # listed but missing
    with pytest.raises(BundleError):
        load_bundle(d)
    d = make_bundle(tmp_path, "case-003")
    (d / "manifest.json").unlink()
    with pytest.raises(BundleError):
        load_bundle(d)


@pytest.mark.parametrize(
    "files",
    [
        {"../x": "0" * 64},
        {"/abs": "0" * 64},
        {"logs\\001.jsonl": "0" * 64},
        {"incident.json": "ZZ"},
        {"incident.json": 5},
    ],
)
def test_manifest_bad_keys_or_hashes(tmp_path, files):
    d = make_bundle(tmp_path)
    (d / "manifest.json").write_text(json.dumps({"files": files}), encoding="utf-8")
    with pytest.raises(BundleError):
        load_bundle(d)


def test_bad_case_name_and_manifest_shape(tmp_path):
    for name in ("case-1", "case-001x", "Case-001", "001"):
        d = make_bundle(tmp_path, "case-777")
        d.rename(tmp_path / name)
        with pytest.raises(BundleError):
            load_bundle(tmp_path / name)
        (tmp_path / name).rename(d)
        __import__("shutil").rmtree(d)
    d = make_bundle(tmp_path)
    (d / "manifest.json").write_text('{"files": [], "x": 1}', encoding="utf-8")
    with pytest.raises(BundleError):
        load_bundle(d)


def test_symlink_refused(tmp_path):
    d = make_bundle(tmp_path)
    try:
        (d / "logs" / "002.jsonl").symlink_to(d / "logs" / "001.jsonl")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not available")
    with pytest.raises(BundleError):
        load_bundle(d)


def test_bundle_without_optional_parts_is_valid(tmp_path):
    b = load_bundle(
        make_bundle(tmp_path, metrics=None, logs=None, deploys=None, k8s=None, runbooks=None)
    )
    assert b.ids == frozenset()


# ---------------------------------------------------------------- tools


def test_seven_tools_only():
    names = [t["name"] for t in TOOL_SPECS]
    assert sorted(names) == sorted(ALLOWED_TOOLS) and len(names) == 7
    assert "output_schema" not in json.dumps(TOOL_SPECS)


def test_list_data(tmp_path):
    out = _snap(tmp_path).call("list_data", {})
    assert out["metrics"] == [{"file": "metrics/001.json", "query": "cpu"}]
    assert out["logs"] == [{"file": "logs/001.jsonl", "services": ["api", "db"]}]
    assert out["k8s"] == [{"file": "k8s/001.json", "kind": "Deployment", "name": "api"}]
    assert out["runbooks"] == [{"file": "runbooks/001.md", "title": "Latency runbook"}]


def test_query_metrics_exact_match_window_and_clamp(tmp_path):
    s = _snap(tmp_path)
    all_pts = s.call("query_metrics", {"query": "cpu"})
    assert [r["id"] for r in all_pts] == [
        "metrics/001.json#0",
        "metrics/001.json#1",
        "metrics/001.json#2",
    ]
    clamped = s.call("query_metrics", {"query": "cpu", "end": "2099-01-01T00:00:00Z"})
    assert clamped == all_pts  # the end is clamped to the alert time, never beyond
    win = s.call(
        "query_metrics",
        {"query": "cpu", "start": "2026-01-01T09:15:00Z", "end": "2026-01-01T09:45:00Z"},
    )
    assert [r["id"] for r in win] == ["metrics/001.json#1"]


@pytest.mark.parametrize(
    "inputs",
    [
        {"query": "cp"},  # not an exact match
        {"query": "CPU"},
        {"query": "cpu", "start": "2026-01-01T10:00:01Z"},  # start after the alert
        {
            "query": "cpu",
            "start": "2026-01-01T09:45:00Z",
            "end": "2026-01-01T09:15:00Z",
        },  # inverted
        {"query": "cpu", "start": "yesterday"},
        {"query": "cpu", "end": "2026-01-01T10:00:00"},
        {"query": 5},
        {},
        {"query": "cpu", "extra": 1},
        {
            "query": "cpu",
            "start": "2025-01-01T00:00:00Z",
            "end": "2025-01-02T00:00:00Z",
        },  # empty window
    ],
)
def test_uniform_no_data(tmp_path, inputs):
    assert _snap(tmp_path).call("query_metrics", inputs) == NO_DATA


def test_unknown_tool_and_non_dict_input(tmp_path):
    s = _snap(tmp_path)
    assert s.call("delete_everything", {}) == NO_DATA
    assert s.call("query_logs", "x") == NO_DATA


def test_metric_points_capped(tmp_path):
    pts = [
        {"ts": f"2026-01-01T09:{m:02d}:{s:02d}Z", "value": s} for m in range(5) for s in range(60)
    ]
    s = _snap(tmp_path, metrics={"001": {"query": "q", "points": pts}})
    assert len(s.call("query_metrics", {"query": "q"})) == MAX_POINTS == 200


def test_query_logs_order_filters_limit(tmp_path):
    s = _snap(tmp_path)
    got = s.call("query_logs", {})
    assert [r["id"] for r in got] == [
        "logs/001.jsonl#1",
        "logs/001.jsonl#0",
        "logs/001.jsonl#2",
    ]  # by time
    assert [r["id"] for r in s.call("query_logs", {"service": "api"})] == [
        "logs/001.jsonl#0",
        "logs/001.jsonl#2",
    ]
    assert [r["id"] for r in s.call("query_logs", {"contains": "boom"})] == [
        "logs/001.jsonl#1",
        "logs/001.jsonl#2",
    ]
    assert s.call("query_logs", {"contains": "BOOM"}) == NO_DATA  # case sensitive
    assert len(s.call("query_logs", {"limit": 1})) == 1
    assert len(s.call("query_logs", {"limit": 500})) == 3  # capped at 50, only 3 exist
    for bad in (
        {"limit": 0},
        {"limit": "5"},
        {"limit": True},
        {"service": 3},
        {"start": "2026-01-02T00:00:00Z"},
    ):
        assert s.call("query_logs", bad) == NO_DATA


def test_deploys_k8s_runbook(tmp_path):
    s = _snap(tmp_path)
    assert [r["id"] for r in s.call("get_deploys", {})] == ["deploys.json#0"]
    assert s.call("get_deploys", {"service": "db"}) == NO_DATA
    assert [r["id"] for r in s.call("get_k8s", {})] == [
        "k8s/001.json#spec",
        "k8s/001.json#events.0",
    ]
    assert s.call("get_k8s", {"kind": "Pod"}) == NO_DATA
    rb = s.call("get_runbook", {})
    assert [r["id"] for r in rb] == ["runbooks/001.md#0", "runbooks/001.md#1", "runbooks/001.md#2"]
    assert s.call("get_runbook", {"name": "Latency runbook"}) == rb
    assert s.call("get_runbook", {"name": "runbooks/001.md"}) == rb
    assert s.call("get_runbook", {"name": "other"}) == NO_DATA


def test_render_cap_and_returned_ids():
    recs = [{"id": f"logs/001.jsonl#{i}", "message": "x" * 1000} for i in range(40)]
    text, ids = render(recs)
    assert len(text.encode()) <= 20_000
    assert ids == {r["id"] for r in json.loads(text)} and 0 < len(ids) < 40
    assert render([{"id": "a#0", "message": "x" * 30_000}]) == (json.dumps(NO_DATA), set())
    assert render(NO_DATA) == (json.dumps(NO_DATA), set())


# ---------------------------------------------------------------- evidence IDs


@pytest.mark.parametrize(
    "eid",
    [
        "logs/001.jsonl#01",
        "logs/001.jsonl#-1",
        "logs/001.jsonl#0 ",
        " logs/001.jsonl#0",
        "logs/001.jsonl#0\n",
        "logs/001.jsonl",
        "logs/../logs/001.jsonl#0",
        "../logs/001.jsonl#0",
        "logs\\001.jsonl#0",
        "/logs/001.jsonl#0",
        "k8s/001.json#events.01",
        "k8s/001.json#events",
        "k8s/001.json#spec.1",
        "deploys.json#a",
        "metrics/001.json#1.5",
        "other/001.json#0",
        5,
        None,
    ],
)
def test_id_attacks(eid):
    assert not id_grammar_ok(eid)


def test_good_ids_pass_grammar(tmp_path):
    b = load_bundle(make_bundle(tmp_path))
    assert all(id_grammar_ok(i) for i in b.ids)


def test_bad_citations_cover_all_three_checks_and_first_three_only(tmp_path):
    b = load_bundle(make_bundle(tmp_path))
    ok = {"service": "api", "fault_type": "oom", "evidence_ids": ["logs/001.jsonl#0"]}

    def diag(*ids_per_cause):
        causes = [{**ok, "evidence_ids": list(ids)} for ids in ids_per_cause]
        return parse_diagnosis({"causes": causes})

    returned = {"logs/001.jsonl#0", "logs/001.jsonl#1"}
    assert bad_citations(diag(["logs/001.jsonl#0"]), b, returned) == []
    assert bad_citations(diag(["logs/001.jsonl#9"]), b, returned | {"logs/001.jsonl#9"}) == [
        "logs/001.jsonl#9"
    ]  # (b)
    assert bad_citations(diag(["logs/001.jsonl#2"]), b, returned) == [
        "logs/001.jsonl#2"
    ]  # (c) never shown
    assert bad_citations(diag(["logs/001.jsonl#00"]), b, returned) == ["logs/001.jsonl#00"]  # (a)
    fourth_bad = diag(["logs/001.jsonl#0"], ["logs/001.jsonl#0"], ["logs/001.jsonl#0"], ["nope"])
    assert bad_citations(fourth_bad, b, returned) == []  # only the first 3 are checked


def test_alert_time_constant_is_a_valid_timestamp():
    assert parse_ts(ALERT_TIME) is not None and default_parts()


def test_surrogate_invalid_utf8_and_every_string_scanned(tmp_path):
    later = "2026-01-02T00:00:00Z"
    cases = {
        "surrogate": lambda d: _log_row(d, ts="2026-01-01T09:00:00Z", message="x" + chr(0xD83D)),
        "log_message": lambda d: _log_row(d, ts="2026-01-01T09:00:00Z", message=later),
        "deploy_version": lambda d: _edit_json(
            d, "deploys.json", lambda o: o[0].update(version=later)
        ),
        "metric_query": lambda d: _edit_json(
            d, "metrics/001.json", lambda o: o.update(query=later)
        ),
    }
    for name, fn in cases.items():
        d = make_bundle(tmp_path / name)
        fn(d)
        write_manifest(d)
        with pytest.raises(BundleError):
            load_bundle(d)
    for rel in ("logs/001.jsonl", "runbooks/001.md"):
        d = make_bundle(tmp_path / ("bad_" + rel.replace("/", "_")))
        (d / rel).write_bytes(b"\xff\xfe\xfa")
        write_manifest(d)
        with pytest.raises(BundleError):
            load_bundle(d)


def test_rolling_update_and_prefix_keys_are_allowed(tmp_path):
    spec = {"strategy": {"rollingUpdate": {"maxSurge": 1}}, "prefix": "a", "updateStrategy": "x"}
    snap = _snap(tmp_path, k8s={"001": {**default_parts()["k8s"]["001"], "spec": spec}})
    assert snap.call("get_k8s", {})[0]["spec"] == spec


def test_list_data_is_capped(tmp_path):
    many = {f"{i:03d}": {"query": "q" * 500 + str(i), "points": []} for i in range(1, 80)}
    text, ids = render(_snap(tmp_path, metrics=many).call("list_data", {}))
    assert len(text.encode()) <= 20_000 and ids == set() and json.loads(text)["metrics"]
