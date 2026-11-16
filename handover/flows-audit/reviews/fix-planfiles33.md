# fix-planfiles33: round 33 fixes to RUNBOOK.md, FIX-PLAN.md, TAKE-CHECKLIST.md

Static review. Nothing ran in n8n, Postgres or HubSpot. Made-up data only. Not committed.

## What failed, what is uncertain, what was not checked (first)

- No block chain was run. `bash -n` (syntax read only, not run) was applied to 25 code fences of TAKE-CHECKLIST.md: 0 syntax errors. The chains in RUNBOOK.md and FIX-PLAN.md (inline backticks) got no `bash -n`.
- Run in a scratch folder: the python receipt program of Blocks P1b/P2b and the `--check-reviewer-line` helper of take_check.sh. Nothing else.
- NOT done in full: M12 split. Steps 16 and 17 of RUNBOOK.md were split by a mechanical rule into 12 and 16 numbered parts (`**16.1**` ... `**17.16**`, `<br>` between parts; content unchanged). Parts are still long where one sentence holds a long bracket (largest: 1,802 and 3,436 characters). A real rewrite into short sub-steps was not done. The 35 review-history paragraphs of RUNBOOK.md before section 5 were not moved (reader said they hold live rules; moving them risks losing rules). Next step: the lead decides whether to restructure.
- NOT done: bare "step" fixed only in FIX-PLAN lines the reader named (107, 109, 112). A full sweep of every bare "step N" in the three files was not done. "lead ID" in FIX-PLAN line 122 is inside a proposed video sentence; left unchanged so the wording check stays true.
- IST sweep is mechanical (regex over all prose outside code fences, 498 insertions); I read only a sample. Times at or after 18:30 UTC would roll to the next day and were skipped on purpose. Times inside code fences got no IST.
- The check scripts do not test any of this prose; they passed, which proves only that references, names, secrets and counts still hold.

## Contested

- Brief: use `"$REPO/$RUNSHEET"`. RUNBOOK.md section 4 sets `RUNSHEET="$REPO/handover/demo/VIDEO-RUNSHEET.md"` (a full path) and every command uses `"$RUNSHEET"`. `"$REPO/$RUNSHEET"` would double the path. I kept `"$RUNSHEET"` and fixed the TAKE-CHECKLIST row that said "relative to `$REPO`".

## Fixed

Shell reviewer (B1, M1 to M4):
- B1: Blocks P1b/P2b take a 4th argument `PIN_RECEIPT` and refuse unless it is 8 lower-case hex and equals the first 8 characters of the pin's own sha256 line. Reviewer line is `# reviewed by: NAME, YYYY-MM-DD, pin sha256 XXXXXXXX`. Updated in TAKE-CHECKLIST (procedure, P1a/P1b/P2b text, Inputs item, placeholder and example rows, check 11), RUNBOOK (pin definition, header, 4b (a)(c), 13 (d), I36) and FIX-PLAN step 4.
- `-v ON_ERROR_STOP=1` on psql (TAKE-CHECKLIST check 2, RUNBOOK step 8 (ii), FIX-PLAN item 97) with pass word `table-file-run` inside the chain.
- `need_set`, `test -d`, `test -s` before greps (checks 3B, 7, R2, R2j, R6j, R7j, P2c pre-look, R6 ledger paths); echo inside the chain so a refused guard never prints a pass form; R3 absolute EVLOG, clean-tree markers; new R3c; R4r says paste the WHOLE Block R4; FIX-PLAN item 98 uses `$FILLED`; R6 sanity (expect rows=45, flagged=45; checked against LEDGER-ROWS.md) and ledger_check use; pin-2 `test -s`.
- FIX-PLAN 73 (4): `shas.env` chain now refuses when REPO or TAKE_FOLDER is empty, when the file exists, or when the RUNBOOK marker line is missing; checks the result is non-empty before `chmod`.

Reader reviewer (M1 to M12):
- Start-state gate (b) now includes `alert_sent` and unknown/failed rows (checked against mf_leads.sql line 16): TAKE-CHECKLIST check 2, RUNBOOK step 24 (b), FIX-PLAN item 109.
- M4: Block R7 Part A now also greps `one postgres`, `one db`, `same database`, `1 database`; a written rule says any hit in the two viewer files fails unless fix A passed with evidence named (FIX-PLAN 8b points to it).
- M6: T19 reply bound renamed "T19 reply limit (10 s, PROVISIONAL)"; text says it is not the recovery-off seconds N (RUNBOOK, TAKE-CHECKLIST, FIX-PLAN).
- M7: new paragraph at the top of RUNBOOK section 10: one due time per input, items (a) to (e), earlier time governs.
- M8: RUNBOOK N5 and section 8 now say plainly the two lead rules (re-pin ends 07:00Z, take starts by 12:00Z) cannot both hold; the operator follows 06:53Z (12:23 IST) until the lead answers. FIX-PLAN line 1 and TAKE-CHECKLIST item 17 text match.
- M9: one rule for gate (e) (try the search first; NOT CHECKED only if refused; repeat at RUNBOOK step 19) in FIX-PLAN 109; Row 4 (d) allowance in RUNBOOK and TAKE-CHECKLIST.
- M10: "made-up lead" to "made-up contact", "lead IDs" to "lead keys" in FIX-PLAN; "retake gate" to "start-state gate of the retake"; bare steps in FIX-PLAN 107/109/112 given file names; `$TAKE_TREE` row now fixed (`$TAKE_FOLDER/take-tree`); `$RUNSHEET` row.
- M11: IST added after UTC times (see caveat above); Clock blocks of FIX-PLAN and TAKE-CHECKLIST (first 49 lines) compared equal after the sweep.
- M12 (part): FINAL_SHA timing stated plainly in RUNBOOK section 8 (5) and FIX-PLAN step R3; steps 16 and 17 split (see above).

## Outputs (run from handover/flows-audit)

```
check_refs.py            PASS 5178 references
check_names.py           PASS 655 rows
check_secrets.py         PASS 0 hits in 2739 files
check_counts.py          PASS 52 files / 655 nodes
check_runsheet_paste.py  RESULT: PASS
ruff format --check .    886 files already formatted
bash -n (read, not run)  25 TAKE-CHECKLIST code fences, 0 errors
```

## Question lines for QUESTIONS.md

1. NO-GO re-pin: Q27 item 6 (re-pin ends Mon 23 Nov 07:00Z, 12:30 IST) and Q27 item 7 (take starts by 12:00Z, 17:30 IST) cannot both hold (the chain is 307 min). Which rule gives way? Until you answer, the files say 06:53Z (12:23 IST).
2. Due times: confirm RUNBOOK section 10 "Round 33, M7" items (a) to (e) (one due time per input, the earlier one).
3. When does RUNBOOK step 1 really start, given FINAL_SHA exists only after merges and Block R3 (run time unmeasured)? Who measures R3?
4. Row 4 (d): is "PASS ON (a) TO (c) ONLY" with (d) due before rehearsal the rule you want when the HubSpot scope answer is not in yet?
5. Is "same lead ID sent twice" (FIX-PLAN line 122, proposed video sentence) to be reworded to "contact" or "lead key"?
