# out-g2: conflict map, core docs patch vs claims series

Read-only analysis. Nothing in /tmp/review-tree, the realhead clones, final-series.diff or the patch was edited.
All trials ran on scratch COPIES under /tmp/claude-0/-home-user/b34836a1-affe-5ae5-ba66-3c71b6499c1e/scratchpad/
(rt* = copies of /tmp/review-tree, mn* = copy of the f3c39cf clone /tmp/realhead.7fEhlw/c).
EGM skipped: read-only analysis, no deliverable code or text for the owner. Bible R-numbers: not looked up (the studio
folder path is not in the brief; this task needed none). Token use: not measured.

## 1. Why it does not apply (the root cause)

Core's patch is a delta on a BASE THAT IS NOT main f3c39cf and not in main's history. The index lines name base blobs
that exist in no clone: contract.md 08d0722, docs/real-services.md 71bfc5b, docs/settings.md 9fcff6d,
scripts/real-run.env.example f453632 (git cannot resolve them; `--3way` says "repository lacks the necessary blob").
docs/tests.md b040092 exists only in older main (c30c373, 61ded9e). README.md, docs/hubspot-probe.md, docs/limits.md and
both workflows do match main's blobs.

Core's base also describes CODE that main and the claims tree do not have (checked by grep, all three trees):
- run_real_check.py start question: main and claims tree ask `Start? [y/N]` (line 920). Core's docs context says the user
  types the HubSpot host and `y` does not start it. No `GetConsoleMode` in any tree under /tmp.
- `--assume-yes` exists only in run_real_check.py (4 hits); run_live_check.py has 0. Core's docs say it exists there too.
- core says `DESK_HUBSPOT_BASE_URL` is required with no default; main/claims code and real-run.env.example say it has a
  default (HUBSPOT_BASE_URL) and is optional.
- core README hunk 7 names `scripts/precheck.py`: file does not exist in the claims tree nor in main (0 hits).
So part of core's patch documents a core code branch that is not on main. Applying those hunks would write false text.

## 2. git apply --check results (on copies)

Whole patch, all-or-nothing:
- claims tree: FAILS, 9 files: README.md, contract.md, docs/hubspot-probe.md, docs/limits.md, docs/real-services.md,
  docs/settings.md, docs/tests.md, scripts/real-run.env.example, versions.md.
- main f3c39cf: FAILS, 3 files: docs/real-services.md, docs/settings.md, scripts/real-run.env.example.

Per hunk, single-hunk `--check` (rt = claims tree, mn = main):

| file | hunks | claims tree | main |
|---|---|---|---|
| .github/workflows/lint.yml | 1 | ok (offset 2) | ok |
| .github/workflows/sonar.yml | 1 | ok | ok |
| README.md | 7 | 1-6 FAIL, 7 ok | all ok |
| contract.md | 1 | FAIL | ok |
| docs/hubspot-probe.md | 1 | FAIL | ok |
| docs/limits.md | 1 | FAIL | ok |
| docs/real-services.md | 2 | both FAIL | 1 ok, 2 FAIL |
| docs/settings.md | 4 | all FAIL | 2 ok; 1, 3, 4 FAIL |
| docs/tests.md | 3 | 1, 2 FAIL; 3 ok | all ok (offset 18) |
| load_tools/README.md | 1 | ok | ok |
| scripts/crash_desk.py | 1 | ok | ok |
| scripts/real-run.env.example | 1 | FAIL | FAIL |
| tests/test_docs_match_tools.py (new file) | 1 | ok | ok |
| versions.md | 1 | FAIL | ok |

Patch defect: the new-file header reads `diff --git a/tree-F4c/tests/test_docs_match_tools.py b/tests/test_docs_match_tools.py`
(a stray `tree-F4c/` on the a/ side). `git apply` copes (it uses the b/ path); `patch -p1` or `git am` may not.

## 3. Conflict map, per file and hunk
Series hunk numbers are those of final-series.diff for that file. Line ranges are old-side (main) lines.

Verdict key: SAME = same fact, only wording differs; DIFF = differ in fact or strength; STALE-S = the series sentence
is stale/inexact, core right; STALE-C = core's text is stale or describes absent code; CTX = old sentence still present
exactly, hunk fails only because the series rewrote neighbouring lines (a re-base of context fixes it).

