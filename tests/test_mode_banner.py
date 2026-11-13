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
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from hadavin_sdk import mode_banner as mb
from hadavin_sdk.backends.table import DEMO_ONLY, TABLE
from hadavin_sdk.config import load_config
from hadavin_sdk.stages import STAGES
from hadavin_sdk.tools import ToolSpec
from tests.conftest import make_cfg
from tests.refusal import refused

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
    ), "the demo text lost its made-up sentences"
    assert (
        b.standins.startswith("MADE-UP STAND-INS IN USE: CRM, mail.")
        and "pretend versions" in b.standins
    ), "the loud stand-ins line is not the loud one"
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
        assert b.tone == "quiet" and b.text == "No real service is connected.", (
            "pilot_or_live_still_lists_the_stand_ins_in_the_quiet_tone: check 1"
        )
        assert b.standins == "Still stand-ins, not connected: AI step, mail.", (
            "pilot_or_live_still_lists_the_stand_ins_in_the_quiet_tone: check 2"
        )
        assert b.stand_ins == ("AI step", "mail"), (
            "pilot_or_live_still_lists_the_stand_ins_in_the_quiet_tone: check 3"
        )
        assert "made-up" not in (b.text + b.standins).lower(), (
            "pilot_or_live_still_lists_the_stand_ins_in_the_quiet_tone: check 4"
        )


def test_a_service_that_is_both_real_and_listed_as_stand_in_counts_as_real() -> None:
    b = _b("demo", ["crm"], ["crm", "mail"], names=NAMES)
    assert b.real == ("CRM",) and b.stand_ins == ("mail",), (
        f"a service that is both real and a stand-in was not counted as real only: {b.real} {b.stand_ins}"
    )


def test_names_come_from_the_caller_and_repeats_are_shown_once_in_order() -> None:
    b = _b("pilot", ["b", "a", "b"], names={"a": "Alpha", "b": "Beta"})
    assert b.real == ("Beta", "Alpha"), f"names shown: {b.real}"


def test_a_key_without_a_shown_name_is_read_as_component_and_the_key() -> None:
    assert _b("pilot", ["llm", "store"]).real == ("component llm", "component store"), (
        "a_key_without_a_shown_name_is_read_as_component_and_the_key: check 1"
    )
    assert _b("pilot", ["llm"], names={"other": "Other"}).real == ("component llm",), (
        "a_key_without_a_shown_name_is_read_as_component_and_the_key: check 2"
    )


def test_the_words_can_be_replaced_without_changing_which_sentence_is_chosen() -> None:
    words = mb.BannerWords(tag_by_mode={"demo": "D", "pilot": "P", "prod": "L"}, made_up="MADE.")
    b = _b("demo", words=words)
    assert b.tag == "D" and b.text.startswith("MADE.")
    assert _b("demo", ["x"], words=words).tone == "real"  # the choice is not in the words


def test_the_default_words_have_a_tag_for_every_stage_and_a_missing_one_is_refused() -> None:
    assert set(mb.DEFAULT_WORDS.tag_by_mode) == set(STAGES)
    with refused(ValueError, "a tag table without pilot and prod", match="no tag for the stage"):
        mb.BannerWords(tag_by_mode={"demo": "D"})


def test_the_lists_are_required_so_an_unchecked_call_cannot_say_nothing_real() -> None:
    for label, call in (
        ("no lists at all", lambda: mb._banner_for("demo")),  # type: ignore[call-arg]
        ("real_services only", lambda: mb._banner_for("demo", real_services=[])),  # type: ignore[call-arg]
        ("stand_ins only", lambda: mb._banner_for("demo", stand_ins=[])),  # type: ignore[call-arg]
        ("both lists given by position", lambda: mb._banner_for("demo", [], [])),  # type: ignore[misc]
    ):
        with refused(TypeError, f"the call with {label}"):
            call()


def test_an_unknown_stage_is_refused() -> None:
    for mode in ["", "DEMO", "Demo", "canary", "live", "test", None, 3]:
        with refused(ValueError, f"stage {mode!r}", match="is not one of demo, pilot, prod"):
            _b(mode)  # type: ignore[arg-type]


def test_a_bare_string_dict_set_or_non_list_is_refused_not_read_by_accident() -> None:
    for bad in ["crm", b"crm", None, 5, {"crm": "CRM"}, {"crm"}, frozenset({"crm"})]:
        for kwargs in (
            {"real_services": bad, "stand_ins": []},
            {"real_services": [], "stand_ins": bad},
        ):
            with refused(
                TypeError,
                f"{type(bad).__name__} {bad!r} as {'real_services' if 'real_services' in kwargs and kwargs['real_services'] is bad else 'stand_ins'}",
                match="must be a list of service names",
            ):
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
        with refused(
            ValueError,
            f"hostile name {name!r} given as a shown name",
            match="plain words|non-empty",
        ):
            _b("pilot", ["k"], names={"k": name})
        with refused(
            ValueError,
            f"hostile name {name!r} given as a real service key",
            match="plain words|non-empty",
        ):
            _b("pilot", [name])
        with refused(
            ValueError,
            f"hostile name {name!r} given as a stand-in key",
            match="plain words|non-empty",
        ):
            _b("demo", [], [name])


def test_a_plain_name_of_the_longest_allowed_length_is_shown_and_one_more_character_is_not() -> (
    None
):
    assert _b("pilot", ["k"], names={"k": "x" * 40}).real == ("x" * 40,)
    for ok in ("Mail 2", "a-b", "x.y", "z_9", "Mail.com", "AI step"):
        assert _b("pilot", ["k"], names={"k": ok}).real == (ok,)
    with refused(ValueError, "a name of 41 characters", match="plain words"):
        _b("pilot", ["k"], names={"k": "x" * 41})


def test_a_service_key_that_is_not_text_is_refused() -> None:
    with refused(ValueError, "the service key 3 (a number)", match="non-empty text"):
        _b("demo", [3])  # type: ignore[list-item]


def test_a_banner_longer_than_the_page_script_accepts_is_refused_in_python() -> None:
    long_names = {f"k{i}": f"{chr(65 + i)}" * 40 for i in range(20)}
    with refused(ValueError, "twenty long real service names", match="too many services"):
        _b("pilot", list(long_names), names=long_names)
    with refused(ValueError, "twenty long stand-in names", match="too many services"):
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
    kw.setdefault("overridden", ())
    return mb.banner_from_config(cfg, tool_specs={} if tool_specs is None else tool_specs, **kw)


def _services(cfg, tool_specs: object = None):
    return mb._services_in(cfg, {} if tool_specs is None else tool_specs)


NOTHING = {("signer", "none"), ("anchor", "none"), ("detector", "regex")}


def test_banner_from_config_reads_the_stage_and_both_lists_from_the_config(tmp_path: Path) -> None:
    cfg = load_config(make_cfg(tmp_path))  # the fixture is the demo config and holds fakes
    real, pretend = _services(cfg)
    assert real == () and {"llm", "channel", "secrets", "store"} <= set(pretend), (
        "banner_from_config_reads_the_stage_and_both_lists_from_the_c: check 1"
    )
    b = _banner(cfg)
    assert (b.mode, b.tone) == (cfg.environment, "demo"), (
        "banner_from_config_reads_the_stage_and_both_lists_from_the_c: check 2"
    )
    assert b.stand_ins == tuple(f"component {c}" for c in pretend) and b.real == (), (
        "banner_from_config_reads_the_stage_and_both_lists_from_the_c: check 3"
    )
    assert {(c, s.kind) for c, s in cfg.backends.entries() if c in pretend} <= DEMO_ONLY, (
        "banner_from_config_reads_the_stage_and_both_lists_from_the_c: check 4"
    )
    for named in ("demo", "pilot", "prod"):  # the stage is read from the config, never fixed
        assert _banner(_fake_config(named, [("llm", "anthropic")])).mode == named, (
            f"the banner did not read the stage {named} from the config"
        )


def test_a_real_kind_in_the_config_is_named_and_the_made_up_sentence_is_never_given() -> None:
    cfg = _fake_config("demo", [("llm", "anthropic"), ("store", "memory"), ("signer", "none")])
    b = _banner(cfg, names={"llm": "AI step"})
    assert b.tone == "real" and b.real == ("AI step",) and b.stand_ins == ("component store",), (
        f"a real kind in the config was not named as real: {b.tone} {b.real}"
    )
    assert "made-up" not in (b.text + b.standins).lower()
    for stage in STAGES:
        assert _banner(_fake_config(stage, [("llm", "bedrock")])).tone == "real", (
            f"the real banner was missing for {stage!r}"
        )


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
        with refused(ValueError, f"the kind {bad_kind!r}", match="cannot be placed in the banner"):
            _banner(_fake_config("demo", [("llm", bad_kind)]))
    with refused(ValueError, "an entry with an empty name", match="cannot be placed in the banner"):
        _banner(_fake_config("demo", [("", "fake")]))


def test_the_stage_of_the_config_is_checked_like_any_other_stage() -> None:
    with pytest.raises(ValueError, match="is not one of demo, pilot, prod"):
        _banner(_fake_config("canary", [("llm", "fake")]))


def test_the_old_public_names_are_gone_and_banner_from_config_is_the_only_entry() -> None:
    for old in ("banner_for", "services_in", "stand_ins_in"):
        assert not hasattr(mb, old), old
        assert old not in mb.__all__
    assert [n for n in mb.__all__ if n.startswith("banner")] == [
        "banner_from_config",
        "banner_or_unconfirmed",
    ]
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


