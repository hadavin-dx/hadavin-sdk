"""The kind registry: every kind is a stand-in or a real kind, and nothing is left unclassified.

A stand-in is a local imitation of a service (the fake model, the in-memory store). A live stage (pilot, prod) must
refuse it (DEMO_ONLY; the two in-process exceptions in PILOT_STAND_INS are refused only in prod), and it must say
which hosts it reaches (an empty list is a deliberate "none") so the config check can insist on this computer. A
planted bad kind must fail each rule, and the rules run the first time a config is built, not only in these tests.
"""

from __future__ import annotations

import ipaddress
import random
import sys
import types
from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import AnyUrl

from hadavin_sdk.backends import table as table_mod
from hadavin_sdk.backends.table import (
    DEMO_ONLY,
    NOT_PROD,
    PILOT_STAND_INS,
    TABLE,
    Entry,
    KindSettings,
    assert_registry_sound,
    names_a_machine,
    registry_problems,
)
from hadavin_sdk.config import load_config
from tests.conftest import make_cfg

# The deliberate "reaches no machine": a stand-in must declare its hosts, and an empty list says none.
GOOD = Entry(
    KindSettings, "hadavin_sdk.backends.builtin:fake_secrets", role="stand_in", hosts=lambda s: []
)
LISTED = frozenset({("x", "fake")})
LISTED_CK = frozenset({("c", "k")})


def _table(**kinds: Entry) -> dict[str, dict[str, Entry]]:
    return {"x": dict(kinds)}


def _model(**fields: object) -> type[KindSettings]:
    """A settings model with the given fields: name -> annotation."""
    return type(
        "S",
        (KindSettings,),
        {"__annotations__": dict(fields), **dict.fromkeys(fields)},
    )


def test_every_registered_kind_is_classified_exactly_once():
    unclassified = [(c, k) for c, ks in TABLE.items() for k, e in ks.items() if e.role is None]
    assert unclassified == [], f"unclassified kinds: {unclassified}"
    assert registry_problems(TABLE) == [], "the real table breaks a registry rule"
    assert_registry_sound()  # the call a config build makes


def test_the_stand_ins_are_exactly_these_seven_and_each_is_refused_by_the_stage_that_must():
    stand_ins = {(c, k) for c, ks in TABLE.items() for k, e in ks.items() if e.role == "stand_in"}
    assert stand_ins == {
        ("secrets", "fake"),
        ("signer", "none"),
        ("anchor", "none"),
        ("store", "memory"),
        ("audit", "local_dir"),
        ("llm", "fake"),
        ("channel", "fake"),
    }, "the set of stand-in kinds changed"
    assert PILOT_STAND_INS == {("signer", "none"), ("anchor", "none")}, (
        "the pilot exceptions changed"
    )
    assert PILOT_STAND_INS <= NOT_PROD, "a pilot exception is not refused in prod"
    # a pilot or prod config refuses every other stand-in (DEMO_ONLY is refused in any live stage)
    assert stand_ins - PILOT_STAND_INS <= DEMO_ONLY, (
        "a stand-in would run in a pilot with client data"
    )
    assert PILOT_STAND_INS <= stand_ins, "a pilot exception that is not a stand-in"


def test_a_kind_marked_for_demo_only_or_not_prod_exists_and_is_not_forgotten():
    every = {(c, k) for c, ks in TABLE.items() for k in ks}
    assert DEMO_ONLY | NOT_PROD <= every


def test_every_stand_in_of_the_table_declares_its_hosts_and_names_no_machine():
    stand_ins = [(c, k) for c, ks in TABLE.items() for k, e in ks.items() if e.role == "stand_in"]
    assert len(stand_ins) == 7
    for cap, kind in stand_ins:
        entry = TABLE[cap][kind]
        assert entry.hosts is not None, f"{cap}/{kind} declares no hosts"
        assert names_a_machine(entry.settings) == [], (
            f"{cap}/{kind} has a setting that names a machine"
        )


def test_plant_an_unclassified_kind_is_caught():
    found = registry_problems(_table(new=replace(GOOD, role=None)))
    assert found == ["backend x kind new: not classified; give it role stand_in or real"], (
        "an unclassified kind was not reported"
    )


def test_plant_a_misspelt_role_is_caught():
    found = registry_problems(_table(new=replace(GOOD, role="standin")))  # type: ignore[arg-type]
    assert len(found) == 1 and "not classified" in found[0], "a misspelt role was not reported"


def test_plant_a_stand_in_a_live_stage_would_accept_is_caught():
    found = registry_problems(_table(fake=GOOD), demo_only=frozenset(), not_prod=frozenset())
    assert len(found) == 1 and "must be listed in DEMO_ONLY" in found[0], (
        "a stand-in outside DEMO_ONLY was not reported"
    )
    assert registry_problems(_table(fake=GOOD), demo_only=LISTED) == [], "demo-only listing refused"