### README.md (series hunks 1-5 cover lines 5-145)
| core hunk | core old lines | overlaps series | verdict |
|---|---|---|---|
| 1 "What you will see" bullet 1 | 17-23 | s1 | Same sentence edited twice. Series only adds "(web form or webhook)" and keeps "changes nothing". Core says no second lead/email, one receipt number consumed, `receipt_id` 3 for the other door. STALE-S: in the claims code the replay does `ON CONFLICT DO UPDATE SET attempts = attempts + 1` (desk.py 1363) and SQLite AUTOINCREMENT skips id 2 (I ran this in sqlite3: ids 1, 3). Merge: core's sentence plus series' "(web form or webhook)". Also context lost because series rewrote bullet 3 (reminder, 90 s). |
| 2 "Replayed" definition | 34-40 | s1 | CTX + STALE-S. Old line present exactly. Core adds `attempts` and the due-follow-up rule. |
| 3 Linux feed comments | 59-66 | s2 | CTX + STALE-S. Old lines present exactly; series changed the outbox comment under them (90 s). |
| 4 Windows feed comments | 76-83 | s2, s3 | same as 3. |
| 5 "Claimed" bullet 1 | 93-99 | s3, s4 | CTX + STALE-S, plus DIFF in strength: core says "repeats cannot use up the 5 automatic tries"; series' contract.md line 308 deliberately says "not meant to use up" and notes no test replays with the wait passing until the 5th try. Core's wording overclaims against the series' evidence. |
| 6 "Tests and more commands" | 127-133 | s4 | DIFF. Both rewrite the same sentence. Series drops the "about 20 minutes" claim and says other combinations are "not supported". Core replaces it with "16 minutes 33 seconds for 2516 tests ... (`docs/tests.md`)". The claims docs/tests.md has no 2516/16:33/2ce1f98/993 s figure (it has 2465 tests, 958 s, commit 558d37f), so core's cross-reference would dangle. STALE-C on the claims tree; take the series sentence. |
| 7 layout list, `scripts/precheck.py` | 145-151 | s5 | Applies cleanly, but STALE-C: scripts/precheck.py does not exist in the claims tree or main. Do not apply. |

### contract.md (series hunk 8, lines 170-181)
core hunk 1 (175-181), the HTTP-table intro. Series rewrote the same paragraph ("carry Content-Length ... JSON, except the GET /ui 308 ..."); the old sentence is no longer there. Core's added text (replay makes no second lead/email; starts the follow-up only when due) is a fact the claims code supports (`_pending_and_due`, desk.py 1417) and contract.md line 308 already says the due rule. SAME fact, but the two use different strength ("cannot use up" in core's test pin vs "not meant to" in series). Core's new sentence also has a typo: "no second email; If the follow-up". Re-base onto the series paragraph, soften "cannot".

### docs/hubspot-probe.md (series hunks 3, 4, lines 39-61)
core hunk 1 (49-56). Old lines present exactly (claims line 46); fails on context only (CTX). Core is more exact: `--plan` does not look at the name, a bad name is refused only with `--yes-spend-calls`. I ran the code assertions of core's test on the claims tree and they pass (bad name refused and not printed, `--plan` returns 0). STALE-S: the series keeps "anything else is refused without being printed". Take core, re-based.

### docs/limits.md (series hunk 1, lines 1-83)
core hunk 1 (68-74) edits the "Run on two systems ... 2449 passed" bullet. The series already rewrote and moved it (claims line 65: "run on earlier commits ... not on the commit that holds this file ... neither was repeated on this commit") and adds a line 66 on 2462+2=2464 vs the 2465 run. SAME fact; the series text is the fuller one. Drop core's hunk. Side effect: core's test `test_every_old_test_count_is_named_as_from_an_earlier_commit` fails on claims limits.md line 66 (it mentions 2464 without the words "earlier commit"/"earlier full run") and wants the literal phrase "on an earlier commit, not named here".

