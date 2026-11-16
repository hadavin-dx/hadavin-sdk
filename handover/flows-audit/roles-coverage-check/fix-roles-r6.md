# Fix round 6: roles coverage check

Date 2026-11-16. Files touched: test_check_grants.py (7 new tests), README.md (one paragraph), this log. The check script itself is unchanged. Nothing committed by me.

## Failures, gaps and what I did NOT check (first)
- My first R5-20 test did not kill the mutant (it passed on the mutant: `SURVIVED`). Reason: for the words the check looks for, a parser that ignores the doubled quote `''` finds the same words, because the two pieces it sees are still literals. Found the real difference by trying all short quote/word combinations on the real and mutated regex: the real parser sees ONE literal, the mutant sees TWO, so a word on both sides of `''` is reported once vs twice. Test rewritten to count (`test_escaped_quote_keeps_one_literal`); now killed. The second test I wrote first (`..._harmless_is_balanced`) passes on the mutant too; it stays only as a guard against false alarms, it is not the killer.
- Two ruff RUF059 findings (unused `rc`) in my first draft, fixed (not suppressed).
- R5-08 needs a way to make an unexpected error type happen inside `run()`. A real input exists (a parameter nested about 995 levels deep overflows the stack in the check; shown with the script run as a process: `FAIL internal error ... RecursionError`), but the exact depth depends on the interpreter, so that test scans depths 900..1000 and requires at least one to hit the safety net (it can fail on a Python with a very different stack limit; it did pass here, Python 3.13). The deterministic killer forces each of the six error types the net names into `run()` with `unittest.mock` and expects exactly one `FAIL internal error ...` line, rc=1, no traceback.
- Not run: any database, n8n, CodeQL/SonarCloud/CodeRabbit, the repo-wide pytest suite, the `uv run` variant (system ruff/bandit used). Other agents are editing files under handover/ at the same time, so my scratch copy takes only this folder, the ROLES-PROPOSAL.md and the two flow folders.

## Mutants (scratch copy, one replacement each, then `python3 -m unittest test_check_grants` there)
| Mutant | Before | After | Test that kills it |
|---|---|---|---|
| R5-08 `except UNEXPECTED` -> `except ZeroDivisionError` | survived | KILLED (1 error, 1 failure) | `test_main_safety_net_unexpected_error_is_one_clean_line`, `test_real_input_overflowing_the_stack_is_clean` |
| R5-20 `''` escape removed from the literal pattern | survived | KILLED (1 failure) | `test_escaped_quote_keeps_one_literal` |
| R5-22 notes of non-Postgres nodes not scanned | survived | KILLED (1 failure) | `test_sql_in_notes_of_non_postgres_node` (control: `test_plain_notes_on_non_postgres_node_not_flagged`) |
| extra: lower-casing of table names removed | n/a | KILLED | `test_uppercase_table_name_is_the_same_table_by_decision` |

On the real script all tests pass.

## Decision: uppercase table name `MF_LEADS`
Checked: a copy of the real flow with `Stored` reading `FROM MF_LEADS` gives `mf-form Stored -> mf_door: covered`, rc=0. Postgres folds unquoted names to lower case, so it is the same table; no behaviour change, no reason found to refuse it. A quoted `"MF_LEADS"` is a different table and is already refused (quoted names). Stated in a test (`test_uppercase_table_name_is_the_same_table_by_decision`, which also fails if the lower-casing is removed) and in a README paragraph.

## Gate (from /home/user/hadavin-sdk, folder handover/flows-audit/roles-coverage-check)
- `python3 -m unittest test_check_grants` (from the folder): Ran 71 tests, OK (64 before + 7 new).
- Baseline: `python3 -I check_grants_cover_queries.py ../../demo/n8n-flows-real-v5 ../../demo/n8n-flows-film-v5` -> rc=0, "14 postgres nodes" for each, TOTAL PROBLEMS: 0.
- `ruff check` rc=0 (All checks passed); `ruff format --check` rc=0 (10 files already formatted); `bandit -ll -r` rc=0 (no issues); `grep noqa|nosec` in .py files: 0 hits.
- Scratch scripts (outside the repo): $SCRATCH/r6/mut.py.
