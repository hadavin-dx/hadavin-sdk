"""A stand-in kind may only be reached on this computer, and every way to build a config refuses anything else.

No stand-in kind in the table names a host today (the fake model, store and channel are in-process), so these tests
plant one: a stand-in channel with a `fakes_host` setting, a real channel with the same setting, and check both. The
rule sits on `Backends`, so the loader, a direct `Backends(...)` and `Backends.model_validate(...)` all hit it.
"""

from __future__ import annotations

import random

import pytest
import yaml
from pydantic import ValidationError

from hadavin_sdk.backends import table as table_mod
from hadavin_sdk.backends.table import TABLE, Entry, KindSettings
from hadavin_sdk.config import Backends, ConfigError, load_config, stand_in_host_problem
from hadavin_sdk.netguard import is_loopback_host
from tests.conftest import make_cfg


class _Hosted(KindSettings):
    fakes_host: str = "127.0.0.1"
    second_host: str | None = None


def _hosts(s: _Hosted) -> list[str]:
    return [s.fakes_host] + ([s.second_host] if s.second_host is not None else [])


def _plant(monkeypatch, name: str, entry: Entry) -> None:
    """Register a kind under channel/<name>; a stand-in is also listed DEMO_ONLY where the stage rule reads it."""
    monkeypatch.setitem(TABLE["channel"], name, entry)
    if entry.role == "stand_in":
        both = table_mod.DEMO_ONLY | {("channel", name)}
        monkeypatch.setattr("hadavin_sdk.config.DEMO_ONLY", both)
        monkeypatch.setattr(table_mod, "DEMO_ONLY", both)


@pytest.fixture
def planted(monkeypatch, tmp_path):
    """A stand-in channel kind `imitation` and a real channel kind `service`, both with host settings."""
    # not the conftest fixture: the mutant runner runs with no conftest
    cfg_dir = make_cfg(tmp_path)
    _plant(monkeypatch, "imitation", Entry(_Hosted, "m:f", hosts=_hosts, role="stand_in"))
    _plant(monkeypatch, "service", Entry(_Hosted, "m:f", hosts=_hosts, role="real"))

    def use(kind: str, **settings):
        path = cfg_dir / "config.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["backends"]["channel"] = {"kind": kind, **settings}
        path.write_text(yaml.safe_dump(data), encoding="utf-8")
        return load_config(cfg_dir)

    use.cfg_dir = cfg_dir
    return use


def _backends_with(planted, **channel_settings) -> dict:
    """The fields of a valid Backends (from the shipped test config) with the channel replaced: for a direct build."""
    good = planted("service").backends
    fields = {cap: getattr(good, cap) for cap in TABLE}
    fields["channel"] = _Hosted(kind="imitation", **channel_settings)
    return fields


@pytest.mark.parametrize(
    "host", ["127.0.0.1", "localhost", "LOCALHOST", "::1", "127.8.9.10", "[::1]"]
)
def test_a_stand_in_on_this_computer_is_accepted(planted, host):
    assert planted("imitation", fakes_host=host).backends.channel.kind == "imitation"


OTHER_COMPUTERS = [
    "example.test",
    "10.0.0.5",
    ".".join(["0"] * 4),  # the wildcard address, built from parts
    "::",
    "127.0.0.1.example.test",
    "2130706433",
    "127.1",
    "0x7f.0.0.1",
    "",
    " 127.0.0.1",
]


def test_a_stand_in_on_another_computer_is_refused(planted):
    for host in OTHER_COMPUTERS:
        with pytest.raises(
            ConfigError,
            match=r"backends.channel \(imitation\): a stand-in kind may only be reached on this computer",
        ):
            planted("imitation", fakes_host=host)


def test_a_backends_built_directly_hits_the_same_rule(planted):
    """Not through the loader: `Backends(...)` and `Backends.model_validate(...)` must refuse as well."""
    fields = _backends_with(planted, fakes_host="example.test")
    with pytest.raises(
        ValidationError, match="a stand-in kind may only be reached on this computer"
    ):
        Backends(**fields)
    with pytest.raises(
        ValidationError, match="a stand-in kind may only be reached on this computer"
    ):
        Backends.model_validate(fields)
    ok = _backends_with(planted, fakes_host="127.0.0.1")
    assert Backends(**ok).channel.kind == "imitation", (
        "a loopback stand-in built directly was refused"
    )


def test_one_bad_host_among_several_refuses_the_kind(planted):
    two = {"fakes_host": "127.0.0.1", "second_host": "example.test"}
    assert (
        stand_in_host_problem("channel", "imitation", _Hosted(kind="imitation", **two)) is not None
    ), "one bad host among several was accepted"
    with pytest.raises(ConfigError, match="imitation"):
        planted("imitation", **two)
    assert planted("imitation", fakes_host="127.0.0.1", second_host="::1"), (
        "two loopback hosts refused"
    )


def test_a_real_kind_may_name_any_host(planted):
    refused = None
    try:
        planted("service", fakes_host="example.test")
    except ConfigError as exc:
        refused = exc
    assert refused is None, "a real kind was refused for its host"


