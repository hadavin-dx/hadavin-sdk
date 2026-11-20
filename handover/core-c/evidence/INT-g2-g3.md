# INT-g2-g3 (integration of G2 + G3 with G7), worktree /tmp/core-c-int, branch wip-int-g2g3

## Progress note 1 (after the conflict work, before the batch)
- redact.py (G7 settle + P1d-a _sub_glued + G3 fold scan in find()) imports, ruff check and format clean. settle() calls find(), so the fold scan runs in the second pass.
- 5 redact test files targeted run: 151 passed, 4 xfailed. Batch NOT yet run.
- Already in the snapshot: typography tests (tests/test_redact_g3_port.py), dm_2_257 comment, EMAIL tail fix `(?![A-Za-z])`, tests/test_text_parts_together.py.

# FINAL (2026-11-20), worktree /tmp/core-c-int, branch wip-int-g2g3 (never pushed)

## Commits on top of 4a8406a (G7 whole class, itself on the cherry-picks of the 5 P1d-a and 6 P2d-1 commits over f16d48e)
8f55f20 code G: integration step 5: mutants A3, A3b follow the moved code, A11 killed by a tag-split-only row, A43 by the undefang row
43cc0b1 code G: integration step 4: clean re-reads once through one shared function with a fixed note past the bound, no check pass when nothing changed (channel.py / slack_channel.py, SPINE-owned)
d064e91 code G: integration step 3: bound the glued-address search (M1), the e-mail test asserts no leak (M2), tail check M7, tag-split row N3, stale N4 exemption
b41ccc0 code G: integration step 2: A43 row test, clean() re-read cap test, glued e-mail regression and the glued-rest probe of the other value kinds
9effeed code G: integration step 1: redact.py imports and is ruff-clean (G7 second pass + P1d-a _sub_glued + G3 fold scan); typography tests, text-parts test (draft)
5316e14 code G: integration of G2 + G3 with G7, INTERRUPTED by the model limit, NOT verified
(5316e14 was the interrupted snapshot; step 1 sits on it.)

## Conflicts and resolutions (the three-way merge in guard/redact.py, as found in the snapshot, verified here)
- G7 `settle()` calls `self.find()`, so the G3 fold scan (inside `find`) runs in the second pattern pass too; `actions` counts masks of both pattern passes and both sweeps (sweep adds copies replaced). P1d-a `_sub_glued` is used for the EMAIL pattern inside the same `find`.
- `RedactionResult.actions` replaces `runmap.is_masked` (not used anywhere; cb-1-1 test asserts actions > 0).
- Test expectation changes forced by the combination (old -> new -> reason):
  1. tests/test_redact_context_after_sweep.py signature pin of `redact`: gains `_deadline: 'float | None' = None` (G3 parameter).
  2. tests/test_redact_fold.py test_ascii_2: far filler `"x"*300` -> `"x "*150`: a 300-letter run is masked as one blob, the G7 second pass then sees the bank word 17 characters before the account and masks the ASCII control line too. Intent (a window beyond 100 characters) kept.
  3. tests/test_redact_fold_budget.py test_dm_2_257...: comment names OLD (257 NFD names with ASCII Z raise InputTooLarge, 256 do not) and NEW (same edge with full-width Z; 257 plain NFD names are NOT refused and all are masked).
  4. tests/test_p1d_a_paths.py: `plain.count(value) <= model.count(value)` -> `value not in plain` and `not in model` (review M2, it excused a leak); stale `.replace("<HOSTNAME_1>[.]", "")` exemption removed (N4); fixture no longer patches slack_channel.defang_text (the module does not import it any more).
  5. Behaviour change of channel.clean: after the re-read bound the card is SETTLE_NOTE (was: the unsettled text), see M4.

## Follow-ups
(a) Typography tests: tests/test_redact_g3_port.py, 5 tests: em dash, curly quote, U+2215, U+2571, U+29F8 (each refused: line withheld with FOLD_NOTE, actions 2; the character alone hides nothing). The three new public textnorm names: `fold_view`, `without_spacing_marks`, `SPACING_CATEGORIES`. dm_2_257 comment: see above.
(b) clean() re-read cap: tests/test_text_parts_together.py (never-settling and alternating readers: 3 reads, then SETTLE_NOTE; refused read and spent budget -> note; note is stable; no check pass when nothing changed). Timing of clean (median, this machine, after steps 3-4): 174-char card 1.26 ms before the re-read -> 3.60 ms after; 71,179-char card 367 ms -> 655 ms (earlier measurement before the skip rule: 1.29 -> 2.77 ms, 336 -> 726 ms). Comment in src/hadavin_sdk/defaults.py updated.
(c) Glued rest. EMAIL pattern now ends with `(?![A-Za-z])` instead of `\b` (both EMAIL patterns): `anna.m@example.org9`, `_x`, `_` and `_a@b.cc_` masked for the model and on the card; regression tests in test_text_parts_together.py and test_p1d_a_paths.py (property pieces `_a@b.cc_`, `a@b.cc9` added). Probe of the other kinds (letters/digit/_x glued behind; script tests/ scratch probe):
  - host name: PARTLY, NOT FIXED: `db-7.corp.internal9` -> `<HOSTNAME_1>.internal9` (the identifying labels are masked, only the last label shows; `internal` is not a secret). Not changed: different pattern.
  - IPv4: letter or `_x` glued (`10.20.30.40_x`, `...40a`): shown whole. NOT FIXED (different pattern, more than the two lines). A glued digit is masked.
  - phone: `_x` or letter glued: shown whole. NOT FIXED (different pattern). Digit glued: masked.
  - IBAN: `_x` glued: shown whole. NOT FIXED. Letter or digit: masked.
  - UUID: digit, `_x` or letter glued: shown whole. NOT FIXED.
  - tenant id, account id, secrets (password=, Bearer): no gap (tests: test_glued_rest_other_kinds_with_no_gap).
  The list of NOT FIXED kinds should go to the lead as the next G ticket (a lookahead change per pattern, with its own perf and false-positive check).
