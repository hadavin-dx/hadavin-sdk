"""Who may reach a server this deployment starts: a server that holds a real service stays on this computer.

A process that listens on a network address can be called by any program that reaches that address. If the same
process also holds a real service (a real model, store, channel, secrets manager, source or system, as opposed to a
stand-in that only exists for the demo stage), a stranger could use the process to act on that service. So a
bind that other computers can reach is refused whenever a real service is configured; a bind on this computer
(see ``netguard.is_loopback_host``) is always fine, and so is any bind while every kind is a stand-in.

``listen`` is the one place in the package that creates a server socket. It asks first and builds the server
second, so a server cannot be started without the question being asked (a repo test reads every ``.py`` file of
``src``, ``demos`` and ``tools`` and fails on any other server socket). Both the check and the bind never look a
name up (the standard server's own reverse lookup of the bound address is replaced): ``localhost`` is turned into ``127.0.0.1`` before the socket exists, and any other host must be an IP
address written out.

A person who really needs a bind that other computers can reach with a real service (a container behind a proxy
that must listen on every address) says so with ``allow_public_bind_reason``: a short printable sentence. It is
written to the log (WARNING, logger ``hadavin_sdk.bindguard``) together with the services it lets through. No audit
sink is reachable from here without a new dependency, so the log line is the record.

The list of stand-ins is not written here. It is read from the backend table (``DEMO_ONLY``, ``NOT_PROD`` and
``IN_PROCESS`` in ``backends/table.py``), so a new kind is a real service unless the table says it reaches none; the
test ``tests/test_bindguard.py`` pins every kind of the table to one answer, so adding a kind cannot slip through.
"""

from __future__ import annotations

import logging
import socket
import socketserver
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

_LOG = logging.getLogger("hadavin_sdk.bindguard")


class BindRefused(ConfigError):
    """A bind that other computers can reach was asked for while a real service is configured."""


def stand_in_kinds() -> frozenset[tuple[str, str]]:
    """The (capability, kind) pairs that reach no real service, from the backend table: the stand-ins (DEMO_ONLY,
    NOT_PROD) and the kinds that run inside the process (IN_PROCESS)."""
    return DEMO_ONLY | NOT_PROD | IN_PROCESS


def real_services(config: Config) -> tuple[str, ...]:
    """The configured things that reach a real service, or that could (custom code), each named in words
    ("backends.llm: anthropic", "system billing", "source cluster", "tools:my_tools"); empty when everything is a
    stand-in. Only the loaded ``Config`` is read: nothing outside it is known here.

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


def _shown(bind: object) -> str:
    """The bind as it is shown in a sentence: only readable text, at most ``BIND_SHOWN_MAX_CHARS`` characters."""
    if not (isinstance(bind, str) and bind.isprintable()):
        return "(unreadable)"
    limit = defaults.BIND_SHOWN_MAX_CHARS
    return bind if len(bind) <= limit else bind[:limit] + "..."


def reason_problem(reason: object) -> str | None:
    """None when ``reason`` is a usable reason for a public bind (text, not empty after trimming, printable, at most
    ``BIND_REASON_MAX_CHARS`` characters); otherwise the sentence that says why not."""
    limit = defaults.BIND_REASON_MAX_CHARS
    if not isinstance(reason, str):
        return "allow_public_bind_reason must be text"
    text = reason.strip()
    if not text:
        return "allow_public_bind_reason must say why, in a few words"
    if len(text) > limit or not text.isprintable():
        return f"allow_public_bind_reason must be one printable line of at most {limit} characters"
    return None


def public_bind_problem(bind: object, config: Config) -> str | None:
    """None when the bind is fine; otherwise the sentence that says why it is refused. Anything that is not a
    readable host (not text, empty) counts as a bind other computers can reach."""
    real = real_services(config)
    if not real or is_loopback_host(bind):
        return None
    return (
        f"bind {_shown(bind)!r} can be reached from other computers while a real service is configured "
        f"({', '.join(real)}): a stranger who reaches the port could act on it. Bind to a loopback address "
        "(127.0.0.1 or ::1) and put your own sign-in in front, use only stand-ins, or, if the server really must "
        "be reachable (for example behind your own proxy), pass allow_public_bind_reason with the reason"
    )


def require_safe_bind(
    bind: object, config: Config, *, allow_public_bind_reason: str | None = None
) -> None:
    """Raise BindRefused with the sentence from ``public_bind_problem``, unless a valid
    ``allow_public_bind_reason`` was given (then the reason is logged and the bind is let through). A reason that
    is not valid is refused even when it was not needed. Servers call this before they listen."""
    if allow_public_bind_reason is not None and (bad := reason_problem(allow_public_bind_reason)):
        raise BindRefused(bad)
    if (problem := public_bind_problem(bind, config)) is None:
        return
    if allow_public_bind_reason is None:
        raise BindRefused(problem)
    _LOG.warning(
        "public bind %s allowed with a real service configured (%s); reason: %s",
        _shown(bind),
        ", ".join(real_services(config)),
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
) -> ThreadingHTTPServer:
    """The one place in the package that creates a server socket. Refuses a bind that other computers can reach
    while a real service is configured (see ``require_safe_bind``; ``allow_public_bind_reason`` is the named, logged
    way past that), refuses a host that is not an IP address written out or ``localhost``, binds an IPv6 address
    on an IPv6 socket, and checks the address the socket really got. Nothing is looked up. The caller runs
    ``serve_forever()`` on the result."""
    require_safe_bind(host, config, allow_public_bind_reason=allow_public_bind_reason)
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
        and real_services(config)
        and not is_loopback_host(server.server_address[0])
    ):
        server.server_close()
        raise BindRefused(
            f"the server got address {_shown(server.server_address[0])!r}, which is not on this computer"
        )
    return server


__all__ = [
    "BindRefused",
    "listen",
    "public_bind_problem",
    "real_services",
    "reason_problem",
    "require_safe_bind",
    "stand_in_kinds",
]
