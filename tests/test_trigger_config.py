"""Contract test of the trigger config block (`Config.triggers`), its registry cross-check and its start-up wiring.

Written by a different agent than the builder, against the code as built on cloud/core-b. On a branch where the block
does not exist yet the whole module is skipped. Fields the request asked for and that are not built yet (host, port,
poll_s, allow_non_loopback, a limit on the number of senders) are tested only when present; their tests skip by name.

A test marked xfail(strict) is a FINDING: the code is weaker than the review of it says it should be. The assertion
is the wanted behaviour; when the code is fixed the mark must be removed (strict makes the fixed code fail the mark).

Second round (core-b's fix round 1, commit d0de90512): the findings F2, F3, F4a, F4b, F5, F7 and F8 of the first round
are fixed in the code, so their marks are gone and their assertions now guard the fixes. The reader the worker gets
is `App.trigger_secret`; `App.secrets` is gone. Open: FINDING T1 (the `env` secrets kind folds different names
onto one variable).
"""

from __future__ import annotations

import dataclasses
import inspect
import math
import traceback
import types
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


def test_default_body_cap_leaves_room_for_a_full_size_document():
    """Case: the default request body cap is larger than the largest document (first-round finding F7, fixed)."""
    assert defaults.TRIGGER_MAX_BODY_BYTES > defaults.MAX_DOCUMENT_BYTES


def test_default_body_cap_is_at_least_twice_the_document_cap_and_inside_its_own_ceiling(cfg_dir):
    """Case: the new default body cap. It is at least two times the document cap (what request 001 asked for), it
    is not above the ceiling a config may write, and a block that names no cap loads with exactly this number."""
    assert defaults.TRIGGER_MAX_BODY_BYTES >= 2 * defaults.MAX_DOCUMENT_BYTES
    assert defaults.TRIGGER_MAX_BODY_BYTES <= defaults.TRIGGER_MAX_BODY_BYTES_CEILING
    cap = _load(cfg_dir, _block()).triggers.max_body_bytes
    assert type(cap) is int
    assert cap == defaults.TRIGGER_MAX_BODY_BYTES


def test_default_max_running_and_ack_wait_as_built(cfg_dir):
    """Case: the defaults the worker gets when the block names no number: max_running is the whole number 4 and
    ack_wait_s is the float 5.0 (core-b's answer to request 001, DRAFT 2: both unchanged)."""
    t = _load(cfg_dir, _block()).triggers
    assert (type(t.max_running), t.max_running) == (int, 4)
    assert (type(t.ack_wait_s), t.ack_wait_s) == (float, 5.0)


def test_number_of_senders_is_limited(cfg_dir):
    """Case: one sender more than the largest allowed number of senders. Refused, and the largest number loads.
    Skips until a limit on the number of senders is built."""
    limit = next(
        (m.max_length for m in FIELDS["senders"].metadata if getattr(m, "max_length", None)), None
    )
    if limit is None:
        pytest.skip("field not built on this branch: a limit on the number of triggers.senders")
    senders = {f"s{i}": _sender(f"key-{i}") for i in range(limit + 1)}
    assert "triggers.senders" in _refused(cfg_dir, _block(senders))
    del senders["s0"]
    assert len(_load(cfg_dir, _block(senders)).triggers.senders) == limit


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
    ("tab inside", "sender\tone"),
    ("carriage return at the end", "sender\r"),
    ("non-breaking space", "sender\u00a0one"),
    ("zero-width space", "sender\u200bone"),
    ("NUL character", "sender\x00one"),
    ("digit of another script", "\u0661"),
    ("letter outside a-z", "stra\u00dfe"),
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


@pytest.mark.parametrize("name", [" ", "\t", "   ", "key-one\n", "key\none", " key-one"], ids=repr)
def test_blank_or_newline_secret_name_refused(cfg_dir, name):
    """Case: a secret name that is blank, only whitespace, or holds a line break or a leading space. Must be
    refused, naming the sender and the field (first-round finding F5, fixed by a character rule)."""
    assert "triggers.senders.s1.secret_names" in _refused(cfg_dir, _block({"s1": _sender(name)}))


