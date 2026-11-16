Status: resolved

# Goldfish Annotated Review Report, PD Part 6 (mode banner and demo-only guard), round 14

**Target:** `/home/user/build/snap/pdbanner-8c814fe6/DIFF.patch` (full, merge-base diff), head `8c814fe6c591dc2fde28588865a53ede5e2dc196`, mode-safety path (no round cap).
**Inputs:** `pdbanner-8c814fe6-design-r14.md` (0 Blocker, 3 Major, 8 Nit) and `pdbanner-8c814fe6-codebase-r14.md` (0 Blocker, 2 Major, 7 Minor, 7 Nit). Both reviewers read the snapshot only and ran nothing. Evidence runner a3ea530e has not reported; its facts are an addendum for the builder (`handover/evidence/PD-banner/8c814fe6/RESULTS.md`).
**Settled and not re-opened:** seal by identity, deepcopy raises, LIVE is the prod display word, the guard keeps one git call and loads only `fixed_run` by path, "this diff adds no suppressions" is checked by count, the S603 ruling (ONE marker on the single helper line), the `bypass` ruling (visible only for an exact boolean literal with nothing after it), stage names demo/pilot/prod only.
**Result:** no Blocker and no fail-open path. All three round 13 Majors are fixed in substance (R13B2 killed, S603 as ruled, `READ_ERRORS` has six sites each with a surprise test). Two merged Majors remain, both false statements: a stale CHANGELOG paragraph and one mutant row whose expected text cannot be in the first failing line. Because batch 15 changes code and tests on a mode-safety path, **round 15 is REQUIRED**.

## Handoff counts
- PROPOSE FIX: 20 items (3 merged Majors, 7 Minors, 10 Nits).
- CONTEST 0. ESCALATE 0. DECLINE 3 (listed at the end). Remaining unaddressed: 0.

## Prioritized findings

### Issue 1, Major, class WORDING-TRUTH (design M1 = codebase M1; design M2; codebase Minor 4)
- `CHANGELOG.md:227` (and line 22 in the file as cut) still says a bare scheme word with a token follows the core redactor exactly and that a token of 11 or fewer characters after a bearer word stays visible "exactly as in the core redactor". False: `Bearer a1b2c3` and `Basic abc-defghijklmnop` are hidden by `_hide_shaped_scheme_token` (`demo_only_guard.py:353-367`). The paragraph also lists name words (key, token, secret, password) but `auth` and `credential` are in `_SECRET_NAME` (:317). `tests/test_changelog_numbers.py:206` pins the phrase "the core redactor `hadavin_sdk.guard.redact`", which sits inside this stale sentence.
- The batch 13/14 paragraph "Stated differences from the core redactor, all on the hiding side" is false: the core (`redact.py:598-614`) hides `bypass=true`; the guard shows it at the end of a line by the lead's ruling. The sentences that the masker "never shows less" are therefore too strong.
- The dropped helper-independent log-name test is not stated in the CHANGELOG.
PROPOSE FIX:
1. Rewrite the whole masker description in ONE place (the batch 13/14 paragraph) and make `:227` and every other mention point at it. Keep the pinned phrase inside the new text.
2. The new text lists both directions in plain words. HIDES MORE than the core: Bearer plus 1-11 mixed letters and digits; Basic plus 1-7 mixed; Basic plus 16 or more characters that include a dash; `authorization=<Bearer|Basic|Digest> <token>` at any length including a quoted value; a bare word `bypass` unless its value is exactly true/false/yes/no/on/off/0/1 (any case) with only white space after; a whole `Authorization:` header line to the end of the line; names holding key, token, secret, password, `auth` or `credential`. SHOWS WHAT THE CORE HIDES: `bypass=true` at the end of a line (lead ruling). NOT COVERED by this masker at all (the core may hide them): the colon form, a quoted JSON `"token": "x"`, `--password x`, `"authorization": "Bearer x"`, JWT, API-key and high-entropy runs, cookies. State: "the guard copies five passes of the core rules; it is a check on copied demo text, not a replacement for the core redactor".
3. A claim test per sentence of the new paragraph: every example named in the paragraph is run through the masker and the stated result asserted (hidden/visible/shown-where-core-hides); a test fails when the old phrases "exactly", "follows the core", "all on the hiding side", "never shows less" reappear in the masker text of `CHANGELOG.md` or the guard comments.
4. State in the CHANGELOG that the helper-independent log-name test was dropped and why, or restore it (builder chooses restore if it takes under 30 minutes).
Fail-before: the claim tests fail on 8c814fe6 (the stale sentence); label from raw lines.

