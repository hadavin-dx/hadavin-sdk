"""The mode banner: what a screen says about the stage and the services it is connected to. Made-up data only.

The words live in hadavin_sdk.mode_banner; the page script (templates/mode-banner/mode_banner.js) only paints them.
Rows: made-up data is claimed only in the demo stage with nothing real connected; every connected real service is named;
stand-ins are listed loudly; a value nobody checked (stage, bare string, odd name) is refused; the page script never
hides a banner, never parses HTML and falls back to the same words as the Python fallback.
"""

from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
from pathlib import Path

import pytest

from hadavin_sdk import mode_banner as mb
from hadavin_sdk.backends.table import DEMO_ONLY
from hadavin_sdk.config import load_config
from hadavin_sdk.stages import STAGES
from tests.conftest import make_cfg

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "templates" / "mode-banner" / "mode_banner.js"
PROBE = Path(__file__).resolve().parent / "mode_banner_probe.js"
NAMES = {"crm": "CRM", "mail": "mail", "ai": "AI step"}

needs_node = pytest.mark.skipif(
    shutil.which("node") is None and os.environ.get("HADAVIN_REQUIRE_NODE") != "1",
    reason="node is not installed",
)


# -- the words and the choice between them ---------------------------------------------------------------------------
def test_demo_with_only_stand_ins_says_made_up_and_lists_the_stand_ins_loudly() -> None:
    b = mb.banner_for("demo", [], ["crm", "mail"], NAMES)
    assert (b.stage, b.tone, b.tag) == ("demo", "demo", "DEMO")
    assert "made-up demo data" in b.text and "Nothing here is sent to real customers" in b.text
    assert (
        b.standins.startswith("STAND-INS IN USE: CRM, mail.") and "pretend versions" in b.standins
    )
    assert b.real == () and b.stand_ins == ("CRM", "mail")


def test_demo_with_no_stand_ins_still_says_nothing_real_is_connected() -> None:
    b = mb.banner_for("demo")
    assert b.tone == "demo" and "made-up demo data" in b.text
    assert b.standins == "No real service is connected."


def test_a_real_service_is_named_and_made_up_data_is_never_claimed() -> None:
    for stage in STAGES:
        b = mb.banner_for(stage, ["crm", "mail"], ["ai"], NAMES)
        assert b.tone == "real" and b.tag == mb.DEFAULT_WORDS.tag_by_stage[stage]
        assert (
            "Real services are connected: CRM, mail." in b.text and "may be sent to them" in b.text
        )
        assert "made-up" not in b.text and "Nothing here is sent" not in b.text
        assert b.standins == "Still stand-ins, not connected: AI step."


def test_pilot_or_live_with_nothing_real_is_quiet_and_not_made_up() -> None:
    for stage, tag in [("pilot", "PILOT"), ("prod", "LIVE")]:
        b = mb.banner_for(stage, [], ["ai"], NAMES)
        assert (b.tone, b.tag, b.text, b.standins) == (
            "quiet",
            tag,
            "No real service is connected.",
            "",
        )
        assert "made-up" not in b.text


def test_a_service_that_is_both_real_and_listed_as_stand_in_counts_as_real() -> None:
    b = mb.banner_for("demo", ["crm"], ["crm", "mail"], NAMES)
    assert b.real == ("CRM",) and b.stand_ins == ("mail",)


def test_names_come_from_the_caller_and_repeats_are_shown_once_in_order() -> None:
    b = mb.banner_for("pilot", ["b", "a", "b"], names={"a": "Alpha", "b": "Beta"})
    assert b.real == ("Beta", "Alpha")
    assert mb.banner_for("pilot", ["Unmapped Name"]).real == ("Unmapped Name",)


def test_the_words_can_be_replaced_without_changing_which_sentence_is_chosen() -> None:
    words = mb.BannerWords(tag_by_stage={"demo": "D", "pilot": "P", "prod": "L"}, made_up="MADE.")
    b = mb.banner_for("demo", [], [], words=words)
    assert b.tag == "D" and b.text.startswith("MADE.")
    assert (
        mb.banner_for("demo", ["x"], words=words).tone == "real"
    )  # the choice is not in the words


def test_an_unknown_stage_is_refused() -> None:
    for stage in ["", "DEMO", "Demo", "staging", "live", "test", None, 3]:
        with pytest.raises(ValueError, match="is not one of demo, pilot, prod"):
            mb.banner_for(stage)  # type: ignore[arg-type]


def test_a_bare_string_or_non_list_is_refused_not_read_letter_by_letter() -> None:
    for bad in ["crm", b"crm", None, 5]:
        for kwargs in ({"real_services": bad}, {"stand_ins": bad}):
            with pytest.raises(TypeError, match="must be a list of service names"):
                mb.banner_for("demo", **kwargs)  # type: ignore[arg-type]


