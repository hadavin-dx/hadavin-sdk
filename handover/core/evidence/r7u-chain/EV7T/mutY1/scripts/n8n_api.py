"""Tiny n8n REST helper: import, activate, deactivate, list workflows. Needs an n8n API key in a file you name.

Run from the repository root with N8N_URL (default http://127.0.0.1:5679) and N8N_API_KEY_FILE set:
  python scripts/n8n_api.py import file.json | activate NAME | deactivate NAME | list
Workflows are addressed by NAME so no id is printed.
The key is read from the file, sent as a header, never printed.

N8N_URL must be an https address, or http to this computer (127.0.0.1, ::1, localhost): the key travels in a header and
plain http to another computer would send it unencrypted. Anything else (and an address that cannot be read) is refused
at start, before the key file is opened. To reach an n8n on another computer use https, or an SSH tunnel to 127.0.0.1.
A redirect answer is never followed (the header with the key would go to the new address); it is reported as an error.
For http to this computer the proxy settings of the environment (HTTP_PROXY, no_proxy) are ignored: the key header goes
straight to this computer, never to a proxy. For https they are used as usual.
The key file must hold one printable ASCII word of 8 to 4096 characters (no space, no second line, no control
character; a UTF-8 byte-order mark is accepted); anything else is refused at start with a fixed message that does
not show the file text.
Every failure that can come from the address, the key file, the workflow file, the network or n8n's answer ends with a
short message and an exit code: 1 n8n answered but refused the request, 2 a bad command line or a name that matches no
or several workflows, 3 n8n cannot be reached or answered something unusable, 4 a bad N8N_URL, key file or workflow
file. Never a Python traceback, and never prints the key, the address, a header, an answer body, the name of a Python
error class or a name you typed: a network or protocol fault prints one fixed line. That list is: an address that
cannot be read or is not allowed (also a port outside 1..65535),
a key file that is missing, unreadable, a directory or not one printable ASCII word of at least 8 characters, a
workflow file that is missing, not JSON, nested too deeply (RecursionError) or without a name, a workflow that cannot
be encoded, every network, TLS and protocol fault, an answer that is not JSON or is nested too deeply, a list with an
odd entry. A workflow name that the terminal cannot show is printed with "?" in place of the characters it cannot
encode. NOT covered (a traceback is possible): Ctrl-C (KeyboardInterrupt), running out of memory (MemoryError), and a
closed output pipe (BrokenPipeError).
"""

from __future__ import annotations

import http.client
import json
import os
import re
import sys
import urllib.error
import urllib.request
from http import HTTPStatus
from pathlib import Path
from typing import NoReturn
from urllib.parse import urlsplit

# insert(0) puts each entry first, so the entry added LAST ends up ahead: add the repository folder first, so that src
# stays ahead of it (the same order as PYTHONPATH=src:. in the run commands). That order holds only when neither folder
# is on PYTHONPATH already (an entry that is already there is not moved). A `tools` package of another project that
# comes first on the path stops the start with a traceback (ModuleNotFoundError or ImportError): start it from the
# repository folder, without another project's `tools` on PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from http_guard import ReplyTooBig, open_http, read_reply

from lead_desk.config import is_loopback_host
from lead_desk.constants import EXIT_BAD_SETTING_OR_PATH, EXIT_CHECK_FAILED, EXIT_REFUSED, EXIT_UNREACHABLE, PORT_MAX
from lead_desk.envnum import SettingRefused, split_url
from lead_desk.jsonread import JsonTooDeep, loads_bounded
from lead_desk.regfile import FileRefused, load_json_file, plain_reason, read_secret_line
from lead_desk.scrub import secret_boundary
from tools.pathconfine import ROOTS_ENV, PathRefused, confine_existing

REFUSED = (
    "N8N_URL must be an https address, or http to this computer (127.0.0.1, ::1 or localhost); "
    "for an n8n on another computer use https, or an SSH tunnel to 127.0.0.1"
)


class Refusal(SystemExit):
    """A SystemExit whose exit status is the int `code` and whose `str()` is the fixed line that was printed."""

    def __init__(self, text: str, code: int) -> None:
        super().__init__(code)
        self.text = text

    def __str__(self) -> str:
        return self.text


def refuse(text: str, code: int = EXIT_BAD_SETTING_OR_PATH) -> NoReturn:
    """The ONE way this script ends on a refusal: the fixed `text` on the error output, then the exit code (4 a setting
    or path that cannot be used, 2 a name that matches none or several, 3 n8n did not answer with something usable).
    Never a bare SystemExit(text): that is always exit 1, and 1 is kept for a failed check."""
    print(text, file=sys.stderr)
    raise Refusal(text, code)


