"""Round 7B (review part 2, M2): the portal reads the made-up CRM view of a big run whole. The old cap (4 MiB,
about 20,000 rows) refused the view of a run of 100,000 leads; the cap now comes from constants.py (round 7C: the
portal asks for PORTAL_ROWS_MAX rows, each at most PORTAL_VIEW_ROW_BYTES bytes). A reply over the cap is refused
whole."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from support import HOST

from lead_desk.constants import (
    PORTAL_ROWS_MAX,
    PORTAL_VIEW_REPLY_MAX_BYTES,
    PORTAL_VIEW_ROW_BYTES,
)

portal_demo = pytest.importorskip("demo_only.portal_demo")


def _serve(body: bytes) -> tuple[ThreadingHTTPServer, str]:
    class H(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 (the name the server looks for)
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a: object) -> None:
            return

    srv = ThreadingHTTPServer((HOST, 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://{HOST}:{srv.server_address[1]}/v"


def _view(rows: int) -> bytes:
    row = {"id": "r-000000", "email": "a@example.com", "name": "Made Up", "stage": "new", "note": "x" * 150}
    return json.dumps({"count": rows, "rows": [row] * rows}).encode()


def test_the_cap_covers_the_rows_the_portal_asks_for() -> None:
    assert PORTAL_VIEW_REPLY_MAX_BYTES >= PORTAL_ROWS_MAX * PORTAL_VIEW_ROW_BYTES  # the size no longer follows the run
    assert len(_view(1)) < PORTAL_VIEW_ROW_BYTES + 100  # the sample row is inside the size the cap assumes


def test_a_view_of_the_rows_the_portal_shows_and_over_the_old_cap_of_the_script_replies_is_read_whole() -> None:
    body = _view(PORTAL_ROWS_MAX * 20)  # 4000 rows of the sample shape: more than the portal ever asks for
    assert len(body) < PORTAL_VIEW_REPLY_MAX_BYTES
    srv, url = _serve(body)
    try:
        got = portal_demo._fetch_json(url, 20.0)
    finally:
        srv.shutdown()
        srv.server_close()
    assert got is not None and got["count"] == PORTAL_ROWS_MAX * 20 and len(got["rows"]) == PORTAL_ROWS_MAX * 20


def test_a_reply_over_the_view_cap_is_refused_whole(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(portal_demo, "PORTAL_VIEW_REPLY_MAX_BYTES", 1000)
    srv, url = _serve(_view(20))
    try:
        assert portal_demo._fetch_json(url, 10.0) is None  # not a cut-off copy
    finally:
        srv.shutdown()
        srv.server_close()
