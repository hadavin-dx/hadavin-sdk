# Fix round 25 for RUNSHEET-WORDING.md (RW) and CLAIMS-TABLE.md (CT)
Fixer: one agent. Edited only RW and CT. Not committed. Written Mon 16 Nov 2026.

## Failures and uncertainty first
- No check failed. I did not re-read the whole of RW or CT; I edited by text search and ran the checkers only. The reviewer's unread parts (RW 257-261 and others) stay unread by me too.
- Item 3: the default is now "scene 4 is cut by default and never sped up". RW step 13 already says scene 4 is filmed only if P4a passed; I did not change that, so "cut by default" is the written default of row (u) and a kept scene 4 needs the lead's yes in row (u). The lead must confirm this is what he wants.
- Item 7 and 8 need the lead (proposed Q31 texts below). QUESTIONS.md was NOT edited, so Q31 does not yet hold them (Q31 item counts unchanged).
- Item 6: I chose to name CT as the exception for "window" (CT keeps its own meaning) and added a cross note in CT line "More labels". Both files now say it.
- A-050c: no change; its note already says the video has no unknown-lead or alert scene and it is not spoken by default.

## Finding to result
| # | Finding | Result |
|---|---|---|
| 1 | B-153 drops the unknown branch | Verified (CT B-153 REC says MarkFailed sets unknown when mail_sent). RW row B-153, CT row 64 of the table and CT B-153 now read "state failed (or unknown if the e-mail message may have been sent), then an alert from the alert check". |
| 2 | X-4 says the mail went out | Verified (CT label paragraph: mail_sent means started). New string "The lead table shows the current state, whether the mail step was started and whether the alert was sent." in RW X-4, CT row 37, CT X-4 (and CT's own "Say ..." sentence). |
| 3 | scene 4 default differs | Row (u) default, step 13, N-10 note and N-11b note all say: scene 4 is cut by default and never sped up. N-5a and N-5b need no text change (they already say scene 4 is cut if the takeover does not show); step 13 now names them. |
| 4 | n8n port line | Verified (OWNER-STEPS-q16-rows.md line 268 begins "Ports (decision 6 of 2026-11-16"; line 63 is about times). RW "waiting" paragraph now says line 268. |
| 5 | typed answers "line 91" | Both places now say "the typed answers (defined in the studio owner bullet of 0-words)". |
| 6 | window meaning | RW 0-words end sentence now makes CT the exception for window; CT labels paragraph adds "not the RW meaning" and that the old words "claim window" mean the alert hold. |
| 7 | in frame scenes 2 and 3 | Wording used: "in frame in scene 3 only; Q28 item 2 asked scenes 2 and 3, the lead must confirm". Added to RW A-012 note, RW step 11, CT A-012, CT row 7b note. |
| 8 | fourth human action | Row (o), the open-blocker bullet, the "who the lead is" paragraph and the BLOCKER cell now list a fourth action: arrange the program windows (step 10), refresh the mailbox pane and show it in frame (step 12a (3)), check frames (step 16). |
| small | RW rows not in order | The line above the table now says order is rough, find rows by id (V-11 at R:11 stands before A-005 at R:8). I did not move rows. |
| small | B-150b "a person decides" | Changed to "a person must look at the lead and decide outside the flow" in RW, CT B-150 and CT table row; still a file edit never shown. |

## Proposed Q31 questions (lead to add; QUESTIONS.md not edited)
- New item (item 7): "Q28 item 2 asked that the mailbox count after the wait and the mf_leads row be in frame in scenes 2 and 3. RUNSHEET-WORDING.md writes the wait, the refresh and the frame only in scene 3 (step 12a); scene 2 (step 11) has none. Is scene 3 only enough (A-012 note and CLAIMS-TABLE.md say so for now), or must scene 2 also have a wait and a frame step? Answer by Tue 17 Nov 14:00Z (19:30 IST). If unanswered: scene 3 only."
- Q31 item 100 (extend): "Add a fourth action to the people needed: who arranges the program windows (step 10), refreshes the mailbox pane and shows it in frame (step 12a (3)) and checks the frames (step 16). The lead is a Claude session and cannot do this on the filming screen. If unanswered: no person is named and these steps cannot be done."
- Also for the lead: confirm the item 3 default (scene 4 cut by default and never sped up) in row (u) (that row says the lead adds an item).

## Raw outputs (from flows-audit)
- check_runsheet_paste.py: total rows: 195; RESULT: PASS
- check_rw_ct_pairs.py: paste strings in RW: 140 | found word for word in CT: 140; not found in CT: 0
- claims-count.py: 330 total (SUPPORTED 102, RELAYED-ONLY 64, OVERSTATED 84, UNSUPPORTED 15, UNTRACED 65); lanes A 100, B 226, X 4; offenders: 0; ids 330 unique 330
- check_refs.py: PASS 5171 references
- check_names.py: PASS 655 rows
- check_secrets.py: PASS 0 hits in 2689 files
- ruff format --check .: 837 files already formatted
- Status counts by row id: PASTE 53, HELD 89, DELETE 30, NO PASTE 9, SUPERSEDED 14 (195). No status changed.
