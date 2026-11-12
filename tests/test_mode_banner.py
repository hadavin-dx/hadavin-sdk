"""The mode banner: what a screen says about the stage and the services it is connected to. Made-up data only.

The words live in hadavin_sdk.mode_banner; the page script (templates/mode-banner/mode_banner.js) only paints them.
Rows: made-up data is claimed only in the demo stage with nothing real connected; every connected real service is named;
stand-ins are listed (loudly in the demo stage, in every stage); the stage and both lists are read from the config in one
place and the lists have no default; a value nobody checked (stage, bare string, odd name, name with a reserved word) is
refused; the page script never hides, half paints or throws, refuses a self-contradicting banner, never parses HTML and
falls back to the same words as the Python fallback.
"""

from __future__ import annotations

import ast
import json
import os
import random
import re
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from hadavin_sdk import mode_banner as mb
from hadavin_sdk.backends.table import DEMO_ONLY, TABLE
from hadavin_sdk.config import load_config
from hadavin_sdk.stages import STAGES
from tests.conftest import make_cfg

# The old first stage name, built from parts so the stage-name class test (test_stage_names) finds no stage position
# for it in this file. It is used only as a value that must be refused.
OLD_STAGE_WORD = "d" + "ev"

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "templates" / "mode-banner" / "mode_banner.js"
PROBE = Path(__file__).resolve().parent / "mode_banner_probe.js"
NAMES = {"crm": "CRM", "mail": "mail", "ai": "AI step"}

needs_node = pytest.mark.skipif(
    shutil.which("node") is None and os.environ.get("HADAVIN_REQUIRE_NODE") != "1",
    reason="node is not installed",
)


# -- the words and the choice between them ---------------------------------------------------------------------------
def _b(mode: str, real: list[str] | None = None, pretend: list[str] | None = None, **kw: object):
    return mb._banner_for(mode, real_services=real or [], stand_ins=pretend or [], **kw)  # type: ignore[arg-type]


def test_demo_with_only_stand_ins_says_made_up_and_lists_the_stand_ins_loudly() -> None:
    b = _b("demo", [], ["crm", "mail"], names=NAMES)
    assert (b.mode, b.tone, b.tag) == ("demo", "demo", "DEMO")
    assert (
        "made-up demo data" in b.text
        and "Nothing here is set up to send data to real customers" in b.text
    )
    assert (
        b.standins.startswith("MADE-UP STAND-INS IN USE: CRM, mail.")
        and "pretend versions" in b.standins
    )
    assert b.real == () and b.stand_ins == ("CRM", "mail")


def test_demo_with_no_stand_ins_still_says_nothing_real_is_connected() -> None:
    b = _b("demo")
    assert b.tone == "demo" and "made-up demo data" in b.text
    assert b.standins == "No real service is connected."


def test_a_real_service_is_named_and_made_up_data_is_never_claimed() -> None:
    for mode in STAGES:
        b = _b(mode, ["crm", "mail"], ["ai"], names=NAMES)
        assert b.tone == "real" and b.tag == mb.DEFAULT_WORDS.tag_by_mode[mode]
        assert (
            "Real services are connected: CRM, mail." in b.text and "may be sent to them" in b.text
        )
        assert "made-up" not in b.text and "Nothing here is set up to send data" not in b.text
        assert b.standins == "Still stand-ins, not connected: AI step."


def test_pilot_or_live_with_nothing_real_is_quiet_and_not_made_up() -> None:
    for mode, tag in [("pilot", "PILOT"), ("prod", "LIVE")]:
        b = _b(mode, [], [], names=NAMES)
        assert (b.tone, b.tag, b.text, b.standins) == (
            "quiet",
            tag,
            "No real service is connected.",
            "",
        )
        assert "made-up" not in b.text


def test_pilot_or_live_still_lists_the_stand_ins_in_the_quiet_tone() -> None:
    for mode in ("pilot", "prod"):
        b = _b(mode, [], ["ai", "mail"], names=NAMES)
        assert b.tone == "quiet" and b.text == "No real service is connected."
        assert b.standins == "Still stand-ins, not connected: AI step, mail."
        assert b.stand_ins == ("AI step", "mail")
        assert "made-up" not in (b.text + b.standins).lower()


def test_a_service_that_is_both_real_and_listed_as_stand_in_counts_as_real() -> None:
    b = _b("demo", ["crm"], ["crm", "mail"], names=NAMES)
    assert b.real == ("CRM",) and b.stand_ins == ("mail",)


def test_names_come_from_the_caller_and_repeats_are_shown_once_in_order() -> None:
    b = _b("pilot", ["b", "a", "b"], names={"a": "Alpha", "b": "Beta"})
    assert b.real == ("Beta", "Alpha")


def test_a_key_without_a_shown_name_is_read_as_component_and_the_key() -> None:
    assert _b("pilot", ["llm", "store"]).real == ("component llm", "component store")
    assert _b("pilot", ["llm"], names={"other": "Other"}).real == ("component llm",)


def test_the_words_can_be_replaced_without_changing_which_sentence_is_chosen() -> None:
    words = mb.BannerWords(tag_by_mode={"demo": "D", "pilot": "P", "prod": "L"}, made_up="MADE.")
    b = _b("demo", words=words)
    assert b.tag == "D" and b.text.startswith("MADE.")
    assert _b("demo", ["x"], words=words).tone == "real"  # the choice is not in the words


