"""K6 policy: every policy number lives in `measure.Policy` with a documented default, is read from baseline.yaml
(`policy:`, optional, strict) and nothing else; and no key-shaped, channel-id, host or environment literal sits in the
code. Fixtures build such strings from parts."""

from __future__ import annotations

import ast
import re
from datetime import timedelta
from pathlib import Path

import pytest

from hadavin_sdk import measure
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.measure import DEFAULT_POLICY, Policy
from hadavin_sdk.runtime import tick
from tests.test_k6_measure import ACTION, CEIL, NOW, World, day

SRC = Path(__file__).parent.parent / "src" / "hadavin_sdk"


def _baseline(tmp_path, policy: str = ""):
    (tmp_path / "baseline.yaml").write_text(
        "ceiling:\n  metric: m\n  counts: [harmful]\n  max: 0\n  window_days: 90\n  source: s\n"
        + policy,
        encoding="utf-8",
    )
    return tmp_path


# --- one place, documented defaults ---------------------------------------------------------------------------------------


def test_policy_defaults_are_the_documented_ones():
    p = Policy()
    assert (p.promotion_min_labelled, p.promotion_min_agree, p.promotion_max_wrong_harmful) == (
        30,
        0.70,
        1,
    )
    assert (p.promotion_harmful_window_days, p.promotion_min_coverage) == (28, 0.80)
    assert (p.wrong_limit, p.wrong_window_days, p.held_maps_max_days, p.late_start_s) == (
        3,
        14,
        400,
        600,
    )
    assert (p.report_local_offset_minutes, p.report_local_label) == (330, "IST")
    assert (p.enforce_every_s, p.purge_every_s, p.seen_actions_keep_s) == (300, 300, 600)
    assert p.thresholds() == measure.DEFAULTS


def test_policy_numbers_appear_nowhere_else_in_the_measurement():
    """The old module constants are gone: a policy number has one home."""
    text = (SRC / "measure.py").read_text(encoding="utf-8")
    for name in ("WRONG_WINDOW", "WRONG_LIMIT", "HELD_MAPS_MAX_DAYS", "LATE_START_S", "IST ="):
        assert name not in text, name


def test_no_baseline_or_no_policy_key_means_the_defaults(tmp_path):
    assert measure.load_policy(tmp_path) == DEFAULT_POLICY  # dev without a baseline
    assert measure.load_policy(_baseline(tmp_path)) == DEFAULT_POLICY


def test_a_policy_in_baseline_yaml_overrides_exactly_what_it_names(tmp_path):
    root = _baseline(
        tmp_path,
        "policy:\n  wrong_limit: 2\n  promotion_min_agree: 0.9\n  report_local_label: CET\n",
    )
    p = measure.load_policy(root)
    assert (p.wrong_limit, p.promotion_min_agree, p.report_local_label) == (2, 0.9, "CET")
    assert p.wrong_window_days == 14  # untouched keys keep their default
    assert (
        measure.load_policy(
            _baseline(tmp_path, "policy:\n  promotion_min_agree: 1\n")
        ).promotion_min_agree
        == 1.0
    )


@pytest.mark.parametrize(
    ("policy", "error"),
    [
        ("policy: yes\n", "must be a mapping"),
        ("policy:\n  wrong_limt: 2\n", "unknown keys: wrong_limt"),
        ("policy:\n  wrong_limit: '3'\n", "wrong_limit must be a int"),
        ("policy:\n  wrong_limit: true\n", "wrong_limit must be a int"),
        ("policy:\n  wrong_limit: 0\n", "wrong_limit must be between"),
        ("policy:\n  wrong_window_days: 0\n", "wrong_window_days must be between"),
        ("policy:\n  held_maps_max_days: 401\n", "held_maps_max_days must be between 1 and 400"),
        ("policy:\n  promotion_min_labelled: 0\n", "promotion_min_labelled must be between"),
        ("policy:\n  promotion_min_agree: 0\n", "promotion_min_agree must be above 0"),
        ("policy:\n  promotion_min_coverage: 1.5\n", "promotion_min_coverage must be above 0"),
        ("policy:\n  seen_actions_keep_s: 599\n", "seen_actions_keep_s must be between 600"),
        (
            "policy:\n  report_local_offset_minutes: 900\n",
            "report_local_offset_minutes must be between",
        ),
        ("policy:\n  report_local_label: 'a b c'\n", "report_local_label"),
        ("policy:\n  enforce_every_s: -1\n", "enforce_every_s must be between"),
    ],
)
def test_a_bad_policy_refuses_to_start_naming_the_key(tmp_path, policy, error):
    with pytest.raises(ConfigError, match=re.escape(error)):
        measure.load_policy(_baseline(tmp_path, policy))


