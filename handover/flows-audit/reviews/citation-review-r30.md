# Citation review r30 of `reviews-of-core-patches/REVIEW.md`

Checker: citation checker (static; grep, sed, wc, `git show`/`git archive`, `git apply --check` on scratch copies, small read-only Python scripts). Date 2026-11-16. Nothing was edited except this report.
File checked: `handover/flows-audit/reviews-of-core-patches/REVIEW.md` (636 lines, 475,873 bytes; repository HEAD during this check was `215b92356`).

## Honest limits first (what I did NOT check)
- The file has 796 `file:line` cite occurrences (about 460 distinct). I did not read every one by hand. Method: a script resolved each cite to the checkout (`src`, `tests`, `demos`) and to a `git archive b4cce5b` copy, confirmed the line number exists, and compared the identifiers the sentence names (in backticks) with the cited lines. 593 occurrences matched on identifiers. The roughly 200 that did not match were all read by hand (batch printouts of cite, sentence, source line). All 203 resolved to a file and a valid line range except the 3 listed as CANNOT-CHECK. A match of an identifier is weaker than a full semantic check: where a cite matched a name but the sentence makes a deeper claim (what a Postgres right allows, what runs at run time), I did not test that claim.
- Everything about `/tmp/core-b4p`, `/tmp/core-b4m`, `/tmp/ch`, `/tmp/smfull` is CANNOT-CHECK: `/tmp/core-b4p` holds only `pyproject.toml` today, `/tmp/ch` holds only `handover`, the others are gone. I used the durable copies in `patch-copies/` instead (applied to a `git archive b4cce5b` copy).
- `G5-wording.patch` is not in the repository (the file says so), so its line cites (lines 5, 40) are CANNOT-CHECK.
- No Postgres or test behaviour was run (the file marks those UNVERIFIED itself).

## Counts: stated consistently? (28 rows; Major 4 / Minor 13 / Nit 11; PROPOSE FIX 25 / DECLINE 3; 33 answers; Major parts 10)
Script `count_review.py` run on the file (raw last lines): `rows 28`, `severity {'Nit': 11, 'Minor': 13, 'Major': 4}`, `decision {'DECLINE': 3, 'PROPOSE FIX': 25}`. Row ids: C-1..C-8, A-1..A-9, G-1..G-2, D-1..D-3, X-1..X-6 = 28. DECLINE rows are C-1, C-5, A-9 (matches line 308). Minor list at line 308 (A-1..A-6, C-3, C-7, C-8, G-1, X-1, X-3, D-3 = 13) and Nit list (C-1, C-2, C-4, C-5, C-6, A-7, A-8, A-9, G-2, D-1, D-2 = 11) match the table severities.

| cite | claim | what the file says | result |
|---|---|---|---|
| L2, L39, L74, L308, L496, L571, L596, L604 | 28 rows; Major 4 / Minor 13 / Nit 11 | same numbers everywhere (outside History) | OK |
| L74, L308, L604 | PROPOSE FIX 25 / DECLINE 3 | 25 / 3; script agrees | OK |
| L75, L113, L330, L335 | 33 answers = 29 numbered decisions + 9b + 23b + 5-K + Q1 | L75 and L330 write 29+2+1+1; L113 writes 27+4+2; both give 33. Decision table rows 339-371 are exactly 33 rows (1-8, 9a, 9b, 10-22, 23a, 23b, 24-29, Q1, 5-K). Decision headings 1-29 exist (lines 378-409) | OK |
| L38, L40-41, L200-201 | Major parts 10 (X-5: 4, X-6: 6), 12 items = 10 + X-4 + X-2 | X-5.1, 5.2, 5.3, 5.7 Major; X-5.4, 5.5 Minor; 5.6 unrated. X-6.1-6.4, 6.6, 6.8 Major; 6.5, 6.7, 6.9 Minor. Part ids X-5.1..5.7 and X-6.1..6.9 all exist (L200 says seven and nine parts) | OK |
| L42-44, L399 | Decision 20 option counts: option 2 = 3/14/11, option 3 = 6/11/11, option 4 (T2) = 5/12/11, option 6 = 6/11/11 | arithmetic from 4/13/11 is right in every option | OK |
| L30 | "nine serious defects exist in today's code" (Blocker, PLAIN VERSION) | the same sentence block and L40-41, L74, L308, L399 say 10 present Blocker-equivalent parts (4 + 6). The L30 headline later in the same line says 10. | MISMATCH (nine vs 10) |
| L596, L605, L618-L622 | older counts (27 rows, Major 7 to 5, "of the 5 Majors") | these sit in History and are labelled as the numbers of their round; the arithmetic in L596 (9+2+1 = 12 Minor, 7-2 = 5 Major, 24+1 = 25 PROPOSE FIX) is right | OK |
| L24 | History keeps old numbers ("29 answers", "25 numbered decisions") | those two numbers occur only inside that sentence and in History; L494 "20 numbered decisions" and L619 are round-labelled | OK |
| L416-424 | nine exit criteria | rows 1-9 exist; criteria cited anywhere are 1-9; (3,4,5,7) note-only, (8) in part, (1),(2),(6),(9) not: 4+1+4 = 9 | OK |
| all | Decision numbers cited | every "Decision N" is 1-29; every C/A/G/D/X id cited exists; Q1 exists; no dangling pointer found | OK |

