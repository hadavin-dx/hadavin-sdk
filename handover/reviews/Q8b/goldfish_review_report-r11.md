Status: resolved

# Goldfish Annotated Review Report

**Target:** Q8b batch 10, branch `wip/cloud-q8b-b10`, head `166d1313` (base reviewed head `c36ce0dc`), review round 11 by the report numbering (the review of batch 9 was `goldfish_review_report-r10.md`; the review files of this round are named `q8bb10-*-r10.md`). REDACTION path: no round cap.
**Inputs:** `q8bb10-design-r10.md` (0 Blocker, 2 Major, 3 Minor, 3 Nit), `q8bb10-codebase-r10.md` (0 Blocker, 2 Major, 10 Minor, 3 Nit), previous report `goldfish_review_report-r10.md`, independent evidence `handover/evidence/Q8b/166d1313/RESULTS.md`.
**Mode:** automated, recommended option for every item. No reviewer severity changed. Nothing contested. No Blocker; three Major open.

## Prioritized Findings & AI Suggestions (all PROPOSE FIX unless stated)

### [Issue 1] [design M1, Minor 2; codebase M2] - Major
Scope: `tests/test_q8b_batch8_lines.py:180` (`planted_killers`), `:186-202` (`NO_FAULT`, `UNPLANTED_MAX = 29`), `:250-254`, `:290-298`; `tests/q8b_mutants.py`.
Gap: the controls table (the r10-report Issue 3) is undone again. The ceiling went UP (28 to 29) when M132 was re-pointed. Of 74 controls, 38 have a planted fault, 29 have neither a fault nor a reason, 7 carry "no product line can be faulted", which is untrue (M136 and M142 plant faults in test files). Nothing fails at 29 (`<=`, a ceiling, not a gate). `planted_killers()` proves only that a mutant names a test. Also unkilled: the nine `test_b9_2_...[flag]` pins, the 4 controls-table tests, the 3 time tests, the `--apiInputTokens` pin (17 of 47 ids). M185 was dropped as "survived" with no record: a survivor is a hole in a pin. Evidence confirms 29 / 7 / 38 and 17 unkilled.
Fix: plant a fault for each control or write a checkable true reason; a count above the true number fails and the ceiling becomes the real number (target 0); check that a named killer exists and its fault text is present in the product file; replace M185 by a killing mutant. Candidate killers: change `([A-Za-z]+{_SP}+` to `([^\s"']+{_SP}+` in the flag rule (nine flag pins); make a possessive `_LINE_SPACE++` non-possessive and time it (time tests).

### [Issue 2] [design M2; codebase M1] - Major
Scope: CHANGELOG batch 10 items 4 and 5; builder notes :7, :27-28.
Gap: claims with nothing behind them. Item 5 says the gate lines name the commit each ran on; the notes section is empty and the only commit named is `95cf524f`, not the head. The full mutant run covered 179 mutants on an earlier commit; the head table has 182 (the builder said 183; evidence ran 182 of 182 good; the difference is unexplained). Item 4 says 26 ids were named by a mutant; the notes list 30 killed and 17 unkilled.
Fix: write the gate lines with the commit each ran on, or remove item 5; correct the counts and the 183 versus 182; record the full-table result on the final head.

