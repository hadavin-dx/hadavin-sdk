# P5b2 ticket, round 1, single reviewer (Tier B)
- Reviewer: `egm:egm-codebase-details` (fresh, read-only, Sonnet 5.5). Ticket `tickets/P5b2.md`, commit `45fe05b`. Ran nothing.
- Result: BLOCKER 0; MAJOR 5 (C1-C5); MINOR 6 (C6-C11); NIT 2 (C12-C13). Not clean; fix batch 1 closes the majors.
- Saved by the lead 2026-11-05, CONDENSED. The reviewer confirmed the counts (237 lines/40 files, 171 constructions/37 files, per-file table, 17 `except ... as exc` sites, 2 StoreUnavailable, 1 BundleError, template 17 fields, 18 mutants) and could not verify src unchanged since a5bf80b, 3.12 behaviour, the ticket's own AST outputs, or P5a's `Code` list. Ledger `BL-core-p5b2-r1-cor-*`.

| id | sev | section | problem | fix |
|---|---|---|---|---|
| C1 | MAJOR | Interface "Locked rows"; report lists | Lock forbids downgrading `exception-variable` rows but nothing stops a human setting `class=LITERAL` on a non-literal `unproven-origin` row (a `reason` suffices): free bypass of P5b3. | `class=LITERAL` only if `auto_class=LITERAL`; new report list (e.g. `locked_literal`) with unit test and mutant. |
| C2 | MAJOR | CI test on the real tree, M17 | Subprocess `python -I -c "import tools.gen_config_error_sites"` cannot pass: `-I` drops cwd/PYTHONPATH, `tools` is not installed; M17 killed for the wrong reason. | Run with `cwd=` repo root (`-S`/`-s`) or insert root in sys.path inside `-c`; assert exit code AND an output marker. |
| C3 | MAJOR | hash and scan; "How P5b3 keeps the table in step"; D2/D7 | D2/D7 require wrapping non-literal f-string parts in `t1()`; wrapping ~112 OPERATOR sites changes their hash, they become stale plus new blank `unproven-origin` rows: all human decisions wiped. | State what P5b3 does to OPERATOR rows: `write()` carries human fields when only a `t1(...)` wrapper was added (hash with wrapper stripped) or `--carry-from OLD.csv`; record as a P5b3 requirement. |
| C4 | MAJOR | scan; Problem; reviewer focus | Scan sees direct constructions only; `k1b/bundle.py` writes ~29 messages via `raise _fail(case, f"...")`; a new `_fail(case, f"{exc}")` is invisible. | Configurable `WRAPPERS` (e.g. `_fail`) so wrapper calls are sites, or state the limit plainly with a hostile test; test failing when an unlisted function that returns/raises a ConfigError subclass from a parameter is added. |
| C5 | MAJOR | Mutation plan; Unit (7)(9) | No mutants for report lists `missing_code`, `wrong_literal`; `write()` keeping human fields; `load_csv` refusals (header, duplicate `site`, non-ASCII, `REASON_MAX`); `os.replace` temp write; `PATTERNS` check on `reason`. | Add those mutants with named killing tests. |
| C6 | MINOR | "exception-variable" rule; line 20 | Rule says "plain assignment"; `tools.py:119-120` (`fields = ", ".join(... exc.errors())` then `f"...({fields})"`) is a derived value, tainted by design section 8, listed in neither the 17 nor the 112. | Say whether derived assignment counts; if yes `tools.py:120` becomes locked FOREIGN (18); add to unit (3). |
| C7 | MINOR | column 5 hash | Hash of "the whole raise-argument call" undefined for `return BundleError(...)` (`bundle.py:107`) and bare `raise A`. | Define hash input for those cases. |
| C8 | MINOR | scan; Unit (4)/M1 | `kind` recorded "as written" (alias `CE`, `mod.A`); M1 only killed if `B(A)` file sorts before `A`'s file, unit (4) fixes no names. | Record canonical class; fix file names forcing a second pass. |
| C9 | MINOR | M14 | Combines two edits (reads `*.pyc`/non-`.py`; skips subfolders). | Split M14a/M14b. |
| C10 | MINOR | `load_csv`/`compare` | `code` "only for FOREIGN" not enforced; no report list. | Add `extra_code` or document ignored. |
| C11 | MINOR | Evidence 3, 4 | `python tests/config_error_sites_mutants.py` puts `tests/` not repo root on sys.path; evidence 3 `--write` leaves unproven rows blank (fine, unstated). | State root insertion or `-m`; "blank classes expected". |
| C12 | NIT | line 27 | "No line numbers so moving code does not change the row" true only within the same symbol. | Reword. |
| C13 | NIT | Files / memo-5 | Memo-5 row lists 3 files; ticket also changes `tests/test_diagnostics_hostile.py`, `CHANGELOG.md`, adds `tests/config_error_sites_mutants.py`. | Tell lead: P0e overlap table needs rows. |

Not a finding: Tier A vs B tension is flagged PENDING LEAD 1 (order 6(b) lists P5b2 Tier B). Model used: Sonnet 5.5 (set by the lead).
