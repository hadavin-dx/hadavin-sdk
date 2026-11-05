"""DF5 cost controls, settings side (package A2): the new ``model`` keys of ``config/service.json``, the accessors for the review page, ``purpose``, and
the rule that the vendor's request keys appear only in ``model_anthropic.py``."""

from __future__ import annotations

import ast
import copy
import json

import pytest

from conftest import ROOT, settings_for_tests
from intake import settings as cfg
from intake.codes import ConfigError

SRC = ROOT / "src" / "intake"


def parse(**model_changes):
    data = copy.deepcopy(cfg.read_config())
    for k, v in model_changes.items():
        if v is cfg_missing:
            data["model"].pop(k, None)
        else:
            data["model"][k] = v
    return cfg._parse_config(data, ROOT)[0]  # noqa: SLF001


cfg_missing = object()


def refused(**model_changes) -> str | None:
    """The ConfigError code, or None when the config was accepted (an assertion on it fails by value, never by an exception)."""
    try:
        parse(**model_changes)
    except ConfigError as e:
        return e.code
    except Exception as e:  # noqa: BLE001 (a crash is reported by name, so the caller's assertion fails by value)
        return f"crash:{type(e).__name__}"
    return None


def accepted(**model_changes):
    """The parsed ModelConfig, or None when it was refused."""
    try:
        return parse(**model_changes)
    except ConfigError:
        return None


def attr(obj, name):
    return getattr(obj, name, "attribute missing")


def test_the_committed_config_parses_to_the_df5_defaults():
    m = parse()
    assert (m.tier_read, m.tier_fallback) == ("claude-sonnet-5-5", "claude-sonnet-5-5")
    assert (attr(m, "fallback_wait_s"), attr(m, "fallback_wait_max_s"), attr(m, "strict_tool")) == (2, 10, False)
    assert (attr(m, "approved_read_models"), attr(m, "stronger_than_read")) == (("claude-sonnet-5-5",), ())
    assert attr(m, "display_names") == {"claude-sonnet-5-5": "Claude Sonnet 5.5"}
    assert set(m.extra_body) == {"read", "fallback"}


def test_the_wait_keys_have_defaults_ranges_and_an_order():
    m = parse(fallback_wait_s=cfg_missing, fallback_wait_max_s=cfg_missing)
    assert (attr(m, "fallback_wait_s"), attr(m, "fallback_wait_max_s")) == (2, 10)
    assert attr(accepted(fallback_wait_s=0, fallback_wait_max_s=0), "fallback_wait_max_s") == 0
    assert attr(accepted(fallback_wait_s=30, fallback_wait_max_s=60), "fallback_wait_s") == 30
    for bad in (-1, 31, True, 1.5, "2", None):
        assert refused(fallback_wait_s=bad) == "bad_config"
    for bad in (-1, 61, True, "10"):
        assert refused(fallback_wait_max_s=bad) == "bad_config"
    assert refused(fallback_wait_s=11, fallback_wait_max_s=10) == "bad_config"  # wait above its own cap


def test_send_temperature_is_removed_and_refused():
    for v in (None, 0, 1):
        assert refused(send_temperature=v) == "bad_config"
    assert "send_temperature" not in cfg.read_config()["model"]


def test_strict_tool_must_be_a_real_boolean():
    assert attr(accepted(strict_tool=True), "strict_tool") is True
    for bad in (1, "true", None, 0):
        assert refused(strict_tool=bad) == "bad_config"


def test_read_model_must_be_approved():
    assert refused(tiers={"read": "claude-haiku-5-5", "fallback": "claude-haiku-5-5"}) == "bad_config"
    assert refused(tiers={"read": "claude-opus-5-5", "fallback": "claude-opus-5-5"}) == "bad_config"
    m = accepted(
        tiers={"read": "claude-opus-5-5", "fallback": "claude-opus-5-5"},
        approved_read_models=["claude-opus-5-5"],
        extra_body={"read": {}, "fallback": {}},
        display_names={},
    )
    assert attr(m, "tier_read") == "claude-opus-5-5"


