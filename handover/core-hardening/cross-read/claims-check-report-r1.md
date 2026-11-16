# Claims check r1: REPORT.md top block (11:10Z) and STATUS-BOARD.md against the files they cite

Read-only (ls, grep, wc, head, sed, df, ps, date). Nothing run, nothing edited except this file. Checked 2026-11-16 at about 11:16 UTC (system clock, `date -u`). Paths below are relative to handover/core-hardening/.

## FAILURES FIRST (claim, where, what the file says)

1. STATUS-BOARD ITEMS_OPEN: 7 (line 8) with ITEMS_TOTAL 11.
   The table has 14 rows (C1, C2, C3, C3b, C4, C4b, C5, C6, C7, C8, C9, C10, C11, edit list v10). 9 are below 100 percent (C3b, C4b, C6, C7, C8, C9, C10, C11, edit list v10); only C1 to C5 other than C3b are 100. Neither 11 nor 7 matches the table. PERCENT 95 does match the table mean (about 94.5, my arithmetic).

2. STATUS-BOARD ORDER line (line 4) cites "027, 028" with UPDATED_UTC 11:15:13Z.
   ORDERS.md:158 stamps ORDER 027 "11:22Z" and ORDERS.md:161 stamps ORDER 028 "11:31Z". Both are later than the board stamp and later than the real clock (11:16 UTC at check time). ORDERS.md was last written 11:08:36 (`ls -l`). ORDERS.md:156 itself says "Your board UPDATED_UTC is in the future". So the lead's order times are not real clock times, or the board cites orders that did not exist at 11:15. One of the two is wrong. Not resolvable from files.

3. STATUS-BOARD C8 row: "run.py r3 reviewed: 2 majors (-p no:NAME, hard links)".
   mutation-lane/review-runpy4-security.md:3-4 has Major A (-p no:NAME) and Major B (hard links). mutation-lane/review-runpy4-evidence.md:3-4 adds two more majors: Major 1 (new-test proof weaker than the table: T29 flag check passes on r2 code, timeout branch uncovered, T34/T30b fail on R1 code only because of an unknown flag) and Major 2 (S603 cannot be cleared without a suppression). So the two reviews together hold 4 majors, not 2. The board and REPORT item 4 name only the two security majors.

4. REPORT item 4: "2 ruff S603 findings unsuppressed (lead decides)".
   The count is right (mutation-lane/handback-runpy4.md:3, review-runpy4-evidence.md:2: run.py:219 and :578). But REPORT-runpy3.md:12 says "no precedent in the repo" for a noqa, while review-runpy4-evidence.md:4 says "repo precedent exists". The two files contradict each other; I did not check src/.

5. REPORT item 6: "port 5690 labelled 'take' in repin patches (decision 6)".
   cross-read/contradiction-sweep-r1.md:9 (F3) cites inputs/plan-wp6-resmoke-v5.md:121 ("take n8n 5690"), not the repin patches. The repin patch paste-check/plan-v5-repin-v6.patch:81 does carry the same line as context, so the claim is partly supported, but the cited source is the input plan.

6. REPORT uses "decision 6" for two different things.
   "Claim wording A or B (decision 6)" (For the lead to decide) = "LEAD DECISION 6" in paste-check/plan-v10-real-v5-edits.md:457. "port 5690 ... (decision 6)" (item 6) = inputs/DECISIONS-2026-11-16.md:7 item 6, which is Ports. Same label, two meanings. The wording-clarity rule asks for one word, one meaning.

7. REPORT item 1: "v14 builder still running; no review of v14 yet" and STATUS-BOARD C4b/FAILED (1).
   REPORT.md was last written 11:07:05 (yet its heading says 11:10Z, three minutes ahead of the file time). The v14 reviews are dated 11:09:59 to 11:12:19 (citation-check-v14.md, review-v14-security.md, review-v14-stranger.md, adversarial-v14.md, contradiction-v14.md). So the REPORT line was true when written and is now out of date. The board's later line is the current one.

8. STATUS-BOARD C3b row: "v8 round 6: 0 blockers".
   paste-check/review-c3b-v8-r6.md:3 lists one Major (closing fence and prose on one line, fixed in place by the lead). "0 blockers" is true; "0 majors" is not claimed, but the board does not mention that a Major was found. The row's evidence column cites older files (handback-c3b-v7.md, review-c3b-v6-readiness-r4.md), not review-c3b-v8-r6.md.