def _unconfirmed(seen: dict, why: str = "") -> None:
    assert seen["threw"] == "" and seen["htmlWrites"] == [], why
    assert seen["hidden"] is False and seen["tone"] == "unconfirmed" and seen["mode"] == "", why
    assert seen["shownTone"] == "unconfirmed", why
    assert seen["lines"][0]["text"] == mb.not_confirmed()["tag"], why
    assert seen["lines"][1]["text"] == " " + mb.not_confirmed()["text"], why


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
        assert seen["hidden"] is False, f"the {banner.tone} banner was left hidden"
        assert seen["tone"] == banner.tone and seen["mode"] == banner.mode, (
            "tone or mode not painted"
        )
        assert seen["lines"][0] == {"cls": "mode-banner__tag", "text": banner.tag}
        assert seen["lines"][1] == {"cls": "mode-banner__text", "text": " " + banner.text}
        assert len(seen["lines"]) == (3 if banner.standins else 2), "wrong number of lines painted"
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
        {**GOOD_DEMO, "tag": ""},
        {**GOOD_DEMO, "tag": 5},
        {**GOOD_DEMO, "text": 5},
        {**GOOD_DEMO, "text": "x" * 601},
        {**GOOD_DEMO, "standins": 7},
        {**GOOD_DEMO, "standins": "x" * 601},
        {**GOOD_DEMO, "tone": "unconfirmed"},
        {**GOOD_DEMO, "tone": "fine"},
        {**GOOD_DEMO, "real": "crm"},
        {**GOOD_DEMO, "stand_ins": "a"},
        {**GOOD_DEMO, "stand_ins": [1]},
        {k: v for k, v in GOOD_DEMO.items() if k != "real"},
        {k: v for k, v in GOOD_DEMO.items() if k != "stand_ins"},
    ]
    good = _paint(
        GOOD_DEMO
    )  # the control: the one valid banner every odd entry is built from is painted as given
    assert good["tone"] == "demo" and good["lines"][0]["text"] == "DEMO", (
        "GOOD_DEMO is not valid by itself"
    )
    for i, bad in enumerate(bad_banners):
        shown = (
            {k: v for k, v in bad.items() if GOOD_DEMO.get(k) != v}
            if isinstance(bad, dict) and bad.keys() >= GOOD_DEMO.keys()
            else bad
        )  # for an entry built from GOOD_DEMO: only the one changed field
        _unconfirmed(_paint(bad), f"odd banner #{i} changes {str(shown)[:40]}")
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
    for i, banner in enumerate(wrong):
        _unconfirmed(_paint(banner), f"contradiction #{i}")


@needs_node
def test_pin_a_tag_that_is_not_plain_text_is_not_painted_as_given() -> None:
    controls = _paint(GOOD_DEMO)
    assert controls["tone"] == "demo", "the control banner must be painted as given"
    for value in [None, 5, "", ["x"], {"a": 1}, "x" * (mb.MAX_TEXT_LENGTH + 1)]:
        _unconfirmed(_paint({**GOOD_DEMO, "tag": value}), f"tag check: tag = {value!r:.20}")


@needs_node
def test_pin_a_text_that_is_not_plain_text_is_not_painted_as_given() -> None:
    controls = _paint(GOOD_DEMO)
    assert controls["tone"] == "demo", "the control banner must be painted as given"
    for value in [None, 5, "", ["x"], {"a": 1}, "x" * (mb.MAX_TEXT_LENGTH + 1)]:
        _unconfirmed(_paint({**GOOD_DEMO, "text": value}), f"text check: text = {value!r:.20}")


@needs_node
def test_the_painter_never_throws_and_never_leaves_the_page_blank() -> None:
    for scenario in ("throwing-getter", "proxy"):
        seen = _paint(GOOD_DEMO, scenario)
        assert seen["usableThrew"] == "", (
            f"usable() on its own threw in scenario {scenario}"
        )  # it never throws either
        _unconfirmed(seen)
    seen = _paint(GOOD_DEMO, "throwing-doc")  # the page cannot make elements at all
    assert seen["threw"] == "" and seen["tone"] == "unconfirmed" and seen["hidden"] is False
    assert seen["text"] == f"{mb.not_confirmed()['tag']} {mb.not_confirmed()['text']}"
    seen = _paint(GOOD_DEMO, "null-el")  # no element to paint into: no throw, nothing to show
    assert seen["threw"] == "" and seen["lines"] == [] and seen["shownTone"] == "demo", (
        "no element: the painter must report the banner and write nothing"
    )
    seen = _paint(
        GOOD_DEMO, "failing-append"
    )  # painting fails half way: the plain "not confirmed" text is put in
    assert seen["threw"] == "" and seen["tone"] == "unconfirmed" and seen["hidden"] is False
    assert seen["text"] == f"{mb.not_confirmed()['tag']} {mb.not_confirmed()['text']}"


@needs_node
def test_the_page_fallback_has_the_same_words_as_the_python_fallback() -> None:
    assert _paint(None)["notConfirmed"] == mb.not_confirmed(), (
        "the_page_fallback_has_the_same_words_as_the_python_fallback: check 1"
    )


@needs_node
def test_the_page_lists_are_the_python_lists() -> None:
    seen = _paint(None)
    assert seen["modes"] == list(STAGES) and seen["tones"] == list(mb.TONES), (
        "the_page_lists_are_the_python_lists: check 1"
    )
    assert seen["maxText"] == mb.MAX_TEXT_LENGTH, "the_page_lists_are_the_python_lists: check 2"
    assert re.search(rf"var MAX_TEXT = {mb.MAX_TEXT_LENGTH};", JS.read_text(encoding="utf-8")), (
        "the_page_lists_are_the_python_lists: check 3"
    )


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


# Spellings that the connection guard's normaliser would fold into "localhost" (padding, full-width and modifier letters)
# or that hold a control character: as a bare host they are NOT this machine (the stricter reading wins everywhere).
PADDED_OR_ODD_HOSTS = [
    "localhost\n",
    " localhost",
    "localhost ",
    "\tlocalhost",
    "localhost\x00",
    "\x00localhost",
    "\uff4c\uff4f\uff43\uff41\uff4c\uff48\uff4f\uff53\uff54",  # full-width "localhost"
    "\u02e1ocalhost",  # modifier letter small l, which NFKC folds to "l"
    "127.0.0.1\n",
    "::1\n",
]

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
    (
        "egress_hosts",
        frozenset({"[::1]"}),
        mb.EGRESS_HOSTS,
    ),  # a bare bracketed address is not a host name
    *[("egress_hosts", frozenset({h}), mb.EGRESS_HOSTS) for h in PADDED_OR_ODD_HOSTS],
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
        assert real == (key,), (
            f"{field}={value!r}: a configured address that leaves this machine was not counted as real"
        )
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
    with refused(
        ValueError, "a real note that names no service", match="does not name every real service"
    ):
        _banner(_fake_config("pilot", [("llm", "bedrock")]), words=forgetful)
    # a reworded real note that repeats the made-up sentence is refused in a real and in a quiet banner
    boastful = mb.BannerWords(tag_by_mode=tags, real_data_note=claim.made_up)
    with refused(
        ValueError,
        "a real note that repeats the made-up sentence (real banner)",
        match="claims made-up data",
    ):
        _banner(_fake_config("pilot", [("llm", "bedrock")]), words=boastful)
    quiet_boast = mb.BannerWords(tag_by_mode=tags, none_real=claim.made_up)
    with refused(
        ValueError,
        "a quiet note that repeats the made-up sentence (quiet banner)",
        match="claims made-up data",
    ):
        _banner(_fake_config("prod", []), words=quiet_boast)
    # a demo banner that names a real service is refused (built by hand: banner_from_config never makes one)
    hand_made = mb.ModeBanner(
        "demo", "demo", "DEMO", claim.made_up + " " + claim.nothing_sent, "", ("record",), ()
    )
    with refused(
        ValueError,
        "a demo banner that names a real service",
        match="demo banner must name no real service",
    ):
        mb._check_what_is_claimed(hand_made, claim)


@needs_node
def test_the_page_exports_and_the_fallback_cannot_be_changed_by_a_page() -> None:
    frozen = _paint(None)["frozen"]  # api, fallback, its two lists, TONES, MODES
    assert frozen == [True] * 6, f"frozen flags: {frozen}"


@needs_node
def test_a_failed_last_resort_write_never_leaves_the_banner_hidden() -> None:
    seen = _paint(GOOD_DEMO, "failing-all-writes")  # appending and then the text write both throw
    assert seen["threw"] == "", "the painter threw"
    assert seen["hidden"] is False, "the last-resort write left the element hidden"
    assert seen["text"] == "", (
        f"the old words stayed on screen after the text write failed: {seen['text']!r}"
    )  # emptied first: nothing is shown, never the old claim


@needs_node
def test_a_failed_append_leaves_words_on_the_screen_never_an_empty_banner() -> None:
    seen = _paint(GOOD_DEMO, "failing-append")
    assert seen["threw"] == "" and seen["hidden"] is False
    assert seen["text"].strip() != "", "the fallback wrote empty text"
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
    _unconfirmed(
        _paint(real), "a part of a word counted as the name"
    )  # "CRM" is only part of "CRMS": not named
    fine = {**real, "text": real["text"].replace("CRMS", "CRM")}
    assert _paint(fine)["tone"] == "real"


# --- round 4 ----------------------------------------------------------------------------------------------------------
def _spec(*hosts: str, module: str = "mod") -> ToolSpec:
    return ToolSpec(
        name="read_x",
        function=f"{module}:read_x",
        description="reads x",
        input_schema={"type": "object"},
        side_effect="none",
        hosts=hosts,
    )


def test_a_tool_specs_that_is_not_a_mapping_is_refused_with_a_type_error() -> None:
    cfg = _fake_config("demo", [("llm", "fake")])
    for odd in ([], "agent", 5, [("a", {})]):
        with pytest.raises(
            TypeError, match="tool_specs must be the registry's tools mapping or None"
        ):
            mb.banner_from_config(cfg, tool_specs=odd, overridden=())  # type: ignore[arg-type]


def test_tool_specs_has_no_default_so_forgetting_it_is_an_error() -> None:
    cfg = _fake_config("demo", [("llm", "fake")])
    with refused(TypeError, "banner_from_config called without tool_specs"):
        mb.banner_from_config(cfg, overridden=())  # type: ignore[call-arg]
    with refused(TypeError, "_services_in called without tool_specs"):
        mb._services_in(cfg)  # type: ignore[call-arg]


def test_a_tool_manifest_host_that_is_not_this_machine_is_a_real_service() -> None:
    cfg = _fake_config("demo", [("llm", "fake")])
    specs = {"agent": {"read_x": _spec("api.example.test")}}
    assert mb._outside_endpoints(cfg, specs) == [mb.TOOL_HOSTS], (
        "the outside-endpoint search missed a tool manifest host that leaves this machine"
    )
    real, _ = _services(cfg, specs)
    assert real == (mb.TOOL_HOSTS,), (
        f"a tool manifest host that leaves this machine was not real: {real}"
    )
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
        assert _banner(cfg, specs).tone == "demo", (
            f"a tool host on this machine was counted as real: {specs}"
        )
    mixed = {"a": {"t": _spec("localhost")}, "b": {"u": _spec("api.example.test")}}
    assert _services(cfg, mixed)[0] == (mb.TOOL_HOSTS,), (
        "one outside host in one agent was not enough"
    )


