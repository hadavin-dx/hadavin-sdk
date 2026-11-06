"""The stages are exactly demo, pilot and prod. The old first stage name is refused, never read as a stage, and a
class test keeps the old word out of every place that names a stage.

No stage is stored anywhere today, so there is no read site to test. The first change that stores one must map an old
value to demo on read for display only (never for a guard decision) and add a test through that real read site.

Rows: unknown stage and half-renamed flag refuse start; the class test looks at stage POSITIONS only; pilot and prod
refuse relaxed kinds; the live guards fail closed on a value that is not a stage.
"""

import re
import typing
import unicodedata
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from hadavin_sdk import app as app_mod
from hadavin_sdk import config as config_mod
from hadavin_sdk import deferred
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.app import build
from hadavin_sdk.backends import table
from hadavin_sdk.config import STAGES, Config, ConfigError, is_live, load_config
from hadavin_sdk.registry import _module_pin_problems, load_registry
from tests.conftest import make_cfg, qualify

# The old word is built from parts in this file: the class test never scans this file, but a grep for it should find
# only the places that matter.
OLD = "d" + "ev"
RENAMED = (
    "environment: "
    + OLD
    + " was renamed to demo; write environment: demo (allowed values: demo, pilot, prod)"
)
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def cfg_dir(tmp_path):
    """A copy of the fixture config. Defined here, not taken from conftest, because the mutation runner runs with --noconftest."""
    return make_cfg(tmp_path)


def _edit(cfg_dir, fn):
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _set_env(cfg_dir, value):
    _edit(cfg_dir, lambda d: d.update(environment=value))


# --- the stage set -------------------------------------------------------------------------------------------------


def test_the_stages_are_exactly_demo_pilot_prod(tmp_path):
    assert STAGES == ("demo", "pilot", "prod")
    # the field's allowed values are the same tuple, not a second copy that can drift
    assert typing.get_args(Config.model_fields["environment"].annotation) == STAGES
    # the one place that decides "live": only exactly the first stage is relaxed, anything else is live
    assert [is_live(s) for s in STAGES] == [False, True, True], "is_live is wrong for a stage"
    assert all(is_live(v) for v in ("stag" + "ing", "Demo", OLD, "", None)), (
        "is_live is wrong for a value that is not a stage"
    )
    assert not hasattr(deferred, "LIVE"), (
        "an allowlist of live stages is back: a new value would count as not live"
    )
    try:
        demo_sites = _live_by_site(tmp_path / "a", "demo")
    except (
        ConfigError
    ) as exc:  # a guard that treats demo as live refuses the demo config while it loads
        raise AssertionError(
            f"demo is not live, but a guard refused it as live: {exc}"[:200]
        ) from None
    assert demo_sites == {
        "registry": False,
        "deferred": False,
        "app": False,
    }, "demo is not live"
    for stage in ("pilot", "prod"):
        assert _live_by_site(tmp_path / stage, stage) == {
            "registry": True,
            "deferred": True,
            "app": True,
        }, f"{stage} is live"


def test_dev_is_refused_with_the_rename(cfg_dir):
    _set_env(cfg_dir, OLD)
    with pytest.raises(ConfigError) as via_load:
        load_config(cfg_dir)
    assert RENAMED in str(via_load.value), "the refusal does not name the rename"
    # a reader sees that one sentence and nothing of pydantic's wrapper around it
    assert str(via_load.value) == RENAMED, (
        "pydantic's wrapper is visible around the rename sentence"
    )
    # direct construction gets the same text
    loaded = load_config(make_cfg(cfg_dir.parent / "again"))
    fields = {name: getattr(loaded, name) for name in type(loaded).model_fields}
    with pytest.raises(ValueError) as direct:
        Config(**{**fields, "environment": OLD})
    assert RENAMED in str(direct.value), "the refusal does not name the rename"


