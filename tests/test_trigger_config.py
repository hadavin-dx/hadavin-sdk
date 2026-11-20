"""Contract test of the trigger config block (`Config.triggers`), its registry cross-check and its start-up wiring.

Written by a different agent than the builder, against the code as built on cloud/core-b. On a branch where the block
does not exist yet the whole module is skipped. Fields the request asked for and that are not built yet (host, port,
poll_s, allow_non_loopback, a name-limited reader on App) are tested only when present; their tests skip by name.

A test marked xfail(strict) is a FINDING: the code is weaker than the review of it says it should be. The assertion
is the wanted behaviour; when the code is fixed the mark must be removed (strict makes the fixed code fail the mark).
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest
import yaml

from hadavin_sdk import config as config_mod
from hadavin_sdk import defaults
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.app import build
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.registry import load_registry
from tests.conftest import make_cfg, qualify

if not hasattr(config_mod, "TriggerSettings"):
    pytest.skip("core-b trigger config not on this branch yet", allow_module_level=True)

FIELDS = config_mod.TriggerSettings.model_fields
AGENT = "test-agent"  # the fixture's agent and its service principal
SERVICE = "svc:test-agent"
PERSON = "user:a"  # a fixture principal of kind person
ACTION_KEY_NAME = "fixture-token"  # the secret name of the fixture's http actions
# Fake values, built from parts so that no key-shaped literal stands in the file.
TOKEN = "tok" + "-trigger"
VALUE_ONE = "one-" + "x" * 36
VALUE_TWO = "two-" + "y" * 36
PASTED = "pasted" + "-" + "Zq7" * 12  # stands for a real secret typed where a NAME belongs


@pytest.fixture
def cfg_dir(tmp_path: Path) -> Path:
    return make_cfg(tmp_path)


def _sender(*names: str, **over) -> dict:
    return {
        "secret_names": list(names or ("sender-one-key",)),
        "agent_id": AGENT,
        "principal_id": SERVICE,
        **over,
    }


def _block(senders: dict | None = None, **over) -> dict:
    """A valid block in the shape core-b built: `senders` is a mapping sender id -> sender."""
    return {"tenant": "tenant-a", "senders": senders or {"s1": _sender()}, **over}


def _write(cfg_dir: Path, block: dict | None) -> None:
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data.pop("triggers", None)
    if block is not None:
        data["triggers"] = block
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _load(cfg_dir: Path, block: dict | None):
    _write(cfg_dir, block)
    return load_config(cfg_dir)


def _refused(cfg_dir: Path, block: dict) -> str:
    with pytest.raises(ConfigError) as info:
        _load(cfg_dir, block)
    return str(info.value)


def _need(field: str) -> None:
    if field not in FIELDS:
        pytest.skip(f"field not built on this branch: triggers.{field}")


# --- the block itself ----------------------------------------------------------------------------------------------


def test_no_block_loads_as_none(cfg_dir):
    """Case: no `triggers` key. The fixture config loads and `Config.triggers` is None."""
    assert _load(cfg_dir, None).triggers is None


def test_smallest_block_loads_with_the_defaults(cfg_dir):
    """Case: tenant and one sender only. Every number comes from `defaults`."""
    t = _load(cfg_dir, _block()).triggers
    assert t.tenant == "tenant-a"
    assert set(t.senders) == {"s1"}
    s = t.senders["s1"]
    assert (tuple(s.secret_names), s.agent_id, s.principal_id) == (
        ("sender-one-key",),
        AGENT,
        SERVICE,
    )
    assert t.max_body_bytes == defaults.TRIGGER_MAX_BODY_BYTES
    assert t.max_running == defaults.TRIGGER_MAX_RUNNING
    assert t.ack_wait_s == defaults.TRIGGER_ACK_WAIT_S


def test_the_ceilings_as_built():
    """Case: the upper bounds a config cannot pass (the request's 64 runs and 30 seconds)."""
    assert defaults.TRIGGER_MAX_RUNNING_CEILING == 64
    assert defaults.TRIGGER_ACK_WAIT_S_CEILING == 30.0
    assert defaults.TRIGGER_MAX_BODY_BYTES_CEILING >= defaults.TRIGGER_MAX_BODY_BYTES
    assert 1 <= defaults.TRIGGER_MAX_RUNNING <= defaults.TRIGGER_MAX_RUNNING_CEILING
    assert 0 < defaults.TRIGGER_ACK_WAIT_S <= defaults.TRIGGER_ACK_WAIT_S_CEILING


@pytest.mark.xfail(
    strict=True,
    reason="FINDING: the default body cap (TRIGGER_MAX_BODY_BYTES) equals MAX_DOCUMENT_BYTES, so a full-size "
    "document cannot fit once it is wrapped and escaped as JSON (review finding 7; request 001 asked for 2 x)",
)
def test_default_body_cap_leaves_room_for_a_full_size_document():
    """Case: the default request body cap is larger than the largest document."""
    assert defaults.TRIGGER_MAX_BODY_BYTES > defaults.MAX_DOCUMENT_BYTES


@pytest.mark.parametrize("where", ["settings", "sender"])
def test_unknown_extra_key_refused(cfg_dir, where):
    """Case: one key the model does not know, in the block or in a sender. Refused, the key is named."""
    block = _block({"s1": _sender(surprise=1)}) if where == "sender" else _block(surprise=1)
    text = _refused(cfg_dir, block)
    assert "surprise" in text
    assert "triggers" in text


@pytest.mark.parametrize("missing", ["secret_names", "agent_id", "principal_id"])
def test_sender_field_required(cfg_dir, missing):
    """Case: a sender without one of its three fields. Refused, the field is named."""
    sender = _sender()
    del sender[missing]
    assert f"triggers.senders.s1.{missing}" in _refused(cfg_dir, _block({"s1": sender}))


@pytest.mark.parametrize("senders", [{}, None, []])
def test_at_least_one_sender(cfg_dir, senders):
    """Case: no sender at all (empty mapping, null, empty list). Refused."""
    block = _block()
    block["senders"] = senders
    assert "triggers.senders" in _refused(cfg_dir, block)


def test_senders_key_required(cfg_dir):
    """Case: the block has a tenant and no `senders` key. Refused."""
    assert "triggers.senders" in _refused(cfg_dir, {"tenant": "tenant-a"})


# --- tenant ---------------------------------------------------------------------------------------------------------

GOOD_IDS = ["a", "0", "s1", "sender-one", "-", "a" * 40]
BAD_IDS = [
    ("upper case", "Sender"),
    ("too long", "a" * 41),
    ("empty", ""),
    ("blank", " "),
    ("trailing newline", "sender\n"),
    ("inner space", "sender one"),
    ("underscore", "sender_one"),
    ("dot", "sender.one"),
    ("colon", "svc:sender"),
]


def test_tenant_required(cfg_dir):
    """Case: no tenant. Refused, the field is named (there is no default tenant)."""
    block = _block()
    del block["tenant"]
    assert "triggers.tenant" in _refused(cfg_dir, block)


@pytest.mark.parametrize("tenant", GOOD_IDS)
def test_tenant_pattern_accepts(cfg_dir, tenant):
    """Case: a tenant of 1 to 40 characters from a-z, 0-9 and the hyphen. Loads unchanged."""
    assert _load(cfg_dir, _block(tenant=tenant)).triggers.tenant == tenant


@pytest.mark.parametrize(("case", "tenant"), BAD_IDS)
def test_tenant_pattern_refuses(cfg_dir, case, tenant):
    """Case: a tenant outside the pattern (see the id column). Refused, the field is named."""
    assert "triggers.tenant" in _refused(cfg_dir, _block(tenant=tenant)), case


# --- sender ids -----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("sender_id", GOOD_IDS)
def test_sender_id_pattern_accepts(cfg_dir, sender_id):
    """Case: a sender id of 1 to 40 characters from a-z, 0-9 and the hyphen. Loads under that id."""
    assert set(_load(cfg_dir, _block({sender_id: _sender()})).triggers.senders) == {sender_id}


@pytest.mark.parametrize(("case", "sender_id"), BAD_IDS)
def test_sender_id_pattern_refuses(cfg_dir, case, sender_id):
    """Case: a sender id outside the pattern (upper case, too long, empty, blank, trailing newline, other
    characters). Refused, and the text points into `triggers.senders`."""
    assert "triggers.senders" in _refused(cfg_dir, _block({sender_id: _sender()})), case


def test_duplicate_sender_id_refused(cfg_dir):
    """Case: the same sender id written twice. As built, senders are a mapping, so this is a duplicate YAML key:
    refused by the loader (the second entry never silently replaces the first)."""
    _write(cfg_dir, None)
    path = cfg_dir / "config.yaml"
    entry = (
        f"  same-id:\n    secret_names: [{{name}}]\n    agent_id: {AGENT}\n"
        f"    principal_id: '{SERVICE}'\n"
    )
    path.write_text(
        path.read_text(encoding="utf-8")
        + "triggers:\n  tenant: tenant-a\n  senders:\n"
        + entry.replace("{name}", "key-one")
        + entry.replace("{name}", "key-two"),
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="duplicate key 'same-id'"):
        load_config(cfg_dir)


# --- secret names ---------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("count", [1, 2])
def test_one_or_two_secret_names_load(cfg_dir, count):
    """Case: 1 name, and 2 names (two only while a secret is being changed). Loads, order kept."""
    names = [f"key-{i}" for i in range(count)]
    sender = _load(cfg_dir, _block({"s1": _sender(*names)})).triggers.senders["s1"]
    assert list(sender.secret_names) == names


@pytest.mark.parametrize("count", [0, 3])
def test_zero_or_three_secret_names_refused(cfg_dir, count):
    """Case: 0 names and 3 names. Refused, the sender and the field are named."""
    sender = _sender()
    sender["secret_names"] = [f"key-{i}" for i in range(count)]
    assert "triggers.senders.s1.secret_names" in _refused(cfg_dir, _block({"s1": sender}))


def test_secret_names_must_be_a_list(cfg_dir):
    """Case: one name written as plain text, not as a list. Refused (it must not be read letter by letter)."""
    sender = {**_sender(), "secret_names": "key-one"}
    assert "triggers.senders.s1.secret_names" in _refused(cfg_dir, _block({"s1": sender}))


def test_empty_secret_name_refused(cfg_dir):
    """Case: the empty text as a secret name. Refused, the sender and the field are named."""
    text = _refused(cfg_dir, _block({"s1": _sender("")}))
    assert "triggers.senders.s1.secret_names" in text


@pytest.mark.xfail(
    strict=True,
    reason="FINDING: a secret name is only checked for length 1, so a whitespace-only name or a name holding a "
    "line break loads (review finding 5: needs a charset pattern or stripping with a minimum length)",
)
@pytest.mark.parametrize("name", [" ", "\t", "   ", "key-one\n", "key\none", " key-one"], ids=repr)
def test_blank_or_newline_secret_name_refused(cfg_dir, name):
    """Case: a secret name that is blank, only whitespace, or holds a line break or a leading space. Must be
    refused, naming the sender and the field."""
    assert "triggers.senders.s1.secret_names" in _refused(cfg_dir, _block({"s1": _sender(name)}))


@pytest.mark.xfail(
    strict=True,
    reason="FINDING: agent_id and principal_id are only checked for length 1 in config; a whitespace-only value "
    "passes the config model and is refused only later, by the registry, as an unknown id (review finding 5)",
)
@pytest.mark.parametrize("field", ["agent_id", "principal_id"])
def test_blank_agent_or_principal_refused_by_the_model(field):
    """Case: a whitespace-only agent_id or principal_id given to the model itself. Must be a validation error."""
    with pytest.raises(ValueError, match=field):
        config_mod.TriggerSender(**_sender(**{field: " "}))


def test_duplicate_secret_name_inside_one_sender_refused(cfg_dir):
    """Case: one sender lists the same name twice. Refused; the text names the sender and not the name."""
    text = _refused(cfg_dir, _block({"s1": _sender(PASTED, PASTED)}))
    assert "triggers.senders.s1.secret_names: the same name twice" in text
    assert PASTED not in text


def test_secret_name_shared_by_two_senders_refused(cfg_dir):
    """Case: two senders list the same name (a sender is known by the secret that verified, so the name must
    belong to one sender). Refused; the text names both senders and not the name."""
    block = _block({"s1": _sender(PASTED), "s2": _sender("key-two", PASTED)})
    text = _refused(cfg_dir, block)
    assert "triggers.senders.s2.secret_names: a name is also used by sender s1" in text
    assert PASTED not in text


def test_every_secret_name_problem_is_reported_at_once(cfg_dir):
    """Case: a duplicate inside s1 and a name shared by s2 and s3. One refusal lists both."""
    block = _block(
        {
            "s1": _sender("key-one", "key-one"),
            "s2": _sender("key-two"),
            "s3": _sender("key-two"),
        }
    )
    text = _refused(cfg_dir, block)
    assert "triggers.senders.s1.secret_names: the same name twice" in text
    assert "triggers.senders.s3.secret_names: a name is also used by sender s2" in text


def test_distinct_names_across_senders_load(cfg_dir):
    """Case: two senders, three names, none shared. Loads."""
    block = _block({"s1": _sender("key-one", "key-two"), "s2": _sender("key-three")})
    assert set(_load(cfg_dir, block).triggers.senders) == {"s1", "s2"}


# --- bounds ---------------------------------------------------------------------------------------------------------

# field -> lowest allowed, highest allowed, one below, one above. host, port, poll_s: the request's bounds; their rows
# skip until the field is built.
BOUNDS = {
    "max_body_bytes": (
        1,
        getattr(defaults, "TRIGGER_MAX_BODY_BYTES_CEILING", 0),
        0,
        getattr(defaults, "TRIGGER_MAX_BODY_BYTES_CEILING", 0) + 1,
    ),
    "max_running": (1, 64, 0, 65),
    "ack_wait_s": (0.001, 30.0, 0, 30.001),
    "poll_s": (0.01, 1.0, 0.009, 1.001),
    "port": (1, 65535, 0, 65536),
}


@pytest.mark.parametrize("field", sorted(BOUNDS))
@pytest.mark.parametrize("end", ["lowest", "highest"])
def test_bound_allowed_value_loads(cfg_dir, field, end):
    """Case: the lowest and the highest allowed value of each bounded field. Loads with that value."""
    _need(field)
    value = BOUNDS[field][0 if end == "lowest" else 1]
    assert getattr(_load(cfg_dir, _block(**{field: value})).triggers, field) == value


@pytest.mark.parametrize("field", sorted(BOUNDS))
@pytest.mark.parametrize("side", ["below", "above"])
def test_bound_one_outside_refused(cfg_dir, field, side):
    """Case: one step below the lowest and one step above the highest allowed value. Refused, the field named."""
    _need(field)
    value = BOUNDS[field][2 if side == "below" else 3]
    assert f"triggers.{field}" in _refused(cfg_dir, _block(**{field: value}))


@pytest.mark.parametrize("field", sorted(BOUNDS))
def test_negative_refused(cfg_dir, field):
    """Case: a negative number in a bounded field. Refused, the field named."""
    _need(field)
    assert f"triggers.{field}" in _refused(cfg_dir, _block(**{field: -1}))


@pytest.mark.parametrize("value", [math.nan, math.inf])
def test_ack_wait_not_a_finite_number_refused(cfg_dir, value):
    """Case: ack_wait_s is not-a-number or infinite. Refused."""
    assert "triggers.ack_wait_s" in _refused(cfg_dir, _block(ack_wait_s=value))


@pytest.mark.parametrize("field", ["max_body_bytes", "max_running", "port"])
def test_fraction_for_a_whole_number_refused(cfg_dir, field):
    """Case: 1.5 where a whole number is expected. Refused, the field named."""
    _need(field)
    assert f"triggers.{field}" in _refused(cfg_dir, _block(**{field: 1.5}))


# --- booleans and numbers are not each other ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason="FINDING: `true` loads as the number 1 for max_running, max_body_bytes and ack_wait_s (the fields are "
    "not strict), so a mistyped switch becomes a limit of 1 (review finding 8)",
)
@pytest.mark.parametrize("field", ["max_running", "max_body_bytes", "ack_wait_s"])
def test_true_is_not_a_number(cfg_dir, field):
    """Case: `true` where a number is expected (max_running, max_body_bytes, ack_wait_s). Must be refused."""
    assert f"triggers.{field}" in _refused(cfg_dir, _block(**{field: True}))