def test_plant_a_stand_in_listed_only_in_not_prod_is_caught_unless_it_is_a_named_exception():
    """A not-prod-only stand-in would run in a pilot with client data: only the named in-process ones may."""
    only_not_prod = registry_problems(
        _table(fake=GOOD), demo_only=frozenset(), not_prod=LISTED, pilot_stand_ins=frozenset()
    )
    assert len(only_not_prod) == 1 and "must be listed in DEMO_ONLY" in only_not_prod[0], (
        "a stand-in listed only in NOT_PROD was accepted"
    )
    named = registry_problems(
        _table(fake=GOOD), demo_only=frozenset(), not_prod=LISTED, pilot_stand_ins=LISTED
    )
    assert named == [], "a named in-process exception was refused"
    only_named = registry_problems(
        _table(fake=GOOD), demo_only=frozenset(), not_prod=frozenset(), pilot_stand_ins=LISTED
    )
    assert len(only_named) == 1, "an exception that prod does not refuse was accepted"


def test_plant_a_stand_in_that_declares_no_hosts_is_caught():
    bad = replace(GOOD, hosts=None)
    found = registry_problems(_table(fake=bad), demo_only=LISTED)
    assert found == [
        "backend x kind fake: a stand-in must declare its hosts (hosts=; an empty list means none)"
    ], "a stand-in with no declared hosts was not reported"
    assert registry_problems(_table(fake=GOOD), demo_only=LISTED) == [], "an empty list refused"


MACHINE_FIELDS = [
    "fakes_host", "HOST", "hostname", "api_base", "base", "dsn", "uri", "server", "origin", "domain",
    "proxy", "broker", "target", "remote", "socket", "bind", "endpointUrl", "base_url", "ip", "address",
    "netloc",
]  # fmt: skip
PLAIN_FIELDS = [
    "dir",
    "recorded_dir",
    "region",
    "timeout_s",
    "database_name",
    "name",
    "retention_days",
]
URL_TYPES = [
    AnyUrl,
    AnyUrl | None,
    list[AnyUrl],
    ipaddress.IPv4Address,
    ipaddress.IPv6Address | None,
]


def test_a_field_name_that_points_at_a_machine_is_found():
    for field in MACHINE_FIELDS:
        assert names_a_machine(_model(**{field: str})) == [field], (
            f"a field that points at a machine was not found: {field}"
        )


def test_a_field_name_that_points_at_no_machine_is_not_flagged():
    for field in PLAIN_FIELDS:
        assert names_a_machine(_model(**{field: str})) == [], (
            f"a field that points at no machine was flagged: {field}"
        )


def test_a_field_that_holds_a_url_or_an_address_is_found_whatever_it_is_called():
    for annotation in URL_TYPES:
        assert names_a_machine(_model(thing=annotation)) == ["thing"], (
            f"a field typed as a URL or an address was not found: {annotation}"
        )


def test_the_kind_field_itself_is_never_a_machine():
    assert names_a_machine(KindSettings) == []


def test_a_real_kind_needs_no_demo_only_entry_and_no_hosts():
    real = replace(GOOD, role="real", hosts=None, settings=_model(fakes_host=str))
    assert registry_problems(_table(svc=real)) == [], "a real kind was held to the stand-in rules"


def test_every_problem_is_reported_at_once():
    table = _table(a=replace(GOOD, role=None), b=replace(GOOD, hosts=None))
    # a: not classified. b: not listed and no hosts.
    assert len(registry_problems(table, demo_only=frozenset())) == 3, (
        "not every problem was reported at once"
    )


def test_the_sets_are_read_when_the_check_runs_not_when_it_is_defined(monkeypatch):
    monkeypatch.setattr(table_mod, "DEMO_ONLY", frozenset())
    assert any("must be listed in DEMO_ONLY" in p for p in registry_problems(TABLE)), (
        "the check used the DEMO_ONLY of definition time"
    )
    with pytest.raises(RuntimeError, match="must be listed in DEMO_ONLY"):
        assert_registry_sound()


def test_the_check_raises_naming_every_broken_kind():
    with pytest.raises(RuntimeError, match=r"backend x kind new: not classified"):
        assert_registry_sound(_table(new=replace(GOOD, role=None)))
    assert_registry_sound(_table(ok=replace(GOOD, role="real")))


# --- the rules run the first time a config is built, whoever built the kind -------------------------------------


@pytest.fixture
def valid_cfg_dir(tmp_path):
    return make_cfg(tmp_path)


DOWNSTREAM = [
    (Entry(KindSettings, "m:f", role=None), "not classified"),
    (
        Entry(KindSettings, "m:f", role="stand_in", hosts=lambda s: []),
        "must be listed in DEMO_ONLY",
    ),
    (Entry(KindSettings, "m:f", role="stand_in"), "must declare its hosts"),
]