def test_fallback_model_must_be_same_or_listed_stronger():
    other = {"read": "claude-sonnet-5-5", "fallback": "claude-opus-5-5"}
    assert refused(tiers=other) == "bad_config"
    assert attr(accepted(tiers=other, stronger_than_read=["claude-opus-5-5"]), "tier_fallback") == "claude-opus-5-5"
    weaker = {"read": "claude-sonnet-5-5", "fallback": "claude-haiku-5-5"}
    assert refused(tiers=weaker) == "bad_config"


@pytest.mark.parametrize("key", ["approved_read_models", "stronger_than_read"])
def test_model_id_lists_are_checked(key):
    ok = ["claude-sonnet-5-5"] if key == "approved_read_models" else []
    assert attr(accepted(**{key: ok}), key) == tuple(ok)
    for bad in ("claude-sonnet-5-5", [1], ["bad id"], ["x" * 101], ["claude-sonnet-5-5"] * 9, [""], {"a": 1}):
        assert refused(**{key: bad}) == "bad_config"
    nine = [f"m{i}" for i in range(8)]
    assert len(attr(accepted(**{key: ["claude-sonnet-5-5", *nine[:7]]}), key)) == 8  # eight entries are allowed


def test_display_names_are_checked():
    assert attr(accepted(display_names={}), "display_names") == {}
    for bad in (
        [],
        {"bad id": "x"},
        {"claude-sonnet-5-5": ""},
        {"claude-sonnet-5-5": "x" * 61},
        {"claude-sonnet-5-5": "<b>x</b>"},
        {"claude-sonnet-5-5": 'say "hi"'},
        {"claude-sonnet-5-5": "a&b"},
        {"claude-sonnet-5-5": "it's"},
        {"claude-sonnet-5-5": "line\nbreak"},
        {"claude-sonnet-5-5": 5},
    ):
        assert refused(display_names=bad) == "bad_config"
    long = "Sonnet " + "x" * 53
    assert attr(accepted(display_names={"claude-sonnet-5-5": long}), "display_names") == {"claude-sonnet-5-5": long}


def _config_file(tmp_path, **model_changes):
    data = copy.deepcopy(cfg.read_config())
    data["model"].update(model_changes)
    p = tmp_path / "service.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_read_model_id_and_display_name_accessors(tmp_path):
    read_model_id = getattr(cfg, "read_model_id", lambda path=None: "function missing")
    display_name = getattr(cfg, "display_name", lambda model_id, path=None: "function missing")
    assert read_model_id() == "claude-sonnet-5-5" and display_name("claude-sonnet-5-5") == "Claude Sonnet 5.5"
    p = _config_file(tmp_path, display_names={"claude-sonnet-5-5": "Sonnet Reader One"})
    assert display_name("claude-sonnet-5-5", p) == "Sonnet Reader One"
    assert display_name("claude-unknown-9", p) == "claude-unknown-9"  # unknown id: shown as the id
    assert display_name("claude-sonnet-5-5", tmp_path / "missing.json") == "claude-sonnet-5-5"  # any failure: the id, never an exception
    bad = _config_file(tmp_path, display_names=[1])
    assert display_name("claude-sonnet-5-5", bad) == "claude-sonnet-5-5"
    assert read_model_id(_config_file(tmp_path)) == "claude-sonnet-5-5"
    with pytest.raises(ConfigError):
        read_model_id(tmp_path / "missing.json")


def test_purpose_default_other_and_bad_value_refused(tmp_path):
    s = settings_for_tests(tmp_path)
    assert attr(s, "purpose") == "other"
    env = {"HADAVIN_LOCAL": str(s.local), "INTAKE_MODEL_BACKEND": "fake"}
    for good in ("calibration", "eval", "demo", "other"):
        assert attr(cfg.load({**env, "INTAKE_PURPOSE": good}), "purpose") == good
    assert attr(cfg.load({**env, "INTAKE_PURPOSE": ""}), "purpose") == "other"
    for bad in ("Demo", "production", "demo ", "x" * 50):
        try:
            cfg.load({**env, "INTAKE_PURPOSE": bad})
            code = None
        except ConfigError as e:
            code = e.code
        assert code == "bad_config", bad