INEXACT = [
    "Demo",
    "DEMO",
    " demo",
    "demo ",
    "demo-eu",
    "uat",
    "staging",
    "development",
    "test",
    "",
    "stage",
    # the old word in other spellings: refused by the allowed-values rule, like any other non-stage
    "Dev",
    "DEV",
    " dev",
    "dev\n",
    # six look-alikes and invisible characters, built from code points (no literal look-alike in this file); the
    # allowed-values rule in pydantic refuses the rest of the family, so these are the ones a "tidy" step would let in
    "d" + chr(0x0435) + "mo",  # Cyrillic small ie in place of e
    "".join(chr(0xFF00 + ord(c) - 0x20) for c in "demo"),  # fullwidth demo (NFKC gives demo)
    "de" + chr(0x200B) + "mo",  # zero-width space inside
    "demo" + chr(0x00A0),  # no-break space (NFKC gives a plain space)
    chr(0x217E) + "emo",  # small roman numeral five hundred (NFKC gives d)
    "demo" + chr(0x0301),  # demo plus a combining accent
    "demo\n",
    "~",
    "null",
    "None",
]


def test_values_are_compared_exactly_never_normalised(cfg_dir):
    """Case, spaces, a prefix such as demo-eu, and a project label (uat) are not the stage."""
    for value in INEXACT:
        _set_env(cfg_dir, value)
        try:
            cfg = load_config(cfg_dir)
        except ConfigError as exc:
            assert "environment" in str(exc), f"{value!r}: refused for another reason"
        else:
            raise AssertionError(
                f"a stage that is not exactly demo, pilot or prod was accepted: {value!r} -> {cfg.environment}"
            )


@pytest.mark.parametrize("value", [None, 0, 1.5, True, ["demo"], {"demo": 1}])
def test_a_stage_that_is_not_a_string_is_refused(cfg_dir, value):
    _set_env(cfg_dir, value)
    with pytest.raises(ConfigError, match="environment"):
        load_config(cfg_dir)


def test_a_missing_stage_is_refused(cfg_dir):
    _edit(cfg_dir, lambda d: d.pop("environment"))
    with pytest.raises(ConfigError, match="environment"):
        load_config(cfg_dir)


@pytest.mark.parametrize("raw", ["~", "null", "Null", "NULL", ""])
def test_a_yaml_null_stage_is_refused(cfg_dir, raw):
    """`environment: ~` (and the other YAML spellings of null, and a bare key) reads as None: refused, never a default."""
    path = cfg_dir / "config.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("environment: demo", f"environment: {raw}"), encoding="utf-8")
    assert f"environment: {raw}" in path.read_text(encoding="utf-8")
    with pytest.raises(ConfigError, match="environment"):
        load_config(cfg_dir)


def test_the_look_alike_strings_are_what_the_list_says_they_are():
    """The NFKC-equivalent entries really do become demo after NFKC, casefold and strip, so a program that tidied the
    value that way would accept them: they are in the list to stop exactly that."""

    def tidy(value):
        return unicodedata.normalize("NFKC", value).casefold().strip()

    tidy_to_demo = [v for v in INEXACT if tidy(v) == "demo"]
    assert len(tidy_to_demo) >= 6, tidy_to_demo
    for must in (
        "".join(chr(0xFF00 + ord(c) - 0x20) for c in "demo"),
        "demo" + chr(0x00A0),
        chr(0x217E) + "emo",
        "DEMO",
        "demo\n",
    ):
        assert must in tidy_to_demo
    for v in INEXACT:
        assert v not in STAGES


def test_demo_loads_and_pilot_and_prod_load_only_without_the_fakes(cfg_dir):
    assert load_config(cfg_dir).environment == "demo"
    for stage in ("pilot", "prod"):
        _set_env(cfg_dir, stage)
        with pytest.raises(ConfigError, match=f"environment {stage}: refused"):
            load_config(
                cfg_dir
            )  # a valid stage, refused for the fixture's fake kinds, not for its name


# --- demo-only kinds -----------------------------------------------------------------------------------------------

SIX_PAIRS = {
    ("llm", "fake"),
    ("channel", "fake"),
    ("secrets", "fake"),
    ("secrets", "env"),
    ("store", "memory"),
    ("audit", "local_dir"),
}


