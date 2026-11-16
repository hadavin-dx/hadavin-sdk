# P5b2 round 1 resolve (egm:egm-resolve, AUTO mode)

- **Status:** resolved (AUTO mode, order 20 item 6). The ticket is NOT edited here; the next revision (2) applies the table below. Not committed, not pushed.
- **Target:** `handover/tickets/P5b2.md` (revision 1, full file, 130 lines, reviewed at `45fe05b`). **Findings:** `handover/reviews/P5b2-round1-reviewer.md` (single Tier B reviewer, C1-C13: 0 BLOCKER, 5 MAJOR, 6 MINOR, 2 NIT).
- **Gate:** I skipped the interactive gate (AUTO; order 7(1)). There is one decision per finding id. I contest nothing and escalate nothing; my reasons are under "Positions". Round plan per order 20(6): revision 2, round 2, round 3, freeze (cap 3 from round 1).
- **Facts I checked myself** (read-only, grep/sed on `/home/user/hadavin-sdk-handover/src`, whose last `src/` commit is `ce70eb5`):
  1. `grep -rn --include='*.py' 'ConfigError(' src | wc -l` = 169; `... 'ConfigError' ...` = 237. Both match the ticket.
  2. `k1b/bundle.py:106-107`: `def _fail(case, msg) -> BundleError: return BundleError(f"bundle {case}: {msg}")` is a `return`, not a `raise` (C7). There are **29** callers, all `raise _fail(case, ...)` in `k1b/bundle.py` (`:114` to `:314`), and none in any other file (C4). Of those, 13 pass a plain string and 16 pass an f-string (`rel`, `key`, `sorted(...)`). None interpolates `exc`; four have `from exc`.
  3. `tools.py:118-120`: `except ValidationError as exc:` then `fields = ", ".join(... for e in exc.errors())` then `raise ConfigError(f"{where}: invalid tool entry ({fields})") from None`. This is a derived value of `exc`, and it is not in the ticket's 17 (C6).
  4. `store/postgres.py:170-174`: the `StoreUnavailable` site interpolates only `exc.__class__.__name__`. It is already one of the 17.
  5. `pyproject.toml:86` has `pythonpath = ["."]`, and no `tools` package is installed. In Python, `-I` implies `-P` (no `''` or script folder on `sys.path`), so `python -I -c "import tools..."` cannot find `tools` (C2).
  6. `k1b/replay.py` has 6 `ConfigError(` lines today (`:90, 113, 115, 117, 120, 126`), and `ConfigError` is already imported at `:22`.
  7. `design-v3-FROZEN-amendments.md` D2 (line 11) says every non-literal f-string part inside a `ConfigError` message must be wrapped in `t1()`, and the AST test requires this. D7 (line 26) repeats it (C3).
- **Honest note (what I did NOT check):**
  - I ran no AST script, so the ticket's 171 / 42 / 114 / 15 / 17 / 112 figures are not re-derived by me. Only the grep figures (169, 237, 6, 29) are mine.
  - I did not count how many more sites the wider taint rule of C6 catches beyond `tools.py:120`. I did not run Python 3.12.
  - I read P4a, P4d, P3a and P4b2 only by grep for `ConfigError` / `StoreUnavailable` / `MigrationNumberError`, not in full. I did not check P1, P2a, P2d, P4b1, P4c or P5b1 for new constructions.
  - I did not read design section 8 (taint propagation) or the memo-5 overlap table beyond the P5b2 row (`memo-5-overlap.md:38`, 3 files).
  - I did not verify that P5b1 really merges after P4a. That is P5b1's PENDING LEAD 1, not yet answered.

