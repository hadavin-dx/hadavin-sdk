"""Round 7C, finding F: the size claim of the portal view is TRUE. The old comment said a row was about 400 bytes; the
real worst row (longest name, e-mail and company, every character outside the Basic Multilingual Plane, which the
fake prints as two 6-byte escapes) is far larger. This builds that worst row through the real fake server, checks it
fits PORTAL_VIEW_ROW_BYTES, and checks that the portal's request (`?limit=`) keeps a 100,000-lead view under the cap."""

from __future__ import annotations

import http.client
import json
import urllib.parse

import pytest

from demo_only.fakes_server import serve_fakes_in_thread, stop_fakes
from lead_desk.constants import (
    COMPANY_MAX,
    EMAIL_MAX,
    NAME_MAX,
    PORTAL_ROWS_MAX,
    PORTAL_VIEW_REPLY_MAX_BYTES,
    PORTAL_VIEW_ROW_BYTES,
)

portal_demo = pytest.importorskip("demo_only.portal_demo")
ASTRAL = "\U0001f600"  # one character, printed as two \uXXXX escapes (12 bytes)


def _worst_row(n: int) -> dict[str, object]:
    record = {
        "lead_id": f"L{n:012x}",
        "name": ASTRAL * NAME_MAX,
        "email": ASTRAL * EMAIL_MAX,
        "company": ASTRAL * COMPANY_MAX,
        "source": "webhook",
        "ai_label": "needs_person",
    }
    return {"lead_id": record["lead_id"], "record": record}


def _get(url: str) -> bytes:
    parts = urllib.parse.urlsplit(url)
    conn = http.client.HTTPConnection(parts.hostname or "", parts.port, timeout=20)
    try:
        conn.request("GET", parts.path + ("?" + parts.query if parts.query else ""))
        return conn.getresponse().read()
    finally:
        conn.close()


@pytest.fixture
def fake() -> object:
    srv, url, th = serve_fakes_in_thread()
    yield srv, url
    stop_fakes(srv, th)


def test_the_worst_row_fits_the_row_size_and_a_limited_view_fits_the_cap(fake: tuple[object, str]) -> None:
    srv, url = fake
    with srv.state.lock:
        for n in range(PORTAL_ROWS_MAX + 50):
            row = _worst_row(n)
            srv.state.crm.append(row)
            srv.state.crm_fields[str(row["lead_id"])] = {"owner_id": "o" * 64, "status": "s" * 32}
    one = json.dumps(_worst_row(0)).encode()
    assert len(one) <= PORTAL_VIEW_ROW_BYTES, (len(one), PORTAL_VIEW_ROW_BYTES)
    assert len(one) > PORTAL_VIEW_ROW_BYTES // 2  # the bound is not wildly loose
    body = _get(url + "/fake/crm" + portal_demo.LIMIT_QUERY)
    got = json.loads(body)
    assert got["count"] == PORTAL_ROWS_MAX + 50 and len(got["rows"]) == PORTAL_ROWS_MAX
    assert len(got["fields"]) == PORTAL_ROWS_MAX  # fields only for the rows shown
    assert len(body) <= PORTAL_VIEW_REPLY_MAX_BYTES, (len(body), PORTAL_VIEW_REPLY_MAX_BYTES)
    assert portal_demo._fetch_json(url + "/fake/crm" + portal_demo.LIMIT_QUERY, 20.0) is not None


def test_limit_cuts_only_the_list_never_the_totals(fake: tuple[object, str]) -> None:
    srv, url = fake
    with srv.state.lock:
        for n in range(7):
            srv.state.outbox.append({"key": f"nudge:{n}" if n % 2 else f"k{n}", "to": "a@example.test", "subject": "s"})
    whole = json.loads(_get(url + "/fake/outbox"))
    cut = json.loads(_get(url + "/fake/outbox?limit=3"))
    assert len(whole["messages"]) == 7 and len(cut["messages"]) == 3
    assert cut["count"] == whole["count"] == 7 and cut["reminders"] == whole["reminders"]
    for bad in ("limit=-1", "limit=x", "limit=%C2%B2", "limit=999999999999"):
        assert len(json.loads(_get(url + "/fake/outbox?" + bad))["messages"]) == 7  # not a valid number: the whole list
    assert json.loads(_get(url + "/fake/outbox?limit=0"))["messages"] == []
