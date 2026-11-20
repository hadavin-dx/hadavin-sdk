"""The signed trigger endpoint's sender secret names (request 001, DRAFT 3): one canonical form for comparing
names, the load-time refusals, the start-up check against every other secret name, and the sender-only reader
`app.trigger_secret`.

Written by a different agent than the builders. Every name here is an invented label, every value a filler.
"""

from __future__ import annotations

import pytest
import yaml
from pydantic import ValidationError

from hadavin_sdk import app as app_mod
from hadavin_sdk.backends import platform_secrets
from hadavin_sdk.config import ConfigError, TriggerSender, load_config
from hadavin_sdk.registry import load_registry
from hadavin_sdk.secret_name import canonical_secret_name
from tests.conftest import qualify
from tests.k5_support import edit_config

FILLER = "v" * 40
EXECUTOR_SECRET = "fixture-token"  # noqa: S105 - the fixture config's one http contract reads this


# --- the canonical form --------------------------------------------------------------------------------------

CANON = [
    ("SLACK_TOKEN", "slack_token"),
    ("slack-token", "slack_token"),
    ("a-b", "a_b"),
    ("A_B", "a_b"),
    ("db.pass", "db_pass"),
    ("DB_PASS", "db_pass"),
    ("db:pass", "db_pass"),
    ("x", "x"),
    ("./x", "x"),
    ("a/../x", "a_x"),
    ("a//b", "a_b"),
    ("a--__..b", "a_b"),
    ("_lead", "lead"),
    ("trail_", "trail"),
    ("--both--", "both"),
    ("..x..", "x"),
    ("A1-b2", "a1_b2"),
    ("", ""),
    ("-", ""),
    ("___", ""),
    ("..", ""),
    (".-_:", ""),
]


@pytest.mark.parametrize(("name", "canon"), CANON)
def test_canonical_secret_name_table(name, canon):
    assert canonical_secret_name(name) == canon


@pytest.mark.parametrize(
    "group",
    [
        ("SLACK_TOKEN", "slack-token", "Slack.Token", "slack:token"),
        ("a-b", "A_B", "a.b", "a b"),
        ("db.pass", "DB_PASS", "db-pass"),
        ("x", "./x", "x/", "/x"),
    ],
)
def test_names_a_provider_could_fold_together_collide(group):
    assert len({canonical_secret_name(n) for n in group}) == 1


def test_platform_secrets_reexports_the_same_function():
    assert platform_secrets.canonical_secret_name is canonical_secret_name


def test_distinct_names_stay_distinct():
    assert canonical_secret_name("ab") != canonical_secret_name("a-b")
    assert canonical_secret_name("key1") != canonical_secret_name("key-1")


# --- the model and the load-time refusals -------------------------------------------------------------------


def sender(*names, agent="test-agent", principal="svc:test-agent"):
    return {"secret_names": list(names), "agent_id": agent, "principal_id": principal}


def triggers(senders):
    return {"tenant": "acme", "senders": senders}


def write_triggers(cfg_dir, senders, **more):
    edit_config(cfg_dir, lambda d: d.update(triggers=triggers(senders), **more))


@pytest.mark.parametrize(
    "bad",
    ["a/b", "/x", "./x", "..", "a..b", ".", "--", "-", "_", ".-:", "line\nbreak", "x\n", "", " "],
)
def test_the_model_refuses_a_bad_secret_name_without_showing_it(bad):
    with pytest.raises(ValidationError) as caught:
        TriggerSender(secret_names=(bad,), agent_id="test-agent", principal_id="svc:test-agent")
    text = str(caught.value)
    if any(c.isalnum() for c in bad):
        assert bad not in text


@pytest.mark.parametrize("good", ["a-b", "A_B", "db.pass", "slack:token", "k"])
def test_the_model_accepts_an_ordinary_secret_name(good):
    s = TriggerSender(secret_names=(good,), agent_id="test-agent", principal_id="svc:test-agent")
    assert s.secret_names == (good,)


def test_one_sender_listing_the_same_name_in_two_spellings_is_refused(cfg_dir):
    write_triggers(cfg_dir, {"alpha": sender("a-b", "A_B")})
    with pytest.raises(ConfigError) as caught:
        load_config(cfg_dir)
    text = str(caught.value)
    assert "triggers.senders.alpha.secret_names: the same name twice" in text
    assert "a-b" not in text and "A_B" not in text


def test_the_same_name_twice_in_the_very_same_spelling_is_refused(cfg_dir):
    write_triggers(cfg_dir, {"alpha": sender("k1", "k1")})
    with pytest.raises(ConfigError, match="the same name twice"):
        load_config(cfg_dir)