def test_the_default_words_have_a_tag_for_every_stage_and_a_missing_one_is_refused() -> None:
    assert set(mb.DEFAULT_WORDS.tag_by_mode) == set(STAGES)
    with pytest.raises(ValueError, match="no tag for the stage"):
        mb.BannerWords(tag_by_mode={"demo": "D"})


def test_the_lists_are_required_so_an_unchecked_call_cannot_say_nothing_real() -> None:
    for call in (
        lambda: mb._banner_for("demo"),  # type: ignore[call-arg]
        lambda: mb._banner_for("demo", real_services=[]),  # type: ignore[call-arg]
        lambda: mb._banner_for("demo", stand_ins=[]),  # type: ignore[call-arg]
        lambda: mb._banner_for("demo", [], []),  # type: ignore[misc]
    ):
        with pytest.raises(TypeError):
            call()


def test_an_unknown_stage_is_refused() -> None:
    for mode in ["", "DEMO", "Demo", "canary", "live", "test", None, 3]:
        with pytest.raises(ValueError, match="is not one of demo, pilot, prod"):
            _b(mode)  # type: ignore[arg-type]


def test_a_bare_string_dict_set_or_non_list_is_refused_not_read_by_accident() -> None:
    for bad in ["crm", b"crm", None, 5, {"crm": "CRM"}, {"crm"}, frozenset({"crm"})]:
        for kwargs in (
            {"real_services": bad, "stand_ins": []},
            {"real_services": [], "stand_ins": bad},
        ):
            with pytest.raises(TypeError, match="must be a list of service names"):
                mb._banner_for("demo", **kwargs)  # type: ignore[arg-type]


def test_names_that_are_not_a_mapping_are_refused_with_a_type_error() -> None:
    for bad in (["crm", "CRM"], "crm=CRM", 5, ("a",)):
        with pytest.raises(TypeError, match="names must be a mapping"):
            _b("pilot", ["crm"], names=bad)


HOSTILE_NAMES = [
    "",
    "a\nb",
    "Every record here is real.\nDEMO",
    "<b>x</b>",
    'quote"',
    "x" * 41,
    " lead",
    "trail ",
    "double  space",
    "a\u202eb",
    "\u00e9",
    "Mail. All data is made up",
    "Mail.",
    "a. b",
    "Nothing is real",
    "made-up",
    "Made Up CRM",
    "Demo CRM",
    "REAL CRM",
    "Stand-in mail",
    "standin",
    "nothing is sent",
]


def test_a_name_that_could_change_the_sentence_is_refused() -> None:
    for name in HOSTILE_NAMES:
        with pytest.raises(ValueError, match="plain words|non-empty"):
            _b("pilot", ["k"], names={"k": name})
        with pytest.raises(ValueError, match="plain words|non-empty"):
            _b("pilot", [name])
        with pytest.raises(ValueError, match="plain words|non-empty"):
            _b("demo", [], [name])


def test_a_plain_name_of_the_longest_allowed_length_is_shown_and_one_more_character_is_not() -> (
    None
):
    assert _b("pilot", ["k"], names={"k": "x" * 40}).real == ("x" * 40,)
    for ok in ("Mail 2", "a-b", "x.y", "z_9", "Mail.com", "AI step"):
        assert _b("pilot", ["k"], names={"k": ok}).real == (ok,)
    with pytest.raises(ValueError, match="plain words"):
        _b("pilot", ["k"], names={"k": "x" * 41})


def test_a_service_key_that_is_not_text_is_refused() -> None:
    with pytest.raises(ValueError, match="non-empty text"):
        _b("demo", [3])  # type: ignore[list-item]


def test_a_banner_longer_than_the_page_script_accepts_is_refused_in_python() -> None:
    long_names = {f"k{i}": f"{chr(65 + i)}" * 40 for i in range(20)}
    with pytest.raises(ValueError, match="too many services"):
        _b("pilot", list(long_names), names=long_names)
    with pytest.raises(ValueError, match="too many services"):
        _b("pilot", [], list(long_names), names=long_names)
    ok = {f"k{i}": f"{chr(65 + i)}" * 20 for i in range(10)}
    assert len(_b("pilot", list(ok), names=ok).text) <= mb.MAX_TEXT_LENGTH


# -- property test, seeded: only the safety property is asserted, never the rule that produces the text -------------
def test_property_the_made_up_claim_never_appears_next_to_a_real_service() -> None:
    rng = random.Random(20261112)  # noqa: S311 - a seeded test generator, not a secret
    good = ["crm", "mail", "ai", "store", "Chat", "x.y", "a-b", "z_9"]

    def pick() -> str:  # mostly plain names, sometimes a hostile one
        return rng.choice(HOSTILE_NAMES if rng.random() < 0.08 else good)

    refused = shown = 0
    for _ in range(1500):
        mode = rng.choice(STAGES if rng.random() < 0.95 else [OLD_STAGE_WORD, "", "DEMO"])
        real = [pick() for _ in range(rng.randint(0, 3))]
        pretend = [pick() for _ in range(rng.randint(0, 3))]
        names = {pick(): pick() for _ in range(rng.randint(0, 2))}
        try:
            b = mb._banner_for(mode, real_services=real, stand_ins=pretend, names=names)
        except (ValueError, TypeError):
            refused += 1
            continue
        shown += 1
        text = (b.text + "\n" + b.standins).lower()
        if real:  # a real service was connected: nothing may call the data made up, and the line says "real"
            assert "made-up" not in text and "made up" not in text, (mode, real, b)
            assert b.tone == "real"
        assert not any(ord(c) < 32 for c in b.text + b.standins)
        assert json.loads(json.dumps(b.as_dict()))["tone"] == b.tone
    assert shown > 100 and refused > 100  # the generator reached both outcomes


