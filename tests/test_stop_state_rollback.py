"""An old release (one that writes the kill_switch row itself) on a guarded database fails loudly, never silently."""

from __future__ import annotations

import pytest
from psycopg import errors

from tests.test_stop_state_db import (
    stop_world as _w_fixture,  # noqa: F401  (registers the `w` fixture)
)


def test_old_release_fails_loudly_on_a_guarded_database(w):
    """The pre-P2a upsert, run by the runtime login, is refused with a privilege error (not swallowed)."""
    old_upsert = 'UPDATE kill_switch SET "on" = true'
    with w.as_(w.runtime) as db:
        with pytest.raises(errors.InsufficientPrivilege):
            db.execute(old_upsert)
        with pytest.raises(errors.InsufficientPrivilege):
            db.execute('INSERT INTO kill_switch (id, "on") VALUES (1, true)')
    assert w.state()[0] is False