# --- the numbers really come from the policy -------------------------------------------------------------------------------


def _world(tmp_path, **policy):
    from dataclasses import replace

    w = World(tmp_path)
    w.measure.policy = replace(DEFAULT_POLICY, **policy)
    w.measure.th = w.measure.policy.thresholds()
    return w


def test_the_wrong_rule_follows_the_policy(tmp_path):
    w = _world(tmp_path, wrong_limit=2, wrong_window_days=3)
    a, b = w.run(), w.run()
    w.label(a, "wrong", when=day(5))  # outside a 3-day window by the time of the second
    assert not w.label(b, "wrong", when=day(1)).demoted
    w2 = _world(tmp_path / "two", wrong_limit=2)
    c, d = w2.run(), w2.run()
    w2.label(c, "wrong", when=day(2))
    assert w2.label(d, "wrong", when=day(1)).demoted  # two are enough when the policy says two


def test_the_promotion_numbers_follow_the_policy(tmp_path):
    w = _world(
        tmp_path, promotion_min_labelled=2, promotion_min_agree=0.5, promotion_min_coverage=0.5
    )
    w.labelled("agree", 2, when=day(9), action="create_draft_record")
    res = w.measure.promote_check("test-agent", "create_draft_record")
    assert not any("labelled" in p for p in res.problems)  # 2 labelled is enough here
    assert w.measure.th.min_labelled == 2


def test_the_report_uses_the_policys_local_time_and_late_start_and_retention(tmp_path):
    from hadavin_sdk.models import TickState

    w = _world(
        tmp_path,
        report_local_offset_minutes=60,
        report_local_label="CET",
        late_start_s=120,
        held_maps_max_days=30,
    )
    w.store.save_tick_state(TickState(step="backlog", last_run_at=NOW, detail={"late_starts": 4}))
    rid = w.run(created=day(7))
    w.label(rid, "wrong", when=day(7))
    text = w.measure.render_report(NOW.date() - timedelta(days=7), NOW)
    assert "13:00 CET" in text and " IST" not in text  # 12:00 UTC + 60 minutes
    assert "started later than 2 minutes: 4" in text
    assert "(30 days from the run)" in text


def test_the_nonce_keep_time_follows_the_policy(tmp_path):
    w = _world(tmp_path, seen_actions_keep_s=1200)
    w.store.claim_action("old", NOW - timedelta(minutes=15))
    w.store.claim_action("older", NOW - timedelta(minutes=25))
    assert w.measure.purge_seen(NOW) == 1  # only the one past 20 minutes


def test_tick_cadence_comes_from_the_policy(tmp_path):
    w = _world(tmp_path, enforce_every_s=77, purge_every_s=0)
    app = type("A", (), {"measure": w.measure})()
    steps = {s.name: s for s in tick.STEPS}
    assert steps["measure_levels"].every_s(app) == 77
    assert steps["purge_seen_actions"].every_s(app) == 0
    assert steps["weekly_report"].every_s == 0  # a retry every tick, by design
    bare = type("A", (), {})()
    assert steps["measure_levels"].every_s(bare) == DEFAULT_POLICY.enforce_every_s


def test_app_build_reads_the_policy_from_baseline_yaml(tmp_path):
    from hadavin_sdk import app as app_mod
    from hadavin_sdk.approvals.channel import FakeChannel
    from hadavin_sdk.config import load_config
    from hadavin_sdk.registry import load_registry
    from tests.conftest import qualify
    from tests.test_k3_pilot import SECRETS, ScriptedLLM, dev_cfg

    cfg = dev_cfg(tmp_path, {ACTION: "shadow"})
    _baseline(cfg, "policy:\n  wrong_limit: 5\n")
    qualify(load_registry(load_config(cfg)))
    app = app_mod.build(
        cfg,
        ["test-agent"],
        channel=FakeChannel("s"),
        llm=ScriptedLLM(),
        secrets=SECRETS,
    )
    assert app.measure.policy.wrong_limit == 5 and CEIL.max == 0
    bad = dev_cfg(tmp_path / "bad", {ACTION: "shadow"})
    _baseline(bad, "policy:\n  nonsense: 1\n")
    with pytest.raises(ConfigError, match="unknown keys"):
        app_mod.build(
            bad,
            ["test-agent"],
            channel=FakeChannel("s"),
            llm=ScriptedLLM(),
            secrets=SECRETS,
        )


