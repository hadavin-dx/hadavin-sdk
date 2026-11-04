"""A test tool module (K5): tools served from recorded results, so no network is needed.

``READ_OPERATIONS`` is the read list a manifest's ``operations`` must stay inside. ``RESULTS`` is filled by the
test (or by a red-team bundle) with the text each ``read_logs`` name returns.
"""

from __future__ import annotations

import time
from typing import Any

# operation id -> (METHOD, regex the URL path must fully match)
READ_OPERATIONS = {
    "bundle.read": ("GET", r"/.*"),
    "bundle.post": ("POST", r"/.*"),
    "bundle.other": ("GET", r"/other/.*"),
}
RESULTS: dict[str, str] = {}


def read_logs(args: dict[str, Any], ctx) -> str:
    name = args["name"]
    if name == "boom":
        raise RuntimeError("secret store down for ops@example.com")
    return RESULTS.get(name, "no data")


def fetch_url(args: dict[str, Any], ctx) -> str:
    url = args.get("url", args.get("name"))
    return ctx.fetch(args.get("method", "GET"), url, operation=args.get("operation", "bundle.read"))


def with_secret(args: dict[str, Any], ctx) -> str:
    return "token=" + ctx.secret(args["secret"])


def slow(args: dict[str, Any], ctx) -> str:
    time.sleep(2)
    return "late"