@pytest.mark.parametrize("field", ["port", "poll_s"])
def test_true_is_not_a_number_for_later_fields(cfg_dir, field):
    """Case: `true` for port or poll_s. Must be refused. Skips until the field is built."""
    _need(field)
    assert f"triggers.{field}" in _refused(cfg_dir, _block(**{field: True}))


@pytest.mark.parametrize("value", [1, 0, 1.0, "true", "yes"], ids=repr)
def test_number_or_text_is_not_the_boolean_switch(cfg_dir, value):
    """Case: 1, 0, 1.0 or the text "true" / "yes" for allow_non_loopback. Must be refused: only the YAML boolean
    switches it. Skips until the field is built."""
    _need("allow_non_loopback")
    assert "triggers.allow_non_loopback" in _refused(cfg_dir, _block(allow_non_loopback=value))


def test_boolean_switch_defaults_to_off(cfg_dir):
    """Case: allow_non_loopback not written. It is exactly False. Skips until the field is built."""
    _need("allow_non_loopback")
    assert _load(cfg_dir, _block()).triggers.allow_non_loopback is False


# --- the registry cross-check ---------------------------------------------------------------------------------------


def _registry_refusal(cfg_dir: Path, block: dict) -> str:
    cfg = _load(cfg_dir, block)  # the config model itself accepts it
    with pytest.raises(ConfigError) as info:
        load_registry(cfg)
    return str(info.value)