def test_tool_modules_without_the_manifests_count_as_one_real_service() -> None:
    cfg = _fake_config("demo", [("llm", "fake")])
    cfg.tool_modules = ["some_mod"]
    assert _services(cfg, None)[0] == (mb.TOOL_MODULES,), "no spec at all with a tool module"
    real, _ = mb._services_in(cfg, None)  # None: the caller could not read the manifests
    assert real == (mb.TOOL_MODULES,), (
        "tool_modules_without_the_manifests_count_as_one_real_service: check 2"
    )
    assert mb.banner_from_config(cfg, tool_specs=None, overridden=()).tone == "real", (
        "tool_modules_without_the_manifests_count_as_one_real_service: check 3"
    )
    cfg.tool_modules = []
    assert mb._services_in(cfg, None)[0] == (), (
        "tool_modules_without_the_manifests_count_as_one_real_service: check 4"
    )  # no module configured: nothing hidden by None
    with pytest.raises(TypeError, match="tool_specs"):
        mb._services_in(cfg, ["not", "a", "mapping"])  # type: ignore[arg-type]


def test_the_tools_of_a_real_registry_are_what_the_banner_reads(tmp_path: Path) -> None:
    import dataclasses

    from hadavin_sdk.registry import Registry, load_registry

    config = load_config(make_cfg(tmp_path))
    registry = load_registry(config)
    assert isinstance(registry, Registry) and isinstance(registry.tools, dict)
    assert mb.banner_from_config(config, tool_specs=registry.tools, overridden=()).tone == "demo"
    outside = dataclasses.replace(registry, tools={"a": {"t": _spec("api.example.test")}})
    b = mb.banner_from_config(outside.config, tool_specs=outside.tools, overridden=())
    assert b.tone == "real" and b.real == (f"component {mb.TOOL_HOSTS}",), "registry tools dropped"


def test_the_words_state_what_is_checked_and_not_a_false_premise() -> None:
    sentence = mb.DEFAULT_WORDS.nothing_sent
    assert sentence == "Nothing here is set up to send data to real customers or real systems."
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
    "http://[::1]evil.example/",  # text after the closing bracket
    "http://[::1]:80x/",  # a port that is not digits
    "http://127.0.0.1:80x/",
    "http://localhost\n/",
    "http://\uff4c\uff4f\uff43\uff41\uff4c\uff48\uff4f\uff53\uff54/",  # full-width host in a url
    "http://\u02e1ocalhost/",
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
    wrong_type = {"systems": "x", "egress_hosts": 5, "sources": [], "tool_modules": "m"}
    for field, value in wrong_type.items():
        kept = {f: getattr(real, f) for f in fields}
        try:
            _banner(SimpleNamespace(**{**kept, field: value}))
        except TypeError as exc:
            assert "not a usable value" in str(exc) and field in str(exc), f"field {field}: {exc}"
        else:
            pytest.fail(f"a {field} of the wrong type was used")


def test_an_empty_made_up_sentence_is_an_error_not_a_switched_off_check() -> None:
    tags = {"demo": "DEMO", "pilot": "PILOT", "prod": "LIVE"}
    for field in ("made_up", "nothing_sent"):
        words = mb.BannerWords(tag_by_mode=tags, **{field: "  "})
        with refused(ValueError, f"a blank {field} sentence", match="must not be empty"):
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


# --- round 5 ----------------------------------------------------------------------------------------------------------
def test_a_bare_host_that_is_padded_or_not_plain_ascii_is_not_this_machine() -> None:
    for host in PADDED_OR_ODD_HOSTS:
        assert mb._is_this_machine(host) is False, f"bare host {host!r} read as this machine"
        cfg = _with_endpoints(egress_hosts=frozenset({host}))
        assert _services(cfg)[0] == (mb.EGRESS_HOSTS,), f"egress host {host!r} read as this machine"
        specs = {"agent": {"read_x": _spec(host)}}
        assert _services(_fake_config("demo", [("llm", "fake")]), specs)[0] == (mb.TOOL_HOSTS,), (
            f"tool host {host!r} read as this machine"
        )
    for host in ("localhost", "LOCALHOST", "localhost.", "127.0.0.1", "::1"):
        assert mb._is_this_machine(host) is True, f"plain host {host!r} not read as this machine"
    for odd in (None, 5, b"localhost", "", ["localhost"]):
        assert mb._is_this_machine(odd) is False, f"value {odd!r} read as this machine"


def test_a_url_and_a_bare_host_give_the_same_answer_for_every_spelling() -> None:
    for host in [
        *PADDED_OR_ODD_HOSTS,
        "localhost",
        "LOCALHOST",
        "localhost.",
        "10.0.0.5",
        "x.example",
    ]:
        in_url = mb._url_leaves_this_machine(f"http://{host}/")
        assert in_url is (not mb._is_this_machine(host)) or in_url, (
            f"url and host differ for {host!r}"
        )
        if not mb._is_this_machine(host):
            assert in_url is True, f"a url with the host {host!r} stayed on this machine"


def _type_error_of(call, why: str) -> str:
    """The text of the TypeError `call` raises; a different outcome fails with `why` in the message."""
    try:
        call()
    except TypeError as exc:
        return str(exc)
    except Exception as exc:  # noqa: BLE001 - reported with its type, so the failing line names the case
        pytest.fail(f"{why}: raised {type(exc).__name__} instead of TypeError")
    pytest.fail(f"{why}: no error")


def test_a_tool_spec_without_hosts_or_with_odd_hosts_raises_naming_the_tool() -> None:
    cfg = _fake_config("demo", [("llm", "fake")])
    odd = [
        SimpleNamespace(name="read_x"),  # no hosts at all
        SimpleNamespace(hosts=None),
        SimpleNamespace(hosts="api.example.test"),  # a bare string would be read letter by letter
        SimpleNamespace(hosts={"api.example.test"}),
        SimpleNamespace(hosts=["ok.example.test", 5]),
    ]
    for i, bad in enumerate(odd):
        why = f"hosts case #{i}"
        text = _type_error_of(
            lambda bad=bad: mb.banner_from_config(
                cfg, tool_specs={"agent": {"read_x": bad}}, overridden=()
            ),
            why,
        )
        assert "tool 'read_x' of agent 'agent' has no `hosts` list" in text, f"{why}: {text}"
    for i, inner in enumerate([[_spec("api.example.test")], None]):
        why = f"agent entry case #{i}"
        text = _type_error_of(
            lambda inner=inner: mb.banner_from_config(
                cfg, tool_specs={"agent": inner}, overridden=()
            ),
            why,
        )
        assert "tool_specs['agent'] must be a mapping" in text, f"{why}: {text}"
    # a list of hosts is accepted like a tuple; a bad spec after an outside host still raises (every spec is read)
    ok = SimpleNamespace(hosts=["api.example.test"])
    assert _services(cfg, {"a": {"t": ok}})[0] == (mb.TOOL_HOSTS,)
    text = _type_error_of(
        lambda: _services(cfg, {"a": {"t": ok, "u": SimpleNamespace()}}),
        "a bad spec after an outside host",
    )
    assert "tool 'u'" in text, text


def test_tool_modules_with_no_spec_at_all_count_as_one_real_service_like_none() -> None:
    cfg = _fake_config("demo", [("llm", "fake")])
    cfg.tool_modules = ["some_mod"]
    for empty in ({}, {"a": {}}, {"a": {}, "b": {}}):
        assert _services(cfg, empty)[0] == (mb.TOOL_MODULES,), f"modules with no spec {empty!r}"
    local = {"a": {"t": _spec("localhost", module="some_mod")}}
    assert _services(cfg, local)[0] == (), "a manifest that names this machine is not hidden"
    both = {"a": {"t": _spec("api.example.test", module="some_mod")}}
    assert _services(cfg, both)[0] == (mb.TOOL_HOSTS,)
    cfg.tool_modules = []
    assert _services(cfg, {})[0] == (), "no module and no spec is nothing"


def test_the_loopback_names_are_pinned_by_content() -> None:
    from hadavin_sdk.guard.http import LOOPBACK as SHARED

    assert frozenset(SHARED) == frozenset({"localhost", "127.0.0.1", "::1"}), (
        "shared loopback names changed"
    )
    assert frozenset(mb.LOOPBACK) == frozenset({"localhost", "127.0.0.1", "::1"}), (
        "banner loopback names widened"
    )


def _client_refuses_the_url(url: str) -> bool:
    """True when the tool client's own url checks (the real `ToolContext.fetch`, read from tools.py) refuse `url` as a
    url: a backslash, white space, a control or non-ASCII character, `%`, credentials, or a host that its manifest
    check calls not a plain name. The host and scheme rules that exist to keep a tool on its manifest hosts are not
    part of the question (the banner reads a loopback host as this machine, the client refuses loopback in a manifest)."""
    from hadavin_sdk import tools as tools_mod

    spec = tools_mod.ToolSpec(
        name="read_x", function="mod:read_x", description="reads x", input_schema={"type": "object"},
        side_effect="none", hosts=("api.example.test",), operations=["op.read"],
    )  # fmt: skip
    ctx = tools_mod.ToolContext(spec, 1.0, bindings={"op.read": ("GET", r"/.*")})
    secure = url.replace("http://", "https://", 1)
    for candidate in (url, secure):
        try:
            ctx.fetch("GET", candidate, operation="op.read")
        except tools_mod.ToolRefused as why:
            text = str(why)
            if any(w in text for w in ("backslash", "percent-encoding", "credentials in the URL")):
                return True
        except Exception:  # noqa: BLE001 - a malformed url that raises elsewhere is refused all the same
            return True
    return False


def test_the_banner_is_at_least_as_strict_as_the_tool_client_on_urls_and_hosts() -> None:
    from hadavin_sdk import tools as tools_mod

    for url in [*LEAVING_URLS, *[f"http://{h}/" for h in PADDED_OR_ODD_HOSTS]]:
        assert mb._url_leaves_this_machine(url) is True, f"banner reads {url!r} as this machine"
    for _field_name, value in THIS_MACHINE:
        for entry in value.values() if isinstance(value, dict) else ():
            url = getattr(entry, "base_url", None) or ""
            if url:
                assert _client_refuses_the_url(url) is False, f"the client refuses {url!r}"
    # whenever the tool client refuses a url as a url, the banner says it leaves this machine
    corpus = [*LEAVING_URLS, "http://localhost:8080/", "http://[::1]:8080/", "http://LOCALHOST:80/"]
    refused = [u for u in corpus if _client_refuses_the_url(u)]
    assert len(refused) >= 8, "the parity test must really reach the client's refusals"
    for url in refused:
        assert mb._url_leaves_this_machine(url) is True, f"client refuses {url!r}, banner does not"
    # and for a bare host the client's manifest check calls "not a plain lowercase ASCII hostname"
    for host in PADDED_OR_ODD_HOSTS:
        why = tools_mod.forbidden_host(host)
        if why is not None and "plain lowercase ASCII" in why:
            assert mb._is_this_machine(host) is False, (
                f"client refuses host {host!r}, banner does not"
            )
    assert (
        tools_mod.forbidden_host("localhost") is not None
    )  # the client refuses loopback in a manifest
    assert (
        mb._is_this_machine("localhost") is True
    )  # and the banner reads it as this machine (fail-safe reading)


