"""The meter tests of ``tests/contracts/`` for the memory store only, so the mutation runner can use them.

``tools/mutation_runner.py`` runs pytest with ``--noconftest`` (a planted conftest must never be read), so the
``store`` fixture of ``tests/contracts/conftest.py`` does not exist there. This module supplies the one fixture the
tests need, a fresh MemoryStore, and re-exports the tests of the two contract files unchanged: no scenario is written
twice. The file name does not start with ``test_``, so a normal pytest run does not collect it (the contract files
already run on the memory store there); ``tests/meter_mutants.py`` names it explicitly.
"""

from __future__ import annotations

import pytest

from hadavin_sdk.store.memory import MemoryStore
from tests.contracts import test_store_time_rules, test_t1_meter_cap


@pytest.fixture
def store() -> MemoryStore:
    return MemoryStore()


for _module in (test_store_time_rules, test_t1_meter_cap):
    for _name, _obj in vars(_module).items():
        if _name.startswith("test_"):
            assert _name not in globals(), f"{_name} is in both contract files"
            globals()[_name] = _obj