def test_a_name_that_could_change_the_sentence_is_refused() -> None:
    for name in [
        "",
        "a\nb",
        "Every record here is real.\nDEMO",
        "<b>x</b>",
        'quote"',
        "x" * 41,
        " lead",
        "a\u202eb",
        "\u00e9",
    ]:
        with pytest.raises(ValueError, match="plain words|non-empty"):
            mb.banner_for("pilot", ["k"], names={"k": name})
        with pytest.raises(ValueError, match="plain words|non-empty"):
            mb.banner_for("pilot", [name])
        with pytest.raises(ValueError, match="plain words|non-empty"):
            mb.banner_for("demo", [], [name])


def test_a_service_key_that_is_not_text_is_refused() -> None:
    with pytest.raises(ValueError, match="non-empty text"):
        mb.banner_for("demo", [3])  # type: ignore[list-item]


# -- property test, seeded ------------------------------------------------------------------------------------------
def test_property_the_banner_never_misleads_for_any_stage_and_services() -> None:
    rng = random.Random(20261112)  # noqa: S311 - a seeded test generator, not a secret
    pool = ["crm", "mail", "ai", "store", "Chat", "x.y", "a-b", "z_9"]
    for _ in range(600):
        stage = rng.choice(STAGES)
        real = rng.sample(pool, rng.randint(0, 4))
        pretend = rng.sample(pool, rng.randint(0, 4))
        b = mb.banner_for(stage, real, pretend)
        shown = b.text + "\n" + b.standins
        assert b.tone in mb.TONES and b.tag and b.text
        assert b.tone == ("real" if real else ("demo" if stage == "demo" else "quiet"))
        assert ("made-up" in shown) == (stage == "demo" and not real)
        assert all(n in b.text for n in real), (
            stage,
            real,
            b,
        )  # every connected real service is named
        assert set(b.real).isdisjoint(b.stand_ins)
        assert not any(ord(c) < 32 for c in b.text + b.standins)
        assert json.loads(json.dumps(b.as_dict()))["tone"] == b.tone
        if stage == "demo" and not real and pretend:
            assert "STAND-INS IN USE" in b.standins and all(n in b.standins for n in pretend)


# -- reading the stand-ins from a loaded config ---------------------------------------------------------------------
def test_stand_ins_in_lists_the_components_whose_kind_is_demo_only(tmp_path: Path) -> None:
    cfg = load_config(make_cfg(tmp_path))  # the fixture is the demo config and holds fakes
    found = mb.stand_ins_in(cfg)
    assert found and {"llm", "channel", "secrets", "store"} <= set(found)
    assert {(c, s.kind) for c, s in cfg.backends.entries() if c in found} <= DEMO_ONLY
    assert mb.banner_for(cfg.environment, [], found).standins.startswith("STAND-INS IN USE")


# -- the page script ------------------------------------------------------------------------------------------------
def _paint(banner: object) -> dict:
    arg = "undefined" if banner is None else json.dumps(banner)
    out = subprocess.run(  # noqa: S603 (fixed argument list, no shell)
        ["node", str(PROBE), str(JS), arg],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return json.loads(out.stdout.strip().splitlines()[-1])


@needs_node
def test_the_page_paints_exactly_what_python_wrote() -> None:
    banners = [
        mb.banner_for("demo", [], ["crm"], NAMES),
        mb.banner_for("demo", ["crm"], ["mail"], NAMES),
        mb.banner_for("pilot", [], []),
        mb.banner_for("prod", ["mail"], []),
    ]
    for banner in banners:
        seen = _paint(banner.as_dict())
        assert (
            seen["hidden"] is False
            and seen["tone"] == banner.tone
            and seen["stage"] == banner.stage
        )
        assert seen["lines"][0] == {"cls": "mode-banner__tag", "text": banner.tag}
        assert seen["lines"][1] == {"cls": "mode-banner__text", "text": " " + banner.text}
        assert len(seen["lines"]) == (3 if banner.standins else 2)
        if banner.standins:
            assert seen["lines"][2] == {"cls": "mode-banner__standins", "text": banner.standins}


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
    ]
    for bad in bad_banners:
        seen = _paint(bad)
        assert (
            seen["hidden"] is False
            and seen["tone"] == "unconfirmed"
            and seen["shownTone"] == "unconfirmed"
        )
        assert seen["lines"][0]["text"] == mb.not_confirmed()["tag"]
        assert seen["lines"][1]["text"] == " " + mb.not_confirmed()["text"]


@needs_node
def test_the_page_fallback_has_the_same_words_as_the_python_fallback() -> None:
    assert _paint(None)["notConfirmed"] == mb.not_confirmed()


@needs_node
def test_markup_in_the_text_is_shown_as_text_never_parsed() -> None:
    evil = "<img src=x onerror=alert(1)>"
    seen = _paint({"tone": "real", "tag": "<b>", "text": evil, "standins": "<i>"})
    assert seen["lines"][1]["text"] == " " + evil and seen["lines"][0]["text"] == "<b>"


def test_the_page_script_has_no_way_to_parse_html_or_load_anything() -> None:
    text = JS.read_text(encoding="utf-8")
    for banned in (
        "innerHTML",
        "outerHTML",
        "insertAdjacentHTML",
        "document.write",
        "eval(",
        "fetch(",
        "XMLHttpRequest",
    ):
        assert banned not in text, banned
    assert "textContent" in text  # the check is not vacuous