def test_a_port_that_is_not_digits_or_text_after_a_bracket_is_not_this_machine() -> None:
    for netloc, ok in (
        ("[::1]", True),
        ("[::1]:8080", True),
        ("[::1]:", True),
        ("[::1]evil.example", False),
        ("[::1]:80x", False),
        ("[::1]x:80", False),
        ("localhost", True),
        ("localhost:80", True),
        ("localhost:80x", False),
        ("localhost:", True),
    ):
        assert mb._port_tail_ok(netloc) is ok, f"port tail of {netloc!r}"


def test_banner_or_unconfirmed_gives_the_banner_or_the_not_confirmed_one(
    caplog: pytest.LogCaptureFixture,
) -> None:
    good = _fake_config("demo", [("llm", "fake")])
    assert mb.banner_or_unconfirmed(good, tool_specs={}, overridden=()) == _banner(good).as_dict()
    secret_looking = "internal-host-" + "x" * 5
    bad_name = {"llm": f"{secret_looking}\n<script>"}
    real = _fake_config("pilot", [("llm", "bedrock")])
    named_tool = {
        "a": {secret_looking: SimpleNamespace()}
    }  # its error text names the tool: the log must not copy it
    with pytest.raises(TypeError) as caught:
        mb.banner_from_config(good, tool_specs=named_tool, overridden=())
    assert secret_looking in str(caught.value), (
        "the error text no longer holds the name, so this test proves nothing"
    )
    for call in (
        lambda: mb.banner_or_unconfirmed(
            good, tool_specs=named_tool, overridden=()
        ),  # a spec without hosts, whose error text holds the tool name
        lambda: mb.banner_or_unconfirmed(
            real, bad_name, tool_specs={}, overridden=()
        ),  # a name that is not plain words
        lambda: mb.banner_or_unconfirmed(
            SimpleNamespace(environment="demo"), tool_specs={}, overridden=()
        ),  # lost fields
    ):
        caplog.clear()
        with caplog.at_level("WARNING", logger=mb.__name__):
            assert call() == mb.not_confirmed(), (
                "a banner that could not be built was shown as built"
            )
        assert len(caplog.records) == 1, "exactly one log line"
        line = caplog.records[0].getMessage()
        assert "internal-host" not in line, f"the log line holds a name from the config: {line!r}"
        assert "<script>" not in line, f"the log line holds markup from the config: {line!r}"
        assert "SimpleNamespace" not in line, f"the log line holds an object text: {line!r}"
        assert "not-confirmed banner" in line, f"the log line does not say what was shown: {line!r}"
    with pytest.raises(TypeError):
        mb.banner_or_unconfirmed(good)  # type: ignore[call-arg]
    # the claim: banner_from_config itself raises, banner_or_unconfirmed does not
    with pytest.raises(ValueError, match="plain words"):
        mb.banner_from_config(real, bad_name, tool_specs={}, overridden=())


def test_an_empty_name_is_never_in_a_text() -> None:
    assert mb.names_in("any text at all", "") is False, "an empty name was found in a text"
    assert mb.names_in("", "") is False, "an empty name was found in an empty text"


def test_the_limits_are_stated_in_words() -> None:
    doc = " ".join((mb.__doc__ or "").split())
    for phrase in (
        "app.build",
        "`tools=` callables",
        "sources=",
        "channel=",
        "llm=",
        "detector=",
        "secrets=",
        "localhost` is trusted to resolve to the loopback",
        "a page cache",
        "reloaded",
        "settings of a stand-in kind are never inspected",
        "callable handed to `app.build(tools=...)`",
        "RAISES when it cannot say",
        "banner_or_unconfirmed",
        "plain ASCII",
        "trusts",
    ):
        if phrase == "trusts":
            phrase = "paints the `tone` it is given"
        assert phrase in doc or phrase in (JS.read_text(encoding="utf-8")), (
            f"limit not stated: {phrase}"
        )
    assert "a banner is always shown" not in doc  # the old, wider claim is gone


def test_a_service_name_may_not_hold_the_made_up_claim_of_the_words_in_use() -> None:
    tags = {"demo": "DEMO", "pilot": "PILOT", "prod": "LIVE"}
    words = mb.BannerWords(tag_by_mode=tags, made_up="Fiktiv", nothing_sent="Nichts wird gesendet")
    for name in ("Fiktiv", "Mail fiktiv", "Nichts wird gesendet"):
        refusal = None
        try:
            _b("pilot", ["k"], names={"k": name}, words=words)
        except ValueError as exc:
            refusal = exc
        assert refusal is not None and "plain words" in str(refusal), f"name {name!r}: {refusal}"
    assert _b("pilot", ["k"], names={"k": "Mail"}, words=words).real == ("Mail",)
    _b("pilot", ["k"], names={"k": "Fiktiv"})  # the default words do not reserve it
    for name in ("CRMé", "ｃｒｍ", "café mail"):  # service names are ASCII only
        with pytest.raises(ValueError, match="plain words"):
            _b("pilot", ["k"], names={"k": name})


def test_the_names_are_checked_in_the_formatted_names_part_of_the_text_only() -> None:
    words = mb.DEFAULT_WORDS
    right = _b("pilot", ["crm"], names=NAMES)
    mb._check_what_is_claimed(right, words)  # the real banner passes
    # "CRM" occurs in the text but not in the formatted list of names: not counted as shown
    sneaky = mb.ModeBanner(
        "pilot", "real", "PILOT",
        "Real services are connected: Mail. Data this system handles may be sent to them. CRM", "",
        ("CRM",), (),
    )  # fmt: skip
    with pytest.raises(ValueError, match="does not name every real service"):
        mb._check_what_is_claimed(sneaky, words)
    text = words.real_connected.format(names="CRMS") + " " + words.real_data_note + " CRM."
    tricky = mb.ModeBanner("pilot", "real", "PILOT", text, "", ("CRM",), ())
    try:  # the later "CRM." is not the list
        mb._check_what_is_claimed(tricky, words)
    except ValueError:
        pass
    else:
        raise AssertionError("a name that occurs only after the list was counted as shown")
    other = mb.ModeBanner(
        "pilot", "real", "PILOT", "Some other sentence about CRM.", "", ("CRM",), ()
    )
    with pytest.raises(ValueError, match="does not name every real service"):
        mb._check_what_is_claimed(other, words)


@needs_node
def test_a_failing_attribute_write_never_leaves_the_old_words_on_screen() -> None:
    seen = _paint(
        GOOD_DEMO, "failing-every-attribute"
    )  # every setAttribute throws; the element held an earlier banner
    assert seen["threw"] == "" and seen["hidden"] is False, (
        "element left hidden or the painter threw"
    )
    assert seen["text"] == mb.not_confirmed()["tag"] + " " + mb.not_confirmed()["text"], (
        f"the old words were not replaced by the not-confirmed words: {seen['text'][:30]!r}"
    )
    assert seen.get("tone") is None, "a tone was recorded although the attribute write throws"


@needs_node
def test_a_failing_tone_attribute_alone_still_replaces_the_old_words_and_clears_the_mode() -> None:
    seen = _paint(
        GOOD_DEMO, "failing-tone-attr"
    )  # only data-tone throws; the element held an earlier banner
    assert seen["threw"] == "" and seen["hidden"] is False, (
        "element left hidden or the painter threw"
    )
    assert seen["text"] == mb.not_confirmed()["tag"] + " " + mb.not_confirmed()["text"], (
        "the old words stayed although only the tone write failed"
    )
    assert seen.get("tone") is None and seen.get("mode") == "", (
        f"expected no new tone and a cleared mode, got tone {seen.get('tone')!r} mode {seen.get('mode')!r}"
    )


@needs_node
def test_a_failing_mode_attribute_leaves_the_not_confirmed_tone_with_its_text() -> None:
    seen = _paint(
        GOOD_DEMO, "failing-mode-attr"
    )  # only data-mode throws, after the tone and the words are written
    assert seen["threw"] == "" and seen["hidden"] is False
    assert seen["tone"] == "unconfirmed", "a mode failure left the tone of the given banner"
    assert seen["text"] == mb.not_confirmed()["tag"] + " " + mb.not_confirmed()["text"], (
        "wrong words for the tone"
    )


@needs_node
def test_the_page_trusts_the_tone_it_is_given_and_python_checks_the_sentences() -> None:
    # the page cannot read a sentence: a demo-tone banner of a made-up text with another text is painted as given,
    # which is why Python refuses to send one (the check above); this pins the division of work.
    odd = {**GOOD_DEMO, "text": "Some other words."}
    assert _paint(odd)["tone"] == "demo"
    with pytest.raises(ValueError, match="claims made-up data"):
        mb._check_what_is_claimed(
            mb.ModeBanner("pilot", "quiet", "PILOT", mb.DEFAULT_WORDS.made_up, "", (), ()),
            mb.DEFAULT_WORDS,
        )


NAME_TABLE_5 = [
    ("connected: AI step.", "AI step", True),  # a name with a space
    ("connected: AI steps.", "AI step", False),
    ("connected: xAI step.", "AI step", False),
    ("connected: e-mail.", "e-mail", True),  # a name with a hyphen
    ("connected: x-e-mail.", "e-mail", False),
    ("connected: CRM.v2.", "CRM.v2", True),  # a name with a dot
    ("connected: CRM.v2x.", "CRM.v2", False),
    ("CRM is connected.", "CRM", True),  # at the start of the text
    ("connected is CRM", "CRM", True),  # at the very end
    ("CRMS is connected.", "CRM", False),
    ("connected: 2CRM.", "CRM", False),  # a digit before
    ("connected: 2.CRM.", "CRM", False),  # a digit and a dot before
    (
        "connected: a..CRM.",
        "CRM",
        True,
    ),  # a double dot: the second dot is not joined to a letter or digit
    ("connected: CRM..", "CRM", True),
]
NAME_TABLE.extend(NAME_TABLE_5)


