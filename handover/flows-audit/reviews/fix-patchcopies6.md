# fix-patchcopies6: fixer log, patch-copies reader r2 (B1-B3, M1-M8) and code r6 (1 Major)
Date 2026-11-16. Fixer session (assistant run). Edited: `reviews-of-core-patches/patch-copies/README.md`, `DEAD-MAN-CHECK.md`, this log. Patch files and REVIEW.md untouched. Nothing committed.

## NOT verified (first)
- No database was started: every Postgres rule in the new "Which login runs each statement" table (CREATEROLE, grant option, owner of schema `public` = `pg_database_owner` at 15+, ALTER ROLE rights at 16, `\password` hashing) is from my knowledge of the manual, marked UNVERIFIED in the file. The four catalog queries were not run.
- The full pytest runs were NOT repeated; the 9364/9394/9396 figures are from the fifth pass. Only the verdict script was tested, on made-up logs.
- Where the scheduler stores `deadman_reader_password`: unknown, written as an UNANSWERED lead item. D3/D4/D6 defaults are my proposals marked "AUDIT PROPOSAL, lead to confirm"; whether the scheduler machine has a mail command is unknown.
- The gate block was run with `UV_OFFLINE=1` added (the plain `env -i` form loses the sandbox proxy certificate and failed at the package download); on two copies of the unpatched archive, not on a patched one.

## Findings (reviewer words re-checked)
| Id | Right? | Fix |
|---|---|---|
| B1 + code Major | yes (clause d vanishes when guard tests are fixed; lines 144/146 disagreed) | (d) applies only while failed tests exist; branch "no failures at all" prints "(d) not needed"; PASSED = (a),(b),(c), pytest exit 0; one verdict script prints the clauses and the verdict. Tested on 4 made-up cases: today -> ADDS NO NEW FAILURE; clean -> PASSED; extra failure -> NOT PASSED; wrong count -> NOT PASSED |
| B2 | yes | code block with function `E`, folders `$W/unpatched`, `$W/patched`, `rc=$?` per command, no pipes, six lines to `$W/gates.txt`; table heads name the folders. Block run: all six rc 0 |
| B3 | yes | new section "Which login runs each statement" (login needed per row, which rows were tested only as a superuser: the throwaway used a local trust login as the `postgres` OS user), plus four catalog queries to find the login |
| M1 | yes | typeable password block (`openssl rand -base64 24` into a 600 file, clipboard, `\password`, `shred`); storage place: UNANSWERED lead item |
| M2 | yes (5 meanings) | words-box row "live" (one sense: marker `live`, and "the live code"); other uses renamed "paid model", "real-use stage", "turned on" |
| M3 | yes | "head" -> "newest commit" everywhere except "studio head" |
| M4 | yes | "scheduler owner" -> scheduler operator (new D6); "login that owns tick_state" -> table-owning login; database/schema owner -> database-owning / schema-owning login |
| M5 | yes | row 9 says three offending files |
| M6 | yes | Decision 23 defined (23a, 23b) |
| M7 | yes | D2-D6 have a written default marked AUDIT PROPOSAL, lead to confirm; first lines of README say the folder is for a copy, never the live code |
| M8 | yes | script prints "(b) ok"/"(b) FAILED" from the numbers; text says 9364/9394/9396 are examples from one run |
Extra: reviewer code-r6 doubted "99 guard tests"; `pytest --collect-only` on the three files at `b4cce5b` gives 99 collected (fine; text now says so).

## Commands (from `handover/flows-audit`)
- `python3 -I tools/check_refs.py` PASS 5176 references; `check_names.py` PASS 655 rows; `check_secrets.py` PASS 0 hits in 2033 files; `ruff format --check .` 747 files already formatted.
- `bash -n` on 5 fenced README bash blocks and the DEAD-MAN password block: all rc 0 (the two SQL blocks and the sample-output block are not bash).
- `git apply --check` on a fresh `git archive b4cce5b` extract (git init): C-01.patch rc 0, C-01-price-only.patch rc 0, A-01.patch rc 0; price-only applied then A-01 --check rc 0.
