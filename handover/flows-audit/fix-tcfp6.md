# fix-tcfp6: TAKE-CHECKLIST.md / FIX-PLAN.md readiness round 5 (fixer log)

Static edit only. Nothing was run in n8n, no psql, no pytest. Backup of both files before the edit: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-tcfp6/. Findings: reviews/round-12z-findings.md, section "TAKE-CHECKLIST.md / FIX-PLAN.md readiness round 5".

## Verification of each finding before the edit (against text, not memory)
- B1: confirmed. take_check.sh, function `reviewer_ok` (read): needs `NAME, YYYY-MM-DD[, note]`, NAME at least 3 letters from letters, spaces, dots, apostrophes, hyphens, stand-in words rejected as whole words (tbd todo name placeholder unknown nobody someone anonymous claude agent session bot assistant gpt model lead person xxx abc), date real and not in the future. The committed pin line 2 reads "flows-audit session ... lead to confirm": rejected.
- M1 to M8, N2 to N4: confirmed by reading the two files.
- N1: confirmed against ORDERS.md: the heading line is one before the answer text (Q13 heading 109, text 110; Q16 112/113; Q20 text 125; Q21 131/132; Q22 134/135; Q22 follow-up 137/138; Q23-Q24 140/141; Q25 143/144; Q26 146/147; Q27 155/156; NOTE 159/160; Q28 text 166; Q29 text 167; Q30 heading 169, correction 170, text 171). All single cites moved to the text line; ranges that hold heading and text were kept.
- N5: confirmed: "decision 4" appears in take_check.sh in the header comment, in the exit-4 test of the ACCEPTED line and in its message, and in check_flows.py in the constant SAVE_ACCEPT_REASON (searched by text; no line numbers used).
- N6: the check_flows.py half is now read (the constant, found by search), not assumed. Not checked: whether any test script pins that text.

## Changes
- Inputs item 14 and new check 11 item 6 and new Pin procedure section (steps 1 to 6) carry B1 and M6, M8. Reviewer grammar quoted. Marked "planned by the audit, lead to confirm".
- Placeholder table: new rows `$KEYS`, `$FINAL_SHA`, `$BODY`/`$HOOK_URL`/`$POSTLOG`, `$PIN_REVIEWER`; `$REPO` and `$LOG` rows reworded; all bracket markers removed except the documented `<new folder>`.
- GO rows 1, 3, 5, 7 and the honest-limit paragraph rewritten (M1, M2, M7, N2); check 1 pass cell shortened and its pin procedure moved (M8, N4); check 2 and check 7 commands made runnable and non-vacuous (M4, N3); FIX-PLAN steps 1, 2, 3, 4, 5, 9, 14 and item 8b adjusted (M3 to M6, N5).

## Question text for the lead (for QUESTIONS.md; this fixer did not edit QUESTIONS.md)
Q-PIN: The take check reads a reviewer line in `flow-check/take-warns.pin` that must be `# reviewed by: NAME, YYYY-MM-DD` with a human's name and a real date; an agent's or session's name is rejected, so the lead cannot sign it. The audit proposes that the owner (or another named human he picks) reads the WARN lines of the pin before the re-pin check on Tue 17 Nov about 08:00Z (13:30 IST) and tells the lead the line to write. Does the owner agree to read the lines, or whom does he name? Planned by the audit, lead to confirm. Until a human's name is on the line, take_check.sh exits 4 and GO row 4 cannot pass.

## LEAD FILLS rows added or changed (all planned by the audit, lead to confirm)
| Item | Proposal | Where |
|---|---|---|
| Reviewer of the pin | the owner or another named human reads the WARN lines; value `$PIN_REVIEWER` | Inputs item 14; check 11 item 6; Pin procedure step 4 |
| Final evidence head | `$FINAL_SHA` = head of `$BRANCH`; two shas (evidence, patch) | GO row 3 |
| Post-twice fallback | stored-body curl loop with `$BODY`, `$HOOK_URL`, `$POSTLOG` | GO row 5 (e) |
| Fallback for rows with no runnable pass | read as NOT PASSED at 14:00Z; the lead owns the missing item | honest-limit paragraph |
| Patch branch base | `$PATCH_BRANCH` is created from `$BRANCH` | FIX-PLAN step 1 |

## Not checked
Nothing was run: no command written here was executed. Whether the pin sha256 equals a regenerated copy was not checked. Whether test scripts pin the text "decision 4" was not searched beyond flow-check file names. The curl fallback's content type is a guess for the lead to confirm.
