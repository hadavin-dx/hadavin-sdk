"""One TCP connect whose WHOLE time, including the look-up of the host name, is bounded.

`socket.create_connection` bounds only the connect itself: the name look-up (getaddrinfo) before it has no time limit
and a name server that does not answer can hold a caller for minutes, past any total time limit. Here the look-up
runs in a helper thread that the caller waits for at most the time given; a look-up that is still running then is left
to finish on its own (it holds no connection and no secret) and the caller gets a TimeoutError. At most LOOKUP_HUNG_MAX
look-up threads run at once, counted from the moment a caller reserves a place (under a lock, before the thread
starts) until the thread ends, whether or not its caller still waits: while that many run, a new look-up is refused at
once with the same TimeoutError and no thread is started. An IP address written out in digits (no `%` zone), in any
form the system accepts (127.0.0.1, 127.1, 0x7f.1, 2130706433, a form with a leading zero, ::1), is decided by the
system itself with the flag AI_NUMERICHOST, which never asks a name server, so it cannot hang; it needs no
look-up thread. The name `localhost` is answered by the calling thread at once with ONE address, 127.0.0.1 (IPv4
only; the IPv6 address ::1 is not invented for it, so a refused ::1 can never replace a time-out); the cap never
refuses either.
When several addresses are tried and one ends in a time-out, that time-out is the error raised even if a later address
is refused, so a run with a total time limit ends with the time-out.

Whatever the look-up raises, the caller gets an OSError and nothing is written to stderr: a name the look-up refuses
(`getaddrinfo` raises UnicodeError for a label of more than 63 characters, an empty label or a lone surrogate) and a
name the system does not know (a gaierror: the empty name, `example.test.`) end the same way, as
OSError(LOOKUP_REFUSED_TEXT), ONE fixed text with no host name, no error number and no Python class name in it. The
same text is raised for a look-up that returns no address."""

from __future__ import annotations

import contextlib
import socket
import threading
import time
from typing import Any

from lead_desk.constants import CONNECT_PER_ADDRESS_SECONDS, LOOKUP_HUNG_MAX

LOOKUP_TEXT = "the look-up of the host name took longer than the time limit"
LOOKUP_REFUSED_TEXT = "the host name cannot be looked up"  # the ONE text for every look-up that fails in any other way

# Real constants, taken once: the digit-address answer must not depend on the module attribute `socket`, which tests
# replace with a stand-in.
_AF_INET, _STREAM, _TCP = socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP
_NUMERIC_ONLY = socket.AI_NUMERICHOST
_getaddrinfo = socket.getaddrinfo  # the real function, taken once (tests replace `netconnect.socket`)

_lock = threading.Lock()
_count = {"running": 0}  # look-up threads reserved or running (waited for or not); changed only under _lock


def hung_lookups() -> int:
    """How many look-up threads are running now (never more than LOOKUP_HUNG_MAX). The name is from r7h, when only
    look-ups that nobody waited for any more were counted."""
    with _lock:
        return _count["running"]


def _without_lookup(host: str, port: int) -> list[Any] | None:
    """The answer for an address in digits and for `localhost`, without a look-up thread; None for any other name.
    `localhost` gives 127.0.0.1 only. A digit address is decided by the system (AI_NUMERICHOST: it never asks a name
    server and never waits), so every form it accepts (127.1, 0x7f.1, 2130706433, a leading-zero form) is answered
    here."""
    if host.isascii() and host.lower() == "localhost":
        return [(_AF_INET, _STREAM, _TCP, "", ("127.0.0.1", port))]
    if not host or not host.isascii() or "%" in host:  # a zone name (fe80::1%eth0) needs the system: the normal look-up
        return None
    try:
        found = _getaddrinfo(host, port, type=_STREAM, flags=_NUMERIC_ONLY)
    except (OSError, ValueError, UnicodeError):  # not a digit address: the normal look-up (and its one refusal text)
        return None
    return list(found) or None


