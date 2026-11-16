Status: resolved

# Goldfish Annotated Review Report (round 14)

**Target:** Q8b batch 13, branch `wip/cloud-q8b-b13`, head `120f3f78` (code `245a9b3c`; previous reviewed head `a148bda6`), round 14. REDACTION path: no round cap.
**Inputs:** `q8bb13-design-r14.md` (0 Blocker, 2 Major D1-D2, 2 Minor D3-D4, 2 Nit D5-D6), `q8bb13-codebase-r14.md` (0 Blocker, 2 Major C1-C2, 5 Nit N1-N5), previous report `goldfish_review_report-r13.md`, evidence `handover/evidence/Q8b/120f3f78/RESULTS.md` (PARTIAL, see below).
**Mode:** automated; no person available; the recommended option is taken for every item. No reviewer severity is changed. Nothing is contested: where the two reviewers disagree, the run settles it (Group 1).

## Evidence summary (PARTIAL: what was run and what was not)
- **NOT RUN on this head:** full pytest, `q8b_mutants` (root and nobody), `stage_mutants`, `mutation_runner_mutants` re-runs (the builder ran two of them before its last change to `redact.py`), fail-before on `a148bda6`, cost and timing, the timing test. The independent evidence runner could not get a heavy slot (about 18 jobs queued for 3 slots at 15:58 UTC, mostly builder jobs) and handed back. Python 3.12, semgrep, zizmor, trivy, pip-audit, PostgreSQL 17: impossible now.
- **Ran (exit 0):** ruff check, ruff format --check (338 files), scan_repo, bandit -ll, gitleaks over origin/main..HEAD.
- **Runner probe** (made-up values; head, main `2a8c2aac`, `a148bda6`): head readable and main masked: overlap joins 0 of 1242, capital hyphen words 0 of 264, JSON siblings and breaks 0 of 214, prefixed ordinary words 240 of 1755 (the 15 bare words plus prefixes `-`, `en`, `re`), bare words 75 of 90 (owner item). Main readable and head masked: 160 joins, 45 prefixed, 190 JSON and break cells.
- **Lead probe** (`evidence/Q8b/120f3f78/lead-probe-d1.py`, head source against main source): `x--bypass`, `x--compass`, `x--overpass`, `x--possession` and `-bypass` are READABLE on head and MASKED on main in the key=value and the quoted-JSON form; `x-bypass` and `new_bypass` are masked on both; the flag form `--key value` is readable on both sides.

## Prioritized Findings & AI Suggestions

### Group 1 [design D1] - Severity: Major (reviewers disagree on the facts; the run settles it)
*   **Affected Scope:** `src/hadavin_sdk/guard/redact.py:239` (`(?<!(?<![\w.])(?<![\w.]-)by)`), `_bare_word` :252, `QUOTED_KEY_WORDS` :327; `tests/test_q8b_batch13.py:234` (`PREFIXES`); CHANGELOG item 5.
*   **Discrepancy Description:** The group 5 exemption leaves `x--bypass=<value>` readable although main masks it. For `x--bypass` the two characters before the word are `--`: the first is `-`, not `[\w.]`, so the inner look-behinds hold, the word counts as a bare start and the outer look-behind blocks the `pass` alternative. Main's unquoted rule `(?<![\w.\-])[\w.\-]{0,40}(...)` swallowed the whole key. Same for `x--compass`, `x--overpass`, `x--possession` and the other words, in the unquoted and quoted rules. The 8 tested prefixes never put `-` directly after `-`; M249 restores only the old class.
*   **Rationale:** This is the class group 5 claimed to close ("a word in front of it is a credential key again, as on main"): a secret readable on head that main masked. The codebase reviewer read `x--bypass` as readable on both sides; the lead's run shows main masking it, so the design reading is correct and the codebase reading is wrong by run. Both findings are recorded as reported.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Redaction path, a readable credential. The exemption holds only when the ordinary word is the whole key: nothing before it except the start, a character that cannot be in a key, or at most two leading hyphens that themselves follow a non-key character (for example `(?<![\w.\-])` forms). Add the prefixes `x--`, `x-.-`, `a--b-`, `.-`, `-x-`, `en`, `re`, `-` to `PREFIXES`, built as a generator over every non-key/key character pair so no shape is picked by hand; a mutant for the new shape killed for that reason. A form that must stay shown goes to the owner with the cell list (the 15 bare words already do). Check the flag rule and the record walk for the same shape.
*   ***Proposed Edit:***
    *   Location: `src/hadavin_sdk/guard/redact.py`, `tests/test_q8b_batch13.py`, `tests/q8b_mutants.py`, CHANGELOG item 5.
    *   Change: as above; show the new test failing on `120f3f78` with measured counts.