### docs/real-services.md (series hunk 1, lines 1-22)
- core hunk 1 (1-6): core replaces "The steps above use only the demo stand-ins". Series already replaced that sentence ("This section is for someone who wants to try the desk against their own free HubSpot account..."). SAME intent (this section is not part of the demo). Apply on main, drop or re-word on the claims tree.
- core hunk 2 (8-22): STALE-C for most of it. Core's text describes the typed-host start question, `--assume-yes`, a "F1 to F6" check naming and a BOM warning for a core code branch. The claims text, like the claims code, says `y/N`. Only the doc-only advice (BOM, full paths) could be carried over after the owner checks it against the claims code; it must not go in with the typed-host sentences. Fails on main too (main's step 3 and intro differ).

### docs/settings.md (series hunks 1, 2, 4; lines 1-44, 48-87, 118-126)
- core 1 (1-6): CTX/DIFF. Series rewrote the opening paragraph and has no "HubSpot key file at its first CRM call" sentence. Core says the key file is opened at EVERY call (claims crm_hubspot.py `_key()` reads the file each call: consistent). Core's text also says the real-run script "checks the file before its start question" (typed-host code).
- core 2 (48-54), `rota`: SAME fact (`crm_owner_id` key required, value may be empty); different wording. Takes either; applies on main only.
- core 3 (67-85): mostly SAME/more exact. `DESK_SMTPP_TIMEOUT_SECONDS`: series says default 5.0, smaller `DESK_SEND_TIMEOUT_SECONDS` wins; core says the same and adds the 9-second ceiling (claims constants.py CALL_DEADLINE_MAX_SECONDS = 9.0 and smtp_provider.py agree). Core also adds that `run_real_check.py` sets `DESK_SEND_TIMEOUT_SECONDS=8` (not checked). Core's KEY_FILE text mentions the start question (STALE-C part).
- core 4 (120-129): DIFF. Core's text says no default base URL for run_live_check and a refusal for `http` loopback (core-only code); the claims docs line 101 says `DESK_LIVE_BASE_URL` defaults to the provider's address. Core also adds `DPLD_REQUIRE_COUNT` and a second reader of `DPLD_REQUIRE_SCAN` (`tests/test_gitleaks_exceptions.py`); those two sentences are valid only if the new test file and that test file go in.

