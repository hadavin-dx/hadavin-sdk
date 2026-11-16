# fix-fixplan5 (edited FIX-PLAN.md only; static, nothing ran; backup in scratchpad bak-fp6/FIX-PLAN.md)
Failures first: none. Not checked: no script run; take-warns.pin line numbers differ by whether the 3 comment lines are counted, so the fix names the six lines by text.
Verified against files: take-warns.pin has six placeholder WARN lines (mf-form 3 ids, mf-hook 3 ids, mf-recovery 1 value + 7 ids, mf-sub-crm-mail 2 values + 7 ids); flow-check/README.md line 17 names no script; take_check.sh builds the INFO line with sed (text 'run saving is ON') and runs the checker with --quiet-info.
Changes: Step 9 (all six placeholder WARNs may vanish, named by text); Lead fix (3) (README line 17 names no script; n8n_api.py only in ORDERS Q22-5, Q26-3); Step 4 (INFO built by take_check.sh with sed; count 3 unchanged).
Read fix-contra1.md first: it ended with its final report line before I edited. Agents started: 0.
