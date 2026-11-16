Status: resolved (headless, auto accept; fixes applied by the author, not by this skill)

# Goldfish Annotated Review Report, flowcheck round 1
**Target:** flowcheck/REPORT.md (full), tools/flowcheck.py, run_all.sh. Findings: review-design-r1.md, review-codebase-r1.md, evidence-runner.md. All findings are valid; contested 0, escalated 0.

## Majors (all PROPOSE FIX)
1. [design M5] No rung table; "linters do not cover X" unverified. Fix: replace section 2 by a rung table (rung 1 sdk searched with the command, rung 3/4 linters UNVERIFIED not run, rung 5-7 not applicable, verdict KEEP-CODE thin, re-decide after one tool is run on the 16 files); reword "not allowed" to "not tried".
2. [design M2 + codebase nit line 60] Write-path check is a list, line 60 by eye. Fix: script flags any ancestor external call that is continueRegularOutput or alwaysOutputData, and does not list a plain HTTP POST to the desk (Qualify) as a mail or CRM write (writes = emailSend, hubspot, and httpRequest only if its name is CrmUpsert-like: use node-name list in script is hardcoding, so rule: httpRequest counts as a CRM write when its URL parameter contains "crm", case-insensitive); self-test case for the flag; report states the flag result.
3. [design M3] F-002 flag clean in all files. Fix: state it; add a flag "responseNode webhook path: node with default stop (no onError) that is a Postgres, call or HTTP node between the webhook and its first reply", reported as WARN (not fail) so the pristine defect is shown.
4. [design M4 + codebase M4] Patched mf-form: Stored and RunSub still default stop; repeat-key path depends on n8n zero-row output. Fix: add rows to the not-verified item and to the failures list; the new WARN flag shows Stored and RunSub.
5. [codebase M1, M2, M3] Counts: six nodes in mf-recovery; postgres 2/2/5/5; hunk offsets. Fix: exact text from the review.
6. [evidence runner] Crash on `{}` and node without type. Fix: check() reads with .get and turns missing keys into FAIL lines; self-test cases added for both.
7. [design Q3] Section 1 order and plain words (items 2, 3, 4, 5); nothing-fails line moved to "What passed"; item 4 rewritten, flows-go1 comparison saved as evidence (added to run_all.sh).
8. [design M1] Error-settings table not in the report. Fix: embed the real-v5 pristine tables for the four files.

## Nits (PROPOSE FIX, cheap)
121 lines not 150 and what the self-test covers; status line (runner done, evidence by author script and by runner); 32 files built, 16 shown; line 57 add mf-hook and RunSub, Claim "in pristine"; film-v5 recovery reads no $env; run_all.sh header order.txt removed and rm -rf guarded to a path under /tmp; webhook wording in plain words; script header lists checks not done ($node["X"], $items, computed $env, headerAuth without credential, disabled nodes, other trigger types).

## Counts: accepted 8 Majors + 8 Nits; contested 0; escalated 0; declined 0.
Round 2 needed: yes, for items 1, 2, 3 (rung table and the two new flags) and 6 (crash fix); the rest only if round 2 finds a Blocker or Major.
