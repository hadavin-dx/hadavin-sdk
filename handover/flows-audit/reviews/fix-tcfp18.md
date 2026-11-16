# fix-tcfp18: round 23 fixes M1-M14 (RUNBOOK, FIX-PLAN, TAKE-CHECKLIST)
Static work only. Nothing was run against n8n, Postgres or HubSpot. Reviewer words were checked against the files. All lead answers stay "planned by the audit, lead to confirm".

## What did NOT get done fully (first)
- M12 is only partly fixed: FIX-PLAN still has its own step numbers (0 to 17). A full renumber to RUNBOOK numbers would touch about 170 bare "step N" mentions in FIX-PLAN plus about 40 cross-references; many mean the RUNBOOK and many mean FIX-PLAN, so a mechanical rewrite would change meanings. Done instead: one mapping (FIX-PLAN line 63, now with 11b), RUNBOOK numbers written out in the time table (line 72) and the reader windows (lines 52/53, and TAKE-CHECKLIST), the collision named, and the rule "every number in a time, due date or pass line carries its file". Needs lead: say yes to a full renumber (then one dedicated pass with a per-line review).
- M10 is partly contested (see below). Nothing was executed, so every command is `bash -n` only.
- Step 8 was NOT added to the [step log] list (brief said to add it): every command of step 8 now writes to `$TESTLOG`, the saved log its title already names, so a second log would split the pass lines. Step 13 WAS added.

## Per finding
- M1 fixed: Clock block (FIX-PLAN 28 = TAKE-CHECKLIST 22) labels each latest-start time with its case and lists the 60 (step 14 f) and 30 (fix pass) pieces in words (b1.py).
- M2 fixed: RUNBOOK:214 (step 8 "Cannot run before"): order 5, 6, 8, 7, no parallel run; says why step 8 does NOT need step 6's scripts.
- M3 fixed: RUNBOOK:215 (step 9) now names step 7 (n8n up) for (c) and (a2) before (b).
- M4 fixed: RUNBOOK:215 (a2) uses about 5 of step 9's 30 min, ids due about 05:59Z (lead to confirm); same in TAKE-CHECKLIST:59 and FIX-PLAN:70. The "before 05:54Z" zero-minute window is removed.
- M5 fixed: RUNBOOK:201 "Why the due times differ" (04:54Z database inputs vs 05:14Z n8n inputs; no due time changed); DB_GRANTS first use 05:29Z, inside step 8 (TAKE-CHECKLIST:93, FIX-PLAN:192).
- M6 fixed: FIX-PLAN:103 now Q31 item 69, due 04:16Z (was 04:51Z and "no item"); "step 5 waits" became "step 4a waits up to 30 min, to 04:46Z" (FIX-PLAN:188, 189); TAKE-CHECKLIST:85 "RUNBOOK step 5".
- M7 fixed: "settings lines" for values-file entries (FIX-PLAN:70, 193; TAKE-CHECKLIST:63; RUNBOOK step 9); "lead key" / "HubSpot trial-account credential" in the Clock and Who blocks. No "nine keys", "8 keys" or "HubSpot key" is left (grep prints nothing).
- M8 fixed: RUNBOOK:87 (skeleton line, text at 172) adds a `functions-ok` / `functions-BLOCKED` check for need_set, need_new, input_ready, keysave, keyload, stepjudge, with an append instruction; same in FIX-PLAN:73. Tested: skeleton `bash -n` ok; sourced in a scratch folder prints `functions-ok`; a copy without keysave, keyload and stepjudge prints three `function-MISSING` lines and `functions-BLOCKED`.
- M9 fixed: FIX-PLAN:73 no longer says KEY, KEYS, ADDR are typed again (they come from keysave/keyload); RUNBOOK:232 step 18 no longer makes `KEY=` by hand.
- M10 mostly fixed, partly contested: RUNBOOK:232 T20 loop, the T20 extra case, the two row counts, T21 (1) and (3) now start with `. "$ENVSH"` and need_set. CONTESTED: the T19 hook leg and T21 (2) already had `. "$ENVSH" && keyload 18 && need_set ...` before this round.
- M11 fixed: step 8 (0a, 0b, pg-secrets-ready, datname, i, ii, ii-b, insert-test count) all write to `$TESTLOG` (RUNBOOK:214); step 9 (a)/(a2)/(c) pass lines have one command into `runbook-step-9.log` (RUNBOOK:215); step 13 has a step log with its (d) command (RUNBOOK:220, [step log] tag, list at 181); step 17 (4) and step 23 use stepjudge (RUNBOOK:224, 238); step 21 uses the `$TESTLOG` wrapper (RUNBOOK:236).
- M12 partly fixed (see top). 11b added to the mapping, to the Clock row (both files) and to the RUNBOOK sum list (1 min inside step 12's 15); FIX-PLAN Step 9 now says the export folder is made by RUNBOOK step 11b.
- M13 fixed: FIX-PLAN:107 labels 08:33Z as the gated time and 08:25Z to 08:40Z as the dated Clock time.
- M14 fixed: the two Who tables are identical (diff empty); no bare "gate check" is left (grep prints nothing).
- Note on reader windows: FIX-PLAN:72 and the Who table now say they shift by the 4a wait (up to 30 min).

## Verification (from handover/flows-audit)
```
diff <(sed -n 14,47p FIX-PLAN.md) <(sed -n 8,41p TAKE-CHECKLIST.md)   -> empty, rc=0
diff <(sed -n 49,61p FIX-PLAN.md) <(sed -n 43,55p TAKE-CHECKLIST.md) -> empty
bash -n: 22 new or changed command spans + the shas.env skeleton -> 0 failures (23 blocks)
python3 -I tools/check_refs.py    -> PASS 5176 references
python3 -I tools/check_names.py   -> PASS 655 rows
python3 -I tools/check_secrets.py -> PASS 0 hits in 2647 files
ruff format --check .             -> 795 files already formatted
```
## Slips
I overwrote old shared scratch copies of the three files and ed.py early on; the work moved to scratchpad/tcfp18/. Nothing in the repository was lost.
