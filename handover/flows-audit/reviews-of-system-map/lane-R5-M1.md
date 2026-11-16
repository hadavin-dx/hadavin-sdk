# R5-M1 (egm-codebase-details, sonnet): Major sample, SWEEP.md lines 61-200
Saved by the lead 2026-11-16 ~08:00 UTC, condensed (every row kept, notes shortened). Scope: 140 Major rows in lines 61-200; sample = every 2nd (odd file lines 61-199) = 70 rows. Structural finding: the 12 sampled L3-FD rows (002,007,009,011,013,015,021,023,031,036,038,041) have no claim sentence, only quotes: quotes confirmed on the cited lines but "supported" cannot be judged; a Major with no stated claim is itself a defect (L3-FD-040 admits "claim sentence missing"). Rubric used: leftover copies, internal count slips and rig-only items = Nit.
Counts: CONFIRMED in full or on cites 62; WRONG or partly wrong 4 (L1-FD-025, L3c-FD-007, L3c-FD-018, L4-FD-011); overstated/weak 6 (L1-FD-010, L1-FD-032, L2c-FD-002, L2c-FD-008, L2-FD-016, L3c-FD-005); UNVERIFIABLE parts: L2-FD-019 (HubSpot), L3c-FD-030 (n8n), L3c-FD-037 and L1-FD-032 (take repo). Severity AGREE on 31 rows; DISAGREE on 39 (27 should be Nit, 12 are the claimless L3-FD rows). Possible Blocker: L3-FD-011 if docs/settings.md is published; L2-FD-019 if real HubSpot merges on e-mail.
| id | verdict | sev | note (evidence read under handover/demo or demo3 unless full path) |
|---|---|---|---|
| L1-FD-001 | CONFIRMED | AGREE | CORE-TO-DEMO:85-97 JSON-lines ledger + lock at :92, "keep the demo ledger" :97; DECISION exception is stage.journal only; take-mode code "not in the public repo" (:92) so UNVERIFIED right |
| L1-FD-003 | CONFIRMED (cites only) | Nit | patch:1567, pr4-body:5; "about 600 KB" unbacked; L1c-FD-007 says 519 KB; leftovers |
| L1-FD-005 | CONFIRMED | AGREE | APPLY-LIST:1,13,18,20,102 header 20:38Z vs STATUS 02:08Z; two items numbered 6; "Batch 2 not produced later applied" part weak |
| L1-FD-007 | CONFIRMED | Nit | ORDERS:5,14,160,246 times out of order; log untidiness |
| L1-FD-010 | PARTIAL, overstated | Nit | DRIFT-REPORT-1:34 says "BOTH FINE" (one added test file); INT-1 later gives 2349/116 and 2400; "not reconciled" overstates |
| L1-FD-012 | CONFIRMED | AGREE | REPORT:1839 seven restarts, :2836 oom_kill 0 failcnt 0; no cause written |
| L1-FD-014 | CONFIRMED | Nit | evidence-phase4:4,5 "NOT root-caused", load sample EMPTY; no lead/mail path |
| L1-FD-017 | CONFIRMED | Nit | egm_model_patch.py:25, egm_setup.sh:33 duplicate helper |
| L1-FD-020 | CONFIRMED | Nit | CLOUD-EGM-SETUP:1,3 addressed to a retired session id; stale file |
| L1-FD-022 | CONFIRMED | AGREE | ORDERS:265-278,333-335 breach class stays open in public code; real-run patches not pushed |
| L1-FD-025 | PARTLY WRONG | AGREE | ORDERS:164 raises CI install question; cited :165 is the wrong line ("Branch protection NONE"); "45 to 116 never run on GitHub" mixes 45 (Windows laptop skip) with 116 (Linux no-Playwright) |
| L1-FD-032 | CONFIRMED but overstated | AGREE | DECISION:6-14: mf_leads itself was proven (WP6 smoke P11 :7); unproven = app schema, three roles, saved history; row blurs this |
| L1-FD-038 | CONFIRMED | AGREE | VERIFY:66-69,126-133; "box gone after session" is inference |
| L1c-FD-003 | CONFIRMED | Nit | CHECKLIST:58,111,226,258, AB-PAPER:39 same text under different comment ids; 213-2x53-11=96 consistent |
| L1c-FD-005 | CONFIRMED | Nit | 4 followup reviews; patch:1567; 190 KB unchecked; DO-NOT-USE already named |
| L1c-FD-007 | CONFIRMED | Nit | pr2-v5:13, pr4-A:4, VERIFY:120; sizes unchecked |
| L1c-FD-009 | CONFIRMED | AGREE | semgrep-pr-body-v6:7,13,44-47: scan not repeated on db54e13; v9 text honest and dated: published claim not false |
| L1c-FD-011 | CONFIRMED | AGREE | semgrep-pr-body-v6:47,52,53 licence "not downloaded or read"; owner yes recorded |
| L1c-FD-014 | CONFIRMED | AGREE | evidence-ab-workflows:152, RUNBOOK:92, xdist patch:21; "private pytest field" part unchecked |
| L1c-FD-016 | CONFIRMED | AGREE | REVIEW-MAP-PR4:50 waits 10/60/180/420, counter in memory only; desk out of take; "DECISION line 7" loosely a retry owner |
| L1c-FD-018 | CONFIRMED | AGREE | REVIEW-nodemo-v5-fresh:3,9,16 NOT CLEAN 0B/2M/5m, 280 of 1228; patch not visible: UNVERIFIABLE whether fixed |
| L1c-FD-020 | CONFIRMED | AGREE | hygiene-v3.patch:65,151 four added noqa; CORE-TO-DEMO:117 says 116 vs 117 hits :64 small mismatch |
| L1c-FD-025 | CONFIRMED | Nit | CORE-TO-DEMO:86,115-122 pending owner decision; "seven gaps, four recommended" unchecked |
| L2-FD-004 | CONFIRMED | AGREE | mf-form.json:7, mf-hook.json:7, harness:26, mf_leads.sql:5 same lead_key key space (submission_id vs message_id), no source column; collision could drop a lead |
| L2-FD-006 | CONFIRMED | Nit | mf-sub-crm-mail.json:326-358,693-736 both outputs go to OutUnknown: dead node |
| L2-FD-010 | CONFIRMED | Nit | V4-README:10; mf.py not in tree: helper for not-run design |
| L2-FD-012 | CONFIRMED | AGREE | run_b/f/h/k/l/m/n/p.sh lines b:5 f:4 h:5 k:5 l:5 m:5 n:5 p:6, none bounded |
| L2-FD-014 | CONFIRMED | AGREE | REPORT:11,48, make_results.py:31, make_results_v.py:7: GO-1 and control runs left out of RESULTS.md; "20 of 126" unchecked |
| L2-FD-016 | CONFIRMED, weak | AGREE | run_b.sh:10 three t14 specs; RESULTS:37 one run (ft14n); not shown that ft14a-c ran |
| L2-FD-019 | CONFIRMED for the fake | AGREE | mf-form.json:97, fakes.py:103, harness:161: "lead id OR e-mail" match is in the FAKE CRM; real HubSpot UNVERIFIABLE; if it merges, two leads = one CRM row (lead loss, Blocker) |
| L2-FD-021 | CONFIRMED | Nit | FREEZE:27 "was NOT run": process gap |
| L2c-FD-002 | CONFIRMED but overstated | Nit | register:195,290; cited rule is the core repo's commit gate vs the take rig "CI only": two repos |
| L2c-FD-004 | CONFIRMED (cites) | AGREE | register:4,9,222,357,399; counts (150, 167, about 20 open) not recomputed |
| L2c-FD-006 | CONFIRMED | Nit | register:43,102,342 hygiene |
| L2c-FD-008 | CONFIRMED, slightly overstated | Nit | register:14,209,220,225; :209 gives an environment reason; only :220 "not reconciled" |
| L2c-FD-010 | CONFIRMED | Nit | register:400,401 n8n 2.46.6; DB_TYPE/DB_POSTGRESDB appear nowhere under demo3; row says not the take |
| L2c-FD-012 | CONFIRMED | AGREE | register:323,326,332; log-secret question marked UNVERIFIED by the row |
| L3-FD-002 | quotes CONFIRMED, no claim | DISAGREE (no claim) | f7-rerun md: three reruns exist; duplication claim not stated |
| L3-FD-007 | quotes CONFIRMED, no claim | DISAGREE (no claim) | crosscheck-demo-numbers:3,10, claims-stack-tests:2 |
| L3-FD-009 | quotes CONFIRMED, no claim | DISAGREE (no claim) | crosscheck:9: doc's "-q prints per-file lines" is wrong, numbers right |
| L3-FD-011 | quotes CONFIRMED, no claim | AGREE (maybe Blocker) | cold-reader-settings-portal:11,12: docs/settings.md says a bad value stops the start; desk starts with DESK_BIND garbage = false doc sentence; Blocker if published |
| L3-FD-013 | quotes CONFIRMED | AGREE | trace-b90:28,36, sql-review.out:6, REPORT:18: at-least-once alert (duplicate possible), "fix not applied" |
| L3-FD-015 | quotes CONFIRMED, no claim | Nit | q2-run.sh:4, q4_driver.sh:4, q8_mutate.py:3 hard-coded /home/user/work paths |
| L3-FD-021 | quotes CONFIRMED, no claim | Nit | paused-b21:3, b22:1,8, b23:4 paused rounds |
| L3-FD-023 | quotes CONFIRMED, no claim | Nit | fix-10-r6-notes:38, checkpoint-b17:8 run hygiene |
| L3-FD-031 | quotes CONFIRMED, no claim | Nit | checkpoint-b17:4, note.sh:3: one progress log written two ways |
| L3-FD-036 | quotes CONFIRMED, no claim | DISAGREE (no claim) | crosscheck:47, trace-b90:9 retry timing in two files |
| L3-FD-038 | quotes CONFIRMED, no claim | Nit | identity-fuzz:3 nothing says what is duplicated |
| L3-FD-041 | quotes CONFIRMED, no claim | Nit | 4 design reviews :1/:2 all show 0 Blockers |
| L3c-FD-003 | CONFIRMED | AGREE | e8-fix-6:5, cold-reader-realservices:8, xdist-proof:28, skipped-on-purpose:36, unskip-gitleaks:12 different skip splits for same skips |
| L3c-FD-005 | CONFIRMED (cites) | AGREE | hang-hunt:8, suite-pr14:4; "no report compared them" absence claim unchecked |
| L3c-FD-007 | PARTLY WRONG | Nit | cited lines show fix-5 majors 2, 1B+2, 4, 3: does not "rise"; row's 6 and 7 may be sums not shown |
| L3c-FD-009 | CONFIRMED | Nit | resolve-fix-2-r12:6,8 effort on retired desk |
| L3c-FD-011 | CONFIRMED | AGREE | paused-b22:14,39, paused-b23:5, checkpoint-b23:27, resolve-fix-10-r6:2; round 7 after stop order not provable |
| L3c-FD-014 | CONFIRMED | AGREE | resolve-fix-2-r11:1, review-fix-2-r11:6, fix-10-r5:27, fix-5-r9:1; reviewer rules deferral "not allowed" |
| L3c-FD-016 | CONFIRMED | AGREE | load-claims:19,20; measure_burst/LOAD_RETRY 0 hits in resolve/review md; "fails 3 of 3" not on cited lines |
| L3c-FD-018 | WRONG (overstated) | Nit | cold-reader-n8n:63, realservices:8, needed-check-1:22, skipped-on-purpose:3: numbers belong to different heads (2513 "on 2ce1f98"; 3683 later main) |
| L3c-FD-020 | CONFIRMED | AGREE | resolve-fix-10-r3:11, r4:8, r5:7, needed-check-1:17 |
| L3c-FD-022 | CONFIRMED | Nit | reader-xdist-flake:40, resolve-fix-5-2-r1:4 unused work |
| L3c-FD-024 | CONFIRMED | Nit | reader-pr12-e-marks:8,24 run already ruled INVALID |
| L3c-FD-028 | CONFIRMED | Nit | resolve-fix-5-r7:6, checkpoint-b21:40, checkpoint-b23:25 wasted runs; "no single script" unchecked |
| L3c-FD-030 | CONFIRMED | AGREE | cold-reader-n8n-limits:6, DECISION:15 recipe 8765/8766/5679; not run in real n8n UNVERIFIABLE |
| L3c-FD-032 | CONFIRMED (cites) | Nit | resolve-round1-fix-2:36, resolve-fix-2-r12:15; absence claim unchecked |
| L3c-FD-037 | CONFIRMED | AGREE | realservices:41, settings-portal:171 untested items; real HubSpot/mail/n8n UNVERIFIABLE |
| L4-FD-002 | CONFIRMED | Nit | outsider:5, outsider2:7, layout:6, fixes/PLAN:2 duplicate reports of same PIL failure |
| L4-FD-004 | CONFIRMED | Nit | DRY-RUN-CHECKS:4,40 224 vs 124+22+38+8+34 = 226; row says real impact low |
| L4-FD-007 | CONFIRMED (cites) | Nit | fixes/PLAN:2, CRLF-GUARD-V7-NOTES:3, real-run/FIXES:19; patch counts unchecked |
| L4-FD-009 | CONFIRMED (cite) | Nit | layout/SUMMARY2:7; more than 100 PNGs, no count |
| L4-FD-011 | WRONG (overstated) | Nit | INT-1:11, SCAN-TABLE:14, ORDERS:348: "no file says which head is current" is false (ORDERS:348 PR #4 merged as 61ded9eb on main; the sweep cites it in L1-FD-004) |
| L4-FD-013 | CONFIRMED, severity wrong | Nit | SCAN-TABLE:10,11, gitleaks/SUMMARY:8: finding is sonar-project.properties line 4 "the projectKey line"; 325 history findings (long-hex-token 313, hardcoded-hostname 10, generic-api-key 2); a projectKey is not a secret: scanner false positive |
| L4-FD-015 | CONFIRMED | AGREE | DRY-RUN-CHECKS:23-32 D1 to D6 real; key file not checked at start, final note misleads after "y" |
Not checked (reviewer): absence claims ("no file says", "no resolve mentions", "no answer recorded" for L1-FD-025; only measure_burst, LOAD_RETRY, __fspath__ grepped); aggregate sizes and counts (600 KB, 190 KB, 519 KB, 378 PNGs, "10 of 12 identical nodes" (lead re-checked: TRUE, 10 of 12 have identical parameters), "20 of 126", 150 and 167 line counts, patch counts); even-line rows (unsampled); cited lines not read in context (SKIP-TABLE:84, REPORT:1547/1550/1756, hostile-f7-rerun.md:1, archive:1 header, reader-e3b:14); take repo, n8n, HubSpot, SMTP.