def test_demo_only_is_exactly_the_six_pairs():
    assert table.DEMO_ONLY == SIX_PAIRS
    assert isinstance(table.DEMO_ONLY, frozenset)


def test_demo_accepts_every_demo_only_kind(cfg_dir):
    try:
        cfg = load_config(cfg_dir)  # the fixture is the demo config and holds fakes
    except ConfigError as exc:
        raise AssertionError("demo config was refused: " + str(exc)) from None
    assert cfg.environment == "demo"
    held = {(c, s.kind) for c, s in cfg.backends.entries()}
    assert {("llm", "fake"), ("channel", "fake"), ("secrets", "fake"), ("store", "memory")} <= held
    assert ("audit", "local_dir") in held
    assert cfg.allow_insecure_loopback is True


def test_pilot_and_prod_refuse_every_relaxed_kind(cfg_dir):
    """The fake model, the memory store, the other fakes and the loopback switch."""
    for stage in ("pilot", "prod"):
        _set_env(cfg_dir, stage)
        with pytest.raises(ConfigError, match=f"environment {stage}: refused: ") as err:
            load_config(cfg_dir)
        for item in (
            "llm: fake",
            "store: memory",
            "audit: local_dir",
            "secrets: fake",
            "channel: fake",
            "allow_insecure_loopback",
        ):
            assert item in str(err.value), f"{stage} did not refuse {item}"


@pytest.mark.parametrize("pair", sorted(SIX_PAIRS))
def test_each_demo_only_pair_is_named_in_the_pilot_and_prod_refusal(cfg_dir, pair):
    """One test per pair, so a pair dropped from the set is named by its own failing test."""
    cap, kind = pair
    if pair == ("secrets", "env"):  # the fixture holds the other five
        _edit(cfg_dir, lambda d: d["backends"].update(secrets={"kind": "env"}))
    for stage in ("pilot", "prod"):
        _set_env(cfg_dir, stage)
        with pytest.raises(ConfigError, match=f"environment {stage}: refused: ") as err:
            load_config(cfg_dir)
        assert f"{cap}: {kind}" in str(err.value), f"{pair} was not refused in {stage}"


def test_demo_is_not_live(tmp_path):
    """A tool module with no pin loads in demo and is refused in pilot and prod; no restored-hash key is needed in demo."""
    cfg_dir = make_cfg(tmp_path)
    loaded = load_config(cfg_dir)
    fields = {name: getattr(loaded, name) for name in type(loaded).model_fields}
    fields["tool_modules"] = ["tests.fixtures.k5_tools"]
    demo = Config(**fields)
    assert _module_pin_problems(demo) == [], "demo was treated as live"
    for stage in ("pilot", "prod"):
        # the same config in a live stage is refused for its fake kinds before anything else; the pin check is a
        # separate function, so ask it directly with the stage changed.
        live = demo.model_copy(update={"environment": stage})
        problems = _module_pin_problems(live)
        assert any("no tool_module_hashes pin" in p for p in problems), (
            f"{stage} accepted an unpinned module"
        )
    # app.build in demo needs no restored hash key
    qualify(load_registry(load_config(cfg_dir)))
    build(cfg_dir, ["test-agent"], secrets=FakeSecretProvider({"fixture-token": "tok" + "-stage"}))


# --- the live guards fail closed -----------------------------------------------------------------------------------------


def _live_by_site(tmp_path, stage):
    """Ask each of the three places that decide 'live' (the unpinned tool module check in registry.py, the pilot and prod
    rules in deferred.py, the startup checks in app.py) about a config whose stage is `stage`, set on an unvalidated copy
    (model_copy skips the check that only demo, pilot and prod load). True: that place treated the config as live."""
    cfg_dir = make_cfg(tmp_path)
    cfg = load_config(cfg_dir)
    reg = load_registry(cfg)
    qualify(reg)
    copy = cfg.model_copy(
        update={"environment": stage, "tool_modules": ["tests.fixtures.k5_tools"]}
    )
    in_registry = any("no tool_module_hashes pin" in p for p in _module_pin_problems(copy))
    agent = SimpleNamespace(id="a", max_run_usd=None, data_class="internal", levels=None)
    probe = SimpleNamespace(config=copy, contracts={}, agents={"a": agent})
    in_deferred = any("is required in pilot and prod" in p for p in deferred.check(probe))
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(app_mod, "load_config", lambda _d: copy)
        mp.setattr(app_mod, "load_registry", lambda _c: reg)
        try:
            app_mod.build(
                cfg_dir,
                ["test-agent"],
                secrets=FakeSecretProvider({"fixture-token": "tok" + "-stage"}),
            )
            in_app = False
        except ConfigError as exc:
            in_app = "restored_hash_key_secret_name is required in pilot and prod" in str(exc)
    return {"registry": in_registry, "deferred": in_deferred, "app": in_app}


