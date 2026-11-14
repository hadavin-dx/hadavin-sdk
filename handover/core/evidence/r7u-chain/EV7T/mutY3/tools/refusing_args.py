"""One command-line parser for every script that takes options
(scripts/, load_tools/, demo_only/): a bad command line ends in ONE fixed refusal line and
nothing that was typed is ever printed back.

Why (bug class: text typed by the person is echoed back, or an exception name is shown, instead of a fixed refusal):
argparse's own error texts repeat the typed words (`invalid int value: '<x>'`, `unrecognized arguments: <x>`,
`invalid choice: '<x>'`, `ignored explicit argument '<x>'`, `ambiguous option: <x>`). A person who pastes a key or an
address into the wrong place would see it printed in the terminal and in its scroll-back. Rule broken: a secret is
never printed (the studio rule `no hardcoding, no secrets`; the same reason the check scripts never print the key).
The fix sits here, at the one place every script's parse errors pass through: `RefusingParser.error`.

The line is `refused: <OPTION>: <fixed text>` on standard output, exit code 2. The OPTION slot holds an option name that
matches `--[a-z][a-z0-9-]*` (an option name given by the script, never typed text) or `the arguments`.

The argument types of this module are the ONE way a script reads a typed number or address: `bounded_int` and
`bounded_float` (a limit on both sides, a finite number) and `http_address` (an http or https address that can be split,
with the loopback rule where the script has one). A script option that takes a number or an address must use one of
them, never a bare `type=int`, `type=float` or a text that is later given to `urlsplit` or an opener; the
scan in `tests/test_script_number_limits.py` reads every script and fails for a bare `type=int` or `type=float`."""

from __future__ import annotations

import errno
import ipaddress
import math
import re
import socket
import sys
import unicodedata
from argparse import ArgumentParser, ArgumentTypeError
from collections.abc import Callable
from pathlib import Path
from typing import NoReturn
from urllib.parse import urlsplit

try:  # started as a script without the src folder on the path: it is added (the exit codes live in constants.py)
    from lead_desk.constants import EXIT_REFUSED, EXIT_UNREACHABLE, LOOPBACK_HOSTS
    from lead_desk.envnum import read_number
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from lead_desk.constants import EXIT_REFUSED, EXIT_UNREACHABLE, LOOPBACK_HOSTS
    from lead_desk.envnum import read_number

__all__ = [
    "EXIT_REFUSED",
    "EXIT_UNREACHABLE",
    "RefusingParser",
    "bounded_float",
    "bounded_int",
    "http_address",
    "LOOPBACK_HOST_TEXT",
    "loopback_host",
    "require_loopback",
    "listen_refusal",
    "refusal",
]
OPTION_NAME = re.compile(r"--[a-z][a-z0-9-]*(/--[a-z][a-z0-9-]*)*")
# the fixed texts of a script's own argument types (`argparse.ArgumentTypeError` messages): shown as they are
TYPE_TEXTS = ("is not a number", "needs ID=IN_PRICE,OUT_PRICE")
# the fixed text of `bounded_int`: only the two limits the script gave (never a typed word) are in it
BOUNDED_INT_TEXT = re.compile(r"must be a whole number from -?\d+ to \d+")
# the fixed text of `bounded_float`: only the two limits the script gave are in it
BOUNDED_FLOAT_TEXT = re.compile(r"must be a number from -?[0-9.e+-]+ to [0-9.e+-]+")
# the fixed texts of `http_address`
ADDRESS_TEXT = "must be an http or https address (for example http://127.0.0.1:8765)"
LOOPBACK_ADDRESS_TEXT = "must be an http address on this computer (127.0.0.1 or localhost)"
LOOPBACK_HOST_TEXT = "must be this computer: localhost or 127.0.0.1"


# the fixed texts a script passes to `parser.error()` itself (no typed word in them): shown under their own option names
SCRIPT_TEXTS = {"give exactly one of --index or --all": "refused: --index, --all: give exactly one of them"}


def refusal(option: str, text: str) -> str:
    """The one refusal line."""
    return f"refused: {option}: {text}"


