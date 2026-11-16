# Goldfish Annotated Review Report (plan round 1, resolve)

Status: resolved (headless auto accept; no human gate available). The lead rewrites PLAN.md as version 2 from this file. I did not edit PLAN.md.

**Target:** `handover/system-map/reviews-of-core-hardening/PLAN.md` (full file, version 1)
**Findings:** `work/plan-review-r1.md` (zoom-out Z-*, implementation-readiness R-*)

## Counts
- Findings read: 7 Z (3 Major, 4 Nit) + 1 coverage nit + 11 R (2 Blocker, 9 Major) + 6 R-nits.
- PROPOSE FIX: all Blockers and Majors, plus the Nits listed (merged into 14 edits below).
- CONTEST: 0. ESCALATE: 0. DECLINE: 1 (see D1).
- Check against ORDER 005 (`handover/system-map/ORDERS.md`, last section): no finding contradicts it. One finding tightens it: the order says "at least half of the Majors" (40 of 80); v2 sets the floor higher (see E3).

## Summary of edits to make in PLAN.md v2
Merged duplicates: Z-N2 + R-M3 (sampling) -> E3; Z-N3 + R-M2 -> E2; Z-N4 + R-B2 -> E1; Z-M3 + R-M6 -> E6; Z-M2 + R-M5 -> E5; R-B1 + Z-N2 (checker) -> E1/E6; Z-N1 + nit "who lists 22 files" -> E6.

---
### E1 [R-B1, R-B2, Z-N4] Blocker: paths, fetch method, target file list
PROPOSE FIX. Add a section "Paths and inputs" to PLAN.md:
```
Paths (all absolute, fixed):
- SCR   = /tmp/claude-0/-home-user/d72bd15c-b484-516a-89e0-703eea3c1a47/scratchpad
- SNAP  = $SCR/snap    code snapshot of b4cce5b (git archive b4cce5b), read only. Owner: lead (already built).
- CH    = $SCR/ch/handover/core-hardening   copy of the target folder (git archive origin/cloud/core-hardening handover/core-hardening), read only. Owner: lead (already built).
- OUT   = /home/user/hadavin-sdk/handover/system-map/reviews-of-core-hardening   (WORK = $OUT/work, PATCHES = $OUT/patches)
- CHECK = /home/user/hadavin-sdk/handover/system-map/tools/check_citations.py   (reused unchanged; usage: python3 CHECK <repo_root> <out_tsv> <abs file.md>...; repo_root = SNAP)
Target files, read from CH (agents may also use `git -C /home/user/hadavin-sdk show origin/cloud/core-hardening:handover/core-hardening/<file>`):
 MASTER-MAP.md, AUDIT-FINDINGS.md, README.md, REPORT.md, QUESTIONS.md, patches/C-01-and-A-02.patch, patches/ledger-rows.md, result-resolve-1/2 and result-review-1a..1d, 2a..2c, parts/ (36 files).
 "Part 1 result" = AUDIT-FINDINGS.md plus parts/findings-*, parts/evidence-1.* and result-review-1a..1d + result-resolve-1 (the part 1 result files). Round 2 files (result-review-2a..2c, result-resolve-2) are read as well; the target says round 2 was not re-reviewed.
Code is read only from SNAP, never from the repo's own src/ (22 files differ, see E6).
```

### E2 [R-M2, Z-N3] Major: process rules from ORDER 002 (unchanged)
PROPOSE FIX. Replace "Time box 45 minutes; a checkpoint note every 20 minutes" in "Rules for every agent brief" with:
```
Process (same as ORDER 002): before starting an agent, write its row in REPORT.md (id, purpose, started UTC/IST, expected end, last check, state, next action). A status block goes into REPORT.md every 10 minutes (UTC and IST) naming agents running and what each does; commit and push to cloud/system-map each time. Builder time box 45 minutes (hard limit 60); a builder writes a checkpoint note into its own work file at 30 minutes. At the expected end I read the agent's file, then close its row in the same turn. At the end: sweep of the register, counts of agents started/closed/still open (must be 0 open), FINAL block.
```

