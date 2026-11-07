"""The Migration repair steps of CHANGELOG.md, read as data, so a test can RUN the steps it prints (not only match its words).

Nothing here is made up in the test: the lock number, the `DO` check, the evidence tables block, the check query and the
`UPDATE` of a renamed row are cut out of the runbook text itself.
"""

from __future__ import annotations

import re
from pathlib import Path

CHANGELOG_PATH = Path(__file__).resolve().parents[2] / "CHANGELOG.md"
CHANGELOG = CHANGELOG_PATH.read_text(encoding="utf-8")
RUNBOOK = CHANGELOG[
    CHANGELOG.index("### Migration ") :
]  # "repair steps" now, "runbook" in older text
TIMEOUTS = [
    "SET LOCAL lock_timeout = '5s';",
    "SET LOCAL statement_timeout = '60s';",
]  # as the rule says
PSQL_ARGS = [
    "psql",
    "-X",
    "-v",
    "ON_ERROR_STOP=1",
]  # the rule of the runbook; the caller adds `-f <file>`


def case(letter: str) -> str:
    """The text of runbook case `(letter)`: from its bullet to the next bullet (or the end)."""
    marker = f"- **({letter}) "
    start = RUNBOOK.index(marker)
    nxt = re.search(r"\n- \*\*\([a-z]\) ", RUNBOOK[start + 1 :])
    return RUNBOOK[start : start + 1 + nxt.start()] if nxt else RUNBOOK[start:]


def sql_blocks() -> list[str]:
    return re.findall(r"```sql\n(.*?)```", RUNBOOK, flags=re.DOTALL)


def block_with(fragment: str) -> str:
    found = [b for b in sql_blocks() if fragment in b]
    assert len(found) == 1, (fragment, len(found))
    return found[0]


def lock_number() -> int:
    return int(re.search(r"pg_advisory_xact_lock\((\d+)\)", RUNBOOK).group(1))


def do_check(new: str, old: str) -> str:
    return block_with("the ledger row was not renamed").replace("<NEW>", new).replace("<OLD>", old)


def evidence_block() -> str:
    return block_with("ADD COLUMN IF NOT EXISTS error")


def span_in(text: str, start: str) -> str:
    """The inline-code span in `text` that starts with `start`."""
    return re.search(r"`(" + re.escape(start) + r"[^`]*)`", text).group(1)


def hand_file(schema: str, *steps: str) -> str:
    """The header the runbook prescribes, then `steps`, then COMMIT."""
    head = [
        "\\set ON_ERROR_STOP on",
        f'SET search_path TO "{schema}";',
        "BEGIN;",
        *TIMEOUTS,
        f"SELECT pg_advisory_xact_lock({lock_number()});",
    ]
    return "\n".join([*head, *steps, "COMMIT;", ""])


def rename_step(old: str, new: str) -> str:
    """The `UPDATE` of case (b), as printed there, with the two names filled in."""
    update = span_in(case("b"), "UPDATE schema_migrations SET version")
    return update.replace("<file_stem>", new).replace("<wrong name>", old)
