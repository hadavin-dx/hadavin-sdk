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
import re
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from hadavin_sdk import mode_banner as mb
from hadavin_sdk.backends.table import DEMO_ONLY, TABLE
from hadavin_sdk.config import load_config
from hadavin_sdk.stages import STAGES
from hadavin_sdk.tools import ToolSpec
from tests.conftest import make_cfg
from tests.fixed_run import run as run_fixed
from tests.refusal import refused
from tests.seeded import Seeded

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
    kw.setdefault("overridden", ())  # `_banner_for` has no default for it
    return mb._banner_for(mode, real_services=real or [], stand_ins=pretend or [], **kw)


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


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_the_lists_are_required_so_an_unchecked_call_cannot_say_nothing_real() -> None:
    # `overridden=()` is given in every call, so only the missing lists can make the call fail (a missing `overridden` raises a
    # TypeError too, which let the mutant row B12 survive on dd827d79)
    banner_for: Any = mb._banner_for
    for label, call in (
        ("no lists at all", lambda: banner_for("demo", overridden=())),
        ("real_services only", lambda: banner_for("demo", real_services=[], overridden=())),
        ("stand_ins only", lambda: banner_for("demo", stand_ins=[], overridden=())),
        ("both lists given by position", lambda: banner_for("demo", [], [], overridden=())),
    ):
        with refused(TypeError, f"the call with {label}"):
            call()


def test_an_unknown_stage_is_refused() -> None:
    for mode in ["", "DEMO", "Demo", "canary", "live", "test", None, 3]:
        with refused(ValueError, f"stage {mode!r}", match="is not one of demo, pilot, prod"):
            _b(mode)


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_bare_string_dict_set_or_non_list_is_refused_not_read_by_accident() -> None:
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
                mb._banner_for("demo", overridden=(), **kwargs)


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
        _b("demo", cast("Any", [3]))


def test_a_banner_longer_than_the_page_script_accepts_is_refused_in_python() -> None:
    long_names = {f"k{i}": f"{chr(65 + i)}" * 40 for i in range(20)}
    with refused(ValueError, "twenty long real service names", match="too many services"):
        _b("pilot", list(long_names), names=long_names)
    with refused(ValueError, "twenty long stand-in names", match="too many services"):
        _b("pilot", [], list(long_names), names=long_names)
    ok = {f"k{i}": f"{chr(65 + i)}" * 20 for i in range(10)}
    assert len(_b("pilot", list(ok), names=ok).text) <= mb.MAX_TEXT_LENGTH


# -- property test, seeded: only the safety property is asserted, never the rule that produces the text -------------
# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_property_the_made_up_claim_never_appears_next_to_a_real_service() -> None:
    rng = Seeded(20261112)
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
            b = mb._banner_for(
                mode, real_services=real, stand_ins=pretend, names=names, overridden=()
            )
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
    rng = Seeded(20261112)
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


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_the_old_public_names_are_gone_and_banner_from_config_is_the_only_entry() -> None:
    for old in ("banner_for", "services_in", "stand_ins_in"):
        assert not hasattr(mb, old), f"the old public name {old!r} is still in the module"
        assert old not in mb.__all__, f"the old public name {old!r} is still in __all__"
    assert [n for n in mb.__all__ if n.startswith("banner")] == [
        "banner_from_config",
        "banner_or_unconfirmed",
    ]
    assert all(hasattr(mb, n) for n in mb.__all__)
    star = {
        name: getattr(mb, name) for name in mb.__all__
    }  # what `from hadavin_sdk.mode_banner import *` binds
    assert "banner_from_config" in star and not any(k.startswith("_") for k in star)


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
    out = run_fixed(
        ["node", str(PROBE), str(JS), arg, scenario],
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
    "mode": "demo",
    "tone": "demo",
    "tag": "DEMO",
    "text": "t",
    "standins": "s",
    "real": [],
    "stand_ins": ["a"],
    "overridden": [],
}


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


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
@needs_node
def test_pin_a_banner_that_contradicts_itself_is_not_painted_as_given() -> None:
    real = {
        "mode": "pilot",
        "tone": "real",
        "tag": "PILOT",
        "text": "Real services: CRM.",
        "standins": "",
        "real": ["CRM"],
        "stand_ins": [],
    }
    quiet = {
        "mode": "pilot",
        "tone": "quiet",
        "tag": "PILOT",
        "text": "None.",
        "standins": "",
        "real": [],
        "stand_ins": [],
        "overridden": [],
    }
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
        "mode": "pilot",
        "tone": "real",
        "tag": "<b>",
        "text": evil + " CRM",
        "standins": "<i>",
        "real": ["CRM"],
        "stand_ins": [],
    }
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
    rng = Seeded(20261113)
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
            mb.banner_from_config(cfg, tool_specs=odd, overridden=())


def test_tool_specs_has_no_default_so_forgetting_it_is_an_error() -> None:
    cfg = _fake_config("demo", [("llm", "fake")])
    with refused(TypeError, "banner_from_config called without tool_specs"):
        cast("Any", mb.banner_from_config)(cfg, overridden=())
    with refused(TypeError, "_services_in called without tool_specs"):
        cast("Any", mb._services_in)(cfg)


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
        mb._services_in(cfg, ["not", "a", "mapping"])


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


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_names_in_follows_the_table() -> None:
    for text, name, expected in NAME_TABLE:
        assert mb.names_in(text, name) is expected, (
            f"names_in({text!r}, {name!r}) was not {expected}"
        )
    assert mb.names_in("anything", "") is False


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
@needs_node
def test_pin_the_page_and_python_agree_on_every_row_of_the_name_table() -> None:
    for text, name, expected in NAME_TABLE:
        banner = {
            "mode": "pilot",
            "tone": "real",
            "tag": "PILOT",
            "text": text,
            "standins": "",
            "real": [name],
            "stand_ins": [],
        }
        page_says_named = _paint(banner)["tone"] == "real"
        assert page_says_named is expected is mb.names_in(text, name), (
            f"the page read {name!r} in {text!r} as {'named' if page_says_named else 'not named'}, python as {mb.names_in(text, name)}"
        )


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


# What the tool client may raise for a url or a host it will not use, besides its own `ToolRefused`.
_OTHER_REFUSALS = (ValueError, TypeError, LookupError, AttributeError, OSError)


def _type_error_of(call, why: str) -> str:
    """The text of the TypeError `call` raises; a different outcome fails with `why` in the message."""
    try:
        call()
    except TypeError as exc:
        return str(exc)
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
        name="read_x",
        function="mod:read_x",
        description="reads x",
        input_schema={"type": "object"},
        side_effect="none",
        hosts=("api.example.test",),
        operations=["op.read"],
    )
    ctx = tools_mod.ToolContext(spec, 1.0, bindings={"op.read": ("GET", r"/.*")})
    secure = url.replace("http://", "https://", 1)
    for candidate in (url, secure):
        try:
            ctx.fetch("GET", candidate, operation="op.read")
        except tools_mod.ToolRefused as why:
            text = str(why)
            if any(w in text for w in ("backslash", "percent-encoding", "credentials in the URL")):
                return True
        except _OTHER_REFUSALS:  # a malformed url that raises elsewhere is refused all the same
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
        cast("Any", mb.banner_or_unconfirmed)(good)
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
        "pilot",
        "real",
        "PILOT",
        "Real services are connected: Mail. Data this system handles may be sent to them. CRM",
        "",
        ("CRM",),
        (),
    )
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
    )  # a kind someone later refuses in prod for being demo-only
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
    "localhost",
    "LocalHost",
    "LOCALHOST.",
    "127.0.0.1",
    "[::1]",
    "127.0.0.2",
    "[::2]",
    "localhost.example.test",
]
_PARITY_TAILS = ["", "/", "/a/b", "?q=1", ":443/"]
PARITY_URLS = [
    f"https://{h}{tail}" for h in _PARITY_HOSTS for tail in _PARITY_TAILS
]  # 40 spellings
PARITY_BARE_HOSTS = [
    "localhost",
    "LOCALHOST",
    "Localhost",
    "localhost.",
    "LOCALHOST.",
    "127.0.0.1",
    "::1",
    "[::1]",
    "127.0.0.2",
    "::2",
    "0." + "0.0.0",
    "localhost.localdomain",
    "127.1",
    "0x7f.1",
    "2130706433",
    " localhost",
    "localhost ",
    "localhost\n",
    "ｌｏｃａｌｈｏｓｔ",
    "evil.example",
]


class _ClientAccepted(Exception):
    pass


def _tool_client_accepts(manifest_hosts: tuple[str, ...], url: str) -> bool:
    """True when the real `ToolContext.fetch` gets past every check of the operation, url, host and port, to the point of
    counting the request (it is stopped there: nothing is sent)."""
    from hadavin_sdk import tools as tools_mod

    spec = ToolSpec(
        name="read_x",
        function="mod:read_x",
        description="reads x",
        input_schema={"type": "object"},
        side_effect="none",
        hosts=manifest_hosts,
        operations=["op.read"],
    )

    def stop() -> None:
        raise _ClientAccepted

    ctx = tools_mod.ToolContext(spec, 1.0, bindings={"op.read": ("GET", r"/.*")}, on_fetch=stop)
    try:
        ctx.fetch("GET", url, operation="op.read")
    except _ClientAccepted:
        return True
    except (tools_mod.ToolRefused, *_OTHER_REFUSALS):  # any refusal is a refusal
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
        cast("Any", mb._clean_names)("real_services", ["a"], {})


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
        shown = mb.banner_or_unconfirmed(cfg, words=words, tool_specs={}, overridden=())
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
    )
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
        mb.BannerWords(tag_by_mode=dict(mb.DEFAULT_WORDS.tag_by_mode), reserved_words=["x"])


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
    # written with the fix of an earlier round (a pin: it passes on 07bfda12, the code of batch 8; it was not run against the code before batch 8): the generator was accepted (tone real once, then tone demo over the same real host)
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
    # written with the fix of an earlier round (a pin: it passes on 07bfda12, the code of batch 8; it was not run against the code before batch 8): the generator was accepted
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
        cast("Any", mb._tool_hosts_leave)({"agent": (x for x in ())})
        raise AssertionError("the tools of an agent as a generator were read")


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_generator_for_names_or_the_service_lists_or_the_reserved_words_is_refused() -> None:
    # partly a pin: the service lists as generators were read on the older code (that part is a proof); names and reserved_words were refused already (those parts only pin)
    with pytest.raises(TypeError, match="real_services must be a list of service names"):
        mb._banner_for("demo", real_services=(r for r in ("crm",)), stand_ins=[], overridden=())
        raise AssertionError("real_services as a generator was read")
    with pytest.raises(TypeError, match="stand_ins must be a list of service names"):
        mb._banner_for("demo", real_services=[], stand_ins=(r for r in ("crm",)), overridden=())
        raise AssertionError("stand_ins as a generator was read")
    with pytest.raises(TypeError, match="names must be a mapping"):
        mb._banner_for("demo", real_services=[], stand_ins=[], names=(n for n in ()), overridden=())
        raise AssertionError("names as a generator was read")
    with pytest.raises(ValueError, match="reserved_words must be a tuple"):
        mb.BannerWords(
            tag_by_mode={"demo": "D", "pilot": "P", "prod": "L"}, reserved_words=(w for w in ("x",))
        )
        raise AssertionError("reserved_words as a generator was read")


