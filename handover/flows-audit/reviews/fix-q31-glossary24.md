# fix-q31-glossary24 (Mon 16 Nov 2026)

## Failures and uncertainty first
- Task item (3) lists row 132 for the re-check done time. Row 132 ("practice run") contains NO re-check time, so nothing was changed for that reason. I did add one marker in row 132 for the take-prep message sentence "(L12, L22)", because that sentence says the take-prep message carries the HubSpot scopes ask (same stale reading as rows 161 and 178). Remove it if the lead did not want it.
- Rows 78 (L22), 172 and 180 and the other lines that mention the scopes ask or the 16:00Z time were NOT touched (outside the permitted places). Not searched exhaustively for other stale 09:30Z or Wednesday-scopes wording in lines 1-419 beyond grep for "re-check done", "09:30Z", "HubSpot".
- A plain grep for `\[OPEN` over the Q31 section gives 108, not 105, because some items mention the label in their text. The line-start grep gives the true counts (below). Row text now says to count line-start labels.
- All new wording is marked AUDIT PROPOSAL, lead to confirm; no lead choice was decided. Facts re-read from the file: RUNBOOK.md line 97 (KEEP="$HOME/keep"), line 124 (VALUES="$KEEP/flow-values.env"), TAKE-CHECKLIST.md line 145 (`$VALUES`), Q31 item 61.

## Counts (raw)
Labels at line start in lines 420-end: 113 = 105 OPEN + 6 NOTE (41, 42, 44, 45, 46, 66) + 2 ANSWERED (20, 43). Main list = numbers 1-39 and 47-112 = 105 items (103 OPEN, 1 ANSWERED, 1 NOTE); second list 40-46 (1 OPEN, 1 ANSWERED, 5 NOTE); 15A OPEN. Open in all 103+1+1 = 105.

## Row table
| Line | Old | New |
|---|---|---|
| 40 (status row Q31) | 101 items in main list (1-39, 47-108), 99 OPEN, 109 labelled, 101 OPEN, "99+1+1=101" | 105 items (1-39, 47-112), 103 OPEN, 113 labelled = 105 OPEN + 6 NOTE + 2 ANSWERED, "103+1+1=105"; marker PARTLY SUPERSEDED; history kept, with a note that "now gives" in it means the older time |
| 42 (LEAD-ACTION COUNT paragraph) | same old counts | same new counts as line 40 |
| 112 | "missing: GO or NO-GO" = owner's reply at 16:00Z if no message | old sentence kept; marker added: lead's deadline 15:00Z, only a one-line "read" reply counts, "missing: ..." counts as no reply, GO not sent by 15:00Z is NO-GO, GO without "read" by 16:00Z is NO-GO (Q31 item 6 (b), front page) |
| 130 | "re-check done" planned 09:30Z | planned 09:43Z (15:13 IST); 09:30Z only if the Tuesday positive control is dropped (Q31 item 6 (a)) |
| 132 | take-prep message (L12, L22) | marker: L22 scopes ask goes Monday night (items 27, 30); message carries ceiling only. (No re-check time present in this row.) |
| 161 | scopes asked in take prep (L22), "ceiling and scopes question asked only after T19-T21", message part "L12 ceiling, L22 scopes question" | three markers: scopes ask Mon night (answer by 21:00Z = 02:30 IST Tue, item 27; item 30 by 20:30Z), refusal/silence = "not confirmed", nothing blocked; take-prep message no longer carries it |
| 163 | name and place not given, "Q31 item 14 (d), no default: step 9 waits, then does not run" | name flow-values.env in $KEEP is a written proposal (RUNBOOK section 4, TAKE-CHECKLIST `$VALUES`, item 61 = five values); STILL OPEN: real path of $KEEP and the five values; no default; step 9 waits then does not run; NO-GO at 14:00Z |
| 178 | message states ceiling and asks the scopes question | marker: scopes asked Monday night under the default, message states ceiling only |
| 184 | "re-check done" planned 09:30Z (15:00 IST); owner treats Wed 18 Nov as NO-GO if none by 14:00Z | planned 09:43Z (15:13 IST), 09:30Z only if the positive control is dropped; NO-GO sentence read as the lead's own result (only the lead rules NO-GO, item 93), kept or dropped by the lead with item 6 (a) |

## Raw outputs
- `diff` of changed line numbers: 40c40 42c42 112c112 130c130 132c132 161c161 163c163 178c178 184c184 (no other line).
- Q31 section (line 420 to end) compared with the saved copy (`diff` of `awk 'NR>=420'` of both): EMPTY (identical; `cmp` says identical). Total lines 720 before and after.
- `python3 -I tools/check_refs.py`: PASS 5175 references
- `python3 -I tools/check_names.py`: PASS 655 rows
- `python3 -I tools/check_secrets.py`: PASS 0 hits in 2705 files
- `ruff format --check .`: 853 files already formatted
- Recount: `awk 'NR>=420' QUESTIONS.md | grep -E "^(- )?[0-9]+[A-Z]?\. \[" | wc -l` = 113
- Original copy: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/Q.orig. Not committed.
