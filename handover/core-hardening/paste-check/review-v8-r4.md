# Real-v5 edit list v8, round 4 (readiness), condensed copy, 2026-11-16
No Blockers, 5 Majors, 1 lead decision. Not checked: nothing run; plan-wp6-resmoke-v5.md not read (OLD blocks only via dryrun-v8.txt 29/29 rc 0); sections 1b.2, 2, P-2; run.sh, swap-test files, DECISIONS, FACTS; flow citations; arithmetic. Step 4 paste in plan lines 361-402 identical to 10b-clean-start.sh.
Round 3 status: V7-1 fixed for overwrite case (residual = Major 5); V7-2 mostly fixed (Majors 1-3); V7-3 shells separated (Major 4).
## Major
1 Edit 27 step 2: no command or pass text for sending the prep record; no address/payload/program; PREP_KEY value not defined. Fix: name sender (take program, lead fills the line, "lead verifies at re-pin"), set PREP_KEY before sending, give pass text.
2 Edit 27 steps 2/7: prep id may collide with a leftover rehearsal row (ON CONFLICT DO NOTHING) so the read returns an old 'done' = false pass. Fix: run the step 2 query before sending; must print empty line; else new key; put fresh-id rule into step 1.
3 Edit 27 step 2: 'unknown' outcome has no verdict. Fix: one rule, e.g. unknown = STOP until the alert is read; then resend with new key or accept, written down.
4 Edit 13 recipe: diff has no safe pass text; silent output fits failed extractions; PowerShell hash printed but unused; $S vs hard-coded $W/_local/scratch/wp6-smoke/film-crm.tar. Fix: positive expected shape (difference in exactly the url line), empty/traceback/missing tar = STOP; name hash purpose or drop; state $S equals folder or add exists+non-zero check.
5 Edit 27 steps 4a/6: deletion list can be split across OUT and OUT.attemptN. Fix: step 6 says deletion list = union of OUT and every OUT.attemptN, duplicates removed.
## Lead decision
6 Claim wording: Q15.3 (10:13Z) 'processed once inside the lease' vs Q21.2 (10:50Z) 'processed once' (DECISIONS 1) + one lease sentence. Plan quotes Q15.3 form. State which text plan carries; Q21.2 also asks whether unique index exists: 'index present by primary key (lead_key text PRIMARY KEY, read in 1b.2)'.
Checked OK vs Q15-Q21: Q15.2 verbatim, Q15.1/Q17 label, Q19.1, Q20.1, Q20.2, decision 10, Q20.4.