def test_registry_accepts_an_existing_agent_and_service_principal(cfg_dir):
    """Case: the sender's agent is in agents.yaml and its principal is a service principal. The registry loads."""
    reg = load_registry(_load(cfg_dir, _block()))
    assert reg.principals[SERVICE].kind == "service"
    assert AGENT in reg.agents


def test_registry_refuses_a_sender_whose_agent_does_not_exist(cfg_dir):
    """Case: agent_id names no agent. Refused; sender and field named, the written id not shown."""
    text = _registry_refusal(cfg_dir, _block({"s1": _sender(agent_id="no-such-agent")}))
    assert "triggers.senders.s1.agent_id: no agent with this id in agents.yaml" in text
    assert "no-such-agent" not in text


def test_registry_refuses_a_sender_whose_principal_does_not_exist(cfg_dir):
    """Case: principal_id names no principal. Refused; sender and field named, the written id not shown."""
    text = _registry_refusal(cfg_dir, _block({"s1": _sender(principal_id="svc:no-such")}))
    assert "triggers.senders.s1.principal_id: no principal with this id in principals.yaml" in text
    assert "svc:no-such" not in text


def test_registry_refuses_a_sender_whose_principal_is_a_person(cfg_dir):
    """Case: principal_id names a principal of kind person. Refused: a sender runs as a service principal."""
    text = _registry_refusal(cfg_dir, _block({"s1": _sender(principal_id=PERSON)}))
    assert "triggers.senders.s1.principal_id: the principal must be of kind service" in text


