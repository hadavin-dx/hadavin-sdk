import dataclasses
import re
from importlib import resources

import pytest

from jagrat import environments as env
from jagrat.models import ActionKind

REMOVED_KEYS = (
    "autonomy",
    "code_fix",
    "auto_merge",
    "github",
    "oidc",
    "aws_region",
    "aws_global_region",
    "discussion",
)


def test_shipped_policy_loads_and_unknown_environment_fails_closed():
    p = env.EnvironmentPolicies.load()
    assert p.known_environments == ("dev", "prod")
    dev = p.for_env("dev")
    assert dev.tier == "nonprod" and not dev.auto_remediate and dev.require_human_approval
    assert dev.permits(ActionKind.scale_up) and dev.permits(ActionKind.no_action)
    other = p.for_env("typo-env")
    assert other.name == "typo-env" and other.tier == "unknown"
    assert not other.permits(ActionKind.scale_up) and other.permits(ActionKind.no_action)
    assert not other.authorizes("role:oncall")


def test_removed_keys_are_gone_from_data_and_code():
    text = (resources.files("jagrat") / "data" / "environments.yaml").read_text(encoding="utf-8")
    keys = {m.group(1) for m in re.finditer(r"^\s*([a-z_]+):", text, re.MULTILINE)}
    assert not keys & set(REMOVED_KEYS)
    fields = {f.name for f in dataclasses.fields(env.EnvPolicy)}
    assert not fields & set(REMOVED_KEYS)
    for name in ("names", "region", "EnvNames", "_code_fix", "_autonomy", "_github", "_region"):
        assert not hasattr(env, name), name


@pytest.mark.parametrize(
    "doc,why",
    [
        ("version: 1\nenvironments:\n  dev:\n    tier: Prod\n", "tier"),
        ("version: 1\nenvironments:\n  dev:\n    auto_remediate: 'false'\n", "auto_remediate"),
        (
            "version: 1\nenvironments:\n  dev:\n    allow_actions: [not_an_action]\n",
            "allow_actions",
        ),
        ("version: 1\nenvironments: {}\n", "no environments"),
        ("version: 1\nenvironments:\n  Dev_X:\n    tier: nonprod\n", "name"),
        (
            "version: 1\nfault_environments: [prod]\nenvironments:\n  prod:\n    tier: prod\n",
            "fault",
        ),
        ("- not a mapping\n", "mapping"),
    ],
)
def test_bad_policies_are_refused(tmp_path, doc, why):
    f = tmp_path / "p.yaml"
    f.write_text(doc)
    with pytest.raises(env.EnvironmentPolicyError):
        env.EnvironmentPolicies.load(f)


def test_both_times_shows_utc_and_zone():
    from datetime import UTC, datetime

    out = env.both_times(datetime(2026, 1, 1, 0, 0, tzinfo=UTC), seconds=False)
    assert out.startswith("2026-01-01 00:00Z")
