Status: resolved

# Goldfish Annotated Review Report

**Target:** Q8b batch 12, branch `wip/cloud-q8b-b12`, head `a148bda6` (code `6b5e7e69`), round 13 (REDACTION path: no round cap).
**Inputs:** `q8bb12-design-r13.md` (2 Blocker F1-F2, 0 Major, 2 Minor F3-F5 in the file, Nits F6-F8), `q8bb12-codebase-r13.md` (1 Blocker C1, 5 Major C2-C6, 3 Minor C7-C9, Nit C10), previous report `goldfish_review_report-r12.md`, independent evidence `handover/evidence/Q8b/a148bda6/RESULTS.md`. Automated mode, recommended option for every item, no severity changed, nothing contested. The reviewers read only; both said F1, F2/C1, C6 need a run. The evidence runner did not probe those shapes, so they are still confirmed by reading only: the builder must reproduce each on `a148bda6` and on main first.

## Evidence summary (recorded by the runner, not judged)
- **Green:** full pytest 11147 passed, 1 skipped, exit 0; `q8b_mutants` 241 of 241 as root and as nobody (M195 absent, M234-M246 present); `stage_mutants` 37 of 37; `mutation_runner_mutants` 64 of 64; ruff, format, bandit, scan_repo, gitleaks exit 0.
- **Not green:** CI perf step 1 failed, 28 passed. The one failure is the known timing test (do not touch it); it also fails on main 3 of 3.
- Fail-before on `2153ad85`: 31 failed, 317 passed. The 15 batch-12 tests that pass on old code are the same 15 ids the builder listed.
- **Readable on head and masked on main:** 16 cells in `probe` and 75 cells in `probe12`, all of them the 15 bare ordinary words (owner question `q-q8b-bare-bypass`); 0 in `probe_extra`, `pair12`, `fold12` and the other groups.
- Folded headers and shapes A and C: `fold12` head 3945 of 9240 readable (shape B 1755 of 6930, shape C 2190 of 2310; main 9240); `shapeA` 312 of 336; `fuzz3` shape B 294 of 1017 on head against 791 on `2153ad85`. Same classes as r12, not new regressions against main; their exact reach must stay in LIMITS.
- Cost `clean()` head against main 1.07 to 1.38 (0.91 s against 0.66 s at 262,144 hostile); builder's figures 1.04 to 1.57 differ and "median of three" is not backed by the builder's file. The glued-run shape of C2 was not measured by the runner.
- Unplanted wall-clock controls: the builder says 4 (CHANGELOG says 3); the runner counts 3 without a killer in the lines table plus 4 wall-clock tests named nowhere in `q8b_mutants.py`, 7 in all; the reviewers name at least 8.
- Not run: Python 3.12, semgrep, zizmor, trivy, pip-audit (IMPOSSIBLE-NOW); gates ran on PostgreSQL 16.15 (CI pin 17.10).

## Prioritized Findings & AI Suggestions (all PROPOSE FIX unless marked)

### [Group 1] [design F1; codebase C6] - Blocker (a literal prefilter hides a match that main masked)
Scope: `src/hadavin_sdk/guard/redact.py` `_sub_at_literals`, `_GATE_FINDERS[words].finditer(low)` (~1479-1517), `KEY_GATE_WORDS`; tests `test_b12_3_*` (`tests/test_q8b_batch12.py:296-389`).
Gap (class: a shortcut that tries fewer start positions than a full scan, so a match that starts inside the previous gate word is never tried): `accessession=<value>`, `xpassession=<value>`, `passecret=`, `passas_token=` and similar joins. `finditer` gives non-overlapping hits, so the second word is skipped; main's full scan masks it, head shows it. The comment and CHANGELOG item 3 call the pieces "a superset of what a match needs", which is false when two pieces share a character. The differential corpus joins whole words only, so it cannot see it.
Fix: zero-width look-ahead finder, or `search(low, i)` stepping one character after each hit, at the one place all gated rules route; add overlap joins to the corpus (every suffix of one gate word that is a prefix of another: `pass`+`session`, `access`+`sessid`, `access`+`secret`, `pass`+`sas_token`, `client`+`token`, `secret`+`token`) with a seeded generator, a test that fails on `a148bda6`, and a mutant that plants the non-overlapping finding with a killer that fails for that reason. Grep every other `finditer` that feeds a substitution. Re-run `redact()` on head and main over the joins and report 0 readable on head and masked on main.