def test_registry_reports_every_sender_problem_at_once(cfg_dir):
    """Case: s1 has an unknown agent, s2 a person as principal. One refusal names both; the good s3 is not named."""
    block = _block(
        {
            "s1": _sender("key-one", agent_id="no-such-agent"),
            "s2": _sender("key-two", principal_id=PERSON),
            "s3": _sender("key-three"),
        }
    )
    text = _registry_refusal(cfg_dir, block)
    assert "triggers.senders.s1.agent_id" in text
    assert "triggers.senders.s2.principal_id" in text
    assert "triggers.senders.s3" not in text


# --- config_hash ----------------------------------------------------------------------------------------------------


def _hashes(cfg_dir: Path, block: dict | None) -> dict[str, str]:
    reg = load_registry(_load(cfg_dir, block))
    return {agent_id: reg.config_hash(agent_id) for agent_id in sorted(reg.agents)}


def test_config_hash_of_every_agent_is_the_same_with_and_without_the_block(cfg_dir):
    """Case: no block, a block with one sender, the same block with a second sender, and changed numbers. The
    config_hash of every agent stays the same, so no agent loses its qualification."""
    without = _hashes(cfg_dir, None)
    assert without  # at least one agent is compared
    assert _hashes(cfg_dir, _block()) == without
    two = _block({"s1": _sender("key-one"), "s2": _sender("key-two", "key-three")})
    assert _hashes(cfg_dir, two) == without
    changed = _block(tenant="tenant-b", max_body_bytes=1, max_running=2, ack_wait_s=1.5)
    assert _hashes(cfg_dir, changed) == without


