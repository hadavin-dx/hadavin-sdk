"""Default deny at the table level (brief-v3 5.1, 15.1): every row has exact roles, a viewer may read and nothing else, only the approver decides and
exports, a token row is never a session row. The listener-level half (a request to a row with EMPTY roles answers 403 for every role; the rows that
have a handler) is package 6d's ``routes_have_roles`` in ``tests/test_service_routes.py``, because it needs the real dispatch."""

from __future__ import annotations

import pytest

from intake import routes

ID = "invoice-a-1a2b3c4d"


def _path(r: routes.Route) -> str:
    return r.path.replace("{id}", ID)


def test_every_row_has_exact_roles_and_a_unique_listener_method_path():
    seen = set()
    for r in routes.ROUTE_TABLE:
        assert r.roles and r.roles <= {*routes.ROLES, routes.ANYONE, routes.TOKEN_HOLDER}, r
        assert (r.app, r.method, r.path) not in seen, r
        seen.add((r.app, r.method, r.path))
        assert r.method in ("GET", "POST") and (r.method == "GET") != r.writes
        assert (routes.ANYONE in r.roles) == (r.family == "login") and (routes.TOKEN_HOLDER in r.roles) == (r.family == "token")


def test_viewer_may_read_the_lists_and_sign_out_and_nothing_else():
    for r in routes.ROUTE_TABLE:
        if r.app != "work":
            continue
        got = routes.allowed(r.method, _path(r), routes.VIEWER)
        expect = r.name in (
            "login",
            "login_post",
            "home",
            "item",
            "overview",
            "logout",
        )  # /export is approver-only (M-C); decide and export_run write
        assert got is expect, r.name


def test_only_the_approver_decides_and_exports_and_opens_the_export_page():
    for name in ("decide", "export_run", "export"):
        r = routes.route(name)
        assert routes.allowed(r.method, _path(r), routes.APPROVER)
        assert not routes.allowed(r.method, _path(r), routes.VIEWER)
    for r in routes.ROUTE_TABLE:
        if r.app == "work":
            assert routes.allowed(r.method, _path(r), routes.APPROVER), r.name  # the approver gets every work route


@pytest.mark.parametrize("role", ["", None, "admin", "Approver", "system", "cli", "approver ", 1, "token_holder", "dash"])
def test_unknown_and_foreign_roles_are_refused_everywhere_except_the_open_sign_in_rows(role):
    for r in routes.ROUTE_TABLE:
        if r.app != "work":
            continue
        assert routes.allowed(r.method, _path(r), role) is (routes.ANYONE in r.roles), (r.name, role)


def test_token_rows_are_never_session_rows():
    for r in routes.ROUTE_TABLE:
        if r.app == "token":
            assert r.roles == {routes.TOKEN_HOLDER} and r.family == "token"
            for role in (routes.APPROVER, routes.VIEWER, routes.TOKEN_HOLDER, None):
                assert not routes.allowed(r.method, r.path, role)  # asked on the work listener: not a row there
                assert not routes.allowed(r.method, r.path, role, "dash")
        else:
            assert routes.TOKEN_HOLDER not in r.roles


def test_no_dash_row_writes_and_the_dash_listener_has_no_rows_yet():
    assert [r for r in routes.ROUTE_TABLE if r.app == "dash"] == []  # release 2 adds rows (brief-v3 5.0)
    assert routes.match("dash", "GET", "/") is None


def test_the_rows_without_a_wp6_handler_are_exactly_the_overview_page():
    """Until portal P2a adds its handler, ``overview`` is the one work row that answers 404 (brief-v3 5.1). 6d's version checks the real handlers;
    here the table must still carry the row, because ``ui.py``'s navigation links to it."""
    assert routes.route("overview").path == "/overview" and routes.route("overview").roles == {routes.APPROVER, routes.VIEWER}