### [Issue 8] [evidence, severity assigned by the lead: Major; no reviewer found it] - Major
Scope: `guard/redact.py` (Basic, Token, ApiKey, Bearer rules and `_DIGEST_FOLDS`); evidence `probe-readable-on-head-cells.tsv`, fuzz output.
Gap: after Basic, Token, ApiKey and Bearer headers whose token continues on the next lines, the continuation lines stay readable on head, `c36ce0dc` and main alike (72 of 72 cells; the first line is masked; Digest folded over 2 to 4 lines is now fully masked). The fuzz of 3000 texts leaves a readable stretch in 222 of 1005 wrapped-form texts on head (c36 314, main 336) and 746 of 1016 multi-cut texts (c36 760, main 861); Digest fold 0 of 979 (c36 979, main 979). Better than main, not closed. Bare scheme plus token with no header name is readable in 3207 of 9072 cells (same 3207 as main; c36 4767); bare `compass`, `overpass`, `encompass`, `bypass`, `cookiejar`, `cookiestore` stay readable by choice (`q-q8b-bare-bypass`, `handover/questions-for-lead.md:1850`).
Fix: continuation lines of a folded header for the same schemes as for Digest, with the same two-sided pins and limits; classify every remaining readable fuzz stretch by shape and fix each shape that is not a stated owner choice. The bare scheme plus token class stays as on main unless the owner says otherwise: add it to `q-q8b-bare-bypass` (lead action in this report's handoff).

### [Issue 3] [design Minor 1; codebase m2, m3; design Nit] - Minor
Scope: `redact.py:313-315`, `:343-353` (`_FLAG_NOT_ORDINARY`, `(?![a-z0-9])`), `k1b/redaction.py:125`, `:256` (`_CAPITALS_COOKIE`).
Gap: drift between text, flag and record paths. `--compass_key2 v`, `--possession-id2 v`, `--bypass_key2 v`, `--compass2-key` stay readable as flags while the record walk strips trailing digits and `key=value` is masked; `compass.key=v` text (pair rule allows only `[_-]?`) against the record walk's split on `.`; `compass_keyboard=v`, `possession_identity=v` masked in text but the record key stays readable; `--possession_cookie` has no flag rule yet CHANGELOG lists it as masked in a flag; `_CAPITALS_COOKIE.search(key)` runs on the raw key before NFKC and `_FOLD`; the flag guard does not read a wrapped `--authorization Basic<LF>token` (same as main); no digit or dot rows in the new tests.
Fix: allow `[0-9]*` in the look-ahead; digit and dot rows for flag, text and record; decide each name explicitly; one test per path.

### [Issue 4] [design Minor 3; codebase m5, m6; Nits] - Minor
Scope: `redact.py:781`, `:869-885`; LIMITS in `k1b/redaction.py:80`; CHANGELOG item 2.
Gap: Digest fold limits not stated or pinned: the fold run is unbounded (an unrelated indented block after the header is masked); a first line shorter than 8 characters (`Authorization: Digest u="a",<LF> response="<hash>"`) matches neither alternative, so the folded response stays readable; LIMITS and CHANGELOG wording about "any line break after Basic, Token, ApiKey, Digest or Bearer" holds inside an Authorization header only (a bare `Basic<LF>` uses `[a-z0-9+/<>_]`, bare Bearer needs 12, the other schemes have no bare rule: as main); two stale comments (`:781`, `:869`).
Fix: pin both sides, name both in LIMITS, fix the comments. Done together with Issue 8.

### [Issue 5] [codebase m1] - Minor
Scope: `redact.py:233-240`, `:266-276`; `k1b/redaction.py:156-162`, `:236`; `tests/test_q8b_batch8.py:218-220`.
Gap: CHANGELOG item 6 "one table" is overstated: `KEY_ALTERNATIVES` is nine hand-typed `_guarded_key` calls (the comment says it is generated); the record walk's glued side is the hand list `GLUED_ENDINGS`; `GUARDED_GLUED` is dead in `src` and its comment is stale.
Fix at the choke point: generate `KEY_ALTERNATIVES` and `GLUED_ENDINGS` from the one table, delete the dead name, make the test compare the generated sets; or reword the CHANGELOG to what the code does.

### [Issue 6] [codebase m4, m8, pass-on-old, notes arithmetic] - Minor
Scope: `tests/q8b_mutants.py` (M159, M130, M165, M90, M110, M171); `tests/test_q8b_batch10.py` (`test_b10_6_..._stays_readable[*]`); notes :21, :38; evidence `passed-on-old-code.txt`.
Gap: M159 was removed as "equivalent", but under `_LINE_SPACE = [ \t]` the text `Authorization: Digest\x0busername=u, response=<secret>` loses the Digest rule, so `test_b9_1_a_digest_header_goes_on_after_a_line_fold_and_a_no_break_space_but_not_after_a_plain_line_break` should kill it; M130 duplicates M165 (identical old and new text, r8 Issue 7 pattern) and sits at the wrong indent; CHANGELOG "killed by a test of batch 10 or batch 8" is wrong for M90 (batch 6), M110 (batch 7), M171 (batch 9); the 15 `test_b10_6_..._no_family_stays_readable[*]` tests fail on old code only because `ordinary_second_words` does not exist (AttributeError): controls, so "62 failed" overstates behavioural proof; notes say "the other 11 words fail" (14 of 15); a renamed test is named in the notes. Evidence: 62 failed and 5 passed for the new file; 126 of the batch 8/9 tests pass on old src and 4 fail.
Fix: run M159 and keep it if killed; remove or re-point the M130 duplicate; correct the claims; split out the AttributeError tests; re-record.

### [Issue 7] [codebase m7, m9, m10; Nit] - Minor
Scope: CHANGELOG batch 9 items 1, 7 and 9, batch 10 items 1, 2 and 6; builder notes :14; `tickets/Q8b-partial-mask-and-card-redaction.md:30, :156`.
Gap: b9 item 1 still says `_SCHEME_GAP` serves the Digest rule; b10 item 2 claims it corrected b9 items 1 and 6 but fixes only a count and the cost; b9 item 7 reads "M159 to M178"; M185 appears nowhere; the cost claim does not reconcile (b10 "1.5 to 2.2x main and 0.85 to 1.0x batch 9" against b9 "3.05 to 3.44x main"); independent evidence measured head at about 1.8x main on hostile text and 2.0x on prose, `c36ce0dc` equal to head, 400 kB takes 1.413 s (time doubles with size); the corpus count "8 matches in 10.4 million lines" looks too low for the same-line form; "ticket 1f counted the names that stay readable as 6" is wrong (the 6 is from b9 item 6; ticket 1f says 107,041 keys, 0 refused); the A2 key check was not shown rerun; "1 left readable" omits bare `compass` and `possession`.
Fix: use the measured numbers and say which shapes were measured; say what the corpus count counts and that the corpus is the build machine's installed docs and source; correct the attributions; show the A2 key check rerun.

### [Issue 9] [Nits] - Nit
Gap: stale test name in notes :38; the "exact inputs" and "limits_and_changelog" b10 tests are string-presence checks; `test_b10_6_..._so_xcompass_key_is_a_key_as_before` is killed by its second loop, not by the name it carries; the differential test (`test_q8b_batch10.py:144`) omits `\x1c-\x1f`, U+2028, U+2029 as gaps; time tests catch only a quadratic fault.
Suggestion: fix those in files the builder edits; list the rest with a reason. No new review round for Nits.

### [Issue 10] [evidence deviations] - Minor
Gap: full pytest on the head: 1 failed, 11011 passed, 1 skipped, 29 deselected, 16 xfailed. The one failure is `tests/demo_askdata/test_validate_harm.py` dblink-connect, caused by the runner not setting PGUSER and PGHOST in its own server environment; the file alone gave 253 passed after the restart; the whole suite was NOT re-run. `uv sync --locked --no-build` fails here (known). The known timing flake failed 3 of 3 on head and 2 of 3 on main on a shared machine (do not touch). Not run: pip-audit, semgrep, zizmor, trivy, tests-py312, perf (impossible here, already ledgered); the ticket's own acceptance commands (only the runner's own probes were run).
Fix: the final-head evidence of the next batch runs the whole suite clean with PGUSER, PGHOST and PGPORT in the server environment, and the ticket's acceptance commands.