(d) A43: the double-backtick guard in `_per_part` is dead under defang_text (certain=True takes the whole line) but NOT dead code: undefang_text and the sanitise default path use it. Killer: test_row_G2_undefang in tests/test_p1d_a_rows.py (`undefang_text("a``b `x[.]y` c") == "a``b `x.y` c"`); mutant A43 retargeted to it: KILLED. No code deleted.
(e) tests/test_text_parts_together.py: look-alike host (Cyrillic -> line withheld; full-width -> masked in place) + glued addresses + bank code and account: one clean() gives the exact card, second pass, undefanged pass and the Slack re-render change nothing; the model view likewise, and a second redact_text changes neither text nor map.

## Coordinator input (review G2-result-review-1)
- M1 DONE: `_NOT_ADDRESS.search(text, last, last + _GLUED_WINDOW)`; test test_glued_search_for_the_end_of_the_token_is_bounded (every search has an end within the window; deterministic).
- M2 DONE (see c; EMAIL ends in a negative lookahead).
- M3 DONE: channel.settled() returns SETTLE_NOTE after the bound (or on a RedactionError); SlackChannel._blocks calls the same `settled` (commit 43cc0b1, channel.py / slack_channel.py, SPINE-owned files; slack_channel.py lost 4 unused imports).
- M4 = M3. M5 PARTLY: check pass skipped when pass 1 changed nothing and no `[.]` was there; InputTooLarge/RedactionError in the loop -> note; ONE budget across the passes is a CPU-seconds clock from the start of clean() checked before each re-read (REDACT_BUDGET_S), NOT a deadline passed into redact_text (its signature takes none; the first two calls keep their own internal budget). defaults.py comment updated.
- M7 DONE (domain tail check in test_card_masks_what_model_masks). N4 DONE. N3 DONE: test_row_TS1_card (needs `<i> </i>`; a bare `<i></i>` is already stripped by neutralise) kills A11. N2: see (d).
- NOT touched, as ordered: slack_channel `_who()` and other card strings.

## Verification (final tree; commands, results)
- uv sync --all-extras --group test: ok. ruff check src tests tools: All checks passed. ruff format --check: 341 files already formatted.
- Batch (pytest -n 2 -m "not perf" over the files matching redact|runmap|textnorm|approvals|model_gate): 1 failed, 11542 passed, 63 skipped, 7 xfailed in 359.96s. The one failure is the known accepted red tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered (unregistered model caller guard/model_gate.py). No NEW failure. (First batch, before steps 3-5: 11527 passed, same 1 failed, 357 s.)
- perf (serial, -n 0, tests with a redact/textnorm/fold/perf match, step-2 tree): 62 passed in 165.7 s; slowest: test_k5_perf super-linear keywords 32.7 s, fold budget hostile shapes 32.0 s. After steps 3-4 the perf tests of test_p1d_a_paths and test_redact_context_after_sweep: 18 passed in 14.65 s. Redactor on 100,000 characters (budget 6 s): ASCII mixed text 0.24 s, same with non-ASCII words 1.06-1.11 s, 100,000 characters of glued addresses 0.24 s.
- tests/gate_mutants.py: 27 of 27 good; problems: [] (2m46s, step-2 tree; redact.py/channel.py changes since do not touch model_gate/runmap).
- tests/p1d_a_mutants.py full run on the step-4 tree: all KILLED except A11 (now KILLED after step 5), A15 (expected survivor, inherited), and A3/A3b SNIPPET NOT FOUND (retargeted to channel.py in step 5, KILLED). A43 KILLED. Rerun of A3*, A11, A43 after step 5: all KILLED. (The whole script was not rerun after step 5 in one go.)
- bandit -ll on guard and approvals: no output (clean).
- Re-pins: none needed in this resume (the manifest hash of textnorm.py, mutant counts and CHANGELOG were re-pinned by the earlier G3 step 4 commit 9a06491 and their tests pass); no textnorm.py change here.

## Files of other owners touched
src/hadavin_sdk/approvals/channel.py and slack_channel.py (SPINE/core-b files; ORDER 014 item 14 accepted channel.py as ours; slack_channel.py by coordinator order M3), src/hadavin_sdk/defaults.py (comment only).

## NOT RUN
Python 3.12, PostgreSQL 17, full repository suite (only files matching the grep), textnorm mutant list (tests/textnorm_mutants.py), the whole p1d_a_mutants.py after step 5 in one run, picking onto cloud/core-c (not done: no push, no pick).
