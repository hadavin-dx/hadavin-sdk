# fix-runbook3 (flows-audit, round 3, 2026-11-16)

Backup of the round 2 file: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-rb3/RUNBOOK.md. Only RUNBOOK.md and this log were written. Nothing was run in n8n; no git command; no commit. The edit was applied by one script (rb3.py in the scratchpad) with an exact-match check per replacement; it exited ok. I did not re-read the whole file after the edit (only grepped for stale figures). No EGM review of the result was run by me; the lead runs it.

## Failures and doubts first (all kept visible in RUNBOOK)
1. The lead's 09:30 UTC "done" for the re-smoke is 30 min more than 08:00 + 60 min; planned 60 min and showed the 90-min slot as a second figure (I14).
2. Whether the re-smoke's "n8n start, import and fill" repeats steps 7 to 13 is not said (I14, I15).
3. The full caption sentence is joined by me from Q25-2 and the Q28-1 phrase (failure 11, I35); the step 14 grep uses it.
4. The "recount" of Q29-2: I read it as a second count after the stated wait; the gap is not given (I20).
5. Estimates of mine: positive control 10 min (step 19a), step 14 raised 20 to 30 min, and the arithmetic that depends on them.
6. Still open: reading (A) or (B) of the Q27-6 07:00 UTC (both now fit with the 1-hour re-smoke); "decision 1" (Q27-8) against the script text "(decision 4)"; clock times of S9-2 and S9-3; the post date for a slipped take; the new text of DECISIONS items 1 and 7 and VIDEO-RUNSHEET N-9 to N-11 (not read); n8n_drive.py and the post-twice script existence (UNVERIFIED); branch and time of the read-only review (I33).

## What changed
- Header, status, sources: round 3; stamps of earlier ORDERS blocks dropped (line 170), answers cited by Q number and ORDERS line.
- Failure 6: re-smoke now about 1 h (NOTE). Failure 7: Q30-2 and Q29-3 added. Failure 8: Q28-5 added. Failure 9: Step A closed (removed, Q28-3). New failures 11, 12.
- Roles: owner decides crop/blur/cover/not needed for private addresses, no Step A; lead never edits the recording.
- Steps: 6 (six paths, n8n_drive.py, branch for read-only review), 14 (F-031/F-007 by Wed 06:00 UTC, item g DECISIONS/N-9..11 and in-frame, caption with "in the intake mailbox", 30 min), 16 (1 h), 17, 18 (T19/T20 fail = NO-GO, no unpatched fallback; precondition F-031/F-007), new 19a positive control, 21, 23, 25, 26 (recount, in frame, list of private addresses), 27 (no Step A), 28, 29, section 7 row.
- Arithmetic recomputed: Tuesday event 224 min (3 h 44); latest step 2 start for Tuesday GO 09:16 UTC (60 min re-smoke) or 08:46 (90 min); one repeat 06:25 or 05:55; Wednesday: control 07:30-07:40, rehearsal 07:40-09:20, gate to 09:45, GO check to 09:50, take 10:00; NO-GO chain 350 min (5 h 50): reading A ends 12:50 UTC, reading B 16:34 UTC.
- Section 9: seven stale-text bullets added. Section 10: I1, I4, I9, I12, I14 to I16, I18, I20, I26, I27, I29 to I31 updated with ORDERS lines; I32 to I35 added.

Not checked: whether ORDERS line numbers shift if the file is edited again; sums were done by hand, not by a script.