### Issue 2, Major, class MUTANT-EXPECT (design M3 = codebase M2)
`tests/banner_mutants.py:2474-2480` row R13A8 expects "READ_ERRORS holds a type that takes every error", which is the message of the SECOND assert in `test_the_list_of_read_errors_holds_no_type_that_takes_every_error` (`test_mode_banner.py:3795`). Under the mutant (`Exception` added as a sixth member) the FIRST assert (`mb.READ_ERRORS == NAMED_READ_ERRORS`, "READ_ERRORS is not the five named types") fails first, so the runner reports the row BAD and `python tests/banner_mutants.py` (blocking CI step, `ci.yml:104-105`) exits 1. `expectation_nowhere_in_killer` only checks that the string occurs in the killer file, so the static test hides it.
PROPOSE FIX (class: a static check that cannot see which assert fails first):
1. Split the killer into two tests, one per assert, so each row has its own killer with its own message; R13A8 points at the first test and expects "READ_ERRORS is not the five named types"; the second test (no type that takes every error) gets its own row (a mutant adding `BaseException`, or `Exception` at another position, that the equality assert alone would also catch: if both fire, make the second test not depend on the first and say which fires first in the row label).
2. Class check: a static test (`expectation_in_first_assert`) that for every row whose killer is a plain test function the `expect` string occurs in the FIRST `assert` message of that function or in a message that function can produce before any other assert; rows where this cannot be decided statically are listed in `COMPUTED_EXPECT` (existing exemption) and are checked by the runner's first-failing-line comparison.
3. Plant test for the check: a planted killer whose expect belongs to the second assert is refused.
4. The evidence runner confirms by running R13A8 and the 24 `COMPUTED_EXPECT` rows against their first failing line.
Fail-before: the planted test fails on the old check.

### Issue 3, Major (lead evidence), class UNKILLED-ROW: banner mutant B12
The lead's laptop run on dd827d79 found banner mutant B12 "the lists get a default again" with no killing test. Evidence for 8c814fe6 is owed.
PROPOSE FIX: the evidence runner runs B12 on 8c814fe6 (asked at 05:44Z). If it is killed, record the killer name. If it survives or the row no longer exists under that name, the builder writes a killer (the lists must not get a default: a sealed list that is absent stays absent, behaviour first) and shows killed with the first failing line. The builder reports the result by row name either way.

### Issue 4, Minor, class UNPINNED-LIMITS (codebase Minor 1, Minor 2, Minor 6, Minor 7; nits 6, 7)
- The 16-character threshold (`demo_only_guard.py:356 len(body) >= 16`) is unpinned: mutants `>= 17`, `>= 15`, `>= 13` survive; letters-only tokens of 16 or more are hidden by the core anyway, so `"a"*16` tests do not exercise the rule. Unpinned too: `min(end + 1, n)` in `_value_end` (unterminated quote) and the `line[tail:stop] != _HIDDEN` re-hide guard.
- The empty-file-list refusal (`demo_only_guard.py:488-493`) has no test or row; it changes `include_new=False` callers (:1075, :1130): in a repo with only new, never-added files the scan passes and `run_without_folder` dies with the misleading "git listed no files", and the designed "N file(s) are not added to git" message (:1131-1135) is unreachable.
- No mutant rows for the helper's other checks (`fixed_run.py:27` list/tuple and non-empty, :33 NUL and text, :35 `isabs`/`shutil.which`, the allow-list); no test that a tuple is accepted or that a dict, set, generator, bytes element or PathLike is refused; the one-marker count is not pinned.
- The "only through the helper" test misses `from subprocess import run`, `import subprocess as sp`, `Popen`, `check_call`, `os.system`, `os.popen`, `os.exec*`, and files outside the two tools.
- Masker edge: `authorization=Digest username="a", response="b"` hides only the first token.
PROPOSE FIX:
1. Pin the threshold: `Basic abc-defghijklmn` (15 characters with a dash, visible as the core shows it) and a 16-character dashed token (hidden), each with a row that moves the limit by one in both directions; rows for `min(end + 1, n)` and the re-hide guard with killers.
2. Empty file list: tests for an empty repository (refused with the empty-list message) and an only-new-files repository (the "N file(s) are not added to git" message is what the user sees, so reorder or branch so the right message is reachable); a row for each branch.
3. Helper: rows for each check (type, empty, NUL, element type, `isabs`/which, each allow-list refusal); tests for tuple accepted, dict/set/generator/bytes element/PathLike refused; a test that counts markers on added lines of the guard and helper files (exactly one `noqa: S603` on the line that starts the program, none elsewhere).
4. "Only through the helper": an AST test over every `.py` file under `tools/` and `tests/` helpers and `src/` that flags `subprocess.*` attribute calls (any alias via the import table), `from subprocess import ...`, `os.system`, `os.popen`, `os.exec*`, `os.spawn*`, with an exception list that names each allowed file and the reason (`fixed_run.py` only); sibling sweep: grep `subprocess` over the repo and list every other file that starts a program, with a verdict (if `tools/mutation_runner.py` or others start programs directly, they are outside this change: list them as a follow-up item with file and line, not silently allowed).
5. Masker: `Digest` with several name=value parts hides every part up to the end of the line; add the row and test.