def test_a_downstream_kind_that_breaks_a_rule_is_refused_at_the_first_config(
    monkeypatch, valid_cfg_dir
):
    """The user adds a kind; nothing imports a test; the first config build must refuse."""
    for planted, message in DOWNSTREAM:
        with monkeypatch.context() as m:
            m.setitem(TABLE["channel"], "downstream", planted)
            with pytest.raises(RuntimeError, match=message):
                load_config(valid_cfg_dir)


def test_the_same_refusal_holds_for_a_backends_built_directly(monkeypatch, valid_cfg_dir):
    from hadavin_sdk.config import Backends

    good = load_config(valid_cfg_dir).backends
    fields = {cap: getattr(good, cap) for cap in TABLE}
    assert Backends(**fields) == good, "the unplanted copy was refused"
    monkeypatch.setitem(TABLE["channel"], "downstream", Entry(KindSettings, "m:f", role=None))
    with pytest.raises(RuntimeError, match="not classified"):
        Backends(**fields)


# --- the import-time guard: classification only ----------------------------------------------------------------


def _source() -> str:
    return Path(table_mod.__file__).read_text(encoding="utf-8")


def _import_copy(source: str, name: str = "hadavin_sdk.backends._table_copy") -> types.ModuleType:
    """Run `source` (the text of table.py, maybe edited) as a fresh module and return it."""
    module = types.ModuleType(name)
    module.__file__ = str(Path(table_mod.__file__))
    sys.modules[name] = module
    try:
        exec(compile(source, module.__file__, "exec"), module.__dict__)  # noqa: S102  # nosec B102 - our own source file
    finally:
        sys.modules.pop(name, None)
    return module


def test_importing_the_table_with_a_kind_that_has_no_role_stops_the_import():
    old = 'Entry(KindSettings, f"{_BUILTIN}:memory_store", role="stand_in", hosts=_no_hosts)'
    assert old in _source()
    edited = _source().replace(old, old.replace(', role="stand_in"', ""))
    with pytest.raises(RuntimeError, match=r"backend store kind memory: not classified"):
        _import_copy(edited)


def test_importing_the_untouched_table_works_and_is_sound():
    module = _import_copy(_source())
    module.assert_registry_sound()  # its own TABLE and its own sets
    assert set(module.TABLE) == set(TABLE)


def test_a_broken_listing_does_not_stop_the_import_but_fails_at_first_use():
    """Rules 2 and 3 wait for the first config: enforcing them at import would crash a half-edited table before any
    test could say why (it crashed five stage mutants in an earlier try)."""
    old = '        ("store", "memory"),\n'
    assert _source().count(old) == 1
    error = None
    try:
        module = _import_copy(_source().replace(old, ""))
    except RuntimeError as exc:
        error = exc
    assert error is None, f"a rule other than classification stopped the import: {error}"
    with pytest.raises(RuntimeError, match=r"backend store kind memory: a stand-in must be listed"):
        module.assert_registry_sound()


def test_seeded_fuzz_of_role_marks_and_listings_agrees_with_the_rules():
    """800 random tables: the checker's verdict equals an independent statement of the rules (no global is touched)."""
    rng = random.Random(20261112)  # noqa: S311 - a seeded test generator, not a secret
    names = ["host", "url", "address", "endpoint", "dir", "region", "timeout_s", "api_base", "dsn"]
    seen = {"clean": 0, "unclassified": 0, "unlisted": 0, "no_hosts": 0, "exception": 0}
    for _ in range(800):
        fields = rng.sample(names, rng.randint(0, 3))
        role = rng.choice(["stand_in", "real", None, "other"])
        demo = rng.random() < 0.4
        not_prod = rng.random() < 0.5
        pilot = rng.random() < 0.5
        declared = rng.random() < 0.7
        entry = Entry(
            _model(**dict.fromkeys(fields, str)),
            "m:f",
            role=role,  # type: ignore[arg-type]
            hosts=(lambda s: []) if declared else None,
        )
        got = registry_problems(
            {"c": {"k": entry}},
            demo_only=LISTED_CK if demo else frozenset(),
            not_prod=LISTED_CK if not_prod else frozenset(),
            pilot_stand_ins=LISTED_CK if pilot else frozenset(),
        )
        want: list[str] = []
        if role not in ("stand_in", "real"):
            want.append("not classified")
            seen["unclassified"] += 1
        elif role == "stand_in":
            if not (demo or (not_prod and pilot)):
                want.append("must be listed in DEMO_ONLY")
                seen["unlisted"] += 1
            elif not demo:
                seen["exception"] += 1
            if not declared:
                want.append("must declare its hosts")
                seen["no_hosts"] += 1
        if not want:
            seen["clean"] += 1
        assert len(got) == len(want) and all(w in g for w, g in zip(want, got, strict=True)), (
            f"the checker disagrees with the rules: {(fields, role, demo, not_prod, pilot, declared, got)}"
        )
    assert all(n > 20 for n in seen.values()), f"the generator never reached a branch: {seen}"