9. STATUS-BOARD C4b evidence cites steps-edits/review-v13-stranger.md, review-v13-security.md and citation-check-v13.md, but the row text is about v14. The v14 files exist (review-v14-stranger.md, review-v14-security.md, citation-check-v14.md) and carry the numbers in the row.

10. STATUS-BOARD CAPACITY: "disk ... (77% used)".
   `df -h /` at check time says 78% (30G used, 8.9G avail of 252G). Load 0.1 (board) vs 0.56 (uptime now); these move with time, so only the disk percent is a (small) mismatch.

11. REPORT Housekeeping: "Zombie postgres pid 5074 is not mine".
   At check time `ps -p 5074` shows no such process and `ps aux` shows 0 postgres processes. The claim may have been true earlier; it is not true now. "/syntax-check-output.txt (root-owned, outside repo)": confirmed present, root owned, 356 bytes, dated 10:43.

12. STATUS-BOARD agent table: cannot be checked from files (see not checked).

## CLAIMS THAT HOLD (file:line)

Top block, item 1 (owner sheet):
- v13 stranger "8 major": steps-edits/review-v13-stranger.md:2 ("8 new majors"). Holds.
- v13 security "7 majors": steps-edits/review-v13-security.md:2 ("0 blockers, 7 majors, 9 minors"). Holds.
- v13 citation "5 minors": steps-edits/citation-check-v13.md:3 ("0 Blockers, 0 Majors, 5 Minors"). Holds.
- v13 adversarial "20": cross-read/adversarial-v13.md has numbered items 1 to 20. Holds.
- "about 20 values only the lead has are blank (L1-L20)": steps-edits/v13-OPEN-FOR-LEAD.md rows L1 to L20 (lines 7-26). Holds. (v14-OPEN-FOR-LEAD.md adds L21 and L22.)
- Worst findings: Emergency cancel spares the run key (review-v13-security.md:3 major 1), key page shows the key once (major 2), no procedure for other secrets (major 3), run total not a worst case (major 5). Hold.
- Board v14 numbers: security 9 majors (review-v14-security.md:2), stranger blocker plus 17 majors (review-v14-stranger.md:3-5, 17 numbered majors), adversarial 43 (adversarial-v14.md items to 43), contradiction 12 (contradiction-v14.md items to 12), citation 6 minors (citation-check-v14.md:6). Hold. "blanks B1-B13" is in v14-OPEN-FOR-LEAD.md:3. Holds.

Item 2 (C7b): patches-ready/review/design-c7b-fix4-r5.md:2 "0 blockers, 0 majors", :5 "Recommendation: accept"; :4 patch nit at :124-126 and the Remove-EC2_x / Remove-S32 gap; patches-ready/review/codebase-c7b-fix3-r4.md:4 says the patch test passes on old code too. The bare Remove-EC2 / Remove-EC2* gate gap is in patches-ready/README.md:67 and v6-extra/DESCRIBE-ONLY-flaky-id-test.md:8, labelled "may not match", "unchecked" (the REPORT states it as a gap; the source says possible and unchecked). Q16 is cited as the describe-only reason: yes, README.md:67 and the DESCRIBE-ONLY file.

Item 3 (C3b): review-c3b-v6-facts-r4.md:2 "Blockers none. Majors none"; review-c3b-v7-readiness-r5.md:2 "0 blockers, 2 majors", R5-M1 (A9 never flips LEAD-FILL 9) and R5-M2 (C2b stand-in pid note "as in C9"). Hold. v8 small-fix hand-back exists (handback-c3b-v8.md).

Item 4 (run.py): mutation-lane/REPORT-runpy4.md:16 and :41 and raw/run-py-safety-tests-r3-new-final.txt (126 PASS lines, one "FAILED CHECKS 0" line) and raw/run-py-safety-tests-r3-r2-code.txt (94 PASS lines; 33 FAIL lines, 32 failures plus a summary line). 126 PASS, 0 fail and 94/32 hold. Minors listed in handback-runpy4.md:3 (SIGQUIT/ALRM/USR1/USR2/XCPU, marker after Popen, --restore needs git, .tmp-* after SIGKILL): all four hold.

Item 5 (edit list v10): paste-check/review-v10-r6.md:2-3 "No blockers, no majors", "Nits" (two: three-clause lease sentence, heading). Holds. paste-check/review-v10-flowfacts.md:2 "INCOMPLETE ... no git show" and two wording majors, same file lines 4-5. Hold. The file now also carries an "UPDATE 11:20Z" section that says the primary-source check is done (paste-check/evidence-v10-primary.md, written 11:15:28); the file's own time label (11:20Z) is later than its write time (11:15:48), the same clock skew as failure 2.

