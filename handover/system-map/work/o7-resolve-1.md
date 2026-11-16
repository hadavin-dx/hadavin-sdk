Status: resolved (headless, auto accept; fixes applied by the author, not by this skill)

# Goldfish Annotated Review Report, ORDER 007 round 1

**Target:** SWEEP.md and ONE-PLACE-TABLE.md (full files). Findings: work/o7-review-R2-design-r1.md (design), work/o7-review-R1-codebase-r1.md (codebase-details). Merged duplicates: R2 M1 headline + R1 N6 (one fix); R2 M5 row 13 + R1 M2 (one fix); R2 M6 row 16 + R1 N2 (one fix); R2 M6 row 17 + R1 N3 (one fix).

## Majors
### 1. [R1 M1] Counts omit the 8 L7 rows. PROPOSE FIX
Change the table to security 6/22/3/31; unverified 1/55/15/71; raw 17/219/86/322 (322 = 319 rated + 3 merged); dedup 13/216/86/315; scope line "322 raw, 315 deduplicated"; state that the earlier 314 / 307 did not contain L7-FD-001..008. Check REPORT.md count lines.
### 2. [R1 M2 + R2 M5 row 13] Name counts wrong; rewrite instruction would damage evidence. PROPOSE FIX
L1-FD-021, Decisions E and row 13: full name in 2 files (handover/CLOUD-EGM-SETUP-2026-11-12.md:3, handover/demo/ORDERS.md:6); Windows login name in 7 lines of 3 files (demo/ORDERS.md, demo/speed/RUNBOOK-SPEED-3.md, demo/speed/evidence-phase4.md); the public account handle on 72 lines of 5 raw API JSON evidence files is not rewritten. Row 13: no path rename (drop it); responsible laptop lead edits, studio head says yes; verification by grep of the full name and of the path form outside handover/demo/pr-stack/raw-*.json. Replace "owner's name" by "studio head's name" in E and row 13.
### 3. [R1 M3] L6-FD-026 node count. PROPOSE FIX
Seven nodes with continueRegularOutput (six Postgres nodes at lines 43, 119, 141, 223, 247, 283 and the sub-workflow call RunSub at 97); AlertSend line 199 uses continueErrorOutput, wiring NOT traced.
### 4. [R2 M1] Leftover COUNTER contradictions. PROPOSE FIX
L6-J-005 reason: "DUPLICATE of core Limits (both enforce a dollar ceiling); not a duplicate of stage.journal". L3c-FD-009 ending: per-lead model-call guard, dollar cap open (Decisions A). L6-J-034 state: UNVERIFIED (stand-in only), Owner line: "its independence is not yet shown". Delete the fragment "the proof count is the independent count, so no counter question gates this row" from the six desk rows and row 8. Headline: open for the studio head A to E; open for the laptop lead: the watcher and the UNVERIFIED checks.
### 5. [R2 M2] "independent" two meanings, undefined terms. PROPOSE FIX
Add "independent count" and "proof count" to the word lists; L7-FD-007 uses "separate from n8n".
### 6. [R2 M3] Row 2. PROPOSE FIX
Studio head chooses; laptop lead creates the separate model account and sets the limit; verification with limit set to 1 USD and recorded replies; option 2 only after Wed 18 Nov; studio head yes: yes.
### 7. [R2 M4] Decisions not decidable by a non-technical reader. PROPOSE FIX
Add plain-word lines (provider, hard limit, worst-case price, SMTP, heartbeat, cron job, uptime service, rotate, untrack, history rewrite, sha, role, migrations identity, journal count); the 5 USD suggestion becomes "studio head's number; laptop lead writes price per call"; C gets three options; D gets time per option as "estimate, laptop lead fills"; B who-watches de-circularised; rung per option.
### 8. [R2 M5] Rows 5, 6, 7. PROPOSE FIX
Row 5 people; row 6 when-cell "after Wed 18 Nov"; row 7 split into 7a rotate and untrack, 7b decide the rewrite, verification: old key refused, n8n restarts with the new encryption key, git ls-files empty; old values stay in public history so rotation is the real protection.
### 9. [R2 M6 + R1 N2, N3] Rows 8, 15-17. PROPOSE FIX
Row 8 after rows 15-17, rows 18-23 say "apply as in row 8"; row 16: "pending security patches", use the on-disk files, order does not matter per the summaries, L4c-FD-002 not confirmed here; row 17: one action, spend check against the stand-in server, script is in the desk repository (not this checkout).
### 10. [R2 M7] L7 rows have no fix-plan row; L7-FD-005 severity. PROPOSE FIX
L7-FD-005 re-rated Blocker (by the table rule: each post starts a paid model call; the earlier Major was this author's choice, no evidence for it). New fix-plan rows: 25 webhook token (before Wed 18 Nov, re-smoke), 26 credential scopes list, 27 exit outline per vendor, 28 stage.journal process check; row 12 extended. Counts: raw Blocker 18, dedup 14, Major 218 / 215, totals unchanged; touch-the-take Blockers 10.

## Nits (all PROPOSE FIX, cheap)
L6-EX-10 (b) not archive/ (Decisions C); "rotation starts as soon as the studio head says yes"; rewrite does not reach clones or forks; row 22 clause finished; L7-FD-008 wording and the hubspot_probe.py location; "1 rows" to "1 row"; L6-FD-004 action sentence; L7-FD-004 conflicts-with cell none; L7-FD-005 "method POST and a path"; L1c-FD-021 evidence says saved copies.

## Counts: accepted 10 Majors + 10 Nits; contested 0; escalated 0; declined 0.
Round 2 needed: yes for Majors 1, 2, 10 (numbers and new rows); other items only if round 2 finds a Blocker or Major.