def bounded_int(low: int, high: int) -> Callable[[str], int]:
    """An argparse `type=` for a whole number from `low` to `high` (both included). Anything else (a word, a number
    that is too small or too big, `nan`, `1e999`, a text of thousands of digits) is refused with one fixed text that
    holds only the two limits. Why: `type=int` lets a number like 99999 reach `socket.bind` (an OverflowError
    traceback) or `0` reach `threading.Barrier(0)` (a ValueError traceback)."""
    text = f"must be a whole number from {low} to {high}"

    def parse(value: str) -> int:
        try:
            number = read_number(value, int)  # the one ASCII-only reader: no `1_0`, no other-script digits, no spaces
        except ValueError:  # also a text of more than 4300 digits
            raise ArgumentTypeError(text) from None
        if not low <= number <= high:
            raise ArgumentTypeError(text)
        return number

    return parse


def listen_refusal(error: OSError, has_host_option: bool = True) -> str:
    """The one refusal line for a server that could not listen: a host name that cannot be looked up, or an address that
    is not one of this computer's, names `--host`; anything else (the port is in use, or not allowed) names `--port`.
    Never the typed words, never the system's own text. Why: asyncio and socketserver let the OSError of the bind
    through, which ended the script in a traceback."""
    if has_host_option and (isinstance(error, socket.gaierror) or error.errno == errno.EADDRNOTAVAIL):
        return refusal("--host", "is not an address of this computer")
    return refusal("--port", "cannot be listened on (it is already in use, or not allowed)")


def bounded_float(low: float, high: float) -> Callable[[str], float]:
    """An argparse `type=` for a finite number from `low` to `high` (both included). `nan`, `inf`, `1e999` (it reads
    as infinity), a word, or a number outside the limits is refused with one fixed text that holds only the limits.
    Why: `float("1e999")` is infinity, which turns a ceiling off without a word (`--max-503-rate 1e999`)."""
    text = f"must be a number from {low:g} to {high:g}"

    def parse(value: str) -> float:
        try:
            number = read_number(value, float)
        except ValueError:
            raise ArgumentTypeError(text) from None
        if not math.isfinite(number) or not low <= number <= high:
            raise ArgumentTypeError(text)
        return number

    return parse


ADDRESS_LABEL_MAX = 63  # the longest part of a host name between two points (the standard for names)
ADDRESS_HOST_MAX = 253  # the longest host name
PORT_LOW, PORT_HIGH = 1, 65535  # a port written in an address: 0 is "any port" for a listener, not a place to send to
_ADDRESS_LABEL = re.compile(r"[A-Za-z0-9_]([A-Za-z0-9_-]*[A-Za-z0-9_])?")  # ASCII letters, digits, _ and - inside


def _host_problem(host: str) -> bool:
    """True when `host` (as urlsplit gives it, lower case, no brackets) is not a plain ASCII host name or address."""
    if not host or not host.isascii() or len(host) > ADDRESS_HOST_MAX:
        return True
    if ":" in host:  # an IPv6 address: the standard library says whether it is one
        try:
            ipaddress.IPv6Address(host.split("%", 1)[0])
        except ValueError:
            return True
        return False
    return any(not _ADDRESS_LABEL.fullmatch(label) or len(label) > ADDRESS_LABEL_MAX for label in host.split("."))


