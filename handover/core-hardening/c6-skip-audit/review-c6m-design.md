# c6m design and filming-safety review (egm-design, condensed copy of the inline report), saved by the lead session
Target: c6-skip-audit/REPORT-c6m.md (72 rows, NOT APPLIED). Read-only review; nothing was run. Verdict: no blocker; 1 major, 8 minors. Applying all defaults cannot start the take.

## Major
- M1 rows 6 (item 13) and 21 (report lines ~235, ~250): the 45-second check is measured from the first reply of scene 2, but the spoken card line (row 13) and caption (row 21) say "within 45 seconds of the first send". The lease starts when the claim row is written (mf-form.json:97, now() + interval '45 seconds'), before the reply. Failing case: reply at 6 s, repeat 42 s after the reply passes the gate (42 < 45) but is 48 s after the first send. Scene 2 budget is 40 s (run sheet line 31). Fix: measure from the first send; require under about 30 s from the first send; say scene 2 must be shortened to fit.
- M2 (second major in the report text) L-ONEDB default and line 143: the "ratified" interim sentence says "two stores". Q21.3 (ORDERS.md:152) says stage.journal is a second record (decision 10 exception), so the take has n8n's database, the claim database and the journal file. Fix: default becomes "no viewer-facing sentence on the number of stores until C-8 passes", or reword to "n8n's own database, our claim table in Postgres, and a journal file: more than one place". Also decide whether it conflicts with the Q21.3 caption "one Postgres server, two databases".

## Minor
3. Rows 14 (card line 3) and 44: retention sentence assumes n8n's automatic clean-up is on; N8N-START.md:42 says EXECUTIONS_DATA_PRUNE=false was still being tested; no file sets pruning. Say "may stay in n8n's database; we did not measure how long, or whether n8n's clean-up removes it".
4. Rows 3 and 4 dependencies: row 3 depends on L-CARDTEXT, row 4 on L-CARDCUT, but neither is tied to them in table 3b. Add the ties or write "if the card is shortened".
5. Contact-deletion check written twice (row 6 item 12 and row 8 item 11) with different required records. Keep the full record in row 8; row 6 item 12 points to it (keep only the owner-sheet part 12b).
6. Row 8: "Plan 4 lines 106 and 148 stale according to that answer" is the report's inference. Say "probably stale (Q19 item 1, Q23); the lead confirms at re-pin".
7. L-KILL default cites DEC:9; DEC:9 only replaces the real-account smoke with the loopback re-smoke. Default (a) is still right (K3B/K3 not run on real-v5) but do not cite DEC:9 as the cause.
8. "18 runs" rule not met everywhere: report lines 52, 54, 113 and 449 do not name VOID-fl45k3b and VOID-fl45k6c (verify-c6m-output.txt:26). Name both labels there or drop the claim in line 51.
9. Wording slips: C-10c box says "key read-only" but the grep counts any "read-only|read only" (v25-A hit "The exit code is read only at 7.9"); the phrase "lead verifies at re-pin" (Q23/Q27) appears only in report prose, not in rows 6 and 8 ("UNVERIFIED until..." is used); rows 40 and 48 cite raw-lane3/RESULTS.md which exists on cloud/core-hardening, not on the demo branch holding the page-statements file; row 6 item 14 "from the edit of the four flow files on" does not depend on L-SAVE.

## Verified sound (reviewer's list)
Contact-delete gate (no row states that the take deletes or archives; Q19, Q23, Q27, Q20.3 cited with the right lines); saved-runs gate and all eight JSON edit lines; 18 kept runs K1 5, K2 5, K3B 5, K3 3, kill to final 60.1-61.9 s, median 60.85; row 36 correction 52.9 to 52.8; row 33 medians; row 11 total 180 s; all UTC/IST pairs; DEC line numbers (decision N on line N+1); 72 of 72 old-text quotes on their line, 0 mismatches in order; wave-1 count 35 + 34 = 69.

## Not checked by the reviewer
No scripts run; take script, probe script, lane3 reports HB171 to HB194 and R460 not on disk (so "no archive or delete call in the take" stays UNVERIFIED); n8n flow-level saving override untested; which owner sheet the owner actually reads (L-SHEET) unknown; long run-sheet lines for rows 1, 8, 16-20, 23, 26, 27, 30 were omitted by the viewer.