| id(s) | category | decision for the next revision |
|---|---|---|
| C1 (MAJOR) | PROPOSE FIX | The rule becomes two-way: `class=LITERAL` **if and only if** `auto_class=LITERAL`. Define the existing, currently undefined list `wrong_literal` as "class is LITERAL XOR auto_class is LITERAL" (no new list). Add a unit (9) case for each direction and mutant M19 (the check accepts `LITERAL` on an `unproven-origin` row). |
| C2 (MAJOR) | PROPOSE FIX | In the subprocess, keep `-I` but pass the repo root as `argv[1]`. The `-c` text does `sys.path.insert(0, sys.argv[1])` before the import, runs with `cwd=` the repo root, and prints the marker `STDLIB-ONLY-OK`. The test asserts exit 0 AND the marker on stdout. M17 is killed by the static half of the test (every import of the generator in `sys.stdlib_module_names`) on an `assert`, not by the subprocess. |
| C3 (MAJOR) | PROPOSE FIX | Add the named constant `HASH_TRANSPARENT_CALLS = ("t1",)`. Before tokens are hashed, a call `t1(X)` inside the message is replaced by `X`, so wrapping a part in `t1()` keeps the site key and the human fields. Add a unit (5) case (wrap changes no key; any other new call changes the key) and mutant M20 (no stripping). Add a P5b3 requirement under "How P5b3 keeps the table in step": wrapping sites with the D2 helper must produce no `stale`/`unclassified` pair, and the helper's final name is set in the constant (see PENDING LEAD 9). Not taken: `--carry-from OLD.csv` (more surface). |
| C4 (MAJOR) | PROPOSE FIX | Factories become visible. `scan` finds every function that `return`s or `raise`s a site whose message interpolates one of its own parameters (today only `k1b/bundle.py::_fail`), and records each CALL of it as a site (`kind` = the factory's class). auto_class/auto_reason are computed over the arguments bound to the interpolated parameters, so the 29 `_fail` calls are `unproven-origin`, because `case` is a name. The factory's own construction stays a row. A factory that is itself called through another factory raises `SitesError` (fail closed, one level only). No hand-kept `WRAPPERS` list. Add a hostile case (a new `_fail2(case, f"{exc}")` factory and caller in a synthetic tree is reported, and the caller is `exception-variable`), mutant M21 (factories ignored), and the row-count impact in Counts. |
| C5 (MAJOR) | PROPOSE FIX (part CUT) | Add mutants with named killing tests: M22 `code_mismatch` not reported (unit (9)); M23 `write()` drops human fields of unchanged rows (unit (7)); M24a-d `load_csv` accepts a wrong header / duplicate `site` / non-ASCII byte / `reason` over `REASON_MAX` or with a newline (hostile cases); M25 `PATTERNS` check on `reason` removed (a hostile `reason` holding a key-shaped made-up string, not real-looking). CUT: the `os.replace` temporary-file promise is deleted from `write()`. A half-written CSV already fails closed (bad row -> `SitesError`; missing rows -> `unclassified`), so no atomicity claim and no mutant are needed. |
| C6 (MINOR) | PROPOSE FIX | Taint propagation: any assignment (plain, augmented, annotated, tuple target) whose right side mentions a tainted name taints its target, to a fixed point inside one function. `tools.py:120` becomes a locked `FOREIGN / exception-variable` site (17 -> at least 18; the builder's generator gives the final number, which may be higher). Add `fields = ", ".join(x for x in e.errors())` to unit (3). |
| C7 (MINOR) | PROPOSE FIX | The hash input is the tokens of the construction's `Call` node itself (`ast.get_source_segment`), in any context (`raise`, `return`, assignment, argument). A bare `raise A` hashes the tokens of `A`. A factory call site (C4) hashes the factory call. Then the `HASH_TRANSPARENT_CALLS` stripping (C3) applies. |
| C8 (MINOR) | PROPOSE FIX | `kind` records the CANONICAL class name (alias and attribute resolved: `CE` / `errors.ConfigError` -> `ConfigError`). The hash still uses the text as written. Unit (4) fixes the file names so a single sorted pass misses the subclass: `a_sub.py` holds `class B(A)` and `z_base.py` holds `class A(ConfigError)`. |
| C9 (MINOR) | PROPOSE FIX | M14 splits into M14a (reads `*.pyc` / non-`.py` files, killed by the hostile `__pycache__` and non-`.py` cases) and M14b (skips subfolders, killed by the nested-package case in unit (4)). |
| C10 (MINOR) | PROPOSE FIX | Rename `missing_code` to `code_mismatch`: a `FOREIGN` row with no `code`, OR a non-`FOREIGN` row with a `code`. That is one list, not two. The unit (9) list count stays seven. |
| C11 (MINOR) | PROPOSE FIX | The mutant runner puts the repo root (`Path(__file__).resolve().parents[1]`) first on `sys.path`, and runs each mutant's pytest in a subprocess with `cwd=` the temporary tree. State this in the ticket. Evidence 3 adds: "the scratch CSVs have blank `class` on unproven rows by design; `cmp` compares keys and auto columns". |
| C12 (NIT) | PROPOSE FIX | Reword: "No line numbers: reformatting or moving code inside the same symbol keeps the row; renaming the symbol or moving the site to another function or file makes the old row `stale` and the new one `unclassified`." |
| C13 (NIT) | PROPOSE FIX | List all six files in "Files" against memo-5 (3 listed there, plus `tests/test_diagnostics_hostile.py`, `CHANGELOG.md` and `tests/config_error_sites_mutants.py`), and raise PENDING LEAD 8. |

## Positions
- I contest nothing. Each finding was checked against a file the reviewer could read (facts 2-7), and each one holds. C1's list name `wrong_literal` was in the ticket but never defined, so the reviewer is right that nothing enforced it.
- Cut surface (order 7/8): `os.replace` atomicity (C5) is deleted, not tested. C10 merges two lists instead of adding one. C4 uses automatic factory detection instead of a hand-kept list. C3 uses one constant instead of a carry-over mode.

## Couplings (found while resolving; relay to the named tickets)
1. **P5a -> P5b2 (new; not in the review).** `P5a-round1-resolve.md:11` and `:39` cut `t1` / `safe_detail` from P5a and say "a closed template enum owned by P5b2". P5b2 changes nothing under `src/`, and D2's `t1` is what C3 strips. See PENDING LEAD 9.
2. **P5a ledger rows 005 and 033 (`classification`, owner R3a = P5b2; `tickets/P5a.md:92-93`).** `test_later_rows_are_not_overdue` makes the owning PR fail until it asserts them, and the P5b2 ticket does not mention them. Revision 2 adds two assertions in the appended `tests/test_diagnostics_hostile.py` rows (exact shape PENDING P5a, as already written).
3. **P5b3:** the C3 requirement (wrapping must not wipe human fields) and the C4 factory rows (29 `_fail` calls) are P5b3's inputs. `_fail` itself is still the recommended `FOREIGN`.

## The stale counts (lead's relay, `freeze-list.md:26` "P5b2 counts")
The ticket's 171 rows / 42 literal / 37 files / `k1b/replay.py` 6 are counted on `ce70eb5`. Packages that merge before P5b2 change them:
- **P4a-2** (`tickets/P4a.md:38`, `:203`, `:316`): adds TWO separate `raise ConfigError("...")` with literal messages in `k1b/replay.py` `_replay` (PL55 fake-kind guard, PL62 detector allowlist). The effects:
  - constructions 171 -> **173** (`ConfigError` 168 -> 170);
  - literal 42 -> **44**;
  - files still **37**;
  - `k1b/replay.py` 6 -> **8**;
  - `grep 'ConfigError('` lines 169 -> **171**, and all `ConfigError` lines 237 -> **239** (the import already exists).

  P4a's own zero-price check raises `ValueError` inside a `model_validator` and reaches the user through the existing `config.py:120` site, so it adds no new site. P4a's `:48` and `:560` say "one `ConfigError` check" for PL55 alone, which is consistent with two in total.
- **P4d** (`tickets/P4d.md:29`, `:37`): adds **no** construction. Its money errors are `RuntimeError` / `ValueError` / `StaleState`, deliberately not derived from `ConfigError`. It edits `store/postgres.py` (lock), which moves lines but not the `:172` site's text, so the key is unchanged. This comes from the ticket text only; built code is not seen.
- **Not asked, but found by grep, and also stale:**
  - **P3a** (frozen, builds early) adds `class MigrationNumberError(ConfigError)` and new and changed refusals in `store/migrate.py` (today 8 sites). The delta is UNVERIFIED.
  - **P4b2** (rev 1) adds at least two `ConfigError("...")` (maintenance role grants, `maintenance_dsn_secret_name`), if it merges before P5b2.
- **Decision for revision 2:**
  - Keep the `ce70eb5` figures, labelled "on ce70eb5".
  - Add a "known deltas before P5b2" table with the lines above.
  - Make the acceptance rule "the builder's generator count at the merge base, each difference from ce70eb5 + known deltas explained in the evidence" (this extends PENDING LEAD 5).
  - Fix the 112 / 17 split per C4 and C6 (see Counts).

## PENDING LEAD (continuing the ticket's 1-7)
8. **Memo-5 / P0e overlap table (C13).** The P5b2 row lists 3 files; the package touches 6, with `tests/test_diagnostics_hostile.py` shared with P5a and P5b1/3/4/5 and `CHANGELOG.md` a hot file. Recommended: the lead adds the three rows; there is no conflict in time, because the chain is P5a -> P5b1 -> P5b2 -> P5b3.
9. **Owner of the D2 `t1` helper / "closed template enum" after P5a's cut.** Recommended: P5b3 (it rewrites the sites and owns the D11 AST rule), not P5b2 (P5b2 changes no `src/`). P5b2 only keeps `HASH_TRANSPARENT_CALLS`, set to the final helper name.
10. **Row-count growth from C4.** On `ce70eb5` the table grows to about 200 rows and the human workload to about 140. Recommended: accept. The 29 `_fail` calls share one origin decision for `case` (a bundle folder name: `OPERATOR`) plus a per-message read. The FOREIGN > 30 stop (item 6) still applies to the reviewed table.

## Counts
- Findings 13: **PROPOSE FIX 13** (one of them partly by cut: C5), CONTEST 0, ESCALATE 0, DECLINE 0, unaddressed 0.
- New PENDING LEAD items: 3 (8-10).
- New mutants: M19-M25, with M24 as four (a-d) and M14 split into a/b. That is 18 + 10 new + 1 from the M14 split = **29 rows**.
- Expected table on `ce70eb5` after the rule changes (my arithmetic, `python3 -I` not needed):
  - 171 + 29 factory calls = **200 rows**, of which 42 LITERAL, at least 18 locked FOREIGN, and at most 140 human decisions;
  - after P4a-2: **202 rows**, 44 LITERAL;
  - P3a / P4b2 deltas: UNVERIFIED.
