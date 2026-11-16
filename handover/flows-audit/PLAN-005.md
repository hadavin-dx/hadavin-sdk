# PLAN-005: independent cross-review of system-map (ORDER 005)
Written 2026-11-16 07:52 UTC / 13:22 IST; v2 after plan review round 1 (07:55 UTC / 13:25 IST). Static review only: no runtime, no real client data seen, edit only handover/flows-audit/.

## Target (read-only copies, from `git archive origin/cloud/system-map`, head sha 707768f)
- Outputs: /tmp/sm/handover/system-map/{MASTER-MAP.md, SWEEP.md, ONE-PLACE-TABLE.md, REPORT.md, DECISION-one-store.md}
- Whole tree for checking cited file:line: /tmp/smfull (handover/demo, handover/demo3, src, demos, .github)
- Not visible to anyone here: take repo `duplicate-proof-lead-desk`, n8n runtime, HubSpot, SMTP -> UNVERIFIABLE, never guessed.

## What I judge (ORDER 005 focus)
1. One-place table: is the single owner right for STORE, LOG, FILTER, COUNTER, RETRY, NOTICE, OTHER; are the extras truly duplicates; any NEEDED called DUPLICATE or the reverse; anything proposed for deletion/archive that has a caller.
2. The 4 open lead decisions the target lists (dollar-cap place, second alert channel + watcher, what the take proof counter reads, count outside n8n / three roles vs fourth identity).
3. The three Blocker bands in the fix plan (before-video decisions; before-video only if chosen; after-video): is each Blocker real, in the right band.
4. Spot-check every Blocker (raw 20 / dedup 16) and at least half of the Majors against real file:line: CONFIRMED / WRONG / UNVERIFIABLE.
5. What the target MISSED.

