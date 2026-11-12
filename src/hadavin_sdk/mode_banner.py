"""The mode banner: the one line a person sees at the top of a screen that says what the system is connected to.

A reader of a demo screen must never mistake pretend services for real ones, and a reader of a real screen must never
be told its data is made up. This module is the only place the words live. A screen (web page, console, report)
receives the finished banner from `banner_from_config(config).as_dict()` and only paints it; the ready-made painter for
a web page is `templates/mode-banner/mode_banner.js`.

The stage and both lists of services (the real ones and the pretend ones, called stand-ins) are read from the loaded
config in one place, `banner_from_config`, so a caller cannot forget to name a real service and so get the made-up
sentence by accident. `_banner_for` is the private lower-level function it uses: its lists are required keyword arguments with
no defaults, because an empty default would answer "nothing real is connected" when nobody had checked.

The mode is one of the stages in `stages.STAGES` (demo, pilot, prod) and nothing else; any other value is refused. The
names shown to people come from the caller (config), never from this file, and are checked so that a name cannot carry
a line break, markup, or a word that would change what the banner says (made-up, demo, real, stand-in, nothing is).

Rules the tests pin:
  * made-up data is claimed only in the demo stage with no real service connected;
  * every real service that is connected is named in the text, in the order given, once;
  * the stand-ins are listed in every stage (loudly in the demo stage), so a pilot or live system never hides them;
  * a banner is always shown: there is no "hidden" state, so a missing banner can never be read as "all is real".
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from hadavin_sdk.backends.table import DEFAULTS, DEMO_ONLY, NOT_PROD
from hadavin_sdk.stages import STAGES

# The one way in is `banner_from_config`. The older public names `banner_for`, `services_in` and `stand_ins_in` are
# gone (the lower-level pieces keep a leading underscore); a test pins that.
__all__ = [
    "DEFAULT_WORDS",
    "MAX_TEXT_LENGTH",
    "TONES",
    "BannerWords",
    "ModeBanner",
    "banner_from_config",
    "not_confirmed",
]

_DEMO_STAGE = "demo"  # the stage whose banner may say "made-up"; it is checked against STAGES below, not its position
if (
    _DEMO_STAGE not in STAGES
):  # pragma: no cover - a stage rename must show up here, loudly, at import
    raise RuntimeError(
        f"mode_banner: the demo stage {_DEMO_STAGE!r} is not in stages.STAGES {STAGES}"
    )

# What a service name may look like when it is shown to a person: words made of letters, digits and . _ - joined by
# SINGLE spaces; a word never ends with "." (so a name cannot hold a sentence break) and the whole name is at most 40
# characters. Anything else (line breaks, angle brackets, quotes, double or edge spaces) is refused.
_NAME_OK = re.compile(
    r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9_-])?(?: [A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9_-])?)*"
)
_NAME_MAX = 40
# Words a name may not hold, because they would let a name say what only the banner may say.
_NAME_RESERVED = re.compile(
    r"(?<![A-Za-z0-9])(?:made[ _.-]?up|demo|real|stand[ _.-]?ins?|nothing is)(?![A-Za-z0-9])",
    re.IGNORECASE,
)
# The page script refuses a text longer than this (templates/mode-banner/mode_banner.js); a test pins both numbers.
MAX_TEXT_LENGTH = 600
TONES = ("demo", "real", "quiet", "unconfirmed")
# Kinds that connect to nothing outside the process: no signer, no anchor, and the built-in pattern detector. They are
# neither a real service nor a stand-in, so they are not listed. Every OTHER kind outside the DEMO_ONLY table counts as real:
# a kind this file does not know is never hidden, because naming too much is the safe mistake.
_NOTHING_CONNECTED = NOT_PROD | {("detector", DEFAULTS["detector"])}


@dataclass(frozen=True)
class BannerWords:
    """Every sentence of the banner. Replace a field to reword it (for example for another language); the rules above
    still hold because the choice of which sentence is shown is made in `_banner_for`, not here."""

    tag_by_mode: Mapping[str, str]
    made_up: str = "Every record here is made-up demo data."
    nothing_sent: str = "Nothing here is sent to real customers or real systems."
    real_connected: str = "Real services are connected: {names}."
    real_data_note: str = "Data this system handles may be sent to them."
    standins_loud: str = "MADE-UP STAND-INS IN USE: {names}. These are pretend versions of real services. They are not connected."
    standins_none: str = "No real service is connected."
    standins_still: str = "Still stand-ins, not connected: {names}."
    none_real: str = "No real service is connected."
    not_confirmed_tag: str = "UNCONFIRMED"
    not_confirmed: str = (
        "The mode of this system could not be confirmed. Treat everything here as real."
    )

    def __post_init__(self) -> None:
        missing = [m for m in STAGES if m not in self.tag_by_mode]
        if missing:
            raise ValueError(f"tag_by_mode has no tag for the stage(s): {', '.join(missing)}")


DEFAULT_WORDS = BannerWords(tag_by_mode={"demo": "DEMO", "pilot": "PILOT", "prod": "LIVE"})


@dataclass(frozen=True)
class ModeBanner:
    """The finished banner. `tone` is "demo" (pretend services only), "real" (at least one real service), "quiet"
    (a pilot or live system with nothing real connected) or "unconfirmed" (only from `not_confirmed`). `standins` is a second, loud line, or "" when not needed."""

    mode: str
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
    """The shown names of a list of service keys: each mapped through `names` (a key without an entry is shown as
    "component <key>"), checked, de-duplicated in order."""
    if isinstance(keys, (str, bytes, Mapping, set, frozenset)) or not isinstance(keys, Iterable):
        # a bare string would be read letter by letter; a dict or set has no order to keep
        raise TypeError(f"{kind} must be a list of service names, not {type(keys).__name__}")
    out: dict[str, None] = {}
    for key in keys:
        if not isinstance(key, str) or not key:
            raise ValueError(f"{kind}: every entry must be a non-empty text, got {key!r}")
        shown = names.get(key, f"component {key}")
        if (
            not isinstance(shown, str)
            or len(shown) > _NAME_MAX
            or not _NAME_OK.fullmatch(shown)
            or _NAME_RESERVED.search(shown)
        ):
            raise ValueError(
                f"{kind}: the name shown for a service must be plain words (letters, digits, . _ - and single "
                f"spaces, at most {_NAME_MAX} characters, and none of the words made-up, demo, real, stand-in, nothing is)"
            )
        out.setdefault(shown, None)
    return tuple(out)


def _banner_for(
    mode: str,
    *,
    real_services: Iterable[str],
    stand_ins: Iterable[str],
    names: Mapping[str, str] | None = None,
    words: BannerWords = DEFAULT_WORDS,
) -> ModeBanner:
    """The banner for a stage and the services it is connected to (the lower-level call: prefer `banner_from_config`).

    `real_services` are the services that are really connected; `stand_ins` the pretend ones; both are required, with no
    default, so an empty list always means "checked, none". `names` maps a service key to the name a person reads (a key
    without an entry is shown as "component <key>"). A stage that is not in `stages.STAGES`, a bare string, dict or set
    where a list is wanted, a `names` that is not a mapping, a name that is not plain words, or a text too long for the
    page script raises (the screen must not show a banner built from a value nobody checked)."""
    if mode not in STAGES:
        raise ValueError(f"mode {mode!r} is not one of {', '.join(STAGES)}")
    if names is not None and not isinstance(names, Mapping):
        raise TypeError(
            f"names must be a mapping of service key to shown name, not {type(names).__name__}"
        )
    shown = names or {}
    real = _clean_names("real_services", real_services, shown)
    pretend = tuple(n for n in _clean_names("stand_ins", stand_ins, shown) if n not in real)
    tag = words.tag_by_mode[mode]
    if real:
        text = words.real_connected.format(names=", ".join(real)) + " " + words.real_data_note
        extra = words.standins_still.format(names=", ".join(pretend)) if pretend else ""
        banner = ModeBanner(mode, "real", tag, text, extra, real, pretend)
    elif mode == _DEMO_STAGE:
        loud = (
            words.standins_loud.format(names=", ".join(pretend)) if pretend else words.standins_none
        )
        text = words.made_up + " " + words.nothing_sent
        banner = ModeBanner(mode, "demo", tag, text, loud, real, pretend)
    else:
        extra = words.standins_still.format(names=", ".join(pretend)) if pretend else ""
        banner = ModeBanner(mode, "quiet", tag, words.none_real, extra, real, pretend)
    if len(banner.text) > MAX_TEXT_LENGTH or len(banner.standins) > MAX_TEXT_LENGTH:
        raise ValueError(
            f"the banner text is longer than the {MAX_TEXT_LENGTH} characters the page script shows: too many services"
        )
    return banner


class _Setting(Protocol):
    @property
    def kind(self) -> str: ...


class _Backends(Protocol):
    def entries(self) -> Sequence[tuple[str, _Setting]]: ...


class ConfigLike(Protocol):
    """What the banner reads from a loaded `Config`: the stage and the chosen kind of every component."""

    @property
    def environment(self) -> str: ...

    @property
    def backends(self) -> _Backends: ...


def _services_in(config: ConfigLike) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(real, stand_ins): the component names of a loaded `Config`, sorted by kind. A stand-in is a component whose
    chosen kind is one of the demo-only kinds (`backends.table.DEMO_ONLY`, the same table that makes config refuse those
    kinds outside the demo stage); a component that connects to nothing outside the process is left out; every other
    component is real. An entry without a kind raises ValueError: it is not guessed into a list."""
    real: list[str] = []
    stand_ins: list[str] = []
    for component, setting in config.backends.entries():
        kind = getattr(setting, "kind", None)
        if not isinstance(component, str) or not component or not isinstance(kind, str) or not kind:
            raise ValueError(
                f"a component without a name or a kind cannot be placed in the banner: {component!r}"
            )
        if (component, kind) in DEMO_ONLY:
            stand_ins.append(component)
        elif (component, kind) not in _NOTHING_CONNECTED:
            real.append(component)
    return tuple(real), tuple(stand_ins)


def banner_from_config(
    config: ConfigLike,
    names: Mapping[str, str] | None = None,
    words: BannerWords = DEFAULT_WORDS,
) -> ModeBanner:
    """The banner of a loaded `Config`: the stage is `config.environment`, and the real services and stand-ins come
    from `config.backends.entries()` (see `_services_in`). This is the one place the decision is made."""
    real, stand_ins = _services_in(config)
    return _banner_for(
        config.environment, real_services=real, stand_ins=stand_ins, names=names, words=words
    )


def not_confirmed(words: BannerWords = DEFAULT_WORDS) -> dict[str, Any]:
    """The banner a screen shows when it has no usable banner from the system. The same object the page script builds
    for itself; kept here so the words stay in one place."""
    return {
        "mode": "",
        "tone": "unconfirmed",
        "tag": words.not_confirmed_tag,
        "text": words.not_confirmed,
        "standins": "",
        "real": [],
        "stand_ins": [],
    }