### Group 2 [design D2 and codebase C1] - Severity: Major
*   **Affected Scope:** `tests/test_q8b_batch13.py:383-395`, `:395` (`WALL_CLOCK_UNPLANTED_MAX = 9`), `:406`; `tests/test_q8b_batch8_lines.py:176-192`; `tests/q8b_mutants.py` (M241, M256, M257); NOTES.md; CHANGELOG item 4.
*   **Discrepancy Description:** 9 wall-clock tests still have no planted fault (`test_b10_2` `_DIGEST_FOLDS`, `test_b9_1`, `test_b9_4`, `test_b8_5`, `test_b8_8`, `test_b8_10`, `test_b9_5`, `test_b7_6`, `test_r1`). The reason given is the time box, which is not an allowed exception (impossible now, owner, third party). Third round with this item open. The gate counts only bodies with `perf_counter` or `time.time()` (a helper, `time.monotonic`, `process_time`, `timeit` is invisible: 9 is a floor). `test_b13_3` has one plant (M248) for the single quadratic unit; the other 8 glued shapes are controls, so a quadratic regression in `secret:"x"`, `token="x"`, `X-Api-Key:Basic x` or `token:Basic\n x` is not killed. `planted_killers()` reads only single-quoted rows (45 rows are written `mutant("...`) and a lazy match can credit a later row.
*   **Rationale:** A quadratic regression of these rules passes the suite: a denial of service on the redaction path. The technique already exists in the table.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Plant a possessive-to-greedy or look-ahead fault for each rule and each glued unit with a named killer, drop the constant to 0 and delete it; detect clocks by the `time` import; or replace wall-clock timing by a work count (regex tries) so no machine speed is involved. Make `planted_killers()` parse the mutant table with `ast`, not a regex (also closes N5).
*   ***Proposed Edit:***
    *   Location: tests named, `tests/q8b_mutants.py`.
    *   Change: as above; one "unplanted" count only.

### Group 3 [codebase C2] - Severity: Major
*   **Affected Scope:** CHANGELOG item 7 ("tested on all five paths for each break"); `tests/test_q8b_batch13.py:321-327`, `:357-369`; `src/hadavin_sdk/approvals/channel.py:57-59` (`_LINE_BREAK_CONTROLS`); `tests/test_q8b_batch12.py:184-185`.
*   **Discrepancy Description:** The card path for U+001C, U+001D, U+001E is untested. `RARE` holds 5 breaks; the three separators are checked only through `redact_module.redact`. M254 is killed only through `[form feed]`; M253 changes `_OTHER_BREAKS`, not the card regex; a mutant that drops the three from `_LINE_BREAK_CONTROLS` is not killed. On a card `Authorization: Bearer <a>\x1c <b>` would turn into one flat line and `<b>` stay readable. The CHANGELOG sentence is false for 3 of 8 characters; the b12 comment ("the card path turns a rare break into a space") is stale.
*   **Rationale:** A claim stronger than the proof on the card path.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Run every break that `str.splitlines` knows (derived by brute force, as `test_b13_8` does) through all five paths; a mutant dropping the three separators from the card regex; correct the stale comment; CHANGELOG states exactly what each path does.
*   ***Proposed Edit:***
    *   Location: `tests/test_q8b_batch13.py`, `tests/q8b_mutants.py`, `tests/test_q8b_batch12.py`, CHANGELOG.
    *   Change: as above.

### Group 4 [design D3, D4; codebase builder-admission note] - Severity: Minor
*   **Affected Scope:** `tests/test_q8b_batch13.py:215-229`; `builder-evidence/cost-b13.txt`; `tests/q8b_mutants.py` M256, M257; `tests/test_q8b_batch11.py:185` (`big < small * 12`); `tests/test_q8b_batch10.py:141` (absolute 20 s).
*   **Discrepancy Description:** The glued-header test compares 20k with 80k at a bound of 9 for 4x size, so an exponent up to about 1.58 passes. M256 and M257 add a look-ahead the text never satisfies, so the rule stops matching and the kill rests on time alone with a thin margin (12x against 16x for pure quadratic; M257 on an absolute 20 s budget). The codebase reviewer notes the raw cost file shows main growing the same (about 12x from 30k to 262k) and head over main flat (1.9), so "not proven linear" is more cautious than the evidence; the CHANGELOG figures match the raw file.
*   **Rationale:** Weak detectors, not a head defect.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Use a work-count assertion (Group 2) so the tests do not depend on the host; plants that keep the output the same and change only the possessive/greedy form; record per-run load in the cost file; state the head-over-main ratio as the claim.
*   ***Proposed Edit:***
    *   Location: files named, CHANGELOG cost wording.
    *   Change: as above.