# Neighbours of finding F5: characters that look like nothing, or like an allowed character, and are neither.
HOSTILE_NAMES = [
    ("tab inside", "key\tone"),
    ("trailing space", "key-one "),
    ("carriage return", "key\rone"),
    ("vertical tab", "key\x0bone"),
    ("non-breaking space alone", "\u00a0"),
    ("non-breaking space inside", "key\u00a0one"),
    ("zero-width space", "key\u200bone"),
    ("byte order mark in front", "\ufeffkey-one"),
    ("NUL character", "key\x00one"),
    ("delete character", "key-one\x7f"),
    ("full-width letter", "\uff4bey-one"),
    ("letter of another script that looks like e", "k\u0435y-one"),
    ("accented letter", "k\u00e9y-one"),
    ("inner space", "key one"),
    ("one character too long", "k" * 129),
]


@pytest.mark.parametrize(("case", "name"), HOSTILE_NAMES, ids=[c for c, _ in HOSTILE_NAMES])
def test_hostile_secret_name_refused_and_not_shown(cfg_dir, case, name):
    """Case: a secret name with a tab, a trailing space, a carriage return, a vertical tab, a non-breaking space,
    a zero-width space, a byte order mark, a NUL, a delete character, a full-width or other-script or accented
    letter, an inner space, or 129 characters. Refused; the sender and the field are named, the name is not
    shown."""
    text = _refused(cfg_dir, _block({"s1": _sender(name)}))
    assert "triggers.senders.s1.secret_names" in text, case
    assert name not in text, case


def test_hostile_secret_name_as_second_of_two_refused(cfg_dir):
    """Case: a good first name and a second name with a zero-width space (the pair used while a secret is being
    changed). Refused: the rule holds for every name of the list, not only the first."""
    text = _refused(cfg_dir, _block({"s1": _sender("key-one", "key\u200btwo")}))
    assert "triggers.senders.s1.secret_names" in text


@pytest.mark.parametrize(
    "name", ["k", "K" * 128, "Key_one.v2:eu.primary-1"], ids=["one", "128", "all"]
)
def test_secret_name_characters_allowed_as_built(cfg_dir, name):
    """Case: the secret names the character rule lets through as built: one character, 128 characters, and one
    name with every allowed kind of character (letters of both cases, digits, underscore, dot, colon,
    hyphen). Loads unchanged. (A slash left the charset in core-b's D-config fix round 2, DRAFT 3 of
    handover/core-b/requests/001.answer.md; see the next test.)"""
    sender = _load(cfg_dir, _block({"s1": _sender(name)})).triggers.senders["s1"]
    assert sender.secret_names == (name,)


@pytest.mark.parametrize(
    "name", ["Key_one.v2:eu/primary-1", "a/b", "/", ".", "..", "a..b", "-", "_.:"]
)
def test_secret_name_with_a_slash_or_a_path_trick_or_no_letter_refused(cfg_dir, name):
    """Case: interface change (core-b DRAFT 3, requests/001.answer.md): "/" is no longer a secret-name character,
    and "." / ".." / a name holding ".." / a name with no letter or digit are refused (a file-backed provider
    would read a path). Refused at load, naming the field and not showing the name."""
    text = _refused(cfg_dir, _block({"s1": _sender(name)}))
    assert "triggers.senders.s1.secret_names" in text
    if len(name) > 6:  # a short name such as "-" is part of any text
        assert name not in text


HOSTILE_REF_IDS = [" ", "\t", "a b", "a\n", "a\u00a0b", "a\u200bb", "a\x00b", "a/b", "a" * 129, ""]


@pytest.mark.parametrize("value", HOSTILE_REF_IDS, ids=repr)
@pytest.mark.parametrize("field", ["agent_id", "principal_id"])
def test_blank_agent_or_principal_refused_by_the_model(field, value):
    """Case: an agent_id or principal_id given to the model itself that is whitespace-only (first-round finding
    F5, fixed), or holds a tab, a space, a line break, a non-breaking space, a zero-width space, a NUL or a slash,
    or has 129 characters, or is empty. Must be a validation error that names the field and does not show the
    value."""
    with pytest.raises(ValueError, match=field) as info:
        config_mod.TriggerSender(**_sender(**{field: value}))
    assert not value.strip() or value not in str(info.value)


