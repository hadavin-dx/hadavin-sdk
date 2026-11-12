"""Who may reach a server this deployment starts: a server that holds a real service stays on this computer.

A process that listens on a network address can be called by any program that reaches that address. If the same
process also holds a real service (a real model, store, channel, secrets manager, source or system, as opposed to a
stand-in that only exists for the demo stage), a stranger could use the process to act on that service. So a
bind that other computers can reach is refused whenever a real service is configured; a bind on this computer
(see ``netguard.is_loopback_host``) is always fine, and so is any bind while every kind is a stand-in.

``listen`` is the one place in the package that creates a server socket. It asks first and builds the server
second, so a server cannot be started without the question being asked (a repo test reads every ``.py`` file of
``src``, ``demos`` and ``tools`` and fails on every form of server it lists: the standard server classes, bind and
listen calls, ``multiprocessing`` listeners, ``http.server.test``, datagram endpoints, aiohttp sites, a ``.run(host=...)``
call and the import of a module that only serves, with import aliases resolved; the list is of forms, not proof that no
other form exists; a run-time test also checks that only ``listen`` reaches a socket bind). Both the check and the bind never look a
name up (the standard server's own reverse lookup of the bound address is replaced): ``localhost`` is turned into ``127.0.0.1`` before the socket exists, and any other host must be an IP
address written out.

A person who really needs a bind that other computers can reach with a real service (a container behind a proxy
that must listen on every address) says so with ``allow_public_bind_reason``: a short printable sentence. It is
written to the log (WARNING, logger ``hadavin_sdk.bindguard``) together with the services it lets through. It is a
log line, not an audit record: no audit sink is reachable from here without a new dependency.

The list of stand-ins is not written here. It is read from the backend table (``DEMO_ONLY``, ``NOT_PROD`` and
``IN_PROCESS`` in ``backends/table.py``), so a new kind is a real service unless the table says it reaches none; the
test ``tests/test_bindguard.py`` pins every kind of the table to one answer, so adding a kind cannot slip through.
"""

from __future__ import annotations

import logging
import socket
import socketserver
from collections.abc import Mapping
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from hadavin_sdk import defaults
from hadavin_sdk.backends.table import DEMO_ONLY, IN_PROCESS, NOT_PROD
from hadavin_sdk.config import Config
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.netguard import (
    LOOPBACK_V4,
    is_localhost_name,
    is_loopback_host,
    is_loopback_literal,
    parse_ip_literal,
)
from hadavin_sdk.standins import is_stand_in

_LOG = logging.getLogger("hadavin_sdk.bindguard")


class BindRefused(ConfigError):
    """A bind that other computers can reach was asked for while a real service is configured."""


def stand_in_kinds() -> frozenset[tuple[str, str]]:
    """The (capability, kind) pairs that reach no real service, from the backend table: the stand-ins (DEMO_ONLY,
    NOT_PROD) and the kinds that run inside the process (IN_PROCESS)."""
    return DEMO_ONLY | NOT_PROD | IN_PROCESS


# The core's own stand-in classes are the literal list in ``hadavin_sdk.standins`` (looked up in the module that holds
# them, exact class only, pinned; never a name, never a subclass).

# held services whose emptiness decides: an empty ``tools`` or ``sources`` mapping holds nothing
_COUNTED_WHEN_NOT_EMPTY = frozenset({"tools", "sources"})


def is_stand_in_object(obj: object) -> bool:
    """True only for an object whose exact class is one of the core's own stand-ins (looked up by module and
    name, pinned, instance scanned: see ``hadavin_sdk.standins``), or a detector list (``AnyOf``) whose entries all
    are. Anything else, including a subclass or a class of the same name, is real. Never raises."""
    return is_stand_in(obj)


def config_services(config: Config) -> tuple[str, ...]:
    """The things the loaded ``Config`` reaches that are real, or could be (custom code), each named in words
    ("backends.llm: anthropic", "system billing", "source cluster", "tools:my_tools"); empty when everything is
    a stand-in. The config is read once and the answer kept by whoever needs it (``Approvals`` freezes it at
    construction, because the containers of a ``Config`` can be changed after it is built).

    * a backend kind is real unless the backend table lists it as a stand-in or as running inside the process;
    * a system is real unless its address is plain http to this computer and the config allows that
      (``allow_insecure_loopback``, the local test setup);
    * a configured read source is always real (it reads a live system);
    * every module of ``tool_modules`` and of ``check_modules`` counts (``tools:<module>``, ``checks:<module>``):
      custom code in the process can open any connection, so a non-empty list is not "everything is a stand-in";
    * every ``egress_hosts`` entry that is not a loopback host counts (``egress <host>``): the process is set up to
      reach the outside, and an entry that cannot be read as a host counts too (fail closed)."""
    stand_ins = stand_in_kinds()
    found = [
        f"backends.{cap}: {s.kind}"
        for cap, s in config.backends.entries()
        if (cap, s.kind) not in stand_ins
    ]
    for name, system in config.systems.items():
        parts = urlsplit(system.base_url)
        local = (
            config.allow_insecure_loopback
            and parts.scheme == "http"
            and is_loopback_literal(parts.hostname)
        )
        if not local:
            found.append(f"system {name}")
    found += [f"source {name}" for name in config.sources]
    found += [f"tools:{module}" for module in config.tool_modules]
    found += [f"checks:{module}" for module in config.check_modules]
    found += [
        f"egress {_shown(host)}"
        for host in sorted(config.egress_hosts)
        if not is_loopback_host(host)
    ]
    return tuple(found)


