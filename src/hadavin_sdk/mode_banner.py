"""The mode banner: the one line a person sees at the top of a screen that says what the system is connected to.

A reader of a demo screen must never mistake pretend services for real ones, and a reader of a real screen must never
be told its data is made up. This module is the only place the words live. A screen (web page, console, report)
receives the finished banner from `banner_for(...).as_dict()` and only paints it; the ready-made painter for a web page
is `templates/mode-banner/mode_banner.js`.

The mode is one of the stages in `stages.STAGES` (demo, pilot, prod) and nothing else; any other value is refused. The
names shown to people come from the caller (config), never from this file, and are checked so that a name cannot carry
a line break or markup that would change what the banner says.

Rules the tests pin:
  * made-up data is claimed only in the demo stage with no real service connected;
  * every real service that is connected is named in the text, in the order given, once;
  * the stand-ins (pretend services) are listed loudly in the demo stage;
  * a banner is always shown: there is no "hidden" state, so a missing banner can never be read as "all is real".
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any

from hadavin_sdk.backends.table import DEMO_ONLY
from hadavin_sdk.stages import STAGES

# What a service name may look like when it is shown to a person: a plain word or short phrase. Anything else (line
# breaks, angle brackets, quotes, very long text) is refused, so a name cannot rewrite the sentence round it.
_NAME_OK = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,39}")
TONES = ("demo", "real", "quiet", "unconfirmed")


@dataclass(frozen=True)
class BannerWords:
    """Every sentence of the banner. Replace a field to reword it (for example for another language); the rules above
    still hold because the choice of which sentence is shown is made in `banner_for`, not here."""

    tag_by_stage: Mapping[str, str]
    made_up: str = "Every record here is made-up demo data."
    nothing_sent: str = "Nothing here is sent to real customers or real systems."
    real_connected: str = "Real services are connected: {names}."
    real_data_note: str = "Data this system handles may be sent to them."
    standins_loud: str = "STAND-INS IN USE: {names}. These are pretend versions of real services. They are not connected."
    standins_none: str = "No real service is connected."
    standins_still: str = "Still stand-ins, not connected: {names}."
    none_real: str = "No real service is connected."
    not_confirmed_tag: str = "UNCONFIRMED"
    not_confirmed: str = (
        "The mode of this system could not be confirmed. Treat everything here as real until it is."
    )


DEFAULT_WORDS = BannerWords(tag_by_stage={"demo": "DEMO", "pilot": "PILOT", "prod": "LIVE"})


@dataclass(frozen=True)
class ModeBanner:
    """The finished banner. `tone` is "demo" (pretend services only), "real" (at least one real service), "quiet"
    (a pilot or live system with nothing real connected) or "unconfirmed" (only from `not_confirmed`). `standins` is a second, loud line, or "" when not needed."""

    stage: str
    tone: str
    tag: str
    text: str
    standins: str
    real: tuple[str, ...]
    stand_ins: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Plain data for JSON: what a screen receives."""
        d = asdict(self)
        d["real"] = list(self.real)
        d["stand_ins"] = list(self.stand_ins)
        return d


def _clean_names(kind: str, keys: object, names: Mapping[str, str]) -> tuple[str, ...]:
    """The shown names of a list of service keys: each mapped through `names`, checked, de-duplicated in order."""
    if isinstance(keys, (str, bytes)) or not isinstance(keys, Iterable):
        # a bare string would be read letter by letter and shown as a list of letters
        raise TypeError(f"{kind} must be a list of service names, not {type(keys).__name__}")
    out: dict[str, None] = {}
    for key in keys:
        if not isinstance(key, str) or not key:
            raise ValueError(f"{kind}: every entry must be a non-empty text, got {key!r}")
        shown = names.get(key, key)
        if not isinstance(shown, str) or not _NAME_OK.fullmatch(shown):
            raise ValueError(
                f"{kind}: the name shown for a service must be plain words (letters, digits, space . _ -)"
            )
        out.setdefault(shown, None)
    return tuple(out)


def banner_for(
    stage: str,
    real_services: Iterable[str] = (),
    stand_ins: Iterable[str] = (),
    names: Mapping[str, str] | None = None,
    words: BannerWords = DEFAULT_WORDS,
) -> ModeBanner:
    """The banner for a stage and the services it is connected to.

    `real_services` are the services that are really connected; `stand_ins` the pretend ones; `names` maps a service
    key to the name a person reads (a key without an entry is shown as it is). A stage that is not in
    `stages.STAGES`, a bare string where a list is wanted, or a name that is not plain words raises (the screen must
    not show a banner built from a value nobody checked)."""
    if stage not in STAGES:
        raise ValueError(f"stage {stage!r} is not one of {', '.join(STAGES)}")
    shown = names or {}
    real = _clean_names("real_services", real_services, shown)
    pretend = tuple(n for n in _clean_names("stand_ins", stand_ins, shown) if n not in real)
    tag = words.tag_by_stage[stage]
    if real:
        text = words.real_connected.format(names=", ".join(real)) + " " + words.real_data_note
        extra = words.standins_still.format(names=", ".join(pretend)) if pretend else ""
        return ModeBanner(stage, "real", tag, text, extra, real, pretend)
    if stage == STAGES[0]:
        loud = (
            words.standins_loud.format(names=", ".join(pretend)) if pretend else words.standins_none
        )
        return ModeBanner(
            stage, "demo", tag, words.made_up + " " + words.nothing_sent, loud, real, pretend
        )
    return ModeBanner(stage, "quiet", tag, words.none_real, "", real, pretend)


def not_confirmed(words: BannerWords = DEFAULT_WORDS) -> dict[str, Any]:
    """The banner a screen shows when it has no usable banner from the system. The same object the page script builds
    for itself; kept here so the words stay in one place."""
    return {
        "stage": "",
        "tone": "unconfirmed",
        "tag": words.not_confirmed_tag,
        "text": words.not_confirmed,
        "standins": "",
        "real": [],
        "stand_ins": [],
    }


def stand_ins_in(config: Any) -> tuple[str, ...]:
    """The component names of a loaded `Config` whose chosen kind is a demo-only kind (a stand-in): the same table
    (`backends.table.DEMO_ONLY`) that makes config refuse these kinds outside the demo stage."""
    return tuple(c for c, s in config.backends.entries() if (c, s.kind) in DEMO_ONLY)
