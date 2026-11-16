# v10-CHANGES (revision 10 of LEAD-CHECKLIST-v5.md and LEAD-FILL-list-v5.md; file names unchanged)

Date 2026-11-16 (UTC). Builder: sub-agent. Nothing committed or pushed.

## Failures and gaps first
- Nothing ran in Git Bash, WSL or PowerShell. All tests ran on Linux bash on scratch copies with made-up data; cygpath is a stub (raw output: `evidence-c7h.md`).
- The review ids of the stranger and adversarial reviews were not all readable as one id list, so the table below is keyed by the brief's must-do letters (a) to (r) plus the citation-check ids (F1 to F7) and the evidence-chain-r2 ids (F1, F2).
- The apply script's own defects (damaged RENUMBER line not refused; dangling-symlink output written through) are not mine to fix: listed in `v10-OPEN-FOR-LEAD.md`. The checklist's step4 guards the symlink case and the checksum catches the damaged line.
- Four small bugs were found by my own tests and fixed in the same pass: (1) C9 printed the wrong STOP on a second release (check order); (2) the D2 process scan printed a redirect error for a vanished process; (3) C7 showed the first three bytes as a confusing number (now labelled hex); (4) SP note text claimed a placeholder was refused by the block (it is refused by the shell).

## What changed, per finding
| id | change | where | how checked |
|---|---|---|---|
| (a) CR / autocrlf | section 0b: set autocrlf false before getting files, how files reach the laptop, CR check of acc5.sh in A2 | 0b, A2 | evidence 3 (N7 CR in a patch: STOP A2) |
| (b) no dash in Git Bash | optional with a visible NOTE line; C9 does not depend on it | C2c, C9 | evidence 2.x (C2c with dash missing: NOTE, not STOP) |
| (c) one HB form | HB is the Git Bash form only; norm, flip, HBW in quotes, spaces handled | 1, 0 | evidence 2.x (block 19 HBW); norm only on strings |
| (d) exact control file command and folder for every K step | WSL-1 to WSL-4 name folder and command | WSL-1..4 | evidence 2.x WSL blocks as uid 65534 |
| (e) missing patch tool | CHAIN becomes 2, git apply fallback for steps 1 and 2 only | A0, A3, A4, A5b | evidence 3 (N3 fallback ok; N4 STOP for CHAIN 3) |
| (f) re-runs | "already applied" detected by sha, never says to discard good work | A3, A4, A5b, A5b4 | evidence 2.x re-run blocks |
| (g) CHAIN left empty | empty is a STOP; plain-words basis for 2, 3, 4 | A0, E table | evidence 3 (N1) |
| (h) one STOP meaning, one E table | table E has a row for every printed STOP id (checked by script) | 0, E | script compared printed ids with table rows: only combined rows differ (C5/C6, C8b/C9, C2b/C2c) |
| (i) C7 and C4 | C7 STOP names each fix; C4 empty field and FILE-MISSING continue | C4, C7 | evidence 2.x C7 negatives |
| (j) C2b | step 2 does not overwrite a customised P-4b.sh; says where the answer text of LEAD-FILL 1 and 1b goes | C2b | evidence 2.x (C2b(2) re-run refuses) |
| (k) runner and builder | how to start the runner, reach the builder, BP path, no empty angle brackets | C3 | evidence 2.x (C3, bad BP) |
| (l) C5/C6 | STOP if W3 is missing or git show fails | C5, C6 | evidence 2.x (W3 missing, OLD nowhere) |
| (m) D2 | never deletes under a live process, one block per action, person to ask named | D2 | evidence 2.x (alive fake process: refused; nothing alive: deleted) |
| (n) C9 | release also calls pinok, needs C6 ACCEPT proof, C2c ok, stand-in gone proof, last runner line `P-3a done`; PIN must equal branch tip; `accept` refuses markers 1, 1b, 6, 9 without the check | C9, accept | evidence 2.x (six refusals plus success; second release refused) |
| (o) LEAD-FILL line 9 and question 2 | owner clause removed; question 2 is open ruling L1; `accept 2` needs `L1_RULED=yes` | fill list, B1 | evidence 2.x (accept 2 refused until ruled) |
| (p) false "word for word" and "tested" claims | only the first marker grep and the four C7 count patterns are word for word; ROWS, C5/C6, C8 stated as the checklist's own text; no "tested" claim beyond evidence-c7h.md | 3 | read-through; evidence-c7h.md |
| (q) undefined terms | Q18 item 2, proposal 3, R5, round-5 builder, tar, take/ctl, gate rows, v9/v10 defined or removed; "step" disambiguated | glossary, fill list | read-through only (no command) |
| (r) stale PLAN-CHAIN.md references | not edited; listed | v10-OPEN-FOR-LEAD.md | n/a |
| citation F1 to F7, F10, F11 | chain shas, per-CHAIN marker lines and A6 counts recomputed from rebuilt plans c2, c3, c4; CHAIN-specific table for C2/A7/D2/glossary lines | A0 table | A6 and A7 blocks ran per CHAIN |
| evidence-chain-r2 F1, F2 | CHAIN=4 marker lines and the A6 sha `28f92c5d1211207c` corrected | A6, A7 | evidence 2.4 |
| evidence-chain-r2 F3, F4 | not mine (script); checklist guards: sha check, symlink check | A5b4 | evidence 3 (N5, N5b) |

## Files written
`LEAD-CHECKLIST-v5.md`, `LEAD-FILL-list-v5.md` (edited in place), `evidence-c7h.md`, `checkpoint-v10.md`, `v10-CHANGES.md`, `v10-OPEN-FOR-LEAD.md`.