def test_a_bytearray_a_memoryview_and_a_subclass_with_its_own_iteration_are_not_read_by_accident() -> (
    None
):
    # written with the fix of an earlier round (a pin: it passes on 07bfda12, the code of batch 8; it was not run against the code before batch 8): a bytearray of egress hosts was read as numbers
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
    # written with the fix of an earlier round (a pin: it passes on 07bfda12, the code of batch 8; it was not run against the code before batch 8): the keyword `overridden` did not exist
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
    # written with the fix of an earlier round (a pin: it passes on 07bfda12, the code of batch 8; it was not run against the code before batch 8): the keyword `overridden` did not exist
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
    # written with the fix of an earlier round (a pin: it passes on 07bfda12, the code of batch 8; it was not run against the code before batch 8): the keyword `overridden` did not exist
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


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_an_unknown_or_oddly_typed_override_list_is_refused() -> None:
    # written with the fix of an earlier round (a pin: it passes on 07bfda12, the code of batch 8; it was not run against the code before batch 8): the keyword `overridden` did not exist
    for odd in (("timeout_s",), "tools", (t for t in ("tools",)), [1]):
        with pytest.raises((TypeError, ValueError), match="overridden"):
            mb.banner_from_config(_demo_config(), tool_specs={}, overridden=odd)
            raise AssertionError(f"overridden={odd!r} was accepted")
    shown = mb.banner_or_unconfirmed(_demo_config(), tool_specs={}, overridden=("clock",))
    assert shown["tone"] == "unconfirmed", (
        "an unknown override name did not give the unconfirmed banner"
    )


def test_app_build_records_the_overrides_that_were_given_and_the_banner_says_so(
    tmp_path: Path,
) -> None:
    # written with the fix of an earlier round (a pin: it passes on 07bfda12, the code of batch 8; it was not run against the code before batch 8): App had no `overridden` and no `mode_banner`
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


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_given_overrides_counts_an_object_and_a_filled_mapping_but_not_an_empty_one() -> None:
    # written with the fix of an earlier round (a pin: it passes on 07bfda12, the code of batch 8; it was not run against the code before batch 8): no such function
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
        app_mod._given_overrides(timeout_s=object())
    assert app_mod._given_overrides(hold_run_ids=lambda: set()) == ("hold_run_ids",), (
        "a hold_run_ids callable was not recorded as an override"
    )


def test_a_real_looking_source_object_handed_to_build_never_yields_the_made_up_sentence() -> None:
    # written with the fix of an earlier round (a pin: it passes on 07bfda12, the code of batch 8; it was not run against the code before batch 8): no `overridden`, so a banner built from the stand-in-only config said made-up
    shown = mb.banner_or_unconfirmed(_demo_config(), tool_specs={}, overridden=("sources",))
    assert shown["tone"] != "demo" and "made-up" not in shown["text"], (
        f"a source object given to build still gave the made-up sentence: {shown['text']!r}"
    )