def test_two_senders_listing_aliases_are_refused(cfg_dir):
    write_triggers(
        cfg_dir,
        {"alpha": sender("Shared.Key"), "beta": sender("shared-key")},
    )
    with pytest.raises(ConfigError) as caught:
        load_config(cfg_dir)
    text = str(caught.value)
    assert "triggers.senders.beta.secret_names: a name is also used by sender alpha" in text
    assert "hared" not in text


def test_two_senders_with_different_names_load(cfg_dir):
    write_triggers(cfg_dir, {"alpha": sender("key-one", "key-two"), "beta": sender("key-three")})
    cfg = load_config(cfg_dir)
    assert set(cfg.triggers.senders) == {"alpha", "beta"}


@pytest.mark.parametrize("bad", ["a/b", "..", "a..b", ".", "--"])
def test_the_config_refuses_a_path_like_or_empty_name_at_load(cfg_dir, bad):
    write_triggers(cfg_dir, {"alpha": sender(bad)})
    with pytest.raises(ConfigError) as caught:
        load_config(cfg_dir)
    assert "alpha" in str(caught.value)


def test_the_config_refuses_a_name_with_a_line_break_at_load(cfg_dir):
    write_triggers(cfg_dir, {"alpha": sender("good\nname")})
    with pytest.raises(ConfigError) as caught:
        load_config(cfg_dir)
    assert "good" not in str(caught.value)


# --- check_senders: the start-up check against every other secret name -------------------------------------------

OTHER_KINDS = {
    "a backend secret name": "pg-dsn",
    "a tool secret name": "crm-api-key",
    "a source token name": "source-token",
    "the restored-hash key": "restored-key",
    "the reset_credential_ref": "reset-login",
}


class Counting:
    """A provider double that counts its calls (a refusal must come before any read)."""

    def __init__(self, values=None, fail=False):
        self.values, self.fail, self.calls = dict(values or {}), fail, []

    def get(self, name):
        self.calls.append(name)
        if self.fail:
            raise RuntimeError(f"provider cannot read {name}")
        return self.values[name]


def texts(exc):
    return [str(exc), str(exc.__cause__), str(exc.__context__), repr(exc)]


@pytest.mark.parametrize("what", sorted(OTHER_KINDS), ids=sorted(OTHER_KINDS))
@pytest.mark.parametrize(
    "spell", [lambda n: n, str.upper, lambda n: n.replace("-", "_"), lambda n: n.replace("-", ".")]
)
def test_check_senders_refuses_an_alias_of_another_secret_name(what, spell):
    other = OTHER_KINDS[what]
    alias = spell(other)
    provider = Counting({alias: FILLER, "innocent-name": FILLER})
    with pytest.raises(ConfigError) as caught:
        platform_secrets.check_senders(
            provider, {"alpha": ["innocent-name"], "beta": [alias]}, {other, "unrelated"}
        )
    message = str(caught.value)
    assert "triggers.senders.beta.secret_names" in message
    assert "alpha" not in message
    for text in texts(caught.value):
        assert other not in text and alias not in text
    assert provider.calls == []  # found before the first read


def test_check_senders_names_every_offending_sender_and_never_a_name():
    provider = Counting()
    with pytest.raises(ConfigError) as caught:
        platform_secrets.check_senders(
            provider,
            {"alpha": ["Backend-Key"], "beta": ["tool.key"], "gamma": ["fine-one"]},
            {"backend_key", "TOOL_KEY"},
        )
    message = str(caught.value)
    assert "triggers.senders.alpha.secret_names" in message
    assert "triggers.senders.beta.secret_names" in message
    assert "gamma" not in message
    for text in texts(caught.value):
        for name in ("Backend-Key", "backend_key", "tool.key", "TOOL_KEY", "fine-one"):
            assert name not in text


def test_check_senders_passes_distinct_names_and_reads_each_once():
    provider = Counting({"k-one": FILLER, "k-two": FILLER, "k-three": FILLER})
    platform_secrets.check_senders(
        provider, {"alpha": ["k-one", "k-two"], "beta": ["k-three"]}, {"other"}
    )
    assert sorted(provider.calls) == ["k-one", "k-three", "k-two"]


def test_a_provider_failure_at_start_names_the_sender_and_field_but_never_the_name_or_chain():
    secret_like = "ZQ-marker-name-9"  # noqa: S105 - a name label, not a value
    provider = Counting(fail=True)
    with pytest.raises(ConfigError) as caught:
        platform_secrets.check_senders(provider, {"alpha": [secret_like]}, set())
    assert "triggers.senders.alpha.secret_names" in str(caught.value)
    for text in texts(caught.value):
        assert secret_like not in text
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True


