Status: resolved

# Goldfish Annotated Review Report, PD Part 6 (mode banner and demo-only guard), round 9

**Target:** `/home/user/build/snap/pdbanner-dd827d79/DIFF.patch` (full), head `dd827d79e00bea6da81e757e0fa0746bbbd3449d`, mode-safety path (no round cap).
**Inputs:** `pdbanner-dd827d79-design-r9.md` (0 Blocker, 3 Major, 8 Nit) and `pdbanner-dd827d79-codebase-r9.md` (1 Blocker, 6 Major, 12 Nit). Both reviewers read code only; nothing was run by them. Runner ab8e69ea has not reported; its findings are an addendum for the builder. The full pytest and the complete banner_mutants table run on the lead's laptop (Linux Docker).
**Method:** every finding was checked against what the reviewers could read. No finding is contested. 31 findings merge into 12 issues.
**Binding decisions applied:** Part 6 does not call `is_stand_in` until Part 2 merges; the masker equals main exactly (BEARER 12+, BASIC 8+); fix by class; no suppressions; fake credentials built from parts.

## Handoff counts

- PROPOSE FIX accepted: 12 issues (all findings, nits included).
- CONTEST: 0. ESCALATE: 0. DECLINE: 0.
- Remaining unaddressed in this report: 0. Round 10 is REQUIRED (one Blocker and Majors that are fail-open).

## Prioritized findings

### Issue 1, Blocker, class TEXT-TRUTH (codebase 1)
`mode_banner.py:323-325`, `mode_banner.js:93-94`, `tests/test_mode_banner.py:2709-2726`: the `_banner_for` docstring says a reworded banner is painted as the English fallback "with the names"; the code returns the frozen `NOT_CONFIRMED` with `overridden: []`, so no names are shown. The test named "...with_the_names" replaces the very line it should assert and never checks names (vacuous). PROPOSE FIX: decide the behaviour in code. Either keep names for a reworded banner (page builds the note from `overridden` even when the text differs) or state plainly that names are dropped; then make docstring, test name and test agree, and make the test assert the actual `overridden` result of the call.

### Issue 2, Major, class SEAL-COMPLETE (design M1)
`app.py:55-73,114-121,189`: Registry.tools and Config.systems/sources are frozen dataclasses with mutable dicts exempt as "plain data". `del app.registry.tools[agent][name]` or `app.config.sources.clear()` after build removes a real host from what `mode_banner()` re-reads while the toolbox still reaches it (fail-open). PROPOSE FIX: at `_seal` store the value the banner reads (`_services_in(config, registry.tools)` as a tuple, built from references) and compare it in `_known_overrides`. Tests: delete a tool spec; clear config sources.

### Issue 3, Major, class SEAL-COMPLETE (codebase 3)
`app.py:55-73,120`: any dict, list, tuple or set is "plain" whatever it holds, so `ToolBox.fns/specs` and executor contract dicts of callables can be swapped without changing the seal. PROPOSE FIX: judge containers one level down by reference with `is` (each value held, compared on re-read), or list the toolbox members explicitly. Test: replace one `fns` entry; add one `specs` entry; mutant rows for each.

### Issue 4, Major, class SEAL-COPY (codebase 2, design N6)
`copy.deepcopy(app)` reads unconfirmed only because the `_PLAIN` sentinel is copied to a new object; if the sentinel ever becomes atomic it turns "known". The test does `except Exception: return` so it can skip. PROPOSE FIX: seal a per-instance token (or the App identity) that deepcopy cannot carry; test fails (not skips) when the copy raises, and asserts unconfirmed for `deepcopy`, `copy.copy` stays known as documented.

### Issue 5, Major, class PAGE (design M2)
`mode_banner.js:83` treats missing or null `overridden` as `[]` and paints demo or quiet; Python (`mode_banner.py:32-33,698`) treats missing or None as not known. PROPOSE FIX: absent or null `overridden` is unusable for demo and quiet; page and Python agree; test and mutant row; correct the JS comment that says "same rule as Python" (Python normalises, the page rejects; stricter is correct) (codebase 19).