# What urllib dials is the whole text between "//" and the next "/": a host (letters, digits, dots, hyphens) or a
# bracketed IPv6 literal, then at most one ":port" of digits. Any other shape (a backslash, a second colon, text after
# a bracket, an empty port) is read one way by urlsplit and another by urllib, so it is refused.
NETLOC = re.compile(r"(\[[0-9A-Fa-f:.]+\]|[A-Za-z0-9.-]+)(:[0-9]{1,5})?")


def checked_base(url: str) -> str:
    """The n8n address, only when the API key may travel to it: https, or http to this computer. Uses the repository's
    own readers (split_url, is_loopback_host). Anything else is a SystemExit that says what to do."""
    try:
        parts = split_url("N8N_URL", url)
    except SettingRefused as e:
        refuse(f"{e}; {REFUSED}")
    # urlsplit drops tabs and line breaks and reads the host after the last "@"; urllib dials the whole text between
    # "//" and the next "/". So a user name part or a blank/control character is refused here, by a check.
    if "@" in parts.netloc or any(c.isspace() or not c.isprintable() for c in url):
        refuse(REFUSED)
    shape = NETLOC.fullmatch(parts.netloc)
    if shape is None or (shape.group(2) is not None and not 1 <= int(shape.group(2)[1:]) <= PORT_MAX):
        refuse(REFUSED)
    scheme, host = parts.scheme.lower(), parts.hostname or ""
    if host and (scheme == "https" or (scheme == "http" and is_loopback_host(host))):
        return url.rstrip("/")
    refuse(REFUSED)


UNREACHABLE_TEXT = (
    "cannot reach n8n (no answer, refused, timed out, or a network, TLS or protocol fault; details are not shown)"
)
USAGE = "usage: python scripts/n8n_api.py import FILE | activate NAME | deactivate NAME | list"


def usage_ok(a: list[str]) -> bool:
    """True for `list`, or `import|activate|deactivate` with a second word."""
    cmd = a[1] if len(a) > 1 else ""
    return cmd in ("list", "import", "activate", "deactivate") and (cmd == "list" or bool(a[2:]))


if __name__ == "__main__" and not usage_ok(sys.argv):  # a bad command line is a usage line and exit 2 BEFORE the
    print(USAGE, file=sys.stderr)  # address and the key file are looked at (no key file or a bad address must not
    sys.exit(EXIT_REFUSED)  # turn "wrong words" into a different message and exit code)

BASE = checked_base(os.environ.get("N8N_URL", "http://127.0.0.1:5679"))
PROXY_ALLOWED = urlsplit(BASE).scheme.lower() == "https"  # http is only ever to this computer: no proxy for the key


@secret_boundary()
def _read_key() -> str:
    name = os.environ.get("N8N_API_KEY_FILE")
    if not name:
        refuse("N8N_API_KEY_FILE must be the path of a one-line file with the n8n API key")
    try:  # the ONE secret reader of the repository: regular file, bounded, UTF-8 (BOM accepted, UTF-16 explained), one
        return read_secret_line(name, "n8n API key", "key")  # line, printable ASCII, no space, at least 8 characters
    except FileRefused as e:  # its texts are fixed: neither the path nor the content is in them
        refuse(str(e))


KEY = _read_key()
KEEP = ("name", "nodes", "connections", "settings")  # the create call refuses other top-level keys


def say(*parts: object) -> None:
    """print() for names that come from n8n or from a file: a character the terminal cannot encode (a lone surrogate,
    an emoji on a cp1252 pipe) becomes "?" instead of ending the run with a UnicodeEncodeError."""
    encoding = sys.stdout.encoding or "utf-8"
    text = " ".join(str(p) for p in parts)
    sys.stdout.write(text.encode(encoding, errors="replace").decode(encoding, errors="replace") + "\n")


NAME_SHOWN_MAX = 120  # the most characters of a workflow name that `list` prints


def shown(value: object, limit: int = NAME_SHOWN_MAX) -> str:
    """A name from n8n as ONE safe line: every character that is not printable (a line break, ESC, a bidi control, a
    lone surrogate ...) becomes its backslash form (`\\n`, `\\x1b`), and a long name is cut with "..." (never a terminal
    command or a fake extra line from a name n8n holds)."""
    text = "".join(
        c if c.isprintable() else c.encode("unicode_escape", errors="backslashreplace").decode("ascii")
        for c in str(value)
    )
    return text if len(text) <= limit else text[: limit - 3] + "..."