# --- no key, id, host or environment literal in the code ---------------------------------------------------------------------

_FAKE_OK = "AKIA" + "IOSFODNN7EXAMPLE"  # the one literal AWS documents as an example
_KEY_SHAPES = {
    "AWS access key id": re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA)[0-9A-Z]{16}\b"),
    "Slack token": re.compile(r"\bxox[abprs]-[0-9A-Za-z-]{10,}"),
    "Slack app token": re.compile(r"\bxapp-[0-9A-Za-z-]{10,}"),
    "API secret key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY"),
    "arn with an account": re.compile(r"arn:aws[a-z-]*:[a-z0-9-]*:[a-z0-9-]*:\d{12}:"),
}
# A Slack user, channel, team or DM id as a whole string: upper case and digits, at least one digit (a plain
# upper-case word such as an enum value is not an id).
_SLACK_ID = re.compile(r"^(?=[A-Z0-9]*\d)[UWCGDT][A-Z0-9]{8,12}$")
_ID_LIKE_OK: set[str] = set()  # none today: an id-shaped constant belongs in config


def _string_constants(path: Path):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.lineno, node.value


def test_no_key_shaped_or_channel_id_literal_anywhere_in_the_code():
    found = []
    for path in sorted(SRC.rglob("*.py")):
        for line, value in _string_constants(path):
            for what, rx in _KEY_SHAPES.items():
                if rx.search(value.replace(_FAKE_OK, "")):
                    found.append(f"{path.relative_to(SRC)}:{line}: {what}")
            if _SLACK_ID.match(value) and value not in _ID_LIKE_OK:
                found.append(
                    f"{path.relative_to(SRC)}:{line}: channel/user id shaped constant {value!r}"
                )
    assert found == []


def test_the_scan_catches_what_it_is_for(tmp_path):
    """Plant one of each shape (built from parts) in a throwaway module and see every one found."""
    planted = {
        "AWS access key id": "AKIA" + "ABCDEFGHIJKLMNOP",
        "Slack token": "xox" + "b-1234567890-abcdefghij",
        "API secret key": "sk" + "-" + "a" * 24,
        "GitHub token": "gh" + "p_" + "a" * 36,
        "private key": "-----BEGIN " + "RSA PRIVATE KEY-----",
    }
    for what, value in planted.items():
        assert _KEY_SHAPES[what].search(value), what
    assert _SLACK_ID.match("U" + "0ABCDEFGH") and _SLACK_ID.match("C" + "01234ABCDE")
    assert not _SLACK_ID.match("CHECKPOINT_LABEL_X")  # an ordinary constant is not an id


K6_MODULES = [
    "measure.py",
    "runtime/tick.py",
    "approvals/receiver.py",
    "approvals/hmac_v0.py",
    "approvals/cards.py",
]


def test_k6_code_names_no_environment_host_or_secret_source():
    """Environment, hosts and secrets come from config and the secrets kind, never from literals or the process
    environment inside the measurement."""
    env_names = {"dev", "pilot", "prod", "staging", "production", "development"}
    hosts = re.compile(r"https?://|\b[a-z0-9-]+\.(?:com|io|net|org|dev)\b")
    found = []
    for rel in K6_MODULES:
        path = SRC / rel
        text = path.read_text(encoding="utf-8")
        assert "os.environ" not in text and "getenv" not in text, rel
        for line, value in _string_constants(path):
            if value.strip().lower() in env_names:
                found.append(f"{rel}:{line}: environment name {value!r}")
            if hosts.search(value) and "docs.slack" not in value:
                found.append(f"{rel}:{line}: host {value!r}")
    assert found == []
    cli = (SRC / "cli.py").read_text(encoding="utf-8")
    body = cli[cli.index("def measure_cmd") : cli.index("def _tick")]
    assert not any(
        v.strip().lower() in env_names
        for _, v in [(0, c) for c in re.findall(r'"([^"\n]*)"', body)]
    )
