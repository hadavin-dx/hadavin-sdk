"""The stages are exactly demo, pilot and prod. The old first stage name is refused, never read as a stage, and a
class test keeps the old word out of every place that names a stage.

No stage is stored anywhere today, so there is no read site to test. The first change that stores one must map an old
value to demo on read for display only (never for a guard decision) and add a test through that real read site.

Rows: unknown stage and half-renamed flag refuse start; the class test looks at stage POSITIONS only; pilot and prod
refuse relaxed kinds; the live and prod-only guards fail closed on a value that is not a stage.
"""

import re
import typing
import unicodedata
from pathlib import Path
from types import SimpleNamespace

import pytest

from hadavin_sdk import app as app_mod
from hadavin_sdk import config as config_mod
from hadavin_sdk import deferred
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.app import build
from hadavin_sdk.backends import table
from hadavin_sdk.config import Config, ConfigError, _anchor_refusals, load_config, parse_backends
from hadavin_sdk.registry import _module_pin_problems, load_registry
from hadavin_sdk.stages import STAGES, is_live, is_prod
from tests.conftest import make_cfg, qualify
from tests.k5_support import edit_config as _edit

# The old word is built from parts in this file: the class test never scans this file, but a grep for it should find
# only the places that matter.
OLD = "d" + "ev"
RENAMED = (
    "environment: "
    + OLD
    + " was renamed to demo; write environment: demo (allowed values: demo, pilot, prod)"
)
ROOT = Path(__file__).resolve().parents[1]
ALLOWED = "Input should be 'demo', 'pilot' or 'prod'"  # pydantic's text for a value outside the three stages


@pytest.fixture
def cfg_dir(tmp_path):
    """A copy of the fixture config. Defined here, not taken from conftest, because the mutation runner runs with --noconftest."""
    return make_cfg(tmp_path)


def _set_env(cfg_dir, value):
    _edit(cfg_dir, lambda d: d.update(environment=value))


# --- the stage set -------------------------------------------------------------------------------------------------


def test_the_stages_are_exactly_demo_pilot_prod(tmp_path):
    assert STAGES == ("demo", "pilot", "prod")
    # the field's allowed values are the same tuple, not a second copy that can drift
    assert typing.get_args(Config.model_fields["environment"].annotation) == STAGES
    # the one place that decides "live": only exactly the first stage is relaxed, anything else is live
    assert [is_live(s) for s in STAGES] == [False, True, True], "is_live is wrong for a stage"
    assert [is_prod(s) for s in STAGES] == [False, False, True], "is_prod is wrong for a stage"
    nonstage = ("stag" + "ing", "Demo", OLD, "", None)
    assert all(is_live(v) for v in nonstage), "is_live is wrong for a value that is not a stage"
    assert all(is_prod(v) for v in nonstage), "is_prod is wrong for a value that is not a stage"
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
    # beside another problem in the same file: both are shown, the sentence still without the wrapper
    _edit(cfg_dir, lambda d: d.update(nonsense_key=1))
    with pytest.raises(ConfigError) as both:
        load_config(cfg_dir)
    assert RENAMED in str(both.value), "the rename sentence is lost beside another problem"
    assert "nonsense_key" in str(both.value), "the other problem is hidden by the rename sentence"
    assert "validation error" not in str(both.value), "pydantic's wrapper is visible"
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
    "d"
    + chr(0x0435)
    + "v",  # the old word with a Cyrillic e: no rename hint, only the allowed-values refusal
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
    """Case, spaces, a prefix such as demo-eu, and a project label (uat) are not the stage. Every spelling of the old
    word gets the rename sentence (a hint only; it is refused all the same)."""
    for value in INEXACT:
        _set_env(cfg_dir, value)
        try:
            cfg = load_config(cfg_dir)
        except ConfigError as exc:
            message = str(exc)
        else:
            raise AssertionError(
                f"a stage that is not exactly demo, pilot or prod was accepted: {value!r} -> {cfg.environment}"
            )
        # the allowed-values text (it lists demo, not dev), or the rename sentence for the old word's spellings
        want = RENAMED if value.strip().casefold() == OLD else ALLOWED
        assert want in message, f"{value!r}: refused for another reason: {message[:150]}"


