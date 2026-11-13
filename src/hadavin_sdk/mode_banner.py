"""The mode banner: the one line a person sees at the top of a screen that says what the system is connected to.

A reader of a demo screen must never mistake pretend services for real ones, and a reader of a real screen must never
be told its data is made up. This module is the only place the words live. A screen (web page, console, report)
receives the finished banner from `banner_or_unconfirmed(config, tool_specs=registry.tools)` and only paints it; the ready-made painter for
a web page is `templates/mode-banner/mode_banner.js`.

The stage and both lists of services (the real ones and the pretend ones, called stand-ins) are read from the loaded
config in one place, `banner_from_config(config, names, words, tool_specs=...)` (a screen calls `banner_or_unconfirmed`, which
calls it and never raises), so a caller cannot forget to name a real service and so get the made-up
sentence by accident. `_banner_for` is the private lower-level function they use: its lists are required keyword arguments with
no defaults, because an empty default would answer "nothing real is connected" when nobody had checked.

The mode is one of the stages in `stages.STAGES` (demo, pilot, prod) and nothing else; any other value is refused. The
names shown to people come from the caller (config), never from this file, and are checked so that a name cannot carry
a line break, markup, or a word that would change what the banner says (made-up, demo, real, stand-in, nothing is).

Rules the tests pin:
  * made-up data is claimed only in the demo stage with no real service connected, and "connected" covers every field of
    the config that can name an endpoint: the backends, `systems`, `egress_hosts`, `sources` and the hosts named by the
    tool manifests (`tool_specs`, required: a caller that cannot give them passes None and a configured tool module then
    counts as one real service);
  * before a banner leaves, one check confirms that it names every real service as a whole word, that a real, pilot or live
    banner never holds the made-up sentences, and that a demo banner names no real service;
  * every real service that is connected is named in the text, in the order given, once;
  * the stand-ins are listed in every stage (loudly in the demo stage), so a pilot or live system never hides them;
  * there is no "hidden" state: `banner_or_unconfirmed` always gives a finished banner (the "not confirmed" one when
    the real banner cannot be built), so a missing banner can never be read as "all is real". `banner_from_config`
    itself RAISES when it cannot say (a missing config field, a name that is not plain words): a screen that calls it
    must catch that and show `not_confirmed()`, or call `banner_or_unconfirmed`, which does both;
  * a service name is shown only when it is plain ASCII words (see `_NAME_OK`): a name in another script is refused, not
    transliterated (so a reserved word written in another script can never occur in a name, and listing one in
    `BannerWords.reserved_words` is harmless but has no effect), and the reserved claim words are the English ones, the two
    made-up sentences of the `words` in use and the `reserved_words` of those `words`.

Limits, stated where the made-up sentence is made: (1) "this machine" means the loopback names of `guard.http.LOOPBACK`; a
loopback address can still be a port-forward, a tunnel or a sidecar that leads off the machine, and the banner cannot see
that. (2) Tool code runs in this process and is reviewed, not sandboxed: it could open a socket the manifest does not name;
the banner counts what the manifests name, and counts a configured tool module as one real service when no manifest
names a host for it (no manifest read for that module, or only manifests with an empty `hosts` list): a tool that reaches
nothing but declares no host therefore also reads as real, which is the safe mistake. (3) The banner is worked out when `banner_from_config` is called; a caller that
keeps it, a page cache, or a config whose fields are changed or reloaded afterwards, can show an out-of-date banner: call it
again when the config is loaded again. (4) `localhost` is trusted to resolve to the loopback address on this machine. (5) The
settings of a stand-in kind are never inspected: the banner reads the kind name only. (6) The overrides handed to `app.build`
(`tools=` callables, `sources=`, `channel=`, `llm=`, `detector=`, `secrets=`) replace what the config names and are not seen by
the banner; a callable handed to `app.build(tools=...)` has no manifest, so its hosts are not counted. (7) The page script paints the
`tone` it is given and checks it against the mode, the real list and the names; the made-up sentences themselves are checked here,
in Python, before a banner leaves (`_check_what_is_claimed`), not again in the page. (8) "This machine" is decided for a bare host and
for a url by one function (`_is_this_machine`): a host with a space, a control character, a non-ASCII character or padding is NOT
this machine, whether it is written alone (an egress list, a tool manifest) or inside a url.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Protocol
from urllib.parse import urlsplit

from hadavin_sdk.backends.table import DEFAULTS, DEMO_ONLY
from hadavin_sdk.guard.egress import normalise_host
from hadavin_sdk.guard.http import LOOPBACK
from hadavin_sdk.sources.kinds import source_endpoint
from hadavin_sdk.stages import STAGES

if TYPE_CHECKING:  # the type only: no load-time import of the tool client
    from hadavin_sdk.tools import ToolSpec

_LOG = logging.getLogger(__name__)

# A screen calls `banner_or_unconfirmed`; `banner_from_config` is the same decision but raises when it cannot say. The
# older public names `banner_for`, `services_in` and `stand_ins_in` are gone (the lower-level pieces keep a leading
# underscore); a test pins that.
__all__ = [
    "DEFAULT_WORDS",
    "EGRESS_HOSTS",
    "EXTERNAL_SYSTEMS",
    "MAX_TEXT_LENGTH",
    "NOTHING_CONNECTED",
    "READ_SOURCES",
    "TONES",
    "TOOL_HOSTS",
    "TOOL_MODULES",
    "BannerWords",
    "ModeBanner",
    "banner_from_config",
    "banner_or_unconfirmed",
    "names_in",
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
# Words a name may not hold, because they would let a name say what only the banner may say. The fixed English words
# below always apply; `_reserved_for(words)` adds the two made-up sentences and the `reserved_words` of the words in use,
# so a reworded banner (another language) protects its own claim sentences and key words too.
_RESERVED_WORDS = r"made[ _.-]?up|demo|real|stand[ _.-]?ins?|nothing is"
_BOUNDARY = r"(?<![A-Za-z0-9])(?:{})(?![A-Za-z0-9])"
# The page script refuses a text longer than this (templates/mode-banner/mode_banner.js); a test pins both numbers.
MAX_TEXT_LENGTH = 600
TONES = ("demo", "real", "quiet", "unconfirmed")
# The (component, kind) pairs that connect to nothing outside the process. They are neither a real service nor a
# stand-in, so the banner does not list them. This is an explicit allow-list, not derived from any other table (the table the
# prod gate reads, `backends.table.NOT_PROD`, is about what is allowed in prod and can grow for other reasons): every OTHER
# kind outside the DEMO_ONLY table counts as real, so a kind this file does not know, or a kind added to another table
# later, is never hidden: naming too much is the safe mistake. A test pins the exact content.
#   ("signer", "none")   no signing at all: nothing is called.
#   ("anchor", "none")   no anchoring at all: nothing is called.
#   ("detector", <the default detector kind>)  the built-in pattern detector runs inside the process.
# Not listed on purpose: ("signer", "ed25519_local") signs in process but reads its key from the secrets component or a
# file and is shown as real (the safe reading, and the same as before this list was explicit); every other signer and
# anchor kind calls a key service or a storage service over the network.
NOTHING_CONNECTED: frozenset[tuple[str, str]] = frozenset(
    {("signer", "none"), ("anchor", "none"), ("detector", DEFAULTS["detector"])}
)


@dataclass(frozen=True)
class BannerWords:
    """Every sentence of the banner. Replace a field to reword it (for example for another language); the rules above
    still hold because the choice of which sentence is shown is made in `_banner_for`, not here."""

    tag_by_mode: Mapping[str, str]
    made_up: str = "Every record here is made-up demo data."
    nothing_sent: str = "Nothing here is set up to send data to real customers or real systems."
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
    # Key words of the made-up claim that no service name may hold (see `_reserved_for`). A reworded banner (another
    # language) lists its own key words here; the English ones are always reserved as well. Names are plain ASCII, so a word in
    # another script can never occur in a name.
    reserved_words: tuple[str, ...] = ("made-up", "demo", "real", "stand-in", "nothing is")

    def __post_init__(self) -> None:
        missing = [m for m in STAGES if m not in self.tag_by_mode]
        if missing:
            raise ValueError(f"tag_by_mode has no tag for the stage(s): {', '.join(missing)}")
        if not isinstance(self.reserved_words, tuple) or not all(
            isinstance(w, str) and w.strip() for w in self.reserved_words
        ):
            raise ValueError("reserved_words must be a tuple of non-empty text")


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


def _reserved_for(words: BannerWords) -> re.Pattern[str]:
    """The words a service name may not hold: the fixed English words, the made-up sentences of `words` (the two
    sentences that claim made-up data) and its `reserved_words` (their key words). An empty sentence adds nothing here
    (the claim check refuses it separately)."""
    extra = [
        re.escape(c.strip())
        for c in (words.made_up, words.nothing_sent, *words.reserved_words)
        if c.strip()
    ]
    return re.compile(_BOUNDARY.format("|".join([_RESERVED_WORDS, *extra])), re.IGNORECASE)


def _clean_names(
    kind: str, keys: object, names: Mapping[str, str], words: BannerWords
) -> tuple[str, ...]:
    """The shown names of a list of service keys: each mapped through `names` (a key without an entry is shown as
    "component <key>"), checked, de-duplicated in order. A name is plain ASCII words only (see `_NAME_OK`)."""
    reserved = _reserved_for(words)
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
            or reserved.search(shown)
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
    real = _clean_names("real_services", real_services, shown, words)
    pretend = tuple(n for n in _clean_names("stand_ins", stand_ins, shown, words) if n not in real)
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
    _check_what_is_claimed(banner, words)
    if (
        len(banner.text) > MAX_TEXT_LENGTH
        or len(banner.standins) > MAX_TEXT_LENGTH
        or len(banner.tag) > MAX_TEXT_LENGTH
    ):
        raise ValueError(
            f"the banner text or tag is longer than the {MAX_TEXT_LENGTH} characters the page script shows: too many services"
        )
    return banner


def names_in(text: str, name: str) -> bool:
    """True when `name` is in `text` as a whole name. A neighbouring letter, digit, "_" or "-" makes it part of a longer
    word, and so does a "." with a letter or digit beyond it ("CRM.v2", "x.CRM"); a sentence-ending "." does not. The page
    script (`templates/mode-banner/mode_banner.js`, `hasName`) applies the same rule; a test runs both on one table."""
    if not name:
        return False
    word = "A-Za-z0-9_-"
    pattern = (
        rf"(?<![{word}])(?<![A-Za-z0-9]\.)" + re.escape(name) + rf"(?![{word}])(?!\.[A-Za-z0-9])"
    )
    return re.search(pattern, text) is not None


def _names_segment(banner: ModeBanner, words: BannerWords) -> str | None:
    """The part of the banner text that holds the formatted list of real names (and one character after it), or None
    when the text is not the `real_connected` sentence of these words with that list in it. Only this part may carry a
    name: a name that happens to occur elsewhere in the text (a note, another sentence) does not count as shown."""
    before, found, _after = words.real_connected.partition("{names}")
    joined = ", ".join(banner.real)
    if not found or not banner.text.startswith(before + joined):
        return None
    return banner.text[len(before) : len(before) + len(joined) + 1]


def _check_what_is_claimed(banner: ModeBanner, words: BannerWords) -> None:
    """The last check before a banner leaves: what it says must agree with what it was built from. A banner that names
    a real service lists every one of them in its text (as a whole name) and never holds the made-up sentences; a quiet
    banner (pilot or live, nothing real) never holds them either; the made-up claim appears only in a demo banner, which
    names no real service. A reworded `BannerWords` that breaks one of these, or leaves a claim sentence empty (which would
    switch the check off), raises here instead of reaching a screen."""
    claim = (words.made_up, words.nothing_sent)
    if not all(isinstance(c, str) and c.strip() for c in claim):
        raise ValueError("the made-up sentences of the banner words must not be empty")
    said = banner.text + " " + banner.standins
    if banner.tone == "demo" and banner.real:
        raise ValueError("a demo banner must name no real service")
    if banner.real:
        segment = _names_segment(banner, words)
        missing = [n for n in banner.real if segment is None or not names_in(segment, n)]
        if missing:
            raise ValueError(f"the banner text does not name every real service: {missing}")
    if banner.tone != "demo" and any(c in said for c in claim):
        raise ValueError(
            "a banner with a real service, or a pilot or live one, claims made-up data"
        )


class _Setting(Protocol):
    @property
    def kind(self) -> str: ...


class _Backends(Protocol):
    def entries(self) -> Sequence[tuple[str, _Setting]]: ...


class ConfigLike(Protocol):
    """What the banner reads from a loaded `Config`: the stage, the chosen kind of every component, and
    `systems`, `egress_hosts`, `sources` and `tool_modules`, the other fields that can name an endpoint. All of them are
    required: a config that lacks one, or holds None or a value of the wrong type, makes the banner raise (see `_field`).
    `systems` values hold a `base_url` (`config.System.base_url` is a `str`; a value of any other type is read as a place
    that is not this machine). `egress_hosts` is any collection or iterable of host texts: it is read once."""

    @property
    def environment(self) -> str: ...

    @property
    def backends(self) -> _Backends: ...

    @property
    def systems(self) -> Mapping[str, Any]: ...

    @property
    def egress_hosts(self) -> Collection[str] | Iterable[str]: ...

    @property
    def sources(self) -> Mapping[str, Any]: ...

    @property
    def tool_modules(self) -> Sequence[str]: ...


# The keys of the real services that are not backends. A caller may give each a nicer shown name through `names`.
EXTERNAL_SYSTEMS = "external-systems"
EGRESS_HOSTS = "egress-hosts"
READ_SOURCES = "read-sources"
TOOL_HOSTS = "tool-hosts"
TOOL_MODULES = "tool-modules"


def _is_this_machine(host: object) -> bool:
    """True only for a host that the connection guard reads as this machine (`guard.http.LOOPBACK`, after the guard's own
    `normalise_host`: NFKC, lower case, no trailing dot). It is the ONE place that decides, for a bare host (an egress
    list, a tool manifest) and for the host part of a url alike. The text must be a non-empty `str`, ASCII only, with no
    padding (it equals its own `.strip()`; any other white space or control character inside a name already keeps it
    out of the loopback names, so no separate check is kept for it); otherwise it is NOT this machine,
    so a full-width or padded spelling of `localhost` reads as leaving, never as this machine (the stricter reading wins
    everywhere). Modelled on the connection guard's loopback names and normaliser, and at least as strict as the tool client.
    The manifest check `tools.spec_problems` (through `forbidden_host`) refuses a host that is an IP literal, a numeric host,
    `localhost`, a name under `.localhost` or a metadata name, and one that is not lower case or holds `/`, `:` or `@`, so
    a manifest that passes it names no loopback host; a loopback name is still read as this machine here, so that the
    function gives one answer everywhere (a spec built without that check can hold one)."""
    if not isinstance(host, str) or not host or not host.isascii() or host != host.strip():
        return False
    return normalise_host(host) in LOOPBACK


_PORT_TAIL = re.compile(r":[0-9]*")


def _port_tail_ok(netloc: str) -> bool:
    """After the host part of a url's network location only `:port` (digits) may follow. Text after the closing `]` of
    an address in brackets (`[::1]evil.example`, `[::1]:80x`), or a port that is not digits, is not read as a host
    on this machine."""
    if netloc.startswith("["):
        tail = netloc.rpartition("]")[2]
    else:
        _host, colon, port = netloc.partition(":")
        tail = colon + port
    return tail == "" or _PORT_TAIL.fullmatch(tail) is not None


def _url_leaves_this_machine(url: object) -> bool:
    """True when `url` names a host that is not this machine. It reads a url the way the tool client does
    (`tools.py`, `ToolContext.fetch`): a backslash, white space, a control or non-ASCII character, a percent sign or an
    `@` in the host part, or a value that cannot be read, counts as leaving: naming too much is the safe mistake."""
    if not isinstance(url, str) or re.search(r"[\\\s\x00-\x1f\x7f]", url) or not url.isascii():
        return True
    try:
        parts = urlsplit(url)
        host = parts.hostname
    except ValueError:
        return True
    if "%" in parts.netloc or "%" in parts.path or "@" in parts.netloc:
        return True
    if not _port_tail_ok(parts.netloc):
        return True
    return not _is_this_machine(host)


def _source_leaves_this_machine(source: object) -> bool:
    """True when a configured read source points at a host that is not this machine, or when its endpoint cannot be
    worked out (a kind this file does not know, settings that do not build)."""
    try:
        return _url_leaves_this_machine(source_endpoint(source))
    except Exception:  # noqa: BLE001 - any failure means "unknown", and unknown is shown as real
        return True


def _field(config: object, name: str, kind: type | tuple[type, ...]) -> Any:
    """A field of the config that can name an endpoint. A config without it, or with a value of the wrong type, raises:
    a missing field must never read as "empty, so nothing is sent"."""
    value = getattr(config, name, None)
    if value is None:
        raise ValueError(f"the config has no {name}: the banner cannot say what it is connected to")
    if not isinstance(value, kind):
        raise TypeError(f"the config's {name} is a {type(value).__name__}, not a usable value")
    return value


def _tool_hosts_leave(
    tool_specs: Mapping[str, Mapping[str, ToolSpec]],
) -> tuple[bool, frozenset[str]]:
    """(some manifest host is not this machine, the tool modules whose every spec names at least one host). Every spec
    is read: one without a `hosts` list of text raises TypeError naming the tool, and an agent entry that is not a mapping
    raises TypeError (never AttributeError, and never read as "no hosts", which would show a risk as no risk). The module
    of a spec is the part of its `function` before ":"; a spec with no usable `function` belongs to no module. A module
    with a spec that names no host, or with no spec at all, is not in the answer (see `_outside_endpoints`)."""
    leaves = False
    named: dict[str, bool] = {}  # module -> every spec read so far names a host
    for agent, by_name in tool_specs.items():
        if not isinstance(by_name, Mapping):
            raise TypeError(
                f"tool_specs[{agent!r}] must be a mapping of tool name to spec, not {type(by_name).__name__}"
            )
        for tool, spec in by_name.items():
            hosts = getattr(spec, "hosts", None)
            if not isinstance(hosts, (tuple, list)) or not all(isinstance(h, str) for h in hosts):
                raise TypeError(
                    f"tool {tool!r} of agent {agent!r} has no `hosts` list of text: the banner cannot say where it reaches"
                )
            function = getattr(spec, "function", None)
            module = function.partition(":")[0] if isinstance(function, str) else ""
            named[module] = named.get(module, True) and len(hosts) > 0
            leaves = leaves or any(not _is_this_machine(h) for h in hosts)
    return leaves, frozenset(m for m, every in named.items() if every and m)


def _outside_endpoints(
    config: object, tool_specs: Mapping[str, Mapping[str, ToolSpec]] | None
) -> list[str]:
    """The keys of the places a config can send data to besides its backends: a system whose base_url is not this
    machine, any egress host that is not this machine, a read source whose endpoint is not this machine, a host named by
    a tool manifest that is not this machine. `tool_specs` is the registry's `tools` (agent -> tool name -> spec); None
    means the caller cannot give them. A configured tool module counts as ONE real service (`TOOL_MODULES`) when `tool_specs`
    is None, and also when any configured module has no spec that names it, or has a spec that names no host: a module the
    manifests do not account for is not hidden, however many other modules are. Tool code is reviewed, not sandboxed
    (see the module docstring), so the hosts its manifest names are what can be counted."""
    found: list[str] = []
    systems = _field(config, "systems", Mapping)
    if any(_url_leaves_this_machine(getattr(s, "base_url", None)) for s in systems.values()):
        found.append(EXTERNAL_SYSTEMS)
    egress = _field(config, "egress_hosts", Iterable)
    if isinstance(egress, (str, bytes, Mapping)):
        raise TypeError(
            f"the config's egress_hosts is a {type(egress).__name__}, not a list of hosts"
        )
    if any(not _is_this_machine(h) for h in tuple(egress)):
        found.append(EGRESS_HOSTS)
    sources = _field(config, "sources", Mapping)
    if any(_source_leaves_this_machine(src) for src in sources.values()):
        found.append(READ_SOURCES)
    modules = _field(config, "tool_modules", (list, tuple))
    if tool_specs is None:
        if modules:
            found.append(TOOL_MODULES)
        return found
    if not isinstance(tool_specs, Mapping):
        raise TypeError(
            f"tool_specs must be the registry's tools mapping or None, not {type(tool_specs).__name__}"
        )
    leaves, covered = _tool_hosts_leave(tool_specs)
    if any(not isinstance(m, str) or m not in covered for m in modules):
        found.append(
            TOOL_MODULES
        )  # a configured module no manifest accounts for: nothing is known about it
    if leaves:
        found.append(TOOL_HOSTS)
    return found


def _services_in(
    config: ConfigLike, tool_specs: Mapping[str, Mapping[str, ToolSpec]] | None
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(real, stand_ins): the component names of a loaded `Config`, sorted by kind. A stand-in is a component whose
    chosen kind is one of the demo-only kinds (`backends.table.DEMO_ONLY`, the same table that makes config refuse those
    kinds outside the demo stage); a component that connects to nothing outside the process is left out; every other
    component is real. Beside the backends, a system, an egress host, a read source or a tool-manifest host that is not
    this machine is real too (`_outside_endpoints`): the made-up sentence says nothing is sent to real systems, so it is checked against
    every field that can name an endpoint, not the backends alone. An entry without a kind raises ValueError: it is
    not guessed into a list."""
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
        elif (component, kind) not in NOTHING_CONNECTED:
            real.append(component)
    real += _outside_endpoints(config, tool_specs)
    return tuple(real), tuple(stand_ins)