@pytest.mark.parametrize("field", ["agent_id", "principal_id"])
def test_agent_and_principal_id_characters_allowed_as_built(field):
    """Case: an agent_id or principal_id of 128 characters, and one with a colon, a dot, an underscore and a
    hyphen (the fixture's service principal has a colon). The model accepts both unchanged."""
    for value in ("a" * 128, "svc:Agent_one.v2-b"):
        assert getattr(config_mod.TriggerSender(**_sender(**{field: value})), field) == value


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


@pytest.mark.parametrize("field", ["max_running", "max_body_bytes", "ack_wait_s"])
def test_true_is_not_a_number(cfg_dir, field):
    """Case: `true` where a number is expected (max_running, max_body_bytes, ack_wait_s). Must be refused
    (first-round finding F8, fixed by strict fields)."""
    assert f"triggers.{field}" in _refused(cfg_dir, _block(**{field: True}))


@pytest.mark.parametrize("value", [False, "1", "4", "4.0", " 4", None, [4], {"n": 4}], ids=repr)
@pytest.mark.parametrize("field", ["max_running", "max_body_bytes", "ack_wait_s"])
def test_not_a_number_is_not_a_number(cfg_dir, field, value):
    """Case: neighbours of finding F8: `false`, the texts "1", "4", "4.0" and " 4", an explicit null, a list and a
    mapping where a number is expected (max_running, max_body_bytes, ack_wait_s). Refused, the field named: text
    is never turned into a number."""
    assert f"triggers.{field}" in _refused(cfg_dir, _block(**{field: value}))


@pytest.mark.parametrize("value", [4.0, 1.0, 64.0], ids=repr)
@pytest.mark.parametrize("field", ["max_running", "max_body_bytes"])
def test_float_for_a_whole_number_refused(cfg_dir, field, value):
    """Case: a float with no fraction (4.0, 1.0, 64.0) where a whole number is expected (max_running, max_body_bytes).
    Refused, the field named: a float is not silently cut to a whole number."""
    assert f"triggers.{field}" in _refused(cfg_dir, _block(**{field: value}))


@pytest.mark.parametrize("field", ["max_running", "max_body_bytes", "ack_wait_s"])
def test_number_far_above_the_ceiling_refused(cfg_dir, field):
    """Case: a whole number too large for 64 bits (2 to the power 70) in a bounded field. Refused, the field named
    (no overflow, no wrap-around to a small number)."""
    assert f"triggers.{field}" in _refused(cfg_dir, _block(**{field: 2**70}))


def test_whole_number_for_ack_wait_loads_as_a_float(cfg_dir):
    """Case: ack_wait_s written as the whole number 5 (the one mixing of types core-b keeps). Loads as the float
    5.0."""
    value = _load(cfg_dir, _block(ack_wait_s=5)).triggers.ack_wait_s
    assert (type(value), value) == (float, 5.0)


def test_exponent_text_for_ack_wait_refused(cfg_dir):
    """Case: ack_wait_s written as 1e1 in the YAML file itself. The YAML reader hands this over as text, not as a
    number, so the strict field refuses it (it is not read as 10 seconds)."""
    _write(cfg_dir, _block())
    path = cfg_dir / "config.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "  ack_wait_s: 1e1\n", encoding="utf-8")
    assert yaml.safe_load(path.read_text(encoding="utf-8"))["triggers"]["ack_wait_s"] == "1e1"
    with pytest.raises(ConfigError, match=r"triggers\.ack_wait_s"):
        load_config(cfg_dir)


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