Item 6 (sweeps): contradiction-sweep-r1-summary.md:2 (F1 9514 on tree with A-01 and C-01; F2 DECISION-one-store.md:14 "ONE database"; F3; F6 probe contact on no deletion list) and :3 ("13 sends", head de6b574 unbacked). inputs/DECISION-one-store.md:14 does say "ONE database for everything we own". The lease figures 45/20/120 s: one-place-sweep-r1.md:11-14. Five lease wordings: one-place-sweep-r1.md:5-10 lists five (headline says "Four", fifth added at :9). Hold.

"For the lead to decide": exit-code rule case C (L4), backstop 180 or 189 (L18), run-card values (L5), Q20/Q21 items, retake count (L17), Remove-EC2 gap, S603: all appear in files above. Lease sentence approval (L11, v13-OPEN-FOR-LEAD.md:17). Hold.

Patches README: patches-ready/README.md:49, :52, :53 give 9418 (v5 final), 9514 (v3 plus C7b fix), 9391 (pristine base) with the same raw log cites. Hold. "Unreviewed": no review file for README.md other than patches-ready/review/citation-check-readme.md (which found a cite off by one, line 7), so "line cites may be off by 1-2" is itself supported.

Board other rows: C5 "v5 done, no blocker or major": review/design-r5-c5v5.md:2. C7 row: same file as item 2. C6 row: c6-skip-audit/REPORT-c6f.md exists. All cited evidence files exist (see below). Capacity: 4 cores (`nproc`), 15 GB RAM (`free -g`), disk 252G with 8.9G free (matches "8.9 GB free of 252 GB").

Files named in the two blocks: all exist except the file I was asked to write. Checked: v13-OPEN-FOR-LEAD.md, patches-ready/README.md, review-v10-flowfacts.md, DESCRIBE-ONLY-flaky-id-test.md, DECISION-one-store.md, NOT-CHECKED-lane-c-r2.md, handback-c3b-v7.md, review-c3b-v6-readiness-r4.md, review-v13-stranger/security, citation-check-v13, design-r5-c5v5.md, REPORT-c6f.md, design-c7b-fix4-r5.md, REPORT-runpy3.md, review-v10-r6.md, paste-check/REPORT.md, EDITS.md, reviews-of-flows-audit/REVIEW.md, hygiene-patches/, review-contradictions-r1.md, ORDERS.md, QUESTIONS.md.

Sha prefixes: only de6b574 (real head, never tested) appears in the top block. It is named, not tested, in patches-ready/README.md:8 and design-c7b-fix4-r5.md:4. Holds as "never run". No other sha prefix in the top block or the board.

## NOT CHECKED

- AGENTS_RUNNING 5 and the agent ids, start and end times: no agent list is available to me; the three "(new)" agents cannot be matched to files (cross-read/claims-check-report-r1.md is this file).
- Test counts (126 PASS, 94/32, 9418, 9514, 9391, 455): checked only against the files that cite them and the raw log line counts for the run.py runs. I did not open the raw pytest logs (full-suite files) and did not recompute any hash (sha256sum not run).
- All "X majors" counts for reviews other than the ones listed above, and the 10:50Z and older REPORT blocks (the task named the 11:10Z block only; I read the older blocks only for context).
- Whether patches apply, whether n8n, Postgres, PowerShell, WSL behave as claimed: nothing run. The Remove-EC2 gate gap, the lease behaviour and the 45 s figure are repeated from reviews; I did not open src/ or the real-v5 flows (evidence-v10-primary.md was only noted, not read).
- Line cites such as :124-126, :219, :578, mf-form.json:97: not re-opened in the target files.
- ORDER wording inside ORDERS.md beyond lines 118-162; DECISIONS items other than 1 to 12 titles.
- The board's CAPACITY numbers for load and memory: they change by the minute; only disk and core count were compared.

## Lead response 11:22Z
Fixed in REPORT.md top block: v14 review status (item 1), run.py major count 4 and noqa precedent (item 4), decision-6 double meaning (item 6). Board next beat: ITEMS_OPEN 9, C3b row mentions the round 6 major fixed in place, C4b evidence column to v14 files, disk 78%. Order stamps 11:22Z/11:31Z are the lead's clock (ORDERS.md itself says my board stamp is "in the future"); my board stamps use the real container clock; not an error of mine. Port item 5: repin patch carries the line as context (plan-v5-repin-v6.patch:81); wording kept as "labelled take in the plan and carried in the patch".
