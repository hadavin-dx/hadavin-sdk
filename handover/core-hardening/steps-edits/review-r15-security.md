# EDITS r15 security review (egm-design, condensed copy of the inline report), 2026-11-16
Target: EDITS.md round 15 (59 rows, 47 Apply now, 12 Hold). Read-only, nothing run. Verdict: REVISE. 0 blockers, 4 majors, 8 minors. Of 8 r14 findings: 5 closed in text, 2 closed with new defects, 1 not closed (length).

## MAJOR
- F1 `key revoked` is not tied to a time and also counts as the "Are you sure?" confirmation (E-48 key steps C, D, E; E-55; E-58; E-16). A plain status report after any early revoke (alarm 1 at 17:49 UTC = 23:19 IST, or a revoke on Wed 18 Nov) can stand in for `yes, no more takes`, which releases the owner's own deletions. Fix: it counts only when typed after 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 and no `no more takes` was typed; give a separate report word (for example `key gone, no more decisions`); otherwise the assistant asks again.
- F2 CRM contacts can still be deleted by count or "names": input line 112 (step 20) has no row; E-04 and E-42 are on Hold (G1) and end with "made-up names". Fix: Apply-now row for line 112; delete only a contact whose address is exactly take-<id>-a/-b/-c at the example domain for that take id; stop if more than 3 or any other address; contact number is a cross-check only; drop "made-up names".
- F3 The shred rule cannot cover the password file, its nano backups (`<name>~`, `.save`) or the old password file (E-09 e and f against key step G, which allows only (a) key copy in the take folder, (b) the owner's list of key copies, (c) the two item-6 files). `shred done` says nothing about them; the item-1 `rm` leaves n8n.env and the password file in free space. Fix: add part (d) "password files and editor copies made in step 8", listed with full paths; `shred done` includes (d); define the list as "files that hold a secret you saved".
- F4 Contradictory order among `shred done`, the retire check and item 1 (E-16, key step G, E-55, E-59, input lines 125-126). Item 6 (the two files) is part of `shred done` but item 5 (retire check) needs those files and needs items 2 and 3 first; E-16 still says the assistant tells the owner before his own items 2, 4, 5, 6 while item 1 waits for `shred done`. An owner chasing `shred done` can destroy the only check. With key not revoked and shred not done, item 1 still removes the take folder (path to the live key copy). Fix: one numbered order: key revoked; shred (a),(b) = `shred done 1`; items 2, 3; item 5; item 6 = `shred done 2`; `start clean-up`; item 1. Item 1 must not start while the key copy exists and the key is not revoked.

## MINOR
- m1 `<folder>` never stated to be the take folder (E-09, E-16, key step E); the check proves two assistant messages agree, not that the folder is dedicated; clean-up recursion vs "never removes a recording". Add "new and empty, never your home folder"; owner reads the item-1 list; clean-up stops if a video or recording is inside.
- m2 Key step H: the new key is shown before "stop looking". Move `please stop looking` before the click that creates it; say the key is typed in the browser only.
- m3 Bare `ok` as consent (E-11, key step B). Require `ok stand-in test` or `ok flow rehearsal`.
- m4 Time arithmetic: 18:00 + 1:00 typing + 14:20 + 4:00 = 18:19:20 after 18:19; the `end` pause is the person's own time. Only one alarm: add a third at 18:09 UTC = 23:39 IST. Money safe because the key is revoked at 18:19 and the take is killed.
- m5 L-LEN not met: key steps A-K about 3,250 words, E-09 and E-12 about 2,000 more; add a half-page card and move detail to an appendix.
- m6 Route B keeps a live paid key and copy up to five days; from secret handling A is safer; lead decides knowing the exposure.
- m7 Other secret files (app-password files, E-37) have no shred step; add to the F3 list.
- m8 Counts paragraph says "total 56" (47 + 12 = 59) and ids "E-01 to E-58" (file goes to E-61); latest start 18:00 UTC = 23:30 IST vs ORDERS L-23NOV 18:04 UTC = 23:34 IST (confirmation o still open).

## Closed in r15
M3 latest start (arithmetic of the UTC/IST pairs and weekdays checked); m1 alarm vs running take; m2 item-6 shred (but see F4); m3 (but see F3); m5 same-key 30 minutes.

## Not checked
E-01, E-02, E-26 to E-34, E-38, E-49, E-50, E-53 bodies; inputs other than OWNER-STEPS lines 100-129; code, the 860 s figure, click paths, vendor behaviour, shred on this disk; verify scripts; word counts taken from resolve-r15.md.