def banner_from_config(
    config: ConfigLike,
    names: Mapping[str, str] | None = None,
    words: BannerWords = DEFAULT_WORDS,
    *,
    tool_specs: Mapping[str, Mapping[str, ToolSpec]] | None,
) -> ModeBanner:
    """The banner of a loaded `Config`: the stage is `config.environment`, and the real services and stand-ins come
    from `config.backends.entries()`, the endpoint fields and `tool_specs` (see `_services_in`). `tool_specs` has no
    default, so forgetting it is a TypeError and never a silent "nothing real": pass the registry's `tools` (agent ->
    tool name -> spec), or None when you cannot (a configured tool module then counts as one real service). A spec
    without a `hosts` list raises `TypeError`; so does an agent entry that is not a mapping. This is the one place the
    decision is made. It RAISES when it cannot say: a screen should call `banner_or_unconfirmed`."""
    real, stand_ins = _services_in(config, tool_specs)
    return _banner_for(
        config.environment, real_services=real, stand_ins=stand_ins, names=names, words=words
    )


def banner_or_unconfirmed(
    config: ConfigLike,
    names: Mapping[str, str] | None = None,
    words: BannerWords = DEFAULT_WORDS,
    *,
    tool_specs: Mapping[str, Mapping[str, ToolSpec]] | None,
) -> dict[str, Any]:
    """What a screen should call: the finished banner as plain data (`banner_from_config(...).as_dict()`), or, when the
    banner cannot be built for any reason (a missing config field, a name that is not plain words, a spec without
    hosts), `not_confirmed(words)`. One log line names the kind of error and nothing from the config (no value, no host,
    no name). `tool_specs` is still required, so forgetting it is a TypeError at the call, before this function runs."""
    try:
        return banner_from_config(config, names, words, tool_specs=tool_specs).as_dict()
    except Exception as exc:  # noqa: BLE001 - whatever went wrong, the screen must still say something
        _LOG.warning(
            "mode banner could not be built (%s): showing the not-confirmed banner",
            type(exc).__name__,
        )
        return _not_confirmed_that_cannot_fail(words)


def _not_confirmed_that_cannot_fail(words: object) -> dict[str, Any]:
    """`not_confirmed(words)`, but built so that it cannot raise: the tag and the text of `words` are used only when both are
    non-empty texts the page script will show; otherwise (malformed `words`, a missing field, a getter that raises) the
    default words are used. The screen always gets a finished banner."""
    try:
        tag = words.not_confirmed_tag  # type: ignore[attr-defined]
        text = words.not_confirmed  # type: ignore[attr-defined]
        if all(isinstance(s, str) and 0 < len(s) <= MAX_TEXT_LENGTH for s in (tag, text)):
            return {
                "mode": "",
                "tone": "unconfirmed",
                "tag": tag,
                "text": text,
                "standins": "",
                "real": [],
                "stand_ins": [],
            }
    except Exception:  # noqa: BLE001, S110 - malformed words: fall through to the fixed defaults
        pass
    return not_confirmed(DEFAULT_WORDS)


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
