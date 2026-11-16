# Evidence c11 (independent run). EVIDENCE RUNNER: raw results only, no judgement

Run date 2026-11-16, 12:15 to about 12:35 UTC (17:45 to 18:05 IST). Checklist revision 11: LEAD-CHECKLIST-v5.md and LEAD-FILL-list-v5.md. The builder's evidence-c11.md was not read.

## 0. What was NOT run or is weaker than the real thing (read first)
- Git Bash, PowerShell, real WSL, n8n, Docker: none exist here. Not run.
- Git Bash was replaced by bash in a private chroot, with a stub `cygpath` that turns `C:\...` into `/c/...`. The `/c` and `/mnt/c` folders inside the chroot are bind mounts of my own scratch tree; the host `/c` and `/mnt/c` were not touched. Non-root user (uid 65534) via setpriv.
- WSL for the D blocks was faked by bind-mounting a `/proc/version` that contains "microsoft" (FAKEWSL=1). The D blocks were also run WITHOUT the fake (section 6, T12).
- The "worktree" is a stand-in git repository. The old commit used for C5/C6 is a stand-in commit, not the real old sha. The real round-5 worktree and its real head were not available.
- The n8n process was a python stand-in whose environ is unreadable to its own user. Other-user (different uid) P-4b case: NOT run (inside the chroot I am already non-root and cannot start a process as a second user). The root-session variant (ROOTSESS) was only partly used.
- RAW OUTPUT LOST: the raw outputs of my hostile groups T01 to T07 (chain order, skipped step, symlink paths, metacharacter paths, non-digit pid, A-block variants, p4bcheck/rows variants) were overwritten by later runs because the harness reused one output file. The raw files kept are: positive paths (pos-2/3/4/b), syntax.txt, and T08 to T14 below. T01 to T07 results below come from my session notes, not from kept raw files; treat them as less strong evidence.
- Three cases from my plan were not redone: metacharacter BR/PIN/WTN in C2 through the real block (the first attempt sourced wrongly), `accept '3;echo x'` with quotes, and the PROGRESS.md symlink test before any LEAD-GO line existed (T14 below covers the symlink after a LEAD-GO line).
- The C3 runner brief text is deliberately not copied here (it contains words the repo guard bans).

## 1. Syntax of every bash block
48 blocks extracted (45 checklist, 3 fill-list). `bash -n` and `dash -n` on each: 96 of 96 exit 0 (file syntax.txt, last lines: `LEAD-FIL-03-L45.sh dash rc=0`; `grep -c rc=0` = 96).

## 2. Plan chains rebuilt (positive paths, kept raw files pos-2/3/4)
| chain | expected sha prefix | seen in raw output | lines |
|---|---|---|---|
| 2 | 39af84aec78b650f | seen (2 hits) | 587 expected; the line count is NOT in the kept raw file |
| 3 | 515cf4704ebba5bd | seen (1 hit) | 622 expected; NOT in the kept raw file |
| 4 | 28f92c5d1211207c | `written .../real-v5-plan.md 28f92c5d1211207c 780 lines` | 780 |

All three positive runs printed `ok A2: every file checked, proof file written` and `ok B2: outcome A written into PF`; no STOP in the A..B2 path (grep of STOP/rc=1 gave none in pos-2/3/4).

## 3. Hostile inputs T08 (PIN, branch, flags, old commit, answer text)
Source: the raw log of T08. All rc=0 unless shown.
- C2 with PIN = 7 chars, UPPERCASE 40 hex, 39 chars, 41 chars, 40 `g`, `;id` appended, empty, `HEAD`, branch name: each `STOP C2: PIN is not 40 hex characters`. 
- C2 with PIN = 40 `a` (valid form, no such commit): `STOP C2: PIN is not a commit of <worktree>`.
- C2 with PIN = a real older commit: `STOP C2: the branch take/nlite-int-r5 ... tip is not PIN`.
- C9 with every one of those PIN values: STOP (empty or not a commit, or not the tip of the branch).
- C2 FINAL5=no and NAMES_OK=maybe: `STOP C2: FINAL5 or NAMES_OK is not yes: nothing changed`.
- C2 BR = `main`, `take/nlite-int-r5x`: STOP branch missing or tip not PIN. BR = `take/nlite int`, `$(id)`, empty: `STOP C2: BR has unsafe characters or is empty`.
- C5 OLD empty or `zzzzzzz` or `--all`: STOP (old commit in neither worktree), rc=1.
- C5 OLD = `-h`: git printed its full `git cat-file` usage text (about 30 lines) before the STOP line. The value `-h` reached git as an option.
- C5 OLD = `HEAD`: printed `known` and an empty diff (`== n8n_start.sh`, `== n8n_kill.py`, `== end`), rc=0: no STOP.
- C5 OLD = a real older stand-in commit (7 chars): `known`, then the diff lines for start.sh and kill.py.
- C6 OLD present only in the round-3 stand-in: printed `ACCEPT` and the kill.py diff (the W3 route works).
- C6 OLD in neither: STOP C5 then STOP C6 (do not write the release line). C6 OLD valid but W3 folder path missing: same two STOPs.