def test_vendor_keys_only_in_model_anthropic():
    """The provider's request keys are string literals in ``model_anthropic.py`` only (a second backend has its own)."""
    names = {"thinking", "tool_choice", "strict", "disable_parallel_tool_use", "between_tools"}
    hits = []
    for p in sorted(SRC.rglob("*.py")):
        if p.name == "model_anthropic.py" or "core_copy" in p.parts:
            continue
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in names:
                hits.append((p.name, node.lineno, node.value))
    assert hits == []
    ma = (SRC / "model_anthropic.py").read_text(encoding="utf-8")
    assert '"tool_choice"' in ma and '"thinking"' in ma and '"strict"' in ma  # the scan is not vacuous


# ---- A12 fix batch: fail-closed model lists, display names, accessors, vendor words ------------------------------------------------------------
@pytest.mark.parametrize("value", [cfg_missing, None])
def test_approved_read_models_absent_or_null_is_refused(value):  # FAIL-BEFORE: the old code silently approved the Sonnet id
    assert refused(approved_read_models=value) == "bad_config"


def test_approved_read_models_empty_list_refuses_every_read_model():
    assert refused(approved_read_models=[]) == "bad_config"  # tiers.read is not in an empty list


@pytest.mark.parametrize("name", ["Reader {x}", "Reader " + chr(92) + " x", "100% model", "Reader\x07", "Reader <b>", 'Say "hi"'])
def test_display_names_refuse_braces_backslash_percent_and_unprintable(name):  # FAIL-BEFORE for { } \ %
    assert refused(display_names={"claude-sonnet-5-5": name}) == "bad_config"


@pytest.mark.parametrize(
    "model_id,label,bad",
    [
        ("claude-sonnet-5-5", "Claude Opus 5.5", True),
        ("claude-haiku-5-5", "Sonnet reader", True),
        ("claude-sonnet-5-5", "Claude Sonnet 5.5", False),
        ("claude-sonnet-5-5", "Sonnet invoice reader", False),
        ("claude-sonnet-5-5", "Claude Sonnet Opus", True),  # two families in one label
    ],
)
def test_a_display_name_may_not_name_another_model_family(model_id, label, bad):  # FAIL-BEFORE: no consistency check
    code = refused(display_names={model_id: label}) if bad else None
    if bad:
        assert code == "bad_config"
    else:
        assert refused(display_names={model_id: label}) is None


def test_accessors_use_the_loaded_settings_and_never_read_the_file(tmp_path, monkeypatch):  # FAIL-BEFORE: no settings parameter
    s = settings_for_tests(tmp_path)
    monkeypatch.setattr(cfg, "read_config", lambda path=None: (_ for _ in ()).throw(AssertionError("second file read")))
    assert cfg.read_model_id(settings=s) == s.model.tier_read
    assert cfg.display_name(s.model.tier_read, settings=s) == s.model.display_names.get(s.model.tier_read, s.model.tier_read)


def test_display_name_returns_the_id_for_a_broken_settings_object():
    class Broken:
        model = None

    assert cfg.display_name("claude-sonnet-5-5", settings=Broken()) == "claude-sonnet-5-5"  # AttributeError caught


def _vendor_hits(tree: ast.AST, names: set[str], model_prefix: str) -> list[str]:
    """Every way the vendor words can appear in code: a string constant, a piece of an f-string, a keyword argument name (also in dict(...)), a
    concatenation of constants, the vendor model id."""
    hits: list[str] = []

    def text_of(n: ast.AST) -> str | None:
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            return n.value
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
            a, b = text_of(n.left), text_of(n.right)
            return a + b if a is not None and b is not None else None
        if isinstance(n, ast.JoinedStr):
            return "".join(v.value for v in n.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
        return None

    for n in ast.walk(tree):
        t = text_of(n)
        if t is not None and (t in names or model_prefix in t):
            hits.append(t)
        if isinstance(n, ast.keyword) and n.arg in names - {"strict"}:  # zip(strict=True) is Python, not the vendor
            hits.append(f"kw:{n.arg}")
        if isinstance(n, ast.JoinedStr):  # an f-string part on its own
            for v in n.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str) and (v.value in names or model_prefix in v.value):
                    hits.append(v.value)
    return hits


