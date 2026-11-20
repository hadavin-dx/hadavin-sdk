"""Mutants of the audit drain (step A): M1 to M9 of the ticket, run by ``tools/mutation_runner.py``.

Each mutant reverts ONE guard of ``audit/chain.py`` or ``runtime/tick.py`` in a temp copy of the package; the pinned
test of ``tests/test_audit_drain.py`` must be the one that fails first, and its first failing line must hold
``expect``. Not collected by pytest in an ordinary run (the file name is not a test file name). Run from the repo root:

    uv run --all-extras --group test python tests/audit_drain_mutants.py          # list M; exit 1 if any is not good
    uv run --all-extras --group test python tests/audit_drain_mutants.py M3       # only names that hold the text
    HADAVIN_TEST_PG_DSN=<dsn> uv run --all-extras --group test python tests/audit_drain_mutants.py --hand

How the killers reach the runner. The runner starts pytest with ``--noconftest``, and the killers need the fixtures
of ``tests/conftest.py`` (``live_cfg_dir``, ``fake_system``), so ``tests/test_audit_drain.py`` cannot be handed to it
directly: its unmutated baseline would fail on a missing fixture. This file is therefore ALSO the test file the
runner's pytest child is given: when it is imported (not run as a script) it names ``tests.conftest`` as a plugin
(the copy inside the runner's snapshot, loaded by name, no file in a parent folder) and takes over every test and
fixture of ``tests/test_audit_drain.py`` unchanged. A pinned id therefore reads ``tests/audit_drain_mutants::<test>``;
the function is the one defined in ``tests/test_audit_drain.py``.

``HAND`` holds the killers that need a real PostgreSQL (the runner gives its child no DSN by design). ``--hand``
applies each to THIS working tree, runs the killer in ``tests/test_audit_drain.py`` with the caller's
HADAVIN_TEST_PG_DSN, and puts the file back byte for byte; it refuses to start when a target file has uncommitted
changes and runs the killer on the clean tree first. Exit 1 if any is not KILLED.

M4 is written as "the drained event is not removed and the flush stops": the plain form (the ``pop`` removed)
loops forever, which the runner would report as TIMEOUT and not as a kill.

M1 ends its killer in an exception, not in a failed assertion (the test looks the step up by name before it
asserts on the order), so it is marked ``allow_crash`` and the exception class is checked.

F1 to F6 are the mutants of fix round 1 (``_drain`` returns the exception, a refused event or row no longer blocks
the ones after it, the step fails with the counts); their killers are the f1 to f7 tests."""

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
SELF = "tests/audit_drain_mutants.py"
TEST = "tests/test_audit_drain.py"
CHAIN = "src/hadavin_sdk/audit/chain.py"
TICK = "src/hadavin_sdk/runtime/tick.py"

if (
    __name__ != "__main__"
):  # imported by the runner's pytest child as its test file (see the module docstring)
    import tests.test_audit_drain as _killers

    pytest_plugins = ("tests.conftest",)
    globals().update(
        {n: getattr(_killers, n) for n in dir(_killers) if n.startswith("test_") or n in ("app", "pg")}
    )  # fmt: skip

N1 = "test_n1_audit_drain_is_the_last_tick_step"
N2 = "test_n2_one_tick_writes_a_parked_outcome_to_the_chain"
N3 = "test_n3_the_next_successful_write_flushes_what_this_process_parked"
E5 = "test_e5_a_failed_triggering_append_makes_no_flush_attempt"
KEPT = "test_an_outbox_row_that_cannot_be_written_yet_is_kept"
H1 = "test_h1_unreadable_rows_are_kept_and_never_block_the_rows_after_them"
ERROR = "test_an_outbox_that_answers_with_an_error_fails_the_step"
E7 = "test_e7_a_runtime_role_that_cannot_read_the_outbox_fails_the_step"
CROSS = "test_cross_process_an_outcome_parked_by_one_process_is_written_by_the_tick_of_another"
F1 = "test_f1_a_refused_row_between_two_good_rows_fails_the_step_and_blocks_nothing"
F1_TEXT = "test_f1_reconcile_raises_only_after_the_whole_loop_and_with_counts_only"
F3 = "test_f3_a_failed_delete_is_counted_and_the_next_drain_deletes_without_a_duplicate"
F5_ASIDE = "test_f5_a_flush_moves_a_refused_event_aside_and_writes_the_ones_after_it"
F5_OUTAGE = "test_f5_a_flush_stops_at_an_outage_and_keeps_the_rest_in_order"
F6_PG = "test_f6_pg_a_runtime_role_that_cannot_insert_fails_the_step_and_keeps_the_row"

