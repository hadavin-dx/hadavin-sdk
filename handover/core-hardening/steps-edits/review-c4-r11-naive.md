# EDITS r11 naive-reader review (egm-comprehension, condensed copy of the inline report), 2026-11-16
Target: EDITS.md rows E-09, E-11, E-12, E-16, E-37, E-48, E-52, E-57, E-58 (read as the owner who has never seen the project). Verdict: 2 blockers, 9 majors, many minors. The reader could not check code or command behaviour.

## BLOCKERS
- B1 E-09 step f: the owner cannot type "the SAME password" into n8n later: he typed it once in nano; nothing says how to see it again (reopen with nano) or which n8n field takes it; the clipboard is never connected to step f.
- B2 E-48 and E-57 conflict: revoke the model key "right after the last take you accept" and "in every case by 18:19 UTC = 23:49 IST" (E-48) vs revoke "only when no retake (step 20) is wanted" (E-57), while the watch that decides a retake can come after 18:19. "Last take that you accept" is undefined on a Wed 18 Nov take; "accept" and "cut" mean two things (take, video edit). State the order: watch the cut first, revoke at the latest 18:19.

## MAJOR
- M1 E-12: the content of the request for the yes is listed twice (old v3 sentence with money figures, E-12 list without them); `<X>` (3 times the worst case) appears only in the old sentence; old words "the lead", "window end" remain. Merge.
- M2 E-12 reply form `evidence <evidence file>` ambiguous: up to three kinds of evidence; "three file names" but the request may give two evidence files.
- M3 "studio lead", "exit code", "final code", "finding" undefined in owner text; the 23 Nov paragraph is one 200-word block.
- M4 E-37 "NOT SETTLED whether the take deletes" vs v3 steps 17-18 still say "archived"; "call" has three meanings: use "delete request".
- M5 Undefined: container, Docker volume, database server, wipe, shred (explained far below); E-16 is one 300-word sentence asking a decision without its consequence.
- M6 WSL window / WSL terminal / screen used for the same or different things; E-52 defines "screen" and "window" but step 17 and E-09 still use "on screen", "WSL window".
- M7 Reply forms inconsistent (long form; exactly `Yes, remove the container only` / `No`; lowercase yes / `no, other things use it`; "not looking" / "you may look again"; ok / no); case, backticks and `not sure` not stated.
- M8 E-12 fact 1 has no word for a check that ran and showed a bad result; crash check "not run" has no slot; owner not told a failed check is a "no".
- M9 E-48 overloaded (model-key question, timing, shred, "take still running at 18:19", older keys inside "delete BOTH HubSpot private apps"); the 18 Nov plan has no stated deadlines; E-58 screenshot row unconditional though no screenshot on `no` / `not sure`.

## MINOR (grouped)
E-09: step c refers to a password not yet created (step g); step e asks a path the owner must compose; Start-menu path unchecked; umask applies to one window only; "assistant creates n8n.env, never opens it" may be misread. E-37: "private apps", `hadavin_label`, "read-only one of step 7, app 1" unexplained; model-key reply words only in E-48; take id rule UNVERIFIED and whether a new id or a retake needs a new yes is silent. "Check" means many things; "count screen", "journal", "spend record", "stage settings file" unexplained; E-11 "ok" needs the real key file path (not given); E-52 names plan-wp6-resmoke-v5.md the owner may not have; personal Windows paths in v3.

## Could not check
Rows E-01..E-08, E-17..E-36, most of E-38+ (except E-37..39, E-40..47 partly), the "Lines checked" tail, rest of v3, AGENT-SCOPE, DECISION-one-store, plan, ORDERS; whether nano/umask/chmod behave as written; 56/44 counts.
