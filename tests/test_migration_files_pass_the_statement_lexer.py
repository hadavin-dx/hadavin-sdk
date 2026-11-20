"""Every shipped migration file must pass the statement lexer's refusal list (`migration_numbers.refused_statements`).
`migrate` does not call it yet (P3a-2 wiring), so a file that uses a refused statement (a DO block, say) would be
refused on every database the day the wiring lands. No database needed."""

from __future__ import annotations

import pytest

from hadavin_sdk.store import migrate as migrate_mod
from hadavin_sdk.store.migration_numbers import refused_statements


@pytest.mark.parametrize("path", migrate_mod._migration_files(), ids=lambda p: p.name)
def test_no_shipped_migration_is_refused_by_the_lexer(path):
    assert refused_statements(path.read_text(encoding="utf-8")) == []