@secret_boundary()  # the key is a header here: an error never keeps the request
def call(method: str, path: str, body: object = None) -> tuple[int, object]:
    try:
        data = None if body is None else json.dumps(body).encode()
    except (ValueError, TypeError, RuntimeError):  # nested too deeply (RecursionError), a lone surrogate, ...
        refuse("cannot encode the workflow as JSON")
    try:
        req = urllib.request.Request(  # noqa: S310 - local n8n, http by design
            BASE + "/api/v1" + path,
            data=data,
            method=method,
            headers={"X-N8N-API-KEY": KEY, "Content-Type": "application/json"},
        )
        with open_http(req, 60, follow_redirects=False, use_proxy=PROXY_ALLOWED) as r:
            raw = read_reply(r)  # at most SCRIPT_REPLY_MAX_BYTES: ReplyTooBig is handled below
            if r.status != HTTPStatus.OK:  # any other success answer (201, 204 ...): same as an error answer
                return r.status, "(no body kept)"
            try:
                return r.status, (loads_bounded(raw) if raw else {})
            except JsonTooDeep:  # JSON nested thousands of levels deep
                refuse("n8n answered 200 with a body nested too deeply to read (not shown)", EXIT_UNREACHABLE)
            except ValueError:  # JSONDecodeError and UnicodeDecodeError: n8n (or something in front of it) sent no JSON
                refuse("n8n answered 200 with a body that is not JSON (not shown)", EXIT_UNREACHABLE)
    except urllib.error.HTTPError as e:
        try:
            read_reply(e)  # the body is not kept: an error page could echo a header
        except (OSError, http.client.HTTPException, ValueError):
            pass  # a reset or a cut-off while reading an error page changes nothing: the status is what counts
        return e.code, "(no body kept)"
    except ReplyTooBig:
        refuse("n8n answered with a reply that is too big to read (not shown)", EXIT_UNREACHABLE)
    except (OSError, http.client.HTTPException, ValueError):
        # refused, no route, timeout, TLS fault, a bad address, a cut-off answer: ONE fixed line, no class name (the
        # text of such an error can hold the address or, for a bad header, the key), and exit code 3 ("unreachable")
        print(UNREACHABLE_TEXT, file=sys.stderr)
        raise SystemExit(EXIT_UNREACHABLE) from None


def workflows() -> list[dict[str, object]]:
    """The workflow list, or a clean SystemExit when n8n did not answer 200 (a redirect, a refused key, an error) or
    sent a list whose entries are not workflows (an entry without a text name, an id or an active flag)."""
    code, res = call("GET", "/workflows?limit=250")
    if code != HTTPStatus.OK:
        refuse(f"n8n answered {code} to the workflow list ({res})", EXIT_UNREACHABLE)  # res is "(no body kept)" here
    items = res.get("data") if isinstance(res, dict) else None
    if not isinstance(items, list):
        refuse(f"n8n answered {code} to the workflow list (unexpected body)", EXIT_UNREACHABLE)
    for w in items:
        if not (isinstance(w, dict) and isinstance(w.get("name"), str) and "id" in w and "active" in w):
            refuse(
                f"n8n answered {code} to the workflow list (an entry without name, id or active flag)", EXIT_UNREACHABLE
            )
    return items


def find(name: str) -> str:
    hits = [str(w["id"]) for w in workflows() if w["name"] == name]
    if len(hits) != 1:
        refuse(f"{len(hits)} workflows have the NAME given (exactly one is needed)", EXIT_REFUSED)
    return hits[0]


def main(a: list[str]) -> int:
    cmd = a[1] if len(a) > 1 else ""
    if not usage_ok(a):
        print(USAGE, file=sys.stderr)
        return EXIT_REFUSED
    if cmd == "list":
        for w in workflows():
            say(shown(w["name"]), "active" if w["active"] else "inactive")
    elif cmd == "import":
        try:
            wf = load_json_file(confine_existing(a[2], what="FILE"))
            wf.setdefault("settings", {})
            str(wf["name"])  # a workflow file without a name is refused here, not after the call
        except PathRefused as e:  # the rule is in the message: a workflow file lies in an allowed folder
            hint = "" if ROOTS_ENV in str(e) else f"; more folders can be listed in {ROOTS_ENV}"
            refuse(
                f"cannot read a workflow ({e}). Rule: the file must exist and lie in the folder you started in, "
                f"the repository folder or the temporary folder{hint}"
            )
        except (OSError, ValueError, KeyError, AttributeError, RuntimeError) as e:  # no file, not JSON (or nested too
            # deeply: RecursionError), not an object, no name
            refuse(f"cannot read a workflow from the FILE given ({plain_reason(e)})")
        code, res = call("POST", "/workflows", {k: wf[k] for k in KEEP if k in wf})
        say(f"import: n8n answered {code}", "" if code == HTTPStatus.OK else res)  # no name: a name typed in a file
        return 0 if code == HTTPStatus.OK else EXIT_CHECK_FAILED
    else:  # activate or deactivate
        code, res = call("POST", f"/workflows/{find(a[2])}/{cmd}")
        say(f"{cmd}: n8n answered {code}", "" if code == HTTPStatus.OK else res)  # no name: the NAME was typed
        return 0 if code == HTTPStatus.OK else EXIT_CHECK_FAILED
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