@needs_node
def test_a_failed_text_write_never_leaves_the_old_made_up_claim_or_a_stale_mode() -> None:
    # written with the fix of an earlier round (a pin: it passes on 07bfda12, the code of batch 8; it was not run against the code before batch 8): the old words stayed under the new tone and data-mode stayed "demo"
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
    # written with the fix of an earlier round (a pin: it passes on 07bfda12, the code of batch 8; it was not run against the code before batch 8): both accepted a blank tag or text
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
    # written with the fix of an earlier round (a pin: it passes on 07bfda12, the code of batch 8; it was not run against the code before batch 8): the page counted UTF-16 units, so 600 emoji (1200 units) were refused there but allowed in Python
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


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
@needs_node
def test_pin_an_unconfirmed_banner_keeps_the_override_names_in_its_note_and_odd_unconfirmed_fields_are_not_painted() -> (
    None
):
    # What it guards against (a fault of the code before batch 8): any unconfirmed banner was replaced by the fixed one, so the names of the overrides were lost)
    shown = mb.banner_from_config(_demo_config(), tool_specs={}, overridden=("llm",)).as_dict()
    seen = _paint(shown)
    assert (
        seen["shownTone"] == "unconfirmed" and "not checked here: llm." in seen["lines"][1]["text"]
    ), f"painted {seen['lines']!r}"
    # a banner that also lists a real service or a second line contradicts its tone: the plain fallback, no names
    for bad in (
        {**shown, "real": ["crm"]},
        {**shown, "standins": "MADE-UP STAND-INS IN USE: x."},
    ):
        seen = _paint(bad)
        _unconfirmed(seen, f"painted odd unconfirmed {bad!r}")


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: painted odd unconfirmed {'mode': 'demo', 'tone': 'unconfirmed', 'tag': 'UNCONFIRMED', 'text': 'Every record here is made
@needs_node
def test_an_unconfirmed_banner_with_other_tag_or_text_is_painted_with_the_pages_words_and_the_names() -> (
    None
):
    # what it shows (such a banner was replaced by the plain fallback, so the names of the overrides were lost)
    shown = mb.banner_from_config(_demo_config(), tool_specs={}, overridden=("llm",)).as_dict()
    expected = (
        " "
        + mb.not_confirmed()["text"]
        + " "
        + mb.DEFAULT_WORDS.overridden_note.format(names="llm")
    )
    for odd in (
        {**shown, "text": "Every record here is made-up demo data."},
        {**shown, "tag": "DEMO"},
    ):
        seen = _paint(odd)
        assert seen["shownTone"] == "unconfirmed" and seen["lines"][1]["text"] == expected, (
            f"painted odd unconfirmed {odd!r}: {seen['lines']!r}"
        )


# -- batch 8: "not known" is not "none" (class A), the override list comes from `build` (class B), the page (class D) ----
def _given(*names: str):
    """The names `build` works out (a `_Given`), as `build` hands them to `_seal`; `_given()` is "nothing was handed in"."""
    from hadavin_sdk import app as app_mod

    # Older heads (dd827d79, cdbe1445) have no `_Given`: their `_seal` took a plain tuple, so the same call runs there and the
    # old result reflects behaviour, not a missing name.
    return getattr(app_mod, "_Given", tuple)(names)


def _built_app(tmp_path: Path, channel=None):
    from hadavin_sdk import app as app_mod
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.approvals.channel import FakeChannel
    from hadavin_sdk.registry import load_registry
    from tests.conftest import qualify

    cfg_dir = make_cfg(tmp_path)
    qualify(load_registry(load_config(cfg_dir)))
    secrets = FakeSecretProvider({"fixture-token": "t" * 8})
    return app_mod.build(cfg_dir, ["test-agent"], channel=channel or FakeChannel(), secrets=secrets)


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


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_an_app_copied_or_changed_after_build_gives_the_unconfirmed_banner(
    tmp_path: Path,
) -> None:
    import dataclasses

    app = _built_app(tmp_path)
    app._seal(
        _given()
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
        # same number of parts and same names: only the comparison of each part by identity sees it
        (
            "the config replaced by an equal copy",
            lambda a: setattr(a, "config", __import__("copy").copy(a.config)) or a,
        ),
    ):
        fresh = _built_app(tmp_path / label.replace(" ", "_"))
        fresh._seal(_given())
        changed = change(fresh)
        assert changed.mode_banner()["tone"] == "unconfirmed", (
            f"{label}: the banner was {changed.mode_banner()['tone']!r}"
        )


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_banner_from_config_has_no_default_for_overridden() -> None:
    # What it guards against (a fault of the code before batch 8): the keyword had the default `()`)
    with pytest.raises(TypeError, match="overridden"):
        cast("Any", mb.banner_from_config)(_demo_config(), tool_specs={})
        raise AssertionError("banner_from_config without overridden was accepted")


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_banner_or_unconfirmed_has_no_default_for_overridden() -> None:
    # What it guards against (a fault of the code before batch 8): the keyword had the default `()`)
    with pytest.raises(TypeError, match="overridden"):
        cast("Any", mb.banner_or_unconfirmed)(_demo_config(), tool_specs={})
        raise AssertionError("banner_or_unconfirmed without overridden was accepted")


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_overridden_none_raises_a_value_error_in_banner_from_config() -> None:
    # What it guards against (a fault of the code before batch 8): None was read as none): the rule itself
    with pytest.raises(ValueError, match="overridden") as raised:
        mb.banner_from_config(_demo_config(), tool_specs={}, overridden=None)
        raise AssertionError("overridden=None was read as none")
    assert raised.type is ValueError


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_overridden_none_says_it_is_not_known_and_gives_the_unconfirmed_banner() -> None:
    # What it guards against (a fault of the code before batch 8): None was read as none): the words, and the screen call
    with pytest.raises(ValueError) as raised:
        mb.banner_from_config(_demo_config(), tool_specs={}, overridden=None)
        raise AssertionError("overridden=None was read as none (words)")
    assert "overridden is not known" in str(raised.value), (
        f"overridden=None did not say it is not known: {raised.value}"
    )
    shown = mb.banner_or_unconfirmed(_demo_config(), tool_specs={}, overridden=None)
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


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_the_page_lists_of_overrides_and_the_note_words_agree_with_python() -> None:
    # What it guards: a pin (passes on 07bfda12) (fails only on the code before batch 8: the page had no such lists)
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


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_the_blank_set_of_python_and_of_the_page_literal_is_one_set() -> None:
    # What it guards: a pin (passes on 07bfda12) (fails only on the code before batch 8: the sets did not exist as lists)
    assert _blank_set_of_js_literal() == _blank_set_of_python(), (
        f"blank sets differ at code points {sorted(_blank_set_of_js_literal() ^ _blank_set_of_python())}"
    )


@needs_node
def test_the_blank_set_is_what_python_strip_and_javascript_trim_both_call_white_space() -> None:
    # proof (fails on old code: the page used trim, so U+0085 and U+001C to U+001F were visible there but blank in Python, and U+FEFF the reverse)
    out = run_fixed(
        ["node", str(PROBE.with_name("mode_banner_blank_probe.js")), str(JS)],
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


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: painted a forged text 'The mode of this system could not be confirmed. Treat everything here as real. Every record here
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
        assert seen["shownTone"] == "unconfirmed" and seen["threw"] == "", f"painted {seen!r}"
        assert seen["lines"][1]["text"] == (
            " " + words.not_confirmed + " " + words.overridden_note.format(names="llm")
        ), f"painted a forged text {forged!r}: {seen['lines']!r}"
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


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
@needs_node
def test_pin_a_text_of_ten_million_characters_is_refused_at_once_and_astral_characters_count_once() -> (
    None
):
    # What it guards against (a fault of the code before batch 8): Array.from ran over the whole string first; counted work, not a clock: no string longer than twice the limit may reach Array.from)
    seen = _paint(_page_banner(), "huge-text")
    assert seen["shownTone"] == "unconfirmed", "ten million characters were painted"
    assert seen["arrayFromLongest"] <= 2 * mb.MAX_TEXT_LENGTH, (
        f"the page walked a string of {seen['arrayFromLongest']} units with Array.from before refusing the ten million character text"
    )
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


# -- batch 9: the seal holds references (class 1), the page and the words (class 2) --------------------------------------
def _sealed_app(tmp_path: Path, name: str = "app"):
    """A built app sealed as if `build` had been given nothing: its banner is the made-up one while it is untouched."""
    app = _built_app(tmp_path / name)
    app._seal(_given())
    assert app.mode_banner()["tone"] == "demo", "an untouched sealed app lost its banner"
    return app


def _replace_hook(member: str):
    def change(a) -> None:
        setattr(a.runtime.hooks, member, (lambda *x, **k: None))

    return change


HOOK_MEMBERS = (
    "request_approval",
    "execute",
    "verify",
    "rollback",
    "post_card",
    "level_override",
    "toolbox",
    "validate_proposal",
    "hold_run_ids",
    "restored_key",
)


def _each_replaced_part() -> list:
    import dataclasses

    cases: list = [(f"hooks.{m}", _replace_hook(m)) for m in HOOK_MEMBERS]
    cases += [
        (
            "a new Hooks with the same tools dict",
            lambda a: setattr(a.runtime, "hooks", dataclasses.replace(a.runtime.hooks)),
        ),
        ("a tool entry replaced", lambda a: a.runtime.hooks.tools.update(t=lambda d: "") or None),
        ("app.store", lambda a: setattr(a, "store", object())),
        ("app.audit", lambda a: setattr(a, "audit", object())),
        ("app.executor", lambda a: setattr(a, "executor", object())),
        ("app.limits", lambda a: setattr(a, "limits", object())),
        ("app.registry", lambda a: setattr(a, "registry", object())),
        ("app.config", lambda a: setattr(a, "config", object())),
        ("app.approvals", lambda a: setattr(a, "approvals", object())),
        ("runtime.store", lambda a: setattr(a.runtime, "store", object())),
        ("runtime.audit", lambda a: setattr(a.runtime, "audit", object())),
        ("runtime.registry", lambda a: setattr(a.runtime, "registry", object())),
        ("runtime.llm", lambda a: setattr(a.runtime, "llm", object())),
        ("runtime.detector", lambda a: setattr(a.runtime, "detector", object())),
        ("runtime.limits", lambda a: setattr(a.runtime, "limits", object())),
        ("the channel of the approvals", lambda a: setattr(a.approvals, "channel", object())),
        ("a source added", lambda a: a.sources.update(k=object())),
        (
            "a field of the store replaced by a new object",
            lambda a: setattr(a.store, "added_client", object()),
        ),
    ]
    return cases


# fail-before (real run on dd827d79 and on 06ed4b4c, batch 12): it PASSES on both. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_every_replaced_connected_part_reads_unconfirmed(tmp_path: Path) -> None:
    # new feature (fails on old code for the cases the fingerprint did not hold: hooks other than the tools dict, the store of
    # the runtime, the channel, a new Hooks; the cases the old fingerprint held (the app's own fields) are pins)
    for i, (label, change) in enumerate(_each_replaced_part()):
        app = _sealed_app(tmp_path, f"c{i}")
        change(app)
        assert app.mode_banner()["tone"] == "unconfirmed", f"{label}: the banner stayed made-up"


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_source_value_replaced_or_changed_in_place_reads_unconfirmed(tmp_path: Path) -> None:
    # what it shows (a source's own attributes and a replaced entry with a reused id were not seen)
    from types import SimpleNamespace

    app = _built_app(tmp_path / "s")
    source = SimpleNamespace(endpoint=None)
    app.sources["k"] = source
    app._seal(_given())
    assert app.mode_banner()["tone"] == "demo"
    source.client = object()  # a new attribute in place
    assert app.mode_banner()["tone"] == "unconfirmed", "a new attribute of a source was not seen"
    app2 = _built_app(tmp_path / "s2")
    inner = SimpleNamespace(session=object())
    app2.sources["k"] = inner
    app2._seal(_given())
    inner.session = object()  # an attribute value replaced in place
    assert app2.mode_banner()["tone"] == "unconfirmed", (
        "a replaced attribute value of a source was not seen"
    )
    app3 = _built_app(tmp_path / "s3")
    app3.sources["k"] = SimpleNamespace(count=1)
    app3._seal(_given())
    app3.sources["k"].count = 2  # plain data changes during a run: no new part
    assert app3.mode_banner()["tone"] == "demo", "a changing counter read as a new part"


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_the_seal_keeps_a_replaced_part_alive_so_its_number_cannot_be_reused(
    tmp_path: Path,
) -> None:
    # what it keeps: the sealed value holds the REFERENCE of every part and compares with `is`. Whether a freed
    # object's number could be reused cannot be observed, because the seal keeps the original alive: that is what this
    # checks (a weak reference to the sealed object is still alive after the app dropped it and the collector ran). Changing
    # the comparison from `is` to `id()` would be an equivalent mutant while the seal holds the objects, so no row asks for it.
    import gc
    import weakref

    class Part:  # a SimpleNamespace cannot be weakly referenced
        pass

    app = _built_app(tmp_path / "r")
    original = Part()
    watcher = weakref.ref(original)
    app.sources["k"] = original
    app._seal(_given())
    app.sources["k"] = Part()
    del original
    gc.collect()
    assert watcher() is not None, (
        "the seal did not keep the sealed object alive: its number could be reused"
    )
    assert app.mode_banner()["tone"] == "unconfirmed", "a replaced source passed as the old part"


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_tampered_or_stub_app_gives_the_unconfirmed_banner_and_never_raises(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    # what it shows (these raised out of `mode_banner`, and the hand-made state logged a WARNING per call)
    import logging

    tamper = (
        ("runtime is a bare object", lambda a: setattr(a, "runtime", object())),
        ("sources is None", lambda a: setattr(a, "sources", None)),
        ("sources is a list", lambda a: setattr(a, "sources", [1, 2])),
        ("mixed int and str source keys", lambda a: a.sources.update({1: object(), "a": object()})),
        ("hooks.tools is not a mapping", lambda a: setattr(a.runtime.hooks, "tools", 5)),
        ("hooks is None", lambda a: setattr(a.runtime, "hooks", None)),
        ("registry has no tools", lambda a: setattr(a, "registry", SimpleNamespace())),
        ("config is None", lambda a: setattr(a, "config", None)),
    )
    for i, (label, change) in enumerate(tamper):
        app = _sealed_app(tmp_path, f"t{i}")
        change(app)
        with caplog.at_level(logging.DEBUG):
            shown = app.mode_banner()
        assert shown["tone"] == "unconfirmed" and shown["overridden"] == [], f"{label}: {shown!r}"
    from hadavin_sdk.app import App

    # the parts are unchanged (the check says known) but reading what the banner needs still fails: the outer catch-all
    stub = _sealed_app(tmp_path, "t-outer")
    stub.registry = SimpleNamespace()
    monkeypatch.setattr(App, "_known_overrides", lambda self: ())
    shown = stub.mode_banner()
    assert shown["tone"] == "unconfirmed", f"a registry without tools gave {shown!r}"
    monkeypatch.undo()

    built = _built_app(tmp_path / "h")
    by_hand = App(
        **{
            f.name: getattr(built, f.name)
            for f in __import__("dataclasses").fields(built)
            if f.init and f.name != "overridden"
        }
    )
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        by_hand.mode_banner()
        by_hand.mode_banner()
    assert [r for r in caplog.records if r.levelno >= logging.WARNING] == [], (
        "a hand-made app (nothing is wrong with it, it is only not sealed) logged a warning"
    )


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: Regex pattern did not match.
def test_copies_of_a_built_app_which_keep_the_same_parts_stay_known_and_the_others_do_not(
    tmp_path: Path,
) -> None:
    # copy.copy shares every part (known, as documented); dataclasses.replace drops the seal (unconfirmed); copy.deepcopy is
    # refused in words (a built app holds locks, so the standard library could not copy it either: its own error is about a
    # lock; ours says what to do). Nothing here can skip: a copy that fails is the assertion.
    import copy
    import dataclasses

    app = _sealed_app(tmp_path, "cp")
    assert copy.copy(app).mode_banner()["tone"] == "demo", (
        "a shallow copy shares every part with the original: it stays known"
    )
    assert dataclasses.replace(app).mode_banner()["tone"] == "unconfirmed"
    with pytest.raises(TypeError, match="cannot be deep-copied"):
        copy.deepcopy(app)


# fail-before (real run on c7eb5c79, batch 13): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_deep_copy_of_an_app_that_could_be_copied_is_refused_as_well(tmp_path: Path) -> None:
    # what it shows (an app of plain parts was copied, and whether the copy read known depended on how the standard
    # library copies a sentinel object): one rule for every app
    import copy

    from hadavin_sdk.app import App

    plain = App.__new__(App)
    slots = len(
        _sealed_app(tmp_path, "slots")._sealed
    )  # the real number of seal slots, not a guess
    plain.__dict__.update({"overridden": (), "_sealed": ((),) * slots})
    try:
        copy.deepcopy(plain)
    except TypeError as exc:
        assert "cannot be deep-copied" in str(exc), f"the refusal gave another reason: {exc}"
    else:
        raise AssertionError("an app of plain parts was deep-copied")


# fail-before (real run on dd827d79 and on 06ed4b4c, batch 12): it PASSES on both. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_the_recorded_names_cannot_be_laundered(tmp_path: Path) -> None:
    # what it shows (`overridden` was not part of the sealed value and `seal` was public)
    from hadavin_sdk.app import App

    app = _built_app(tmp_path / "l")  # build was given a channel and secrets: not made-up
    assert app.overridden == ("channel", "secrets") and app.mode_banner()["tone"] == "unconfirmed"
    app.overridden = ()
    assert app.mode_banner()["tone"] == "unconfirmed", "app.overridden = () laundered a banner"
    plain = _sealed_app(tmp_path, "l2")  # sealed with no overrides: made-up
    assert plain.mode_banner()["tone"] == "demo"
    plain.overridden = ("llm",)  # the recorded names no longer say what build sealed
    assert plain.mode_banner()["tone"] == "unconfirmed", (
        "a changed list of recorded names was trusted"
    )
    assert not hasattr(App, "seal") and not hasattr(app, "seal"), "the public `seal` is back"


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_normal_production_tick_keeps_its_banner(tmp_path: Path) -> None:
    # no false unconfirmed: the banner of a sealed app that holds a configured source survives two ticks (the source's own
    # attributes are the ones the seal reads: its list of namespaces and its text are plain data)
    from hadavin_sdk.models import now
    from hadavin_sdk.runtime import tick as tick_mod
    from hadavin_sdk.sources.kinds import KINDS
    from hadavin_sdk.sources.kubernetes import KubernetesSource

    app = _built_app(tmp_path / "tk")
    settings = KINDS["kubernetes"].settings(api_url="https://127.0.0.1:6443", namespaces=["a"])
    app.sources["k"] = KubernetesSource(lambda *a, **k: (200, {}), settings)
    app._seal(_given())
    before = app.mode_banner()
    assert before["tone"] == "demo", f"the control banner is {before!r}"
    t0 = now()
    tick_mod.run_tick(app, now=t0)
    tick_mod.run_tick(app, now=t0 + __import__("datetime").timedelta(minutes=11))
    assert app.mode_banner() == before, "the banner changed after two ticks"


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_an_object_first_set_on_a_part_after_build_reads_unconfirmed(tmp_path: Path) -> None:
    # what it keeps: a part that makes a client lazily, after build, reads as changed. That is the safe side
    # (the banner says unconfirmed, never made-up); a part that must do this must create the client in `__init__`.
    app = _built_app(tmp_path / "lz")
    app.sources["k"] = SimpleNamespace(client=None)
    app._seal(_given())
    assert app.mode_banner()["tone"] == "demo"
    app.sources["k"].client = object()
    assert app.mode_banner()["tone"] == "unconfirmed", "a client made after build was not seen"


def test_the_clock_is_an_override_when_given_and_not_when_it_is_the_default(tmp_path: Path) -> None:
    # what it shows (clock was on the not-connectivity list)
    from hadavin_sdk import app as app_mod

    assert "clock" in mb.OVERRIDES and "clock" not in mb.NOT_CONNECTIVITY
    assert app_mod._given_overrides(clock=lambda: None) == ("clock",)
    assert app_mod._given_overrides(clock=None) == ()
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.approvals.channel import FakeChannel
    from hadavin_sdk.models import now
    from hadavin_sdk.registry import load_registry
    from tests.conftest import qualify

    cfg_dir = make_cfg(tmp_path)
    qualify(load_registry(load_config(cfg_dir)))
    given = {"channel": FakeChannel(), "secrets": FakeSecretProvider({"fixture-token": "t" * 8})}
    with_clock = app_mod.build(cfg_dir, ["test-agent"], clock=lambda: now(), **given)
    assert "clock" in with_clock.overridden, "build did not record a clock that was handed in"
    default = app_mod.build(cfg_dir, ["test-agent"], **given)
    assert "clock" not in default.overridden, "build recorded the default clock as an override"


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: assert {'config_dir'...nly compared'} == {'config_dir'... at run time'}
def test_the_not_connectivity_reasons_say_what_was_checked() -> None:
    # what it shows (the reasons were plain claims): the full text of each reason, so a reason cannot be swapped for a bare
    # claim, and a new parameter on the list needs its own reason written here
    assert mb.NOT_CONNECTIVITY == {
        "config_dir": "a folder that `load_config` reads; the config is what the banner reads; checked: used only there in `build`",
        "agents": "a list of agent names that `Runtime` checks against the registry; checked: no callable or object is handed in",
        "timeout_s": "a number of seconds handed to the executor (`Executor(timeout_s=...)`, as its network timeout); the executor reads it only as a timeout; it is typed as a number in the signature of `build` and not checked at run time",
    }


def test_banner_for_has_no_default_for_overridden() -> None:
    # what it shows (`overridden` defaulted to `()`)
    with pytest.raises(TypeError, match="overridden"):
        cast("Any", mb._banner_for)("demo", real_services=[], stand_ins=[])
        raise AssertionError("_banner_for without overridden was accepted")


def test_banner_or_unconfirmed_with_none_logs_no_warning(caplog: pytest.LogCaptureFixture) -> None:
    # what it shows (the not-known answer was raised and caught, with a WARNING per call)
    import logging

    with caplog.at_level(logging.DEBUG):
        shown = mb.banner_or_unconfirmed(_demo_config(), tool_specs={}, overridden=None)
    assert shown["tone"] == "unconfirmed"
    warned = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    assert warned == [], f"the not-known answer logged a warning: {warned}"


@needs_node
def test_the_page_refuses_a_demo_or_quiet_banner_that_lists_overridden_parts_and_any_list_that_is_not_in_the_python_order() -> (
    None
):
    # what it shows (tone demo with a non-empty list was painted; duplicates and any order were accepted)
    for tone_banner in (
        GOOD_DEMO,
        {
            **GOOD_DEMO,
            "mode": "pilot",
            "tone": "quiet",
            "tag": "PILOT",
            "text": "No real service is connected.",
            "standins": "",
        },
    ):
        for names in (["llm"], ["tools", "llm"], list(mb.OVERRIDES)):
            _unconfirmed(
                _paint({**tone_banner, "overridden": names}),
                f"painted {tone_banner['tone']} with {names!r}",
            )
    base = mb.banner_from_config(
        _demo_config(), tool_specs={}, overridden=("tools", "llm")
    ).as_dict()
    assert (
        _paint(base)["shownTone"] == "unconfirmed"
        and "tools, llm" in _paint(base)["lines"][1]["text"]
    )
    for bad in (["llm", "tools"], ["tools", "tools"], ["llm", "llm"], ["clock", "tools"]):
        _unconfirmed(_paint({**base, "overridden": bad}), f"painted overridden={bad!r}")


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: the names of the overrides were not shown: [{'cls': 'mode-banner__tag', 'text': 'UNCONFIRMED'}, {'cls': 'mode-banner__te
@needs_node
def test_a_reworded_not_confirmed_text_is_painted_by_the_page_as_its_english_fallback_with_the_names() -> (
    None
):
    # what it shows (the page painted the plain fallback, so the names of `overridden` were lost although the
    # docstring said they were shown): a banner reworded through `words.not_confirmed` keeps its names on the page
    words = mb.BannerWords(
        tag_by_mode={"demo": "D", "pilot": "P", "prod": "L"},
        not_confirmed="Another sentence, not the default.",
    )
    shown = mb.banner_from_config(
        _demo_config(), tool_specs={}, overridden=("tools", "llm"), words=words
    ).as_dict()
    assert shown["text"] == "Another sentence, not the default." and shown["overridden"] == [
        "tools",
        "llm",
    ]
    seen = _paint(shown)
    assert seen["shownTone"] == "unconfirmed" and seen["threw"] == ""
    assert seen["mode"] == "", f"the mode of the reworded banner was painted: {seen['mode']!r}"
    assert seen["lines"][0]["text"] == mb.not_confirmed()["tag"], f"painted {seen['lines']!r}"
    assert seen["lines"][1]["text"] == (
        " "
        + mb.not_confirmed()["text"]
        + " "
        + mb.DEFAULT_WORDS.overridden_note.format(names="tools, llm")
    ), f"the names of the overrides were not shown: {seen['lines']!r}"
    assert "Another sentence" not in str(seen["lines"]), "the reworded sentence was painted"


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
@needs_node
def test_pin_an_unconfirmed_banner_that_also_lists_real_services_or_a_second_line_is_the_plain_fallback() -> (
    None
):
    # the killer of row J1b
    for extra in ({"standins": "made-up: crm"}, {"real": ["crm"]}):
        seen = _paint({**mb.not_confirmed(), "mode": "demo", **extra})
        assert seen["shownTone"] == "unconfirmed" and seen["threw"] == ""
        assert len(seen["lines"]) == 2, (
            f"an unconfirmed banner with {extra} painted {seen['lines']!r}"
        )
        assert seen["lines"][1]["text"] == " " + mb.not_confirmed()["text"], (
            f"an unconfirmed banner with {extra} painted the words {seen['lines'][1]['text']!r}"
        )


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
@needs_node
def test_pin_a_forged_tag_on_an_unconfirmed_banner_is_painted_as_the_pages_own_tag() -> None:
    # what it shows (the tag as given was painted): the tag of an unconfirmed banner is the page's own word
    forged = dict(mb.not_confirmed())
    forged["tag"] = "ALL CLEAR"
    forged["mode"] = (
        "demo"  # a mode the page knows: an empty mode is refused before the tag is looked at
    )
    seen = _paint(forged)
    assert seen["shownTone"] == "unconfirmed" and seen["threw"] == ""
    assert seen["lines"][0]["text"] == mb.not_confirmed()["tag"], f"painted {seen['lines']!r}"


def test_the_guard_and_the_banner_modules_say_what_they_compare_in_their_docstrings() -> None:
    # the unconfirmed words rule is in the docstring of `_banner_for` (a reader looks there)
    doc = " ".join((mb._banner_for.__doc__ or "").split())
    assert (
        "exactly `words.not_confirmed`" in doc.replace("EXACTLY", "exactly")
        and "English fallback" in doc
    )


def test_the_overrides_are_exactly_the_objects_and_callables_handed_to_build() -> None:
    # new feature, explicit list (fails on old code: hold_run_ids and clock were not overrides)
    assert mb.OVERRIDES == (
        "tools",
        "sources",
        "channel",
        "llm",
        "detector",
        "secrets",
        "hold_run_ids",
        "clock",
    ), f"the override list is {mb.OVERRIDES!r}"


def test_the_not_connectivity_list_is_exactly_the_parameters_that_hand_in_no_object() -> None:
    # new feature, explicit list (fails on old code: clock was on it and there was no such list before)
    assert set(mb.NOT_CONNECTIVITY) == {"config_dir", "agents", "timeout_s"}, (
        f"the not-connectivity list is {sorted(mb.NOT_CONNECTIVITY)!r}"
    )


# -- batch 10 (r9 fixes): the seal reads what the banner reads, the page and the logs --------------------------------------
def _tool_spec(name: str = "lookup", hosts: tuple[str, ...] = ("api.example.com",)) -> ToolSpec:
    return ToolSpec(
        name=name,
        function="mod:fn",
        description="d",
        input_schema={},
        side_effect="none",
        hosts=hosts,
    )


def _sealed_with(tmp_path: Path, name: str, change) -> object:
    """A built app that `change` prepared (it adds something the banner reads), sealed with no overrides."""
    app = _built_app(tmp_path / name)
    change(app)
    app._seal(_given())
    return app


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: a deleted tool spec left a made-up banner
def test_a_tool_spec_deleted_after_build_reads_unconfirmed(tmp_path: Path) -> None:
    # what it shows (the manifests are a mutable dict inside a frozen record, so a deleted real host was not seen
    # and the banner said made-up while the toolbox could still reach the host)
    app = _sealed_with(
        tmp_path, "d1", lambda a: a.registry.tools.update({"agent": {"lookup": _tool_spec()}})
    )
    assert app.mode_banner()["tone"] == "real", "the control: a real host is named"
    del app.registry.tools["agent"]["lookup"]
    assert app.mode_banner()["tone"] == "unconfirmed", "a deleted tool spec left a made-up banner"


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: a deleted tool spec was not seen
def test_a_tool_spec_without_a_host_deleted_after_build_reads_unconfirmed(tmp_path: Path) -> None:
    # what it shows: a deletion that leaves the lists of services equal is caught by the entries, not the lists
    app = _sealed_with(
        tmp_path, "d2", lambda a: a.registry.tools.update({"agent": {"q": _tool_spec("q", ())}})
    )
    assert app.mode_banner()["tone"] == "demo"
    del app.registry.tools["agent"]["q"]
    assert app.mode_banner()["tone"] == "unconfirmed", "a deleted tool spec was not seen"


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: a host added after build left a made-up banner
def test_the_address_of_a_system_changed_after_build_reads_unconfirmed(tmp_path: Path) -> None:
    # what it shows (a field of a system of the config is not read as a part): only the lists of services the
    # banner reads change here (no entry of a container is replaced), so this is the case of the services check
    app = _built_app(tmp_path / "d3")
    app._seal(_given())
    assert app.mode_banner()["tone"] == "demo"
    system = next(iter(app.config.systems.values()))
    object.__setattr__(
        system, "base_url", "https://api.example.com"
    )  # the record is frozen: this is a forced change
    assert app.mode_banner()["tone"] == "unconfirmed", (
        "a host added after build left a made-up banner"
    )


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: cleared sources left a made-up banner
def test_config_sources_cleared_after_build_reads_unconfirmed(tmp_path: Path) -> None:
    # what it shows (`Config.sources` is a dict inside a frozen record; clearing it removed a real source)
    app = _sealed_with(
        tmp_path,
        "d4",
        lambda a: a.config.sources.update({"s": SimpleNamespace(kind="unknown-kind", settings={})}),
    )
    assert app.mode_banner()["tone"] == "real", "the control: an unknown source reads as real"
    app.config.sources.clear()
    assert app.mode_banner()["tone"] == "unconfirmed", "cleared sources left a made-up banner"


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: a replaced config source was not seen
def test_a_config_source_replaced_after_build_reads_unconfirmed(tmp_path: Path) -> None:
    # what it shows: the lists of services stay equal here (both sources read as real), so only the entries show it
    app = _sealed_with(
        tmp_path,
        "d5",
        lambda a: a.config.sources.update({"s": SimpleNamespace(kind="unknown-kind", settings={})}),
    )
    assert app.mode_banner()["tone"] == "real"
    app.config.sources["s"] = SimpleNamespace(kind="other-unknown-kind", settings={})
    assert app.mode_banner()["tone"] == "unconfirmed", "a replaced config source was not seen"


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: a function replaced: the banner stayed made-up
def test_a_toolbox_function_or_spec_swapped_after_build_reads_unconfirmed(tmp_path: Path) -> None:
    # what it shows (the toolbox's dicts of specs and callables were plain data)
    def add(a) -> None:
        a.runtime.hooks.toolbox = SimpleNamespace(
            specs={"lookup": _tool_spec("lookup", ())}, _fns={"lookup": lambda: None}
        )

    for i, (label, change) in enumerate(
        (
            ("a function replaced", lambda box: box._fns.update({"lookup": lambda: "other"})),
            ("a function added", lambda box: box._fns.update({"extra": lambda: None})),
            ("a spec added", lambda box: box.specs.update({"extra": _tool_spec("extra", ())})),
            ("a spec removed", lambda box: box.specs.clear()),
        )
    ):
        app = _sealed_with(tmp_path, f"tb{i}", add)
        assert app.mode_banner()["tone"] == "demo", f"{label}: the control"
        change(app.runtime.hooks.toolbox)
        assert app.mode_banner()["tone"] == "unconfirmed", f"{label}: the banner stayed made-up"


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: a replaced contract was not seen
def test_an_action_contract_replaced_or_added_after_build_reads_unconfirmed(tmp_path: Path) -> None:
    # what it shows (the contracts, which name the system an action is sent to, were plain data)
    import copy

    app = _sealed_app(tmp_path, "ct1")
    name = next(iter(app.registry.contracts))
    app.registry.contracts[name] = copy.copy(app.registry.contracts[name])
    assert app.mode_banner()["tone"] == "unconfirmed", "a replaced contract was not seen"
    app2 = _sealed_app(tmp_path, "ct2")
    app2.registry.contracts["extra"] = app2.registry.contracts[name]
    assert app2.mode_banner()["tone"] == "unconfirmed", "an added contract was not seen"


def _warnings(caplog: pytest.LogCaptureFixture) -> list:
    import logging

    return [r for r in caplog.records if r.levelno >= logging.WARNING]


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: the banner error was logged below warning level: ['DEBUG', 'DEBUG']
def test_a_banner_error_is_logged_once_at_warning_level_with_the_exception_type(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    # what it shows (an AttributeError, as a typo in the code would raise, made every app
    # unconfirmed with one debug line; the same banner error is logged once, at warning level, with
    # its type and never its message)
    import logging

    from hadavin_sdk import app as app_mod
    from hadavin_sdk.app import App

    monkeypatch.setattr(app_mod, "_WARNED", set(), raising=False)

    def boom(self) -> tuple:
        raise AttributeError("a typo")

    app = _built_app(tmp_path / "w1")
    monkeypatch.setattr(App, "_connected_parts", boom)
    with caplog.at_level(logging.DEBUG):
        first = app.mode_banner()
        app.mode_banner()
    assert first["tone"] == "unconfirmed"
    logged = [r for r in caplog.records if r.getMessage().startswith("mode banner:")]
    assert logged, "the error that stopped the banner was not logged at all"
    assert all(r.levelno == logging.WARNING for r in logged), (
        f"the banner error was logged below warning level: {[r.levelname for r in logged]}"
    )
    assert len(logged) == 1, f"the same banner error was logged {len(logged)} times, not once"
    seen = logged
    assert "AttributeError" in seen[0].getMessage(), (
        "the type of the error was not named in the log line"
    )
    assert "a typo" not in seen[0].getMessage(), "the message of the error was logged"


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: the outer catch-all did not warn: ['mode banner: the app could not be read']
def test_an_error_in_the_services_or_in_the_banner_is_logged_at_warning_level_too(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    # what it shows (both catch-alls logged at debug level)
    import logging

    from hadavin_sdk import app as app_mod
    from hadavin_sdk.app import App

    monkeypatch.setattr(app_mod, "_WARNED", set(), raising=False)
    stub = _sealed_app(tmp_path, "w2")
    stub.registry = SimpleNamespace()
    monkeypatch.setattr(App, "_known_overrides", lambda self: ())
    with caplog.at_level(logging.DEBUG):
        assert stub.mode_banner()["tone"] == "unconfirmed"
    assert any("AttributeError" in r.getMessage() for r in _warnings(caplog)), (
        f"the outer catch-all did not warn: {[r.getMessage() for r in caplog.records]}"
    )
    monkeypatch.undo()
    monkeypatch.setattr(app_mod, "_WARNED", set(), raising=False)
    app = _sealed_app(tmp_path, "w3")
    monkeypatch.setattr(App, "_banner_services", lambda self: (_ for _ in ()).throw(KeyError("x")))
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        assert app.mode_banner()["tone"] == "unconfirmed"
    assert any("KeyError" in r.getMessage() for r in _warnings(caplog)), (
        f"an error in the services did not warn: {[r.getMessage() for r in caplog.records]}"
    )


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: painted demo with overridden missing
@needs_node
def test_a_banner_without_overridden_is_not_painted_as_demo_or_quiet_by_the_page() -> None:
    # what it shows (the page read a missing or null `overridden` as "none" and painted made-up or quiet)
    for tone_banner in (
        {
            "mode": "demo",
            "tone": "demo",
            "tag": "DEMO",
            "text": "t",
            "standins": "s",
            "real": [],
            "stand_ins": ["a"],
        },
        {
            "mode": "pilot",
            "tone": "quiet",
            "tag": "PILOT",
            "text": "None.",
            "standins": "",
            "real": [],
            "stand_ins": [],
        },
    ):
        for label, extra in (("missing", {}), ("null", {"overridden": None})):
            seen = _paint({**tone_banner, **extra})
            _unconfirmed(seen, f"painted {tone_banner['tone']} with overridden {label}")
        assert _paint({**tone_banner, "overridden": []})["shownTone"] == tone_banner["tone"], (
            "the control: an empty list is none handed in"
        )


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: the page painted demo with overridden missing
@needs_node
def test_the_page_and_python_both_read_a_null_overridden_as_unknown_for_demo_and_quiet() -> None:
    # Python: None is "not known" and the banner is the unconfirmed one (banner_or_unconfirmed; banner_from_config raises);
    # a MISSING answer is a TypeError at the call (the keyword is required). The page refuses made-up and quiet when the
    # list is missing or null. For a real or unconfirmed banner the page reads a missing list as empty, which is the safe
    # direction and is not tested here.
    shown = mb.banner_or_unconfirmed(_demo_config(), tool_specs={}, overridden=None)
    assert shown["tone"] == "unconfirmed", f"Python read overridden=None as {shown['tone']}"
    with refused(TypeError, "banner_or_unconfirmed without overridden", match="overridden"):
        cast("Any", mb.banner_or_unconfirmed)(_demo_config(), tool_specs={})
    with refused(ValueError, "banner_from_config with overridden=None", match="not known"):
        mb.banner_from_config(_demo_config(), tool_specs={}, overridden=None)
    # the page script, in node, on the same two answers (missing and null) for the two tones that claim "nothing real"
    for tone_mode in ("demo", "pilot"):
        tone = "demo" if tone_mode == "demo" else "quiet"
        base = {**GOOD_DEMO, "mode": tone_mode, "tone": tone}
        assert _paint(base)["shownTone"] == tone, (
            f"the control: {tone} was not painted with overridden []"
        )
        for label, banner in (
            ("missing", {k: v for k, v in base.items() if k != "overridden"}),
            ("null", {**base, "overridden": None}),
        ):
            seen = _paint(banner)
            assert seen["shownTone"] == "unconfirmed", (
                f"the page painted {tone} with overridden {label}"
            )


# -- batch 11 (r10 fixes) ----------------------------------------------------------------------------------------------------
def _with_real_toolbox(app) -> None:
    """Put a REAL `ToolBox` (not a stand-in) and a manifest entry into a built app, as a tooled deployment has."""
    from hadavin_sdk import tools as tools_mod

    spec = _tool_spec("lookup", ())
    app.registry.tools["test-agent"] = {"lookup": spec}
    app.runtime.hooks.toolbox = tools_mod.ToolBox(
        {"lookup": spec}, {"lookup": lambda: "x"}, timeout_s=1.0
    )
    app.config.sources["src1"] = SimpleNamespace(kind="made-up")


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: config.systems['fixture-records'] is not among the connected parts
def test_a_real_built_app_lists_every_named_container_entry_in_its_connected_parts(
    tmp_path: Path,
) -> None:
    # what it keeps: the labels on a REAL registry, config and toolbox
    # (the earlier tests used stand-ins), so a renamed field shows here. The per-container proofs are the tests that replace one
    # entry and expect the unconfirmed banner.
    app = _built_app(tmp_path / "labels")
    _with_real_toolbox(app)
    labels = {label for label, _ in app._connected_parts()}
    for wanted in (
        "config.systems['fixture-records']",
        "config.sources['src1']",
        "registry.agents['test-agent']",
        "registry.principals['svc:test-agent']",
        "registry.chains['chain-abc']",
        "registry.contracts['lookup_record']",
        "registry.tools['test-agent']['lookup']",
        "toolbox.specs['lookup']",
        "toolbox._fns['lookup']",
    ):
        assert wanted in labels, f"{wanted} is not among the connected parts"


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: config.systems was missing and the parts were read all the same
def test_a_named_container_that_is_missing_stops_the_reading_and_names_it(tmp_path: Path) -> None:
    # what it shows (a container that was not a mapping was skipped without a word)
    cases = (
        ("config", "systems"),
        ("config", "sources"),
        ("registry", "agents"),
        ("registry", "principals"),
        ("registry", "chains"),
        ("registry", "contracts"),
        ("registry", "tools"),
    )
    for i, (owner, name) in enumerate(cases):
        app = _built_app(tmp_path / f"miss{i}")
        object.__setattr__(getattr(app, owner), name, None)
        try:
            app._connected_parts()
        except TypeError as exc:
            assert f"{owner}.{name}" in str(exc), f"the error does not name the container: {exc}"
        else:
            raise AssertionError(f"{owner}.{name} was missing and the parts were read all the same")
    app = _built_app(tmp_path / "miss-box")
    _with_real_toolbox(app)
    del app.runtime.hooks.toolbox.__dict__["_fns"]
    try:
        app._connected_parts()
    except TypeError as exc:
        assert "toolbox._fns" in str(exc), f"the error does not name the container: {exc}"
    else:
        raise AssertionError("a toolbox without its functions was read all the same")


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: assert 'demo' == 'unconfirmed'
def test_an_app_sealed_while_a_container_is_missing_reads_unconfirmed_and_build_goes_on(
    tmp_path: Path,
) -> None:
    # what it shows (the seal raised, so a build with such an app would have stopped)
    app = _built_app(tmp_path / "miss-seal")
    object.__setattr__(app.registry, "contracts", None)
    try:
        app._seal(_given())
    except TypeError as exc:
        raise AssertionError(f"the seal stopped on a missing container: {exc}") from None
    assert app.mode_banner()["tone"] == "unconfirmed"


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: () was accepted as the names of the overrides
def test_a_plain_tuple_cannot_seal_an_app_and_a_sealed_app_cannot_be_given_a_new_answer(
    tmp_path: Path,
) -> None:
    # what it shows (`_seal(())` was accepted again and restored the made-up banner of a tampered app)
    app = _sealed_app(tmp_path, "launder")
    app.sources["k"] = object()  # a part added after build
    assert app.mode_banner()["tone"] == "unconfirmed"
    for plain in ((), [], ("tools",), None):
        try:
            app._seal(plain)
        except TypeError:
            pass
        else:
            raise AssertionError(f"{plain!r} was accepted as the names of the overrides")
    assert app.mode_banner()["tone"] == "unconfirmed", (
        "a stray call restored the banner of a tampered app"
    )


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: assert 'demo' == 'unconfirmed'
def test_a_hand_made_app_is_unconfirmed_even_after_a_stray_seal_call(tmp_path: Path) -> None:
    # what it shows (`_seal(())` on a hand-made app gave it the made-up banner)
    import dataclasses

    from hadavin_sdk.app import App

    built = _built_app(tmp_path / "hm")
    by_hand = App(
        **{
            f.name: getattr(built, f.name)
            for f in dataclasses.fields(built)
            if f.init and f.name != "overridden"
        }
    )
    try:
        by_hand._seal(())
    except TypeError:
        pass
    assert by_hand.mode_banner()["tone"] == "unconfirmed"


def _live_app(live_cfg_dir: Path, fake_system):
    from hadavin_sdk import evals
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.app import build
    from hadavin_sdk.llm import FakeLLM
    from hadavin_sdk.registry import load_registry

    cfg = load_config(live_cfg_dir)
    assert evals.gate(
        load_registry(cfg), FakeLLM(cfg.backends.llm.recorded_dir, cfg.routes), "test-agent"
    ).green
    app = build(
        live_cfg_dir,
        ["test-agent"],
        secrets=FakeSecretProvider({"fixture-token": fake_system.token}),
        timeout_s=0.5,
    )
    app._seal(
        _given()
    )  # as if build had been given nothing: the banner is not the unconfirmed one while the app is untouched
    return app


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_the_banner_of_a_real_app_is_the_same_after_an_agent_run(tmp_path: Path) -> None:
    # the fake system is started here, not by a fixture of conftest.py: the mutation runner runs without conftest files
    import secrets

    from tests.fixtures.fake_system import FakeSystem

    fake_system = FakeSystem(token=secrets.token_hex(16)).start()
    try:
        _the_banner_of_a_real_app_after_an_agent_run(
            make_cfg(tmp_path, port=fake_system.port), fake_system
        )
    finally:
        fake_system.stop()


def _the_banner_of_a_real_app_after_an_agent_run(live_cfg_dir: Path, fake_system) -> None:
    # A real built app runs one agent turn on fakes (documents, store, audit, approvals all write during the run): nothing
    # that fills during a run may read as a changed connected part. (The earlier tick test had no agent run.)
    app = _live_app(live_cfg_dir, fake_system)
    before = app.mode_banner()
    assert before["tone"] != "unconfirmed", f"the control banner is {before!r}"
    doc = (app.config.inputs_dir / "create.txt").read_bytes()
    app.runtime.handle("test-agent", "svc:test-agent", doc)
    after = app.mode_banner()
    assert after == before, (
        f"the banner changed after an agent run: {before['tone']} -> {after['tone']}"
    )


def _view(cfg, **over):
    """The config with some fields replaced (a stand-in that reads through to the real one)."""

    class View:
        def __getattr__(self, name: str):
            return over[name] if name in over else getattr(cfg, name)

    return View()


def _unreadable_shapes() -> dict:
    """Three shapes of config or manifest that the banner cannot read, each as a replacement for `_services_in`."""
    real = mb._services_in
    return {
        "a tool spec without hosts": lambda cfg, tools: real(cfg, {"a": {"t": SimpleNamespace()}}),
        "a backend entry without a kind": lambda cfg, tools: real(
            _view(cfg, backends=SimpleNamespace(entries=lambda: [("store", SimpleNamespace())])),
            tools,
        ),
        "egress hosts that are an iterator": lambda cfg, tools: real(
            _view(cfg, egress_hosts=iter(())), tools
        ),
    }


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: a tool spec without hosts: nothing was logged at warning level
def test_a_config_the_banner_cannot_read_does_not_stop_build_and_reads_unconfirmed(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    # what it shows (`build` raised the banner's TypeError or ValueError)
    import logging

    from hadavin_sdk import app as app_mod
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.approvals.channel import FakeChannel
    from hadavin_sdk.registry import load_registry
    from tests.conftest import qualify

    for i, (label, shape) in enumerate(_unreadable_shapes().items()):
        monkeypatch.setattr(app_mod, "_services_in", shape, raising=False)
        monkeypatch.setattr(app_mod, "_WARNED", set(), raising=False)
        cfg_dir = make_cfg(tmp_path / f"shape{i}")
        qualify(load_registry(load_config(cfg_dir)))
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            try:
                app = app_mod.build(
                    cfg_dir,
                    ["test-agent"],
                    channel=FakeChannel(),
                    secrets=FakeSecretProvider({"fixture-token": "t" * 8}),
                )
            except (TypeError, ValueError) as exc:
                raise AssertionError(f"{label}: build stopped on it: {exc}") from None
        assert app.mode_banner()["tone"] == "unconfirmed", (
            f"{label}: the banner was not the unconfirmed one"
        )
        logged = [
            r
            for r in caplog.records
            if r.levelno >= logging.WARNING and "mode banner" in r.getMessage()
        ]
        assert len(logged) >= 1, f"{label}: nothing was logged at warning level"


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_deep_copy_of_a_built_app_raises_on_the_old_code_too(tmp_path: Path) -> None:
    # what it keeps: where the deep copy of a built app already raised a TypeError (the app holds a lock that
    # cannot be copied); the refusal in words only makes the reason clear
    import copy

    app = _built_app(tmp_path / "dc")
    try:
        copy.deepcopy(app)
    except TypeError:
        pass
    else:
        raise AssertionError("a built app was deep-copied")


def _entry_change_is_seen(tmp_path: Path, name: str, change) -> str:
    app = _sealed_app(tmp_path, name)
    change(app)
    return app.mode_banner()["tone"]


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: a replaced agent was not seen
def test_a_replaced_agent_entry_after_build_reads_unconfirmed(tmp_path: Path) -> None:
    # killer of the row that drops the agents from the seal
    import copy

    def change(a) -> None:
        a.registry.agents["test-agent"] = copy.copy(a.registry.agents["test-agent"])

    assert _entry_change_is_seen(tmp_path, "ag", change) == "unconfirmed", (
        "a replaced agent was not seen"
    )


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: a replaced principal was not seen
def test_a_replaced_principal_entry_after_build_reads_unconfirmed(tmp_path: Path) -> None:
    import copy

    def change(a) -> None:
        a.registry.principals["user:a"] = copy.copy(a.registry.principals["user:a"])

    assert _entry_change_is_seen(tmp_path, "pr", change) == "unconfirmed", (
        "a replaced principal was not seen"
    )


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: a replaced chain was not seen
def test_a_replaced_chain_entry_after_build_reads_unconfirmed(tmp_path: Path) -> None:
    import copy

    def change(a) -> None:
        a.registry.chains["chain-abc"] = copy.copy(a.registry.chains["chain-abc"])

    assert _entry_change_is_seen(tmp_path, "ch", change) == "unconfirmed", (
        "a replaced chain was not seen"
    )


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: a replaced system was not seen
def test_a_replaced_system_entry_after_build_reads_unconfirmed(tmp_path: Path) -> None:
    import copy

    def change(a) -> None:
        a.config.systems["fixture-records"] = copy.copy(a.config.systems["fixture-records"])

    assert _entry_change_is_seen(tmp_path, "sy", change) == "unconfirmed", (
        "a replaced system was not seen"
    )


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: a replaced manifest of an agent was not seen
def test_a_replaced_tool_manifest_of_an_agent_after_build_reads_unconfirmed(tmp_path: Path) -> None:
    def prepare(a) -> None:
        a.registry.tools["test-agent"] = {"lookup": _tool_spec("lookup", ())}

    app = _sealed_with(tmp_path, "tm", prepare)
    assert app.mode_banner()["tone"] == "demo", "the control"
    app.registry.tools["test-agent"] = dict(
        app.registry.tools["test-agent"]
    )  # the same specs in a new dict
    assert app.mode_banner()["tone"] == "unconfirmed", (
        "a replaced manifest of an agent was not seen"
    )


# -- batch 12 (r11 fixes) ----------------------------------------------------------------------------------------------------
# fail-before (real run on dd827d79 and on 06ed4b4c, batch 12): it FAILS on both, first failing line: a stage changed after build (demo to pilot) was read as 'quiet'
def test_a_stage_changed_after_build_reads_unconfirmed(tmp_path: Path) -> None:
    # The stage text `config.environment` decides the mode and the tag of the banner. A forced change of it (the config is
    # read-only for normal code, so this goes round it with `object.__setattr__`) must not keep the made-up banner.
    for later in (s for s in STAGES if s != "demo"):
        app = _sealed_app(tmp_path, f"changed-{later}")
        object.__setattr__(app.config, "environment", later)
        tone = app.mode_banner()["tone"]
        assert tone == "unconfirmed", (
            f"a stage changed after build (demo to {later}) was read as {tone!r}"
        )


# fail-before (real run on c7eb5c79, batch 13): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_stage_that_is_not_text_is_an_error_that_names_it(tmp_path: Path) -> None:
    app = _sealed_app(tmp_path, "nostage")
    for value in (None, 5, b"demo", ["demo"]):
        object.__setattr__(app.config, "environment", value)
        with refused(TypeError, f"a stage of {value!r}", match="no stage text"):
            app._stage()
        tone = app.mode_banner()["tone"]
        assert tone == "unconfirmed", f"a stage of {value!r} read as {tone!r}"


# fail-before (real run, batch 12): it FAILS on dd827d79 (a toolbox without an attribute dictionary was not refused) and PASSES on 06ed4b4c, which already refuses; it is the killer of row R12C1, shown by the row run
def test_a_toolbox_without_an_attribute_dictionary_is_an_error_that_names_it(
    tmp_path: Path,
) -> None:
    class Slotted:
        __slots__ = ()

    app = _sealed_app(tmp_path, "slotted")
    app.runtime.hooks.toolbox = Slotted()
    with refused(
        TypeError, "a toolbox without an attribute dictionary", match="no attribute dictionary"
    ):
        app._connected_parts()
    assert app.mode_banner()["tone"] == "unconfirmed", "that toolbox left a made-up banner"


# fail-before (real run, batch 12): it FAILS on dd827d79 (a per-agent tool entry that is a list was not refused) and PASSES on 06ed4b4c, which already refuses; it is the killer of row R12C2, shown by the row run
def test_a_per_agent_tool_entry_that_is_not_a_mapping_is_an_error_that_names_it(
    tmp_path: Path,
) -> None:
    app = _sealed_app(tmp_path, "peragent")
    app.registry.tools["test-agent"] = ["lookup"]
    with refused(TypeError, "a per-agent tool entry that is a list", match=r"registry\.tools\["):
        app._connected_parts()
    assert app.mode_banner()["tone"] == "unconfirmed", "that entry left a made-up banner"


# fail-before (real run on dd827d79 and on 06ed4b4c, batch 12): it PASSES on both. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_the_demo_stage_is_one_of_the_stages() -> None:
    # replaces the import-time check (a branch that could not run): a stage rename that leaves "demo" out fails here
    assert mb._DEMO_STAGE in STAGES, f"the demo stage {mb._DEMO_STAGE!r} is not in {STAGES}"


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: module 'hadavin_sdk.app' has no attribute '_UNREADABLE'
def test_each_unreadable_shape_seals_as_unreadable_and_reads_unconfirmed_with_nothing_handed_in(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The same three shapes, sealed with `_given()` (no override handed in), so the made-up banner is what an app that CAN be
    # read gives (the control) and "unconfirmed" can only come from the unreadable seal, not from a recorded override.
    from hadavin_sdk import app as app_mod

    # Older heads read the services in `mode_banner` only, so the shape is put in both places;
    # `_UNREADABLE` is looked up by
    # name with a default, so a head without it fails on what it stored, not on a missing name.
    unreadable = getattr(app_mod, "_UNREADABLE", None)
    for i, (label, shape) in enumerate(_unreadable_shapes().items()):
        app = _built_app(tmp_path / f"seal{i}")
        app._seal(_given())
        assert app.mode_banner()["tone"] == "demo", (
            f"{label}: the control (a readable app) lost its banner"
        )
        with monkeypatch.context() as patch:
            patch.setattr(mb, "_services_in", shape)
            patch.setattr(app_mod, "_services_in", shape, raising=False)
            app._seal(_given())
            sealed = app._sealed
            tone = app.mode_banner()["tone"]
        assert tone == "unconfirmed", f"{label}: an unreadable app read as {tone!r}"
        assert unreadable is not None and sealed == unreadable, (
            f"{label}: the app was not sealed as unreadable (it was sealed with {type(sealed).__name__})"
        )


class _Surprise(Exception):
    """An error type that no tuple of the banner or of the app names: it stands for a bug in the code."""


def _raise_surprise(*_a, **_k):
    raise _Surprise("a bug")


def _reading_the_parts(app, monkeypatch, boom):
    from hadavin_sdk.app import App

    monkeypatch.setattr(App, "_connected_parts", boom)
    return app.mode_banner


def _building_the_banner(app, monkeypatch, boom):
    monkeypatch.setattr(mb, "banner_from_config", boom)
    return app.mode_banner


def _the_outer_catch_of_the_app(app, monkeypatch, boom):
    from hadavin_sdk import app as app_mod

    monkeypatch.setattr(app_mod, "banner_or_unconfirmed", boom)
    return app.mode_banner


def _banner_or_unconfirmed_itself(app, monkeypatch, boom):
    monkeypatch.setattr(mb, "banner_from_config", boom)
    return lambda: mb.banner_or_unconfirmed(
        app.config, None, mb.DEFAULT_WORDS, tool_specs=app.registry.tools, overridden=()
    )


def _the_words_of_the_banner(app, monkeypatch, boom):
    class Words:
        @property
        def not_confirmed_tag(self):
            boom()

    return lambda: mb.not_confirmed_banner(Words())


def _sealing_the_app(app, monkeypatch, boom):
    from hadavin_sdk.app import App

    monkeypatch.setattr(App, "_connected_parts", boom)
    return lambda: app._seal(_given())


SURPRISE_SITES = {
    "App._known_overrides (reads the parts)": _reading_the_parts,
    "App.mode_banner (the outer catch)": _the_outer_catch_of_the_app,
    "banner_or_unconfirmed": _banner_or_unconfirmed_itself,
    "_not_confirmed_that_cannot_fail (the words)": _the_words_of_the_banner,
    "App._seal (reads the app at build)": _sealing_the_app,
}


def _a_bug_is_not_turned_into_a_banner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, site: str
) -> None:
    app = _sealed_app(tmp_path, "s1")
    call = SURPRISE_SITES[site](app, monkeypatch, _raise_surprise)
    try:
        call()
    except _Surprise:
        return  # no banner is returned at all: not a made-up one, not a quiet one, not even an unconfirmed one
    raise AssertionError(f"{site}: a bug of an unnamed type was turned into a banner")


# fail-before: on c7eb5c79 and dd827d79 each of these sites caught `Exception`, so the bug was
# swallowed
# fail-before (real run on c7eb5c79, batch 13): it FAILS there, first failing line: AssertionError: App._known_overrides (reads the parts): a bug of an unnamed type was turned into a banner
def test_a_bug_in_reading_the_parts_of_the_app_is_not_turned_into_a_banner(
    tmp_path, monkeypatch
) -> None:
    _a_bug_is_not_turned_into_a_banner(
        tmp_path, monkeypatch, "App._known_overrides (reads the parts)"
    )


# fail-before (real run on c7eb5c79, batch 13): it FAILS there, first failing line: AssertionError: App.mode_banner (the outer catch): a bug of an unnamed type was turned into a banner
def test_a_bug_in_the_outer_catch_of_the_app_is_not_turned_into_a_banner(
    tmp_path, monkeypatch
) -> None:
    _a_bug_is_not_turned_into_a_banner(tmp_path, monkeypatch, "App.mode_banner (the outer catch)")


# fail-before (real run on c7eb5c79, batch 13): it FAILS there, first failing line: AssertionError: banner_or_unconfirmed: a bug of an unnamed type was turned into a banner
def test_a_bug_in_banner_or_unconfirmed_is_not_turned_into_a_banner(tmp_path, monkeypatch) -> None:
    _a_bug_is_not_turned_into_a_banner(tmp_path, monkeypatch, "banner_or_unconfirmed")


# fail-before (real run on c7eb5c79, batch 13): it FAILS there, first failing line: AssertionError: _not_confirmed_that_cannot_fail (the words): a bug of an unnamed type was turned into a banner
def test_a_bug_in_the_words_of_the_banner_is_not_turned_into_a_banner(
    tmp_path, monkeypatch
) -> None:
    _a_bug_is_not_turned_into_a_banner(
        tmp_path, monkeypatch, "_not_confirmed_that_cannot_fail (the words)"
    )


# fail-before (real run on c7eb5c79, batch 13): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_bug_in_sealing_the_app_is_not_turned_into_a_banner(tmp_path, monkeypatch) -> None:
    _a_bug_is_not_turned_into_a_banner(tmp_path, monkeypatch, "App._seal (reads the app at build)")


# fail-before (real run on c7eb5c79, batch 13): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
@pytest.mark.parametrize("site", sorted(SURPRISE_SITES))
def test_pin_a_named_read_error_still_reads_unconfirmed_at_every_site(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, site: str
) -> None:
    # the other side of the rule above: each error in `READ_ERRORS` is an unreadable banner, shown
    # as not confirmed
    for kind in mb.READ_ERRORS:

        def raise_kind(*_a, _kind=kind, **_k):
            raise _kind("unreadable")

        app = _sealed_app(tmp_path, f"s2-{kind.__name__}")
        call = SURPRISE_SITES[site](app, monkeypatch, raise_kind)
        result = call()
        if isinstance(result, dict):
            assert result["tone"] == "unconfirmed", f"{site}: {kind.__name__} gave {result['tone']}"
        else:  # `_seal` returns nothing: the app is sealed as unreadable
            assert app.mode_banner()["tone"] == "unconfirmed", f"{site}: {kind.__name__}"
        monkeypatch.undo()  # the next error type starts from an untouched app


# fail-before: the old heads name no READ_ERRORS tuple (they have a private one), so the first run there fails on that name, which is not a behaviour result; this is a new check of the tuple itself.
def test_the_list_of_read_errors_holds_no_type_that_takes_every_error() -> None:
    wide = [kind.__name__ for kind in mb.READ_ERRORS if issubclass(_Surprise, kind)]
    assert not wide, f"READ_ERRORS holds a type that takes every error: {wide}"


# fail-before: not run on the old heads; the source check at mode_banner.py `_source_leaves_this_machine` is the sixth `except READ_ERRORS` site (the other five are in the surprise list above).
def test_a_bug_in_reading_the_endpoint_of_a_source_is_not_turned_into_an_answer(
    monkeypatch,
) -> None:
    monkeypatch.setattr(mb, "source_endpoint", _raise_surprise)
    try:
        mb._source_leaves_this_machine(object())
    except _Surprise:
        return
    raise AssertionError(
        "a bug of an unnamed type in the endpoint of a source was turned into an answer"
    )


def test_every_named_read_error_in_the_endpoint_of_a_source_reads_as_leaving_this_machine(
    monkeypatch,
) -> None:
    for kind in mb.READ_ERRORS:

        def raise_kind(*_a, _kind=kind, **_k):
            raise _kind("unreadable")

        monkeypatch.setattr(mb, "source_endpoint", raise_kind)
        assert mb._source_leaves_this_machine(object()) is True, (
            f"{kind.__name__} did not read as unknown"
        )


# fail-before (real run on c7eb5c79, batch 13): it FAILS there, first failing line: AssertionError: a bug in the channel was reported as an undelivered card
def test_an_error_type_the_channel_does_not_name_is_not_reported_as_a_delivered_card(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # fail-before: on c7eb5c79 and dd827d79 `post_card` caught `Exception`
    from hadavin_sdk.approvals.cards import Card
    from hadavin_sdk.approvals.channel import FakeChannel

    channel = FakeChannel()
    app = _built_app(tmp_path / "c1", channel)
    card = Card(text="a card", blocks=[], display_hash="0" * 64)
    monkeypatch.setattr(channel, "post_card", _raise_surprise)
    try:
        app.runtime.hooks.post_card(card)
    except _Surprise:
        pass
    else:
        raise AssertionError("a bug in the channel was reported as an undelivered card")
    for kind in (OSError, ValueError, LookupError, RuntimeError):

        def failing(_card, _kind=kind):
            raise _kind("gone")

        monkeypatch.setattr(channel, "post_card", failing)
        done = app.runtime.hooks.post_card(card)
        assert done.ok is False and done.reason == kind.__name__, f"{kind.__name__}: {done}"


# fail-before (real run on c7eb5c79, batch 13): it FAILS there, first failing line: AssertionError: a catch of every error is back: ['hadavin_sdk.app:295', 'hadavin_sdk.app:312', 'hadavin_sdk.app:471']
def test_one_list_of_read_errors_is_shared_and_no_code_here_catches_everything() -> None:
    import ast
    import inspect

    from hadavin_sdk import app as app_mod

    for module in (app_mod, mb):
        tree = ast.parse(inspect.getsource(module))
        bad = [
            f"{module.__name__}:{h.lineno}"
            for h in ast.walk(tree)
            if isinstance(h, ast.ExceptHandler)
            and (
                h.type is None
                or (isinstance(h.type, ast.Name) and h.type.id in ("Exception", "BaseException"))
            )
        ]
        assert not bad, f"a catch of every error is back: {bad}"
    assert app_mod.READ_ERRORS is mb.READ_ERRORS, "the app has its own list of read errors"
    assert mb.READ_ERRORS == (TypeError, ValueError, AttributeError, LookupError, RuntimeError)
    assert app_mod._DELIVERY_ERRORS == (OSError, ValueError, LookupError, RuntimeError)
    assert not hasattr(app_mod, "_SEAL_ERRORS") and not hasattr(mb, "_READ_ERRORS")