## Definitions (fixed before the lanes start)
- Citation verdict (per Blocker/Major finding of the target): CONFIRMED = the cited file:line was read and the claim holds; WRONG = read and the claim is false, or the line holds different text (say which); UNVERIFIABLE = needs the n8n runtime, HubSpot, SMTP or the take repo (reason stated; never a guess).
- Table verdict (per ONE-PLACE-TABLE row, 59 rows): AGREE / DISAGREE (state the right verdict: OWNER, NEEDED, DUPLICATE, CRM-COULD-DO, NOT-NEEDED, KEEP-CORE) / CANNOT-JUDGE (reason).
- Where things are in the target: Blockers and Majors = rows of the table `## Findings` in SWEEP.md (lines 35-355; 20 Blocker, 209 Major, 85 Nit raw). The three Blocker bands = the `## Fix plan` of SWEEP.md (lines 356-386: before the video as a decision or config change; before the video only if the laptop lead chooses; after the video). The 4 open lead decisions = SWEEP.md line 16 / REPORT.md line 7: (1) the place that holds the dollar cap, (2) the second alert channel and its watcher, (3) what the take proof counter reads, (4) whether the independent count runs outside n8n (and three roles versus a fourth identity). Judging a decision = say whether it is well posed, whether the evidence supports it, and what answer the evidence points to.
- Sample rule for Majors: every 2nd Major row in file order (about 105 of 209 = at least half). R5-M1 takes the sampled rows in SWEEP.md lines 35-200, R5-M2 those in lines 201-355. EV5 (already run) checked the existence of every 3rd Major row's citations (59 rows, 209 citations, all exact-line); this proves the quote exists, not that it supports the claim, so the reviewers judge support. No random seed is used.
- Ids: new findings are `R5-<lane>-<n>` (R5-B, R5-M1, R5-M2, R5-D, R5-Z, EV5). Ledger id = `XR-<n>` in LEDGER-ROWS.md. Severity: the lane gives it; the resolver changes none; a finding raised by two lanes is merged under the higher severity with both ids listed.
- Ledger status at the start: OPEN for every finding against the target (the fix is the target session's work); UNVERIFIABLE items: OWNER-ONLY if the laptop lead or studio head must act, else OPEN. Review verdict word in REVIEW.md: PASS (no Blocker WRONG or missed), PASS WITH CORRECTIONS, or FAIL.
- Rounds: review of the plan max 3 (this is round 1 done, v2 follows); review of the target max 2 rounds; a round 2 happens only if my REVIEW.md/CORRECTIONS.md draft gets a Blocker or Major from a fresh reviewer. Security/mail/money items uncapped, everything else max 2.

## Lanes (agents; all sonnet, fresh, model set on every call; egm-resolve = opus via the Skill; time box 40 min each, checkpoint by report)
Reviewers have Read/Grep/Glob only: they return inline; I save each report to reviews-of-system-map/lane-<id>.md. Each brief carries the studio preamble pointer, the MUST-NOT list and the paths /tmp/sm/handover/system-map (outputs) and /tmp/smfull (tree).
| id | type | scope and output |
|---|---|---|
| EV5 | general-purpose, EVIDENCE RUNNER | citation checks (Blocker rows, the Major sample, every evidence cell of ONE-PLACE-TABLE), caller grep over src, tests, demos, .github, pyproject.toml, tools for every proposal with ARCHIVE, remove, STOP or MERGE in the table (derived by script, not hand-picked; includes L6-J-028, 042, 059), table counts 49+10, 7 Owner lines, id gaps. Writes reviews-of-system-map/evidence-5.md, raw only. |
| R5-B | egm:egm-codebase-details | all 20 raw Blocker rows of SWEEP.md: read the cited file:line, verdict per citation verdict set; table: id, verdict, evidence line, note. |
| R5-M1, R5-M2 | egm:egm-codebase-details | the Major sample (halves as above), same table. |
| R5-D | egm:egm-design | all 59 table rows: table verdict; per job key is the one Owner right and are the extras truly duplicates (reads source where needed); the 4 decisions; the three bands (is each Blocker in the right band; uses R5-B result when it lands). |
| R5-Z | egm:egm-zoom-out | what the target MISSED (stores, logs, counters, retry engines, filters, notices not in the table, from MASTER-MAP.md and the tree); every cut: anything proposed for deletion or archive that has a caller or is NEEDED; wording check of the table wording for a non-technical reader. |
Plan review of this file done: round 1 (design + implementation-readiness) found 1+3 Blockers, 12 Majors; v2 fixes them; round 2 not run (small plan, no new design; said plainly).

## Order
register agents (REPORT.md) -> EV5, R5-B, R5-M1, R5-M2, R5-D, R5-Z in parallel (max 6 at once) -> lead reads reports, merges -> egm-resolve (opus, Skill) -> write REVIEW.md, CORRECTIONS.md, LEDGER-ROWS.md -> fresh reviewer on my drafts (round 1 of review) -> fix -> drift check (my outputs vs lanes vs evidence) -> ORDER 004: already applied and pushed in 35235ac, re-checked by `git log` at the end, no new work -> FINAL block in REPORT.md, push to cloud/flows-audit, stop. Status block every 10 minutes (clock from `date -u`).

## Stop rule (checklist; each item gets a count and command result in REVIEW.md)
- 20 of 20 raw Blockers have a citation verdict.
- Majors checked >= ceil(209/2) = 105 (count written).
- 59 of 59 table rows have a table verdict.
- 4 of 4 open decisions have a view; 3 of 3 bands judged.
- A "Not checked" section exists; UNVERIFIABLE only with a reason.
- Every claim line in REVIEW.md carries a path:line or the tag UNVERIFIABLE (script check).
- Review rounds <= 2; ledger rows have 9 columns (script check); all agents closed.

## Outputs (/home/user/hadavin-sdk/handover/flows-audit/reviews-of-system-map/, created by me)
REVIEW.md (verdict first, failures first), CORRECTIONS.md (exact fixes to the target), LEDGER-ROWS.md (id | source | severity | area | summary | status | fixing artifact | verified-by | date), evidence-5.md, lane-*.md. The ledger file `egm\tools\ledger_check.py` does not exist here; the rows are for the lead to append to the ledger.