### Issue 6, Major, class MASKER (design M3, codebase 4)
`demo_only_guard.py:298-336`: `_hide_pairs` runs before BEARER/BASIC, so `authorization=Bearer <12+ chars>`, `auth=Bearer ...`, `secret=Basic ...`, `token=Bearer ...` hide only the scheme word and the token stays visible. PROPOSE FIX: run the BEARER and BASIC rules first (text equal to main), then pairs; values built from parts. Test each shape; mutant row for the order. Also say in the docstring that the colon form (`"password": "x"`, `token: x`) is out of scope, or mask it (codebase 14); name R9D6 for what it kills (codebase 15: `\S+` after `authorization:` hides nothing when a space follows the colon, so fix the row name or add a killer).

### Issue 7, Major, class PIN-NAMING (codebase 5)
About 28 tests carry "PIN of batch 9 (passes on 07bfda12)" next to "proof (fails only on the code before batch 8)"; only 5 are named `test_pin_*`. `_sealed_app` calls `app._seal`, absent on the old code, so "fails on old code" there is an AttributeError, not behaviour. The masker-cost test fails on old code only because `_SECRET_NAME` is missing. PROPOSE FIX: rename real pins `test_pin_*` and remove the contradictory comments; for behaviour tests that rely on `_seal`, run the fail-before check on a shim or state that the old failure is by missing API and add one behavioural proof; for the masker cost test add a time/step assertion that fails on the old quadratic pattern when run with the new test helper in place.

### Issue 8, Major, class MUTANT (codebase 6)
Row R9A1 replaces the sealed value with `(label, id(o))` pairs but compares with `is`, so every comparison mismatches and it dies in an unrelated test; the id-reuse test never reaches reuse. The honest is-to-id mutant is equivalent. PROPOSE FIX: replace the id-reuse test by a weakref liveness check that the sealed original stays alive; rename or drop R9A1 and say in a comment why `is` to `id` is equivalent.

### Issue 9, Major, class CHANGELOG-TRUTH (codebase 7)
`CHANGELOG.md:225`: "four places that list tracked files" are compared (three equal, one superset); "single pass" is five linear passes; the decision the test cites ("also in the CHANGELOG") is not there; no row-count test exists. PROPOSE FIX: correct the wording; add the decision; add a test deriving the row count from the table and tying the typed count if any. Also state in the CHANGELOG that the pyc magic range depends on the interpreter that runs the guard (3.12 gives up to 4531, 3.14 up to 4627) (codebase 8).

### Issue 10, Minor, class FAILURE-LOGGING (codebase 11, 12, design N7)
`app.py:174,191` swallow `except Exception` at debug level; a NameError or AttributeError typo makes every app permanently unconfirmed with only a debug line; the inner except at 174 has no mutant row. The production tick test uses fakes and no sources, so a lazily created non-plain attribute would flip a normal app to unconfirmed after a run. PROPOSE FIX: log the exception type once at warning level, add a row and test; extend the tick test to run sources and a run.

### Issue 11, Minor, class FILE-SAFETY (codebase 9, 13, design N5)
Mode test (`tests/test_demo_only_guard.py:2238-2249`) never asserts the mode; a `chmod(target, 0)` mutant survives. `copy_without_folder` can still raise a bare OSError if an entry is swapped between `_stat_kind` and the copy; `_shape_hits` and the loader read through a link parent without `_parent_is_link`; `_link_rule` says "symlink-loop" for any ELOOP. PROPOSE FIX: assert the mode and add a row; wrap the copy steps like `_link_problem`; add the parent check; correct the rule name.

