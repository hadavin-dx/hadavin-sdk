# fix-review13: round 21 fixes to REVIEW.md (fixer, security path, no round cap)

Backup of the file before edits: scratchpad `REVIEW.before.md`. Static work; not committed. Only REVIEW.md was edited (plus this log). `patch-copies/` not touched.

## Unverified or not done (first)
- Nothing run except the commands below. Postgres behaviour, patch tests, `git apply --check` were not run.
- `git apply --check` results (C-01 exit 1, A-01 exit 0, G5-wording exit 1 on `git archive 176a0cbe0`) are recorded from the lead's note and round 19; NOT re-run by me.
- DISCREPANCY with the brief: the brief says the checkout has no .git. The folder `handover/flows-audit/` has none, but `/home/user/hadavin-sdk/.git` exists. I verified the commits there (below) and wrote that in REVIEW.md ('PROVENANCE').
- New text I wrote and nobody reviewed: the database-down fallback outline (Decision 2), criterion (8) and its start-up check, the answer order, the proposed dates (2026-11-17 and 2026-11-18, UTC), the size figure for Decision 22 (about 3 hours, borrowed from the roles summary for a different job). Whether `ChainAudit._append` refuses a repeated event id was not re-checked.
- Possible new inconsistency (not mine): `patch-copies/` now holds `G5-wording.patch` (another agent's work), while REVIEW.md ('Inputs', Decision 23) says it is NOT copied there. I did not edit that statement; the other agent or the lead should reconcile.
- History section (from line ~395) keeps old words ("live", "the lead decides", "step") on purpose; one added line in Words says so.

## Commands and output
- Before: `python3 reviews-of-core-patches/count_review.py reviews-of-core-patches/REVIEW.md` ->
  rows 28 [C-1..X-6]; severity {'Nit': 11, 'Minor': 13, 'Major': 4}; decision {'DECLINE': 3, 'PROPOSE FIX': 25}
- After (same command): identical output (28 rows; Nit 11, Minor 13, Major 4; DECLINE 3, PROPOSE FIX 25). Numbers unchanged, so no 'Present tense counts' line added.
- Cite re-grep (design M1): `config.py:419-420` = `if is_prod(environment):` / `refused += ... NOT_PROD` (holds); `backends/table.py:604` = `NOT_PROD ... {("signer","none"),("anchor","none")}` (holds); `stages.py:18-23` = `is_prod` true unless environment in STAGES[:2] (demo, pilot) (holds).
- Provenance: `git cat-file -t 176a0cbe0`, `b4cce5b`, `07fef531b` each print `commit`; `git rev-parse --short HEAD` = 0d88ad99c; `git merge-base --is-ancestor 176a0cbe0 HEAD` rc 0; `git diff --stat 176a0cbe0 HEAD -- src tests` prints nothing.
- ROLES-PROPOSAL.md: `wc -l` 434; grep for breakglass/break-glass/passkey/CI deploy/OIDC (case-insensitive) = 0 hits; table of mf_* roles at lines 67-71; line 400 'Not covered: a human read-only login, a backup login ...'; line 366 estimate 3 hours.
- /tmp scratch folders listed: /tmp/ch, /tmp/core-b4p, /tmp/core-b4m, /tmp/smfull exist now.

## What changed, by finding
- Design M1 (signer none in production): prerequisite 'this process does not sign' named in X-5.1, X-6.6, drain row of identity table, single-dependency signer paragraph (no longer says PASSES), criterion (6), Decision 3 (decide after 7, 5, 2; size) and Decision 10 (decide after 7 and 5).
- Design M2 (trigger order): triggers of Decisions 2, 3, 4(note), 5, 7, 10, 12, 14, 21 moved to 'before the proposal is sent'; Decision 1 no longer waits for 22; TIMING paragraph names the alternative (split hold) as needing the studio head's yes, not applied.
- Design M3 (Majors outside the hold): criterion (8) for X-6.6a, b, c; enforcement named as a proposed start-up check, and the text says plainly that nothing in code or CI enforces the hold today.
- Design M4: Decision 20 option 5 now lists all 9 Major parts and 3 departures; Blocker test line 21 now has an answer per patch with cites (the old 'cited line for each row' promise removed).
- Design M5: database-down fallback outline, owner, size, proposed date; acceptance-note folder step and owner; DEADLINE sentence replaced and a 'Work that is possible now and still open' list added; Decision 22 size from the roles summary, stated as unverified and for a different job.
- Design M6: PROVENANCE bullet; the 'byte-identical, HEAD 07fef531b' and 'git copy that no longer exists' statements removed or marked.
- Reader B1: line 5, Words (lead vs studio head), and about 15 other places now say 'lead default' and that the studio head may veto; cite `../inputs/DECISIONS-2026-11-16.md` line 1 and line 5. It is the lead's default; no file shows the studio head confirmed it.
- Reader M2-M7, word slips, pointers: login/role/identity unified in Words (role added, 3 other definitions turned into pointers); `operator` person vs login defined and 8 uses fixed; write function vs write path defined and X-2 line 'is a write path' reconciled with the Blocker test; one plain sentence per option in Decisions 2, 5, 6, 9, 11 and `K1bAudit` explained; all 22 'Recommended default' marked 'assistant suggestion', unsourced numbers marked; answer order line added; 'step' (model program, video path, deployment) , 'live' (C-7 bullet), 'reconcile' (X-2, X-5.5-style mentions in A-6 row and X-3 row) fixed; folder pointers, 'Question Q1', count command path, /tmp note.
- Decision 22 and X-6.6d and the identity-table note: corrected so breakglass, CI deploy and humans have NO source document (ROLES-PROPOSAL.md covers only five lead-intake database roles, four of them logins).

## Could not fix, and why
- Who the lead is vs studio head: I cannot show the studio head's confirmation; only a veto or confirmation by him can close it (needs the studio head).
- Database-down fallback: only an outline exists; design review and build need the builder (possible, scheduled with a proposed date).
- Real size of Decisions 7, 8 and the deployment layout: still unknown (no deployment layout chosen; needs the studio head's choice).
- G5-wording copy conflict (see top): outside my file scope.