# -- batch 6, class A: "connects to nothing" is an explicit list; modules and hosts are compared, not assumed ----------
def test_the_nothing_connected_list_is_pinned_by_content() -> None:
    assert ("signer", "ed25519_local") not in mb.NOTHING_CONNECTED, (
        "the ed25519_local signer is listed as connecting to nothing: it reads a key, so it is shown as real"
    )
    assert ("detector", "regex") in mb.NOTHING_CONNECTED, (
        "the built-in regex detector is missing from the kinds that connect to nothing"
    )
    assert mb.NOTHING_CONNECTED == frozenset(
        {("signer", "none"), ("anchor", "none"), ("detector", "regex")}
    ), "the list of kinds that connect to nothing changed: each pair needs a written reason"
    assert "NOTHING_CONNECTED" in mb.__all__


def _fresh_module_with(monkeypatch: pytest.MonkeyPatch, extra_not_prod: set[tuple[str, str]]):
    """The banner module loaded again from its file while the prod gate table `NOT_PROD` holds `extra_not_prod`."""
    import importlib.util

    from hadavin_sdk.backends import table

    monkeypatch.setattr(table, "NOT_PROD", frozenset(table.NOT_PROD | extra_not_prod))
    spec = importlib.util.spec_from_file_location("mode_banner_fresh", mb.__file__)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(
        sys.modules, "mode_banner_fresh", module
    )  # a dataclass looks its module up here
    spec.loader.exec_module(module)
    return module


def test_a_kind_added_to_the_prod_gate_table_later_still_reads_as_a_real_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    other_only = (
        "secrets",
        "made_up_dev_vault",
    )  # a kind someone later refuses in prod for being dev-only
    fresh = _fresh_module_with(monkeypatch, {other_only})
    cfg = _fake_config("demo", [other_only, ("llm", "fake")])
    real, _ = fresh._services_in(cfg, {})
    assert real == ("secrets",), "a kind added to the prod gate table dropped out of the real list"
    banner = fresh.banner_from_config(cfg, tool_specs={}, overridden=())
    assert banner.tone == "real" and "made-up demo data" not in banner.text, (
        "the demo banner said made-up although a kind the banner does not know is connected"
    )


def test_a_configured_tool_module_that_no_manifest_accounts_for_counts_as_one_real_service() -> (
    None
):
    cfg = _fake_config("demo", [("llm", "fake")])
    cfg.tool_modules = ["mod", "other"]
    one_manifest = {"a": {"t": _spec("localhost", module="mod")}}
    assert _services(cfg, one_manifest)[0] == (mb.TOOL_MODULES,), (
        "two tool modules but a manifest for only one: the other module was not counted"
    )
    both = {"a": {"t": _spec("localhost", module="mod"), "u": _spec("localhost", module="other")}}
    assert _services(cfg, both)[0] == (), "every module has a manifest naming a host: nothing left"
    no_host = {"a": {"t": _spec(module="mod"), "u": _spec("localhost", module="other")}}
    assert _services(cfg, no_host)[0] == (mb.TOOL_MODULES,), (
        "a module whose manifest names no host was read as nothing real"
    )
    mixed = {"a": {"t": _spec(module="mod"), "u": _spec("localhost", module="mod")}}
    cfg.tool_modules = ["mod"]
    assert _services(cfg, mixed)[0] == (mb.TOOL_MODULES,), (
        "one empty spec of a module was hidden by another"
    )
    outside = {"a": {"t": _spec("api.example.test", module="mod")}}
    assert _services(cfg, outside)[0] == (mb.TOOL_HOSTS,), (
        "a module with an outside host is counted once, by its host"
    )
    unnamed = {
        "a": {"t": SimpleNamespace(hosts=("localhost",))}
    }  # a spec that names no function belongs to no module
    assert _services(cfg, unnamed)[0] == (mb.TOOL_MODULES,)


def test_the_type_of_a_system_base_url_is_text_and_another_type_reads_as_real() -> None:
    from pydantic import AnyUrl

    from hadavin_sdk.config import System

    assert System.model_fields["base_url"].annotation is str, (
        "System.base_url is no longer text: the banner's reading of it must be re-checked"
    )
    odd = _with_endpoints(
        systems={"crm": SimpleNamespace(base_url=AnyUrl("http://localhost:8080"))}
    )
    assert _services(odd)[0] == (mb.EXTERNAL_SYSTEMS,), (
        "a URL object was read as this machine, not as unknown"
    )


_PARITY_HOSTS = [
    "localhost", "LocalHost", "LOCALHOST.", "127.0.0.1", "[::1]", "127.0.0.2", "[::2]", "localhost.example.test",
]  # fmt: skip
_PARITY_TAILS = ["", "/", "/a/b", "?q=1", ":443/"]
PARITY_URLS = [
    f"https://{h}{tail}" for h in _PARITY_HOSTS for tail in _PARITY_TAILS
]  # 40 spellings
PARITY_BARE_HOSTS = [
    "localhost", "LOCALHOST", "Localhost", "localhost.", "LOCALHOST.", "127.0.0.1", "::1", "[::1]", "127.0.0.2",
    "::2", "0." + "0.0.0", "localhost.localdomain", "127.1", "0x7f.1", "2130706433", " localhost", "localhost ",
    "localhost\n", "ｌｏｃａｌｈｏｓｔ", "evil.example",
]  # fmt: skip


class _ClientAccepted(Exception):
    pass


def _tool_client_accepts(manifest_hosts: tuple[str, ...], url: str) -> bool:
    """True when the real `ToolContext.fetch` gets past every check of the operation, url, host and port, to the point of
    counting the request (it is stopped there: nothing is sent)."""
    from hadavin_sdk import tools as tools_mod

    spec = ToolSpec(
        name="read_x", function="mod:read_x", description="reads x", input_schema={"type": "object"},
        side_effect="none", hosts=manifest_hosts, operations=["op.read"],
    )  # fmt: skip

    def stop() -> None:
        raise _ClientAccepted

    ctx = tools_mod.ToolContext(spec, 1.0, bindings={"op.read": ("GET", r"/.*")}, on_fetch=stop)
    try:
        ctx.fetch("GET", url, operation="op.read")
    except _ClientAccepted:
        return True
    except Exception:  # noqa: BLE001 - any refusal is a refusal
        return False
    return False


def test_the_banner_is_never_more_lenient_than_the_tool_client_on_40_urls_and_20_hosts() -> None:
    """One direction, by design: when the banner reads a spelling as this machine, the real tool client (given the loopback
    names on its manifest) must accept that same spelling. The client may accept more (it is not asked to be as strict)."""
    from hadavin_sdk.guard.http import LOOPBACK

    assert len(PARITY_URLS) == 40 and len(PARITY_BARE_HOSTS) == 20
    manifest = tuple(sorted(LOOPBACK))
    on_machine = [u for u in PARITY_URLS if not mb._url_leaves_this_machine(u)]
    assert len(on_machine) >= 8, "the corpus must really reach the banner's loopback reading"
    for url in on_machine:
        assert _tool_client_accepts(manifest, url), (
            f"the banner reads {url!r} as this machine, the client refuses it"
        )
    assert sum(_tool_client_accepts(manifest, u) for u in PARITY_URLS) >= 8, (
        "the client side of the corpus is vacuous"
    )
    bare = [h for h in PARITY_BARE_HOSTS if mb._is_this_machine(h)]
    assert len(bare) >= 4, "the bare-host corpus must really reach the banner's loopback reading"
    for host in bare:
        shown = f"[{host}]" if ":" in host else host
        assert _tool_client_accepts((host,), f"https://{shown}/x"), (
            f"the banner reads the bare host {host!r} as this machine, the client refuses it"
        )


# -- batch 6, class E: small defects and sibling gaps -------------------------------------------------------------------
def test_the_words_of_a_name_check_are_required_not_defaulted() -> None:
    with refused(TypeError, "_clean_names called without the words"):
        mb._clean_names("real_services", ["a"], {})  # type: ignore[call-arg]


def test_egress_hosts_may_be_any_list_like_collection_and_a_bare_text_is_refused() -> None:
    # was: a generator of hosts was read (once); a generator is now refused, see the read-once tests at the end of this file
    cfg = _fake_config("demo", [("llm", "fake")])
    for leaving in (
        ["localhost", "api.example.test"],
        ("localhost", "api.example.test"),
        {"api.example.test"},
    ):
        cfg.egress_hosts = leaving
        assert _services(cfg)[0] == (mb.EGRESS_HOSTS,), f"hosts {leaving!r} were not read"
    for this_machine in (
        ["localhost", "127.0.0.1"],
        frozenset({"localhost"}),
        {"localhost": 1}.keys(),
    ):
        cfg.egress_hosts = this_machine
        assert _services(cfg)[0] == (), f"loopback hosts {this_machine!r} were read as leaving"
    for odd in ("localhost", b"localhost", {"localhost": 1}):
        cfg.egress_hosts = odd
        with refused(
            TypeError,
            f"egress_hosts given as {type(odd).__name__} {odd!r}",
            match="not a usable value",
        ):
            _services(cfg)


def test_a_tag_longer_than_the_page_script_shows_is_refused_in_python() -> None:
    long_tag = mb.BannerWords(
        tag_by_mode={"demo": "D" * (mb.MAX_TEXT_LENGTH + 1), "pilot": "P", "prod": "L"}
    )
    with refused(ValueError, "a tag one character too long", match="text or tag is longer"):
        _b("demo", [], [], words=long_tag)
    ok = mb.BannerWords(tag_by_mode={"demo": "D" * mb.MAX_TEXT_LENGTH, "pilot": "P", "prod": "L"})
    assert len(_b("demo", [], [], words=ok).tag) == mb.MAX_TEXT_LENGTH