def _is_empty_mapping(obj: object) -> bool:
    """True only for a plain empty ``dict``. Any other object (a lazy mapping, a proxy, a subclass) is not read:
    its own ``__bool__`` or ``__len__`` is foreign code that could say "empty" or raise."""
    return type(obj) is dict and not dict.__len__(obj)


def held_services_found(held: Mapping[str, object] | None) -> tuple[str, ...]:
    """The held objects that count (``held <name>: <class>``): every one unless its exact class is one of the
    core's own stand-ins (``is_stand_in_object``); a held ``tools`` or ``sources`` mapping counts (``held tools``)
    unless it is a plain empty dict; nothing held (``None``) counts for nothing. A held mapping, a key or an object
    that raises or cannot be read while it is looked at counts (fail closed): the error is not passed on, whatever
    the object is."""
    try:
        items = sorted(
            (held or {}).items(), key=lambda item: item[0] if type(item[0]) is str else "\uffff"
        )
    except Exception:  # noqa: BLE001 - a mapping that cannot be read is not nothing
        return ("held (unreadable)",)
    found: list[str] = []
    for name, obj in items:
        if obj is None:
            continue
        try:
            counted_if_not_empty = name in _COUNTED_WHEN_NOT_EMPTY
            label = (
                f"held {_shown(name)}"
                if counted_if_not_empty
                else f"held {_shown(name)}: {_shown(type(obj).__name__)}"
            )
            counts = (
                not _is_empty_mapping(obj) if counted_if_not_empty else not is_stand_in_object(obj)
            )
        except Exception:  # noqa: BLE001 - an object or a key that cannot be read is not a stand-in
            # a fixed label: the key is hostile, so nothing is called on it again (not even ``_shown``)
            label, counts = "held (unreadable)", True
        if counts:
            found.append(label)
    return tuple(found)