@pytest.mark.parametrize("value", [None, 0, 1.5, True, ["demo"], {"demo": 1}])
def test_a_stage_that_is_not_a_string_is_refused(cfg_dir, value):
    _set_env(cfg_dir, value)
    with pytest.raises(ConfigError, match="environment") as err:
        load_config(cfg_dir)
    assert ALLOWED in str(err.value), f"{value!r}: not refused by the allowed-values rule"


def test_a_missing_stage_is_refused(cfg_dir):
    """Passes on the old code too (a missing field was always refused): it pins that no default fills the gap."""
    _edit(cfg_dir, lambda d: d.pop("environment"))
    with pytest.raises(ConfigError, match="environment\n  Field required"):
        load_config(cfg_dir)


@pytest.mark.parametrize("raw", ["~", "null", "Null", "NULL", ""])
def test_a_yaml_null_stage_is_refused(cfg_dir, raw):
    """`environment: ~` (and the other YAML spellings of null, and a bare key) reads as None: refused, never a default."""
    path = cfg_dir / "config.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("environment: demo", f"environment: {raw}"), encoding="utf-8")
    assert f"environment: {raw}" in path.read_text(encoding="utf-8")
    with pytest.raises(ConfigError, match="environment") as err:
        load_config(cfg_dir)
    assert ALLOWED in str(err.value), "a null stage is not refused by the allowed-values rule"


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
        # The pinned-Unicode guard of app.build (pilot and prod) is not what this test asks about, and on an interpreter with other Unicode
        # data it would stop the build first. tests/conftest.py switches it off for the same reason, but the mutation runner runs with
        # --noconftest, so it is switched off here, in the test. The guard itself is tested in tests/test_textnorm_app.py.
        mp.setattr(app_mod.textnorm, "require_pinned_unidata", lambda *a, **k: None)
        try:
            app_mod.build(
                cfg_dir,
                ["test-agent"],
                secrets=FakeSecretProvider({"fixture-token": "tok" + "-stage"}),
                allow_test_doubles=True,  # pilot and prod refuse a handed-in provider without the switch
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


ANCHOR = {"kind": "s3_object_lock", "bucket": "b", "region": "r"}
KEY_FILE = {"kind": "ed25519_local", "private_key_path": "k.pem"}
KEY_SECRET = {"kind": "ed25519_local", "private_key_secret_name": "audit-key"}


def _backends(anchor, signer):
    raw = {"signer": signer, "anchor": anchor, "audit": {"kind": "chain"}}
    return parse_backends({**raw, "llm": {"kind": "fake", "recorded_dir": "r"}}, Path("."))


def test_a_value_that_is_not_a_stage_gets_the_prod_only_rules():
    """model_copy and model_construct skip the check that only demo, pilot and prod load. The prod-only rules (no local
    key file, an anchor whose retention the client agreed, no signer or anchor of kind none) must then apply, as in
    prod; and COMPLIANCE (undeletable) stays allowed in exactly prod."""
    acked = ANCHOR | {"retention_ack": True}
    cases = [(acked, KEY_FILE), ("none", KEY_FILE), (ANCHOR, KEY_SECRET)]
    for (
        anchor,
        signer,
    ) in cases:  # each is refused in prod, accepted in pilot: the rule is prod-only
        assert _anchor_refusals("prod", _backends(anchor, signer)), (
            "the case must be refused in prod"
        )
        assert _anchor_refusals("pilot", _backends(anchor, signer)) == [], (
            "the case must pass pilot"
        )
    compliance = _backends(acked | {"mode": "COMPLIANCE"}, KEY_SECRET)
    assert _anchor_refusals("prod", compliance) == [], "prod refused COMPLIANCE with retention_ack"
    for bad in ("stag" + "ing", "Prod", "prod ", "", None):
        for anchor, signer in cases:
            found = _anchor_refusals(bad, _backends(anchor, signer))
            assert found, f"{bad!r}: no prod-only rule applied to {anchor} / {signer}"
            assert found == _anchor_refusals("prod", _backends(anchor, signer)), (
                f"{bad!r}: not as prod"
            )
        assert any("COMPLIANCE outside prod" in r for r in _anchor_refusals(bad, compliance)), (
            f"{bad!r}: COMPLIANCE was allowed outside the three stages"
        )


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
# The old word (dev) and its siblings (staging, the bare stage) must not name a stage anywhere. A word is "used as a
# stage" in a position: a value after a stage-like name (config, CLI, env var, enum member), a quoted string literal
# (dict key, list or set member on any line, case label, conditional), a member of a stage list. Prose such as "the
# demo stage", "developer", "stddev" and a dataset split are not positions; the data splits are listed one exact line at
# a time in tests/stage_exemptions.tsv, each with its reason.

_W = r"(?<![A-Za-z0-9])" + OLD + r"(?![A-Za-z0-9])"  # the old word as a whole word
_ANY = r"(?<![A-Za-z0-9])(?:" + OLD + r"|staging|stage)(?![A-Za-z0-9])"  # the old word or a sibling
_STAGE = r"(?:pilot|prod|production|demo)"
_Q = r"[`'\"]?"  # a quote or backtick around the word
_NAME = r"(?<![A-Za-z0-9])(?:env(?:ironment)?|stage|tier|profile|mode)(?![A-Za-z0-9])"
_BEFORE = r"(?:in|for|outside|than|kept in|refused in)"
_AFTER = r"(?:only|executor|stage|tier|environment|config|app|runtime|slice|install)"
# (name, regex). The first three look for the old word and its siblings; the rest for the old word only.
POSITIONS = {
    # `environment: dev`, `ENV=dev`, `APP_ENV=dev`, `--env dev`, `STAGE_DEV`, `Environment.DEV`, `"mode": "dev"`
    "value after a stage name": re.compile(_NAME + r"[^A-Za-z0-9\n]{1,4}" + _ANY, re.IGNORECASE),
    # a quoted literal: `== "dev"`, `{"dev": 1}`, `case "dev":`, `"dev" if x`, a set member alone on its line
    "quoted literal": re.compile(r"[`'\"](?:" + OLD + r"|staging|stage)[`'\"]", re.IGNORECASE),
    # beside another stage in a list: `dev|pilot|prod`, `demo, dev`, a YAML list item `- dev`
    "list member": re.compile(
        _ANY
        + r"\s*[,|/;]\s*"
        + _STAGE
        + r"\b|\b"
        + _STAGE
        + r"\s*[,|/;]\s*"
        + _ANY
        + r"|^\s*-\s+"
        + _ANY
        + r"\s*$",
        re.IGNORECASE,
    ),
    "flag or helper name": re.compile(
        _W
        + r"_(?:only|cfg|config|env|stage|tier|mode|app|runtime)\b|\b(?:in|outside|is|for|not)_"
        + OLD
        + r"(?![A-Za-z0-9])|_"
        + OLD
        + r"(?:_only)?\(",
        re.IGNORECASE,
    ),
    "stage phrase": re.compile(
        r"\b" + _BEFORE + r" " + _Q + OLD + r"(?![A-Za-z0-9])|" + _W + _Q + r" " + _AFTER + r"\b",
        re.IGNORECASE,
    ),
    "url host": re.compile(r"://" + OLD + r"\.|://[^/\s]*-" + OLD + r"\.", re.IGNORECASE),
    "heading": re.compile(r"^#{1,6} .*" + _W, re.IGNORECASE),
}
# Every file of these types below these folders, and in the repo root except the three skipped by name (history, the
# packaging group called dev, a lock file). Not scanned by type: .jsonl, the ask-your-data gold data (42 records hold the
# data split in a tier field).
SCANNED = ("src", "tests", "docs", "demos", ".github", "tools")
TYPES = (
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".json",
    ".yaml",
    ".yml",
    ".sql",
    ".properties",
    ".cfg",
    ".ini",
)
SKIPPED_ROOT = ("CHANGELOG.md", "pyproject.toml", "uv.lock")
EXEMPT_FILE = ROOT / "tests" / "stage_exemptions.tsv"
SELF = Path(__file__).resolve()
# Letters that look like Latin ones, as code points (no look-alike in this file). NFKC and casefold cover fullwidth,
# roman-numeral and capital forms. A plain list until the shared fold (P1a) is merged.
CONFUSABLES = {
    0x0435: "e",
    0x0501: "d",
    0x0475: "v",
    0x03BD: "v",
    0x0455: "s",
    0x0456: "i",
    0x0430: "a",
    0x0261: "g",
}
INVISIBLE = re.compile(
    "[" + "".join(map(chr, (0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0xAD))) + "]"
)


def _exemptions() -> dict:
    """(file, exact stripped line) -> reason, from the tsv. Real non-stage uses only: a data split, a tool name."""
    rows = [r.split("\t") for r in EXEMPT_FILE.read_text(encoding="utf-8").splitlines() if r]
    assert all(len(r) == 3 for r in rows), (
        "a row of stage_exemptions.tsv is not file TAB line TAB reason"
    )
    return {(f, line): why for f, line, why in rows}


def _fold(line: str) -> str:
    """The line as a reader sees it: NFKC, casefold, invisible characters out, look-alike letters made Latin."""
    folded = unicodedata.normalize("NFKC", line).casefold()
    return INVISIBLE.sub("", folded).translate(CONFUSABLES)


def _hits(line: str, markdown: bool = True) -> list[str]:
    """Names of the positions in `line`. A heading is a position in a Markdown file only (a `#` line in code is a comment)."""
    line = re.sub(
        r"\bfor \w+ in " + OLD + r"\b", "", _fold(line)
    )  # `for row in dev`: a dataset split
    return [n for n, rx in POSITIONS.items() if rx.search(line) and (markdown or n != "heading")]


def _scan_text(rel: str, text: str, exempt: dict | None = None) -> tuple[list[str], set]:
    """Hits in one file's text; a line that is exactly an exempt line is excused and its entry is marked used."""
    exempt, out, used = _exemptions() if exempt is None else exempt, [], set()
    for number, line in enumerate(text.splitlines(), 1):
        names = _hits(line, rel.endswith(".md"))
        if names and (rel, line.strip()) in exempt:
            used.add((rel, line.strip()))
            names = []
        if names:
            out.append(f"{rel}:{number} [{', '.join(names)}] {line.strip()[:100]}")
    return out, used


def _scan() -> tuple[list[str], set]:
    """(hits, the exemption entries that matched a line)."""
    paths = [p for folder in SCANNED for p in (ROOT / folder).rglob("*")]
    paths += [p for p in ROOT.glob("*") if p.name not in SKIPPED_ROOT]
    paths = [
        p for p in paths if p.suffix in TYPES or p.name.startswith(".git")
    ]  # .gitleaks.toml, .gitignore
    out, used = [], set()
    for path in paths:
        if not path.is_file() or path in (SELF, EXEMPT_FILE) or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        found, hit_entries = _scan_text(path.relative_to(ROOT).as_posix(), text)
        out += found
        used |= hit_entries
    return sorted(set(out)), used


def test_the_old_stage_word_is_gone():
    found, _ = _scan()
    assert not found, "the old stage word is still used as a stage:\n" + "\n".join(found)


def test_the_exemptions_have_no_stale_entry():
    """An entry that matches no line is stale and fails; each entry is one exact line of one file, with its reason."""
    _, used = _scan()
    exempt = _exemptions()
    assert used == set(exempt), f"stale entries: {sorted(set(exempt) - used)}"
    for (rel, _), why in exempt.items():
        assert why.strip() and (ROOT / rel).is_file(), rel


def test_a_stage_shaped_line_in_a_file_that_holds_an_exempt_line_still_fails():
    """Run the real scan on the real text of a file with an exempt line, plus one added line: the exempt line stays
    excused, the added line is a hit."""
    rel, line = "demos/ask-your-data/askdata/evalset.py", 'split: Literal["dev", "test"]'
    text = (ROOT / rel).read_text(encoding="utf-8")
    assert _scan_text(rel, text)[0] == [], "the file as it is should be clean"
    for added in (
        f"environment: {OLD}",
        f'ENV = "{OLD}"',
        f'split: Literal["{OLD}", "test", "pilot"]',
    ):
        found, used = _scan_text(rel, text + "\n" + added + "\n")
        assert len(found) == 1 and added in found[0], f"the added line was not found: {added}"
        assert used == {(rel, line)}


def _lookalike(word: str) -> str:
    """The word with its e written as a Cyrillic ie (a code point, so no look-alike literal in this file)."""
    return word.replace("e", chr(0x0435))


# One template per shape; {w} is each of the three words in turn (the old word, staging, the bare stage), {W} upper case.
SHAPES = [
    "environment: {w}",
    'environment="{w}"',
    '"environment": "{w}"',
    "ENV={w}",  # unquoted, and the CLI and CI forms
    "APP_ENV={w}",
    "docker run --env {w} app",
    "      env: {w}",
    "STAGE_{W}",  # an enum or constant name, and an enum member
    "Environment.{W}",
    "tier: {w}",
    "profile={w}",
    '"mode": "{w}"',
    'x = {{"{w}": 1}}',  # a dict key
    "    case '{w}':",
    "y = 1 if ok else '{w}'",  # a conditional expression
    '    "{w}",',  # a set or list member alone on its line
    'if env == "{w}":',
    "x = {w}|pilot|prod",
    "demo, {w}",
    "  - {w}",
]
# Only for the old word: "stage" and "staging" are ordinary words in these places.
OLD_ONLY = [
    "{W}_ONLY = frozenset()",
    "def {w}_cfg(tmp_path):",
    "def test_x_outside_{w}(cfg):",
    "kept in {w} for the tests",
    "kinds allowed only in `{w}`.",
    "a {w} executor",
    "https://{w}.example.org/x",
    "## Running in {w}",
]


@pytest.mark.parametrize("shape", SHAPES)
def test_the_scanner_finds_each_shape_for_each_word(shape):
    for word in (OLD, "staging", "stage"):
        line = shape.format(w=word, W=word.upper())
        assert _hits(line), f"not found: {line}"


@pytest.mark.parametrize("shape", OLD_ONLY)
def test_the_scanner_finds_each_old_word_only_shape(shape):
    line = shape.format(w=OLD, W=OLD.upper())
    assert _hits(line), f"not found: {line}"


FULLWIDTH = "".join(chr(0xFF00 + ord(c) - 0x20) for c in OLD)


@pytest.mark.parametrize(
    "word", [FULLWIDTH, _lookalike(OLD), "D" + chr(0x0435) + "V", OLD[0] + chr(0x200B) + OLD[1:]]
)
def test_the_scanner_finds_the_word_spelled_with_look_alike_letters(word):
    for line in (f"environment: {word}", f'x = "{word}"', f"demo, {word}"):
        assert _hits(line), f"not found: {line!r}"
    assert _hits(f"environment: {_lookalike('staging')}"), "staging with a look-alike letter"


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
        "the demo stage and the pilot stage",
        "  - demo",
        f'default-groups = ["{OLD}x"]',
        f"mode: {OLD}elop",
        'pytest.mark.parametrize("test")',
    ],
)
def test_the_scanner_ignores_words_that_are_not_stage_positions(line):
    assert not _hits(line), f"false hit: {line}: {_hits(line)}"


@pytest.mark.parametrize("name", ["env", "environment", "tier", "stage", "profile", "mode"])
def test_the_reach_between_a_stage_name_and_the_old_word_is_four_characters(name):
    """`stage = "dev"` has four characters (space, equals, space, quote) between the words, `"mode": "dev"` has four
    as well: both found. Five is outside the position."""
    for sep in ('": "', ' = "', '"=: ', "':'", ": ", "="):
        assert _hits(name + sep + OLD), f"not found: {name}{sep}{OLD}"
    assert not _hits(name + " " * 5 + OLD), "the reach is four characters, not more"


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