### [Issue 11] [evidence] - closed
Closed by independent evidence: ruff, format, bandit -ll, scan_repo, gitleaks exit 0; `stage_mutants` 37 of 37; `q8b_mutants` 182 of 182 good; `mutation_runner_mutants` 64 of 64; header table 9072 cells per version: head 0 readable with `Authorization:` or `Proxy-Authorization:` in front and a real scheme for every gap and length tested; ordinary word pairs masked as stated.

## IMPOSSIBLE-NOW
None new (pip-audit, semgrep, zizmor, trivy, Python 3.12 already ledgered).

## Handoff
- Findings in: design 2 Major, 3 Minor, 3 Nit; codebase 2 Major, 10 Minor, 3 Nit; plus 1 evidence finding; merged into 11 groups.
- PROPOSE FIX: 10 groups (Major 1, 2, 8; Minor 3-7 and 10; Nit 9). CONTEST 0. ESCALATE 0 (the bare scheme plus token class is appended to the existing owner question). DECLINE 0. Closed by evidence: 1. IMPOSSIBLE-NOW new: 0.
- Applied edits: none to code by this skill. Remaining unaddressed: groups 1-10 (OPEN). No Blocker.
- **Who fixes it:** one batch-11 builder (general-purpose, Sonnet) on `core/q8b-b11` from `166d1313`, pushing to `wip/cloud-q8b-b11`. Files: `src/hadavin_sdk/guard/redact.py`, `src/hadavin_sdk/k1b/redaction.py`, `tests/test_q8b_batch10.py`, `tests/test_q8b_batch8.py`, `tests/test_q8b_batch8_lines.py`, `tests/test_q8b_batch9.py`, `tests/q8b_mutants.py`, `CHANGELOG.md`, the builder notes. Order: 8, then 3, 5, 4, 6, 1, 2, 7, 9, 10. Method per bug: name the class, fix at the shared choke point, grep siblings, show each new test failing on `166d1313`, one mutant per fix, gate lines with the commit each ran on, final-head evidence (whole suite clean). Redaction path: no round cap.