def test_a_value_that_is_not_a_stage_is_live_for_every_guard(tmp_path):
    """Config refuses such a value at load, but model_copy(update=...) and model_construct skip that check. The guards
    must then treat the config as live (strict), not as demo: only exactly demo is relaxed."""
    for n, bad in enumerate(["stag" + "ing", "Demo", "demo ", OLD, "", None, "uat"]):
        got = _live_by_site(tmp_path / str(n), bad)
        for site, live in got.items():
            assert live, f"{site} treated {bad!r} as not live (an allowlist of live stages)"


# --- fail closed on a half-renamed flag ----------------------------------------------------------------------


def test_no_old_spelling_of_the_demo_only_flag_is_left():
    assert not hasattr(table, "DE" + "V_ONLY"), (
        "half-renamed: the old flag name still exists next to DEMO_ONLY"
    )
    assert not hasattr(config_mod, "DE" + "V_ONLY")
    assert hasattr(table, "DEMO_ONLY") and hasattr(config_mod, "DEMO_ONLY")


@pytest.mark.parametrize("key", [OLD + "_only", "demo_only", "demo", OLD, "stage"])
def test_a_config_key_for_either_spelling_of_the_flag_refuses_start(cfg_dir, key):
    """Config has no such key; the strict model refuses it, so a half-renamed pair never starts."""
    _edit(cfg_dir, lambda d: d.update({key: True}))
    with pytest.raises(ConfigError, match=key):
        load_config(cfg_dir)


def test_both_spellings_of_the_stage_together_refuse_start(cfg_dir):
    """`environment: demo` beside an old-spelling key is refused (strict keys), never read as allowed."""
    _edit(cfg_dir, lambda d: d.update({"environment_" + OLD: "demo"}))
    with pytest.raises(ConfigError, match="environment_" + OLD):
        load_config(cfg_dir)


# --- the class test, stage POSITIONS only ------------------------------------------------------------------