def real_services(
    config: Config,
    held: Mapping[str, object] | None,
    frozen: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """``config_services(config)`` and ``held_services_found(held)`` together: what is real now, each named in
    words; empty when everything is a stand-in. ``held`` is the objects a server really holds
    (``Approvals.held_services()``: the channel, the detector and the store it was built with, and every override
    given to ``build()``). The config alone is not the truth: a stand-in config can sit beside a real object put
    in by hand.
    ``frozen`` is what the caller already knows is real (``Approvals.config_facts``: the config as it was when
    the approvals were made, because the lists of a ``Config`` can be changed afterwards); the three are joined
    without repeats."""
    return tuple(dict.fromkeys(frozen + config_services(config) + held_services_found(held)))


def _shown(bind: object) -> str:
    """The bind as it is shown in a sentence: only readable text, at most ``BIND_SHOWN_MAX_CHARS`` characters."""
    if not (isinstance(bind, str) and bind.isprintable()):
        return "(unreadable)"
    limit = defaults.BIND_SHOWN_MAX_CHARS
    return bind if len(bind) <= limit else bind[:limit] + "..."


def reason_problem(reason: object) -> str | None:
    """None when ``reason`` is a usable reason for a public bind (text, at least ``BIND_REASON_MIN_CHARS`` characters
    after trimming, printable, at most ``BIND_REASON_MAX_CHARS``); otherwise the sentence that says why not. The
    reason is written to the log at WARNING; it is not an audit record."""
    limit = defaults.BIND_REASON_MAX_CHARS
    if not isinstance(reason, str):
        return "allow_public_bind_reason must be text"
    text = reason.strip()
    if len(text) < defaults.BIND_REASON_MIN_CHARS:
        return (
            f"allow_public_bind_reason must say why, in at least {defaults.BIND_REASON_MIN_CHARS} "
            "characters"
        )
    if len(text) > limit or not text.isprintable():
        return f"allow_public_bind_reason must be one printable line of at most {limit} characters"
    return None


def public_bind_problem(
    bind: object,
    config: Config,
    held: Mapping[str, object] | None,
    frozen: tuple[str, ...] = (),
) -> str | None:
    """None when the bind is fine; otherwise the sentence that says why it is refused. Anything that is not a
    readable host (not text, empty) counts as a bind other computers can reach. ``held``: see ``real_services``."""
    real = real_services(config, held, frozen)
    if not real or is_loopback_host(bind):
        return None
    return (
        f"bind {_shown(bind)!r} can be reached from other computers while a real service is configured "
        f"({', '.join(real)}): a stranger who reaches the port could act on it. Bind to a loopback address "
        "(127.0.0.1 or ::1) and put your own sign-in in front, use only stand-ins, or, if the server really must "
        "be reachable (for example behind your own proxy), pass allow_public_bind_reason with the reason"
    )


def require_safe_bind(
    bind: object,
    config: Config,
    *,
    allow_public_bind_reason: str | None = None,
    held: Mapping[str, object] | None,
    frozen: tuple[str, ...] = (),
) -> None:
    """Raise BindRefused with the sentence from ``public_bind_problem``, unless a valid
    ``allow_public_bind_reason`` was given (then the reason is logged and the bind is let through). A reason that
    is not valid is refused even when it was not needed. Servers call this before they listen."""
    if allow_public_bind_reason is not None and (bad := reason_problem(allow_public_bind_reason)):
        raise BindRefused(bad)
    if (problem := public_bind_problem(bind, config, held, frozen)) is None:
        return
    if allow_public_bind_reason is None:
        raise BindRefused(problem)
    _LOG.warning(
        "public bind %s allowed with a real service configured (%s); reason: %s",
        _shown(bind),
        ", ".join(real_services(config, held, frozen)),
        allow_public_bind_reason.strip(),
    )


def _literal(host: object) -> tuple[str, int]:
    """The address to bind and its family: ``localhost`` (any letter case) becomes ``127.0.0.1``; an IP address
    written out is kept (square brackets round an IPv6 address are removed); anything else (another name, an empty
    text, a scope id, not text) is refused, because binding a name would look it up."""
    if is_localhost_name(host):
        return LOOPBACK_V4, socket.AF_INET
    if (ip := parse_ip_literal(host)) is not None:
        # a written-out address: the text without the brackets of the URL form is what the socket takes
        return str(ip), socket.AF_INET6 if ip.version == 6 else socket.AF_INET
    raise BindRefused(
        f"bind {_shown(host)!r} is not an IP address written out (or localhost): a server binds an address, it "
        "does not look a name up"
    )


def listen(
    config: Config,
    host: str,
    port: int,
    handler: type[BaseHTTPRequestHandler],
    *,
    allow_public_bind_reason: str | None = None,
    held: Mapping[str, object] | None,
    frozen: tuple[str, ...] = (),
) -> ThreadingHTTPServer:
    """The one place in the package that creates a server socket. Refuses a bind that other computers can reach
    while a real service is configured (see ``require_safe_bind``; ``allow_public_bind_reason`` is the named, logged
    way past that), refuses a host that is not an IP address written out or ``localhost``, binds an IPv6 address
    on an IPv6 socket, and checks the address the socket really got (when no reason was given and a real service is
    present). ``held`` is required (pass ``{}`` for "holds nothing"): what the server really holds, see
    ``real_services``. Nothing is looked up. The caller runs
    ``serve_forever()`` on the result."""
    require_safe_bind(
        host, config, allow_public_bind_reason=allow_public_bind_reason, held=held, frozen=frozen
    )
    address, family = _literal(host)

    class _Server(ThreadingHTTPServer):
        address_family = family

        def server_bind(self) -> None:
            # the standard HTTPServer asks the resolver for the name of the address it just bound
            # (socket.getfqdn); this one keeps the literal, so no name is looked up on any path
            socketserver.TCPServer.server_bind(self)
            host, port = self.server_address[:2]
            self.server_name, self.server_port = str(host), port

    server = _Server((address, port), handler)
    if (
        allow_public_bind_reason is None
        and real_services(config, held, frozen)
        and not is_loopback_host(server.server_address[0])
    ):
        server.server_close()
        raise BindRefused(
            f"the server got address {_shown(server.server_address[0])!r}, which is not on this computer"
        )
    return server


__all__ = [
    "BindRefused",
    "config_services",
    "held_services_found",
    "is_stand_in_object",
    "listen",
    "public_bind_problem",
    "real_services",
    "reason_problem",
    "require_safe_bind",
    "stand_in_kinds",
]