## Source and git cites (selected; every group below was read)
| cite | claim | what the file says | result |
|---|---|---|---|
| L127 / `git` | shallow clone; boundary commit `fda633bb` | `rev-parse --is-shallow-repository` = true; `.git/shallow` = `fda633bbb3fc...` | OK |
| L127 | `b4cce5b` and `176a0cbe0` are commits; b4cce5b not an ancestor of HEAD or of 176a0cbe0 | `cat-file -t` = commit twice; both `merge-base --is-ancestor b4cce5b ...` exit 1 | OK |
| L127 | `176a0cbe0` is an ancestor of HEAD; `src` and `tests` at HEAD equal it | exit 0; `git diff --stat 176a0cbe0 HEAD -- src tests` prints nothing | OK |
| L125 | `git diff --quiet 176a0cbe0 -- src tests pyproject.toml` rc 0 | rc 0 today | OK |
| L127 | "no reflog entry names `b4cce5b` (count 0)" | today `git reflog \| grep -c b4cce5b` = 1: one reflog line whose commit MESSAGE mentions b4cce5b (HEAD@{62}); no reflog entry points at that commit. The statement was true at its run time and is still true of refs | OK (note: the raw count is now 1) |
| L127 | HEAD at run time `76c01f662`; stale ids `0d88ad99c`, `07fef531b`, `1be1b541e` | all exist as commits; `evidence-14-provenance.md` shows HEAD `76c01f662fcd...` | OK |
| L403, L473 | commit `34540bfa2` is on branch `cloud/flows-audit` and holds the G5 copy | exists; subject "flows-audit: WIP reports r16"; contained in `cloud/flows-audit` and `origin/cloud/flows-audit` (I did not check that it holds the G5 file) | OK (partly) |
| L125 | `config.py:393` `refused = []`, `:64` class Route, `:68` max_tokens, `:401` raise, `:394-396` `is_live`/`DEMO_ONLY` (checkout) | all exact | OK |
| L125 | b4cce5b unpatched: `config.py:365` `refused = []`, `Route.max_tokens :59`; uses `self.environment != "dev"` and `DEV_ONLY` | exact (`!= "dev"` at 366, `DEV_ONLY` at 19 and 368) | OK |
| L125, L150 | patched b4cce5b tree: price check `config.py:365-373`, raise `:373`, `refused = []` `:374`, environment raise `:382`; `defaults.py:104` `MAX_ROUTE_TOKENS` | applying the durable `patch-copies/C-01.patch` to b4cce5b gives check 365-374, raise `:374`, `refused = []` `:375`, environment raise `:383`; `defaults.py:104` is right; `config.py:59` also changed. All four config numbers are one lower in the file. The file itself says its patched trees are first-version copies (L140: first-version hunk sizes +53/+74, rebuilt +64/+123), which would explain a missing comment line | MISMATCH against the rebuilt durable copy by 1 line (cannot confirm against the gone first-version tree: CANNOT-CHECK for that) |
| L1/L153 | `C-01.patch` hunk 2 lines 14-30, raise at line 27; for-loop lines 18-26 | exact (hunk header line 14, raise line 27, `for n, r` line 23) | OK |
| L130, L146 | `C-01.patch:87-93`, `C-01-price-only.patch:66-72` hold the non-finite test | exact | OK |
| L140 | hunk headers `C-01.patch:48` +1,64; `A-01.patch:124` +1,123; `C-01-price-only.patch:27` +1,51 | exact (all three) | OK |
| L158-L162, L190 | `A-01.patch:98` "wait there (or in memory)"; `:102-104` getattr/RuntimeError; lines 12, 25, 60, 72 log lines; `:248-264` tick-test hunk, `:261` assertion; lines 10-16 warning | exact in every case | OK |
| L162, L508 | first-version `A-01.patch` lines 190-205 | first-version file is not kept | CANNOT-CHECK |
| L172 | `G5-wording.patch` lines 5 and 40 carry the old handle | patch not in repository | CANNOT-CHECK |
| L24, L30 etc. | `runtime/tick.py:85` is step `reconcile`; `audit/chain.py:232-246` drain, DELETE at `:244`; `app.py:62` `build`; `store/migrate.py:57`, `:59` grants; `app.py:84-89`, `:146`, `:151-160`; `audit/protocol.py:27` | all exact | OK |
| L240, L242, L627 | `chain.py:290-293` `signed_through`, `:299-300` signer None, `:299-304`, `:310-314` INSERT, `:315-317` except/log, `:187`, `:203-204`, `:529`, `:239`, `:243`, `:244` | all exact | OK |
| L158 | `cli.py:262`, `:268` (`emit_outcome`), `:273`, `:275`; `k1b/replay.py:185` | exact | OK |
| L160-161 | `local_dir.py:121` os.replace, `:126-156` reconcile; the 9 reconcile assertions (`test_cuj.py:202`, `test_audit_chain.py:514/517/677`, `test_s2_audit.py:51`, `test_review_fixes.py:105`, `test_capabilities.py:45/59`, `test_review_pr3_round2.py:321`) | lines hold `reconcile() == n` assertions | OK |
| L148-L152 | cost sinks `llm/common.py:164-171` (166-169), `llm/fake.py:48-54`, `k1b/loop.py:120-121`, `limits.py:17-18`, `k1b/replay.py:85-90`, `:87`, `:88` (`llm_kind != "fake"`), demo `meter.py:48-55`, `config.py:64-69`, `fixtures.py:24-25`, `tests/contracts/kinds/builtin.py:20`, `tests/test_k5_tools.py:720` | all resolve to the named code | OK |
| L153 | `backends/table.py:529-535`, `:71-85` (comment `:73`), `:595` `("llm","fake")` in DEMO_ONLY, `:604` NOT_PROD signer | exact | OK |
| L197-L242 | grant map cites: `migrate.py:46-68`, `:47`, `:50`, `:51`, `:56`, `:57-59`, `:62-66`, `:170-186`, `:179` (`REVOKE ALL`), `:195-199`, `:206-209`, `:219` (`owner == role`), `:285-288`, `:298-303`, `:294-295`; `0002_audit_chain.sql:28-35`; `0003_approvals_tick.sql:25-27` | exact | OK |
| L636 | `store/postgres.py:345`, `:349-352`, `:416-431`, `:433-442`, `:453-458`; `requests.py:95-109`, `:107`, `:126`, `:163`, `:170`, `:196-197`, `:210`; `agent_loop.py:267-278`, `:292`, `:747`, `:762-763`, `:768`, `:783`, `:845-867`, `:886`, `:901`, `:909` | exact | OK |
| L226, L240, L294, L382 | `config.py:419-420` production refuses `signer: none` | `if is_prod(environment): refused += ...` at 419-420 | OK |
| L125, L123, L141 | pydantic pin 2.14.1 at `pyproject.toml:16` (checkout and b4cce5b); `/tmp/core-b4p/pyproject.toml:16` | `pydantic==2.14.1` at line 16 in the b4cce5b copy; the `/tmp` file is gone | OK (b4cce5b) / CANNOT-CHECK (`/tmp`) |
| L137, L139, L140, L599 | `evidence-13.md:13` (22 collection errors, 20 + 2), `:22-24` (old source, 15 failed), `:43-58` (AttributeError MAX_ROUTE_TOKENS), `:63-73` and `:74-87` (list tests), `:99` (mutation c) | exact | OK |
| L141 | `evidence-pydantic-nan.md` PART 1: NaN, Infinity, -Infinity, sNaN rejected; '0' and '-1' accepted; PART 2 load_config only NaN, Infinity, -Infinity | exact | OK |
| L73, L137, L323 | heavy lane: 2 failed, 9389 baseline / 9404 patched; 15 more passes; 70 = 5+10+41+14; `SUMMARY.md:22`, `:31`, `:9` | exact; "Correction 09:45 UTC" heading is at line 30, text line 31 | OK |
| L323 | 41 cases in `test_p7_tick.py` (39 functions + 3-case parametrisation), 14 in `test_gate.py` (8, 4, 1, 1) | 39 test functions; test_gate 4 functions of 8, 4, 1, 1 cases = 14 | OK |
| L125 | `../heavy-test-lane/evidence-guards-after-fix.md:4-14` shows other changed/untracked files | lines 4-14 are a `git status --short` list of untracked files under handover | OK |
| L1-L2, L24 | `inputs/DECISIONS-2026-11-16.md` line 1 text; line 5 = item 4 (A-01 deferred, C-01 extras cut, G5 kept); "RIGHT-SIZE" | exact; "RIGHT-SIZE" is not defined in the files I opened (it is used in `ORDERS.md`, not defined) | OK |
| L2 | `../QUEUE.md` line 12 says "6 Majors, APPLY AFTER FIXES" | exact | OK |
| L3 | times 09:02 UTC / 14:32 IST, 15:48 UTC / 21:18 IST (also L479, L560) | +5:30 is right in all four pairs | OK |
| L492, L614 | `fix-review1..12.md` in this folder except `fix-review7.md` (does not exist); 16-19 in `reviews/` | `fix-review7.md` absent, 1-6 and 8-15 present here; 16-19 and 29 present in `reviews/` | OK |
| quoted strings | 'a local Ollama', 'the gate re-scans with a fresh one', "check the runtime role's grants", 'DELETE only on the outbox and the purged evidence tables', 'kill switch ON', 'the audit tables are missing', 'new tables have no runtime grants', 'one step never stops the others', 'the grants above are made first and this runs in the same transaction, so a problem rolls them back' | each found verbatim in `src` | OK |

