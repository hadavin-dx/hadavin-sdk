"""Send the made-up canned leads to the desk, one request each (the two "doors": source form or webhook).

Run from the repository root:  PYTHONPATH=src python scripts/feed.py --source form --index 1
Each lead in demo_only/canned_leads.json becomes the envelope {"source", "source_ref": "canned-<i>", "payload"}, where
<i> is the position in the file starting at 1. Sending the same --index twice sends the same request id twice
(a replay).
The desk address comes from the desk configuration (DESK_BIND, DESK_PORT), not from this file and not from the command
line: there is no option to point the request anywhere else.
A wrong input or a desk that cannot be reached ends in ONE plain line that starts `refused:` (never a Python traceback,
never the address): exit code 2 for a wrong input (a bad --index, a bad setting, an unreadable canned file), exit code
3 when the desk is not running, does not answer or answers something unreadable.
"""

from __future__ import annotations

import http.client
import ipaddress
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the repository folder, for tools/
from http_guard import REPLY_TOO_BIG_TEXT, ReplyTooBig, open_http, read_reply
from refusals import EXIT_REFUSED, EXIT_UNREACHABLE, refusal

from lead_desk.config import Config
from lead_desk.constants import SOURCES
from lead_desk.envnum import SettingRefused
from lead_desk.regfile import load_json_file
from lead_desk.urls import desk_origin
from tools.refusing_args import RefusingParser

CANNED = Path("demo_only") / "canned_leads.json"


def target_host(bind: str) -> str:
    """The name to call for a bind address. A wildcard bind (the all-zeros address, ::) is reached through loopback,
    because the desk refuses a Host header that names a wildcard address."""
    try:
        ip = ipaddress.ip_address(bind.strip("[]"))
    except ValueError:
        return bind
    if ip.is_unspecified:
        return "[::1]" if isinstance(ip, ipaddress.IPv6Address) else "127.0.0.1"
    return f"[{ip}]" if isinstance(ip, ipaddress.IPv6Address) else str(ip)


class FeedRefused(ValueError):
    """A wrong input: carries the refusal line (fixed text; never the typed value)."""


def build_envelope(source: str, index: int, leads: list[dict[str, object]]) -> dict[str, object]:
    if source not in SOURCES:
        raise FeedRefused(refusal("--source", "must be one of " + ", ".join(SOURCES)))
    if not 1 <= index <= len(leads):
        raise FeedRefused(refusal("--index", f"must be a whole number from 1 to {len(leads)}"))
    return {"source": source, "source_ref": f"canned-{index}", "payload": leads[index - 1]}


def load_leads() -> list[dict[str, object]]:
    """The canned leads; a missing, unreadable or wrong file is a refusal (the path is relative: run from the root)."""
    try:
        leads = load_json_file(CANNED)
    except (OSError, ValueError):  # no file, a pipe or folder, too big, not UTF-8, not JSON, nested too deeply
        leads = None
    if not isinstance(leads, list) or not leads or not all(isinstance(x, dict) for x in leads):
        raise FeedRefused(
            refusal(
                "canned leads",
                f"{CANNED.as_posix()} cannot be read as a list of leads; run this from the repository root",
            )
        )
    return leads


def post(url: str, envelope: dict[str, object], timeout: float) -> tuple[int, str]:
    req = urllib.request.Request(  # noqa: S310 - the url is built from the http-only desk config
        url, data=json.dumps(envelope).encode(), headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with open_http(req, timeout) as resp:
            return resp.status, read_reply(resp).decode(errors="replace")
    except urllib.error.HTTPError as err:
        return err.code, read_reply(err).decode(errors="replace")


UNREACHABLE = (
    "the desk cannot be reached (it is not running, or DESK_BIND / DESK_PORT name a different address); "
    "start it with scripts/start_all.sh, then run this again"
)
NO_ANSWER = "the desk did not answer in time (it may be busy or stuck); nothing more was sent"
BAD_ANSWER = "the desk ended the connection or answered something that is not a web reply; nothing more was sent"


def unreachable_line(err: BaseException) -> str:
    """One refusal line for a failed request; it never shows the address (`err` can hold it). A timeout is told apart
    from a refused or unreachable connection; a URLError wraps the OSError that explains it."""
    reason = err.reason if isinstance(err, urllib.error.URLError) else err
    if isinstance(reason, TimeoutError):
        return refusal("the desk", NO_ANSWER)
    if isinstance(reason, ConnectionRefusedError) or (
        isinstance(reason, OSError) and not isinstance(reason, ConnectionError)
    ):  # a reset, abort or broken pipe is a desk that hung up, not one that is not running
        return refusal("the desk", UNREACHABLE)
    return refusal("the desk", BAD_ANSWER)


def run(argv: list[str] | None) -> int:
    ap = RefusingParser(description="Send canned made-up leads to the desk.")
    ap.add_argument("--source", choices=SOURCES, required=True)
    ap.add_argument("--index", type=int, help="position in canned_leads.json, starting at 1")
    ap.add_argument("--all", action="store_true", help="send every canned lead once")
    args = ap.parse_args(argv)
    if args.all == (args.index is not None):
        print(refusal("--index, --all", "give exactly one of them"))
        return EXIT_REFUSED
    cfg = Config.from_env()
    url = f"{desk_origin(target_host(cfg.bind), cfg.port)}/leads"  # from the configuration only
    leads = load_leads()
    indexes = range(1, len(leads) + 1) if args.all else [args.index]
    for i in indexes:
        status, body = post(url, build_envelope(args.source, i, leads), cfg.send_timeout_seconds)
        print(f"canned-{i} {args.source} -> {status} {body}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """The one place where an error becomes a refusal line: nothing above it ends the script with a traceback."""
    try:
        return run(argv)
    except FeedRefused as e:
        print(e)
        return EXIT_REFUSED
    except ReplyTooBig:  # the desk's answer is longer than SCRIPT_REPLY_MAX_BYTES: not read further, not printed
        print(refusal("the desk", REPLY_TOO_BIG_TEXT))
        return EXIT_UNREACHABLE
    except ValueError as e:  # a setting the desk refuses (its text names the setting, never the value)
        print(refusal("desk settings", str(e) if isinstance(e, SettingRefused) else "a desk setting is wrong"))
        return EXIT_REFUSED
    except (urllib.error.URLError, OSError, http.client.HTTPException) as e:
        print(unreachable_line(e))
        return EXIT_UNREACHABLE


if __name__ == "__main__":
    sys.exit(main())