FLUSH = "            self._flush_pending()\n        return key\n\n    def "
NO_FLUSH = "            pass\n        return key\n\n    def "
DELETE = (
    '                self._db.run("DELETE FROM audit_outbox WHERE event_id = ?", (event_id,))\n'
)
BAD_BODY = "            except ValueError:\n                unreadable += 1\n"
BAD_ID = "            if event.event_id != event_id:\n                unreadable += 1\n"
SELECT_GUARD = "            if not is_connectivity_error(exc):\n"
STEP_ROW = '    TickStep("audit_drain", 0, audit_drain),\n'
STEP_BODY = '        _LOG.info("audit_drain drained=%s", fn())\n'
FLUSH_STOP = "                    if failed is not None and is_connectivity_error(failed):\n"
ROW_FAILED = "            if failed is not None:\n"
COUNT = "                not_writable += not is_connectivity_error(failed)\n"
NOT_DELETED = "                not_deleted += 1\n                continue\n"
RAISE = '            raise RuntimeError("audit outbox: " + ", ".join(problems))\n'


def mutant(name, file, old, new, killer, expect, test_file=SELF, crash=""):
    return Mutant(
        name,
        file,
        old,
        new,
        expect,
        allow_crash=bool(crash),
        crash_type=crash,
        test_file=test_file,
        only_test=killer.split("[")[0],
        pinned=test_file[:-3] + "::" + killer,
    )


def by_hand(name, file, old, new, killer, expect):
    return mutant(name, file, old, new, killer, expect, test_file=TEST)


M = [
    mutant("M1 the STEPS row is removed", TICK, STEP_ROW, "", N1, "StopIteration", crash="StopIteration"),
    mutant("M2 the audit_drain body is empty", TICK, STEP_BODY, "        pass\n", N2, "assert (0 == 1)"),
    mutant("M3a the flush call is removed from write_intent", CHAIN,
        FLUSH + "write_outcome", NO_FLUSH + "write_outcome", N3 + "[write_intent]", "rows=None)] == []"),
    mutant("M3b the flush call is removed from write_outcome", CHAIN,
        FLUSH + "_flush_pending", NO_FLUSH + "_flush_pending", N3 + "[write_outcome]", "rows=None)] == []"),
    mutant("M4 the flush does not remove a drained event", CHAIN, FLUSH_STOP,
        "                    if failed is None or is_connectivity_error(failed):\n", N3 + "[write_intent]",
        "rows=None)] == []"),
    mutant("M5 the outbox row is deleted when its append failed", CHAIN, ROW_FAILED,
        "            if failed is not None and not is_connectivity_error(failed):\n", KEPT, "assert [] == ['evt-"),
    mutant("M6a an unreadable body raises at once", CHAIN, BAD_BODY, "            except ValueError:\n                raise\n",
        H1, "evt-e"),
    mutant("M6b a body under another row's id raises at once", CHAIN, BAD_ID,
        BAD_ID + '                raise RuntimeError("audit outbox: 1 unreadable rows kept")\n', H1, "evt-e"),
    mutant("M7a an unreadable body is deleted", CHAIN, BAD_BODY, BAD_BODY + DELETE, H1, "assert [('evt-d'"),
    mutant("M7b a body under another row's id is deleted", CHAIN, BAD_ID, BAD_ID + DELETE, H1, "-not-leak\"}')] == ["),
    mutant("M8a the flush runs after a failed append (write_intent)", CHAIN,
        '            raise AuditUnavailable(f"intent',
        '            self._flush_pending()\n            raise AuditUnavailable(f"intent',
        E5 + "[write_intent]", "assert (['evt-"),
    mutant("M8b the flush runs after a failed append (write_outcome)", CHAIN,
        "                self._pending.append(event)\n            return None\n",
        "                self._pending.append(event)\n            self._flush_pending()\n            return None\n",
        E5 + "[write_outcome]", "assert (['evt-"),
    mutant("M9 a SELECT error that is not an outage is swallowed", CHAIN, SELECT_GUARD, "            if False:\n",
        ERROR, "assert 0 == 1"),
    mutant("F1 an append failure that is not an outage is treated as an outage", CHAIN, COUNT,
        "                not_writable += 0\n", F1, "assert 0 == 1"),
    mutant("F2 a row that is not writable is deleted", CHAIN, COUNT + "                continue\n",
        COUNT + "                if is_connectivity_error(failed):\n                    continue\n", F1, "assert [] == [('evt-b'"),
    mutant("F3 a DELETE failure ends the loop", CHAIN, NOT_DELETED, "                not_deleted += 1\n                break\n",
        F3 + "[refused]", "assert ['evt-a'] == ['evt-a', 'evt-b', 'evt-c']"),
    mutant("F4 the counts are dropped from the RuntimeError", CHAIN, RAISE,
        '            raise RuntimeError("audit outbox: rows kept")\n', F1_TEXT, "assert 'audit outbox: rows kept' == "),
    mutant("F5 the flush stops at a failure that is not an outage", CHAIN, FLUSH_STOP,
        "                    if failed is not None:\n", F5_ASIDE, "assert 1 == 2"),
    mutant("F6 the flush moves an outage failure aside", CHAIN, FLUSH_STOP, "                    if False:\n",
        F5_OUTAGE + "[OSError]", "assert 2 == 1"),
]  # fmt: skip