_W = (
    r"(?<![A-Za-z0-9])" + OLD + r"(?![A-Za-z0-9])"
)  # the old word as a whole word, not inside another word
_STAGE = r"(?:pilot|prod|production|demo)"
_Q = r"[`'\"]?"  # a quote or backtick around the word
_PHRASE_BEFORE = r"(?:in|for|outside|than|kept in|refused in)"
_PHRASE_AFTER = r"(?:only|executor|stage|tier|environment|config|app|runtime|slice|install)"
# (name, regex). Each is a place where the old word would still be a STAGE: a config value, an enum or list member
# beside the other stages, a flag or helper name that carries the stage, a stage phrase in prose, a URL host label,
# a heading. Words such as "developer", "device", "stddev", "vault server -dev" and a dataset split are not positions.
POSITIONS = {
    "config value": re.compile(
        r"environment\b[^A-Za-z0-9\n]{1,5}" + OLD + r"(?![A-Za-z0-9])", re.IGNORECASE
    ),
    "list member": re.compile(
        _W + r"[^A-Za-z0-9\n]{1,5}" + _STAGE + r"\b|\b" + _STAGE + r"[^A-Za-z0-9\n]{1,5}" + _W,
        re.IGNORECASE,
    ),
    "flag or helper name": re.compile(
        r"(?<![A-Za-z0-9])" + OLD + r"_(?:only|cfg|config|env|stage|tier|mode|app|runtime)\b|"
        r"\b(?:in|outside|is|for|not)_" + OLD + r"(?![A-Za-z0-9])|_" + OLD + r"(?:_only)?\(",
        re.IGNORECASE,
    ),
    "stage phrase": re.compile(
        r"\b"
        + _PHRASE_BEFORE
        + r" "
        + _Q
        + OLD
        + r"(?![A-Za-z0-9])|"
        + _W
        + _Q
        + r" "
        + _PHRASE_AFTER
        + r"\b",
        re.IGNORECASE,
    ),
    "stage word then value": re.compile(
        r"\b(?:tier|stage|profile|mode)\b\W{1,4}" + OLD + r"(?![A-Za-z0-9])", re.IGNORECASE
    ),
    "list literal": re.compile(
        r"[\[(\{,]\s*[`'\"]" + OLD + r"[`'\"]\s*[,\])\}]|^\s*-\s+[`'\"]?" + OLD + r"[`'\"]?\s*$",
        re.IGNORECASE,
    ),
    # the generic one: the old word as a quoted value after ==, !=, = or : whatever the name before it is
    # (`ENV=dev`, `target: "dev"`, `deploy = "dev"`, `if env == "dev"`, `{"x": "dev"}`)
    "compared or assigned": re.compile(r"(?:==|!=|=|:)\s*['\"]" + OLD + r"['\"]", re.IGNORECASE),
    "url host": re.compile(r"://" + OLD + r"\.|://[^/\s]*-" + OLD + r"\.", re.IGNORECASE),
    "heading": re.compile(r"^#{1,6} .*" + _W, re.IGNORECASE),
}
SCANNED = (
    ("src", ("*.py", "*.toml", "*.json")),
    ("tests", ("*.py", "*.yaml", "*.yml", "*.toml", "*.json")),
    ("docs", ("*",)),
    ("demos", ("*.py", "*.md", "*.yaml", "*.json", "*.toml")),
    (".github", ("*",)),
    ("tools", ("*.py", "*.txt", "*.md", "*.toml", "*.json")),
    (".", ("*.md",)),
)  # not scanned: pyproject.toml and uv.lock at the root (the packaging group is called dev), CHANGELOG.md (history)
# The one place in src that has to name the refused word: the constant the refusal compares with. Exact line, same
# stale-entry rule.
REFUSAL_LINES = frozenset({("src/hadavin_sdk/config.py", '_OLD_STAGE = "dev"')})
SELF = Path(__file__).resolve()
# The ask-your-data demo has an evaluation data split called dev (train/dev/test): a data split, not a stage (R449).
# Only these exact lines of these exact files are exempt (the word sits inside the split constant, the split flag or the
# split value); any other line in the same files is scanned like everywhere else. An entry that matches no line is stale
# and fails, so the list cannot outlive the code it excuses.
SPLIT_LINES = frozenset(
    {
        (
            "demos/ask-your-data/askdata/evalcli.py",
            'r.add_argument("--split", choices=["dev", "test"], required=True)',
        ),
        ("demos/ask-your-data/askdata/evalset.py", 'split: Literal["dev", "test"]'),
        (
            "demos/ask-your-data/data/goldcheck.py",
            "Field names differ from design 12.2 on purpose of this task: `tier` (dev|test) is the split, `level` the difficulty,",
        ),
        (
            "demos/ask-your-data/data/goldcheck.py",
            "adversarial.dev.jsonl     12 items (`dev`): the prompt is tuned against these, never against the 16 sealed ones",
        ),
        (
            "demos/ask-your-data/data/goldcheck.py",
            "f\"composition of {level}: got {tally[('dev', level)]}/{tally[('test', level)]}, want {dev}/{test}\"",
        ),
        ("demos/ask-your-data/data/goldcheck.py", 'g["tier"] not in ("dev", "test")'),
        (
            "demos/ask-your-data/data/goldcheck.py",
            'if (tally[("dev", level)], tally[("test", level)]) != (dev, test):',
        ),
        (
            "tests/demo_askdata/test_eval_harness.py",
            'assert cli.main(["eval", "run", "--split", "dev"]) == 4  # no config',
        ),
        ("tests/demo_askdata/test_eval_harness.py", 'assert cmd_run(cfg, "dev", 1, None) == 4'),
        (
            "tests/demo_askdata/test_eval_harness.py",
            'assert cmd_run(cfg, "dev", 1, None, harness_factory=factory) == 4',
        ),
        (
            "tests/demo_askdata/test_eval_harness.py",
            'cmd_run(cfg, "dev", 1, None, harness_factory=factory)',
        ),
        (
            "tests/demo_askdata/test_eval_harness.py",
            'code = cmd_run(cfg, "dev", 1, None, harness_factory=factory)',
        ),
        ("tests/demo_askdata/test_eval_harness.py", 'split=kw.pop("split", "dev"),'),
        ("tests/demo_askdata/test_gold_data.py", 'assert not sqls("dev") & sqls("test")'),
        (
            "tests/demo_askdata/test_gold_data.py",
            'lambda rows: next(r for r in rows if r["id"] == "T07").update(tier="dev"),',
        ),
        (
            "demos/ask-your-data/askdata/evalrun.py",
            'label: str = "dev"  # "dev", "sealed", "second look"',
        ),
        (
            "demos/ask-your-data/data/goldcheck.py",
            '"counts": {"gold_dev": sum(g["tier"] == "dev" for g in gold), "gold_test": sum(g["tier"] == "test" for g in gold),',
        ),
        (
            "demos/ask-your-data/data/goldcheck.py",
            '"dev_sha256": digest([g for g in gold if g["tier"] == "dev"]),',
        ),
        (
            "demos/ask-your-data/data/goldcheck.py",
            'if (sum(g["tier"] == "dev" for g in gold), sum(g["tier"] == "test" for g in gold)) != (30, 40):',
        ),
        ("demos/ask-your-data/data/goldcheck.py", 'if g["exemplar"] and g["tier"] != "dev":'),
        (
            "demos/ask-your-data/data/goldcheck.py",
            'if src is None or src["tier"] != "dev" or src["kind"] != "answerable":',
        ),
        (
            "demos/ask-your-data/data/goldcheck.py",
            'want = "dev" if dev else ("ci" if det else "test")',
        ),
        (
            "tests/demo_askdata/test_eval_harness.py",
            'evalrun.sealed_gate(lock, Decimal(0), split="dev", second_look=None)  # dev is never gated',
        ),
        (
            "tests/demo_askdata/test_eval_harness.py",
            'r.harness.report([], [rec], split="dev", meta={})["hard_zeros"][',
        ),
        (
            "tests/demo_askdata/test_eval_harness.py",
            'r.harness.report(r.harness.run_gold([it]), [], split="dev", meta={"model_id": "m"})',
        ),
        (
            "tests/demo_askdata/test_eval_harness.py",
            'rep = r.harness.report([], [rec], split="dev", meta={})',
        ),
        (
            "tests/demo_askdata/test_eval_harness.py",
            'rep = r.harness.report([], list(recs.values()), split="dev", meta={})',
        ),
        (
            "tests/demo_askdata/test_eval_harness.py",
            'rep = r.harness.report(r.harness.run_gold([it]), [], split="dev", meta={})',
        ),
        (
            "tests/demo_askdata/test_eval_harness.py",
            'rep = r.harness.report(recs, [], split="dev", meta={})',
        ),
        ("tests/demo_askdata/test_eval_harness.py", 'rep("green", 0, split="dev"),'),
        ("tests/demo_askdata/test_eval_harness.py", 'rep["label"] == "dev"'),
        (
            "tests/demo_askdata/test_gold_data.py",
            'assert (sum(g["tier"] == "dev" for g in gold), sum(g["tier"] == "test" for g in gold)) == (',
        ),
        (
            "tests/demo_askdata/test_gold_data.py",
            'assert all(ids[e["source_dev_id"]]["tier"] == "dev" for e in data["exemplars"])',
        ),
        (
            "tests/demo_askdata/test_htmlexport.py",
            '"split": "dev", "label": "x", "verdict_text": "green", "aborted": None,',
        ),
    }
)


