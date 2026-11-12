"""Guard for ``tests/inbound_ledger_mutants.py``: every mutant there must still apply to the source (its ``old`` text occurs exactly once in
the file it names), must change something, and must name a killer test that exists. Without this a refactor could silently turn a mutant
into a no-op and the mutation run would report nothing wrong. No database needed."""

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _mutants():
    spec = importlib.util.spec_from_file_location(
        "inbound_ledger_mutants", ROOT / "tests" / "inbound_ledger_mutants.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.M


def test_every_inbound_ledger_mutant_still_applies():
    problems = []
    for m in _mutants():
        text = (ROOT / m.file).read_text(encoding="utf-8")
        if text.count(m.old) != 1:
            problems.append(
                f"{m.name}: `old` occurs {text.count(m.old)} times in {m.file}, not once"
            )
        if m.new == m.old:
            problems.append(f"{m.name}: `new` equals `old`")
        killer_file = (ROOT / m.test_file).read_text(encoding="utf-8")
        if not re.search(rf"^\s*def {re.escape(m.only_test)}\(", killer_file, re.MULTILINE):
            problems.append(f"{m.name}: killer {m.only_test} is not in {m.test_file}")
        if not m.pinned.split("::")[-1].startswith(m.only_test):
            problems.append(f"{m.name}: the pinned id does not name the killer")
    assert not problems, "inbound ledger mutants that no longer apply: " + "; ".join(problems)


def test_the_inbound_ledger_mutants_have_unique_names_and_cover_every_part():
    ms = _mutants()
    names = [m.name for m in ms]
    assert len(set(names)) == len(names), "two inbound ledger mutants share a name"
    files = {m.file for m in ms}
    assert files >= {
        "src/hadavin_sdk/triggers/ledger.py",
        "src/hadavin_sdk/store/memory.py",
        "src/hadavin_sdk/store/postgres.py",
        "src/hadavin_sdk/store/migrations/0006_inbound.sql",
        "src/hadavin_sdk/store/migrate.py",
    }, "a part of the inbound ledger has no mutant"
