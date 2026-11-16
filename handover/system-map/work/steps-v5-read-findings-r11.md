# Steps v5 round 11 naive reader findings (a367b2cf037cf3045; money path, uncapped; 468 lines, about 28,000 words)
Reader read only the sheet and r10 findings.
## BLOCKERS
1. The paid model program is never stopped (lines 118, 271, 313, 375, 37). B1 starts "the model program" (the spender). STOP LINE described only as stopping "the run". After a normal end, `n` or a STOP LINE nothing tells the owner to stop the model program, n8n or the database. Step I item 5 stops n8n, run folder and database container, not the model program; item 7 only "close the second window". A live paid key sits behind a running program for days (line 217).
2. Sheet not followable today and the front does not say so (217, 257, 92): run day unnamed; rehearsal result cannot exist so step-A message cannot exist; core plumbing unknown (mail path, STOP LINE, setup lines, secret file names, who types n8n stop); owner asked to track about 60 fills and 36 tick-list rows to find out nothing can start. READ THIS FIRST never says "today you can do nothing but ask". Lead should resolve fills before sending.
## MAJORS
3. Step G item 4 (355) reads as mandatory "NEW risk answer, NEW yes, NEW run name" after any stop; line 345 says only before any retake.
4. B2 and C circular (274, 275, 286): B2 finishes "BEFORE step C" but item 1 sends owner into C items 2 and 3 (demo-take profile, n8n sign-in); B2 items 3-4 need a signed-in browser with no profile named.
5. C and D contradict (285, 286, 296): C item 2 sign in to "only" HubSpot and receiver; C item 3 "if the lead does not ask, do not open n8n"; D item 4 needs the owner to view n8n executions in that profile; table rows proof-screen candidate has no way to view.
6. Destructive lines typed blind (45, 377, 447): `shred -u`, `rm <lock file>`, n8n/database removal; owner cannot spot `-r`, `*`, `~/.hadavin-take-tags`. Suggest a check rule: refuse any line containing `-r`, `*`, `/` or "tags" other than the named secret-folder cd. Also shred on SSD/WSL does not guarantee erasure; line 128 does not say so.
7. Step I defaults still half-conflict (206, 207, 366, 368, 372): row 206 delete nothing in item 2 until list; row 207 / line 368 delete the program's HubSpot key whether or not named. If list never arrives items 4-6 wait, files and keys stay live; nothing says "do item 1 at minimum"; no deadline or owner-side fallback.
8. Notice/prep unplanned loop (311, 312, 318, 176): after prep call paid and `n` typed, "go back to step A" does not say what the new yes says about the paid prep call.
9. What STOP LINE leaves behind partly covered (315, 316, 324): "laptop sleeps" cannot be seen, no action; power cut/crash mid-run no outcome.
10. Tick-list mismatches: row 171 vs line 271 (B1 fill timing); rows 206/207 opposite defaults; no row for "retake allowed" (line 87); row 179 duplicates 168.
11. READ THIS FIRST gaps (5-16): uses STOP LINE, prep call, both written answers, launch undefined in block; line 9 "before you type y type n" says nothing of what prints the y prompt, omits the second prompt (confirmation line); restates fill rules three times (12-16, 141).
12. Step I listing order 5, 6a, 6, 7, 8 but real order 6a, 6, 8, 7 (376-379).
## NITS
Master sentence repeated 3 times (89, 331, 352) [fact reader: 89 is a description, not a copy]. Line 306 "still works" good at launch vs 372 STILL WORKS bad in retire check. Line 123 run lock file beside run folder, step I item 5 never removes lock file. Line 237 and B.5 sleep/lid settings changed until step I (days). Line 255 lead copies stage.env into a message; nothing says no secret in it. "KEY_PREFIX" (342), "hook door" (116) explained in passing. "Outgoing messages" 392 vague.
## Length
Still too long for one sitting (about 28,000 words); cannot be one sitting anyway (H, I, J other days). READ THIS FIRST helps a little but is nine nested rules in about 12 lines. The r10 split (run-day card, after-run sheet, lead-only file) still stands.
## r10 check
B1 mostly fixed (wording conflict remains = M7); B2 fixed but brought M4, M5; M3 fixed; M4 partly (which program stopped open = B1); M5 partly; M6 fixed; M7 half (= M4); M8 fixed in substance, order confusing (M12); M9 mostly; M10 fixed; M11 partly.
Not checked: any other file; click paths; US$189 applies to key; program refuses piped answers; shred on owner file system.
