"""The one rule for "this computer", in a module that imports only the standard library.

Why it is its own file: the two raw-socket stand-ins (demo_only/fake_imap.py, demo_only/fake_smtp_tls.py) refuse a
listening host that is not this computer BEFORE they open a socket. They used to get that refusal through
demo_only/bad_request.py, which pulls in the desk's settings, the HTTP guard and the command-line parser. Now the rule
sits here and nothing else is loaded with it. `lead_desk.config.is_loopback_host` and `demo_only.bad_request` hand out
these same objects (one source of truth, there is no second copy).

What the rule says, by design: a host is "this computer" when it is `localhost` (any letter case) or a loopback
address (127.x, ::1, ::ffff:127.x; brackets allowed). So `LOCALHOST` is accepted. The rule only judges the spelling of
a name. It does not open a socket and does not promise that anything will listen there; a name such as `localhost`
is later resolved by the system. It fails closed: anything that is not text, a blank, a wildcard such as 0.0.0.0 or ::,
a scope id (::1%eth0) and every other address or name is not this computer."""

from __future__ import annotations

import ipaddress

LOOPBACK_HOST_TEXT = "must be this computer: localhost or 127.0.0.1"


def is_loopback_host(name: str) -> bool:
    """True for localhost and for a loopback address (brackets allowed); a wildcard, a name or any other address is
    reachable from, or reaches, other computers. Fails closed: anything it cannot read is not loopback."""
    if name.lower() == "localhost":
        return True
    bare = name[1:-1] if name.startswith("[") and name.endswith("]") else name
    if "[" in bare or "]" in bare or "%" in bare:  # one bracket, or a scope id (::1%eth0): not a plain address
        return False
    try:
        ip = ipaddress.ip_address(bare)
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped  # the same answer on every Python version (3.13 changed is_loopback for mapped forms)
    return ip.is_loopback


def require_loopback_host(host: object) -> str:
    """The one refusal of a fake's listening host: only this computer (localhost or a loopback address). An empty or
    blank host is refused too (to a socket an empty host means "every interface"); fails closed on anything that is not
    text. Every fake (the three web fakes through QuietServer, the two mail fakes directly) calls this before it makes
    a socket."""
    if not isinstance(host, str) or not is_loopback_host(host):
        raise ValueError(LOOPBACK_HOST_TEXT)
    return host