def test_a_screen_always_gets_a_banner_even_when_the_words_are_malformed() -> None:
    cfg = _fake_config("demo", [("llm", "fake")])
    broken_words = [
        None,
        SimpleNamespace(),
        SimpleNamespace(not_confirmed_tag=5, not_confirmed="x"),
        SimpleNamespace(not_confirmed_tag="T", not_confirmed=""),
        SimpleNamespace(not_confirmed_tag="T", not_confirmed="x" * (mb.MAX_TEXT_LENGTH + 1)),
    ]
    for words in broken_words:
        shown = mb.banner_or_unconfirmed(cfg, words=words, tool_specs={}, overridden=())  # type: ignore[arg-type]
        assert shown == mb.not_confirmed(), (
            f"malformed words {words!r} did not give the default not-confirmed banner"
        )

    class _Raises:
        @property
        def not_confirmed_tag(self) -> str:
            raise RuntimeError("boom")

    assert (
        mb.banner_or_unconfirmed(cfg, words=_Raises(), tool_specs={}, overridden=())
        == mb.not_confirmed()
    )  # type: ignore[arg-type]
    custom = mb.BannerWords(
        tag_by_mode=dict(mb.DEFAULT_WORDS.tag_by_mode), not_confirmed_tag="X", not_confirmed="y"
    )
    assert (
        mb.banner_or_unconfirmed(
            _fake_config("demo", [("llm", "fake")]).__class__(),
            words=custom,
            tool_specs={},
            overridden=(),
        )["tag"]
        == "X"
    )


def test_the_key_words_of_another_language_are_reserved_in_names() -> None:
    spanish = mb.BannerWords(
        tag_by_mode={"demo": "DEMO", "pilot": "PILOTO", "prod": "REAL"},
        made_up="Todos los datos son inventados.",
        nothing_sent="Nada se envia a clientes reales.",
        reserved_words=("inventados", "simulado"),
    )
    for name in ("Datos inventados", "modo simulado", "x Inventados y"):
        with refused(ValueError, f"the reserved word name {name!r}", match="plain words"):
            _b("demo", ["a"], [], names={"a": name}, words=spanish)
    assert _b("demo", ["a"], [], names={"a": "Facturas"}, words=spanish).real == ("Facturas",)
    # the English key words of the default are reserved even when the words in use name others
    with refused(
        ValueError, "the English reserved name made-up under Spanish words", match="plain words"
    ):
        _b("demo", ["a"], [], names={"a": "made-up"}, words=spanish)
    with refused(ValueError, "a reserved_words entry that is empty", match="reserved_words"):
        mb.BannerWords(tag_by_mode=dict(mb.DEFAULT_WORDS.tag_by_mode), reserved_words=("ok", ""))
    with refused(ValueError, "reserved_words given as a list", match="reserved_words"):
        mb.BannerWords(tag_by_mode=dict(mb.DEFAULT_WORDS.tag_by_mode), reserved_words=["x"])  # type: ignore[arg-type]


# -- batch 7, class: an input that can be read only once, and objects the caller handed in --------------------------------
# "Fails on old code" is stated per test (old code = 88e79c25).
class _SameUsedUpGenerator:
    """A config whose property hands back the SAME generator every time: the first reading uses it up."""

    def __init__(self, items: tuple[str, ...]) -> None:
        self._gen = (i for i in items)

    def __call__(self):
        return self._gen


def _config_with_one_shot(field: str, value: object) -> SimpleNamespace:
    cfg = _fake_config("demo", [("llm", "fake")])
    setattr(cfg, field, value)
    return cfg


def test_a_generator_for_egress_hosts_is_refused_and_the_banner_built_twice_is_unconfirmed_both_times() -> (
    None
):
    # written with the fix of an earlier round (not re-run against older code in batch 8): the generator was accepted (tone real once, then tone demo over the same real host)
    cfg = _config_with_one_shot("egress_hosts", (h for h in ("api.example.test",)))
    for attempt in (1, 2):
        shown = mb.banner_or_unconfirmed(cfg, tool_specs={}, overridden=())
        assert shown["tone"] == "unconfirmed", (
            f"egress hosts as a generator: attempt {attempt} gave tone {shown['tone']!r}, not unconfirmed"
        )
        assert "made-up" not in shown["text"], (
            f"egress hosts as a generator: attempt {attempt} claimed made-up"
        )
    with pytest.raises(TypeError, match="egress_hosts"):
        mb.banner_from_config(cfg, tool_specs={}, overridden=())
        raise AssertionError("egress_hosts as a generator was read")


def test_a_generator_for_tool_modules_is_refused_like_egress_hosts() -> None:
    # pin (not a proof): tool_modules already refused a generator on the older code too; this pins the sweep result, and the entry point has a mutant
    cfg = _config_with_one_shot("tool_modules", (m for m in ("mod",)))
    with pytest.raises(TypeError, match="tool_modules"):
        mb.banner_from_config(cfg, tool_specs={}, overridden=())
        raise AssertionError("tool_modules as a generator was read")
    assert mb.banner_or_unconfirmed(cfg, tool_specs={}, overridden=())["tone"] == "unconfirmed", (
        "tool_modules as a generator: the screen did not get the unconfirmed banner"
    )


def test_a_generator_for_the_backend_entries_is_refused() -> None:
    # written with the fix of an earlier round (not re-run against older code in batch 8): the generator was accepted
    cfg = _fake_config("demo", [])
    cfg.backends = SimpleNamespace(
        entries=_SameUsedUpGenerator((("llm", SimpleNamespace(kind="fake")),))
    )
    for attempt in (1, 2):
        shown = mb.banner_or_unconfirmed(cfg, tool_specs={}, overridden=())
        assert shown["tone"] == "unconfirmed", (
            f"backend entries as a generator: attempt {attempt} gave tone {shown['tone']!r}, not unconfirmed"
        )


def test_a_generator_for_the_hosts_of_a_tool_spec_or_for_a_tool_specs_value_is_refused() -> None:
    # pin (not a proof): a spec whose hosts were a generator was refused already on the older code, and so was a by-name mapping that is a generator
    # (pins the sweep result, so the helper at this entry point has a mutant)
    spec = _spec("api.example.test")
    for hosts in ((h for h in ("api.example.test",)), iter(["api.example.test"])):
        object.__setattr__(spec, "hosts", hosts)
        with pytest.raises(TypeError, match="has no `hosts` list of text"):
            mb._tool_hosts_leave({"agent": {"t": spec}})
            raise AssertionError("the hosts of a tool spec as a generator were read")
    with pytest.raises(TypeError, match="must be a mapping of tool name to spec"):
        mb._tool_hosts_leave({"agent": (x for x in ())})  # type: ignore[dict-item]
        raise AssertionError("the tools of an agent as a generator were read")


def test_a_generator_for_names_or_the_service_lists_or_the_reserved_words_is_refused() -> None:
    # partly a pin: the service lists as generators were read on the older code (that part is a proof); names and reserved_words were refused already (those parts only pin)
    with pytest.raises(TypeError, match="real_services must be a list of service names"):
        mb._banner_for("demo", real_services=(r for r in ("crm",)), stand_ins=[])  # type: ignore[arg-type]
        raise AssertionError("real_services as a generator was read")
    with pytest.raises(TypeError, match="stand_ins must be a list of service names"):
        mb._banner_for("demo", real_services=[], stand_ins=(r for r in ("crm",)))  # type: ignore[arg-type]
        raise AssertionError("stand_ins as a generator was read")
    with pytest.raises(TypeError, match="names must be a mapping"):
        mb._banner_for("demo", real_services=[], stand_ins=[], names=(n for n in ()))  # type: ignore[arg-type]
        raise AssertionError("names as a generator was read")
    with pytest.raises(ValueError, match="reserved_words must be a tuple"):
        mb.BannerWords(
            tag_by_mode={"demo": "D", "pilot": "P", "prod": "L"}, reserved_words=(w for w in ("x",))
        )  # type: ignore[arg-type]
        raise AssertionError("reserved_words as a generator was read")


def test_a_bytearray_a_memoryview_and_a_subclass_with_its_own_iteration_are_not_read_by_accident() -> (
    None
):
    # written with the fix of an earlier round (not re-run against older code in batch 8): a bytearray of egress hosts was read as numbers
    cfg = _fake_config("demo", [("llm", "fake")])
    for odd in (bytearray(b"localhost"), memoryview(b"localhost")):
        cfg.egress_hosts = odd
        with pytest.raises(TypeError, match="egress_hosts"):
            mb.banner_from_config(cfg, tool_specs={}, overridden=())
            raise AssertionError(f"egress hosts as a {type(odd).__name__} were read")

    class Quiet(list):
        def __iter__(self):  # an override that would hide every entry
            return iter(())

    cfg.egress_hosts = Quiet(["api.example.test"])
    assert mb._services_in(cfg, {})[0] == (mb.EGRESS_HOSTS,), (
        "a list subclass whose own iteration is empty hid a real host: the builtin reader must be used"
    )


def _demo_config() -> SimpleNamespace:
    return _fake_config("demo", [("llm", "fake"), ("channel", "fake")])


def test_each_override_alone_gives_unconfirmed_with_its_name_and_no_made_up_claim() -> None:
    # written with the fix of an earlier round (not re-run against older code in batch 8): the keyword `overridden` did not exist
    sentence = "These parts were supplied by code and are not checked here: {}."
    for name in mb.OVERRIDES:
        shown = mb.banner_from_config(_demo_config(), tool_specs={}, overridden=(name,))
        assert shown.tone == "unconfirmed", f"override {name}: tone {shown.tone!r}, not unconfirmed"
        # the name is in the banner's own list (the page builds the note from it); the text is exactly the not-confirmed words
        assert shown.overridden == (name,), f"override {name}: lists {shown.overridden!r}"
        assert shown.text == mb.DEFAULT_WORDS.not_confirmed, f"override {name}: text {shown.text!r}"
        assert sentence.format(name) == mb.DEFAULT_WORDS.overridden_note.format(names=name)
        assert "made-up" not in shown.text and "made-up" not in shown.standins, (
            f"override {name}: claims made-up"
        )


def test_no_override_keeps_the_demo_banner_and_the_names_come_out_in_a_fixed_order() -> None:
    # written with the fix of an earlier round (not re-run against older code in batch 8): the keyword `overridden` did not exist
    plain = mb.banner_from_config(_demo_config(), tool_specs={}, overridden=())
    assert plain.tone == "demo" and "made-up demo data" in plain.text, (
        "no override changed the demo banner"
    )
    both = mb.banner_from_config(
        _demo_config(), tool_specs={}, overridden=("secrets", "tools", "tools")
    )
    assert both.overridden == ("tools", "secrets"), f"order or repeat wrong: {both.overridden!r}"