### E3 [R-M3, Z-N2] Major: one hard sampling floor
PROPOSE FIX. Replace Method step 1 sampling text with:
```
Ids: a finding id is as written in AUDIT-FINDINGS.md (A-01, B-01, C-01, D1-01, D2-01, D3-01, X-01 ...). Lanes: A security; B state and runtime; C model code; D1 tests; D2 demos; D3 docs; X cross-lane.
Slices and Major counts: V1 = A + X (2 Blocker, 22 Major); V2 = B + D1 (1 Blocker, 14 Major); V3 = C + D3 (1 Blocker, 27 Major); V4 = D2 (1 Blocker, 17 Major). Total 5 Blocker, 80 Major.
Hard floor per verifier: every Blocker of its slice, and at least ceil(60 percent) of its Majors: V1 14, V2 9, V3 17, V4 11 (sum 51 of 80; ORDER 005 asks for at least 40). Choose rule: Majors in the order of AUDIT-FINDINGS.md, odd number part first (X-01, X-03 ...), then even ones, until the floor is met; then continue with the rest while time remains. The verifier lists every Major it did not check as NOT-SAMPLED.
Shortfall rule: if a slice ends below its floor at the time box, I start one more verifier for the unchecked ids (once). If the total is still below 40 Majors at 09:15 UTC, REVIEW.md and FINAL state "ORDER 005 spot-check target not met: N of 80".
```
Also change the "Goal" line "at least 50 of 80" wording to "at least 51 of 80 (floor), ORDER minimum 40".

### E4 [R-M4, R-M1] Major: criteria, formats, inputs per agent
PROPOSE FIX. Add a section "Verdict rules and report format":
```
Verdicts (per finding): CONFIRMED = the quoted file:line exists in SNAP, the quote is there and the target's claim follows from it. WRONG = file or line exists but the code contradicts the claim, or the quote does not exist anywhere in that file. UNVERIFIABLE = needs a running program, a network or a file outside SNAP; or the line moved and the claim cannot be re-placed within 20 lines; state why. Severity column: AGREES / TOO HIGH / TOO LOW with one line of reason (a true claim can still have the wrong severity). A quote of 6 to 120 characters must be shown for every verdict.
Each verifier's file: work/verify-V<n>.md, a header "What I did NOT check", then a table: id | severity (target) | verdict | severity check | file:line "quote" | one line of reason.
H1 patterns: vendor SDK imports (boto3, botocore, azure, google.cloud, anthropic, openai, psycopg, redis, requests-style vendor clients, temporalio, langgraph) outside the kind module directories (src/hadavin_sdk/kinds/ or the directories named kind in SNAP, found first); stage names other than demo, pilot, prod (grep for "staging", "dev", "production", "stage ="); wildcard actions or resources ("*" in policies, Resource: *), long-lived keys, hardcoded model ids, regions, account ids, prices; literals that look like secrets (only AKIAIOSFODNN7EXAMPLE allowed). Output work/hunt-H1.md.
H2 definitions: DEAD = a module under src/ with no importer except tests and no entry point or config reference; IDLE = imported but never called outside its own tests; DUPLICATE = two modules doing one job (store, log, filter, counter, retry engine, notice); SECOND SOURCE = a demos/ file that copies a src/ core module name or function without a promotion entry; DEMO-LOCAL GENERIC = generic code in demos/ that is not in core and has no promotion entry. Output work/hunt-H2.md.
V5 output work/verify-V5.md. Hunters and V5 quote file:line "quote" for every candidate, else the item is not reported. Every file starts with what was not read.
Inputs: V1-V4 get CH (their slice of AUDIT-FINDINGS.md and the files named in the findings) and SNAP. H1, H2 get SNAP and the rules above only. V5 gets SNAP and the item list (names only, see E5). Runner gets CH, SNAP, CHECK.
```