# -- reading the stage and both lists from a loaded config -----------------------------------------------------------
def _fake_config(environment: str, kinds: list[tuple[str, object]]) -> SimpleNamespace:
    entries = [(c, SimpleNamespace(kind=k)) for c, k in kinds]
    return SimpleNamespace(
        environment=environment,
        backends=SimpleNamespace(entries=lambda: entries),
        systems={},
        egress_hosts=frozenset(),
        sources={},
        tool_modules=[],
    )


def _banner(cfg, tool_specs: object = None, **kw):
    """banner_from_config with the registry's tools given as 'none declared' unless a test says otherwise."""
    return mb.banner_from_config(cfg, tool_specs={} if tool_specs is None else tool_specs, **kw)


def _services(cfg, tool_specs: object = None):
    return mb._services_in(cfg, {} if tool_specs is None else tool_specs)


NOTHING = {("signer", "none"), ("anchor", "none"), ("detector", "regex")}


def test_banner_from_config_reads_the_stage_and_both_lists_from_the_config(tmp_path: Path) -> None:
    cfg = load_config(make_cfg(tmp_path))  # the fixture is the demo config and holds fakes
    real, pretend = _services(cfg)
    assert real == () and {"llm", "channel", "secrets", "store"} <= set(pretend)
    b = _banner(cfg)
    assert (b.mode, b.tone) == (cfg.environment, "demo")
    assert b.stand_ins == tuple(f"component {c}" for c in pretend) and b.real == ()
    assert {(c, s.kind) for c, s in cfg.backends.entries() if c in pretend} <= DEMO_ONLY
    for named in ("demo", "pilot", "prod"):  # the stage is read from the config, never fixed
        assert _banner(_fake_config(named, [("llm", "anthropic")])).mode == named


def test_a_real_kind_in_the_config_is_named_and_the_made_up_sentence_is_never_given() -> None:
    cfg = _fake_config("demo", [("llm", "anthropic"), ("store", "memory"), ("signer", "none")])
    b = _banner(cfg, names={"llm": "AI step"})
    assert b.tone == "real" and b.real == ("AI step",) and b.stand_ins == ("component store",)
    assert "made-up" not in (b.text + b.standins).lower()
    for stage in STAGES:
        assert _banner(_fake_config(stage, [("llm", "bedrock")])).tone == "real"


def test_property_every_config_entry_lands_in_exactly_one_group() -> None:
    rng = random.Random(20261112)  # noqa: S311 - a seeded test generator, not a secret
    every = [(c, k) for c, kinds in TABLE.items() for k in kinds]
    for _ in range(400):
        picks = rng.sample(every, rng.randint(0, len(every)))
        cfg = _fake_config(rng.choice(STAGES), picks)
        real, pretend = _services(cfg)
        for component, kind in picks:
            if (component, kind) in DEMO_ONLY:
                assert component in pretend
            elif (component, kind) not in NOTHING:
                assert component in real
        b = _banner(cfg)
        shown = (b.text + b.standins).lower()
        if real:
            assert b.tone == "real" and "made-up" not in shown


def test_an_entry_without_a_kind_is_refused_not_guessed_into_a_list() -> None:
    for bad_kind in (None, "", 3):
        with pytest.raises(ValueError, match="cannot be placed in the banner"):
            _banner(_fake_config("demo", [("llm", bad_kind)]))
    with pytest.raises(ValueError, match="cannot be placed in the banner"):
        _banner(_fake_config("demo", [("", "fake")]))


def test_the_stage_of_the_config_is_checked_like_any_other_stage() -> None:
    with pytest.raises(ValueError, match="is not one of demo, pilot, prod"):
        _banner(_fake_config("canary", [("llm", "fake")]))


def test_the_old_public_names_are_gone_and_banner_from_config_is_the_only_entry() -> None:
    for old in ("banner_for", "services_in", "stand_ins_in"):
        assert not hasattr(mb, old), old
        assert old not in mb.__all__
    assert [n for n in mb.__all__ if n.startswith("banner")] == ["banner_from_config"]
    assert all(hasattr(mb, n) for n in mb.__all__)
    star: dict = {}
    exec("from hadavin_sdk.mode_banner import *", star)  # noqa: S102 - the public surface, a fixed string
    assert "banner_from_config" in star and not any(
        k.startswith("_") for k in star if k != "__builtins__"
    )


# -- no module of core may grow its own loopback list (the shared one comes with the network-guard promotion) --------
LOOPBACK = {"127.0.0.1", "localhost", "::1"}
# The files that already hold their own copy, each to be removed when part 2 (the shared network guard) lands.
HAVE_OWN_LOOPBACK_LIST = {
    "actions/secrets_vault.py": "part 2 replaces it with the shared guard",
    "backends/table.py": "part 2 replaces it with the shared guard",
    "config.py": "part 2 replaces it with the shared guard",
    "guard/http.py": "part 2 replaces it with the shared guard",
    "llm/openai_compat.py": "part 2 replaces it with the shared guard",
}


