# fix-patchcopies7: fixer log, patch-copies code review r7 (M1-M3, words, nits)
Date 2026-11-16. Fixer session (an assistant run). Edited only `reviews-of-core-patches/patch-copies/README.md` and `DEAD-MAN-CHECK.md`, and wrote this log. Patch files and `REVIEW.md` untouched. I did not commit; a different process committed work-in-progress snapshots of the repository meanwhile (the latest commit already contains my README edits).

## NOT verified (first)
- No database was started. Every Postgres rule I added (CREATEROLE at Postgres 15 and older, the TEMPORARY right of the group `PUBLIC`, rows 3 and 4 being no-ops by default) is from knowledge of the manual and is marked UNVERIFIED in the text.
- The full test runs (9364, 9394, 9396) were not repeated; the verdict script was tested only on made-up logs, not on real pytest output. The exact text of pytest's "short test summary" lines for errors (`ERROR path::test - message`) is from my knowledge of pytest, not from a real run with an error.
- M3: which statement is true is UNVERIFIED; no raw output exists (only the fixer log `reviews-of-core-patches/fix-patchcopies1.md`).
- `uv run --no-build` is not usable (see below); CI's `uv sync --no-build` was not re-run, so what CI does with it is not confirmed here.
- The bandit and ruff lines were run on the unpatched extract only; patched copies were not re-run.
- `pytest --collect-only` was not run at the newest commit.

## Reviewer words re-checked
| Item | Right? | What I did |
|---|---|---|
| M1 bandit group | yes. `pyproject.toml:54` pins bandit only in group `scan` (same at `b4cce5b`); CI `uv sync --locked --no-build --only-group scan` (`ci.yml:113` at `b4cce5b`, `:172` at the newest commit) and `bandit -q -r src demos -ll` (`:119`, newest commit `:181` with `tools`) | recipe line now `uv run --locked --only-group scan bandit -q -r src demos -ll`; table row and text updated. Run: rc 0 on an unpatched extract (network used; offline cache lacks `pip`) |
| M2 verdict hole | yes, and shown: the old script, fed a made-up patched log with one new `ERROR` line and `1 error` in the summary, printed ADDS NO NEW FAILURE | `-rfE`; failed-list now holds FAILED and ERROR lines; (b) compares the whole last line minus time, built from the baseline line with `passed` raised by 30 or 32; (c) rc expectation per run from its own FAILED/ERROR lines (sharper than "rc equal"); (d) keys on "failed or error" |
| M3 contradiction | yes: DEAD-MAN-CHECK `:12` "only the tick_state table" vs `:137` "SELECT on another table" refused. `fix-patchcopies1.md` has both (header "only tick_state"; section 6 "SELECT * FROM audit_outbox (a made-up table)": permission denied). No raw output, no creation command | removed the "only" claim at `:12`; marked the other-table refusal UNVERIFIED at `:137`; said why |
| README:30 false sentence | yes (it said "newest commit" is used only in "studio head") | replaced by: the bare word "head" never names a commit; a commit is written `b4cce5b` or "newest commit" |
| README:213/:240 "changes 2 assertions" | yes, wrong: the hunk in `A-01.patch` adds 2 lines (one list entry, one assertion), changes and removes none | both places reworded |
| head differences | K1bAudit: reviewer right that `cli.py:213` is only an import of `build_audit`; `K1bAudit` is made only by `build_audit` (`audit_sink.py:59`), called only at `cli.py:216` (same lines at `b4cce5b` and the newest commit). Test count: 41 is right at `b4cce5b` (39 functions + 1 parametrized test with 3 cases; `pytest --collect-only`: `41 tests collected`); at the newest commit 39 functions by grep, collected count UNVERIFIED | README and DEAD-MAN-CHECK reworded |
| nit ruff path | partly. CI at `b4cce5b` uses `src tests demos` (`ci.yml:79,:81`); `tools` is added only at the newest commit and does not exist at `b4cce5b` (`git ls-tree`), so the recipe uses `src tests demos` | done; the format count with that path is 294 (seen), not 299 |
| nit `--locked` | yes (CI `ci.yml:77`) | added. `--no-build` NOT added: `uv run --no-build` failed here ("can't be installed because it is marked as --no-build", uv 0.11.32); said so in the text |
| nit wc -l padding | yes | `lines()` helper with `tr -d ' '` |
| nit proof section order | yes | text says: run only after the baseline and verdict; to repeat the baseline use a third clone |
| nit D5 | yes: `PUBLIC` also holds TEMPORARY on the database by default | sentence added (UNVERIFIED, manual) |
| nit CREATEROLE PG<=15 | yes (from the manual) | added to rows 1 and 6-8, UNVERIFIED |
| nit rows 3/4 redundant | yes by default (not on the lead's list; added one sentence, UNVERIFIED) | done |

Words: step (recipe parts now "part of the recipe", "password procedure"; "step" = tick job only); gate (repository gate defined; the outbound gate of `approvals/gate.py` called "outbound filter" outside quotes); live (exception row naming `LIVE_LLM`, `..._for_a_live_model`, `test_a_priced_live_route_still_loads` and the id `live`; checked present in the patches); copy (new row, three meanings); check (price check, dead-man check, `--check` in the same row as before); three numbering schemes (new row mapping rows 1-9, Decisions 18/19/21/23, D1-D6). Not changed: login/role/identity, tick, guard, limit (reviewer listed them without a case; I found no concrete misuse and did not guess).

## Verdict-script proof (made-up logs, 10 cases, script extracted from the README text itself)
New text: 1 today's state -> ADDS NO NEW FAILURE; 2 clean -> PASSED; 3 one extra failure (count consistent) -> NOT PASSED; 4 wrong count -> NOT PASSED; 5 new ERROR on today's state -> NOT PASSED; 6 clean plus new ERROR -> NOT PASSED; 7 same error in both runs -> ADDS NO NEW FAILURE; 8 skipped differs -> NOT PASSED; 9 patched gate exit code 1 -> NOT PASSED; 10 new banned file in the offender list -> NOT PASSED. Old text on case 5: ADDS NO NEW FAILURE (the hole). Harness and logs are in the scratchpad (`.../scratchpad/p7/harness.sh`).

## Commands (from `handover/flows-audit`)
- `python3 -I tools/check_refs.py` PASS 5176 references; `check_names.py` PASS 655 rows; `check_secrets.py` PASS 0 hits in 2048 files; `ruff format --check .` rc 0 (761 files already formatted).
- `bash -n`: 5 fenced README bash blocks, the DEAD-MAN-CHECK password block, and the extracted verdict script: all rc 0 (7 blocks; the SQL blocks and the sample-output block are not bash).
- `git apply --check` on fresh `git archive` extracts (`src tests`, `git init`): at `b4cce5b` `C-01.patch` rc 0, `C-01-price-only.patch` rc 0, `A-01.patch` rc 0; price-only applied then `A-01.patch --check` rc 0; at the current head `C-01.patch` rc 1, `C-01-price-only.patch` rc 1, `A-01.patch` rc 0 (as the README table says; `src` and `tests` are identical between `5b5b8933a` and the head: empty `git diff --stat`).
- Recipe lines on an unpatched `b4cce5b` extract: `ruff check src tests demos` rc 0; `ruff format --check src tests demos` 294 files already formatted; `uv run --locked --only-group scan bandit -q -r src demos -ll` rc 0; `pytest --collect-only tests/test_p7_tick.py`: 41 tests collected.
