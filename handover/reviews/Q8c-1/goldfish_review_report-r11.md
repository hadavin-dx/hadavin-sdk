Status: resolved

# Goldfish Annotated Review Report

**Target:** Q8c-1 batch 11, head e4f1b2a4 (code head 351f2b8b, branch wip/cloud-q8c1-b11): policy page, dated lists, builder-notes check. Security path, no round cap. Round 11.
**Inputs read:** `handover/reviews/Q8c-1/q8c1b11-design-r11.md`, `q8c1b11-codebase-r11.md`, previous report `goldfish_review_report-r10.md`, independent evidence `handover/evidence/Q8c-1/e4f1b2a4/RESULTS.md` (with `probe-policy-page-states.txt`, `probe-day-arguments.txt`, `new-tests-passing-on-old-code.txt`).
**Mode:** automated, no person available; the recommended option is taken for every item. No severity was changed. Duplicates across the two reviews are merged by root cause.

## Evidence in one paragraph
Full pytest 10928 passed, 13 skipped (12 Vault engine tests IMPOSSIBLE-NOW, 1 other skip); stage_mutants 37 of 37; policy_mutants 180 of 180, weak 0, at the real clock, at 2026-12-11 and at 2026-12-12 (the "RED BASELINE" line prints as it must); `src/` untouched against the previous head; ruff, format, bandit, scan_repo, gitleaks exit 0. Fail-before: 20 failed (new runner copied in) or 23 failed (old runner kept) on the old head; of the 45 notes rows, 23 fail on old code and 22 pass on it (list in `new-tests-passing-on-old-code.txt`). Probes: with both dated lists emptied on a copy of the real head, `--check`, `--write`, `--check` all exit 1 with 13 lines (6 names plus 7 claims in the kind modules still lack entries; names only 6 lines, claims only 7 lines); the "no review date applies now" wording appears only when `data_problems` is stubbed. Partial renewal probes exit 0 and the page still names 2026-12-11. `notes_lines_check.py --auto origin/main` exits 1 with 113 "no row" lines; `--auto d8441218` (the push base) exits 0; a weakened helper in `tests/test_policy_docs.py` lists 4 tests (same-file follow works). Not run: Vault tests (IMPOSSIBLE-NOW, CI run with `HADAVIN_REQUIRE_VAULT_ENGINE=1` needed before 2026-12-11), pip-audit, Semgrep, zizmor, Python 3.12, the new CI step on GitHub (it has never run; needs a real pull request run, outside this session), the timing flake test.

## Escalated
None. The "renew all or none" rule for partial renewals (Issue 8) is taken with the safe default; if the owner wants partial renewals allowed, that is a later choice, not a blocker.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` D11-1 + `codebase` M2] - Severity: Major
*   **Affected Scope:** `tests/test_policy_guard.py:4725-4828` (`_cleared`, `_end_state`), `:4081, :4101, :4123, :4374, :4409`, `:233, :201`; `tools/policy_page.py:1255-1259, 1280-1291, 1344-1347, 1585-1587, 1611-1613, 398`.
*   **Discrepancy Description:** `_end_state` gives cleared policies only to the two dated-list rules. In a really cleared tree: `read_marks` refuses an empty `# CLAIM-READ-BY-*:` line (`"".split` gives `[""]`); `claim_mark_problems` refuses every listed text that matches no claim; `# BUILDER-ONLY:` and `# PARTLY-BUILDER-ONLY:` lines reject an empty list; `note_problems` refuses a claim-class note with no claim and a pending-class note whose entry has `verified`; `copy_ready` flips and the page text changes. So a real `--check` or `--write` cannot exit 0 in the end state. Five tests fail by design instead of branching on None, and the empty-kinds case fails two more. NOTES understates the gap and answers r10 Issue 1 ("state exactly which end state is covered") with a different, unstated one.
*   **Rationale:** Evidence confirms it on a copy of the real head (13 lines, exit 1); the page wording appears only under a stub. This is exactly the end state the package exists to handle.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid, confirmed by independent evidence. The fix is in the real rules, not in the test.
*   ***Proposed Edit:***
    *   Location: `tools/policy_page.py` (`read_marks`, `claim_mark_problems`, the BUILDER-ONLY lines, `note_problems`), `tests/test_policy_guard.py`, builder notes.
    *   Change: first write the end-state test with a tmp sources file whose head is legal for zero claims and the real `read_marks` and `claim_mark_problems`, and show it failing on e4f1b2a4; then accept an explicit empty marker (for example `none`) on each of those lines and refuse stale texts only when the line is not the marker; make `note_problems` and `copy_ready` follow; a mutant for each new branch; make the five tests (and the two empty-kinds tests) branch on None like `_date_test_problems`; the renewal "what to do" text lists everything a renewal or an emptying must touch; reword the notes to say exactly what was and was not faked.

