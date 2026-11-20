"""Mutants of the audit rights (ticket A-audit-rights, review 1 section 4): each reverts ONE guard; the pinned killer
of ``tests/test_audit_rights_roles_pg.py`` (or ``tests/test_audit_runtime_rights_pg.py``) must fail, and for the reason
named in ``expect``. Every killer needs a real PostgreSQL (the grants, the functions), so the mutants are applied one at
a time to THIS working tree (the style of ``tests/reserve_mutants.py --hand``), the killer is run with the caller's
HADAVIN_TEST_PG_DSN, and the file is put back byte for byte. Not collected by pytest:

    HADAVIN_TEST_PG_DSN=<dsn> uv run --all-extras --group test python tests/audit_rights_mutants.py
    HADAVIN_TEST_PG_DSN=<dsn> uv run --all-extras --group test python tests/audit_rights_mutants.py "A3"

It refuses to start when a target file has uncommitted changes, runs each killer on the clean tree first (it must
pass, or the kill means nothing), and ends with ``N of N good; problems: [...]``."""

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIG = "src/hadavin_sdk/store/migrate.py"
CHAIN = "src/hadavin_sdk/audit/chain.py"
SQL12 = "src/hadavin_sdk/store/migrations/0012_audit_outbox_functions.sql"
ROLES = "tests/test_audit_rights_roles_pg.py"
RIGHTS = "tests/test_audit_runtime_rights_pg.py"


@dataclass(frozen=True)
class Hand:
    name: str
    file: str
    old: str
    new: str
    node: str  # the pytest node id of the killer
    expect: str  # must be in the killer's output
    more: tuple[tuple[str, str], ...] = ()  # further (old, new) edits of the same file


# A9: with both membership tests off, migrate still refuses the member (it inherits the owner's rights, so the grant
# map check names those instead): the killer pins the refusal's NAMING of the membership, hence "did not match".
MEMBER_OWNER = """        if db.execute("SELECT pg_has_role(%s, %s, 'MEMBER')", (role, owner)).fetchone()[0]:
            problems.append(f"{role}: is a member of {owner}, the owner of relations in {schema}")"""
MEMBER_FUNC = """        elif db.execute("SELECT pg_has_role(%s, %s, 'MEMBER')", (role, owner)).fetchone()[0]:
            problems.append(
                f"{role} is a member of {owner}, the owner of the hadavin_* functions: remove the membership\""""

HAND = [
    Hand("A1 done: the EXISTS (event is in the chain) test is dropped", SQL12,
        "       AND EXISTS (SELECT 1 FROM audit_entries e WHERE e.event_id = p_event_id);", ";",
        f"{ROLES}::test_done_deletes_nothing_while_the_event_is_not_in_the_chain", "ghost-1"),
    Hand("A2 the runtime gets INSERT on audit_checkpoints back", MIG,
        '    "audit_checkpoints": Grant(\n        "table",\n        "SELECT",',
        '    "audit_checkpoints": Grant(\n        "table",\n        "SELECT, INSERT",',
        f"{RIGHTS}::test_runtime_has_no_insert_on_audit_checkpoints", "assert not True"),
    Hand("A3 the runtime gets DELETE on audit_outbox back", MIG,
        '"audit_outbox": Grant("table", "SELECT, INSERT"),',
        '"audit_outbox": Grant("table", "SELECT, INSERT, DELETE"),',
        f"{RIGHTS}::test_runtime_has_no_delete_on_audit_outbox", "assert not True"),
    Hand("A4a the checkpoint role gets UPDATE on audit_checkpoints", MIG,
        "        checkpoint=_APPEND,\n    ),\n    # No DELETE",
        '        checkpoint="SELECT, INSERT, UPDATE",\n    ),\n    # No DELETE',
        f"{ROLES}::test_the_checkpoint_role_holds_only_the_checkpoint_write_and_the_chain_read", "audit_checkpoints"),
    Hand("A4b the checkpoint role gets INSERT on audit_entries", MIG,
        '        checkpoint="SELECT",\n    ),',
        "        checkpoint=_APPEND,\n    ),",
        f"{ROLES}::test_the_checkpoint_role_holds_only_the_checkpoint_write_and_the_chain_read", "audit_entries"),
    Hand("A5 the inline checkpoint is no longer skipped when the checkpoint login is set", CHAIN,
        "            and self._checkpoint_db is None\n", "",
        f"{ROLES}::test_the_inline_checkpoint_is_skipped_when_the_checkpoint_login_is_set", "head > after"),
    Hand("A6 _quarantine is back to INSERT and DELETE on the runtime login", CHAIN,
        "            if self._db.pg:\n                # Postgres: the runtime holds no DELETE",
        "            if False:\n                # Postgres: the runtime holds no DELETE",
        f"{ROLES}::test_the_chain_quarantines_through_the_function_on_the_runtime_login", "assert 0 == 1"),
    Hand("A7 the outbox functions are not re-pinned to the schema", MIG,
        "    for signature in (*MONEY_FUNCTIONS, *AUDIT_FUNCTIONS):\n        if db.execute",
        "    for signature in MONEY_FUNCTIONS:\n        if db.execute",
        f"{ROLES}::test_the_outbox_functions_are_pinned_to_the_catalog_the_schema_and_the_temp_schema", "search_path"),
    Hand("A8 EXECUTE on the outbox functions is left on PUBLIC", SQL12,
        "REVOKE ALL ON FUNCTION hadavin_audit_outbox_done(TEXT) FROM PUBLIC;\n", "",
        f"{ROLES}::test_public_cannot_execute_the_outbox_functions", "can run hadavin_audit_outbox_done"),
    Hand("A9 the owner refusal skips a MEMBER of the owner role", MIG, MEMBER_OWNER,
        MEMBER_OWNER.replace("if db.execute(", "if False and db.execute("),
        f"{ROLES}::test_migrate_refuses_a_checkpoint_login_that_is_a_member_of_the_owner_role", "Regex pattern did not match",
        more=(
            (MEMBER_FUNC, MEMBER_FUNC.replace("elif db.execute(", "elif False and db.execute(")),
        ),
    ),
]  # fmt: skip