### Group 5 [design D5, D6; codebase N1, N2, N3, N4, N5] - Severity: Nit
*   **Affected Scope:** `k1b/redaction.py` LIMITS, `approvals/channel.py:57-61`, `tests/test_q8b_batch13.py:269-275`, `tests/test_q8b_batch7.py:390-399`, `:450-454`, `src/hadavin_sdk/guard/redact.py:77` and `:1006` (`_FIRST_WORD`), `tests/test_q8b_batch8_lines.py:176-192`.
*   **Discrepancy Description:** (N1/D5) LIMITS says a rare break on a card is written as a line feed; the regex needs a space or tab after it, else it stays a space. (N2/D6) The "pinned for all 15 words in all forms" claim is not kept for the flag form (`forms["flag-space"]` is built then skipped; batch 7 covers 6 of the 15 words). (N3) Card text and record walk disagree for `x-bypass`, `new_bypass`, `x_compass` (equal to main on both sides; LIMITS says one table serves all readers). (N4) `Authorization: x-authorization:v` followed by an indented line leaves the folded line readable, because `_FIRST_WORD` stops at `authorization:` inside a word; the b12 head read it with `\S++`; main had no fold rule. (N5) `planted_killers()` partial read and two "unplanted" counts (Group 2).
*   **Rationale:** Wording and small guard gaps; N4 is a real readable shape on a crafted first word.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Fix where the builder is already in the files, no new review round for these alone: LIMITS adds the condition and the N3 sentence; test the flag form for all 15 words; for N4 stop `_FIRST_WORD` only when `authorization:` starts a header (after white space, a quote or start of text) or allow zero first-word characters and continue, with a test and a mutant.
*   ***Proposed Edit:***
    *   Location: files named.
    *   Change: as above.

### Group 6 [evidence] - Severity: Major (gate)
*   **Affected Scope:** `handover/evidence/Q8b/120f3f78/RESULTS.md`, the builder's gate files.
*   **Discrepancy Description:** No independent full evidence exists for this head (see the summary above). The builder's `stage_mutants` 37/37 and `mutation_runner_mutants` 64/64 ran on `5728925c`, before a later change to `redact.py`; its full pytest passed on the final head, but its first full run had 3 failures (dblink environment, two timing tests that failed under load).
*   **Rationale:** A redaction-path change must not close on builder-only evidence; the evidence runner failed for lack of a slot, which is the lead's scheduling, not a finding against the builder.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The batch-14 builder runs the final-head gates (full suite, `q8b_mutants` as root and nobody, `stage_mutants`, `mutation_runner_mutants`) once on the last commit; the lead then runs a FULL independent evidence run on the batch-14 head before any review and counts a review without it as incomplete. The lead keeps the heavy queue short enough for the runner to start.
*   ***Proposed Edit:***
    *   Location: builder notes and lead process.
    *   Change: as above.

### Group 7 [owner item `q-q8b-bare-bypass`] - Severity: Major (carried)
*   **Affected Scope:** the 15 bare ordinary words (`bypass`, `compass` and the other 13) in all forms; the runner probe counts 75 readable cells (90 in all forms and words).
*   **Discrepancy Description:** Shown on purpose; whether to mask them is the owner's decision. The pin covers the key=value, colon, JSON, quoted and upper-case forms; the flag form is covered for fewer words (Group 5).
*   **Rationale:** Needs the owner; outside every file a reviewer could read.
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** Do not fix, do not report as closed.
*   ***Proposed Edit:***
    *   Location: none.
    *   Change: none. The question stays in `questions-for-lead.md`.

## Handoff

*   Accepted fixes (PROPOSE FIX): 6 groups (Groups 1 to 6): 3 Major findings (D1, D2/C1, C2), the evidence gate, 2 Minor (D3, D4) and the Nits (D5, D6, N1 to N5).
*   Contested: 0. Escalated: 1 (Group 7, OWNER-ONLY). Declined: 0.
*   Remaining unaddressed: all of the above until batch 14 lands. Severity counts kept as reported: design 0 Blocker 2 Major 2 Minor 2 Nit; codebase 0 Blocker 2 Major 5 Nit. The two reviewers disagree on D1 and the lead's run settles it for the design reading.
*   Gate state at `120f3f78`: not mergeable; one readable-secret regression against main (D1); evidence incomplete.

## Who fixes it

One batch-14 builder (Sonnet 5.5) on a new branch `core/q8b-b14` from `120f3f78`, pushing to `wip/cloud-q8b-b14`. Order: Group 1, Group 2 (all 9 plants, or a work-count test), Group 3, then Groups 4 and 5, Group 6 last. Method per bug: name the class, cite the standard it breaks, fix at the shared choke point, grep siblings, show each new test failing on `120f3f78` (measured counts), one mutant per fix killed for the named reason, a written reason for every test that passes on old code, CHANGELOG counts recomputed at the final head. Final head: full suite, `q8b_mutants` as root and nobody, `stage_mutants`, `mutation_runner_mutants` once. Then the lead runs a full independent evidence run and two reviewers (round 15; no round cap on this path). The owner item stays OWNER-ONLY; the timing test `test_the_timing_harness_flags_a_quadratic_stand_in` is not touched.