### [Issue 2] [`design` D11-2, D11-3, D11-9 + `codebase` M3] - Severity: Major
*   **Affected Scope:** `.github/workflows/ci.yml:69, 100-110`; `tools/notes_lines_check.py:227-235`.
*   **Discrepancy Description:** `github.event.before` exists only on `synchronize`; on `opened`, `reopened`, `ready_for_review` the base is main, so the first CI run (draft pull requests run no CI) is red by construction: `--auto origin/main` exits 1 with 113 lines. On a pull request the checkout is the synthetic merge commit, so `before..HEAD` includes what main changed; after a force-push `before` may not be fetchable. The fetch runs with `persist-credentials: false`, so it fails on a private repository, which `ci.yml:5-6` says the tools survive. `auto_files` ignores the return code of `git diff`: on error stdout is empty and the tool prints "no test file changed ... nothing to check" and exits 0 (a vacuous pass). `git diff --name-only` honours `diff.renames`, so a renamed file hides the old file's tests. A later push with no test-file change checks nothing on the same head. The step is only text-checked.
*   **Rationale:** The gate is red on its first real run or gets switched off; it also has a fail-open path.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid; the 113-line number and the exit 1 come from the evidence runner.
*   ***Proposed Edit:***
    *   Location: `ci.yml` step, `notes_lines_check.py` `auto_files`, `_notes_step_problem`.
    *   Change: diff `merge-base(main, head)..head` where head is `github.event.pull_request.head.sha`, read blobs with `git show head:path` (never the working tree); `fetch-depth: 0` (as the `security` job has) or an authenticated fetch; check the diff's return code and fail loudly; `--no-renames`; write the missing rows once (up to 113) so the first run is green, or restrict the first run to the push delta with the reason written in the notes (the first option is preferred); extend `_notes_step_problem` to require the authenticated fetch and the head sha, and plant-test the workflow on a made-up merge commit. What the evidence could not show (a run on GitHub) is listed as impossible now: it needs a pull request run, next step is the first CI run after the PR is opened by the lead.

### [Issue 3] [`design` D11-4, D11-8 + `codebase` m7] - Severity: Major
*   **Affected Scope:** `tools/notes_lines_check.py:45-53, 61-68, 91-97, 133-138, 223-224`.
*   **Discrepancy Description:** The check does not see the weakening vectors this package itself uses: imports from `tests.*` are not followed (`stray_days`, `kinds_sentence`, `changelog_entry` now live in `test_policy_guard.py` and are imported by the changelog and docs tests); `tests/policy_mutants.py`, `conftest.py`, `stage_mutants.py` and `tests/fixtures/policy_sources_*.txt` are outside `_TEST_FILE` (deleting a mutant or editing an `expect` needs no row); autouse fixtures are never named by a test; module-level imports and `+=` are not tracked; reason markers are substrings with no word boundary ("plant" matches "implant", "control" matches "controller", "passes on" alone passes, and is not among the four reasons the docstring names); rows are not tied to a push.
*   **Rationale:** The mutant list is the proof that tests can fail and this batch edited it. Preamble rule 5 does not allow deferring a "known gap" that is cheap to close.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid; evidence shows the same-file follow works and the cross-file one is the gap.
*   ***Proposed Edit:***
    *   Location: `tools/notes_lines_check.py`, its tests and plants.
    *   Change: follow `from tests... import name` to that file's base text; add `tests/policy_mutants.py`, `conftest.py`, `stage_mutants.py` and the fixture folder to the changed-file scope with a count check for mutants removed or altered; treat `autouse` fixtures as used by every test; track module-level imports and `+=`; word-boundary markers, drop "passes on", and require an identifier (a mutant name or a log file) after "plant" and "fails on"; tie each row to the push's changed test; plants for each vector, each shown failing before the fix.