### Issue 12, Minor, class TEXT (codebase 10, 16, 17, 18, design N1-N4, N8)
Docstring and comment corrections: `app.py:106-107` "three records and two sets" (code skips four names, `sources` is a dict listed entry by entry); `mode_banner.py:51` limit 6 omits `clock=`; `mode_banner.py:488-490` `timeout_s` reason says "not called, only compared" but `app.py:331` passes it to `Executor(timeout_s=...)`; `demo_only_guard.py:410-412` pyc range and "four values" comment; `_seal` is private only by name (state it, or accept only the value build computed); N8 items from the design review (docstrings "clock", "three records", "single pass", `_link_rule`, masker limits stated, "never raises or warns" test name overclaims). PROPOSE FIX for all in the same push (no new review of the intermediate push).

## ONE FIX BRIEF (single small builder, batch 10; fast-forward only onto `wip/cloud-pd-banner`)

Rules: `PYTHONPATH=<worktree>/src` and print `hadavin_sdk.__file__` before any run; cloud limits (no full suite, focused tests and the focused rows only, at most 2 heavy processes); every new test shown FAILING on dd827d79 and passing on the new head, pins labelled `test_pin_*`; every new or re-pointed mutant row shown killed by its named test; no suppressions; fake credentials built from parts; never commit under `handover/`.

| # | Class | File and change | Test | Mutant row | Fail-before |
|---|---|---|---|---|---|
| A | SEAL-COMPLETE and COPY | `app.py`: seal `_services_in(config, registry.tools)` by reference; compare containers one level down (toolbox fns/specs, executor contracts) with `is`; per-instance token so `deepcopy` is unconfirmed; keep `copy.copy` known | delete a tool spec; clear config sources; replace one `fns` entry; deepcopy unconfirmed (fails, not skips, if copy raises) | one row per check dropped | each fails on dd827d79 |
| B | PAGE | `mode_banner.js`: missing or null `overridden` unusable for demo/quiet; one rule with Python; reworded-banner behaviour decided (Issue 1) and docstring, name and test agree | JS and Python agree on missing/null; reworded banner asserts the real `overridden` | rows for the JS check and the reworded-banner rule | fail on dd827d79 |
| C | MASKER | `demo_only_guard.py`: BEARER/BASIC first (equal to main), then pairs; colon form stated out of scope; R9D6 named for what it kills | `authorization=`, `auth=`, `secret=`, `token=` with a scheme word, values built from parts; time/step test for the masker cost | row for the order; rows for each scheme | fail on dd827d79 |
| D | MUTANT and PINS | replace R9A1 and the id-reuse test by a weakref liveness check; rename real pins `test_pin_*`, remove contradictory comments; behaviour tests that need `_seal` get one behavioural proof | weakref test | rename or drop R9A1, comment why is-to-id is equivalent | by-design |
| E | CHANGELOG | four lists (three equal, one superset), five passes, the decision, interpreter-dependent pyc range; row-count test derived from the table | row-count test | none | the count test fails when a row is added |
| F | FAILURE-LOGGING, FILE-SAFETY | log exception type once at warning; add rows; extend tick test to sources and a run; assert file mode; wrap copy steps; `_parent_is_link`; `_link_rule` name | tests per item | a row each (`chmod(target,0)` etc.) | fail on dd827d79 |
| G | TEXT | all stale comments and docstrings of Issue 12 | none (read check) | none | n/a |

Builder reports once when ALL of A-G are done: new head sha, fail-before list, anything not done and why.

## Round 10 and evidence for the final head

- **Round 10 is required** (Blocker plus fail-open Majors on the mode-safety path, no cap).
- **Cloud evidence (runner, records only):** focused tests on Python 3.12 and 3.13; new and changed mutant rows plus a 60-row sample; fail-before proof for every new test. The runner ab8e69ea findings on dd827d79 are an addendum.
- **RUN ON LAPTOP (Linux Docker, final head only):** hadavin-sdk `<new head sha>` full pytest plus the complete banner_mutants table (283 rows now; more after batch 10), py313 and py312, Postgres, CI flags. Windows is not valid evidence.
- Ledger rows are added by the caller (PDBANNER-r9-n).