def _hits(line: str, markdown: bool = True) -> list[str]:
    """Names of the positions in `line`. A heading is a position in a Markdown file only (a `#` line in code is a comment)."""
    line = re.sub(
        r"\bfor \w+ in " + OLD + r"\b", "", line, flags=re.IGNORECASE
    )  # `for row in dev`: a dataset split, not a stage
    return [n for n, rx in POSITIONS.items() if rx.search(line) and (markdown or n != "heading")]


def _scan_text(rel: str, text: str) -> tuple[list[str], set]:
    """Hits in one file's text; a line that is exactly a listed split line is excused and its entry is marked used."""
    out, used = [], set()
    for number, line in enumerate(text.splitlines(), 1):
        names = _hits(line, rel.endswith(".md"))
        if names and (rel, line.strip()) in SPLIT_LINES | REFUSAL_LINES:
            used.add((rel, line.strip()))
            names = []
        if names:
            out.append(f"{rel}:{number} [{', '.join(names)}] {line.strip()[:100]}")
    return out, used


def _scan() -> tuple[list[str], set]:
    """(hits, the split-exemption entries that matched a line)."""
    out, used = [], set()
    for folder, patterns in SCANNED:
        base = ROOT / folder
        if not base.is_dir():
            continue
        for pattern in patterns:
            for path in base.glob(pattern) if folder == "." else base.rglob(pattern):
                if not path.is_file() or path.resolve() == SELF or "__pycache__" in path.parts:
                    continue
                if folder == "." and path.name == "CHANGELOG.md":
                    continue  # history: it says what was renamed
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                rel = path.relative_to(ROOT).as_posix()
                found, hit_entries = _scan_text(rel, text)
                out += found
                used |= hit_entries
    return sorted(set(out)), used


