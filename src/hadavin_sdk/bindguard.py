"""Who may reach a server this deployment starts: a server that holds a real service stays on this computer.

A process that listens on a network address can be called by any program that reaches that address. If the same
process also holds a real service (a real model, store, channel, secrets manager, source or system, as opposed to a
stand-in that only exists for the demo stage), a stranger could use the process to act on that service. So a
bind that other computers can reach is refused whenever a real service is configured; a bind on this computer
(see ``netguard.is_loopback_host``) is always fine, and so is any bind while every kind is a stand-in.

The list is not written here. It is read from the backend table (``DEMO_ONLY``, ``NOT_PROD`` and ``IN_PROCESS`` in
``backends/table.py``), so a new kind is a real service unless the table says it reaches none; the test
``tests/test_bindguard.py`` pins every kind of the table to one answer, so adding a kind cannot slip through.
"""

from __future__ import annotations

from urllib.parse import urlsplit

from hadavin_sdk.backends.table import DEMO_ONLY, IN_PROCESS, NOT_PROD
from hadavin_sdk.config import Config
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.netguard import is_loopback_host, is_loopback_literal


class BindRefused(ConfigError):
    """A bind that other computers can reach was asked for while a real service is configured."""


def stand_in_kinds() -> frozenset[tuple[str, str]]:
    """The (capability, kind) pairs that reach no real service, from the backend table: the stand-ins (DEMO_ONLY,
    NOT_PROD) and the kinds that run inside the process (IN_PROCESS)."""
    return DEMO_ONLY | NOT_PROD | IN_PROCESS


def real_services(config: Config) -> tuple[str, ...]:
    """The configured things that reach a real service, each named in words ("backends.llm: anthropic",
    "system billing", "source cluster"); empty when everything is a stand-in. One place decides it.

    * a backend kind is real unless the backend table lists it as a stand-in or as running inside the process;
    * a system is real unless its address is plain http to this computer and the config allows that
      (``allow_insecure_loopback``, the local test setup);
    * a configured read source is always real (it reads a live system)."""
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
    return tuple(found)


def public_bind_problem(bind: object, config: Config) -> str | None:
    """None when the bind is fine; otherwise the sentence that says why it is refused. Anything that is not a
    readable host (not text, empty) counts as a bind other computers can reach."""
    real = real_services(config)
    if not real or is_loopback_host(bind):
        return None
    shown = bind if isinstance(bind, str) and bind.isprintable() else "(unreadable)"
    return (
        f"bind {shown!r} can be reached from other computers while a real service is configured "
        f"({', '.join(real)}): a stranger who reaches the port could act on it. Bind to a loopback address "
        "(127.0.0.1 or ::1) and put your own sign-in in front, or use only stand-ins"
    )


def require_safe_bind(bind: object, config: Config) -> None:
    """Raise BindRefused with the sentence from ``public_bind_problem``. Servers call this before they listen."""
    if (problem := public_bind_problem(bind, config)) is not None:
        raise BindRefused(problem)