@pytest.mark.parametrize("status", ["draft", "retired"])
def test_registry_refuses_a_sender_whose_agent_is_not_live(cfg_dir, status):
    """Case (new in core-b's fix round): the sender's agent exists and has status draft or retired. Refused with
    the sender and the field; the same agents.yaml without a triggers block still loads."""
    path = cfg_dir / "agents.yaml"
    text = path.read_text(encoding="utf-8")
    assert text.count("status: live") == 1
    path.write_text(text.replace("status: live", f"status: {status}"), encoding="utf-8")
    refusal = _registry_refusal(cfg_dir, _block())
    assert "triggers.senders.s1.agent_id: the agent must have status live" in refusal
    assert AGENT in load_registry(_load(cfg_dir, None)).agents


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
    # The refusal points to the sender that lists the missing name, and does not show the name itself.
    owner = "s2" if missing == "key-three" else "s1"
    assert f"triggers.senders.{owner}.secret_names" in text
    assert missing not in text


def _start_refusal(cfg_dir: Path, block: dict, values: dict[str, str]) -> tuple[str, _Recording]:
    """The text of the ConfigError that stops the start, and the provider with what was read before it."""
    _write(cfg_dir, block)
    qualify(load_registry(load_config(cfg_dir)))
    provider = _Recording({ACTION_KEY_NAME: TOKEN, **values})
    with pytest.raises(ConfigError) as info:
        build(cfg_dir, [AGENT], secrets=provider)
    return str(info.value), provider


def test_a_sender_secret_name_that_is_an_action_secret_fails_the_start(cfg_dir):
    """Case: a sender lists the name of an action executor's secret. The start is refused; the text names the
    sender's field and shows neither the secret's value nor the shared name, and no secret was read before the
    refusal."""
    text, provider = _start_refusal(cfg_dir, _block({"s1": _sender(ACTION_KEY_NAME)}), {})
    assert "triggers.senders.s1.secret_names" in text
    assert "also used" in text
    assert TOKEN not in text
    assert ACTION_KEY_NAME not in text
    assert provider.read == []


def test_shared_action_secret_refusal_names_the_sender(cfg_dir):
    """Case: as above with two senders, only the second one sharing the action's name. The refusal points to
    `triggers.senders.s2`, not to a backend and not to the sender that is in order (first-round finding F4b,
    fixed)."""
    block = _block({"s1": _sender("key-one"), "s2": _sender(ACTION_KEY_NAME)})
    text, _ = _start_refusal(cfg_dir, block, {"key-one": VALUE_ONE})
    assert "triggers.senders.s2" in text
    assert "triggers.senders.s1" not in text
    assert "give the backend its own secret" not in text


def test_start_refusal_does_not_echo_what_was_typed_as_a_secret_name(cfg_dir):
    """Case: a real secret pasted where a name belongs (it has only characters a name may have); the provider has
    no such name. The start fails naming the sender, and the pasted text is neither in the message nor in the
    printed traceback (first-round finding F4a, fixed: the provider's own error is not chained)."""
    _write(cfg_dir, _block({"s1": _sender(PASTED)}))
    qualify(load_registry(load_config(cfg_dir)))
    with pytest.raises(ConfigError) as info:
        build(cfg_dir, [AGENT], secrets=_Recording({ACTION_KEY_NAME: TOKEN}))
    assert "triggers.senders.s1.secret_names" in str(info.value)
    assert PASTED not in str(info.value)
    printed = "".join(traceback.format_exception(info.value))
    assert PASTED not in printed
    assert info.value.__cause__ is None


def _edit_config(cfg_dir: Path, change) -> None:
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_a_sender_secret_name_that_is_another_platform_secret_fails_the_start(cfg_dir):
    """Case: a sender lists the name configured as evidence.restored_hash_key_secret_name. Must be refused,
    naming the sender (first-round finding F2, fixed); the shared name is not shown and nothing was read."""
    _edit_config(
        cfg_dir, lambda d: d.update(evidence={"restored_hash_key_secret_name": "shared-key"})
    )
    text, provider = _start_refusal(
        cfg_dir, _block({"s1": _sender("shared-key")}), {"shared-key": VALUE_ONE}
    )
    assert "triggers.senders.s1.secret_names" in text
    assert "shared-key" not in text
    assert provider.read == []


