"""segregation rule: demo/client data, learning and caches stay segregated. Nothing learned from demo A may change demo B's outputs. DEV data only."""

import json
import re
from datetime import date
from pathlib import Path

import pytest
import reference as ref

from refunds import config, namespace
from refunds.namespace import CrossClientAccess, Namespace

ROOT = Path(__file__).resolve().parents[1]
OUTSIDE = re.compile(
    "(open|read_text|read_bytes|Path)"
    + chr(92)
    + "("
    + chr(92)
    + "s*["
    + chr(34)
    + chr(39)
    + "]("
    + chr(92)
    + ".."
    + chr(92)
    + "./|/|[A-Za-z]:"
    + chr(92)
    + chr(92)
    + ")"
)
OTHER_DEMOS = ("apexc", "intake", "dealdesk", "ask-your-data", "askdata", "ask_your_data", "portfolio" + "-2026")


def test_config_keys_and_every_kind_carry_the_client_id():
    assert namespace.CLIENT_ID == "refunds" and namespace.config_key("model") == "refunds.model"
    ns = Namespace("refunds")
    for kind in namespace.KINDS:
        assert ns.key(kind, "x").startswith("refunds/" + kind + "/")
    with pytest.raises(ValueError):
        ns.key("not-a-kind", "x")
    for bad in ("", "a/b", "a.b"):
        with pytest.raises(ValueError):
            Namespace(bad)


def test_nothing_in_the_demo_reads_another_demos_data_eval_or_memory_paths():
    offenders = []
    for path in ROOT.rglob("*"):
        if (
            not path.is_file()
            or path.suffix not in (".py", ".json", ".jsonl", ".toml")
            or any(p.startswith(".venv") or p in ("__pycache__", ".ruff_cache", "mutation", ".pytest_cache") for p in path.parts)
        ):
            continue
        if path.name in ("test_segregation.py", "mutation_check.py", "test.jsonl", "world_test.json"):
            continue  # the test-split files are scanned by tests_oneshot, never by the default run
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in OTHER_DEMOS:
            if token in text:
                offenders.append((str(path.relative_to(ROOT)), token))
        if path.suffix == ".py" and OUTSIDE.search(text):
            offenders.append((str(path.relative_to(ROOT)), "path outside the demo"))
    assert not offenders, offenders


def _run_demo(half):
    """A 'demo run' for one namespace: the reference evaluates every steered and correct call of one half of the DEV cases, writing prompts, outputs,
    logs, cache and index entries into the demo's OWN namespace. Two disjoint halves of the dev split stand in for two demos."""
    world, cases = ref.load("dev")
    ns = Namespace(f"demo-{half}")
    for c in cases[half::2][:25]:
        calls = list(c.get("steered", [])) + (
            [ref.correct_call(c)] if c["expected"]["action"] in ("refund", "cancel", "reship", "goodwill") else []
        )
        for n, call in enumerate(calls):
            out = ref.evaluate(c, world, call)
            ns.put("prompts", f"{c['case_id']}-{n}", json.dumps(call, sort_keys=True))
            ns.put("logs", f"{c['case_id']}-{n}", json.dumps({"case": c["case_id"], "result": out}))
            ns.put("cache", f"{c['case_id']}-{n}", out)
            ns.put("index", c["case_id"], c["ticket"]["subject"])
    return ns


def test_a_canary_planted_in_demo_a_never_reaches_demo_b_and_a_is_byte_identical_without_b():
    canary = "CANARY-SEGREGATION-7f3a9c1e"
    a = Namespace("demo-0")
    for kind in ("store", "feedback", "memory", "eval", "fewshot", "golden"):
        a.put(kind, "planted", canary)
    a_alone = json.dumps(_run_demo(0).items(), sort_keys=True, default=str)  # BEFORE demo B has run
    b = _run_demo(1)
    assert canary not in json.dumps(b.items(), sort_keys=True, default=str), (
        "the canary of demo A appeared in demo B's prompts, outputs, logs, cache or index"
    )
    for kind in ("store", "memory", "eval", "feedback", "fewshot", "golden"):
        with pytest.raises(CrossClientAccess):
            b.get_raw(a.key(kind, "planted"))
    a_after_b = json.dumps(_run_demo(0).items(), sort_keys=True, default=str)
    assert a_alone == a_after_b and canary not in a_alone
    assert all(k.startswith("demo-0/") for k in _run_demo(0).items()) and all(k.startswith("demo-1/") for k in b.items())


def test_a_shared_cache_would_leak_which_is_why_namespaces_are_mandatory():
    shared = {}
    a, b = Namespace("demo-a", shared), Namespace("demo-b", shared)
    a.put("cache", "k", "CANARY-LEAK")
    assert b.get("cache", "k") is None and a.get("cache", "k") == "CANARY-LEAK" and "CANARY-LEAK" not in json.dumps(b.items())
    with pytest.raises(CrossClientAccess):
        b.get_raw(a.key("cache", "k"))


@pytest.mark.parametrize(
    "bad",
    [
        "refunds/../other/store/x",
        "refunds//store/x",
        "refunds/./store/x",
        "refunds/store",
        "other/store/x",
        "refunds\\..\\other",
        "refunds/store/a\\b",
        "/refunds/store/x",
        "",
    ],
)
def test_namespace_refuses_traversal_and_foreign_keys(bad):
    with pytest.raises(CrossClientAccess):
        Namespace("refunds").get_raw(bad)


def test_live_runs_need_the_provider_no_training_setting_with_a_real_recent_check_date():
    template = json.loads((ROOT / "demo_only" / "eval" / "lock.template.json").read_text(encoding="utf-8"))
    today = date(2026, 11, 1)
    assert (
        template["client_id"] == "refunds"
        and template["provider_no_training"] is None
        and "provider_no_training" in template["required_before_live_run"]
    )
    assert config.live_run_allowed(template, today) is False
    ok = {"setting": "organisation data use: not used for training", "training_use": False, "checked_on": "2026-10-20"}
    assert config.live_run_allowed({"provider_no_training": ok}, today) is True
    for bad in (
        {**ok, "setting": ""},
        {**ok, "checked_on": "yesterday"},
        {**ok, "checked_on": "9999-99-99"},
        {**ok, "checked_on": "2026-13-45"},
        {**ok, "checked_on": "2026-11-02"},
        {**ok, "checked_on": "2026-07-01"},
        {**ok, "training_use": True},
        {**ok, "training_use": "false"},
        {"setting": "training ENABLED", "checked_on": "2026-10-20"},
    ):
        assert config.live_run_allowed({"provider_no_training": bad}, today) is False, bad
    assert (
        config.live_run_allowed({"provider_no_training": {**ok, "checked_on": "2026-08-03"}}, today) is True
    )  # 90 days old is still accepted
    assert config.live_run_allowed({"provider_no_training": {**ok, "checked_on": "2026-08-02"}}, today) is False
    assert config.live_run_allowed({}, today) is False and config.live_run_allowed(None, today) is False


def test_live_run_gate_uses_the_real_clock_when_no_date_is_passed():
    from datetime import UTC, datetime, timedelta

    real = datetime.now(UTC).date()
    ok = {"setting": "provider console: data use for training = off", "training_use": False}
    for days_ago, allowed in ((0, True), (1, True), (89, True), (90, True), (91, False), (-1, False)):
        stamp = (real - timedelta(days=days_ago)).isoformat()
        assert config.live_run_allowed({"provider_no_training": {**ok, "checked_on": stamp}}) is allowed, days_ago
