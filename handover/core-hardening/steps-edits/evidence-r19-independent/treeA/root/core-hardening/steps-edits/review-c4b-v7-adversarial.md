# C4b v7 adversarial take-day reader (condensed copy of hand-back, ac07992f), 2026-11-16
Read-only; ran nothing; read the whole v7 sheet, no review files. Limits: typed-ahead keystrokes read as wrong `end` lines is plausible but UNVERIFIED; exit code for "C unknown" unknown; whether stage.env holds a key unchecked; run card/rehearsal file/lead messages do not exist yet. Dates/UTC-IST arithmetic consistent.
BLOCKER 1 (L48,88,215,216,223): keystrokes during the run (n8n restart line typed in the run window; `echo $?` row E.5 listed before F) become wrong `end` answers and delete contacts before filming. Fix: n8n line only in a second Ubuntu window; never type in the run window except y, number+name, end; `echo $?` only after the `$` prompt returns; move E.5 after F.
BLOCKER 2 (L80,128,197,7,175): E.0 "receiver and sender are throwaway" is a sentence with nothing to check and omits HubSpot. Fix: a real check (open demo-take Gmail, confirm account name; lead names first 3 letters of sender), extend sentence to HubSpot test account, same before step 0.
MAJOR 3 (L199-203,210): `y` can be typed before the comparison; add "do not type y until checked", positive check that run name is the owner's.
MAJOR 4 (L119,158,206): money check misses money already spent; add "spent so far + this total > backstop = answer no"; add step 0 "delete works" to the list in A.
MAJOR 5 (L158,206,176): cat of stage.env and showing connection value (C.3) can expose a secret on camera/scrollback; do cat before recording; better the lead sends the 3 values; after C.3 close the window, overwrite clipboard, confirm recording off.
MAJOR 6 (L56,174,175,179,190,259): blank card row 13 turns safety checks off; still do C.1, C.2, D; skip only optional I.3, I.7; state what G is.
MAJOR 7 (L48,211,223): row 5 "you type nothing during the run" contradicts y/number/end; no named n8n restart person = do not start.
MAJOR 8 (L232-233,247,248,258): destructive clean-up never says which account/browser profile; work only in demo-take; confirm account name before each delete and before emptying Trash.
MAJOR 9 (L15,88,223,294-297): pass/fail unclear; after any non-zero exit do nothing, send number and last line, delete nothing; state C unknown exit code; F "anything other than 2 or 3".
MAJOR 10 (L211-213,235,305): retry after refusal unclear; exit 1/2 = do not rerun, tell lead; type number by hand.
MAJOR 11 (L247-250): I.2 screenshots can show portal name/id/emails; crop before saving.
MAJOR 12 (L197,80,174,179): E.1 have-ready list leaves out C.1, D, step 0 answered, rehearsal passed, lead reply to E.0.
MAJOR 13 (L80,197): wait for the lead's E.0 reply before the start command.
NIT 14 step 0: 0 does not mean delete works; scan for `@`; key shown => delete the private app. NIT 15 cd line form, checksum first/last 8 chars, where the delay is set. NIT 16 shred: full paths, ls -l first, kept HubSpot key file in refusal list, drop "cancelled by you" contradiction. NIT 17 alert mail place, run-name search matches old runs, "remove only the named" app passwords, rehearsal pass = open file read first line, stop time vs retry.
Note (lead-me): all findings are about v7; v8 was built from reviews of v7 and may already fix some (B1 security, step 0, shred full paths). To fold into v9 after v8 reviews land.