### Issue 5, Minor, class LABELS (codebase Minor 3; nit 11)
- `test_mode_banner.py:3765-3766` `test_pin_a_named_read_error_still_reads_unconfirmed_at_every_site` is named pin but its own label says it fails on dd827d79; `:3798-3799` `test_a_bug_in_reading_the_endpoint_of_a_source...` passes on c7eb5c79 but has no pin name; `test_banner_mutant_table.py:296-297` "FAILS ... table has 337 rows" arises only when the new table is copied onto the old tree and goes stale at the next added row; the helper pins (`test_demo_only_guard.py:2623-2625`) say "PASSES there" though old code has no helper (nothing proven); `test_changelog_numbers.py:203` "not run on the old heads"; each fail-before header written twice with identical text.
PROPOSE FIX: relabel from real runs in worktrees at dd827d79 and c7eb5c79 (raw lines): rename to match what the run shows; helper tests say "cannot run on the old tree (no helper there)"; the row-count line says "the count is derived from the table; the old tree has its own count" and carries no number; one fail-before header per file with both heads in a table; run the claim tests on both old heads and label them from the lines. The builder reports builder-claimed numbers separately from runner numbers.

### Issue 6, Minor, class RUNNER-SAFETY (codebase Minor 5; design nit 7)
Under mutant R13A9 (`if refused:` replaced by `if False:`) the case `{"shell": True}` reaches `subprocess.run([exe, "-c", "pass"], shell=True)`, which runs `sh -c <exe> -c pass`, a bare interpreter reading inherited stdin; it can hang the blocking mutation step if stdin is a terminal or an open pipe.
PROPOSE FIX: the killer passes `timeout=` (allowed by the helper) and `input=""` or `stdin`-less settings so no case can block; add a test that the killer completes in under a stated time on the mutated line (the runner checks this with a hard timeout).

### Issue 7, Minor, class TEXT-AND-CHURN (design nits 4, 5, 9, 10; codebase nits 1, 2, 3, 4, 5; M3 follow-ups)
- `tests/fixed_run.py:5` says the subprocess rule is never waived; the rule is waived once (`noqa: S603` at `tools/fixed_run.py:38`).
- `fixed_run` contract is shape-only: `run_fixed(["sh", "-c", tainted], check=True)` passes.
- The marker text `# noqa: S603 argv validated above` has no separator and does not name the contract.
- `app.py:59-72` `_PLAIN_DATA += (date, timedelta, uuid.UUID, enum.Enum)` is churn with no reason; `_load_fixed_run` is duplicated (`demo_only_guard.py:81-97`, `scan_repo.py:18-34`); R14C1 is out of numeric order (`banner_mutants.py:2451`); `focus_problems` repeats the early exit; 72 added lines of 100 columns or more (for example `tools/fixed_run.py:1, :26, :31, :38`); orphan hard-wrap lines (`app.py:311-315`, `mode_banner.py:788-791`, `demo_only_guard.py:282-283` and `371-373`, the `_load_fixed_run` docstrings).
PROPOSE FIX:
1. `tests/fixed_run.py:5` and the helper docstring: "the contract checks the shape of the command, not which program runs; callers must never pass untrusted data as arguments to an interpreter (`sh`, `python`); the one S603 marker is the only waiver".
2. Marker text in the repo's style with a separator, `# noqa: S603 - argv is validated above: list of text, no NUL, only allowed keywords (see test_...)`; the builder runs `ruff check src tests tools` and shows it clean with exactly one marker; if ruff rejects the separator form the builder reports the raw ruff line to the lead (no per-file ignore).
3. `_PLAIN_DATA`: revert the split (restore the single tuple) unless a reason is written in the CHANGELOG and a row pins it; the builder states which.
4. Duplicated `_load_fixed_run`: FIX by a single small loader in `tools/fixed_run.py`? Not possible (both files load it by path before importing it); so keep the two copies, add a test that the two function bodies are textually identical (AST dump), and state the reason in a comment; this is the "shared choke point" at the cost of a test.
5. Number rows in order (R14C1 after R14A3), remove the duplicated early exit in `__main__` by calling `focus_problems` once, rewrap every line added since the branch base that is over 100 columns and every orphan wrap (`git diff origin/main...HEAD` added lines only; the raw fail-before comment lines in tests are exempt only if wrapped into a table).

