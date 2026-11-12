"""The kind registry: every kind is a stand-in or a real kind, and nothing is left unclassified.

A stand-in is a local imitation of a service (the fake model, the in-memory store). It must be refused by a client
stage (DEMO_ONLY or NOT_PROD) and, if its settings can name a machine, it must say which hosts it reaches so the
config check can insist on this computer. A planted bad kind must fail each rule.
"""

from __future__ import annotations

import ast
import random
import re
from dataclasses import replace
from pathlib import Path

import pytest

from hadavin_sdk.backends import table as table_mod
from hadavin_sdk.backends.table import (
    DEMO_ONLY,
    NOT_PROD,
    TABLE,
    Entry,
    KindSettings,
    assert_registry_sound,
    registry_problems,
)

GOOD = Entry(KindSettings, "hadavin_sdk.backends.builtin:fake_secrets", role="stand_in")


def _table(**kinds: Entry) -> dict[str, dict[str, Entry]]:
    return {"x": dict(kinds)}


def test_every_registered_kind_is_classified_exactly_once():
    unclassified = [(c, k) for c, ks in TABLE.items() for k, e in ks.items() if e.role is None]
    assert unclassified == [], f"unclassified kinds: {unclassified}"
    assert registry_problems(TABLE) == [], "the real table breaks a registry rule"


def test_the_stand_ins_are_exactly_the_demo_only_and_not_prod_kinds_that_imitate_a_service():
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
    assert stand_ins <= DEMO_ONLY | NOT_PROD, "a stand-in is not refused by a client stage"


def test_a_kind_marked_for_demo_only_or_not_prod_exists_and_is_not_forgotten():
    every = {(c, k) for c, ks in TABLE.items() for k in ks}
    assert DEMO_ONLY | NOT_PROD <= every


def test_plant_an_unclassified_kind_is_caught():
    found = registry_problems(_table(new=replace(GOOD, role=None)))
    assert found == ["backend x kind new: not classified; give it role stand_in or real"], (
        "an unclassified kind was not reported"
    )


def test_plant_a_misspelt_role_is_caught():
    found = registry_problems(_table(new=replace(GOOD, role="standin")))  # type: ignore[arg-type]
    assert len(found) == 1 and "not classified" in found[0], "a misspelt role was not reported"


def test_plant_a_stand_in_a_client_stage_would_accept_is_caught():
    found = registry_problems(_table(fake=GOOD))
    assert found == ["backend x kind fake: a stand-in must be listed in DEMO_ONLY or NOT_PROD"], (
        "a stand-in outside DEMO_ONLY and NOT_PROD was not reported"
    )
    assert registry_problems(_table(fake=GOOD), demo_only=frozenset({("x", "fake")})) == [], (
        "demo-only listing refused"
    )
    assert registry_problems(_table(fake=GOOD), not_prod=frozenset({("x", "fake")})) == [], (
        "not-prod listing refused"
    )


class _WithHost(KindSettings):
    fakes_host: str = "127.0.0.1"


def test_plant_a_stand_in_with_a_host_setting_and_no_hosts_is_caught():
    bad = replace(GOOD, settings=_WithHost)
    found = registry_problems(_table(fake=bad), demo_only=frozenset({("x", "fake")}))
    assert found == [
        "backend x kind fake: a stand-in with a host setting (fakes_host) must declare hosts"
    ], "a stand-in with a host setting and no hosts was not reported"
    ok = replace(bad, hosts=lambda s: [s.fakes_host])
    assert registry_problems(_table(fake=ok), demo_only=frozenset({("x", "fake")})) == [], (
        "declared hosts refused"
    )


def test_a_real_kind_needs_no_demo_only_entry_and_no_hosts():
    real = replace(GOOD, role="real", settings=_WithHost)
    assert registry_problems(_table(svc=real)) == [], "a real kind was held to the stand-in rules"


def test_every_problem_is_reported_at_once():
    table = _table(a=replace(GOOD, role=None), b=GOOD)
    assert len(registry_problems(table)) == 2, "not every problem was reported at once"


def test_the_import_time_guard_raises_naming_the_unclassified_kind():
    with pytest.raises(RuntimeError, match=r"backend x kind new: not classified"):
        assert_registry_sound(_table(new=replace(GOOD, role=None)))
    assert_registry_sound(_table(ok=replace(GOOD, role="real")))


def test_the_table_module_runs_the_guard_on_its_own_table_at_import():
    """The guard is a top-level statement of table.py, so a kind added without a role stops every import."""
    tree = ast.parse(Path(table_mod.__file__).read_text(encoding="utf-8"))
    calls = [
        n.value for n in tree.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
    ]
    assert any(
        isinstance(c.func, ast.Name)
        and c.func.id == "assert_registry_sound"
        and ast.unparse(c.args[0]) == "TABLE"
        for c in calls
    ), "table.py no longer runs the registry guard at import"


def test_seeded_fuzz_of_role_marks_and_listings_agrees_with_the_rules():
    """500 random tables: the checker's verdict equals an independent statement of the three rules."""
    rng = random.Random(20261112)  # noqa: S311 - a seeded test generator, not a secret
    names = ["host", "url", "address", "endpoint", "dir", "region", "timeout_s", "base_url", "HOST"]
    for _ in range(500):
        fields = rng.sample(names, rng.randint(0, 3))
        model = type(
            "S",
            (KindSettings,),
            {"__annotations__": {n: str for n in fields}, **{n: "v" for n in fields}},
        )
        role = rng.choice(["stand_in", "real", None, "other"])
        listed = rng.random() < 0.5
        declared = rng.random() < 0.5
        entry = Entry(model, "m:f", role=role, hosts=(lambda s: []) if declared else None)  # type: ignore[arg-type]
        got = registry_problems(
            {"c": {"k": entry}},
            demo_only=frozenset({("c", "k")}) if listed else frozenset(),
            not_prod=frozenset(),
        )
        want: list[str] = []
        if role not in ("stand_in", "real"):
            want.append("not classified")
        elif role == "stand_in":
            if not listed:
                want.append("DEMO_ONLY or NOT_PROD")
            if (
                any(re.search("host|url|address|endpoint", n, re.IGNORECASE) for n in fields)
                and not declared
            ):
                want.append("must declare hosts")
        assert len(got) == len(want) and all(w in g for w, g in zip(want, got, strict=True)), (
            f"the checker disagrees with the rules: {(fields, role, listed, declared, got)}"
        )