def test_a_stand_in_that_lists_no_host_but_has_a_host_setting_is_refused(monkeypatch, planted):
    """An empty list passes `all(...)`: it must not. The kind has `fakes_host`, so an empty answer is a hole."""
    _plant(monkeypatch, "silent", Entry(_Hosted, "m:f", hosts=lambda s: [], role="stand_in"))
    with pytest.raises(
        ConfigError, match=r"backends.channel \(silent\): a stand-in with a setting that names"
    ):
        planted("silent", fakes_host="example.test")


def test_a_stand_in_with_no_hosts_function_is_refused_by_the_rule_itself(monkeypatch):
    entry = Entry(_Hosted, "m:f", role="stand_in")
    monkeypatch.setitem(TABLE["channel"], "bare", entry)
    problem = stand_in_host_problem("channel", "bare", _Hosted(kind="bare"))
    assert problem is not None and "must declare its hosts" in problem, (
        "a stand-in that declares no hosts was accepted"
    )


def test_a_hosts_function_that_raises_refuses_without_echoing_the_error(monkeypatch, planted):
    canary = "can" + "ary-" + "hosts-error"  # built from parts: not a real credential

    def broken(s):
        raise ValueError(canary)

    _plant(monkeypatch, "broken", Entry(_Hosted, "m:f", hosts=broken, role="stand_in"))
    with pytest.raises(
        ConfigError, match=r"backends.channel \(broken\): the hosts of this stand-in"
    ) as err:
        planted("broken")
    assert canary not in str(err.value), "the refusal echoes the error of the hosts function"


def test_a_kind_the_table_does_not_list_is_refused_not_a_key_error():
    problem = stand_in_host_problem("channel", "no_such_kind", KindSettings(kind="no_such_kind"))
    assert problem == "backends.channel: unknown kind; the kind table does not list it"


# --- the refusal text never shows a value ---------------------------------------------------------------------

CANARY = "can" + "ary-" + "s3cr3t"  # built from parts: not a real credential


def test_the_refusal_never_echoes_the_host_or_other_setting_values(planted):
    with pytest.raises(ConfigError) as err:
        planted("imitation", fakes_host=f"{CANARY}.example.test")
    assert CANARY not in str(err.value), "the refusal echoes a setting value"
    fields = _backends_with(planted, fakes_host=f"{CANARY}.example.test")
    with pytest.raises(ValidationError) as direct:
        Backends(**fields)
    assert CANARY not in str(direct.value), "a direct Backends refusal echoes a setting value"


def test_no_value_is_echoed_on_the_other_refusal_paths_of_the_loader(planted, tmp_path):
    """The loader's own refusals (a value of the wrong type, a plain-http model address with a user name and
    password, a system address with credentials in it) name the field and never the value."""
    cfg = planted.cfg_dir / "config.yaml"
    base = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    cases = [
        ("backends", "llm", {"kind": "fake", "recorded_dir": [CANARY]}),
        (
            "backends",
            "llm",
            {"kind": "openai_compat", "base_url": f"http://u:{CANARY}@remote.example.test/v1"},
        ),
        ("backends", "store", {"kind": "postgres", "sslmode": CANARY}),
        ("systems", "s", {"base_url": f"http://u:{CANARY}@remote.example.test/"}),
    ]
    for top, key, value in cases:
        data = yaml.safe_load(yaml.safe_dump(base))
        data.setdefault(top, {})[key] = value
        cfg.write_text(yaml.safe_dump(data), encoding="utf-8")
        with pytest.raises(Exception) as err:
            load_config(planted.cfg_dir)
        assert CANARY not in str(err.value), f"{top}.{key}: the refusal echoes a value"
    cfg.write_text(yaml.safe_dump(base), encoding="utf-8")


def test_a_stand_in_that_reaches_no_machine_is_not_touched(tmp_path):
    entry = TABLE["llm"]["fake"]
    assert entry.hosts is not None and entry.hosts(None) == [], "the fake model declares a host"
    assert (
        stand_in_host_problem("llm", "fake", entry.settings(kind="fake", recorded_dir=tmp_path))
        is None
    )


def test_the_rule_agrees_with_is_loopback_host_on_seeded_random_hosts(monkeypatch):
    rng = random.Random(20261112)  # noqa: S311 - a seeded test generator, not a secret
    pieces = [
        "127", "0", "1", "255", "localhost", "::1", ".", ":", "[", "]", "x", "10", "example.test",
        "%eth0", "",
    ]  # fmt: skip
    monkeypatch.setitem(
        TABLE["channel"], "imitation", Entry(_Hosted, "m:f", hosts=_hosts, role="stand_in")
    )
    seen = {True: 0, False: 0}
    for _ in range(2000):
        host = "".join(rng.choice(pieces) for _ in range(rng.randint(1, 5)))
        problem = stand_in_host_problem(
            "channel", "imitation", _Hosted(kind="imitation", fakes_host=host)
        )
        assert (problem is None) is is_loopback_host(host), (
            f"the rule disagrees with is_loopback_host on {host!r}"
        )
        seen[problem is None] += 1
    assert seen[True] > 20 and seen[False] > 20, f"the generator never reached a branch: {seen}"