### E5 [Z-M1, Z-M2, R-M5] Major: anti-anchoring and second looks
PROPOSE FIX. Add to Method:
```
No anchoring: H1, H2 are not given AUDIT-FINDINGS.md, MASTER-MAP.md or any verdict. After they report I diff their candidates against the target's findings myself ("target found it" / "MISSED"). V5 first gets only the list of item names from the target's one-place table and cut list (no verdicts). V5 classifies each item (NEEDED / DUPLICATE / NOT-NEEDED) from callers and importers in SNAP, then I compare with the target's verdicts; differences go to a second look.
Second look: each of the 5 Blockers is checked a second time, by me (lead) with my own reading of the line in SNAP, not by the first verifier's quote. I also re-read a sample of verifier lines: all WRONG and UNVERIFIABLE lines, plus 10 CONFIRMED lines (every 5th CONFIRMED in table order, at least 10). A verifier whose sample shows 2 or more bad lines is re-run on that slice (once).
A quote that exists is not proof: a CONFIRMED needs the claim to follow, not only the text to exist (see E4).
Result review: reviewers codebase_details, zoom_out, design and comprehension are used (at least 3 of the 4, always different types); each reads REVIEW.md, CORRECTIONS.md, patches/, LEDGER-ROWS.md, the evidence file and the verifier files; they return reports inline; I save them as work/result-review-<round><letter>.md. Resolve runs through the Skill (opus, as the skill sets it); I apply its PROPOSE FIX items to the three deliverables myself.
```

### E6 [Z-M3, R-M6, Z-N1, Z-N2, nits] Major: evidence runner scope, claims without evidence
PROPOSE FIX. Replace Method step 4 with:
```
EVIDENCE RUNNER (sonnet; runs and records, never judges; it runs CHECK, which it did not write, and the commands below, and nothing else; no product program is run; no edits outside work/evidence-ch-1.md and its tsv files):
 a) CHECK on CH/AUDIT-FINDINGS.md and CH/MASTER-MAP.md against SNAP; report counts: cites total, FOUND, quote mismatch, file missing, line out of range (these four counted separately).
 b) Count and list findings (by id) and MASTER-MAP statements that have no `path:line "quote"` (claims without evidence); list statements that say verified, passed or done without a command (grep: "verified", "passed", "done", "confirmed" lines with no backtick command in the same finding).
 c) Findings per lane and severity by grep -c on the `**<id> | <Severity> |` pattern, versus the target's own table (no custom script).
 d) List of the 22 src files that differ between b4cce5b and my branch head: `git -C /home/user/hadavin-sdk diff --name-only b4cce5b HEAD -- src`; mark every cited file and every dead-module claim that falls in that list.
 Raw output in work/evidence-ch-1.md.
```
Also change the opening note "Static only: no program is run" to "Static only: no product program is run".
Replace the Ladder line with: "Rung 1 reuse: CHECK from ORDER 002 unchanged, grep -c for counts. Rungs 2 to 6 not needed. Rung 7: no new code."

### E7 [R-M7] Major: rung table
PROPOSE FIX. Add to the deliverable list and Method: "REVIEW.md contains a RUNG TABLE for the target's proposed fixes and new code in AUDIT-FINDINGS section 4 and the patches: component | need | rung tried (1 to 7, see tool-ladder rule) | evidence | what only our code gives | verdict (RIGHT RUNG / TOO HIGH / TOO LOW). V5 fills it from the fix plan and patches." Counts: no new script, grep -c (E6c) covers the count.

### E8 [R-M8] Major: CORRECTIONS format
PROPOSE FIX. Add:
```
CORRECTIONS.md = an index table (id | file in the target | what is wrong | patch file) and, for each correction, a unified diff in PATCHES/<finding-id>.patch made against the file in CH (diff -u a/<path> b/<path>, paths relative to handover/core-hardening/). A correction to a number, label or verdict in AUDIT-FINDINGS.md or MASTER-MAP.md is a patch of that line only. Where a code fix is needed (the target's own code claim), CORRECTIONS.md gives the exact old and new text but no patch to src/. I never edit CH or the repo outside OUT; I check each patch with `patch --dry-run -p1` in a scratch copy and record the result.
```