def test_build_refuses_a_sender_name_that_aliases_the_restored_hash_key(cfg_dir):
    write_triggers(
        cfg_dir,
        {"alpha": sender("Restored.Key")},
        evidence={"restored_hash_key_secret_name": "restored-key"},
    )
    provider = Counting({"restored-key": FILLER, EXECUTOR_SECRET: FILLER, "Restored.Key": FILLER})
    qualify(load_registry(load_config(cfg_dir)))
    with pytest.raises(ConfigError) as caught:
        app_mod.build(cfg_dir, ["test-agent"], secrets=provider)
    assert "triggers.senders.alpha.secret_names" in str(caught.value)
    for text in texts(caught.value):
        assert "restored-key" not in text and "Restored.Key" not in text
    assert provider.calls == []


def test_build_refuses_a_sender_name_that_aliases_an_action_executor_secret(cfg_dir):
    write_triggers(cfg_dir, {"alpha": sender("FIXTURE_TOKEN")})
    provider = Counting({EXECUTOR_SECRET: FILLER, "FIXTURE_TOKEN": FILLER})
    qualify(load_registry(load_config(cfg_dir)))
    with pytest.raises(ConfigError) as caught:
        app_mod.build(cfg_dir, ["test-agent"], secrets=provider)
    assert "triggers.senders.alpha.secret_names" in str(caught.value)
    for text in texts(caught.value):
        assert "FIXTURE" not in text and "fixture" not in text.replace("fixture-records", "")
    assert provider.calls == []


# --- app.trigger_secret --------------------------------------------------------------------------------------

LISTED = "Sender-Key-One"
SECOND = "sender-key-two"


@pytest.fixture
def built(cfg_dir):
    """An app whose provider is a counting double; `state["fail"]` makes it fail after start-up."""
    write_triggers(cfg_dir, {"alpha": sender(LISTED, SECOND)})
    qualify(load_registry(load_config(cfg_dir)))
    state = {"fail": False}
    values = {LISTED: FILLER, SECOND: FILLER + "2", EXECUTOR_SECRET: FILLER, "unlisted-name": "x"}
    provider = Counting(values)
    real_get = provider.get

    def get(name):
        if state["fail"]:
            provider.calls.append(name)
            raise KeyError(name)
        return real_get(name)

    provider.get = get
    app = app_mod.build(cfg_dir, ["test-agent"], secrets=provider)
    provider.calls.clear()
    return app, provider, state


def test_a_listed_name_returns_the_value(built):
    app, provider, _ = built
    assert app.trigger_secret(LISTED) == FILLER
    assert app.trigger_secret(SECOND) == FILLER + "2"
    assert provider.calls == [LISTED, SECOND]


@pytest.mark.parametrize(
    "name",
    ["unlisted-name", "sender-key-one", "SENDER_KEY_ONE", "", EXECUTOR_SECRET, "Sender-Key-One "],
)
def test_an_unlisted_name_is_refused_and_the_provider_is_not_asked(built, name):
    app, provider, _ = built
    with pytest.raises(PermissionError) as caught:
        app.trigger_secret(name)
    if name.strip():
        assert name not in str(caught.value)
    assert provider.calls == []


def test_without_a_triggers_block_every_name_is_refused(cfg_dir):
    qualify(load_registry(load_config(cfg_dir)))
    provider = Counting({EXECUTOR_SECRET: FILLER, "any-name": FILLER})
    app = app_mod.build(cfg_dir, ["test-agent"], secrets=provider)
    provider.calls.clear()
    with pytest.raises(PermissionError):
        app.trigger_secret("any-name")
    assert provider.calls == []


@pytest.mark.xfail(
    reason="fix round 2 (RuntimeError('sender secret unavailable')) is not in this tree: the reader "
    "lets the provider's own error through",
    strict=True,
)
def test_a_provider_failure_surfaces_as_a_nameless_runtime_error(built):
    app, _, state = built
    state["fail"] = True
    with pytest.raises(RuntimeError) as caught:
        app.trigger_secret(LISTED)
    assert str(caught.value) == "sender secret unavailable"
    for text in texts(caught.value):
        assert LISTED not in text and LISTED.lower() not in text.lower()
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True


def test_yaml_roundtrip_helper_keeps_the_fixture_config_loading(cfg_dir):
    """A guard for this file's own helper: the edited config still loads with the triggers block."""
    write_triggers(cfg_dir, {"alpha": sender(LISTED)})
    assert yaml.safe_load((cfg_dir / "config.yaml").read_text())["triggers"]["tenant"] == "acme"
    assert load_config(cfg_dir).triggers.senders["alpha"].secret_names == (LISTED,)
