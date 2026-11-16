# F9 fixer round 1: SCENE-FLOW-MAP.md (static; nothing run in n8n; nothing committed)
Checked against the JSON in n8n-flows-real-v5 and n8n-flows-film-v5 by script this session.
- F1 fixed: Kind C last sentence replaced with the reviewer's wording.
- F2 fixed: verified (recovery has scheduleTrigger, no path). C1 rewritten: deactivate all real-v5 flows, activate film-v5 (or one set per n8n), check no stuck rows before scene 5.
- F3 fixed: scenes 6, 7, 8, 9, 11 now "The n8n flows and the lead table".
- F4 fixed: files show placeholders + credential mf-mail-smtp; throwaway mailbox now "owner confirms in rehearsal / plan-only". Kind A text changed.
- F5 fixed: caveats moved to "Not for the paste" lines (Kind A, Kind B) and the scene 6 check column; scene 2 sentence marked "use only after the real-v5 rehearsal shows done".
- F6 fixed: verified (desk@example.test to alerts@example.test). Scene 5 adds "same alert logic; the alert mail goes to a stand-in mailbox"; label decision written.
- F7 fixed with a correction: OutStage has no outgoing connection; reply verdict is "processing", recovery retries, MarkFailed after attempts reach 3 (no mail sent), then alert. C4 says this.
- F8 fixed: verified DESK_TIMEOUT_MS vs MF_STAGE_TIMEOUT_MS, film CrmUpsert timeout 10000; V5-NODE-DIFF.txt is real-v4 vs real-v5 (verified from the file), stated.
- F9 fixed: note added that VIDEO-RUNSHEET.md scene 4 row and caption (lines 33 and 90) are superseded and must be edited before the take (not edited here).
- F10 fixed: scene 10 says film-v5.
- F11 fixed: scene 11 clause added (451 refusal on the alert mail only).
- F12 fixed: "two words and one phrase".
- F13 fixed: scene 9 title "Alert, no second mail".
- F14 fixed: note that no scene uses mf-hook.json (grep: no scene names it).
Not checked: no run of anything; banned-word grep (one database, approval, audit trail) returned no hits.
