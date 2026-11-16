# fix-g1-g9 (fixer). Input: reviews/notchecked-lane-r1.md. Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-g/

## Not fixed or not checked (first)
- Nothing ran in n8n, Postgres, HubSpot or the sender. Every new gate line is a written rule; none was rehearsed.
- Sender retry on a non-200 answer: UNKNOWN (sender not in repo). Written as a lead check at re-pin.
- Whether 45 s lease is long enough for Qualify and the CRM write: unmeasured. Written as a rehearsal check.
- CLAIMS-TABLE.md (must use the 'processed once' proof wording), RUNSHEET-WORDING.md and OWNER-STEPS-q16-rows.md are owned by other fixers; I did not touch them.
- The reviewer read only part of FINDINGS (1-96); I checked each item against the files I could read, not the whole set.
- F-031 and F-003 rows: no edit needed (F-031 text fix is FIX-PLAN item 5; F-003 untouched).

## Per item (checked against files)
G1 true: no start-state gate existed in FIX-PLAN item 3 or the README; added (a), README step 5.
G2 true: added (b) proof rule, README step 6; CLAIMS-TABLE change belongs to its owner.
G3 true: (c). G4 true: (d). G5 partly true: recovery ClaimStuck sets 'interval 45 seconds' (mf-recovery.json:26); recovery runs every 30 s per README; no duration check existed: (e).
G6 NOT true as stated: FINDINGS F-008 and FIX-PLAN item 4 already say no deletion (Q19-1) and mark 'deleted at clean-up' SUPERSEDED; added (h) confirming, no contradiction found in the files I read.
G7, G8, G9: added (f), (g), README step 8.
## Files changed
FIX-PLAN.md (item 3 lines a-h), FINDINGS.md (NOT COVERED items 22-27), flow-check/README.md (Before the take steps 5-8; section on RUN_ALL_RAW, RUN_ALL_TAKE_FLOWS, RUN_ALL_NESTED).
## Evidence
python3 tools/count_findings.py FINDINGS.md: rows 45 = Blocker 5 / Major 7 / Nit 33; BEFORE 13, AFTER 32. LEDGER-ROWS.md untouched.
sh handover/flows-audit/tools/check_patches.sh (repo root): PASS 4 patches.
EGM skipped: wording-only edits to audit notes by a fixer under the lead's brief; the lead runs the EGM review.
