"""P0t: the stages are exactly demo, pilot and prod (R449). The old first stage name is refused, never read as a stage
(except on READ of an old stored value, which maps to demo and never rewrites history), and a class test keeps the old
word out of every place that names a stage.

Rows (BN-1 of the ticket): (a) stored old value read as demo, history untouched; (b) unknown stage and half-renamed flag
refuse start; (c) the class test looks at stage POSITIONS only; (d) pilot and prod refuse relaxed kinds.
"""

import hashlib
import re
from pathlib import Path

import pytest
import yaml

from hadavin_sdk import config as config_mod
from hadavin_sdk import deferred
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.app import build
from hadavin_sdk.backends import table
from hadavin_sdk.config import STAGES, Config, ConfigError, load_config, stage_from_stored
from hadavin_sdk.registry import _module_pin_problems, load_registry
from tests.conftest import make_cfg, qualify

# The old word is built from parts in this file: the class test never scans this file, but a grep for it should find
# only the places that matter.
OLD = "d" + "ev"
RENAMED = "stage " + OLD + " was renamed demo"
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


def test_the_stages_are_exactly_demo_pilot_prod():
    assert STAGES == ("demo", "pilot", "prod")
    assert deferred.LIVE == ("pilot", "prod"), (
        "the live stages are pilot and prod: demo is not live"
    )


def test_dev_is_refused_with_the_rename(cfg_dir):
    _set_env(cfg_dir, OLD)
    with pytest.raises(ConfigError) as via_load:
        load_config(cfg_dir)
    assert RENAMED in str(via_load.value), "the refusal does not name the rename"
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
    """BN-1 (d): the fake model, the memory store, the other fakes and the loopback switch."""
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


# --- BN-1 (a): a stored old value is read as demo, history is never rewritten -----------------------------------------


def test_a_stored_old_value_reads_as_demo_and_the_input_is_not_changed():
    stored = {"environment": OLD}
    before = repr(stored)
    assert stage_from_stored(stored["environment"]) == "demo", (
        "a stored old stage value was not read as demo"
    )
    assert repr(stored) == before
    for stage in STAGES:
        assert stage_from_stored(stage) == stage


def test_a_stored_unknown_value_is_refused_not_guessed():
    for value in ["Demo", "staging", "uat", "", " " + OLD, OLD + " ", None, 3, b"demo"]:
        try:
            got = stage_from_stored(value)
        except ConfigError as exc:
            assert "stored stage" in str(exc)
        else:
            raise AssertionError(f"a stored unknown stage was accepted: {value!r} -> {got!r}")


def test_reading_an_old_stored_value_leaves_the_audit_hash_chain_as_it_was():
    """The body that was hashed says dev; the reader maps it to demo for display, and the chain still verifies."""
    from hadavin_sdk.audit import chain

    body = '{"environment":"' + OLD + '"}'
    at, run_id, kind = "2026-01-01T00:00:00.000000+00:00", "r1", "run.start"
    stored_hash = chain._hash(chain.GENESIS, 1, at, run_id, kind, body)
    assert stage_from_stored(yaml.safe_load(body)["environment"]) == "demo"
    assert chain._hash(chain.GENESIS, 1, at, run_id, kind, body) == stored_hash
    renamed = body.replace(OLD, "demo")
    assert chain._hash(chain.GENESIS, 1, at, run_id, kind, renamed) != stored_hash, (
        "a rewritten body must break the chain: that is why history is never rewritten"
    )
    assert hashlib.sha256(body.encode()).hexdigest() != hashlib.sha256(renamed.encode()).hexdigest()


# --- BN-1 (b): fail closed on a half-renamed flag ----------------------------------------------------------------------


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


# --- BN-1 (c): the class test, stage POSITIONS only ------------------------------------------------------------------

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
    "url host": re.compile(r"://" + OLD + r"\.|://[^/\s]*-" + OLD + r"\.", re.IGNORECASE),
    "heading": re.compile(r"^#{1,6} .*" + _W, re.IGNORECASE),
}
SCANNED = (
    ("src", ("*.py",)),
    ("tests", ("*.py", "*.yaml", "*.yml")),
    ("docs", ("*",)),
    ("demos", ("*.py", "*.md", "*.yaml", "*.json")),
    (".", ("README.md", "SECURITY.md")),
)
SELF = Path(__file__).resolve()


def _hits(line: str, markdown: bool = True) -> list[str]:
    """Names of the positions in `line`. A heading is a position in a Markdown file only (a `#` line in code is a comment)."""
    line = re.sub(
        r"\bfor \w+ in " + OLD + r"\b", "", line, flags=re.IGNORECASE
    )  # `for row in dev`: a dataset split, not a stage
    return [n for n, rx in POSITIONS.items() if rx.search(line) and (markdown or n != "heading")]


def _scan() -> list[str]:
    out = []
    for folder, patterns in SCANNED:
        base = ROOT / folder
        if not base.is_dir():
            continue
        for pattern in patterns:
            for path in base.glob(pattern) if folder == "." else base.rglob(pattern):
                if not path.is_file() or path.resolve() == SELF or "__pycache__" in path.parts:
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                for number, line in enumerate(text.splitlines(), 1):
                    if names := _hits(line, path.suffix == ".md"):
                        out.append(
                            f"{path.relative_to(ROOT)}:{number} [{', '.join(names)}] {line.strip()[:100]}"
                        )
    return sorted(set(out))


def test_the_old_stage_word_is_gone():
    found = _scan()
    assert not found, "the old stage word is still used as a stage:\n" + "\n".join(found)


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
        'split = "' + OLD + '"  # the eval split',
        f"{OLD} split of the dataset",
        "(?:com|net|io|" + OLD + "|ai|cloud)",
        "[dependency-groups]",
        f'{OLD} = ["pytest"]',
        "Dev-tool constants",
        "environment variable HADAVIN_X",
        "environment: demo",
        f"for row in {OLD}:",
    ],
)
def test_the_scanner_ignores_words_that_are_not_stage_positions(line):
    assert not _hits(line), f"false hit: {line}: {_hits(line)}"


def test_the_scan_reads_the_places_it_claims_to():
    seen = {p for p in (ROOT / "src").rglob("*.py")}
    assert (ROOT / "src" / "hadavin_sdk" / "config.py") in seen
    assert (ROOT / "tests" / "fixtures" / "config" / "config.yaml").is_file()
    assert (
        POSITIONS["config value"].search((ROOT / "tests/fixtures/config/config.yaml").read_text())
        is None
    )


# --- BN-2 (3): the redactor treats stage words as ordinary words, so `demo` joins them ----------------------------------


def test_the_redactor_does_not_sweep_the_stage_words_but_still_sweeps_secrets_and_other_names():
    from hadavin_sdk.guard.redact import _sweep

    for word in ("prod", "demo", OLD):
        assert _sweep("<TENANT_1>", word) is None, f"{word} is swept like a name"
    assert _sweep("<TENANT_1>", "acme" + "corp") is not None
    assert _sweep("<SECRET_1>", "demo") is not None, (
        "a secret that reads 'demo' must still be swept"
    )