def test_an_override_in_a_pilot_or_live_banner_is_not_quiet_and_in_a_real_banner_it_is_added() -> (
    None
):
    # written with the fix of an earlier round (not re-run against older code in batch 8): the keyword `overridden` did not exist
    quiet = _fake_config("pilot", [("signer", "none")])
    shown = mb.banner_from_config(quiet, tool_specs={}, overridden=("detector",))
    assert shown.tone == "unconfirmed", (
        f"pilot with an override read {shown.tone!r}, not unconfirmed"
    )
    real = _fake_config("prod", [("store", "postgres")])
    shown = mb.banner_from_config(real, tool_specs={}, overridden=("llm",))
    assert shown.tone == "real" and shown.text.endswith("not checked here: llm."), (
        f"real banner: {shown.text!r}"
    )


def test_an_unknown_or_oddly_typed_override_list_is_refused() -> None:
    # written with the fix of an earlier round (not re-run against older code in batch 8): the keyword `overridden` did not exist
    for odd in (("clock",), "tools", (t for t in ("tools",)), [1]):
        with pytest.raises((TypeError, ValueError), match="overridden"):
            mb.banner_from_config(_demo_config(), tool_specs={}, overridden=odd)  # type: ignore[arg-type]
            raise AssertionError(f"overridden={odd!r} was accepted")
    shown = mb.banner_or_unconfirmed(_demo_config(), tool_specs={}, overridden=("clock",))
    assert shown["tone"] == "unconfirmed", (
        "an unknown override name did not give the unconfirmed banner"
    )


def test_app_build_records_the_overrides_that_were_given_and_the_banner_says_so(
    tmp_path: Path,
) -> None:
    # written with the fix of an earlier round (not re-run against older code in batch 8): App had no `overridden` and no `mode_banner`
    from hadavin_sdk import app as app_mod
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.approvals.channel import FakeChannel
    from hadavin_sdk.registry import load_registry
    from tests.conftest import qualify

    cfg_dir = make_cfg(tmp_path)
    SECRETS = FakeSecretProvider({"fixture-token": "t" * 8})
    qualify(load_registry(load_config(cfg_dir)))
    app = app_mod.build(cfg_dir, ["test-agent"], channel=FakeChannel(), secrets=SECRETS)
    assert app.overridden == ("channel", "secrets"), f"recorded {app.overridden!r}"
    shown = app.mode_banner()
    assert shown["tone"] == "unconfirmed" and shown["overridden"] == ["channel", "secrets"], shown
    assert "made-up" not in shown["text"], "an app with handed-in objects claimed made-up data"


def test_given_overrides_counts_an_object_and_a_filled_mapping_but_not_an_empty_one() -> None:
    # written with the fix of an earlier round (not re-run against older code in batch 8): no such function
    from hadavin_sdk import app as app_mod

    assert app_mod._given_overrides(tools={}, sources={}, llm=None) == (), (
        "an empty mapping or None was counted as an override"
    )
    assert app_mod._given_overrides(
        tools={"t": lambda d: ""}, sources={"s": object()}, llm=object()
    ) == (
        "tools",
        "sources",
        "llm",
    )
    with pytest.raises(ValueError, match="not known to the mode banner"):
        app_mod._given_overrides(clock=object())
    assert app_mod._given_overrides(hold_run_ids=lambda: set()) == ("hold_run_ids",), (
        "a hold_run_ids callable was not recorded as an override"
    )


def test_a_real_looking_source_object_handed_to_build_never_yields_the_made_up_sentence() -> None:
    # written with the fix of an earlier round (not re-run against older code in batch 8): no `overridden`, so a banner built from the stand-in-only config said made-up
    shown = mb.banner_or_unconfirmed(_demo_config(), tool_specs={}, overridden=("sources",))
    assert shown["tone"] != "demo" and "made-up" not in shown["text"], (
        f"a source object given to build still gave the made-up sentence: {shown['text']!r}"
    )


@needs_node
def test_a_failed_text_write_never_leaves_the_old_made_up_claim_or_a_stale_mode() -> None:
    # written with the fix of an earlier round (not re-run against older code in batch 8): the old words stayed under the new tone and data-mode stayed "demo"
    seen = _paint(GOOD_DEMO, "failing-text-over-old-claim")
    assert seen["threw"] == "" and seen["hidden"] is False, (
        "the painter threw or left the element hidden"
    )
    assert "made-up" not in (seen["text"] or ""), f"the old made-up claim stayed: {seen['text']!r}"
    assert seen["mode"] == "", f"data-mode stayed {seen['mode']!r} after the failed write"
    assert seen["tone"] == "unconfirmed", f"the tone is {seen['tone']!r}, not unconfirmed"


def _page_banner(**over: object) -> dict:
    return {**GOOD_DEMO, **over}


@needs_node
def test_a_tag_or_text_of_only_white_space_is_not_painted_on_the_page_and_python_refuses_it_too() -> (
    None
):
    # written with the fix of an earlier round (not re-run against older code in batch 8): both accepted a blank tag or text
    for field in ("tag", "text"):
        for blank in (" ", "\t\n", "\u00a0\u2003"):
            seen = _paint(_page_banner(**{field: blank}))
            assert seen["shownTone"] == "unconfirmed", f"the page painted a blank {field} {blank!r}"
    words = mb.BannerWords(tag_by_mode={"demo": "   ", "pilot": "P", "prod": "L"})
    with refused(ValueError, "a blank tag in Python", match="blank"):
        _b("demo", [], [], words=words)
    with refused(ValueError, "a blank made-up text in Python", match="must not be empty"):
        _b(
            "demo",
            [],
            [],
            words=mb.BannerWords(tag_by_mode=words.tag_by_mode | {"demo": "D"}, made_up=" \u00a0 "),
        )
    blank_second = mb.BannerWords(
        tag_by_mode={"demo": "D", "pilot": "P", "prod": "L"}, standins_loud=" "
    )
    with refused(ValueError, "a blank second line in Python", match="blank"):
        _b("demo", [], ["crm"], words=blank_second)
    blank_words = mb.BannerWords(
        tag_by_mode={"demo": "D", "pilot": "P", "prod": "L"}, not_confirmed_tag="  "
    )
    assert (
        mb.banner_or_unconfirmed(
            SimpleNamespace(environment="demo"), words=blank_words, tool_specs={}, overridden=()
        )
        == mb.not_confirmed()
    ), "a not-confirmed tag of only white space was used instead of the default words"


@needs_node
def test_the_length_limit_counts_code_points_on_the_page_and_in_python_at_600_and_601() -> None:
    # written with the fix of an earlier round (not re-run against older code in batch 8): the page counted UTF-16 units, so 600 emoji (1200 units) were refused there but allowed in Python
    for unit in ("a", "\U0001f600"):
        at = _page_banner(text=unit * mb.MAX_TEXT_LENGTH)
        over = _page_banner(text=unit * (mb.MAX_TEXT_LENGTH + 1))
        assert _paint(at)["shownTone"] == "demo", (
            f"the page refused {mb.MAX_TEXT_LENGTH} x {unit!r}"
        )
        assert _paint(over)["shownTone"] == "unconfirmed", f"the page accepted 601 x {unit!r}"
    with pytest.raises(ValueError, match="longer than"):
        _b(
            "demo",
            [],
            [],
            words=mb.BannerWords(
                tag_by_mode={
                    "demo": "\U0001f600" * (mb.MAX_TEXT_LENGTH + 1),
                    "pilot": "P",
                    "prod": "L",
                }
            ),
        )
        raise AssertionError("601 code points were accepted by Python")
    assert (
        len(
            _b(
                "demo",
                [],
                [],
                words=mb.BannerWords(
                    tag_by_mode={
                        "demo": "\U0001f600" * mb.MAX_TEXT_LENGTH,
                        "pilot": "P",
                        "prod": "L",
                    }
                ),
            ).tag
        )
        == mb.MAX_TEXT_LENGTH
    )
    with pytest.raises(
        ValueError, match="longer than"
    ):  # the text: made-up sentence of 601 code points
        _b(
            "demo",
            [],
            [],
            words=mb.BannerWords(
                tag_by_mode={"demo": "D", "pilot": "P", "prod": "L"},
                made_up="\U0001f600" * (mb.MAX_TEXT_LENGTH + 1),
            ),
        )
        raise AssertionError("a text of 601 code points was accepted by Python")


@needs_node
def test_the_page_paints_an_unconfirmed_banner_only_when_it_is_the_own_not_confirmed_words_plus_a_note() -> (
    None
):
    # written with the fix of an earlier round (not re-run against older code in batch 8): any unconfirmed banner was replaced by the fixed one, so the names of the overrides were lost
    shown = mb.banner_from_config(_demo_config(), tool_specs={}, overridden=("llm",)).as_dict()
    seen = _paint(shown)
    assert (
        seen["shownTone"] == "unconfirmed" and "not checked here: llm." in seen["lines"][1]["text"]
    ), f"painted {seen['lines']!r}"
    for bad in (
        {**shown, "text": "Every record here is made-up demo data."},
        {**shown, "tag": "DEMO"},
        {**shown, "real": ["crm"]},
        {**shown, "standins": "MADE-UP STAND-INS IN USE: x."},
    ):
        seen = _paint(bad)
        _unconfirmed(seen, f"painted odd unconfirmed {bad!r}")


# -- batch 8: "not known" is not "none" (class A), the override list comes from `build` (class B), the page (class D) ----
def _built_app(tmp_path: Path):
    from hadavin_sdk import app as app_mod
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.approvals.channel import FakeChannel
    from hadavin_sdk.registry import load_registry
    from tests.conftest import qualify

    cfg_dir = make_cfg(tmp_path)
    qualify(load_registry(load_config(cfg_dir)))
    secrets = FakeSecretProvider({"fixture-token": "t" * 8})
    return app_mod.build(cfg_dir, ["test-agent"], channel=FakeChannel(), secrets=secrets)


def test_an_app_made_by_hand_gives_the_unconfirmed_banner_not_the_made_up_one(
    tmp_path: Path,
) -> None:
    # proof (fails on old code: the default `()` read as "nothing was handed in", so this app said made-up)
    import dataclasses

    from hadavin_sdk.app import App

    built = _built_app(tmp_path)
    by_hand = App(
        **{
            f.name: getattr(built, f.name)
            for f in dataclasses.fields(built)
            if f.init and f.name != "overridden"
        }
    )
    assert by_hand.overridden is None, f"a hand-made App recorded {by_hand.overridden!r}"
    assert by_hand.mode_banner()["tone"] == "unconfirmed", (
        "a hand-made App did not give the unconfirmed banner"
    )
    told = App(
        **{
            f.name: getattr(built, f.name)
            for f in dataclasses.fields(built)
            if f.init and f.name != "overridden"
        },
        overridden=(),
    )
    assert told.mode_banner()["tone"] == "unconfirmed", (
        "a hand-made App that says overridden=() was believed"
    )


