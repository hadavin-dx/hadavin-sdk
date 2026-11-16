# citation-review-r4: cites added or changed in round 25 of `reviews-of-core-patches/REVIEW.md`

Read-only, static check. I edited nothing else. Paths below are relative to `handover/flows-audit/reviews-of-core-patches/` unless a full path is shown. Checkout HEAD when I read: `de16a926a`. `src` and `tests` there show no difference from `176a0cbe0` (`git diff --quiet 176a0cbe0 -- src tests pyproject.toml`, rc 0). The patches target `b4cce5b`; 22 `src` files differ between `b4cce5b` and HEAD.

## What I could not check (first)
- Every Postgres statement in Decisions 26 to 29 and criterion (8) and (9) (advisory-lock signatures, `aclexplode`, CODEOWNERS and branch-rule behaviour, signature handling): no source or host to read. REVIEW marks them UNVERIFIED, and that mark is correct.
- Day and size figures in Decisions 26 to 29: assistant judgement, no source.
- The "FIRST-version" patch files (hunk headers +1,53 and +1,74) no longer exist in `patch-copies/`. The scratch copy `/tmp/core-b4p/tests/` still exists and has 53 and 74 lines with 16 and 19 blank lines, which agrees with 37 and 55 (checked), but it is a scratch folder and not durable.
- I did not re-run any test or the verdict script. I did not check the roughly 400 older `src` cites outside round 25; I checked the ones round 25 added or re-pointed (see log `fix-review18.md`).
- `README` moved while I read it (it was edited at 15:50 UTC, after REVIEW at 15:48 UTC). Line numbers below are from the file as it stands now, 329 lines.

## Table (MISMATCH first)