@pytest.mark.parametrize(
    "store",
    [
        {"dsn_secret_name": "shared-key"},
        {"dsn_secret_name": "dsn-key", "purge_dsn_secret_name": "shared-key"},
        {"dsn_secret_name": "dsn-key", "sslrootcert_secret_name": "shared-key"},
        {"dsn_secret_name": "dsn-key", "reset_credential_ref": "shared-key"},
    ],
    ids=["dsn", "purge-dsn", "root-certificate", "reset-login"],
)
def test_a_sender_secret_name_that_is_a_backend_secret_fails_the_start(cfg_dir, store):
    """Case (neighbour of finding F2): a sender lists a name the store backend uses: its DSN, its purge DSN, its
    root certificate, or the reset login reference. The start is refused naming the sender, before any secret is
    read and before the store is built (no database is touched)."""
    _edit_config(cfg_dir, lambda d: d["backends"].update(store={"kind": "postgres", **store}))
    text, provider = _start_refusal(
        cfg_dir,
        _block({"s1": _sender("shared-key")}),
        {"shared-key": VALUE_ONE, "dsn-key": VALUE_TWO},
    )
    assert "triggers.senders.s1.secret_names" in text
    assert "shared-key" not in text
    assert provider.read == []


def test_second_name_of_a_pair_shared_with_an_action_secret_fails_the_start(cfg_dir):
    """Case (neighbour of finding F2): a sender with two names, the first its own and the SECOND the action's
    secret name. Refused: every name of the pair is compared, not only the first."""
    text, provider = _start_refusal(
        cfg_dir, _block({"s1": _sender("key-one", ACTION_KEY_NAME)}), {"key-one": VALUE_ONE}
    )
    assert "triggers.senders.s1.secret_names" in text
    assert provider.read == []


# --- the `env` secrets kind folds names ------------------------------------------------------------------------------

ENV_PREFIX = "TRIGGER_TEST_"


def _env_provider():
    from hadavin_sdk.actions.secrets_env import EnvSecretProvider

    environ = {
        ENV_PREFIX + "FIXTURE_TOKEN": TOKEN,
        ENV_PREFIX + "KEY_ONE": VALUE_ONE,
        ENV_PREFIX + "KEY_TWO": VALUE_TWO,
    }
    return EnvSecretProvider(ENV_PREFIX, environ)


def _build_with_env(cfg_dir: Path, senders: dict):
    _write(cfg_dir, _block(senders))
    qualify(load_registry(load_config(cfg_dir)))
    return build(cfg_dir, [AGENT], secrets=_env_provider())


def test_env_kind_with_distinct_sender_secrets_starts(cfg_dir):
    """Case: the `env` secrets kind (its own table of variables, not the process environment), two senders whose
    names stand for two different variables. The app starts and each sender reads its own value. (The control
    for the finding below: the env kind itself works here.)"""
    app = _build_with_env(cfg_dir, {"s1": _sender("key-one"), "s2": _sender("key-two")})
    assert app.trigger_secret("key-one") == VALUE_ONE
    assert app.trigger_secret("key-two") == VALUE_TWO


@pytest.mark.parametrize(
    "senders",
    [
        {"s1": _sender("FIXTURE_TOKEN")},
        {"s1": _sender("fixture.token")},
        {"s1": _sender("key-one"), "s2": _sender("key_one")},
        {"s1": _sender("key-one", "KEY-ONE")},
    ],
    ids=["action-secret-upper", "action-secret-dot", "two-senders", "one-sender-pair"],
)
def test_env_kind_alias_of_a_secret_name_fails_the_start(cfg_dir, senders):
    """Case: with the `env` secrets kind, a sender secret name that is written differently from, and stands for
    the same variable as, (1, 2) the action's secret, (3) another sender's secret, (4) the other name of the same
    sender. Must be refused at start, naming the sender: one secret must not serve two jobs or two senders."""
    with pytest.raises(ConfigError, match=r"triggers\.senders\."):
        _build_with_env(cfg_dir, senders)


# --- the reader the worker gets --------------------------------------------------------------------------------------


def _reader(app):
    """The reader for sender secrets as built on core-b's head: `App.trigger_secret`, called with one name."""
    return app.trigger_secret