# --- start-up: the sender secrets are read once, and a missing one stops the start ------------------------------------


class _Recording(FakeSecretProvider):
    def __init__(self, values: dict[str, str]) -> None:
        super().__init__(values)
        self.read: list[str] = []

    def get(self, name: str) -> str:
        self.read.append(name)
        return super().get(name)


def _build(cfg_dir: Path, block: dict | None, values: dict[str, str]):
    _write(cfg_dir, block)
    qualify(load_registry(load_config(cfg_dir)))
    provider = _Recording({ACTION_KEY_NAME: TOKEN, **values})
    return build(cfg_dir, [AGENT], secrets=provider), provider


TWO_SENDERS = {"s1": _sender("key-one", "key-two"), "s2": _sender("key-three")}
TWO_SENDER_VALUES = {"key-one": VALUE_ONE, "key-two": VALUE_TWO, "key-three": VALUE_ONE + "3"}


def test_every_sender_secret_name_is_read_at_start(cfg_dir):
    """Case: two senders with three names, all present. The app starts and every one of the names was read."""
    app, provider = _build(cfg_dir, _block(TWO_SENDERS), TWO_SENDER_VALUES)
    assert app.config.triggers is not None
    assert set(TWO_SENDER_VALUES) <= set(provider.read)


def test_without_the_block_no_extra_secret_is_read(cfg_dir):
    """Case: no block. The app starts and reads nothing but the fixture's own secret."""
    app, provider = _build(cfg_dir, None, {})
    assert app.config.triggers is None
    assert set(provider.read) == {ACTION_KEY_NAME}