def _killer(node: str) -> tuple[int, str]:
    done = subprocess.run(  # noqa: S603 - this interpreter, a fixed test id
        [sys.executable, "-m", "pytest", node, "-q", "-x", "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True, timeout=900, check=False,
    )  # fmt: skip
    return done.returncode, done.stdout + done.stderr


def run_by_hand(only: list[str]) -> list[tuple[str, str]]:
    chosen = [m for m in HAND if not only or any(text in m.name for text in only)]
    dirty = subprocess.run(  # noqa: S603 - fixed arguments
        ["git", "status", "--porcelain", "--", *sorted({m.file for m in chosen})],  # noqa: S607 - git from PATH
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    if dirty.strip():
        raise SystemExit("refused: a target file has uncommitted changes:\n" + dirty)
    results, clean = [], {}
    for m in chosen:
        path = ROOT / m.file
        before = path.read_bytes()
        text = before.decode("utf-8")
        if m.node not in clean:
            clean[m.node] = _killer(m.node)[0] == 0
        if not clean[m.node]:
            verdict = "BASELINE FAILS (the killer fails on the clean tree)"
        elif miss := [o for o, _ in ((m.old, m.new), *m.more) if text.count(o) != 1]:
            verdict = f"NOT APPLIED (the old text is in the file {text.count(miss[0])} times)"
        else:
            try:
                mutated = text
                for old, new in ((m.old, m.new), *m.more):
                    mutated = mutated.replace(old, new)
                path.write_bytes(mutated.encode("utf-8"))
                code, out = _killer(m.node)
            finally:
                path.write_bytes(before)
            if code == 0:
                verdict = "SURVIVED"
            elif m.expect not in out:
                verdict = f"FAILED FOR ANOTHER REASON (no {m.expect!r} in the output)"
                if os.environ.get("MUTANT_LINES"):
                    verdict += (
                        "\n" + "\n".join(x for x in out.splitlines() if x.startswith("E "))[:1500]
                    )
            else:
                verdict = "KILLED"
        results.append((m.name, verdict))
        print(
            f"{'ok ' if verdict == 'KILLED' else 'BAD'} {verdict:8} | {m.name} | {m.file}",
            flush=True,
        )
    return results


if __name__ == "__main__":
    if not os.environ.get("HADAVIN_TEST_PG_DSN"):
        print("HADAVIN_TEST_PG_DSN is not set: the killers would be skipped, nothing was run")
        sys.exit(1)
    done = run_by_hand(sys.argv[1:])
    bad = [n for n, v in done if v != "KILLED"]
    print(f"{len(done) - len(bad)} of {len(done)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