def test_reader_hands_out_every_listed_sender_secret(cfg_dir):
    """Case: the worker asks for each name listed under the senders. It gets that secret's value."""
    app, _ = _build(cfg_dir, _block(TWO_SENDERS), TWO_SENDER_VALUES)
    read = _reader(app)
    for sender in app.config.triggers.senders.values():
        for name in sender.secret_names:
            assert read(name) == TWO_SENDER_VALUES[name]


def test_reader_refuses_a_name_that_no_sender_lists(cfg_dir):
    """Case: the worker asks for a secret that exists and that no sender lists (an action's secret). The reader
    must refuse; a name that does not exist at all must be refused the same way (first-round finding F3, fixed by
    `App.trigger_secret`)."""
    app, _ = _build(cfg_dir, _block(TWO_SENDERS), TWO_SENDER_VALUES)
    read = _reader(app)
    with pytest.raises(PermissionError):
        read(ACTION_KEY_NAME)
    with pytest.raises(PermissionError):
        read("no-such-name")


def _app_with_other_secrets(cfg_dir: Path):
    """An app whose provider holds, next to the sender secrets, an action secret, the restored-hash key (a secret
    of another part of the platform) and a secret nothing in the config names."""
    _edit_config(
        cfg_dir, lambda d: d.update(evidence={"restored_hash_key_secret_name": "hash-key"})
    )
    values = {**TWO_SENDER_VALUES, "hash-key": "hash-" + "h" * 40, "stray-key": "stray-" + "s" * 40}
    app, provider = _build(cfg_dir, _block(TWO_SENDERS), values)
    return app, provider, values


@pytest.mark.parametrize(
    "asked",
    [
        ACTION_KEY_NAME,
        "hash-key",
        "stray-key",
        "no-such-name",
        "",
        "KEY-ONE",
        "key-one ",
        " key-one",
        "key-one\n",
        "key-one\x00",
        "s1",
        PASTED,
    ],
    ids=repr,
)
def test_trigger_secret_refuses_every_name_that_is_not_a_sender_secret_name(cfg_dir, asked):
    """Case (new: `App.trigger_secret`): the worker asks for an action's secret, another platform secret (the
    restored-hash key), a secret no part of the config names, an unknown name, the empty name, a sender name in
    another case or with a space, a line break or a NUL added, a sender id, and a secret value typed as a name.
    Each is refused with PermissionError; the provider is not asked; the text shows no secret value and not the
    name that was asked for."""
    app, provider, values = _app_with_other_secrets(cfg_dir)
    before = list(provider.read)
    with pytest.raises(PermissionError) as info:
        app.trigger_secret(asked)
    text = str(info.value)
    assert provider.read == before
    assert not any(v in text for v in (*values.values(), TOKEN))
    assert not asked or asked not in text
    assert "triggers.senders" in text


@pytest.mark.parametrize(
    "asked", [None, 0, 1, True, b"key-one", ("key-one",), ["key-one"], {"key-one"}], ids=repr
)
def test_trigger_secret_refuses_a_name_of_another_kind(cfg_dir, asked):
    """Case (new: `App.trigger_secret`): the worker passes something that is not text where the name belongs:
    null, a number, a boolean, bytes, a tuple, a list or a set holding a sender name. Each is refused (a
    PermissionError, or a TypeError for a list or set), no value is handed out, the provider is not asked and
    no secret value is in the text."""
    app, provider, values = _app_with_other_secrets(cfg_dir)
    before = list(provider.read)
    with pytest.raises((PermissionError, TypeError)) as info:
        app.trigger_secret(asked)
    assert provider.read == before
    assert not any(v in str(info.value) for v in (*values.values(), TOKEN))