def test_vendor_words_and_model_ids_only_in_model_anthropic():  # FAIL-BEFORE: the old scan saw plain constants only and settings.py held the vendor id twice
    names = {"thinking", "tool_choice", "strict", "disable_parallel_tool_use", "between_tools", "cache_control"}
    found = {}
    for p in sorted(SRC.rglob("*.py")):
        if p.name == "model_anthropic.py" or "core_copy" in p.parts:
            continue
        h = _vendor_hits(ast.parse(p.read_text(encoding="utf-8")), names, "claude-")
        if h:
            found[p.name] = h
    assert found == {}


@pytest.mark.parametrize(
    "code",
    [
        "x = dict(thinking=1)",
        'x = f"claude-{v}"',
        'x = "tool" + "_choice"',
        'x = "claude-" "sonnet"',
        "f(tool_choice=1)",
        'x = {"between_tools": 1}',
    ],
)
def test_the_vendor_scan_sees_every_spelling(code):  # the scan itself: it must catch the shapes the old one missed
    assert _vendor_hits(ast.parse(code), {"thinking", "tool_choice", "strict", "between_tools"}, "claude-") != []


# ---- A12 batch 3 ---------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["Claude Sonnet 5.5", "Sonnet reader (primary) - v2"])
def test_good_display_names_are_accepted(name):
    assert refused(display_names={"claude-sonnet-5-5": name}) is None


@pytest.mark.parametrize("name", ["Sоnnеt", "Reader​", "Reader;", "Reader/x", "Reader,x", "x" * 61, ""])
def test_display_names_are_ascii_letters_digits_and_a_few_marks_only(name):  # FAIL-BEFORE: homoglyphs and zero-width characters passed
    assert refused(display_names={"claude-sonnet-5-5": name}) == "bad_config"


def test_a_label_must_name_the_same_family_as_its_id():
    assert refused(display_names={"claude-sonnet-5-5": "Invoice reader"}) == "bad_config"  # the id names a family, the label must too
    assert refused(display_names={"claude-sonnet-5-5": "Opus reader"}) == "bad_config"
    assert refused(display_names={"claude-sonnet-5-5": "Sonnet reader"}) is None


def test_display_names_may_only_name_configured_models():  # FAIL-BEFORE: any well-formed id was accepted
    assert refused(display_names={"claude-unknown-9": "Reader"}) == "bad_config"
    assert refused(display_names={"claude-sonnet-5-5": "Sonnet Reader"}) is None


def test_an_old_service_json_without_approved_read_models_prints_the_error_and_no_traceback(tmp_path, monkeypatch, capsys):
    import shutil

    from intake import cli

    cfg_dir = tmp_path / "config"
    shutil.copytree(ROOT / "config", cfg_dir)
    data = json.loads((cfg_dir / "service.json").read_text(encoding="utf-8"))
    del data["model"]["approved_read_models"]
    (cfg_dir / "service.json").write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(cfg, "CONFIG", cfg_dir)
    monkeypatch.setenv("HADAVIN_LOCAL", str(tmp_path / "local"))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "fake")
    rc = cli.main(["check"])
    err = capsys.readouterr().err
    assert rc != 0 and "approved_read_models" in err and "Traceback" not in err


def test_check_prints_the_read_model_from_the_loaded_settings(tmp_path, capsys):
    from intake import cli

    s = settings_for_tests(tmp_path, with_ledger=True)
    cli.COMMANDS["check"](s, None)
    assert "read_model: Claude Sonnet 5.5 (claude-sonnet-5-5)" in capsys.readouterr().out