### [Group 2] [design F2; codebase C1] - Blocker (wide scheme-word class leaves a capital-first hyphenated token readable)
Scope: `redact.py:61` `_ANY_SCHEME_WORD`, used at ~935 (single-line Authorization rule) and in the new fold rule (~979); test `test_b12_4_a_lower_case_hyphen_token_is_not_read_as_a_scheme_word` (`tests/test_q8b_batch12.py:212`), mutant M240.
Gap (class: a wider reading than the one it replaced): `Authorization: Ab12-Cd34-Ef56 retried_after_backoff` and `Authorization: Correct-Horse-Battery-Staple` followed by a line break and a header: main (scheme = letters only) masks the token through the 8-or-more-character rule; head reads the token as the scheme word and masks the next word. Licence-style keys fit. Only the lower-case form is tested.
Fix: keep the narrow letters-only scheme in the single-line rule; give the hyphen class only to the fold rule, or accept a hyphenated word as scheme only from a short allowlist (`AWS4-HMAC-SHA256`, `SCRAM-SHA-*`) or only when a second token of 8 or more characters follows on the same line; differential test against main over capital-first, digit-bearing and mixed-case hyphenated tokens with 1 to 3 groups, each followed by a word and by a line break; a mutant per branch.

### [Group 3] [codebase C2] - Major (new fold rule is quadratic on a glued run)
Scope: `redact.py` new any-scheme fold rule (~979), first word `\S++` unbounded; `test_b11_8_a_long_run_of_folded_lines_is_read_in_linear_time` and M241 (spaced text only).
Gap: `'authorization:"x"' * 15000` (about 255k characters, under the 262,144 cap) makes 15,000 attempts that each scan the rest (reviewer estimate about 2e9 steps, against 0.66 s on main; not run). Minified JSON of many small objects has this shape.
Fix: bound the first word (`[^\s]{1,64}+`); a work-count or wall-clock test of the glued run and of the other glued shapes of the same class (grep the other possessive `\S++` first words); a mutant that removes the bound; add the glued shape to the cost measurement (3 or more sizes, alone, against main) and report it in the CHANGELOG. The known timing test stays untouched.

### [Group 4] [codebase C3; design F5, F7; evidence item 8] - Major (CHANGELOG count of controls without a planted fault is wrong, and the gate is blind outside the list)
Scope: CHANGELOG batch 12 item 2; `UNPLANTED_MAX = 3` (`tests/test_q8b_batch8_lines.py:188-322`, counts only the 74 table ids); NOTES.md; `cost-final.txt`.
Gap: the true count is at least 7 (runner) or 8 (reviewer): `test_b11_8_*linear_time`, `test_b8_5_*`, `test_b10_1_*`, `test_b10_2_*`, `test_b9_1_*`, `test_b9_4_*` and the three table controls. The "median of three" cost claim is backed by one value per size; load 3.7 when measured.
Fix: derive the group from every test whose name contains `linear` or that calls `perf_counter`, state the true count in the CHANGELOG, and plant a fault for each (M241 shows a quadratic plant is possible) rather than keeping the claim; record three runs per size in the cost file; correct NOTES counts (340 cells, not 339).

### [Group 5] [codebase C4] - Major (statement "only the bare ordinary word stays readable" is wider than the code)
Scope: `redact.py:308-324` `QUOTED_KEY_WORDS`/`_QUOTED_NOT_BARE`, `_not_after_ordinary_word` (223-231); `tests/test_q8b_batch7.py:449-453`, generator `tests/test_q8b_batch12.py:33-34`.
Gap (same class as r12 group 1: an exemption wider than the reading it replaced): `{"new_bypass": "<value>"}`, `{"x-bypass": ...}`, `{"x_compass": ...}` are readable on head; main's `pass` prefix rule masked them (`_` and `-` are not in `[a-z0-9]`). The generator varies only what follows the word. The evidence runner's probes did not include prefixed keys, so this is by reading and the builder confirms by run.
Fix: default to main's masking: require the ordinary word to start the key (`(?<![\w.\-])`), with a test that fails on `a148bda6`; add prefixes (`x_`, `new-`, `my.`, digits) to the generator; if a prefixed form must stay readable, it goes to the owner with the cell list (group 9), not to a note.

### [Group 6] [codebase C5; design F4] - Major (removing M195 hides a plantable fault)
Scope: `tests/q8b_mutants.py` (M195 removed), CHANGELOG item 2; old fold rule (~951) reads `X-Api-Key`, `token`, `secret`, `passwd` headers, rule ~979 does not.
Gap: `token: Digest u="a",\n response="..."` is masked only by the old rule; the sibling killer `test_b11_8_the_folded_lines_of_a_header_are_masked_for_every_scheme_and_header_name[Digest]` (:65) also runs `token:` and `X-Api-Key:`, so M195 was not shown equivalent.
Fix: re-point M195 to the `[Digest]` killer with a credential-key header name (or restore it) with a killer that fails for the named reason; run it as root and as nobody.