### [Issue 4] [`codebase` M1 + `design` D11-6] - Severity: Major
*   **Affected Scope:** `handover/evidence/Q8c-1/b11/NOTES.md:72, 70, 71, 76-78`; `tests/test_policy_changelog.py:20-26` (old body DELTA.patch:3252-3268); three tests in NOTES section C (`test_every_unchecked_claim_has_a_dated_entry...`, `test_plant_an_overdue_pending_kind_is_caught`, `test_the_check_command_reports_a_name_or_claim_with_no_dated_entry...`).
*   **Discrepancy Description:** Row 72 calls `test_the_changelog_gives_the_days_the_kinds_list_starts_to_fail` "control: only the imports changed". The delta shows the independent pins were removed: `(7, 9)`, the review days 2026-12-11 and 2027-01-31, and the literal sentence. It now asserts `PENDING_KINDS` is non-empty and `kinds_sentence() in changelog_entry()`, built from the same list, so all 16 kinds' review days can move within the 92-day cap with the changelog edited to match and the suite stays green. The row passes because `reason_problem` accepts any reason containing "control". Separately, three tests have only an `AttributeError: no attribute 'review_day'` (a missing helper) as fail-before evidence and no killing mutant. Evidence: 22 of the 45 rows pass on old code, so each row's reason must be true, not merely present.
*   **Rationale:** A weakened test described as unchanged is the failure mode the notes check was built to catch.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid; read from the delta by the codebase reviewer and consistent with the evidence list.
*   ***Proposed Edit:***
    *   Location: `tests/test_policy_changelog.py`, `NOTES.md` section C, `tests/policy_mutants.py`.
    *   Change: restore an independent pin (the group count, or a day read from a fixture the list does not feed); rewrite row 72 to say the pins were replaced by a list-derived check and what pin was restored; re-read rows 70, 71, 76-78 and each of the 22 pass-on-old rows against the diff and give each a true one-line reason (control, plant, or a killing mutant); give each of the three AttributeError-only tests a killing mutant or a plant, or state "control" with the reason.

### [Issue 5] [`design` D11-5 + `codebase` m5] - Severity: Minor
*   **Affected Scope:** `tests/test_policy_guard.py:4532, 4664, 4930, 4935, 4948-4949, 1663-1666`; NOTES.md:15 ("No test writes a day").
*   **Discrepancy Description:** Runner tests use the literal `--day 2026-12-12`; `runner.parse_args` refuses a day before the live `pp.DECIDED`. A first renewal on 2026-12-13 or later moves `DECIDED` past 12-12 and three tests fail with a message unrelated to the renewal; the made-up entry at 1663-1666 starts reporting "decided in the future". The notes claim is untrue.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid.
*   ***Proposed Edit:***
    *   Location: the listed lines and NOTES.md:15.
    *   Change: build the days from `DECIDED + timedelta(...)`; correct the notes sentence.

### [Issue 6] [`design` D11-13 + `codebase` m6] - Severity: Minor
*   **Affected Scope:** `tests/policy_mutants.py:1658, 1667-1673`.
*   **Discrepancy Description:** `canary_day` is the earliest review day minus one, but `parse_args` floors at `pp.DECIDED` and the kinds list has its own `KINDS_DECIDED`. If kinds are renewed on the day the names and claims lists fall due, the canary day precedes a list's `decided` day and the "green" day reads "decided in the future".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid.
*   ***Proposed Edit:***
    *   Location: `tests/policy_mutants.py`.
    *   Change: clamp both the canary day and the `--day` floor to the latest `decided` over the three lists; add a case with a renewal of the kinds only.

### [Issue 7] [`design` D11-7] - Severity: Minor
*   **Affected Scope:** `tests/test_policy_guard.py:1558-1562, 4430-4431, 4467-4471`.
*   **Discrepancy Description:** The `None` branches run on no run today; a typo in one first fails in the end state.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid; becomes cheap once Issue 1 makes the end state reachable.
*   ***Proposed Edit:***
    *   Location: those three bodies.
    *   Change: run each body once with the lists monkeypatched empty and a written page, as a plant.

### [Issue 8] [`design` D11-11] - Severity: Minor
*   **Affected Scope:** `tests/test_policy_guard.py:4403-4411`; tool docstring.
*   **Discrepancy Description:** The batch tests partial renewal with made-up lists, but the repository's own pin requires every dated entry to have `decided == pp.DECIDED`, so a real renewal of only `_ROLE_NAMES` fails it. Evidence: partial renewal probes exit 0 and the page still names 2026-12-11.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Safe default "renew all or none", stated in the tool docstring and the overdue message, with the pin kept and its failure text saying why. If the owner later wants partial renewals, that is a separate decision (not a blocker).
*   ***Proposed Edit:***
    *   Location: tool docstring, overdue message (`policy_page.py:825-827`), pin test message.
    *   Change: write "renew all or none" in plain words in the three places; make the pin's message name the entry that was not renewed.