def test_the_old_stage_word_is_gone():
    found, _ = _scan()
    assert not found, "the old stage word is still used as a stage:\n" + "\n".join(found)


def test_the_split_exemption_has_no_stale_entry_and_covers_only_the_two_demo_places():
    """An entry that matches no line is stale and fails; every entry is in the demo or its tests, nothing else."""
    _, used = _scan()
    assert used == SPLIT_LINES | REFUSAL_LINES, (
        f"stale entries: {sorted((SPLIT_LINES | REFUSAL_LINES) - used)}"
    )
    for rel, _ in SPLIT_LINES:
        assert rel.startswith(("demos/ask-your-data/", "tests/demo_askdata/")), rel
        assert (ROOT / rel).is_file()


def test_a_stage_shaped_dev_line_in_the_same_file_as_a_split_line_still_fails():
    """Run the real scan on the real text of a file that holds a split line, with one stage-shaped line added: the split
    line stays excused, the added line is a hit."""
    rel = "demos/ask-your-data/askdata/evalset.py"
    text = (ROOT / rel).read_text(encoding="utf-8")
    assert _scan_text(rel, text) == ([], {(rel, 'split: Literal["dev", "test"]')}), (
        "the file as it is should be clean and use its one split entry"
    )
    for added in (f"environment: {OLD}", f'ENV = "{OLD}"', f'if target == "{OLD}":'):
        found, used = _scan_text(rel, text + "\n" + added + "\n")
        assert len(found) == 1 and added in found[0], f"the added line was not found: {added}"
        assert used == {(rel, 'split: Literal["dev", "test"]')}


def _excused(rel: str, line: str) -> bool:
    return (rel, line.strip()) in SPLIT_LINES


def test_a_stage_shaped_use_in_the_same_file_still_fails():
    """The exemption excuses exact split lines only: a stage-shaped line in a file that holds one is not excused."""
    rel = "demos/ask-your-data/askdata/evalset.py"
    assert _excused(rel, 'split: Literal["dev", "test"]')
    for line in (
        f'stage = "{OLD}"',
        f"environment: {OLD}",
        f'split: Literal["{OLD}", "test", "pilot"]',  # a split line with a stage added is a different line
        f'tier: Literal["{OLD}", "test"]',
    ):
        assert _hits(line), f"the scanner misses: {line}"
        assert not _excused(rel, line), f"excused by mistake: {line}"
    assert not _excused("demos/ask-your-data/askdata/other.py", 'split: Literal["dev", "test"]')


