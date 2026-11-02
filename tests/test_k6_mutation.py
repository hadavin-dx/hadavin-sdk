"""K6 mutation check: for each guard that carries a money or label path (sticky harmful, the lock, the replay claim,
the signature check, strict digits, the bucketing rule, the false-abstain denominator, the csv overwrite refusal),
copy the package, remove exactly that guard, and require that the tests named for it FAIL. A test that stays green
with its guard removed proves nothing. The mutated copy is put first on PYTHONPATH of a child pytest; the working
tree is never touched. Mutations that need a database are skipped without HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import hadavin_sdk

ROOT = Path(__file__).resolve().parents[1]
PKG = Path(hadavin_sdk.__file__).resolve().parent
K6 = "tests/test_k6_measure.py"
PG = "tests/test_k6_postgres.py"

# (id, file under the package, text that must occur exactly once, replacement, tests that must fail, needs postgres)
MUTATIONS = [
    (
        "memory-sticky-check-removed",
        "store/memory.py",
        'if label.label != "harmful" and not may_lower_harmful:',
        "if False:",
        [f"{K6}::test_k6_harmful_is_sticky_and_only_a_line_owner_lowers_it"],
        False,
    ),
    (
        "postgres-sticky-check-removed",
        "store/postgres.py",
        'if cur is not None and cur["label"] == "harmful":',
        "if False:",
        [f"{PG}::test_k6_two_connections_never_let_a_non_owner_lower_a_harmful_verdict"],
        True,
    ),
    (
        "postgres-advisory-lock-removed",
        "store/postgres.py",
        "self._lock_keys(keys)\n                for label, demote in items:",
        "for label, demote in items:",
        [f"{PG}::test_k6_two_connections_the_lock_orders_a_check_and_its_insert"],
        True,
    ),
    (
        "replay-claim-ignored",
        "measure.py",
        '            if not claimed:\n                self._audit("-", parsed.kind, action.user, result="refused", error_code="replay")',
        '            if False:\n                self._audit("-", parsed.kind, action.user, result="refused", error_code="replay")',
        [f"{K6}::test_k6_a_replayed_click_is_acted_on_once"],
        False,
    ),
    (
        "postgres-nonce-claim-not-unique",
        "store/postgres.py",
        "ON CONFLICT (nonce) DO NOTHING",
        "ON CONFLICT (nonce) DO UPDATE SET seen_at = EXCLUDED.seen_at",
        [f"{PG}::test_k6_two_connections_one_nonce_one_winner"],
        True,
    ),
    (
        "signature-not-compared",
        "approvals/hmac_v0.py",
        "return hmac.compare_digest(_sig(body, ts, secret), sig)",
        "return True",
        [
            f"{K6}::test_k6_unsigned_or_stale_click_is_401_and_records_nothing",
            "tests/test_s6_approvals.py",
        ],
        False,
    ),
    (
        "seq-digits-loose",
        "measure.py",
        "and _DIGITS.fullmatch(parts[3])",
        "and parts[3].isdigit()",
        ["tests/test_k6_round4.py::test_k6_clear_value_with_a_loose_seq_does_not_parse"],
        False,
    ),
    (
        "value-error-releases-claim",
        "measure.py",
        "        except (ValueError, OverflowError):",
        "        except ZeroDivisionError:",
        [
            "tests/test_k6_round4.py::test_k6_a_client_side_value_error_is_a_4xx_and_the_claim_stays_spent"
        ],
        False,
    ),
    (
        "ceiling-window-unbounded",
        "measure.py",
        "or not 1 <= window <= WINDOW_DAYS_MAX",
        "or not 1 <= window",
        ["tests/test_k6_round4.py::test_k6_ceiling_numbers_are_bounded_and_ascii"],
        False,
    ),
    (
        "bucketing-by-label-time",
        "measure.py",
        "and self._run_week(x.run_id) == week",
        "and True",
        ["tests/test_k6_round4.py::test_k6_counts_and_the_wrong_list_use_the_run_week"],
        False,
    ),
    (
        "false-abstain-denominator-is-abstentions",
        "measure.py",
        "{_rate(pw.missed, answerable)}",
        "{_rate(pw.missed, pw.missed + pw.abstain_ok)}",
        [
            "tests/test_k6_round4.py::test_k6_report_false_abstain_uses_the_answerable_denominator_and_states_coverage"
        ],
        False,
    ),
    (
        "approval-grammar-not-checked",
        "measure.py",
        'if len(fields) == 4 and fields[3] in ("approve", "reject") and _DIGITS.fullmatch(fields[2]):',
        "if False:",
        [
            "tests/test_k6_round4.py::test_k6_an_approval_value_is_never_ours_whatever_the_approval_id"
        ],
        False,
    ),
    (
        "csv-import-overwrites-newer-label",
        "measure.py",
        "elif refusal is None and self._would_overwrite(x.run_id, x.label):",
        "elif False:",
        [
            "tests/test_k6_round4.py::test_k6_approve_import_refuses_a_row_that_would_overwrite_a_newer_chat_label"
        ],
        False,
    ),
]


def _child_env(src: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")
    return env


@pytest.mark.parametrize("mid,rel,old,new,tests,needs_pg", MUTATIONS, ids=[m[0] for m in MUTATIONS])
def test_k6_removing_the_guard_turns_its_tests_red(tmp_path, mid, rel, old, new, tests, needs_pg):
    if needs_pg and not os.environ.get("HADAVIN_TEST_PG_DSN"):
        pytest.skip("HADAVIN_TEST_PG_DSN not set")
    src = tmp_path / "src"
    shutil.copytree(PKG, src / "hadavin_sdk", ignore=shutil.ignore_patterns("__pycache__"))
    target = src / "hadavin_sdk" / rel
    text = target.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert text.count(old) == 1, (
        f"{mid}: the guard text is not in {rel} exactly once (update the mutation)"
    )
    target.write_text(text.replace(old, new), encoding="utf-8")
    env = _child_env(src)
    where = subprocess.run(
        [sys.executable, "-c", "import hadavin_sdk; print(hadavin_sdk.__file__)"],
        capture_output=True, text=True, env=env, cwd=tmp_path, check=True,
    ).stdout.strip()  # fmt: skip
    assert Path(where).is_relative_to(src), f"the mutated copy is not the one imported: {where}"
    run = subprocess.run(  # noqa: S603 - fixed argv
        [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "--no-header", *tests],
        check=False, capture_output=True, text=True, env=env, cwd=ROOT, timeout=600,
    )  # fmt: skip
    out = run.stdout + run.stderr
    assert run.returncode == 1, (
        f"{mid}: expected test FAILURES with the guard removed, got {run.returncode}\n{out[-1500:]}"
    )
    assert " failed" in out, out[-1500:]