## Result
- Checked: counts (all), decision/criteria/X-row pointers (all), 33-answer arithmetic, option arithmetic, git/provenance facts, about 460 distinct source cites (identifier-level for all, read by hand for the roughly 200 that the script could not confirm), patch-copy cites, evidence-file cites, time conversions.
- MISMATCH: 2
  1. L30 (Blocker, PLAIN VERSION): "nine serious defects exist in today's code" while the rest of the file (headline in the same line, L40-41, L74, L308, L399) says 10 present Blocker-equivalent parts (X-5: 4, X-6: 6). Fix: write ten.
  2. L125 and L150 (patched b4cce5b line numbers): price check `config.py:365-373`, raise `:373`, `refused = []` `:374`, environment raise `:382` do not match the durable rebuilt copy (`patch-copies/C-01.patch` applied to b4cce5b gives 365-374, `:374`, `:375`, `:383`). Probably the first-version patch had one comment line fewer; the first-version tree is gone, so the file's numbers cannot be confirmed. Fix: either state "first-version copy" next to these numbers or give the rebuilt-copy numbers (one higher).
- CANNOT-CHECK: `/tmp/core-b4p/pyproject.toml:16` (x2), `/tmp/core-b4p` patched line numbers in general, first-version `A-01.patch` lines 190-205, `G5-wording.patch` lines 5 and 40, `tests/test_c01_route_limits.py:27` (new file inside a patch, checked only through the patch text, not located).
- Note (not a mismatch): L127 "reflog count 0" is now 1 because a commit message mentions b4cce5b; the claim about refs still holds.
- Everything else read: OK.
