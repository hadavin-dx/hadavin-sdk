"""Settings: config validation, backend switch, prices rules, owner sentence (never cached), kill switch, temp-folder rule, timing check."""

from __future__ import annotations

import dataclasses
import json
import re
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from conftest import CAP_SENTENCE, CONSENT_SENTENCE, ROOT, settings_for_tests
from intake import settings
from intake.codes import ConfigError, Refused

N8N_HTTP_TIMEOUT_S = 300


def env(tmp_path, **kw):
    return {"HADAVIN_LOCAL": str(tmp_path), **kw}


def test_config_file_is_ascii_lf_only_and_example_domains():
    raw = (ROOT / "config" / "service.json").read_bytes()
    assert b"\r" not in raw and raw.isascii()
    domains = re.findall(rb"[\w.+-]+@([\w.-]+)", raw)
    assert domains and all(d.endswith(b".example.com") for d in domains)


def test_load_defaults(tmp_path):
    s = settings.load(env(tmp_path))
    assert s.backend == "fake" and s.tenant_id == "demo-intake"
    assert s.intake_home == tmp_path / "intake" and s.owner_sentence_path == tmp_path / "intake" / "owner_sentence.txt"
    assert s.spend_dir == tmp_path / "spend"
    assert (s.model.tier_read, s.model.tier_fallback) == ("claude-haiku-5-5", "claude-sonnet-5-5")
    assert s.model.api_host == "api.anthropic.com" and s.service.port == 8750 and s.service.currencies[0] == "USD"
    assert s.model.fake_replies_path.is_file()


def test_unset_local_is_exit_3_class():
    with pytest.raises(ConfigError) as ei:
        settings.load({})
    assert ei.value.code == "local_unset"
    with pytest.raises(ConfigError):
        settings.load({"HADAVIN_LOCAL": "   "})


def test_backend_switch(tmp_path):
    assert settings.load(env(tmp_path, INTAKE_MODEL_BACKEND="anthropic")).backend == "anthropic"
    assert settings.load(env(tmp_path, INTAKE_MODEL_BACKEND="")).backend == "fake"
    for bad in ("Fake", "openai", "anthropic ", "x"):
        with pytest.raises(ConfigError) as ei:
            settings.load(env(tmp_path, INTAKE_MODEL_BACKEND=bad))
        assert ei.value.code == "bad_backend"


def test_settings_is_frozen_and_holds_no_cap_or_secret(tmp_path):
    s = settings.load(env(tmp_path))
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.backend = "anthropic"  # type: ignore[misc]
    names = {f.name for f in dataclasses.fields(settings.Settings)}
    assert not {n for n in names if "cap" in n or "total" in n or "prices" == n or "key" in n}, names
    assert "owner_sentence_path" in names


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["model"].pop("tiers"),
        lambda d: d["model"].update(max_tokens=0),
        lambda d: d["model"].update(deadline_s=True),
        lambda d: d["service"].update(port=80),
        lambda d: d["service"].update(name_regex="("),
        lambda d: d["service"].update(currencies=["usd"]),
        lambda d: d["review"].update(reason_min_chars=600),
        lambda d: d["notify"].update(to="a@b.com"),
        lambda d: d.pop("review"),
    ],
)
def test_bad_config_is_refused(tmp_path, mutate):
    d = json.loads((ROOT / "config" / "service.json").read_text(encoding="utf-8"))
    mutate(d)
    p = tmp_path / "service.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    with pytest.raises(ConfigError) as ei:
        settings._parse_config(settings.read_config(p), ROOT)
    assert ei.value.code == "bad_config"