def test_no_new_module_keeps_its_own_loopback_list() -> None:
    src = ROOT / "src" / "hadavin_sdk"
    found: set[str] = set()
    for path in sorted(src.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.Set, ast.Tuple, ast.List)):
                strings = {e.value for e in node.elts if isinstance(e, ast.Constant)}
                if len(strings & LOOPBACK) >= 2:
                    found.add(path.relative_to(src).as_posix())
    assert found == set(HAVE_OWN_LOOPBACK_LIST), sorted(found ^ set(HAVE_OWN_LOOPBACK_LIST))


# -- the page script ------------------------------------------------------------------------------------------------
def _paint(banner: object, scenario: str = "") -> dict:
    arg = "undefined" if banner is None else json.dumps(banner)
    out = subprocess.run(  # noqa: S603 (fixed argument list, no shell)
        ["node", str(PROBE), str(JS), arg, scenario],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return json.loads(out.stdout.strip().splitlines()[-1])


def _unconfirmed(seen: dict) -> None:
    assert seen["threw"] == "" and seen["htmlWrites"] == []
    assert seen["hidden"] is False and seen["tone"] == "unconfirmed" and seen["mode"] == ""
    assert seen["shownTone"] == "unconfirmed"
    assert seen["lines"][0]["text"] == mb.not_confirmed()["tag"]
    assert seen["lines"][1]["text"] == " " + mb.not_confirmed()["text"]


@needs_node
def test_the_page_paints_exactly_what_python_wrote() -> None:
    banners = [
        _b("demo", [], ["crm"], names=NAMES),
        _b("demo", ["crm"], ["mail"], names=NAMES),
        _b("pilot", [], []),
        _b("pilot", [], ["mail"]),
        _b("prod", ["mail"], []),
    ]
    for banner in banners:
        seen = _paint(banner.as_dict())
        assert seen["threw"] == "" and seen["htmlWrites"] == []
        assert (
            seen["hidden"] is False and seen["tone"] == banner.tone and seen["mode"] == banner.mode
        )
        assert seen["lines"][0] == {"cls": "mode-banner__tag", "text": banner.tag}
        assert seen["lines"][1] == {"cls": "mode-banner__text", "text": " " + banner.text}
        assert len(seen["lines"]) == (3 if banner.standins else 2)
        if banner.standins:
            assert seen["lines"][2] == {"cls": "mode-banner__standins", "text": banner.standins}


GOOD_DEMO = {
    "mode": "demo", "tone": "demo", "tag": "DEMO", "text": "t", "standins": "s", "real": [], "stand_ins": ["a"],
}  # fmt: skip


@needs_node
def test_a_missing_or_odd_banner_is_never_hidden_it_says_not_confirmed() -> None:
    bad_banners = [
        None,
        {},
        [],
        "demo",
        {"tone": "demo"},
        {"tone": "fine", "tag": "T", "text": "x"},
        {"tone": "demo", "tag": "", "text": "x"},
        {"tone": "demo", "tag": "T", "text": 5},
        {"tone": "demo", "tag": "T", "text": "x" * 601},
        {"tone": "demo", "tag": "T", "text": "x", "standins": 7},
        {**GOOD_DEMO, "standins": "x" * 601},
        {**GOOD_DEMO, "tone": "unconfirmed"},
        {**GOOD_DEMO, "tone": "fine"},
        {**GOOD_DEMO, "real": "crm"},
        {**GOOD_DEMO, "stand_ins": "a"},
        {**GOOD_DEMO, "stand_ins": [1]},
        {**GOOD_DEMO, "stand_ins": {"0": "a"}},
        {k: v for k, v in GOOD_DEMO.items() if k != "real"},
        {k: v for k, v in GOOD_DEMO.items() if k != "stand_ins"},
    ]
    for bad in bad_banners:
        _unconfirmed(_paint(bad))
    _unconfirmed(_paint(GOOD_DEMO, "throwing-list"))
    _unconfirmed(_paint(GOOD_DEMO | {"tone": "real", "real": ["x"], "text": "x"}, "throwing-list"))


@needs_node
def test_a_banner_that_contradicts_itself_is_not_painted_as_given() -> None:
    real = {"mode": "pilot", "tone": "real", "tag": "PILOT", "text": "Real services: CRM.", "standins": "", "real": ["CRM"], "stand_ins": []}  # fmt: skip
    quiet = {"mode": "pilot", "tone": "quiet", "tag": "PILOT", "text": "None.", "standins": "", "real": [], "stand_ins": []}  # fmt: skip
    fine = [GOOD_DEMO, real, quiet]
    for banner in fine:  # the controls: consistent banners ARE painted as given
        seen = _paint(banner)
        assert seen["tone"] == banner["tone"] and seen["mode"] == banner["mode"]
    wrong = [
        {**GOOD_DEMO, "mode": "prod"},  # tone demo needs mode demo
        {**GOOD_DEMO, "mode": "pilot"},
        {**GOOD_DEMO, "real": ["CRM"]},  # tone demo needs no real service
        {**real, "real": []},  # tone real needs a real service
        {
            **real,
            "text": "Every record here is made-up demo data.",
        },  # tone real must name every real service
        {**real, "real": ["CRM", "Mail"]},  # ... all of them
        {**quiet, "real": ["CRM"]},  # tone quiet needs no real service
        {**quiet, "mode": "demo"},  # tone quiet is for pilot and prod only
        {**real, "mode": OLD_STAGE_WORD},
        {**real, "mode": ""},
        {**real, "mode": "DEMO"},
        {**real, "mode": 3},
        {**real, "mode": "<b>"},
    ]
    for banner in wrong:
        _unconfirmed(_paint(banner))


@needs_node
def test_the_painter_never_throws_and_never_leaves_the_page_blank() -> None:
    for scenario in ("throwing-getter", "proxy"):
        seen = _paint(GOOD_DEMO, scenario)
        assert seen["usableThrew"] == ""  # usable() called on its own never throws either
        _unconfirmed(seen)
    seen = _paint(GOOD_DEMO, "throwing-doc")  # the page cannot make elements at all
    assert seen["threw"] == "" and seen["tone"] == "unconfirmed" and seen["hidden"] is False
    assert seen["text"] == f"{mb.not_confirmed()['tag']} {mb.not_confirmed()['text']}"
    seen = _paint(GOOD_DEMO, "null-el")  # no element to paint into: no throw, nothing to show
    assert seen["threw"] == "" and seen["lines"] == [] and seen["shownTone"] == "demo"
    seen = _paint(
        GOOD_DEMO, "failing-append"
    )  # painting fails half way: the plain "not confirmed" text is put in
    assert seen["threw"] == "" and seen["tone"] == "unconfirmed" and seen["hidden"] is False
    assert seen["text"] == f"{mb.not_confirmed()['tag']} {mb.not_confirmed()['text']}"


@needs_node
def test_the_page_fallback_has_the_same_words_as_the_python_fallback() -> None:
    assert _paint(None)["notConfirmed"] == mb.not_confirmed()


@needs_node
def test_the_page_lists_are_the_python_lists() -> None:
    seen = _paint(None)
    assert seen["modes"] == list(STAGES) and seen["tones"] == list(mb.TONES)
    assert seen["maxText"] == mb.MAX_TEXT_LENGTH
    assert re.search(rf"var MAX_TEXT = {mb.MAX_TEXT_LENGTH};", JS.read_text(encoding="utf-8"))


@needs_node
def test_markup_in_the_text_is_shown_as_text_never_parsed() -> None:
    evil = "<img src=x onerror=alert(1)>"
    banner = {
        "mode": "pilot", "tone": "real", "tag": "<b>", "text": evil + " CRM", "standins": "<i>", "real": ["CRM"], "stand_ins": [],
    }  # fmt: skip
    seen = _paint(banner)
    assert seen["htmlWrites"] == []  # no write that would parse HTML, whatever it is called
    assert seen["lines"][1]["text"] == " " + evil + " CRM" and seen["lines"][0]["text"] == "<b>"


def test_the_page_script_has_no_way_to_parse_html_or_load_anything() -> None:
    text = JS.read_text(encoding="utf-8")
    for banned in (
        "innerHTML",
        "outerHTML",
        "insertAdjacentHTML",
        "insertAdjacentElement",
        "createContextualFragment",
        "document.write",
        "eval(",
        "fetch(",
        "XMLHttpRequest",
    ):
        assert banned not in text, banned
    assert "textContent" in text  # the check is not vacuous


# --- round 3: the made-up sentence is checked against every field that can name an endpoint -----------------------------


def _with_endpoints(**fields: object) -> SimpleNamespace:
    """A demo config of pretend services only, plus the given endpoint fields (systems, egress_hosts, sources)."""
    cfg = _fake_config("demo", [("llm", "fake"), ("store", "memory")])
    for name, value in fields.items():
        setattr(cfg, name, value)
    return cfg


def _system(url: str | None) -> SimpleNamespace:
    return SimpleNamespace(base_url=url)


def _source(url: str) -> SimpleNamespace:
    return SimpleNamespace(kind="kubernetes", settings={"api_url": url, "namespaces": ["x"]})


LEAVES = [
    ("systems", {"crm": _system("https://crm.example.test")}, mb.EXTERNAL_SYSTEMS),
    (
        "systems",
        {"a": _system("http://127.0.0.1"), "b": _system("https://crm.example.test")},
        mb.EXTERNAL_SYSTEMS,
    ),
    (
        "systems",
        {"crm": _system("http://localhost.example.test")},
        mb.EXTERNAL_SYSTEMS,
    ),  # not localhost
    ("systems", {"crm": _system("not a url")}, mb.EXTERNAL_SYSTEMS),  # unreadable: shown as real
    ("systems", {"crm": _system(None)}, mb.EXTERNAL_SYSTEMS),  # not text at all: shown as real
    ("egress_hosts", frozenset({"api.example.test"}), mb.EGRESS_HOSTS),
    ("egress_hosts", frozenset({"127.0.0.1", "10.0.0.5"}), mb.EGRESS_HOSTS),
    ("egress_hosts", frozenset({""}), mb.EGRESS_HOSTS),
    ("sources", {"k": _source("https://k8s.example.test")}, mb.READ_SOURCES),
    ("sources", {"k": SimpleNamespace(kind="unknown-kind", settings={})}, mb.READ_SOURCES),
    (  # a known kind whose settings do not build: the endpoint cannot be worked out
        "sources",
        {"k": SimpleNamespace(kind="kubernetes", settings={"api_url": 5})},
        mb.READ_SOURCES,
    ),
    (
        "systems",
        {"crm": _system("http://10.0.0.5")},
        mb.EXTERNAL_SYSTEMS,
    ),  # an IP literal that is not loopback
    (
        "systems",
        {"crm": _system("http://127.0.0.2")},
        mb.EXTERNAL_SYSTEMS,
    ),  # only the three shared names count
    ("egress_hosts", frozenset({"127.0.0.2"}), mb.EGRESS_HOSTS),
]
THIS_MACHINE = [
    ("systems", {"crm": _system("http://127.0.0.1:8080")}),
    ("systems", {"crm": _system("http://localhost:8080")}),
    ("systems", {"crm": _system("http://[::1]:8080")}),
    ("egress_hosts", frozenset({"127.0.0.1", "localhost", "::1"})),
    ("sources", {"k": _source("http://127.0.0.1:6443")}),
    ("systems", {}),
    ("egress_hosts", frozenset()),
    ("sources", {}),
]


def test_a_demo_config_that_can_reach_beyond_this_machine_is_not_called_made_up() -> None:
    for field, value, key in LEAVES:
        cfg = _with_endpoints(**{field: value})
        real, _ = _services(cfg)
        assert real == (key,), (field, value)
        b = _banner(cfg)
        assert b.tone == "real" and b.real == (f"component {key}",), (field, value)
        shown = (b.text + b.standins).lower()
        assert "made-up" not in shown and "nothing here is set up to send" not in shown, (
            field,
            value,
        )


@pytest.mark.parametrize(("field", "value"), THIS_MACHINE)
def test_endpoints_on_this_machine_keep_the_demo_banner(field, value) -> None:
    b = _banner(_with_endpoints(**{field: value}))
    assert (b.tone, b.real) == ("demo", ())


def test_a_real_loaded_demo_config_with_an_outside_system_gets_the_real_banner(
    tmp_path: Path,
) -> None:
    import yaml

    d = make_cfg(tmp_path)
    path = d / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["systems"]["fixture-records"]["base_url"] = "https://records.example.test"
    data["allow_insecure_loopback"] = False
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    b = _banner(load_config(d), names={mb.EXTERNAL_SYSTEMS: "Records system"})
    assert b.tone == "real" and b.real == ("Records system",) and "Records system" in b.text


def test_property_any_outside_endpoint_in_any_stage_never_gets_the_made_up_sentence() -> None:
    rng = random.Random(20261113)  # noqa: S311 - a seeded test generator, not a secret
    for _ in range(300):
        fields: dict[str, object] = {}
        outside = False
        if rng.random() < 0.5:
            urls = [
                rng.choice(["http://127.0.0.1", "http://localhost", "https://x.example.test"])
                for _ in range(rng.randint(1, 3))
            ]
            fields["systems"] = {f"s{i}": _system(u) for i, u in enumerate(urls)}
            outside |= any("example" in u for u in urls)
        if rng.random() < 0.5:
            hosts = frozenset(rng.sample(["127.0.0.1", "::1", "h.example.test"], rng.randint(1, 3)))
            fields["egress_hosts"] = hosts
            outside |= "h.example.test" in hosts
        cfg = _with_endpoints(**fields)
        cfg.environment = rng.choice(STAGES)
        b = _banner(cfg)
        assert (b.tone == "real") == outside
        if outside:
            assert "made-up" not in (b.text + b.standins).lower()


def test_a_banner_is_checked_against_what_it_claims_before_it_leaves() -> None:
    claim = mb.DEFAULT_WORDS
    tags = {"demo": "DEMO", "pilot": "PILOT", "prod": "LIVE"}
    # a reworded text that forgets to name the real services is refused, not shown
    forgetful = mb.BannerWords(tag_by_mode=tags, real_connected="Real services are connected.")
    with pytest.raises(ValueError, match="does not name every real service"):
        _banner(_fake_config("pilot", [("llm", "bedrock")]), words=forgetful)
    # a reworded real note that repeats the made-up sentence is refused in a real and in a quiet banner
    boastful = mb.BannerWords(tag_by_mode=tags, real_data_note=claim.made_up)
    with pytest.raises(ValueError, match="claims made-up data"):
        _banner(_fake_config("pilot", [("llm", "bedrock")]), words=boastful)
    quiet_boast = mb.BannerWords(tag_by_mode=tags, none_real=claim.made_up)
    with pytest.raises(ValueError, match="claims made-up data"):
        _banner(_fake_config("prod", []), words=quiet_boast)
    # a demo banner that names a real service is refused (built by hand: banner_from_config never makes one)
    hand_made = mb.ModeBanner(
        "demo", "demo", "DEMO", claim.made_up + " " + claim.nothing_sent, "", ("record",), ()
    )
    with pytest.raises(ValueError, match="demo banner must name no real service"):
        mb._check_what_is_claimed(hand_made, claim)


@needs_node
def test_the_page_exports_and_the_fallback_cannot_be_changed_by_a_page() -> None:
    assert _paint(None)["frozen"] == [True] * 6


@needs_node
def test_a_failed_last_resort_write_never_leaves_the_banner_hidden() -> None:
    seen = _paint(GOOD_DEMO, "failing-all-writes")  # appending and then the text write both throw
    assert seen["threw"] == "" and seen["hidden"] is False
    assert (
        seen["text"] == "previous banner text"
    )  # nothing was cleared before the failing write: the old words stay


@needs_node
def test_a_failed_append_leaves_words_on_the_screen_never_an_empty_banner() -> None:
    seen = _paint(GOOD_DEMO, "failing-append")
    assert seen["threw"] == "" and seen["hidden"] is False
    assert seen["text"].strip() != ""  # the fallback text is written, not just the attributes
    assert seen["text"] == mb.not_confirmed()["tag"] + " " + mb.not_confirmed()["text"]
    assert seen["tone"] == "unconfirmed"


@needs_node
def test_a_real_name_is_matched_as_a_whole_word_only() -> None:
    real = {
        "mode": "pilot",
        "tone": "real",
        "tag": "PILOT",
        "text": "Real services are connected: CRMS. Data this system handles may be sent to them.",
        "standins": "",
        "real": ["CRM"],
        "stand_ins": [],
    }
    _unconfirmed(_paint(real))  # "CRM" is only part of the word "CRMS": not named
    fine = {**real, "text": real["text"].replace("CRMS", "CRM")}
    assert _paint(fine)["tone"] == "real"


# --- round 4 ----------------------------------------------------------------------------------------------------------
from hadavin_sdk.tools import ToolSpec


def _spec(*hosts: str) -> ToolSpec:
    return ToolSpec(
        name="read_x",
        function="mod:read_x",
        description="reads x",
        input_schema={"type": "object"},
        side_effect="none",
        hosts=hosts,
    )


def test_tool_specs_has_no_default_so_forgetting_it_is_an_error() -> None:
    cfg = _fake_config("demo", [("llm", "fake")])
    with pytest.raises(TypeError):
        mb.banner_from_config(cfg)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        mb._services_in(cfg)  # type: ignore[call-arg]


def test_a_tool_manifest_host_that_is_not_this_machine_is_a_real_service() -> None:
    cfg = _fake_config("demo", [("llm", "fake")])
    specs = {"agent": {"read_x": _spec("api.example.test")}}
    real, _ = _services(cfg, specs)
    assert real == (mb.TOOL_HOSTS,)
    b = _banner(cfg, specs, names={mb.TOOL_HOSTS: "Tool services"})
    assert b.tone == "real" and b.real == ("Tool services",) and "Tool services" in b.text
    assert "made-up" not in (b.text + b.standins).lower()
    for stage in STAGES:
        assert _banner(_fake_config(stage, []), specs).tone == "real"


def test_tool_hosts_on_this_machine_or_none_keep_the_demo_banner() -> None:
    cfg = _fake_config("demo", [("llm", "fake")])
    for specs in (
        {},
        {"a": {}},
        {"a": {"t": _spec()}},
        {"a": {"t": _spec("127.0.0.1", "localhost", "::1")}},
    ):
        assert _banner(cfg, specs).tone == "demo", specs
    mixed = {"a": {"t": _spec("localhost")}, "b": {"u": _spec("api.example.test")}}
    assert _services(cfg, mixed)[0] == (mb.TOOL_HOSTS,)  # one outside host in any agent is enough


def test_tool_modules_without_the_manifests_count_as_one_real_service() -> None:
    cfg = _fake_config("demo", [("llm", "fake")])
    cfg.tool_modules = ["some_mod"]
    assert _services(cfg, None)[0] == ()  # the helper's {} default: manifests read and empty
    real, _ = mb._services_in(cfg, None)  # None: the caller could not read the manifests
    assert real == (mb.TOOL_MODULES,)
    assert mb.banner_from_config(cfg, tool_specs=None).tone == "real"
    cfg.tool_modules = []
    assert mb._services_in(cfg, None)[0] == ()  # no module configured: nothing hidden by None
    with pytest.raises(TypeError, match="tool_specs"):
        mb._services_in(cfg, ["not", "a", "mapping"])


def test_a_real_registry_tools_mapping_is_what_the_banner_reads(tmp_path: Path) -> None:
    from hadavin_sdk.registry import Registry

    assert "tools" in {f.name for f in __import__("dataclasses").fields(Registry)}
    cfg = load_config(make_cfg(tmp_path))
    assert mb.banner_from_config(cfg, tool_specs={}).tone == "demo"
    assert (
        mb.banner_from_config(cfg, tool_specs={"a": {"t": _spec("api.example.test")}}).tone
        == "real"
    )


def test_the_words_state_what_is_checked_and_not_a_false_premise() -> None:
    sentence = mb.DEFAULT_WORDS.nothing_sent
    assert "set up to send" in sentence and "reaches only" not in (mb.__doc__ or "")
    assert "not sandboxed" in (mb.__doc__ or "")  # the in-process limit is stated


@needs_node
def test_a_failed_page_write_keeps_non_empty_text() -> None:
    assert _paint(GOOD_DEMO, "failing-append")["text"].strip() != ""


# -- the URL rules are the ones the tool fetcher uses --------------------------------------------------------------------
LEAVING_URLS = [
    "https://evil.example\\@localhost",  # a backslash: browsers read it as a slash
    "http://127.0.0.1/a\\b",  # a backslash in the path
    "http://127.0.0.1/a b",
    "http://127.0.0.1/a\x01b",
    "http://127.0.0.1/caf\u00e9",
    "http://127.0.0.1/%2e%2e",
    "http://localhost%2f.evil.test",
    "http://user@127.0.0.1/",
    "http://127.0.0.1@evil.example/",
    "http://10.0.0.5/",  # an IP literal that is not loopback
    "http://[2001:db8::1]/",
    "http://127.0.0.2/",  # only the three shared loopback names are this machine
    "http://[::2]/",
    "http://\u2460\u2461\u2467.0.0.1/",
    "",
    "localhost",  # no scheme: no host
]


def test_an_odd_url_is_shown_as_leaving_this_machine() -> None:
    for url in LEAVING_URLS:
        b = _banner(_with_endpoints(systems={"s": _system(url)}))
        assert b.tone == "real" and b.real == (f"component {mb.EXTERNAL_SYSTEMS}",), f"url {url!r}"


def test_the_shared_normaliser_treats_these_as_this_machine() -> None:
    for url in ("http://LOCALHOST:80/", "http://localhost./", "http://[::1]/x", "http://127.0.0.1"):
        assert _banner(_with_endpoints(systems={"s": _system(url)})).tone == "demo", f"url {url!r}"


def test_the_banner_uses_the_shared_loopback_names_and_normaliser_not_a_copy() -> None:
    from hadavin_sdk.guard.egress import normalise_host
    from hadavin_sdk.guard.http import LOOPBACK as SHARED

    assert mb.LOOPBACK is SHARED and mb.normalise_host is normalise_host
    assert "ipaddress" not in (Path(mb.__file__).read_text(encoding="utf-8"))


def test_the_source_host_the_app_uses_comes_from_the_shared_endpoint_function() -> None:
    from hadavin_sdk import app
    from hadavin_sdk.sources.kinds import source_endpoint

    src = _source("https://K8S.example.test:6443")
    assert source_endpoint(src) == "https://K8S.example.test:6443"
    assert app._source_host(src) == "k8s.example.test"


def test_a_real_config_with_an_outside_egress_host_or_source_gets_the_real_banner(
    tmp_path: Path,
) -> None:
    import yaml

    d = make_cfg(tmp_path / "a")
    (d / "egress.yaml").write_text(
        yaml.safe_dump({"hosts": ["api.example.test"]}), encoding="utf-8"
    )
    b = _banner(load_config(d))
    assert b.tone == "real" and b.real == (f"component {mb.EGRESS_HOSTS}",)
    d2 = make_cfg(tmp_path / "b")
    data = yaml.safe_load((d2 / "config.yaml").read_text(encoding="utf-8"))
    data["sources"] = {
        "k": {
            "kind": "kubernetes",
            "settings": {"api_url": "https://k8s.example.test", "namespaces": ["x"]},
        }
    }
    (d2 / "config.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
    b2 = _banner(load_config(d2))
    assert b2.tone == "real" and b2.real == (f"component {mb.READ_SOURCES}",)
    data["sources"]["k"]["settings"]["api_url"] = "http://127.0.0.1:6443"
    (d2 / "config.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
    assert _banner(load_config(d2)).tone == "demo"


def test_a_config_that_lost_an_endpoint_field_raises_and_is_never_read_as_nothing(
    tmp_path: Path,
) -> None:
    real = load_config(make_cfg(tmp_path))
    fields = ("environment", "backends", "systems", "egress_hosts", "sources", "tool_modules")
    for missing in ("systems", "egress_hosts", "sources", "tool_modules"):
        kept = {
            f: getattr(real, f) for f in fields if f != missing
        }  # a real Config's values, one field gone
        with pytest.raises(ValueError, match=missing):
            _banner(SimpleNamespace(**kept))
        with pytest.raises(ValueError, match=missing):
            _banner(SimpleNamespace(**{**kept, missing: None}))


def test_an_empty_made_up_sentence_is_an_error_not_a_switched_off_check() -> None:
    tags = {"demo": "DEMO", "pilot": "PILOT", "prod": "LIVE"}
    for field in ("made_up", "nothing_sent"):
        words = mb.BannerWords(tag_by_mode=tags, **{field: "  "})
        with pytest.raises(ValueError, match="must not be empty"):
            _banner(_fake_config("demo", [("llm", "fake")]), words=words)


NAME_TABLE = [
    ("Real services are connected: CRM. Data may be sent.", "CRM", True),
    ("connected: CRMS.", "CRM", False),
    ("connected: xCRM.", "CRM", False),
    ("connected: CRM-2.", "CRM", False),
    ("connected: my-CRM.", "CRM", False),
    ("connected: CRM_x.", "CRM", False),
    ("connected: CRM2.", "CRM", False),
    ("connected: CRM.v2 ", "CRM", False),
    ("connected: a.CRM ", "CRM", False),
    ("connected: CRM.", "CRM", True),
    ("connected: (CRM).", "CRM", True),
    ("connected: CRM, mail.", "CRM", True),
    ("connected: CRMS and CRM.", "CRM", True),  # a longer word first, then the whole name
    ("connected: CRM and CRMS.", "CRM", True),
    ("connected: CRMS and xCRM.", "CRM", False),
    ("connected: crm.", "CRM", False),  # the match is case-sensitive in both
    ("connected: CRM.\u00e9", "CRM", True),  # a non-ASCII letter does not join in either
]


def test_names_in_follows_the_table() -> None:
    for text, name, expected in NAME_TABLE:
        assert mb.names_in(text, name) is expected, (text, name)
    assert mb.names_in("anything", "") is False


@needs_node
def test_the_page_and_python_agree_on_every_row_of_the_name_table() -> None:
    for text, name, expected in NAME_TABLE:
        banner = {
            "mode": "pilot", "tone": "real", "tag": "PILOT", "text": text, "standins": "",
            "real": [name], "stand_ins": [],
        }  # fmt: skip
        page_says_named = _paint(banner)["tone"] == "real"
        assert page_says_named is expected is mb.names_in(text, name), (text, name)