@pytest.mark.parametrize("missing", sorted(TWO_SENDER_VALUES))
def test_a_missing_sender_secret_fails_the_start(cfg_dir, missing):
    """Case: one of the three sender secrets cannot be read (first name, second name of a pair, other sender).
    The start fails with a ConfigError, and no secret value is in the text."""
    values = {k: v for k, v in TWO_SENDER_VALUES.items() if k != missing}
    with pytest.raises(ConfigError, match="cannot be read at start-up") as info:
        _build(cfg_dir, _block(TWO_SENDERS), values)
    text = str(info.value)
    assert not any(v in text for v in (*TWO_SENDER_VALUES.values(), TOKEN))


def test_a_sender_secret_name_that_is_an_action_secret_fails_the_start(cfg_dir):
    """Case: a sender lists the name of an action executor's secret. The start is refused."""
    with pytest.raises(ConfigError, match="secret names used by both") as info:
        _build(cfg_dir, _block({"s1": _sender(ACTION_KEY_NAME)}), {})
    assert TOKEN not in str(info.value)


@pytest.mark.xfail(
    strict=True,
    reason="FINDING: a sender secret name shared with an action secret is refused with the backend sentence "
    "('used by both a backend and an action executor ... give the backend its own secret'); the text does not "
    "name the sender or the triggers block (review finding 4, request 001 R1c)",
)
def test_shared_action_secret_refusal_names_the_sender(cfg_dir):
    """Case: as above. The refusal must point to `triggers.senders.s1`, not to a backend."""
    with pytest.raises(ConfigError) as info:
        _build(cfg_dir, _block({"s1": _sender(ACTION_KEY_NAME)}), {})
    assert "triggers.senders.s1" in str(info.value)


@pytest.mark.xfail(
    strict=True,
    reason="FINDING: text typed into secret_names is echoed by the start-up check (secret '<text>' cannot be read "
    "at start-up), although config.py says a mistyped config may hold the secret itself there and names only the "
    "sender (review finding 4)",
)
def test_start_refusal_does_not_echo_what_was_typed_as_a_secret_name(cfg_dir):
    """Case: a real secret pasted where a name belongs; the provider has no such name. The start must fail
    naming the sender, and the pasted text must not be in the message."""
    with pytest.raises(ConfigError) as info:
        _build(cfg_dir, _block({"s1": _sender(PASTED)}), {})
    assert PASTED not in str(info.value)


