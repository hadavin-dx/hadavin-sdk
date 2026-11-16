Status: round 3 findings applied by a builder (no new review run; the result of this round is NOT reviewed)
# C4 resolve log, round 3, 2026-11-16
Target: steps-edits/EDITS.md only. Findings: review-c4-r2-design.md (1 Blocker, 7 Majors, nits) and review-c4-r2-codebase.md (F1, F2 Majors, F3 Minor, F4 Nit). inputs/ untouched. Each claim was checked against inputs/DECISIONS-2026-11-16.md, FACTS-ALREADY-DONE.md, AGENT-SCOPE-DO-AND-DONT.md, OWNER-STEPS-realrun-v3.md, DECISION-one-store.md and plan v5 (lines 76, 151, 485-492) before changing.

| Finding | Verified how | What changed |
|---|---|---|
| Design 1 (Blocker), F2: decision 2 | DECISIONS file line 3 (D2); AGENT-SCOPE line 20 and OWNER-STEPS lines 69, 95, 103, 104 read | E-04 now keeps app 1 read-only (no scope change); E-05 rewritten (made-up contacts left, owner deletes by hand); new rows E-40 and E-44 (AGENT-SCOPE line 20), E-41 and E-42 (OWNER-STEPS lines 103, 104), E-45 (AGENT-SCOPE line 23, "archive" in the finally step); CODE-CHANGE-NEEDED section added at the top; old NOT DECIDED item 1 dropped |
| Design 2, F2: decision 7 | D7 and FACTS | E-10 deleted (ids not renumbered); old item 6 dropped; E-37 reworded (step 8 may be obsolete, lead's call; owner only types y, challenge, end) |
| Design 3, F2: decision 8 | D8 | E-11 reworded (rehearsal, then ONE made-up lead; no separate real-account smoke); old item 5 dropped; S0 to S13 removed from owner text |
| Design 4, F2: decision 9 | D9 | E-15 names the proof screen (rehearsal screenshot or Postgres node preview); old item 8 dropped |
| Design 5, F2: decision 10 | D10; DECISION-one-store lines 1, 14 | E-27 "compartments" replaced by "databases"; new rows E-43 (line 14 wording), E-46 ("tables in schema n8n" now "separate database n8n", per CORRECTIONS (a)), E-47 (title line); old item 10 dropped; E-09, E-18, E-31 now say the four-login proposal is parked (D3) |
| Design 6, F2: v4 versus v3 | D10, QUEUE.md C4b, FACTS line 5 | Header section "How the rows are used": rows feed OWNER-STEPS v4; v3 archived; only E-37 for v3 read before v4 exists; AGENT-SCOPE and DECISION-one-store rows patched by the lead; old item 12 dropped |
| Design 7, F1: decision numbers | Compared the cited numbers with the file; the file has 12 decisions numbered differently | Header names the sources: D1 to D12 of DECISIONS-2026-11-16.md and EL-1 to EL-7 (the seven earlier decisions from the brief, not a file in inputs/); every why cell cites D-n or EL-n (leftover "decision N" search below); status line no longer says round 2 applied by resolve-r2 for the review that is applied now |
| Design 8: codes in owner text | read new cells | S0 to S13 removed (E-11); HEAD_PIN and PROVISIONAL replaced by plain words (E-01, E-02) |
| Design 9 nits | read | E-25 cell is now a pointer sentence, stated as such; E-36 caveat moved to "FOR THE LEAD TO CONFIRM" (b); old item 9 ("ANSWERED") and item 11 removed, item 2 kept as confirmation (a); E-02 awkward end fixed; E-39 note that it changes the record of an owner approval, applied only on the lead's say; E-18 lead-side condition moved into the why cell |
| Codebase F2: ports | D6 | NOT DECIDED item 2 now says the plan names the port in one place and the number is absent; E-06 why cites D6 |
| Codebase F3: E-23 | plan v5 lines 485-492 read: only "no commit/push/merge" by the runner; QUEUE.md is not an input | E-23 new text drops the "shared cloud branch" claim; why withdraws the section 8 and QUEUE.md citations and marks EL-6 as lead to confirm; E-35 why also reworded |
| Codebase F4: "re-smoke" unexplained | read | Explained once in E-26 (AGENT-SCOPE header) and E-03 (owner sheet); new texts of E-28 to E-34 say "rehearsal" |
| Minors in my own rows | n/a | E-07 why item number updated; E-13, E-14 why cites updated; "Lines checked" block decision numbers converted to EL-n; E-24, E-25 wording updated |

## Raw check output (script run on the final EDITS.md; text check only, nothing else was run)
```
rows 46 old-text failures 0
{'OWNER-STEPS-realrun-v3.md': 28, 'AGENT-SCOPE-DO-AND-DONT.md': 14, 'DECISION-one-store.md': 4}
{'STALE': 15, 'CONTRADICTION': 12, 'MISSING STEP': 10, 'UNCLEAR WORD': 6, 'DEFERRED': 3}
no overlapping old-text spans in the same file
```
All 46 table rows have 7 cells; every old text (43 rows with an edit) occurs once in its input file and on the line shown. Header counts (46 rows, 28/14/4, types 12/15/6/10/3) match this output.

## Not fixed, not verified
- The result of round 3 is not reviewed by anyone yet.
- EL-1 to EL-7 are taken from the earlier brief as the round 2 reviewers listed them; no file in inputs/ holds them. EL-6 (branches local) has no source I could read; E-23 and E-35 are marked lead to confirm.
- E-36 (accuracy of "own credentials") and E-11 (does the one made-up lead make a paid call) need the lead; listed in "FOR THE LEAD TO CONFIRM".
- Whether the code already prints the list of leftover contacts, and what the take's pause prompt says after the code change, are UNVERIFIED (E-40, E-41); the CODE-CHANGE-NEEDED rows are true only after that change.
- Not read: plan v5 beyond lines 76, 151, 485-492 and greps; code; smoke evidence; WP6-RUNBOOK. Times and click paths were not checked. Nothing was committed or pushed. No agents or background processes were started.