### docs/tests.md (series hunks 1, 2; lines 1-57, 67-114)
- core 1 (23-29), crash scene command. Series reworded the sentence but kept `PYTHONPATH=src python scripts/crash_desk.py`. Core says it needs `src:.`. STALE-S, verified: on the claims tree `PYTHONPATH=src` makes the desk exit with "the folder demo_only is missing" (core's crash-script test failed that way in my run). Take core's command; also take its crash_desk.py docstring hunk.
- core 2 (57-67): DIFF/STALE-C. Core's base had a "full run on this lock ... 2516 tests ... 993 s" bullet and a "2329/135" bullet; the series replaced the first with "Counts from earlier full runs ... 958 s" and put a semgrep exit-code paragraph where the 2329 bullet sat. Core's new first bullet adds "This tree holds 3995 tests in 97 test files". The claims tree has 92 test files (93 with core's new file), so 97 is not the claims count; 3995 not measured by me (no full collect run, see 5).
- core 3 (99-105), row P1 (b): applies ok (offset 18 on main; ok on claims). Old text present, "changes nothing" stale (STALE-S); core adds the receipt-number and due-follow-up facts. Take core (soften "cannot use up").

### versions.md (series hunk 1, lines 1-29)
core 1 (6-12) rewrites the "Python required" row's 2449/2462 sentence. The series removed the pass counts from that row altogether (row is now "3.12 or newer ... The tests/ folder holds 92 test files") and moved the counts to limits.md. STALE-C: drop core's hunk. Core's test still asserts `"on an earlier commit, not named here"` in versions.md and limits.md (fails; see 4).

### scripts/real-run.env.example (not in series)
core 1 (16-22). Fails on main and claims tree because the context is core's "REQUIRED ... <HUBSPOT_ADDRESS>" text; main/claims say the base address is optional with a default. Core's added clause ("a loopback test address included, also needs DESK_HUBSPOT_ALLOW_ANY_BASE_URL=yes ... must be an https address at one of the vendor's own domains") is true on the claims code (crm_hubspot.py 170 and 192) and can be carried over as a one-line edit to the existing "any other host needs ..." sentence.

## 4. Non-overlapping core hunks that apply cleanly on the claims tree

| hunk | applies | caveat |
|---|---|---|
| .github/workflows/lint.yml (+DPLD_REQUIRE_COUNT) | yes | only meaningful together with the new test file |
| .github/workflows/sonar.yml (+DPLD_REQUIRE_COUNT) | yes | same |
| scripts/crash_desk.py docstring (`src:.`) | yes | fact verified on claims tree (demo_only missing with `src` only); Linux form only was run, as core says |
| load_tools/README.md "A whole run" recipe | yes | flags checked against catcher.py, load_driver.py, check_invariants.py argparse (all exist, `dupmix:TOTAL:FRACTION` valid); I did NOT run the recipe. Series touches load_tools/catcher.py (docstring) but not this README: no overlap |
| tests/test_docs_match_tools.py (new, 262 lines) | yes (file is new) | applies but does NOT pass, see below |
| README hunk 7 | yes | false on claims tree (scripts/precheck.py absent), do not apply |
| docs/tests.md hunk 3 | yes | overlaps series docs; counted above |

Run of the new test on a scratch copy of the claims tree with only that file added (venv with pytest only, 8.3 s):
`9 failed, 1 passed, 3 errors`. Failures, with the reason from the output:
- windows_form and crash_script tests: docs/tests.md lacks core's "was not run on Windows" sentence; crash script exits because tests.md still says `PYTHONPATH=src` (demo_only missing).
- repeated_request test: README lacks `"receipt_id": 3` and "can skip but are never reused" (code assertions before it passed: ids 1, 3).
- probe test: only the last assertion fails (page lacks "`--plan` does not look at the name"); the code assertions pass.
- no_page_says_changes_nothing: README lines 20, 62(79), 96 and docs/tests.md P1 still say "changes nothing".
- every_page_about_a_repeated_request: README/tests.md/contract.md lack core's exact sentence ("... so repeats cannot use up the 5 automatic tries").
- every_old_test_count: docs/limits.md line 66 ("2462 + 2 = 2464 tests") has no "earlier commit" marker; the "on an earlier commit, not named here" phrase is also missing.
- two load_tools tests: fail only because I did not add core's load_tools/README.md hunk to that copy (expected; not a claims-tree defect).
- 3 errors (the q, qq and count-sentence tests): `No module named 'yaml'` in my minimal scratch venv, an environment gap, not evidence about the code. Whether the count 3995/97 holds on the claims tree was NOT measured.
So the test only becomes green if the doc sentences it pins are ported to the series' wording as well; and two of its pinned sentences ("cannot use up the 5 tries", "on an earlier commit, not named here") contradict deliberate series wording.

## 5. Recommended merge order (for the lead; nothing done)
1. Take as-is on the claims tree: crash_desk.py docstring, both workflow lines (together with the test), load_tools/README recipe (after one real run of it).
2. Port by hand, re-based on series text, wording softened to the series' evidence: README hunks 1-5, contract.md hunk, tests.md hunks 1 and 3, hubspot-probe hunk, env.example clause.
3. Drop: versions.md hunk, limits.md hunk (series already has the fact), README hunk 6 and 7, tests.md hunk 2, the typed-host parts of real-services/settings (document core code that is not in the claims tree).
4. New test: apply only after step 2, with the pinned phrases edited to match the series, and the count sentence set to the number measured on the claims tree.
5. Ask core for the real base commit (the blobs 08d0722, 71bfc5b, 9fcff6d, f453632 are unknown here) and for the code commit behind the typed-host question, `precheck.py`, `--assume-yes` in run_live_check.

## 6. Not checked
- Full test suite, `python -m pytest --collect-only` counts (3995 / 97), ruff, bandit: not run.
- load_tools recipe: not executed. Windows forms: not run.
- Whether core's claim "`run_real_check.py` sets DESK_SEND_TIMEOUT_SECONDS=8" matches the claims code.
- Core's own tree was not available; statements about its code come only from the patch text and context lines.
- The 9 realhead clones other than f3c39cf were only scanned for apply results, not read.
