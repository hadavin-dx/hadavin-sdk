# ledger-history-cells (fix-findings-ledger24, 2026-11-16)

Round-history sentences moved out of live instruction cells of FINDINGS.md and LEDGER-ROWS.md (reader r25 M5). Nothing here is an instruction; the live rule stays in the row. No severity, count or verdict changed.

- F-002 T21 method: earlier text of the 'second way' said to point the n8n credential n8n-publish-pg at a closed port, send, and point it back (UNVERIFIED that n8n applies the change without a restart). Reader r25 M1: that does not give the role LOGIN back; replaced by SECOND_ADMIN in fix-findings-ledger24.
- F-011 STATE OF FIX A (c): earlier text said 'The runner question is not yet in Q31'; item 136 has been in QUESTIONS.md since fix-q31-28 (reader r25 M2).
- F-003 (4a): round 16 wrote the repository-folder question as a NEW QUESTION that someone had to add; round 20 / fix-q31-23 added it to QUESTIONS.md as item 111.
- F-002 F-002b: the older text said 'written now, Mon 16 Nov (the default of item 16)', which was wrong; the default of item 16 is NO (Q31 item 16 (a)).
- F-003 T20 (round 21): the earlier form 'run before and after prints the same number' also looked like a pass when $PGADMIN_PW was unset or psql failed, because two empty or two error answers are 'the same'. The live rule is the numeric guard in the row.
- F-031 (round 21): the earlier form ran a second grep for the sentence alone, and with the heading missing that command printed only the sentence line, a look-alike of a pass. The live rule (exactly two lines, sentence first) stays in the row.

## fix-findings-ledger27 (2026-11-16)

- F-004 (reader r27 item 2): round history moved out of the fix cell: 'regenerated 2026-11-16' note and patches/REGENERATED-NOTE.md pointer; 'after the review it also rewrites the Tag, Test and Raw lines' (now part of the FIX list); 'the earlier sentence of this row that said statement 17 names 45 s and 120 s was stale'; round 16 labels ('PASS LINE (round 16Z)', 'WHO AND WHAT CLOSED PROVES (round 16; planned by the audit...)'); the earlier pass line used `grep -c -e "60\.1" -e "61\.9"` with no path, no exit-status test and no guard, so it printed 0 for an empty $REPO or a missing file (the same look-alike of a pass as F-003 T20 and F-031); the evidence cell said 'Today it prints 4 lines (grep -c, read 2026-11-16)' as the positive control, which was a one-time observation (now pass line part (1)).