def http_address(allowed_hosts: tuple[str, ...] | None = None) -> Callable[[str], str]:
    """An argparse `type=` for a web address a script will open. THE one parser of an address argument (load_driver,
    burst, hubspot_probe, run_real_check, feed, n8n_api): http or https only (never file:, ftp: or data:, which the
    default opener of urllib would also open: a file: address that names a pipe waits for ever), plain ASCII with no
    space or control character, text that `urlsplit` can split (`http://[::1` cannot), NO user name or password
    (`http://127.0.0.1:1@evil` is a request to `evil`, with `127.0.0.1` read as the user name), a host that is a real
    host name or address with labels of at most 63 characters, and a port, when there is one, from 1 to 65535.
    With `allowed_hosts` (the loopback names in constants.LOOPBACK_HOSTS; brackets of an IPv6 name are ignored) the
    scheme must be http and the host one of those names: a script that talks only to this computer cannot be pointed
    at another one (a lead, a key or a mail would go there). One fixed text; the typed address is never repeated.
    Returns the text as it was typed."""
    problem = LOOPBACK_ADDRESS_TEXT if allowed_hosts is not None else ADDRESS_TEXT
    allowed = None if allowed_hosts is None else {h.strip("[]").lower() for h in allowed_hosts}

    def parse(value: str) -> str:
        if not value.isascii() or any(unicodedata.category(c) in ("Cc", "Zs", "Zl", "Zp") for c in value):
            raise ArgumentTypeError(problem)
        try:
            parts = urlsplit(value)
            port = parts.port  # reading the port raises ValueError for a word or a number above 65535
        except ValueError:
            raise ArgumentTypeError(problem) from None
        if parts.scheme.lower() not in ("http", "https") or "@" in parts.netloc:
            raise ArgumentTypeError(problem)
        host = parts.hostname or ""
        if _host_problem(host) or (port is not None and not PORT_LOW <= port <= PORT_HIGH):
            raise ArgumentTypeError(problem)
        if allowed is not None and (parts.scheme.lower() != "http" or host not in allowed):
            raise ArgumentTypeError(problem)
        return value

    return parse


def loopback_host(value: str) -> str:
    """An argparse `type=` for the `--host` of a script that LISTENS (the mail catcher and the stand-in servers):
    `localhost` or a loopback address (constants.LOOPBACK_HOSTS, with or without brackets), nothing else. A listener
    that is not on a loopback address takes requests from other computers, and these stand-ins have no sign-in. Why a
    check and not the system's answer: an empty `--host` and the all-interfaces address are valid to the system and
    listen on every interface. One fixed text; the typed host is never repeated (and never printed back by the
    LISTENING line)."""
    try:
        return require_loopback(value)
    except ValueError:
        raise ArgumentTypeError(LOOPBACK_HOST_TEXT) from None


def require_loopback(host: object) -> str:
    """`host` as `localhost` or a loopback address (lower case, no brackets), or a ValueError with a fixed text. The
    ONE rule behind `loopback_host` and behind the host argument of the stand-in servers' factory functions
    (demo_only/fake_model_server.py, demo_only/fakes_server.py), which have no --host option but take a host from a
    caller or a setting: a stand-in has no sign-in, so it must never listen on another address."""
    if isinstance(host, str) and host.isascii() and host.strip("[]").lower() in {h.strip("[]") for h in LOOPBACK_HOSTS}:
        return host.strip("[]").lower()
    raise ValueError(LOOPBACK_HOST_TEXT)


class RefusingParser(ArgumentParser):
    """argparse that ends a bad command line with the one refusal line (on standard output, exit 2) and never prints
    what was typed."""

    def error(self, message: str) -> NoReturn:
        if message in SCRIPT_TEXTS:
            line = SCRIPT_TEXTS[message]
        elif m := re.match(r"argument (--[a-z][a-z0-9-]*(?:/--[a-z][a-z0-9-]*)*): (.*)", message, re.DOTALL):
            what = m[2]
            if what.startswith("invalid int value"):
                text = "must be a whole number"
            elif what.startswith("invalid float value"):
                text = "must be a number"
            elif what.startswith("expected one argument"):
                text = "needs a value"
            elif what.startswith("invalid choice"):
                text = "is not one of the allowed values (see --help)"
            elif (
                what in TYPE_TEXTS
                or what in (ADDRESS_TEXT, LOOPBACK_ADDRESS_TEXT, LOOPBACK_HOST_TEXT)
                or BOUNDED_INT_TEXT.fullmatch(what)
                or BOUNDED_FLOAT_TEXT.fullmatch(what)
            ):
                text = what
            else:
                text = "cannot be used like this (see --help)"
            line = refusal(m[1], text)
        elif m := re.match(r"the following arguments are required: (.*)", message, re.DOTALL):
            names = [x.strip() for x in m[1].split(",")]
            line = refusal(", ".join(x for x in names if OPTION_NAME.fullmatch(x)) or "the arguments", "not given")
        else:  # unrecognized arguments, an ambiguous abbreviation, ...: the words typed are not repeated
            line = refusal("the arguments", "an option is unknown, ambiguous or has a stray value (see --help)")
        print(line)
        raise SystemExit(EXIT_REFUSED)