### [Issue 9] [`design` D11-10 + `codebase` m4] - Severity: Minor
*   **Affected Scope:** `tests/test_policy_guard.py:4709-4722` (tests 4019-4039; `test_policy_changelog.py:46-55`).
*   **Discrepancy Description:** `DAY_FORMS` misses "12 December" (no year), "the 12th of December", "12 Dec", "Dec. 12", "12-Dec-2026", "12/12/2026", "12.12.2026", "2026.12.12"; months are case-sensitive ("december 12", "DEC 12"); form 4 false-matches "Decision 12", "Mark 12", "Marker 5", "Mayor 3". The claim is "every written form".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid.
*   ***Proposed Edit:***
    *   Location: `DAY_FORMS` and `test_a_day_in_any_written_form_is_found_outside_the_one_allowed_sentence`.
    *   Change: add the missing forms, make the match case-insensitive with `\b` anchors, add each case as a found day and the false-positive words as not-found, with a mutant for each new form.

### [Issue 10] [`codebase` m9 + `design` D11-12 + nits] - Severity: Minor and Nit (merged)
*   **Affected Scope:** `tests/test_policy_guard.py:4958-4961`, `4864-4871`; `policy_page.py:825-827`; `b11/weak-expect-after.txt:1`; brief item "removed equivalent mutant".
*   **Discrepancy Description:** (a) The "takes --day twice", "takes a day before the decision day" and `--day=VALUE` mutants share one message, so "first failing line names the mutant" is only partly true. (b) `weak-expect-after.txt` cites `b11/logs/mut-real.log`, which is not in the snapshot; the "0 of 180" figure is in `g-pm-real.log` and `mut-b11-3.log`. (c) The brief names a "removed equivalent mutant"; none is found in DELTA.patch or NOTES (141 + 39 = 180 is consistent with none removed). (d) The overdue message does not say what a renewal must also change (pin test, `KINDS_DECIDED`, CHANGELOG sentence, regenerated page, notes rows). (e) `changelog_entry` runs to end of file when the entry is the last bullet and ends only at a bold top-level bullet.
*   ***AI Suggestion:*** PROPOSE FIX (all)
*   ***Justification:*** Each is small and true; fixed in the same push.
*   ***Proposed Edit:***
    *   Location: as listed.
    *   Change: one assert and one message per `--day` case; cite `g-pm-real.log`; state in the notes which batch removed the equivalent mutant, or correct the claim; extend the overdue message with the full renewal list (shared with Issue 1); end `changelog_entry` at the next bullet of any kind or at a heading, with a test for the last-bullet case.

## Handoff
- Accepted fixes (PROPOSE FIX): 10 issues (Issues 1-10): the 4 Major groups, plus Minors and Nits.
- Contested: 0.
- Escalated: 0. The one policy choice (Issue 8) takes the safe default "renew all or none".
- Declined: 0.
- Remaining unaddressed in this report: 0. The code is not yet changed. Impossible now, with next step: the CI notes step has never run on GitHub (needs a pull request run; the lead opens it) and the 12 Vault engine tests (a CI run with `HADAVIN_REQUIRE_VAULT_ENGINE=1` before 2026-12-11).

## Who fixes it
One batch-12 builder (Sonnet 5.5) on a new branch from e4f1b2a4, pushing to `wip/cloud-q8c1-b12`. Files: `tools/policy_page.py`, `tools/notes_lines_check.py`, `.github/workflows/ci.yml`, `tests/test_policy_guard.py`, `tests/test_policy_changelog.py`, `tests/test_policy_docs.py`, `tests/policy_mutants.py`, CHANGELOG, builder notes. Order: Issue 1 first (the rules decide what the end-state test can check), then 2, 3, 4, 9, 5, 6, 7, 8, 10. Each new test is shown failing on e4f1b2a4; each new branch gets a mutant; the notes check is run on the builder's own notes with the `--auto` form against both the push base and origin/main. Independent evidence runner and two `egm:*` reviewers follow the next head.