HAND = [
    by_hand("M9 a SELECT error that is not an outage is swallowed (a missing grant)", CHAIN,
        SELECT_GUARD, "            if False:\n", E7, "assert 0 == 1"),
    by_hand("M2 the audit_drain body is empty (two processes)", TICK, STEP_BODY, "        pass\n",
        CROSS, "audit_drain drained=1"),
    by_hand("M1 the STEPS row is removed (two processes)", TICK, STEP_ROW, "", CROSS, "audit_drain drained=1"),
    by_hand("F1 an append failure that is not an outage is treated as an outage (a missing INSERT grant)", CHAIN,
        COUNT, "                not_writable += 0\n", F6_PG, "assert 0 == 1"),
]  # fmt: skip


def _killer(name: str) -> tuple[int, str]:
    done = subprocess.run(  # noqa: S603 - this interpreter, a fixed test id
        [sys.executable, "-m", "pytest", f"{TEST}::{name}", "-q", "-x", "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True, timeout=900, check=False,
    )  # fmt: skip
    return done.returncode, done.stdout + done.stderr


def run_by_hand(only: list[str]) -> int:
    """Apply each HAND mutant to the working tree, run its killer, restore. Returns the number not killed."""
    if not os.environ.get("HADAVIN_TEST_PG_DSN"):
        print("HADAVIN_TEST_PG_DSN is not set: the killers would be skipped, nothing was run")
        return 1
    chosen = [m for m in HAND if not only or any(text in m.name for text in only)]
    dirty = subprocess.run(  # noqa: S603 - fixed arguments
        ["git", "status", "--porcelain", "--", *sorted({m.file for m in chosen})],  # noqa: S607 - git from PATH
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    if dirty.strip():
        print("refused: a target file has uncommitted changes:\n" + dirty)
        return 1
    bad, clean = 0, {}
    for m in chosen:
        path = ROOT / m.file
        before = path.read_bytes()
        text = before.decode("utf-8")
        if m.only_test not in clean:
            code, out = _killer(m.only_test)
            clean[m.only_test] = code == 0 and " skipped" not in out
        if not clean[m.only_test]:
            verdict = "BASELINE FAILS (the killer fails or is skipped on the clean tree)"
        elif m.old not in text:
            verdict = "NOT APPLIED (the old text is not in the file)"
        else:
            try:
                path.write_bytes(text.replace(m.old, m.new).encode("utf-8"))
                code, out = _killer(m.only_test)
            finally:
                path.write_bytes(before)
            if code == 0:
                verdict = "SURVIVED"
            elif m.expect not in out:
                verdict = f"FAILED FOR ANOTHER REASON (no {m.expect!r} in the output)"
            else:
                verdict = "KILLED"
        bad += verdict != "KILLED"
        print(f"{verdict:8} | {m.name} | {m.file} | {m.only_test}", flush=True)
    print(f"{len(chosen) - bad} of {len(chosen)} good by hand")
    return bad


if __name__ == "__main__":
    only = sys.argv[1:]
    if only[:1] == ["--hand"]:
        sys.exit(1 if run_by_hand(only[1:]) else 0)
    if only and not any(o in m.name for m in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)
    first_lines: dict[str, str] = {}

    def show(row):
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:90]}]",
            flush=True,
        )
        if not good or os.environ.get("MUTANT_LINES"):
            print("      first line:", first_lines.get(name, "")[:200], flush=True)

    res = run_mutants(
        ROOT,
        M,
        [SELF],
        extra_dirs=("tests", "tools"),
        only=only,
        on_result=show,
        first_lines=first_lines,
        timeout=300,
    )
    for m in HAND:
        print(f"by hand (--hand): {m.name} -> {m.only_test}")
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
