"""pytest plugin: for every test, tools.policy_page.datetime.now() returns 2026-12-12 12:00 UTC (module attribute `datetime` replaced by a subclass)."""
import datetime as _d
import pytest

FAKE = _d.datetime(2026, 12, 12, 12, 0, tzinfo=_d.UTC)

class _FakeDT(_d.datetime):
    @classmethod
    def now(cls, tz=None):
        return FAKE if tz is None else FAKE.astimezone(tz)

@pytest.fixture(autouse=True)
def _fake_policy_page_clock(monkeypatch):
    from tools import policy_page
    monkeypatch.setattr(policy_page, "datetime", _FakeDT)
