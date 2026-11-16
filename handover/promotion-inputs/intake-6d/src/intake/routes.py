"""The route table: the ONE list of addresses the service answers, who may use each (default deny) and which listener serves it (brief-v3 4.1, 5.1).

Data and pure functions only; this module imports nothing from ``intake`` (so ``ui.py`` can build links from it and the tests can read it without
starting a server). An empty ``roles`` set means nobody: such a row answers 403 for every role."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

APPROVER, VIEWER, DASH = "approver", "viewer", "dash"
ROLES = (APPROVER, VIEWER, DASH)
ANYONE = "anyone"  # login family only: no session needed
TOKEN_HOLDER = "token_holder"  # token family only: the webhook token, never a session
APPS = ("work", "dash", "token")  # which listener serves the row
FAMILIES = ("login", "session", "token")
# Must equal config/service.json name_regex without its ^ and $; `serve` refuses to start otherwise (brief-v3 12.1 step 1b).
STEM_RE = r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}"
ITEM_ID_RE = STEM_RE + r"-[0-9a-f]{8}"  # stem + "-" + 8 hex (spec 7)


@dataclass(frozen=True)
class Route:
    name: str
    method: str
    path: str  # may hold the one segment {id}
    roles: frozenset[str]  # {ANYONE}, {TOKEN_HOLDER}, or a subset of ROLES; EMPTY = nobody (default deny)
    app: str  # one of APPS
    family: str  # one of FAMILIES
    writes: bool = False
    fields: tuple[str, ...] = ()  # allowed POST form fields, exact
    query: tuple[str, ...] = ()  # allowed query keys, exact


def _r(name, method, path, roles, app, family, writes=False, fields=(), query=()) -> Route:
    return Route(name, method, path, frozenset(roles), app, family, writes, tuple(fields), tuple(query))


_BOTH = (APPROVER, VIEWER)
ROUTE_TABLE: tuple[Route, ...] = (
    _r("login", "GET", "/login", (ANYONE,), "work", "login"),
    _r("login_post", "POST", "/login", (ANYONE,), "work", "login", True, ("csrf", "login", "passphrase")),
    _r("home", "GET", "/", _BOTH, "work", "session", query=("sort", "dir", "state")),
    _r("item", "GET", "/item/{id}", _BOTH, "work", "session"),
    _r(
        "decide",
        "POST",
        "/item/{id}/decide",
        (APPROVER,),
        "work",
        "session",
        True,
        ("csrf", "decision", "reason", "content_code", "version"),
    ),
    _r("export", "GET", "/export", (APPROVER,), "work", "session"),
    _r("export_run", "POST", "/export", (APPROVER,), "work", "session", True, ("csrf", "passphrase", "preview")),
    _r("overview", "GET", "/overview", _BOTH, "work", "session"),
    _r("logout", "POST", "/logout", _BOTH, "work", "session", True, ("csrf",)),
    _r("healthz", "GET", "/healthz", (TOKEN_HOLDER,), "token", "token"),
    _r("scan", "POST", "/events/scan", (TOKEN_HOLDER,), "token", "token", True),
)


def validate(table: tuple[Route, ...]) -> None:
    """Import-time rules (each a ``ValueError``); a function so a test can hand it a bad table."""
    seen: set[str] = set()
    known_roles = {*ROLES, ANYONE, TOKEN_HOLDER}
    for r in table:
        if r.name in seen:
            raise ValueError(f"duplicate route name {r.name}")
        seen.add(r.name)
        if r.app not in APPS or r.family not in FAMILIES:
            raise ValueError(f"{r.name}: unknown app or family")
        if not r.roles <= known_roles:
            raise ValueError(f"{r.name}: unknown role")
        if r.app == "dash" and r.writes:
            raise ValueError(f"{r.name}: a dashboard route may not write")  # W-1
        if r.family == "token" and (r.app != "token" or r.roles != {TOKEN_HOLDER}):
            raise ValueError(f"{r.name}: the token family is only for the token listener and the token holder")
        if r.app == "token" and r.family != "token":
            raise ValueError(f"{r.name}: the token listener serves only the token family")
        if r.family == "login" and r.roles != {ANYONE}:
            raise ValueError(f"{r.name}: the login family is for anyone")
        if r.family == "session" and ({ANYONE, TOKEN_HOLDER} & r.roles):
            raise ValueError(f"{r.name}: a session route is for signed-in roles only")
        if r.family == "session" and r.method == "POST" and "csrf" not in r.fields:
            raise ValueError(f"{r.name}: a session POST must carry csrf")
        if r.method not in ("GET", "POST") or not r.path.startswith("/") or r.path.count("{") != r.path.count("{id}"):
            raise ValueError(f"{r.name}: bad method or path")


validate(ROUTE_TABLE)
_BY_NAME = {r.name: r for r in ROUTE_TABLE}
_PATTERNS = tuple(
    (re.compile(re.escape(r.path).replace(re.escape("{id}"), f"(?P<id>{ITEM_ID_RE})")), r) for r in ROUTE_TABLE
)  # fullmatch against the raw path; {id} only ever matches ITEM_ID_RE


def route(name: str) -> Route:
    """The row with this name (``ValueError`` for an unknown name)."""
    try:
        return _BY_NAME[name]
    except KeyError:
        raise ValueError(f"unknown route {name!r}") from None


def match(app: str, method: str, path: str) -> tuple[Route, dict[str, str]] | None | Literal["method"]:
    """The row this listener serves for the raw path and method, with its ``{id}`` value; ``"method"`` when the path exists here under another method
    (405); None when nothing matches (404). The raw path is matched exactly: a ``%`` anywhere is no match; a trailing slash is another path."""
    if "%" in path:
        return None
    other = False
    for pat, r in _PATTERNS:
        if r.app != app:
            continue
        m = pat.fullmatch(path)
        if m is None:
            continue
        if r.method == method:
            return r, m.groupdict()
        other = True
    return "method" if other else None


def allowed(method: str, path: str, role: str | None, app: str = "work") -> bool:
    """True only if a row of this listener matches and grants this exact role (or is open to anyone): the call ``ui.py`` makes to show a navigation
    link only for a page the role may open (the signature of the portal stand-in this module replaces). Default deny."""
    hit = match(app, method, path)
    if not isinstance(hit, tuple):
        return False
    roles = hit[0].roles
    return ANYONE in roles or (isinstance(role, str) and role in roles - {TOKEN_HOLDER})
