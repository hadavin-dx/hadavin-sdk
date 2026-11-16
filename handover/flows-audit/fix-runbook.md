# fix-runbook (flows-audit, 2026-11-16 ~12:00Z; 17:30 IST)

## Failures and doubts first
1. The TAKE_CHECK_FLOWS and TAKE_CHECK_WARN_PIN environment-variable command forms in FIX-PLAN item 3, TAKE-CHECKLIST and flow-check/README.md read as exit 4 in take_check.sh (lines 29-36, 60-67, read, not run). RUNBOOK uses --flows DIR and installs the second pin by copying over take-warns.pin (a commit). Not run: "most likely" until step 4 runs.
2. Missing from the tree (find): scripts/n8n_api.py, run_real_check_n8n.py, n8n_drive.py, post-twice script, T19-T21 runner, F-018 loop. Kept as "lead provides".
3. OWNER-STEPS order has import before fill; FIX-PLAN has fill before import. RUNBOOK follows FIX-PLAN.
4. Rehearsal count differs (one in the brief, two in FIX-PLAN steps 11-13). Both kept, flagged.
5. All minute figures are my estimates. Tuesday fits only with no failure (about 50-110 min spare); Wednesday morning fits with about 5 min spare. Nothing can be done today.

## What I did not check
Patches still apply (check_patches.sh not run); generator reproduces real-v5; fill_flows/take_check on the lead's laptop; any n8n screen or port; durations; whether TAKE-CHECKLIST (being rewritten) still has the check names quoted; the FINDINGS F-002 row text (pass lines taken from FIX-PLAN's description, not re-read in FINDINGS.md); ORDERS.md decision numbers.

## Done
Wrote RUNBOOK.md (24 steps, two day-tables, split re-check boxes, two paths, 31 inputs). No other file edited. EGM skipped: read-only static document written on the lead's direct order; no review round run by this agent (lead runs the EGM step). No process, shell or agent started. R-numbers: none read (no bible in this repository).