### E9 [R-M9] Major: stop rule and verdict scale
PROPOSE FIX. Replace "Stop rule" with:
```
Stop rule: result round 2 is the last. After round 2 only Blockers and Majors get another check; Nits are fixed in the same push. If a Blocker or Major of mine is still open after round 2, it is written into REVIEW.md as OPEN with its reason, ledger status OPEN, and FINAL says so (no new round). Hard stop 09:30 UTC (15:00 IST): at 09:15 I stop starting work, at 09:30 I push whatever exists, and FINAL states which outputs are partial.
REVIEW.md verdict scale (first line): RELIABLE (0 Blocker WRONG and at most 10 percent of checked Majors WRONG) / RELIABLE WITH CORRECTIONS (0 Blocker WRONG and more than 10 and at most 25 percent of checked Majors WRONG, or any Blocker with severity TOO HIGH) / NOT RELIABLE (any Blocker WRONG, or more than 25 percent of checked Majors WRONG, or more than 10 percent of findings with no citation). The numbers behind the verdict are printed next to it.
```

### E10 [R-nit] LEDGER-ROWS rules
PROPOSE FIX. Add: "LEDGER-ROWS.md: 9 columns, id scheme CHR-<lane letters>-<nn> (CHR = core-hardening review), source = REVIEW.md section or verify-V<n>.md line, severity Blocker/Major/Nit, status one of OPEN / FIXED-UNVERIFIED / FIXED-VERIFIED / OWNER-ONLY / IMPOSSIBLE-NOW (new rows start OPEN), date = YYYY-MM-DD UTC."

### E11 [R-nit] MUST-NOT and models
PROPOSE FIX. Extend the MUST-NOT list: "no pipes into cut/tail for exit codes, no commands that write outside the agent's own output file, no `cd` into SNAP or CH to run interpreters (use absolute paths and `python3 -I`), no git commands that change anything." Add: "Models: sonnet-5-5 for verifiers, hunters, runner and result reviewers; resolve and planning through the egm skills (opus, set by the skill); no haiku."

### E12 [R-nit] Dependency order and parallelism
PROPOSE FIX. Add: "Order: (1) plan v2 pushed; (2) at once, in parallel: V1, V2, V3, V4, H1, H2, runner (7 agents, all read only; CPU is light, heavy jobs none); (3) when V1-V4 and the runner report: V5 (needs the runner's cite counts only for context), then my second look; (4) merge deliverables; (5) result review (3 reviewers in parallel from one snapshot of the three deliverables); (6) resolve, fix; (7) round 2 if any Blocker or Major open; (8) drift report, FINAL." Expected times: step 2 about 40 minutes, steps 3 to 4 about 30, step 5 to 8 about 40: ends before 09:30 UTC if step 2 starts by 08:10.

### E13 [Z coverage nit] H2: generic building blocks
PROPOSE FIX. Included in E4 (DEMO-LOCAL GENERIC and SECOND SOURCE definitions). No extra text.

### E14 [Z-N2 part] Sentence "(scratch folder snap/)" in line 3 of PLAN.md
PROPOSE FIX. Replace "scratch folder `snap/`" with "SNAP (see Paths)". Also add to the note about stale claims: "REVIEW.md lists the 22 differing src files (from E6d) and marks each cited claim in them as 'may be stale'".

---
### D1 DECLINE
None of the Z/R findings is declined except the sub-point of Z-N2 that asks to justify a count script: no script is written (E6c uses grep -c), so no justification text is needed.

## Escalations
None. Every finding was checkable from PLAN.md, ORDERS.md and the target folder.

## Remaining unaddressed
0 Blocker, 0 Major. After PLAN.md v2 is written, a plan round 2 is optional (max 3 rounds). Recommendation: skip round 2 because the fixes only add concrete values; the first result round is the real test.