@pytest.mark.parametrize(
    "line",
    [
        f"environment: {OLD}",
        f'environment="{OLD}"',
        f'"environment": "{OLD}"',
        f'Literal["{OLD}", "pilot", "prod"]',
        f"{OLD}|pilot|prod",
        f"demo, {OLD}",
        f"{OLD.upper()}_ONLY = frozenset()",
        f"def {OLD}_cfg(tmp_path):",
        f"def test_x_outside_{OLD}(cfg):",
        f"kept in {OLD} for the tests",
        f"kinds allowed only in `{OLD}`.",
        f"(`{OLD}` only, by the environment table)",
        f"a {OLD} executor",
        f"refused outside {OLD}, no more",
        f"https://{OLD}.example.org/x",
        f"## Running in {OLD}",
        f"tier: {OLD}",
        f'stage = "{OLD}"',
        f"profile={OLD}",
        f'"mode": "{OLD}"',
        f"deploy.mode: `{OLD}`",
        f'STAGES = ["{OLD}"]',
        f'("{OLD}",)',
        f"{{'{OLD}'}}",
        f'x = ["a", "{OLD}"]',
        f"  - {OLD}",
        f'  - "{OLD}"',
        f'ENV="{OLD}"',
        f"target: '{OLD}'",
        f'deploy = "{OLD}"',
        f'if env == "{OLD}":',
        f'if env != "{OLD}":',
        f'x = {{"k": "{OLD}"}}',
    ],
)
def test_the_scanner_finds_each_stage_position(line):
    assert _hits(line), f"not found: {line}"


@pytest.mark.parametrize(
    "line",
    [
        "a developer wrote this",
        "the device is on",
        "stddev = 3",
        "a real `vault server -" + OLD + "` in CI",
        f"the CI Vault {OLD} server",
        f"{OLD} split of the dataset",
        "(?:com|net|io|" + OLD + "|ai|cloud)",
        "[dependency-groups]",
        f'{OLD} = ["pytest"]',
        "Dev-tool constants",
        "environment variable HADAVIN_X",
        "environment: demo",
        f"for row in {OLD}:",
        "modern mode: developer",
        "stage: demo",
        "  - demo",
        f'default-groups = ["{OLD}x"]',
        f"mode: {OLD}elop",
    ],
)
def test_the_scanner_ignores_words_that_are_not_stage_positions(line):
    assert not _hits(line), f"false hit: {line}: {_hits(line)}"


@pytest.mark.parametrize("word", ["tier", "stage", "profile", "mode"])
def test_a_four_character_separator_between_a_stage_word_and_the_old_word_is_found(word):
    """`stage = "dev"` has four characters (space, equals, space, quote) between the words, and `"mode": "dev"` has four
    as well (quote, colon, space, quote): both must be found. The reach is four; five is outside the position."""
    for sep in ('": "', ' = "', '"=: ', "':'", ": ", "="):
        assert _hits(word + sep + OLD), f"not found: {word}{sep}{OLD}"
    assert len('": "') == len(' = "') == 4
    assert not _hits(word + " " * 5 + OLD), "the reach is four characters, not more"


# --- the redactor treats stage words as ordinary words, so `demo` joins them ----------------------------------


def test_the_redactor_does_not_sweep_the_stage_words_but_still_sweeps_secrets_and_other_names():
    from hadavin_sdk.guard.redact import _sweep

    for word in ("prod", "pilot", "demo", OLD):
        assert _sweep("<TENANT_1>", word) is None, f"{word} is swept like a name"
    assert _sweep("<TENANT_1>", "acme" + "corp") is not None
    assert _sweep("<SECRET_1>", "pilot") is not None, (
        "a secret that reads 'pilot' must still be swept"
    )
    assert _sweep("<SECRET_1>", "demo") is not None, (
        "a secret that reads 'demo' must still be swept"
    )