def resolve_bounded(host: str, port: int, seconds: float) -> list[Any]:
    """The addresses of `host` for a stream connection; TimeoutError when the look-up needs more than `seconds`, and
    at once, with no new thread, while LOOKUP_HUNG_MAX look-up threads are running."""
    direct = _without_lookup(host, port)
    if direct is not None:
        return direct
    box: list[Any] = []
    done = threading.Event()
    state = {"finished": False, "released": False}  # changed only under _lock

    def work() -> None:
        # suppress(BaseException): the thread never ends with an exception, so threading.excepthook cannot print a
        # traceback (it would hold the host name) whatever the look-up raises; a non-OSError leaves the box empty
        with contextlib.suppress(BaseException):
            try:
                box.append(socket.getaddrinfo(host, port, type=socket.SOCK_STREAM))
            except OSError:  # a gaierror too ("Name or service not known", the empty name, `example.test.`)
                box.append(OSError(LOOKUP_REFUSED_TEXT))
        with _lock:
            state["finished"] = True
            if not state["released"]:  # the place goes back exactly once, here or where the thread failed to start
                state["released"] = True
                _count["running"] -= 1
        done.set()

    with _lock:
        if _count["running"] >= LOOKUP_HUNG_MAX:
            raise TimeoutError(LOOKUP_TEXT)
        # reserved BEFORE the thread starts, so concurrent callers cannot pass the check together
        _count["running"] += 1
    try:
        threading.Thread(target=work, name="name-lookup", daemon=True).start()
    except BaseException:  # the thread did not start (or failed after it began): the place goes back, once
        with _lock:
            if not state["released"]:
                state["released"] = True
                _count["running"] -= 1
        raise
    if not done.wait(max(seconds, 0.0)):
        with _lock:
            if not state["finished"]:
                raise TimeoutError(LOOKUP_TEXT)
    result = box[0] if box else None
    if result is None:
        raise OSError(LOOKUP_REFUSED_TEXT)
    if isinstance(result, OSError):
        raise result
    found: list[Any] = result
    return found


def connect_bounded(host: str, port: int, seconds: float) -> socket.socket:
    """A connected socket to host:port; look-up and connect together take at most `seconds` (TimeoutError otherwise).
    The addresses are tried in order. THE RULE: each address gets min(CONNECT_PER_ADDRESS_SECONDS, the time left
    divided by the number of addresses not yet tried, this one included), except the last address, which gets all the
    time left. So every address gets a turn while the total limit holds (an address that never answers cannot use more
    than its even share), and a host with one address keeps the whole limit.
    When none works: the time-out if any address ended in one (it wins over a later refusal), else the error of the
    last address. The socket is closed on any exception."""
    deadline = time.monotonic() + seconds
    last: OSError | None = None
    timeout: TimeoutError | None = None
    addresses = resolve_bounded(host, port, seconds)
    for index, (family, kind, proto, _name, address) in enumerate(addresses):
        left = deadline - time.monotonic()
        if left <= 0:
            raise TimeoutError(LOOKUP_TEXT)
        still = len(addresses) - index  # addresses not yet tried, this one included
        own = left if still == 1 else min(CONNECT_PER_ADDRESS_SECONDS, left / still)
        sock: socket.socket | None = None
        try:  # the socket is made INSIDE the try: a family this machine lacks (errno 97) fails this address only
            sock = socket.socket(family, kind, proto)
            sock.settimeout(own)
            sock.connect(address)
            return sock
        except BaseException as e:  # closed on ANY exception (also KeyboardInterrupt); only an OSError tries the next
            if sock is not None:
                sock.close()
            if not isinstance(e, OSError):
                raise
            last = e
            if isinstance(e, TimeoutError):
                timeout = e
    raise timeout or last or OSError(LOOKUP_REFUSED_TEXT)  # a look-up with no address: the same ONE text
