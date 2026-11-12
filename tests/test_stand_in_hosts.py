"""A stand-in kind may only be reached on this computer, and the config refuses anything else at load.

No stand-in kind in the table names a host today (the fake model, store and channel are in-process), so these tests
plant one: a stand-in channel with a `fakes_host` setting, a real channel with the same setting, and check both.
"""

from __future__ import annotations

import random

import pytest
import yaml

from hadavin_sdk.backends.table import DEMO_ONLY, TABLE, Entry, KindSettings
from hadavin_sdk.config import ConfigError, load_config, stand_in_host_problem
from hadavin_sdk.netguard import is_loopback_host
from tests.conftest import make_cfg


class _Hosted(KindSettings):
    fakes_host: str = "127.0.0.1"
    second_host: str | None = None


def _hosts(s: _Hosted) -> list[str]:
    return [s.fakes_host] + ([s.second_host] if s.second_host is not None else [])


@pytest.fixture
def planted(monkeypatch, tmp_path):
    cfg_dir = make_cfg(
        tmp_path
    )  # not the conftest fixture: the mutant runner runs with no conftest
    """A stand-in channel kind `imitation` and a real channel kind `service`, both with host settings."""
    monkeypatch.setitem(
        TABLE["channel"],
        "imitation",
        Entry(_Hosted, "m:f", hosts=_hosts, role="stand_in"),
    )
    monkeypatch.setitem(
        TABLE["channel"], "service", Entry(_Hosted, "m:f", hosts=_hosts, role="real")
    )
    monkeypatch.setattr("hadavin_sdk.config.DEMO_ONLY", DEMO_ONLY | {("channel", "imitation")})

    def use(kind: str, **settings):
        path = cfg_dir / "config.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["backends"]["channel"] = {"kind": kind, **settings}
        path.write_text(yaml.safe_dump(data), encoding="utf-8")
        return load_config(cfg_dir)

    return use


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


def test_one_bad_host_among_several_refuses_the_kind(planted):
    with pytest.raises(ConfigError, match="imitation"):
        planted("imitation", fakes_host="127.0.0.1", second_host="example.test")
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


def test_the_refusal_never_echoes_the_host_or_other_setting_values(planted):
    secret_shaped = "tok" + "-" + "abc123"  # built from parts: not a real credential
    with pytest.raises(ConfigError) as err:
        planted("imitation", fakes_host=f"{secret_shaped}.example.test")
    assert secret_shaped not in str(err.value), "the refusal echoes a setting value"


def test_a_stand_in_without_a_host_is_not_touched(tmp_path):
    assert TABLE["llm"]["fake"].hosts is None
    assert (
        stand_in_host_problem(
            "llm", "fake", TABLE["llm"]["fake"].settings(kind="fake", recorded_dir=tmp_path)
        )
        is None
    )


def test_the_rule_agrees_with_is_loopback_host_on_seeded_random_hosts():
    rng = random.Random(20261112)  # noqa: S311 - a seeded test generator, not a secret
    pieces = [
        "127",
        "0",
        "1",
        "255",
        "localhost",
        "::1",
        ".",
        ":",
        "[",
        "]",
        "x",
        "10",
        "example.test",
        "%eth0",
        "",
    ]
    entry = Entry(_Hosted, "m:f", hosts=_hosts, role="stand_in")
    original = TABLE["channel"].get("imitation")
    TABLE["channel"]["imitation"] = entry
    try:
        for _ in range(2000):
            host = "".join(rng.choice(pieces) for _ in range(rng.randint(1, 5)))
            problem = stand_in_host_problem(
                "channel", "imitation", _Hosted(kind="imitation", fakes_host=host)
            )
            assert (problem is None) is is_loopback_host(host), (
                f"the rule disagrees with is_loopback_host on {host!r}"
            )
    finally:
        if original is None:
            del TABLE["channel"]["imitation"]
        else:
            TABLE["channel"]["imitation"] = original