### [Group 7] [design F3; codebase C7, C8, C9; design F8] - Minor (limits, card path, pins)
- **F3** The any-word fold rule masks every indented sibling after any `Authorization` key with no upper bound (pretty-printed JSON loses its readable siblings; main left them). Fix: keep the five-scheme list for the unbounded fold and bound the any-word rule (until a line that looks like `key:`), or state the cost with a test.
- **C7** The rare fold breaks (vertical tab, form feed, next-line, line separator, paragraph separator) are tested only on the raw rule path and for `\n`, `\r\n` through `clean()`; CHANGELOG item 4 says the card path turns a rare break into a space but LIMITS (`k1b/redaction.py`) has no exception. Fix: test the card path for each of the five and state the result in LIMITS.
- **C8** `_LINE_TEXT` ends a line at the five rare breaks, so `Authorization: Bearer <tok>\n  part1\x0bpart2` shows `part2` where batch 11 masked it (not a regression against main). Fix: keep reading through them in a folded line, or state it in LIMITS with a test.
- **C9, F8** The "15 bare words stay shown" pin covers 8 (`surpass`, `trespass`, `impass`, `lowpass`, `highpass`, `bandpass`, `supersession` unpinned), three forms only; M236 is killed only through those 8. Fix: parametrise over `redact.ORDINARY_WORDS` and add colon and unquoted forms (the evidence shows 75 readable cells: eq, colon, json, quoted, upper-case json).

### [Group 8] [design F6, F7; codebase C10] - Nit (accepted as PROPOSE FIX, cheap)
`_OTHER_BREAKS` (redact.py:59) omits `\x1c`, `\x1d`, `\x1e` while the comment says "and of str.splitlines" (evidence: FS, GS, RS 780 of 840 readable in `fold12`; state or add); LIMITS says the second word on the same line is shown while the new rule masks up to 8 extra words when folded lines follow; the cost file and `probe_extra.py` are not in the snapshot; ratios not monotone; 60k to 120k step 0.18 to 0.47 s in the builder file; CI pin PostgreSQL 17.10 against gates on 16.15.

### [Group 9] [OWNER-ONLY: `q-q8b-bare-bypass`, `Q8bb11-hist-secret-shaped`] - Major (owner decision, not fixed here)
Scope: the 15 bare ordinary words (75 readable cells in `probe12`, 16 in `probe`, all masked on main); shape A residue and shape C (unindented continuation, 2190 of 2310 readable on head); the absolute cost budget; the history of commit `f31c0ead` holding made-up probe values (a rewrite needs the owner).
AI Suggestion: ESCALATE-to-owner, kept OWNER-ONLY. The default stays masking as main did for everything not decided by the owner; the numbers above are the basis. Not marked fixed.

### [Group evidence] [independent evidence deviations] - Minor
Perf step 1 failed (known timing test, do not touch); builder cost figures differ from measured (1.07 to 1.38); 7 unplanted wall-clock controls against the builder's 4; 15 batch-12 tests pass on old code (the builder's NOTES reasons were read as consistent by both reviewers; the builder re-checks each against the final head); Python 3.12, semgrep, zizmor, trivy, pip-audit IMPOSSIBLE-NOW.

## Who fixes it
One batch-13 builder (Sonnet 5.5) on a new branch `core/q8b-b13` from `a148bda6`, pushing to `wip/cloud-q8b-b13`. Order: group 1, group 2 (both Blockers, reproduce on head and main first), then 3, 5, 6, 4, 7, 8. Method per bug: name the class, fix at the shared choke point, grep siblings, show each new test failing on `a148bda6`, one mutant per fix with a killer that fails for the named reason, final-head full suite and `q8b_mutants` as root and nobody, a reason for every test that passes on old code, CHANGELOG and LIMITS corrections with measured numbers. Never touch the timing test. No readable secret-shaped value in any committed file.

## Handoff
- Accepted fixes (PROPOSE FIX): 8 groups plus the evidence group, covering 3 Blockers (F1/C6, F2/C1, which count as 2 groups of 3 findings), 5 Major, 4 Minor findings in group 7, Nits in group 8.
- Escalated: 1 group (9, OWNER-ONLY). Contested: 0. Declined: 0.
- Remaining unaddressed: all of the above until batch 13 is built, run through independent evidence and reviewed (round 14, no cap on this path).