def test_trigger_secret_is_called_with_one_name_and_reads_the_provider_each_time(cfg_dir):
    """Case (new: `App.trigger_secret`): the call signature as built is one parameter called `name`; it works by
    position and by keyword and returns the secret's text. Each call asks the provider once (the reader keeps no
    copy of a value), so a changed secret is seen at the next call."""
    app, provider, values = _app_with_other_secrets(cfg_dir)
    assert list(inspect.signature(app.trigger_secret).parameters) == ["name"]
    before = len(provider.read)
    assert app.trigger_secret("key-one") == VALUE_ONE
    assert app.trigger_secret(name="key-three") == values["key-three"]
    assert provider.read[before:] == ["key-one", "key-three"]
    provider._values["key-one"] = "changed-" + "c" * 36
    assert app.trigger_secret("key-one") == "changed-" + "c" * 36
    with pytest.raises(TypeError):
        app.trigger_secret()
    with pytest.raises(TypeError):
        app.trigger_secret("key-one", "key-two")


def test_trigger_secret_is_a_plain_function_that_does_not_hand_out_the_provider(cfg_dir):
    """Case (new: `App.trigger_secret`): what the object is. A plain function: not the provider, not a method bound
    to the provider (no `__self__`), not a partial (no `func`, `args`, `keywords`), with no public attribute at
    all and no `get`. So no normal attribute of the reader gives the whole provider."""
    app, provider, _ = _app_with_other_secrets(cfg_dir)
    read = app.trigger_secret
    assert read is not provider
    assert type(read) is types.FunctionType
    assert not isinstance(read, FakeSecretProvider)
    for attribute in ("__self__", "func", "args", "keywords", "get", "secrets", "provider"):
        assert not hasattr(read, attribute), attribute
    assert [a for a in dir(read) if not a.startswith("_")] == []
    assert read.__dict__ == {}
    assert read.__defaults__ is None
    assert read.__kwdefaults__ is None


def test_app_has_no_secrets_field_and_no_field_that_is_the_provider(cfg_dir):
    """Case (new): `App.secrets` is gone: no attribute and no field of that name, on the class or on a built app.
    No field of the app IS the secrets provider, and no public attribute of a field's value is the provider
    either. `trigger_secret` is a field of App."""
    app, provider, _ = _app_with_other_secrets(cfg_dir)
    names = [f.name for f in dataclasses.fields(app)]
    assert "secrets" not in names
    assert not hasattr(app, "secrets")
    assert not hasattr(type(app), "secrets")
    assert "trigger_secret" in names
    assert not any(n in names for n in ("provider", "secret_provider", "trigger_resolve"))
    for name in names:
        value = getattr(app, name)
        assert value is not provider, name
        public = {k: v for k, v in getattr(value, "__dict__", {}).items() if not k.startswith("_")}
        assert not any(v is provider for v in public.values()), name


def test_without_the_block_the_reader_exists_and_refuses_every_name(cfg_dir):
    """Case (new, as built): no triggers block. `App.trigger_secret` is not None: it is the same kind of reader
    with no name allowed, so every name is refused with PermissionError, the fixture's own action secret
    included, and the provider is not asked."""
    app, provider = _build(cfg_dir, None, {"key-one": VALUE_ONE})
    assert app.config.triggers is None
    assert callable(app.trigger_secret)
    before = list(provider.read)
    for asked in (ACTION_KEY_NAME, "key-one", "no-such-name", ""):
        with pytest.raises(PermissionError) as info:
            app.trigger_secret(asked)
        assert TOKEN not in str(info.value)
        assert VALUE_ONE not in str(info.value)
    assert provider.read == before


def test_reader_of_one_app_does_not_read_for_another_apps_senders(cfg_dir, tmp_path):
    """Case (new): two apps built one after the other from two configs with different senders. Each reader hands
    out only its own app's sender names (the allowed names are not shared between apps)."""
    first, _ = _build(cfg_dir, _block({"s1": _sender("key-one")}), TWO_SENDER_VALUES)
    other_dir = make_cfg(tmp_path / "other")
    second, _ = _build(other_dir, _block({"s1": _sender("key-three")}), TWO_SENDER_VALUES)
    assert first.trigger_secret("key-one") == VALUE_ONE
    assert second.trigger_secret("key-three") == TWO_SENDER_VALUES["key-three"]
    with pytest.raises(PermissionError):
        first.trigger_secret("key-three")
    with pytest.raises(PermissionError):
        second.trigger_secret("key-one")


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