def test_unreadable_config_is_bad_config(tmp_path):
    (tmp_path / "service.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(ConfigError):
        settings.read_config(tmp_path / "service.json")


def write_prices(tmp_path, **over):
    d = {
        "prices_micro_usd_per_million_tokens": {"read": {"in": 1000000, "out": 5000000}, "fallback": {"in": 3000000, "out": 15000000}},
        "prices_as_of": date.today().isoformat(),
        "anthropic_version": "v",
    }
    d.update(over)
    p = tmp_path / "prices.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    return p


def test_committed_config_alone_has_no_prices(tmp_path):
    s = settings.load(env(tmp_path))
    assert not hasattr(s, "prices")  # Settings never caches prices or the date check: the budget re-reads the file on every reserve
    with pytest.raises(Refused) as ei:
        settings.load_prices(s.prices_path)  # no prices.json: every live reserve would be refused prices_missing
    assert ei.value.code == "prices_missing"
    assert "prices" not in (ROOT / "config" / "service.json").read_text(encoding="utf-8").replace("prices.json", "")


def test_prices_rules(tmp_path):
    today = date(2026, 11, 3)
    ok = write_prices(tmp_path, prices_as_of="2026-11-03")
    assert settings.load_prices(ok, today).read_out == 5000000
    cases = [
        {"prices_as_of": "2026-11-04"},  # future
        {"prices_as_of": "2026-10-03"},  # 31 days old
        {"prices_as_of": "garbage"},
        {"prices_micro_usd_per_million_tokens": {"read": {"in": 0, "out": 5}, "fallback": {"in": 1, "out": 1}}},
        {"prices_micro_usd_per_million_tokens": {"read": {"in": 1.5, "out": 5}, "fallback": {"in": 1, "out": 1}}},
        {"prices_micro_usd_per_million_tokens": {"read": {"in": True, "out": 5}, "fallback": {"in": 1, "out": 1}}},
        {"prices_micro_usd_per_million_tokens": {"read": {"in": 1}}},
    ]
    for over in cases:
        with pytest.raises(Refused) as ei:
            settings.load_prices(write_prices(tmp_path, **{"prices_as_of": "2026-11-03", **over}), today)
        assert ei.value.code == "prices_missing", over
    assert settings.load_prices(write_prices(tmp_path, prices_as_of="2026-10-04"), today)  # exactly 30 days is fine
    with pytest.raises(Refused):
        settings.load_prices(tmp_path / "nope.json", today)
    (tmp_path / "bad.json").write_text("[1", encoding="utf-8")
    with pytest.raises(Refused):
        settings.load_prices(tmp_path / "bad.json", today)


def test_kill_switch_is_read_from_raw_policy_every_call_and_fails_closed(monkeypatch, tmp_path):
    assert settings.read_kill_switch() is False  # the shipped policy
    seen = []

    def fake_policy():
        return seen[-1]

    monkeypatch.setattr(settings, "_raw_policy", fake_policy)
    for raw, expected in [
        ({"executor": {"kill_switch": False}}, False),
        ({"executor": {"kill_switch": True}}, True),
        ({"executor": {"kill_switch": "false"}}, True),
        ({"executor": {"kill_switch": 0}}, True),
        ({"executor": {}}, True),
        ({}, True),
        ({"executor": None}, True),
    ]:
        seen.append(raw)
        assert settings.read_kill_switch() is expected, raw  # same process, value changes between calls: not cached


def test_tenant_comes_from_policy_client_id():
    assert (
        settings.read_tenant_id() == json.loads((ROOT / "config" / "policy.json").read_text(encoding="utf-8"))["client_id"] == "demo-intake"
    )


def test_fake_backend_only_in_a_temporary_folder(tmp_path):
    s = settings.load(env(tmp_path))
    settings.require_safe_backend(s)  # tmp_path is under the temporary folder
    real = settings.load({"HADAVIN_LOCAL": str(Path.home() / "intake-real-folder-test"), "INTAKE_MODEL_BACKEND": "fake"})
    with pytest.raises(Refused) as ei:
        settings.require_safe_backend(real)
    assert ei.value.code == "fake_on_real_folder"
    settings.require_safe_backend(dataclasses.replace(real, backend="anthropic"))  # the live backend has its own checks
    assert not settings.under_temp_folder(Path(tempfile.gettempdir()).parent / "elsewhere")
    assert not settings.under_temp_folder(Path(tempfile.gettempdir()) / ".." / "elsewhere")  # a traversal does not count


def test_timing_check_worst_scan_is_below_the_n8n_http_timeout(tmp_path):
    s = settings.load(env(tmp_path))
    assert s.service.scan_max_files * 2 * s.model.deadline_s == 120 < N8N_HTTP_TIMEOUT_S


def test_name_rule():
    rx = json.loads((ROOT / "config" / "service.json").read_text(encoding="utf-8"))["service"]["name_regex"]
    for good in ("inv-A.txt", "a", "A" * 128, "x.y.z.txt", "CONSULT.txt", "COMX.txt"):
        assert settings.is_name_allowed(good, rx), good
    for bad in (
        ".hidden.txt",
        "-lead.txt",
        "A" * 129,
        "a b.txt",
        "a\n",
        "a/b.txt",
        "CON.txt",
        "nul.txt",
        "Com1.pdf",
        "LPT9",
        "aux.tar.txt",
        "é.txt",
        "",
    ):
        assert not settings.is_name_allowed(bad, rx), bad


def test_settings_for_tests_gives_prices_consent_and_hashes(tmp_path):
    s = settings_for_tests(tmp_path)
    p = settings.load_prices(s.prices_path)
    assert p.read_in > 0 and p.fallback_out > 0
    text = s.owner_sentence_path.read_text(encoding="utf-8")
    assert CONSENT_SENTENCE in text and CAP_SENTENCE in text
    assert (s.intake_home / "synthetic_hashes.txt").read_text().count("\n") == 4
    settings.require_safe_backend(s)
    assert p.as_of <= date.today() + timedelta(days=1)


def test_kill_switch_fails_closed_inside_the_function_when_the_policy_cannot_be_read(monkeypatch):
    def broken():
        raise ConfigError("bad_config", "policy.json unreadable")

    monkeypatch.setattr(settings, "_raw_policy", broken)
    assert settings.read_kill_switch() is True  # engaged, and no exception reaches the caller


def test_prices_age_rule_uses_the_named_clock_seam(tmp_path):
    p = write_prices(tmp_path, prices_as_of="2026-11-03")
    day = {"now": date(2026, 11, 3)}
    assert settings.load_prices(p, clock=lambda: day["now"]).as_of == date(2026, 11, 3)
    day["now"] = date(2026, 12, 4)  # 31 days later, same process, same file: refused on the next call
    with pytest.raises(Refused) as ei:
        settings.load_prices(p, clock=lambda: day["now"])
    assert ei.value.code == "prices_missing"
    assert callable(settings.utc_today) and isinstance(settings.utc_today(), date)


@pytest.mark.parametrize(
    "shape", ["20261103", "2026-1-3", "2026-11-03T00:00:00", "2026-11-03 ", " 2026-11-03", "\uff12026-11-03", "2026-W45-2"]
)
def test_prices_date_is_strict_yyyy_mm_dd(tmp_path, shape):
    with pytest.raises(Refused):
        settings.load_prices(write_prices(tmp_path, prices_as_of=shape), date(2026, 11, 3))


def test_relative_hadavin_local_is_rejected():
    with pytest.raises(ConfigError) as ei:
        settings.load({"HADAVIN_LOCAL": "relative/folder"})
    assert ei.value.code == "bad_config"


def test_hash_list_loader_rules(tmp_path):
    h = tmp_path / "h.txt"
    assert settings.load_hash_list(h) == frozenset()  # missing = empty (STOP)
    good, other = "0" * 63 + "a", "f" * 64
    h.write_text(f"\n{good}\n{good}\n  {other}  \nNOTHEX\n{'A' * 64}\n{'a' * 65}\n", encoding="utf-8")
    assert settings.load_hash_list(h) == frozenset({good, other})  # blank, junk, upper-case and over-long lines are ignored
    h.write_bytes(b"\xff\xfe")
    assert settings.load_hash_list(h) == frozenset()


def test_only_the_backend_factory_may_call_require_safe_backend():
    import ast

    from conftest import ROOT

    allowed = {"src/intake/model.py", "src/intake/settings.py"}  # model.py arrives with WP1
    bad = []
    for p in sorted((ROOT / "src" / "intake").rglob("*.py")) + sorted((ROOT / "tools").rglob("*.py")):
        rel = p.relative_to(ROOT).as_posix()
        if rel in allowed or "__pycache__" in p.parts:
            continue
        if any(
            isinstance(n, (ast.Attribute, ast.Name)) and getattr(n, "attr", getattr(n, "id", "")) == "require_safe_backend"
            for n in ast.walk(ast.parse(p.read_text(encoding="utf-8")))
        ):
            bad.append(rel)
    assert not bad, bad


@pytest.mark.parametrize("top", ["[]", "0", '"x"', "null", "true", "[1, 2]"])
def test_a_non_object_policy_is_a_config_error_and_an_engaged_switch(monkeypatch, tmp_path, top):
    monkeypatch.setattr(settings, "CONFIG", tmp_path)
    (tmp_path / "policy.json").write_text(top, encoding="utf-8")
    with pytest.raises(ConfigError) as ei:
        settings._raw_policy()
    assert ei.value.code == "bad_config"
    assert settings.read_kill_switch() is True
    with pytest.raises(ConfigError):
        settings.read_tenant_id()


@pytest.mark.parametrize("exc", [RuntimeError("x"), TypeError("x"), AttributeError("x"), KeyError("x"), RecursionError()])
def test_read_kill_switch_never_raises(monkeypatch, exc):
    def boom():
        raise exc

    monkeypatch.setattr(settings, "_raw_policy", boom)
    assert settings.read_kill_switch() is True


def test_load_prices_follows_a_monkeypatched_clock_seam(tmp_path, monkeypatch):
    p = write_prices(tmp_path, prices_as_of="2026-11-03")
    monkeypatch.setattr(settings, "utc_today", lambda: date(2026, 11, 3))
    assert settings.load_prices(p).as_of == date(2026, 11, 3)
    monkeypatch.setattr(settings, "utc_today", lambda: date(2026, 12, 4))  # the default is looked up at call time, not bound at definition
    with pytest.raises(Refused) as ei:
        settings.load_prices(p)
    assert ei.value.code == "prices_missing"


def test_anthropic_version_is_optional_for_other_providers(tmp_path):
    p = write_prices(tmp_path, prices_as_of="2026-11-03")
    import json as _j

    d = _j.loads(p.read_text(encoding="utf-8"))
    del d["anthropic_version"]
    p.write_text(_j.dumps(d), encoding="utf-8")
    assert settings.load_prices(p, date(2026, 11, 3)).anthropic_version == ""
    d["anthropic_version"] = 5
    p.write_text(_j.dumps(d), encoding="utf-8")
    with pytest.raises(Refused):
        settings.load_prices(p, date(2026, 11, 3))


def test_the_example_domain_rule_is_a_demo_flag_in_the_config():
    d = json.loads((ROOT / "config" / "service.json").read_text(encoding="utf-8"))
    assert d["notify"]["require_example_domain"] is True
    d["notify"]["to"] = "a@client.test"
    with pytest.raises(ConfigError):
        settings._parse_config(d, ROOT)
    d["notify"]["require_example_domain"] = False
    settings._parse_config(d, ROOT)  # a client build turns the demo rule off
    d["notify"]["require_example_domain"] = "no"
    with pytest.raises(ConfigError):
        settings._parse_config(d, ROOT)
    d["notify"]["require_example_domain"] = False
    d["notify"]["to"] = "not-an-address"
    with pytest.raises(ConfigError):
        settings._parse_config(d, ROOT)


def test_max_lines_has_one_source_the_policy_file():
    from intake import validators

    assert validators.MAX_LINES == settings.read_policy_value("max_lines_per_draft") == rules_policy_lines()
    with pytest.raises(ConfigError):
        settings.read_policy_value("no_such_key")


def rules_policy_lines() -> int:
    from intake import rules

    return rules.load_policy().max_lines_per_draft


@pytest.mark.parametrize("version,ok", [("", False), ("   ", False), ("\t", False), ("2099-01-01", True), ("v1", True)])
def test_require_anthropic_version(version, ok):
    p = settings.Prices(1, 1, 1, 1, date(2026, 11, 3), version)
    if ok:
        assert settings.require_anthropic_version(p) == version
    else:
        with pytest.raises(Refused) as ei:
            settings.require_anthropic_version(p)
        assert ei.value.code == "prices_missing"
    with pytest.raises(Refused):
        settings.require_anthropic_version(settings.Prices(1, 1, 1, 1, date(2026, 11, 3), None))  # type: ignore[arg-type]
