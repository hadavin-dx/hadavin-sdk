# Evidence: Q8c-1 batch 14, head a50d5b2e6e5b0f828bc60e43df93cb3333a3805f

EVIDENCE RUNNER: results are recorded, not judged. Nothing was fixed, committed on the branch or pushed.
Tag Q8c1b14, previous reviewed head c65d9c27. `git rev-parse HEAD` in the evidence worktree = a50d5b2e..., tree clean.
Run 2026-11-12 13:41 to 14:46 UTC (19:11 to 20:16 IST). Raw logs: `/home/user/build/evidence-raw/Q8c1b14-a50d5b2e/`
(outside the repository). Small excerpts and the plant scripts: `excerpts/` here.

## What failed, was different from the builder's claim, or was not run (first)

1. **A builder claim does not match what I counted (wildcards in the three src files).** Builder notes: `secrets_vault.py` and
   `signer_vault.py` "hold no such line" (a line with `*`) and `kubernetes.py` has "4 lines". My count of ADDED lines
   (`git diff -U0 origin/main..HEAD`) containing `*`: secrets_vault.py 7, signer_vault.py 5, kubernetes.py 1. The 7 and the 5 are
   path texts such as `"name": "sys/*"` and `"{mount}/data/*"` inside a `"never"` list of the policy tables; the 1 in kubernetes.py
   is a docstring sentence (line 383). The whole head file kubernetes.py has 7 lines with `*` (lines 26, 69, 71, 77, 114, 269, 383),
   so I cannot reproduce the builder's "4 lines" for added lines either. Details: item 7. I judge nothing.
2. **Plants of the notes check that were NOT listed (exit 0, no output) although the changed unit is used by a test**
   (item 3, set 1, my own scaffold, `excerpts/i3-plants-set1-table.md` and `i3-plants-set1-verify-diffs.log` show the exact edit):
   - `as10`: `W = (WALRUS := 1)` changed to `:= 2` at module level; the test that reads `WALRUS` was not listed.
   - `ut1`, `ut2`: the body of `setUp` and of `setUpClass` of a `unittest.TestCase` class changed; its tests were not listed.
   - `fx1`: a fixture changed; the test that reaches it through a fixture chain WAS listed, the test that names it with
     `@pytest.mark.usefixtures("base_fx")` and the test that reads it with `request.getfixturevalue("base_fx")` were not.
   - `cf10`, `cf11`: an autouse fixture and a `pytest_collection_modifyitems` hook changed inside a module that a conftest names
     in `pytest_plugins = [...]`; the test under that conftest was not listed.
   - `rt3`: `importlib.import_module(f"tests.zzev.dyn_{n}")` with the name made from a variable; the module changed; not listed.
   Everything else I planted was listed (tables below). The tool's own docstring says a name built at run time is not followed.
3. **Item 6, the builder's rehearsal command** (3 plants, each runs a renewed copy with the whole mutant list): it passed (3 passed,
   6 deselected, exit 0). It waited about 30 minutes for a heavy slot first. Nothing failed there.