| Cite | Claimed | Found | Result |
|---|---|---|---|
| REVIEW 66 and 129: quote '9394 = 9364 + 30' at "README line 168" (citation check) / "line 188" (when REVIEW author looked) | text sits at README line 168, then 188 | text is at `patch-copies/README.md:227` (`(9394 = 9364 + 30)`), only there. Line 145 names the figures 9364, 9394, 9396 as examples; line 156 holds `+ 30 (or + 32)`; line 168 is now a shell function `offenders()`; line 188 is the "Known baseline failures" paragraph | MISMATCH (both numbers stale; the quoted text exists). The advice "search the quoted text, not a number" is right |
| Your question: quote at REVIEW "lines 66 and 128" | 66 and 128 | the quote is at REVIEW lines 66 and 129; line 128 is the heading "Verdicts by patch..." | MISMATCH (128 should be 129) |
| REVIEW 66: README "pass criterion of clauses (a) to (e), where (e) is that all guard tests are green" | (e) exists | README "Pass rule" (line 176) says "Clauses (a) to (d)"; (d) is the two red guard tests (d1, d2); there is no (e) (grep `(e)` finds nothing in the clause list) | MISMATCH (a real wording error, not only a line move) |
| REVIEW 66: "README line 7 says price-only 24 new tests plus 6 of A-01 = 30; line 8 says `C-01.patch` has 26 new tests, 32 with A-01" | lines 7 and 8 | the same sentences are at README lines 9 and 10 (lines 7 and 8 are the end of the STATUS paragraph). Numbers 24+6=30 and 26+6=32 are right | MISMATCH on line numbers (numbers MATCH) |
| REVIEW 146: "`README.md:23-24`" (200_000 is the author's choice, needs studio head's yes) | lines 23-24 | lines 23-24 are glossary rows (audit kind, outbox). The matching text is README line 49 (decision row 3: "the number is my placeholder, not from a provider page; studio head") | MISMATCH (stale, older round) |
| REVIEW 157: "`README.md:32-33` describes the step without it; `README.md:36` uses 'held in memory only'" | 32-33, 36 | lines 32-33 are glossary rows (G5/G2..., RUNG); line 36 is a glossary row on Decisions 18, 19, 23. 'held in memory only' is README line 293; the docstring text "or in memory" is line 292 | MISMATCH (stale, older round) |
| REVIEW 171: "patch README.md:51, 'Remaining text I did not change'" | line 51 and that quote | line 51 is decision-table row 5 (database login). The phrase "Remaining text I did not change" appears nowhere in README (grep: no hit for "did not change" in that sense) | MISMATCH (quote not found; cannot place it) |
| REVIEW 161: tick-test hunk "`patch-copies/A-01.patch:248-265`" | 248 to 265 | hunk starts at 248 (`diff --git a/tests/test_p7_tick.py`); the file has 264 lines, so it ends at 264, not 265 | MISMATCH by one at the end |
| README line 36 (pointer into REVIEW): blocks of Decisions 18, 19, 23 "near its line 384 to 390" | 384-390 | blocks are at REVIEW lines 390, 391 and 395-396 | MISMATCH (README side, written against an older REVIEW; not a REVIEW cite) |
| REVIEW 66: README "9394 = 9364 + 30"; baseline `9364 passed`, patched `9394 passed` | present | README 227: baseline `2 failed, 9364 passed, 454 skipped, 26 deselected`; price-only plus A-01 `9394 passed` | MATCH (text; line is the mismatch above) |
| REVIEW 66: README "12 failed and 18 passed on the old code" | 12 / 18 | README 204 and 231: `12 failed, 18 passed` (price-only file); `13 failed, 19 passed` for `C-01.patch` | MATCH |
| Hunk header `C-01.patch:48` `@@ -0,0 +1,64 @@` (REVIEW 72, 139) | line 48, +1,64 | `C-01.patch:48: @@ -0,0 +1,64 @@` | MATCH |
| Hunk header `A-01.patch:124` `@@ -0,0 +1,123 @@` | line 124, +1,123 | `A-01.patch:124: @@ -0,0 +1,123 @@`; body 125-247 = 123 lines | MATCH |
| `C-01-price-only.patch:27` `@@ -0,0 +1,51 @@`; 78 lines; two files; config hunk `@@ -362,6 +362,16 @@` | as stated | line 27 and hunk text match; `wc -l` 78; two `diff --git` (config.py, test file); no defaults.py hunk | MATCH |
| `C-01.patch:87-93`, `C-01-price-only.patch:66-72` (non-finite price test, match 'finite') | those lines | exactly the decorators, def, comment, `pytest.raises(... match="finite")`, `_load(...)` | MATCH |
| `A-01.patch:98` ("wait there (or in memory)"), `:102-104` (getattr, RuntimeError), `:261` (assertion the step ran) | as stated | line 98 docstring "(or in memory)"; 102-104 `fn = getattr`, `if fn is None`, `raise RuntimeError`; line 261 `assert app.store.get_tick_state("audit_reconcile").last_ok_at is not None` | MATCH |
| Test counts: price-only 24 (6+1+16+1), `C-01.patch` 26, A-01 6 test functions; 24+6=30, 26+6=32 | as stated | counted from patch text: price-only 6+1+16+1 = 24; `C-01.patch` adds 2 ceiling tests = 26; `A-01.patch` has 6 `def test_` | MATCH |
| Withdrawal "README line 8 says 24 instead of 26" was false | withdrawn | agreed: no contradiction exists; README lines 9-10 say 24 and 26 | MATCH |
| Counts block (REVIEW 301, 596): 28 rows; Major 4, Minor 13, Nit 11; PROPOSE FIX 25, DECLINE 3 (C-1, C-5, A-9) | as stated | `python3 -I count_review.py REVIEW.md`: rows 28; Major 4, Minor 13, Nit 11; PROPOSE FIX 25, DECLINE 3. I listed rows: Majors X-2, X-4, X-5, X-6; DECLINE rows C-1, C-5, A-9; the 13 Minors and 11 Nits named at line 301 agree with the row ratings | MATCH |
| "33 answers (29 + 2 + 1 + 1)" (REVIEW 323) | 33 | decision table at REVIEW 332-364 has 33 rows: 1-8 (8), 9a, 9b (2), 10-22 (13), 23a, 23b (2), 24-29 (6), Q1, 5-K (2) = 33. 29 numbers + 2 splits + 5-K + Q1 = 33 | MATCH |
| "Twenty-two matter for today's code ... seven only if a patch is applied" (REVIEW 74, 323) | 22 and 7 | Decisions 1-15 (15) + 21, 22 (2) + 25-29 (5) = 22; 16-20, 23, 24 = 7; total 29 | MATCH |
| Decision blocks and table rows for 26-29 (REVIEW 399-402, 359-362; paragraph 457) | present | blocks at 399-402, table rows at 359-362, paragraph at 457, work list at 461-462; internal pointers (26 to 27 to 28; 29 depends on 7) agree between block, row and paragraph | MATCH |
| Note on block count | - | block lines starting `- **Decision` number 32 (includes an umbrella "Decision 9" heading beside 9a and 9b), plus Q1 and 5-K as "Question" blocks: this is not the 33 rows, but it is not a contradiction (umbrella heading) | MATCH (note) |
| Decision 29 text: "`signer: none` is not accepted" | refused | `config.py:419-420` and `backends/table.py:604` (`NOT_PROD` holds `("signer","none")`) refuse it only when `is_prod(environment)`. Outside production it is accepted | MATCH on cite; WORDING gap: "not accepted" should say "refused in production" (REVIEW 209, 224, 287, 375 say it correctly) |
| `chain.py:120`, `migrate.py:314` (advisory xact lock, one-number form) | those lines | both lines hold `pg_advisory_xact_lock(%s)` at b4cce5b and HEAD (files unchanged between them) | MATCH |
| `chain.py:173` (`_pending`), `migrate.py:50-51` (approval requests/decisions grants), `migrate.py:193-262` (`effective_problems`), `migrate.py:298-303`, `tick.py:85` (`reconcile` step), `app.py:62` (`build`) | as stated | each line holds what is claimed at HEAD; `app.py:62` is `def build(` at both b4cce5b and HEAD | MATCH |
| `agent_loop.py` cites (241, 252, 485-486, 799-804, 806, 817, 845-867, 847, 853-854, 879, 886, 901, 909) | line numbers | all agree with HEAD `de16a926a`. At `b4cce5b` the file is 46 lines shorter before `execute` (`execute` at 760, not 806), so these cites are valid ONLY at HEAD | MATCH at HEAD; MISMATCH at `b4cce5b` (REVIEW's "src" tag means this checkout, so correct as tagged) |
| `agent_loop.py:768` ("moving ... to the tick", row 8) | line 768 | HEAD 768: `return self.execute(run.run_id)`; b4cce5b 768 is a different line (`stop = self._recheck(...)`) | MATCH at HEAD only |
| `config.py:64, 68, 393, 401` (base 1, this checkout) | as stated | HEAD: 64 `class Route`, 68 `max_tokens`, 393 `refused = []`, 401 environment raise | MATCH |
| `config.py:365`, `:59` (base 2, `b4cce5b`) | as stated | b4cce5b: 365 `refused = []`, 59 `max_tokens` | MATCH |
| `../inputs/DECISIONS-2026-11-16.md` line 1 and "item 4 (line 5)" | as stated | line 1 "Lead decisions 2026-11-16 ... the owner may veto any line"; line 5 is "4. C5 core patches: A-01 DEFERRED, C-01 extras CUT" | MATCH |
| `evidence-13.md:23-24` (15 failed, 55 passed), `:99` (mutation (c)), `:105` (+37, +55), `:13` (22 collection errors), `:43-58`, `:63-73` | as stated | 23 `rc=1; 15 failed, 55 passed`; 24 the 15 names; 99 mutation (c); 105 `test_a01_audit_reconcile.py +55`, `test_c01_route_limits.py +37`; 13 "22 collection errors"; 43-44 and 63-64 are the failure and per-file blocks | MATCH |
| `../heavy-test-lane/evidence-guards-after-fix.md:4-14` | lines 4-14 | git status listing at lines 4-14 | MATCH |
| `../reviews/fix-review16.md`, `fix-review17.md`, `fix-review18.md`, `fix-patchcopies4.md`, `incident-g5-patch-copy.md`, `review-*-r18` to `r25`, `citation-review-r3.md` | exist in `../reviews/` | all exist | MATCH |
| Bare names in THIS folder: `evidence-13.md`, `fix-review13.md`, `fix-review15.md`, `fix-patchcopies1.md`, `review-design-r17.md`, `fix-review1..12.md` | in this folder | all present; `fix-review7.md` is absent, as REVIEW 485 says | MATCH |
| `evidence-baseline.md`, `evidence-patched.md`, `evidence-guards-after-fix.md` (REVIEW 474) bare names | not in this folder | they are in `../heavy-test-lane/` (all three exist there); REVIEW names `SUMMARY.md` beside them, so the folder is implied, not written | MATCH (note: path not written) |
| `G5-wording.patch` | not in tree | absent from `patch-copies/` (by design, Decision 23a) | MATCH |
| `/tmp/ch`, `/tmp/core-b4p`, `/tmp/core-b4m`, `/tmp/smfull` | exist at start of round 25 | all four exist now | MATCH |
| REVIEW line 3 time stamp "15:48 UTC / 21:18 IST" | 21:18 = 15:48 + 5:30 | arithmetic right; file modified time 15:48 | MATCH |
| Proposed dates "end of 2026-11-18 UTC (05:30 IST on 2026-11-19)" (REVIEW 460, 463) | UTC to IST | 24:00 UTC + 5:30 = 05:30 IST next day | MATCH |

## Summary
- MISMATCH: 9 rows (the two '9394' line numbers, the "128" line, the false clause "(a) to (e)", README lines 7/8, and four older README cites plus A-01.patch end line 265; README's own pointer to REVIEW 384-390 is a tenth stale cite on the README side).
- The most important: the "(a) to (e), (e) = all guard tests green" statement at REVIEW 66 is wrong in content (README has clauses (a) to (d)); fix by naming (a) to (d) and saying (d) is the guard-test clause.
- Everything else added in round 25 (counts block, 33 answers, 22 + 7 split, Decisions 26-29 blocks and rows, hunk headers, test counts, source cites at HEAD) matches.
- Because the README keeps being edited, the safest fix is what REVIEW already advises: cite by quoted text or section name ("Pass rule", "Baseline, then the patched run"), not by line number.