## Declined (recorded, no change)
- Codebase Minor 5 part about the runner's stdin: not testable from the snapshot; covered by Issue 6 (timeout makes it safe regardless).
- Design nit 8 first half (how ruff parses trailing noqa text): handled by the builder running ruff (Issue 7 item 2); no change without a result.
- Design nit 10 and codebase nit 2 (R14C1 order, duplicated early exit) are included in Issue 7 item 5; no separate action.

## ONE FIX BRIEF (single builder, batch 15; fast-forward only onto `wip/cloud-pd-banner` from 8c814fe6)

Rules: `PYTHONPATH=<worktree>/src` and print `hadavin_sdk.__file__` before any run; cloud limits (no full suite, focused tests and rows only, at most 2 heavy processes, each command under 8 minutes and resumable; mutant rows detached with a log); real fail-before in `git worktree` at dd827d79 and c7eb5c79 with raw lines; no suppressions or per-file ignores beyond the one ruled S603 marker; nothing under `handover/`; fake credentials built from parts; suppression-marker count on added lines against the merge base (`origin/main...HEAD`, three dots); run the FULL test files of everything you touch (on 3.12 and 3.13) and list every test file not run; report builder-claimed numbers apart from runner numbers; remove scratch worktrees and stop your own processes; **NEVER answer y/yes to a start or confirm prompt of any script that can reach a network or send mail; run only loopback settings; a prompt means STOP and report.**

| # | Class | Change | Test | Mutant row |
|---|---|---|---|---|
| A | WORDING-TRUTH | issue 1: one masker paragraph (both directions, not-covered list), `:227` points at it; claim tests; log-name test restored or drop stated | claim test per example | none |
| B | MUTANT-EXPECT | issue 2: split R13A8 killer, first-assert static check, planted test | planted killer refused | R13A8 repointed, new row for the second assert |
| C | UNKILLED-ROW | issue 3: B12 on the head | killer if survived | B12 |
| D | UNPINNED-LIMITS | issue 4 | threshold, empty list, helper rows, AST subprocess test, Digest | rows per item |
| E | LABELS | issue 5 | relabel from raw runs | none |
| F | RUNNER-SAFETY | issue 6 | timeout in R13A9 killer | R13A9 |
| G | TEXT-AND-CHURN | issue 7 | marker-count test, identical-bodies test | none |

Builder reports ONCE when ALL of A-G are done: new head sha, row count (derived), rows run by name with killed/survived and first failing line, raw fail-before lines, ruff raw output, marker count, test files not run, anything not done and why.

## Round 15 and evidence
- **Round 15 is REQUIRED.** Fresh `egm:egm-design` and `egm:egm-codebase-details` reviewers on a merge-base snapshot plus one evidence runner on the final head.
- Cloud evidence (runner, records only): focused tests on 3.12 and 3.13; changed and new rows, B12, R13A8, R13A9, the 24 `COMPUTED_EXPECT` rows against their first failing lines, a 60-row sample; fail-before; marker grep; masker probe table against `hadavin_sdk.guard.redact`; surprise exception at each of the six sites.
- **RUN ON LAPTOP (Linux Docker, final head only, after a fresh round finds 0 Blocker and 0 Major):** hadavin-sdk `<final sha>` full pytest, complete `banner_mutants` (337+ rows) and `stage_mutants`, py313 and py312, CI flags, ruff, format, bandit, scan_repo.
- Ledger rows PDBANNER-r14-1..3 are added by the caller.
