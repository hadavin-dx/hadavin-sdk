# evidence-c11 (BUILDER-ONLY evidence: made by the builder, not by an independent runner; it judges nothing and is not a review)
Date 2026-11-16. Environment: Linux container, bash and dash, stand-in cygpath, stand-in git repositories (round-5 worktree with branch take/nlite-int-r5, round-3 worktree), stand-in Windows tree under /tmp reached through /c and /mnt/c, all commands as the unprivileged user nobody (uid 65534, via setpriv). NOT run: Git Bash, PowerShell, WSL (the WSL-only blocks were run in plain Linux; the "is this WSL" guard was tested only on its negative side), a real n8n, Git for Windows patch, a real round-5 worktree.

## Checksums of the two files of revision 11
- LEAD-CHECKLIST-v5.md sha256 67111574af9b9a3c7551939d6482b89508e360d60472721efb3786db1d69a759
- LEAD-FILL-list-v5.md sha256 da2635db2d7c329169eca1aba285e47fd17fd734908bce20dff3a55c122ee9ca (embedded in A2; unchanged from the value A2 holds: da2635db2d7c3291...)

## Syntax
All 45 bash blocks of the checklist extracted: bash -n and dash -n: pass 45 of 45 (final run after the last edit).

## Plan chain walk (blocks A1 to A6, run for each CHAIN)
- CHAIN 2: sha 39af84aec78b650f, 587 lines; A6 ok counts 24 10 2 1.
- CHAIN 3: sha 515cf4704ebba5bd, 622 lines; A6 ok; A7 marker lines 2,3,4,125,258,275,466,467,620,621.
- CHAIN 4: sha 28f92c5d1211207c, 780 lines (A5b4 printed "written ... 28f92c5d1211207c 780 lines", "failing []"); A6 ok; A7 marker lines 2,3,4,137,270,287,509,510,774,775.

## Full CHAIN 4 walk, then B, C, D (raw lines)
A1 ok; A2 "ok A2: every file checked, proof file written"; A3 ok; A4 ok; A5b ok; A5b4 ok; A5c ok; A8 ok copied; A9 (after changing the plan's guessed user name to the test user, as the lead would by hand) string (1) 1, strings (2)(3) 2, flip ok; B1 accept 3 4 8; B2 "ok B2: outcome A written into PF" with L1_RULED=yes; C1 rows (PIN empty: read only; with PIN: 20 rows); C2 ok (0 placeholders left, 20 table rows open); C2b WSL-1..4 in plain Linux: dash -n ok, stand-in pid printed, exit=0, control file written with one P-4b-HIT line, gone; C2c "P-4b files ok"; C3 brief saved; C4 "rows filled by this run: 20", "open 0", accept 6 ok; C7 "ok C7" (counts 0 0 2 1); C8 "ok C8"; C8b "ok C8b"; C9 wrote the LEAD-GO RE-PIN line with pin and plan=0ce5150278073257 (after a 'P-3a done' line was added to PROGRESS.md by hand).

## New negative cases (each printed the STOP shown, nothing changed unless noted)
- M1 chain proof: CHAIN=4 with only chain 3 built (A5b4 skipped): A6 "STOP A6: the plan checksum is 515cf4704ebba5bd, not the one of CHAIN=4"; A8 "STOP A8: the plan checksum is 515cf4704ebba5bd, not 28f92c5d1211207c". CHAIN=2 on a chain-3 plan: "STOP A6: ... already the plan of CHAIN=3, further than your CHAIN=2".
- A2 with plan-v5-repin-v6.patch hidden: "STOP A2: plan-v5-repin-v6.patch is missing"; no stray sha256sum line; A3 "STOP A3: A2 has not passed for this work folder".
- aside twice on the same folder: .old then .old2; nothing overwritten.
- hbok: quote, dollar, backtick, relative path, "/c/Users/../x", "/c/Users/./x" each STOP VARS (rc=1). Windows form C:\Users\ok\Hadavin is converted and then stops only because the folder is missing.
- B2 with L1_RULED=no: STOP B2; accept 2 with L1_RULED=no: STOP B1 (question 2 open).
- C2 without FINAL5/NAMES_OK: STOP C2. C7 with wrong BR: STOP C7. C5/C6 with an old commit that is in neither worktree: STOP C5 then STOP C6. acc5.sh: ACCEPT only when the kill part holds exit 3 or return 3; otherwise "STOP (no exit 3 or return 3 in kill block)".
- D1b: empty pid, non-digit pid, pid 1 (below 2), pid differs from PIDSAYS, pid not in register, GONE-FAIL line, kill exit=3 line, repeat after a LEAD-YES line: each STOP D1; positive case wrote exactly one LEAD-YES R2 line.
- D1a, D2 blocks (39, 41, 42, 44, 45) in a non-WSL shell: STOP D2/D1 first line, nothing scanned or deleted.

## STOP ids against table E
Script run on the final file: 137 'STOP' echo lines; every one has a Next: except 3 that the regex cut at a nested quote (C7, C8 lines checked by eye: they have Next:) and one real gap (STOP B1 unknown question), which was fixed in the last edit. Every id used is a row of table E (rows group ids: "A3 / A4 / A5b", "B1 / B2", "C2b / C2c", "C5 / C6", "C8b / C9").

## Banned vendor strings
Scan with the BANNED tuple read from tests/test_no_reference_material.py (10 entries): hits in LEAD-CHECKLIST-v5.md 0, LEAD-FILL-list-v5.md 0, v11-OPEN-FOR-LEAD.md 0, (v11-CHANGES.md, evidence-c11.md, checkpoint-v11.md: 0, scanned last).

## What this does NOT prove
Nothing ran in Git Bash, PowerShell, WSL or against real n8n; the positive WSL guard (/proc/version with microsoft) was not exercised; the control file proves only itself (open item N2); the checklist cannot hold its own checksum (N3).