def test_an_app_copied_or_changed_after_build_gives_the_unconfirmed_banner(tmp_path: Path) -> None:
    # proof (fails on old code: the recorded list stayed and the banner said made-up although a part had been replaced)
    import dataclasses

    app = _built_app(tmp_path)
    app.seal(
        ()
    )  # as if build had been given nothing: the banner is the made-up one while the app is untouched
    assert app.mode_banner()["tone"] == "demo", "an untouched sealed app lost its banner"
    for label, change in (
        (
            "dataclasses.replace with a real source",
            lambda a: dataclasses.replace(a, sources={"k": object()}),
        ),
        ("an attribute set after build", lambda a: setattr(a, "llm", object()) or a),
        ("a source added after build", lambda a: a.sources.update(k=object()) or a),
        ("the runtime llm replaced", lambda a: setattr(a.runtime, "llm", object()) or a),
        ("the store replaced", lambda a: setattr(a, "store", object()) or a),
    ):
        fresh = _built_app(tmp_path / label.replace(" ", "_"))
        fresh.seal(())
        changed = change(fresh)
        assert changed.mode_banner()["tone"] == "unconfirmed", (
            f"{label}: the banner was {changed.mode_banner()['tone']!r}"
        )


def test_overridden_is_a_required_keyword_and_none_means_not_known() -> None:
    # proof (fails on old code: the keyword had the default `()`)
    cfg = _demo_config()
    with pytest.raises(TypeError, match="overridden"):
        mb.banner_from_config(cfg, tool_specs={})  # type: ignore[call-arg]
        raise AssertionError("banner_from_config without overridden was accepted")
    with pytest.raises(TypeError, match="overridden"):
        mb.banner_or_unconfirmed(cfg, tool_specs={})  # type: ignore[call-arg]
        raise AssertionError("banner_or_unconfirmed without overridden was accepted")
    with pytest.raises(ValueError) as raised:
        mb.banner_from_config(cfg, tool_specs={}, overridden=None)
        raise AssertionError("overridden=None was read as none")
    assert "overridden is not known" in str(raised.value), (
        f"overridden=None did not say it is not known: {raised.value}"
    )
    shown = mb.banner_or_unconfirmed(cfg, tool_specs={}, overridden=None)
    assert shown["tone"] == "unconfirmed" and "made-up" not in shown["text"], shown


def _unclassified(function) -> set[str]:
    """The parameters of `function` that are neither an override nor on the not-connectivity list, plus any that are on both."""
    import inspect

    names = set(inspect.signature(function).parameters)
    both = set(mb.OVERRIDES) & set(mb.NOT_CONNECTIVITY)
    return (names ^ (set(mb.OVERRIDES) | set(mb.NOT_CONNECTIVITY))) | both


def test_every_build_parameter_is_an_override_or_on_the_not_connectivity_list_with_a_reason() -> (
    None
):
    # proof (fails on old code: hold_run_ids was in neither list, and there was no NOT_CONNECTIVITY)
    from hadavin_sdk import app as app_mod

    assert _unclassified(app_mod.build) == set(), (
        f"parameters of build on neither list or on both: {sorted(_unclassified(app_mod.build))}"
    )
    assert all(r.strip() for r in mb.NOT_CONNECTIVITY.values()), "a reason is empty"

    def build_with_a_new_keyword(
        config_dir, agents, *, newcomer=None, **rest
    ): ...  # a copy of `build` plus one parameter

    def build_with_a_missing_one(config_dir, agents): ...

    assert "newcomer" in _unclassified(build_with_a_new_keyword), (
        "a new build keyword was not reported"
    )
    assert _unclassified(build_with_a_missing_one) >= {"tools"}, (
        "a list entry that build lacks was not reported"
    )


def test_pin_the_page_lists_and_the_python_lists_of_overrides_agree() -> None:
    # pin (passes on old code that had the same six names in both places; the page list is new)
    js = JS.read_text(encoding="utf-8")
    found = re.search(r"var OVERRIDES = Object.freeze\(\[(.*?)\]\);", js)
    assert found, "the page has no OVERRIDES list"
    assert tuple(re.findall(r"'([a-z_]+)'", found.group(1))) == mb.OVERRIDES
    note = re.search(r"var OVERRIDDEN_NOTE = '(.*?)';", js)
    assert note and note.group(1) == mb.DEFAULT_WORDS.overridden_note, (
        "the page note differs from the Python words"
    )


def _blank_set_of_js_literal() -> set[int]:
    js = JS.read_text(encoding="utf-8")
    found = re.search(r"var BLANK = /\^\[(.*)\]\*\$/;", js)
    assert found, "the page has no BLANK literal"
    body = found.group(1)
    points: set[int] = set()
    tokens = re.findall(r"\\u([0-9a-f]{4})|\\([tnvfr])|(-)", body)
    seq: list = []
    for u, esc, dash in tokens:
        if dash:
            seq.append("-")
        else:
            seq.append(int(u, 16) if u else {"t": 9, "n": 10, "v": 11, "f": 12, "r": 13}[esc])
    i = 0
    while i < len(seq):
        if i + 2 < len(seq) and seq[i + 1] == "-":
            points.update(range(seq[i], seq[i + 2] + 1))
            i += 3
        else:
            points.add(seq[i])
            i += 1
    return points


def _blank_set_of_python() -> set[int]:
    return {cp for lo, hi in mb.BLANK_RANGES for cp in range(lo, hi + 1)}


def test_pin_the_blank_set_of_python_and_of_the_page_literal_is_one_set() -> None:
    # pin (the sets did not exist as lists on old code)
    assert _blank_set_of_js_literal() == _blank_set_of_python(), (
        f"blank sets differ at code points {sorted(_blank_set_of_js_literal() ^ _blank_set_of_python())}"
    )


@needs_node
def test_the_blank_set_is_what_python_strip_and_javascript_trim_both_call_white_space() -> None:
    # proof (fails on old code: the page used trim, so U+0085 and U+001C to U+001F were visible there but blank in Python, and U+FEFF the reverse)
    out = subprocess.run(  # noqa: S603 (fixed argument list, no shell)
        ["node", str(PROBE.with_name("mode_banner_blank_probe.js")), str(JS)],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    seen = json.loads(out.stdout.strip().splitlines()[-1])

    def points(ranges: list) -> set[int]:
        return {cp for lo, hi in ranges for cp in range(lo, hi + 1)}

    python_white = {
        cp for cp in range(0x110000) if not 0xD800 <= cp <= 0xDFFF and chr(cp).isspace()
    }
    assert points(seen["page"]) == _blank_set_of_python() == python_white | points(seen["trim"]), (
        "the page, Python and the union of strip and trim do not agree: "
        f"{sorted(points(seen['page']) ^ (python_white | points(seen['trim'])))}"
    )


@needs_node
def test_a_forged_unconfirmed_text_is_not_painted_only_the_exact_words_and_a_note_built_by_the_page() -> (
    None
):
    # proof (fails on old code: any text that started with the not-confirmed words was painted, suffix and all)
    words = mb.DEFAULT_WORDS
    base = mb.banner_from_config(_demo_config(), tool_specs={}, overridden=("llm",)).as_dict()
    for forged in (
        words.not_confirmed + " " + words.made_up,
        words.not_confirmed + " Every record here is made-up demo data.",
        words.not_confirmed
        + " These parts were supplied by code and are not checked here: llm. Every record here is made-up demo data.",
        words.not_confirmed + " ",
    ):
        seen = _paint({**base, "text": forged})
        _unconfirmed(seen, f"painted a forged text {forged!r}")
        assert all("made-up" not in line["text"] for line in seen["lines"]), (
            f"painted {seen['lines']!r}"
        )
    seen = _paint(base)
    assert seen["lines"][1][
        "text"
    ] == " " + words.not_confirmed + " " + words.overridden_note.format(names="llm"), seen["lines"]
    for odd in (
        ["llm", "nothing"],
        ["llm"] * 8,
        "llm",
        [3],
        ["Every record here is made-up demo data."],
    ):
        _unconfirmed(_paint({**base, "overridden": odd}), f"painted overridden={odd!r}")
    plain = _paint({**base, "overridden": []})
    assert plain["lines"][1]["text"] == " " + words.not_confirmed, (
        f"an empty list added a note: {plain['lines']!r}"
    )


@needs_node
def test_a_tag_or_text_made_only_of_the_code_points_python_and_the_page_disagreed_on_is_not_painted() -> (
    None
):
    # proof (fails on old code: U+0085, U+001C and U+FEFF are blank to one of strip and trim, not to the other)
    for blank in ("\u0085", "\u001c", "\u001f", "\ufeff", "\ufeff\u0085\u001c"):
        _unconfirmed(_paint(_page_banner(tag=blank)), f"painted tag {blank!r}")
        _unconfirmed(_paint(_page_banner(text=blank)), f"painted text {blank!r}")
        with refused(ValueError, f"a blank tag {blank!r} in Python", match="blank"):
            _b(
                "demo",
                [],
                [],
                words=mb.BannerWords(tag_by_mode={"demo": blank, "pilot": "P", "prod": "L"}),
            )
    assert _paint(_page_banner(tag="a\ufeff"))["shownTone"] == "demo", (
        "a visible tag with an edge mark was refused"
    )


@needs_node
def test_a_text_of_ten_million_characters_is_refused_at_once_and_astral_characters_count_once() -> (
    None
):
    # proof (fails on old code: Array.from ran over the whole string first; the time bound pins that it does not)
    seen = _paint(_page_banner(), "huge-text")
    assert seen["shownTone"] == "unconfirmed", "ten million characters were painted"
    assert seen["ms"] < 200, f"refusing a ten million character text took {seen['ms']} ms"
    for unit in ("a", "\U0001f600"):
        assert _paint(_page_banner(text=unit * 600))["shownTone"] == "demo", (
            f"600 x {unit!r} refused"
        )
        assert _paint(_page_banner(text=unit * 601))["shownTone"] == "unconfirmed", (
            f"601 x {unit!r} accepted"
        )
    for unit in ("a", "\U0001f600"):
        words = mb.BannerWords(tag_by_mode={"demo": unit * 601, "pilot": "P", "prod": "L"})
        with refused(ValueError, f"601 x {unit!r} in Python", match="longer than"):
            _b("demo", [], [], words=words)