4. **Environment facts, same as batch 13:** `uv sync --locked --no-build` (the CI command) fails here ("hadavin-sdk==0.1.0 @
   editable+. ... is marked as --no-build but has no binary distribution"); I used `uv sync --locked --all-extras --group test`.
   `bandit` is not in the venv; I ran `uv run --with bandit bandit -q -r src demos tools -ll`.
5. **Not run:** CI perf step (`pytest -m perf`), the Python 3.12 job, semgrep, zizmor, the CI Vault service (the 13 skips need a real
   Vault server), item 9 (the flaky `test_the_timing_harness_flags_a_quadratic_stand_in` alone, 3 times on head and on main: the ticket
   names no perf item, so I did not run it), the real CI notes step on a pull request (I ran `--auto` locally, also in the CI form
   `--auto origin/main --head a50d5b2e...`, exit 0). The `--day 2026-12-11` etc. runs used the mutant runner's own clock switch, not a changed system clock.
6. My own slips: the first plant driver wrote the old text of plant `as8` with the wrong indentation, so it was not applied; I re-ran
   it by hand (13 of the 13 tests of that file listed). A sleep of 236 seconds exceeded the tool timeout once; no effect on results.
7. Own Postgres 16.15 (user `postgres` through `su`, own folder, TCP port 56731 and a socket in my folder, `PGHOST`, `PGPORT`, `PGUSER`
   set in the server's environment and the tests'). Stopped and deleted at the end (listed at the bottom).

## Table (all on the exact head unless said)

| Item | Command | Exit | Last line / count |
|---|---|---|---|
| 1 | `git diff --name-only origin/main...HEAD` | 0 | 119 files (`excerpts/item1-files.txt`); non-handover: ci.yml, CHANGELOG.md, README.md, docs/declared-permissions.md, 3 src files, 1 fixture, tests/policy_mutants.py, 5 other tests/ files, tools/notes_lines_check.py, tools/policy_page.py |
| 2 | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2 | `ruff format --check src tests demos tools` | 0 | 326 files already formatted |
| 3 | `bandit -q -r src demos tools -ll` (via `--with bandit`) | 0 | only "nosec ... no failed test" warnings |
| 4 | `python tools/scan_repo.py` | 0 | no output |
| 4 | `python tools/policy_page.py --check` | 0 | no output |
| 4 | `gitleaks git --redact --no-banner --exit-code 1 --config .gitleaks.toml --log-opts="origin/main..HEAD" .` | 0 | no leaks found |
| 2 | `python tests/stage_mutants.py` (heavy.sh, own worktree) | 0 | 37 of 37 good; problems: [] |
| 2 | `python tests/policy_mutants.py` (real clock 2026-11-12) | 0 | 324 of 324 good; weak 0 of 324 |
| 2 | `python tests/policy_mutants.py --day 2026-12-11` | 0 | 324 of 324 good; weak 0 of 324 |
| 2 | `python tests/policy_mutants.py --day 2026-12-12` | 0 | 323 of 323 good (one not run: "B12 an overdue unchecked claim is reported one day late (its killer is a date test that is red on that day)"); weak 0 of 324 |
| 2 | `python tests/policy_mutants.py --day 2026-12-13` | 0 | 323 of 323 good (same one not run); weak 0 of 324 |
| 3 | `python tools/notes_lines_check.py --auto c65d9c27` | 0 | no output |
| 3 | `python tools/notes_lines_check.py --auto origin/main` | 0 | no output |
| 3 | same with `--head a50d5b2e...` (the CI form) | 0 | no output |
| 4 | full `pytest -p no:cacheprovider -q -m "not live and not perf" -rs` (heavy.sh, own Postgres 16.15) | 0 | 10983 passed, 13 skipped, 28 deselected in 778.05s |
| 5 | fail-before (below) | 1 | 13 failed, 434 passed, 4 deselected |
| 6 | builder's rehearsal command and my own rehearsal (below) | | |
| 7 | `git diff --stat origin/main..HEAD -- src` | 0 | 3 files, 536 insertions, 0 deletions; `tools/mutation_runner.py` unchanged; `git diff c65d9c27..HEAD -- src tools/mutation_runner.py` is empty |

Mutants with a killer: 324 of 324 (real clock and 12-11), 323 of 323 (12-12 and 12-13). Weak mutants (the runner's lower bound): 0 in all four runs.
"Killed ONLY by a test that reads the clock function": 6 of 324 in each run. The mutant tree was clean after the runs (`git status --short` empty).
All four builder numbers (37, 324, 324, 323, 323, 10983/13/28) match.

## Item 4: the 13 skips (`excerpts/i4-skips.txt`)

1 in tests/contracts/test_llm.py:95 ("Stubber refuses a malformed Converse shape before the kind sees it"); 12 in tests/test_policy_engine.py
(lines 255, 263, 271, 285, 297, 310, 373, 386 (2 tests), 401, 413, 425), each "needs a real Vault server (HADAVIN_TEST_VAULT_ADDR is not set)".

## Item 5: fail-before

Clean detached worktree of c65d9c27 (src and tools of the old commit); copied in ONLY the three changed test files
(tests/test_notes_lines_check.py, tests/test_policy_changelog.py, tests/test_policy_guard.py); tests/test_policy_docs.py is unchanged since c65d9c27.
Command: `pytest -p no:cacheprovider -q -rf -k "not (plant_a_full or plant_a_renewal_of)" <the four files>`: **13 failed, 434 passed, 4 deselected** (same as the builder).
The `-k` deselects 4 tests (the three slow renewal plants and `test_plant_a_renewal_of_only_some_entries_names_the_entry_that_was_not_renewed`).
The 13 failed ids: `excerpts/i5-failed-ids.txt` (all in tests/test_notes_lines_check.py; the first lines are `TypeError`/`AttributeError` for a name or argument the old tool lacks, e.g. `reference_problems() takes 2 positional arguments but 3 were given`).
Collected ids: 436 on the old files, 451 on the head files: 15 added ids, 0 removed (`excerpts/i5-ids-added.txt`). Of the 15 added ids, 11 fail on the old code, 2 pass on the old code (`excerpts/i5-new-pass-on-old.txt`):
- test_a_helper_two_imports_away_lists_the_test_that_reaches_it_in_each_direction
- test_a_two_digit_year_with_hyphens_and_a_day_with_spaces_are_found_and_a_version_is_not
and 2 are among the deselected plants (kinds list alone, names and claims alone). 2 of the 13 failing ids are tests that existed before (changed tests).
The three slow plants run on the same old tree with the same copied tests (`excerpts/i5-failbefore-3-plants-on-old-tests-copied.log`):
**3 failed, 6 deselected in 32.23s**; the failing line of each is "the tests are red after the renewal" followed by the same 13 notes-test ids (the copied notes tests fail on the old tool). I did not build the builder's patched-mutant-file variant.

## Item 3: plants of the notes check

Set 2 (`excerpts/i3-plants-set2-table.md`, `i3-plants-set2-raw-trimmed.log`): scratch clone of the head, one commit per plant, checked with `--auto origin/main` and `--auto c65d9c27`, verbatim first line:

| Plant | origin/main | c65d9c27 |
|---|---|---|
| a: new test file, no row | exit 1, 1 line: "tests/test_zz_plant_a.py: the test test_plant_a_new_test_without_row is new or changed and has no row of its own in the notes" | same |
| b1: only a NEW unused function in tests/k1b_support.py | exit 0, no output | exit 0, no output |
| b2: only a value used by many tests in tests/k1b_support.py (`"severity": "page"` to `"ticket"`) | exit 1, 108 lines, first: tests/test_k1b_bundle.py ... no row | same, 108 lines |
| b3: only the body of `azure_secret_client` in tests/contracts/http_fake.py | exit 1, 74 lines, first: tests/contracts/test_anchor.py: the test test_an_anchor_is_never_replaced ... no row | same, 74 lines |
| b4: only the body of `gcp_secret_client` (http_fake.py) | exit 1, 75 lines | exit 1, 75 lines |
| b5: only the body of `_azure` in tests/contracts/kinds/secrets_neutral.py | exit 1, 74 lines | exit 1, 74 lines |
| b6: only `FakeVault.__init__` in tests/contracts/vault_fake.py | exit 1, 85 lines | exit 1, 102 lines |
| b7: only `fake_vault()` in tests/contracts/vault_fake.py | exit 1, 85 lines | exit 1, 102 lines |
| c1: module-level `pytestmark = pytest.mark.skip(...)` in tests/test_p4b_secrets.py | exit 1, 22 lines (all tests of the file) | same |
| c2: `pytest_collection_modifyitems` skip hook added to tests/conftest.py | exit 1, 2005 lines | exit 1, 2135 lines |
| c3: autouse fixture calling `pytest.skip` added to tests/conftest.py | exit 1, 2014 lines | exit 1, 2144 lines |
| c4: xfail hook added to tests/contracts/conftest.py | exit 1, 75 lines | exit 1, 75 lines |
| d1: an extra row whose unit cell is `B99 no such mutant exists here` | exit 1, 1 line: "tests/policy_mutants.py: a row of the notes (notes of handover/evidence/Q8c-1/b14) names ``B99 no such mutant exists here``, which is no test, mutant or unit of that file" | same |
| d2: unit cell of the existing row changed to `<real mutant>; B99 no such mutant exists here` | exit 1, 2 lines, first: "the mutant B14 notes check accepts a unit cell that names nothing that exists is new or changed and has no row of its own in the notes" | same |
| d3: reason cell names `test_no_such_test_anywhere` | exit 1, 1 line: "... has a row whose reason points at nothing: the test test_no_such_test_anywhere is in no test file" | same |
| d4: reason cell names backticked `B99 no such mutant exists here` | exit 1, 1 line: "... has a row whose reason points at nothing: the mutant `B99 no such mutant exists here` is in no mutant file" | same |
| e: new mutant `B11 notes check does not read class` (a substring of the name `B11 notes check does not read class methods`), no row | exit 1, 1 line: "the mutant B11 notes check does not read class is new or changed and has no row of its own in the notes" | same |

In b3 to b7 the tests listed are the contract tests (tests/contracts/test_*.py) that load the kinds; the first line printed is shown above, the rest are in the raw log (trimmed in the excerpts).

Set 1 (`excerpts/i3-plants-set1-table.md`, my own scaffold under `tests/zzev/`, base = the scaffold commit, so only the plant is "changed"; the scaffold and driver are `excerpts/scaffold.py`, `driver.py`): 66 plants, one commit each, `--auto <scaffold commit>`.
Columns of the table: exit code, number of tests listed, which test I expected and did not see (MISSING), which others were listed.
Listed as expected (the test that uses the changed unit appears in the output): plain constant behind a derived constant (as1); annotated (as2); augmented `+=` (as3); tuple target (as4); value behind a call (as5); subscript assignment (as6, lists all 13 tests of the file); chained (as7); `if` branch (as8, 13 of 13); `for` loop (as9, 13 of 13); attribute assignment (as11, 13 of 13); constant read through a non-test helper (as12); helper of helper of helper across three modules (hh1) and the middle helper (hh2); `from tests.zzev import h_c` + `h_c.f()` (hh3), `import ... as hc` (hh4), relative import (hh5), import inside the test (hh6); `setup_module`, `teardown_module`, `setup_function`, `teardown_function` (su1 to su4: all 5 tests of the file each); `setup_method`, `teardown_method`, `setup_class`, `teardown_class` (su5 to su8: the 2 tests of the class); helper method of a class (su9); unittest class helper, a constant used by a TestCase not named Test*, a mixin base, an inherited method with the base in another module (ut3 to ut6); fixture chain, autouse fixture of a file (9 tests), of a class (2), indirect parametrize fixture, `skipif` constant, `parametrize` values (fx2 to fx6); a conftest's autouse fixture (also a test in a sub folder), named fixture, collection hook, run hook, configure hook, generate hook (cf1 to cf6); `pytest_generate_tests` in a test file (cf8); a `pytest_plugins` list that gains a module (cf9); `importlib.import_module("text")`, `__import__("text")`, a module found by `pkgutil.iter_modules` (rt1, rt2, rt4); module-level `pytestmark` skip, `pytestmark` xfail, `__test__ = False`, module-level `importorskip`, `pytestmark` inside an `if`, a skip decorator (sk1 to sk6); a NEW conftest with `collect_ignore` (sk7), with a skip-everything or xfail-everything collection hook (sk8, sk9: 53 tests of the folder listed), with `collect_ignore_glob` (sk10).
Controls (a unit nothing uses): `leaf6` unused (hh7: 2 tests that import the module `h_c` as a whole were listed anyway); a conftest constant nothing names (cf7: only the constant's own unit); a new helper that nothing calls (sk11: exit 0, no output).
Over-listing, recorded: as5, hh1, hh5, hh6, hh7, ut6 also list test_deep_alias and test_deep_attr (they import the module `h_c` as a whole); rt1, rt2, rt4 list all 5 tests of test_dyn.py.
NOT listed: the six cases in "what failed" item 2 above.

## Item 6: first-renewal rehearsal

**My own, steps applied literally** (scratch worktree of the head, clock set with `HADAVIN_POLICY_FIXED_DAY` and the marker `HADAVIN_POLICY_MUTANT_RUN=1`; new decision day 2026-12-12 and new review day 2027-01-11, 30 days as the old pair):

*Before the renewal*, the four policy test files at 2026-12-12 (the three slow plants deselected): **3 failed, 444 passed**: test_every_kind_is_declared_pending_or_holds_no_identity, test_every_grant_name_is_verified_or_pending_and_every_source_id_resolves, test_every_unchecked_claim_has_a_dated_entry_and_the_suite_goes_red_when_it_is_overdue (`i6-man-unrenewed-1212.log`). The full text a person reads (the first message of each of the three lists: 7, 6 and 7 problems) is in `excerpts/i6-messages-1212.txt`; it starts "PENDING_KINDS secrets/aws_secrets_manager is overdue (review_by 2026-12-11): Q8c PR 2. What to do: finish that work and delete the entry; or, if it cannot be finished now, decide again: ... Renew all or none: ..." and then the numbered steps.

*Edits I made, only from the printed steps* (`excerpts/i6-man-renewal-edits-literal.diff`, 99 lines): tools/policy_page.py (`DECIDED` and the three `review_by` days); tests/test_policy_guard.py (`pp.DECIDED` pin, `KINDS_DECIDED`, `_PR2`, the day in test_the_sixteen_kinds...); tests/test_policy_changelog.py (`KINDS_GROUPS`, `KINDS_LITERAL`); CHANGELOG.md (the kinds sentence); the page rewritten with `pp.main(['--write'], today=date(2026,12,12))`. The printed command `python tools/policy_page.py --write` on the real clock (2026-11-12) exits 1 ("decided 2026-12-12 is in the future"), so I called it with `today` set (write rc 0, check rc 0 at 12-12 and 12-13). I did not change the nine kinds with `review_by` 2027-01-31 (my reading of "the groups of days are kept apart on purpose").
I changed NO day that the steps did not name.

*After the renewal*: the four policy test files at 2026-12-12: **447 passed, 4 deselected**; at 2026-12-13: **447 passed, 4 deselected** (`i6-man-renewed-*.log`). `notes_lines_check.py --auto origin/main` and `--auto c65d9c27` on the renewed copy (committed in the scratch worktree): both exit 0, no output. `policy_mutants.py --day 2026-12-12` on the renewed copy: **324 of 324 good**, exit 0 (`i6-man-mutants-renewed-2026-12-12.log`); `--day 2026-12-13`: **324 of 324 good**, exit 0.
Day or file the steps did NOT name that still failed: none found in this run. The slow plants (a nested renewal of a renewed copy, with the whole mutant list) are not in my manual run; they are the builder's command below.

**The builder's command** (`HADAVIN_POLICY_FULL_RENEWAL_RUN=1 HADAVIN_POLICY_FIXED_DAY=2026-12-12 pytest tests/test_policy_changelog.py -k "plant_a_full or plant_a_renewal_of"`, heavy.sh, own worktree): exit 0, **3 passed, 6 deselected in 1603.17s (0:26:43)** (the full renewal, the renewal of the kinds alone, the renewal of the names and claims alone); tail in `excerpts/i6-builder-rehearsal-tail.txt`. Matches the builder's "3 passed".

## Item 7: src (`excerpts/i7-src.log`, `i7-wildcards2.log`)

`git diff --stat origin/main..HEAD -- src`: 3 files, all modified with added lines only: src/hadavin_sdk/actions/secrets_vault.py 137 insertions, src/hadavin_sdk/audit/signer_vault.py 156, src/hadavin_sdk/sources/kubernetes.py 243 (536 total, 0 deletions).
`git diff --stat origin/main..HEAD -- tools/mutation_runner.py` and `git diff --stat c65d9c27..HEAD -- src tools/mutation_runner.py`: both empty.
Added lines that contain `*` (line numbers of the file at the head): secrets_vault.py 7 (lines 290, 296, 303, 309, 315, 321, 327: `"sys/*"`, `"{mount}/data/*"`, `"{mount}/delete/*"`, `"{mount}/undelete/*"`, `"{mount}/subkeys/*"`, `"{mount}/metadata/*"`, `"{mount}/destroy/*"`; in a block whose key is `"never"`); signer_vault.py 5 (lines 177, 196, 202, 226, 232: `"sys/*"`, `"{transit_mount}/export/*"`, `"{transit_mount}/byok-export/*"`, `"{transit_mount}/restore/*"`, `"{transit_mount}/backup/*"`); kubernetes.py 1 (line 383, a text inside a sentence: "the wildcard verb `*`, shell subresources and any read of `secrets`...").
The other lines with `*` in the whole head files (not added lines): secrets_vault.py lines 4 to 6, 46, 69, 162, 194 (markdown bullets, `*,`, `*handlers`, `**kw`); kubernetes.py lines 26, 69, 71, 77, 114, 269 (a regex, the matcher text and code of the role-rule matcher, a multiplication). I read no line for what it grants and ran no policy simulator.

## Not verified / limits

- The plants in set 1 are my own scaffold (made-up files under `tests/zzev/`), typed from the claims of the brief, not the builder's tests. The result "listed" or "not listed" is by whether the test name appears in the tool's output; I did not check that each listed row is correct beyond that.
- `uv sync` without `--no-build`; bandit via `--with`; no CI-only job ran (list above).
- Wall clock: the heavy.sh queue was busy; my jobs waited about 25 to 35 minutes in total; the full pytest ran in parallel with other agents' suites and my own mutant runs (no timing tests were run alone).
- I did not run the CI perf step, so the flaky timing test and any perf result are not covered.

## Cleanup (end of run)

Listed in the report to the lead (own Postgres stopped and its folder deleted; the worktrees `EV-Q8c1b14-a50d5b2e/*` removed; no other process touched).