@pytest.mark.xfail(
    strict=True,
    reason="FINDING: a sender secret name may equal another platform secret name (here the restored-hash key; the "
    "same holds for a tool secret or a source token): the names are put into one set and never compared, so the "
    "signing secret held by the sender could be an internal credential (review finding 2)",
)
def test_a_sender_secret_name_that_is_another_platform_secret_fails_the_start(cfg_dir):
    """Case: a sender lists the name configured as evidence.restored_hash_key_secret_name. Must be refused,
    naming the sender."""
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["evidence"] = {"restored_hash_key_secret_name": "shared-key"}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ConfigError, match=r"triggers\.senders\.s1"):
        _build(cfg_dir, _block({"s1": _sender("shared-key")}), {"shared-key": VALUE_ONE})


# --- the reader the worker gets --------------------------------------------------------------------------------------


def _reader(app):
    """The reader for sender secrets as built: a name-limited callable when one exists (the request's
    `trigger_resolve`, the review's `trigger_secret`), else `App.secrets.get` (the whole provider)."""
    for name in ("trigger_resolve", "trigger_secret"):
        if callable(getattr(app, name, None)):
            return getattr(app, name)
    return app.secrets.get


def test_reader_hands_out_every_listed_sender_secret(cfg_dir):
    """Case: the worker asks for each name listed under the senders. It gets that secret's value."""
    app, _ = _build(cfg_dir, _block(TWO_SENDERS), TWO_SENDER_VALUES)
    read = _reader(app)
    for sender in app.config.triggers.senders.values():
        for name in sender.secret_names:
            assert read(name) == TWO_SENDER_VALUES[name]


@pytest.mark.xfail(
    strict=True,
    reason="FINDING: the only way to a sender secret is App.secrets, the WHOLE secret provider; there is no reader "
    "limited to the sender names (no App.trigger_resolve), so the worker can read every secret of the app "
    "(review finding 3, request 001 R1d)",
)
def test_reader_refuses_a_name_that_no_sender_lists(cfg_dir):
    """Case: the worker asks for a secret that exists and that no sender lists (an action's secret). The reader
    must refuse; a name that does not exist at all must be refused the same way."""
    app, _ = _build(cfg_dir, _block(TWO_SENDERS), TWO_SENDER_VALUES)
    read = _reader(app)
    with pytest.raises((PermissionError, ConfigError)):
        read(ACTION_KEY_NAME)
    with pytest.raises((PermissionError, ConfigError)):
        read("no-such-name")


def test_no_reader_without_the_block(cfg_dir):
    """Case: no block. `App.trigger_resolve` is None. Skips until the field is built."""
    app, _ = _build(cfg_dir, None, {})
    if not hasattr(app, "trigger_resolve"):
        pytest.skip("field not built on this branch: App.trigger_resolve")
    assert app.trigger_resolve is None


# --- refusal texts never show a value --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "block",
    [
        _block({"s1": _sender(PASTED, PASTED + "2", PASTED + "3")}),
        _block({"s1": _sender(PASTED, surprise=PASTED)}),
        _block({"s1": _sender(PASTED)}, max_running=PASTED),
        _block({"s1": _sender(PASTED)}, ack_wait_s=PASTED),
        _block({"s1": _sender(PASTED)}, tenant=PASTED),
        _block({"s1": {**_sender(), "secret_names": PASTED}}),
        _block({"s1": _sender(PASTED, agent_id=["x"])}),
    ],
    ids=[
        "three-names",
        "extra-key",
        "max_running",
        "ack_wait_s",
        "tenant",
        "not-a-list",
        "agent_id",
    ],
)
def test_validation_refusal_names_the_field_and_never_shows_a_written_value(cfg_dir, block):
    """Case: a secret-like text stands somewhere in a block that is refused for its shape (three names, an extra
    key, text for a number, a bad tenant, a name not in a list, a list for an id). The refusal names the triggers
    field and does not show the text."""
    text = _refused(cfg_dir, block)
    assert "triggers." in text
    assert PASTED not in text