## 4. acc5.sh fed directly (T08 tail)
| input to the kill.py part | output |
|---|---|
| `sys.exit(3)` | ACCEPT |
| `exit(3)` | ACCEPT |
| `return 3` | ACCEPT |
| `os._exit(3)` | ACCEPT |
| `print("exit 3")` | ACCEPT |
| `EXIT 3` (upper case) | ACCEPT |
| `sys.exit(4)` | STOP (other exit text) |
| `sys.exit(30)` | STOP (other exit text) |
| `exit 3x` | STOP (other exit text) |
| `# exit 3` | STOP (no exit 3 or return 3) |
| `sys.exit(main())` only | STOP (no exit 3 or return 3) |
| exit 3 only in start.sh | STOP (no exit 3 or return 3 in kill block) |
| `exit 1` in start.sh plus exit 3 in kill.py | STOP (other exit text) |
| missing `== end` | STOP (block missing) |
| empty input | STOP (block missing) |
Raw fact: `print("exit 3")` and `EXIT 3` and `os._exit(3)` are accepted. Every one of these runs ended rc=0, including the STOP ones.

## 5. T09 repeats on a finished chain-4 tree
`repeat` of A3, A4, A5b, A5b4, A6, A7, B1, B2, C2, C4 rows, C4 fill, C7, C8, C8b, A9: each printed its normal text, rc=0, no STOP, no second change (C4 fill: `rows filled by this run: 0`, `rows still open: 0`; A9: `ok A9: marker 9 flipped; left:` with an empty list).
- A8 repeat: `STOP A8: PF exists and differs from the patched plan: it holds your edits` plus `run lines in PROGRESS.md ...: 2`, rc=0.
- C9 repeat: `STOP C9: a LEAD-GO RE-PIN line is already there`. LEAD-GO count in PROGRESS.md stayed 1.
- A5b4 with an existing `real-v5-plan.md` (after the original was moved aside): `STOP A5b4: ... already exists; the script refuses to overwrite`, rc=1.
- A7 repeat printed the list of LEAD-FILL marker lines (17 lines) and no STOP.

## 6. T10 P-4b.sh against other processes (same uid, run under bash and under dash; same result both)
| case | output |
|---|---|
| no other process | empty, rc=0 |
| unreadable `n8n-stand-in` | `P-4b-HIT pid=44` |
| unreadable `N8N-UPPER` | `P-4b-HIT pid=77` |
| unreadable process without n8n in its name | empty |
| unreadable, `x/n8n/y` | `P-4b-HIT pid=143` |
| readable n8n-named process | empty |
| two unreadable stand-ins | two HIT lines (204, 206) |
| after all killed | empty |
All started processes were killed by me and the namespace was torn down. A first attempt used setpriv inside the chroot and failed (`setgroups failed`); that was a harness error, replaced by the run above.

## 7. T11 tamper of checklist inputs, then A2 and A3 (each restored after)
Every case: A2 printed a STOP naming the file, then `A2 is not clean: A3 to A5b4 refuse to run until it is`, rc=0; A3 then printed `STOP A3: A2 has not passed ... (there is no proof file)`, rc=1.
Cases: CR added to patch 1 (`has CR`); one space appended to patch 1 (`not the expected file (checksum)`); patch 1 deleted (`is missing`); original plan plus one byte (`the original plan is not the expected file`); acc5.sh word changed (`checksum`); fill-list text changed (`checksum`). Final A2 plus A3 after restore: rc=0, no STOP.

## 8. T12 D blocks without the fake WSL (non-WSL shell)
D1a, D2a, D2 check, D2 delete with DEL=yes, D2b with HITPID=1: each `STOP D2/D1: this is not the WSL Ubuntu shell`, `Nothing was scanned or deleted`, rc=0. The test folder `~/hadavin-smoke` still existed afterwards (not deleted).

## 9. T13 step 4 and patch tool
- A5b4 with a dangling symlink at the output path: `STOP A5b4: ... already exists; the script refuses to overwrite`, rc=1.
- A5b4 with a python that exits 1: `STOP A5b4: no working Python 3.6 or newer in Git Bash`, rc=1.
- A5b4 normal: wrote 780 lines, sha 28f92c5d1211207c, rc=0. A5b4 again: no output, rc=0.
- With PATH lacking `patch` (git apply fallback): A3 and A4 rc=0 with no text; A5b chain 3: `STOP A5b: the program patch is not installed, or git apply cannot be used safely here`, rc=1. (The A3/A4 silent rc=0 under the fallback was not checked further; my harness moved the work folder aside in that step, so what A3/A4 did there is not established.)

## 10. T14 PROGRESS.md
- PROGRESS.md replaced by a symlink to a file outside the evidence folder, then C9: the LEAD-GO RE-PIN line was written through the symlink into the outside file (`outside file now: LEAD-GO RE-PIN ...`). No warning.
- PROGRESS.md mode 444: `Permission denied`, rc=1, no STOP line.
- PROGRESS.md as a directory: `STOP C9: the last runner line is not 'P-3a done ...'`, rc=0.

## 11. Earlier groups T01 to T07 (from session notes, raw files overwritten; about 120 sub-cases)
Observed in raw output at the time:
- `ok C2` is printed even when PF is missing.
- PF as a symlink, and a symlinked control file or standin-gone.txt, were accepted with no warning.
- `flip` (uses sed -i) replaces a PF symlink with a regular file.
- Many STOP paths exit with rc=0 (only some exit non-zero), so a script that tests rc alone would not see them.
- Wrong chain, skipped step and non-digit or empty pid cases: the STOP lines appeared as expected (not re-verified from kept raw files).
- Harness errors in my own work (not checklist faults): tree owned by root, undefined $W, unrestored PF between cases, block executed instead of sourced. Each fixed and the group rerun, except the three redo items in section 0.

## 12. Cleanup
Every process I started ran in a private pid namespace that ends with each run; I killed the stand-ins with `kill`. Symlinks I made lived in the chroot tmpfs or in my scratch tree. No git command was run against the repository; nothing outside this file and my scratchpad was written; /c and /mnt/c on the host were not touched.
