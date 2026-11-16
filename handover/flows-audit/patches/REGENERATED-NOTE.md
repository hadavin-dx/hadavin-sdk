# F-003 and F-004 regenerated (2026-11-16, lead decision 1)

Source of the decision: inputs/DECISIONS-2026-11-16.md item 1 (the one video is REAL-V5 ONLY, scenes 1 to 4; scene 5 and the caption number "60.1 to 61.9 s" are cut). Wording follows RUNSHEET-WORDING.md section 1 and 2 rows with their default (held) choices from section 0b. Static work: nothing ran in n8n, a CRM or a mail server.

Old patches are kept unchanged in patches/archive-pre-decision1/ (copies; sha256 in lanes7/evidence-patches-r2.txt). Check output is in lanes7/evidence-patches-r2.txt: PASS 5 patches, exit 0, and 0 lines with the cut strings among the added lines of F-003 and F-004.

## What changed
F-003 (handover/demo/VIDEO-RUNSHEET.md), added text now has:
- scenes 1 to 4 only in the changelog line (A-001), made-up wording for people and e-mail addresses (A-005, A-084), real-v5 flow description (V-11), scene 1 card and the CRM explanation (A-008a, N-6), scene 3 voice and caption (A-016a to d), scene 4: lease label and spoken lease explanation (N-5a, N-5b), no caption with a recovery number (A-017a default), planning guess "not measured at 45 s" (A-087c, A-087d).
- closing card cut to four lines (A-016e, A-051a, A-053b, A-091 with N-3). The older-test lines 2 and 4 (A-050a/b, V-41, A-023) are left out because D2 holds them.
- risk 2, risk 7, risk 8 (V-57 wording), the lease bullet, the timing lines (180 s for scenes 1 to 4 and the closing card), rehearsal item 9 and open decisions 4 and 5 are updated.
- the last paragraph (the final scene 4 caption with "60.1 to 61.9 s") is deleted (A-019a).
F-004 (handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md):
- statement 17 rewritten (A-073a wording, 20 s figure only; no 45 s or 120 s figure; no film-v5, no "60.1 to 61.9 s"); tag says HELD until D2 settles whether the 20 s figure is laptop-measured or relayed.
- total line says 20 statements (A-083); "NOT RUN" list wording for 17.
- statement 20 is marked HELD, DO NOT QUOTE; its range and caption wording are removed.

## What is NOT covered (and the next step)
1. Scene rows 5 to 11 (the stand-in scenes) still exist in VIDEO-RUNSHEET.md, plus the scene 5 caption line and "Update 17:08Z" scene 5 line. This patch does not delete them. Next step: coordinator decides whether to move them to a later-video file or delete them; I did not delete rows I did not write. Lines naming scene 5 to 11 that survive are old text, not added text.
2. Old F-003 also changed "seven" to "six" columns (table screen) and related risk lines. That is not in the regenerated F-003 (table screen is scene 10 material and the rehearsal item still says seven). Next step: add back if the table screen stays in the take.
3. RUNSHEET-WORDING.md rows held by D1, D2, P2, P4a to P4c were not pasted: A-007, A-010, A-010b, A-017b, A-019b, A-023, A-050, A-051b, A-073b, A-073c, A-087a/b, V-41. A-073a is pasted but HELD in the tag. Page statement 18 and 19 and the "Honest limits" lines are untouched (limit lines still say "Lease 120 s: one lane3 figure only", which is true for the old text).
4. F-001 still mentions film-v5 in an SQL comment (patches/F-001-one-ddl.patch line 7). Not part of this assignment; next step: lead decides whether to reword.
5. The check script tests only that patches apply and JSON parses; it does not check wording. The wording rules were checked by reading and one grep (cut strings), not by a reviewer. No EGM review of the result was run: EGM review step (e) and drift report (g) are for the lead to run (this agent cannot invoke them).
6. Statement 17 and card line 4 depend on other-session figures whose raw files are not in this repository: UNVERIFIED.
