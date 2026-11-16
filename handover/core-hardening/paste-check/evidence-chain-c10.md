# evidence-chain-c10.md (EVIDENCE RUNNER, independent; raw output, no verdicts on quality)
Run 2026-11-16 on Linux 6.18 container, bash 5.2, dash, GNU patch, git, Python 3 (/usr/local). Scratch /tmp/c10ev (removed at the end). Blocks ran as uid 65534 (not root) against stand-in folders (`/c/Users/lead/...` symlinked to scratch), a stand-in `cygpath`, stand-in git repositories for the scripts under test (made-up 20-row strings.txt from the plan's section 11 table), a runner emulated by appending lines to PROGRESS.md by hand. NOT RUN: see section 0.

## 0. NOT RUN (read first)
- Git Bash on Windows, PowerShell, real WSL Ubuntu (WSL-1..4 ran on this Linux kernel as uid 65534; a different kernel from WSL), real `cygpath` (stub: `/c/x` -> `C:\x` and `C:/x`), Git for Windows `patch`, the Windows Store python stub, `core.autocrlf` effects on a real clone or zip (block 1 only set and printed the config in a scratch HOME).
- A real n8n, a real runner agent (C3 only wrote and printed the brief; the "runner" lines were typed into PROGRESS.md by me), a real `strings.txt` from P-3a, the real scripts under test (stand-in files; ROWS counts and C5/C6 diff words are from stand-ins), the real stand-in on WSL, real `P-4b.control.txt` made by the lead.
- A5 claim "work folder inside a git repository: git apply may skip files": not run.
- D1 reading `$HOME/hadavin-smoke/take-smoke-1/n8n.pid` and the register file: not run (names only grep-checked in the plan).
- Message wording of D2 (4a)/(4b) to the runner: not run (text only).
- Doc claim "evidence-c7h.md 2.x/3 ids": only the ids N1, N3, N4, N5, N5b, N7 were found by grep; their content was not re-judged.
- Not tested: plan steps of the run itself (P-1 onward).

## 1. Hashes of the targets (as briefed)
LEAD-CHECKLIST-v5.md sha256 95f393ae9b5b00322c911aeafa341149642e3d632efc6bedead029f865fa975f (starts 95f393ae9b5b0032: SAME), 327 lines
LEAD-FILL-list-v5.md  sha256 4ee9ced312e54fcc3c21a3384848925d1311b0e66fcfe20224c8ef5122b6ead3 (starts 4ee9ced312e54fcc: SAME), 52 lines

## 2. Bash blocks (item 1)
42 fenced bash blocks extracted (markdown lines listed below); `bash -n` rc 0 for 42 of 42; `dash -n` rc 0 for 42 of 42 (dash 0.5 here). The proposal script of LEAD-FILL-list-v5.md (`#!/bin/bash` .. `exit 0`): bash -n and dash -n rc 0.
Builder's claim "42 of 42": MATCHES.
Block numbers used below (b01..b42, in file order): 1 autocrlf, 2 section 1, 3 A1, 4 A2, 5 A3, 6 A4, 7 A5b, 8 A5b4, 9 A5c, 10 A6, 11 A7, 12 A8, 13 A9 check, 14 A9 flip, 15 B1, 16 C1, 17 C2, 18 C2b(1), 19 C2b(2), 20 HBW, 21 WSL-1, 22 WSL-2, 23 WSL-3, 24 SP note, 25 WSL-4, 26 C2c, 27 C3, 28 C3b, 29 C4 rows, 30 C4 fill, 31 C5, 32 C6, 33 C7, 34 C8, 35 C8b, 36 C9, 37 D1, 38 D2(1), 39 D2(2), 40 D2(2b), 41 D2-check, 42 D2-delete.

## 3. Rebuild of the plan chain (item 2), scratch copies, GNU patch -p1
| chain step | sha256 (full) | lines | checklist says |
|---|---|---|---|
| original | 67a0a195537de8754ef80bd3bd8d8a4d78a507ca8418bec8f835a0e99abb41f1 | - | same |
| 1 patch 1 | 53f1670383a2c728c4bdbb560f5444766aa0df773ac6f85a4c6496aca1bb1c2a | 561 | same (PLAN-CHAIN.md: 561) |
| 2 patch 2 | 39af84aec78b650f287d20013cdfa2d45dde8b75632e6d6729660bbc21ce3f5b | 587 | 587 |
| 3 patch 3 | 515cf4704ebba5bdc00e3c2ab9fdce7f65a2a7b8467ceec0bf0942b7e21a7e45 (patch said "Hunk #1 succeeded at 3 with fuzz 2") | 622 | 622 |
| 4 apply-v10-after-chain.py | 28f92c5d1211207cce0222c87bb7a6e6dc8e39a21a659624a1a7fe9cc32992ce (script rc 0, "29 old edits; corrected or added: ['2','4','5','18','19','20','21','29','30']", "failing []", "written ... 780 lines") | 780 | 780 |
Every 64-character sha in LEAD-CHECKLIST-v5.md (A0, A2, A3, A4, A5b, A5b4, step4() constants) equals a rebuilt sha; every one is exactly 64 characters. PLAN-CHAIN.md shas also match.
Per chain, counts and lines measured on the rebuilt plans (A6 counts `<FINAL[-]`, `LEAD-FILL [0-9]`, HEAD_PIN lines, RE-PIN lines = 24 10 2 1 for all three):
| CHAIN | marker lines (grep -n -o 'LEAD-FILL [0-9][0-9a-z]*', 17 markers on 10 lines) | `<FINAL` lines | table header (place 4) | P-4b step line | UNVERIFIED 14/15 | 13.1/13.3 | tables in A0 |
|---|---|---|---|---|---|---|---|
| 2 | 2,3,4,125,258,275,433,434,585,586 | 2,136,251,536 (+ 20 rows 538-557) | 536 | 258 | 585,586 | 433,434 | all match |
| 3 | 2,3,4,125,258,275,466,467,620,621 | 2,136,251,571 (+ rows 573-592) | 571 | 258 | 620,621 | 466,467 | all match |
| 4 | 2,3,4,137,270,287,509,510,774,775 | 2,148,263,725 (+ rows 727-746) | 725 | 270 | 774,775 | 509,510 | all match |
Other measured facts: minutes 172/174/176 appear in the plans' section 5 text and PLAN-CHAIN.md; step counts 154 -> 156 (+2) and UNVERIFIED sentences 16 -> 20 (+4) match the A0 wording "2 more plan steps and 4 more UNVERIFIED sentences"; C2 lines 2, 148, 263 each hold exactly the three tokens `<FINAL-SHA-FULL>`, `<FINAL-SHA-7>`, `<FINAL-BRANCH>`; distinct 40-hex shas in the unfilled plan: 0; plan line 3 holds the Windows form once and `PF=C:/...;` twice (A9 counts 1 and 2 after the path edit); the plan names `nlite-fix3`, `/home/<name>/dlrun`, `_local\agents-register.md`, `$C/n8n.pid` with `C=$R/ctl`.
Patch 3 claims tested: `git apply --check` fails ("patch failed ... :3"), `patch --fuzz=0` fails ("Hunk #1 FAILED at 3"): MATCHES A5b text.
The four C7 count patterns and the A7 marker grep are character-identical to the plan's text (grep on the plan).

## 4. Block runs (item 4), exit codes and first STOP lines
Flow CHAIN=4, user 65534 (excerpts of raw output; "STOP" lines are expected negatives I provoked):
- b02 with CHAIN empty: `note: CHAIN is empty (decide in A0)`; b07 and b10: `STOP CHAIN: CHAIN is ''. ...` (exit 1).
- b01: `core.autocrlf now: false`. b03: `ok A1: made ...`; re-run: `ok A1: work folder exists`. b04: 13 lines `ok ...` (8 no CR, 3 patch checksums, original checksum, original no CR).
- b05 `ok A3`; b06 `ok A4`; b07 `ok A5b`; b08 `written ... 28f92c5d1211207c 780 lines` / `ok A5b4`; b09 `ok A5c`; b10 `ok A6 counts 24 10 2 1` and `ok A6 plan checksum for CHAIN=4 (28f92c5d1211207c)`; b11 `ok A7 marker lines are 2,3,4,137,270,287,509,510,774,775`.
- Re-run of b05..b08, b10: `ok A3 (already done ...)`, `ok A4 (already done ...)`, `ok A5b (already done ...)`, `ok A5b4 (already applied: nothing changed)`, A6 ok.
- CHAIN=2 and CHAIN=3 with patch: A3, A4, (A5b) ok; A6 ok; A7 ok with the per-CHAIN lines of section 3.
- No `patch` on PATH: CHAIN=2: `ok A3`, `ok A4` (git apply fallback), A6/A7 ok. CHAIN=3 and 4: `STOP A5b: the program patch is not installed and this chain step cannot use git apply. Next: set CHAIN=2 ...`; then A6 `STOP A6: the plan checksum is not the one of CHAIN=3` (exit 1, nothing changed).
- No Python: b08 `STOP A5b4: no working Python 3.6 or newer in Git Bash. Next: set CHAIN=3 ...`.
- Dangling symlink `real-v5-plan.md`: b08 `STOP A5b4: ... already exists; the script refuses to overwrite ...`; after removal: ok.
- b04 negatives: a CR in acc5.sh: `STOP A2: acc5.sh has CR ...`; missing patch: `STOP A2: plan-v5-repin-v6.patch is missing ...` (and a stray `sha256sum: ... No such file` line plus a second STOP for the same file).
- b12: copied once (`ok A8 copied`); later (PF edited): `STOP A8: PF exists and differs ... run lines in PROGRESS.md ...: 6`.
- b13 before editing line 3 (my path differs from the plan's guess): counts 0 and 0; b14 refuses (`STOP A9 ... nothing changed`); after replacing the strings on line 3 as the text says: counts 1, 2, 1, 1; b14 with PF_CONFIRMED=yes: `ok A9: marker 9 flipped`.
- b15 `accept 3 4 8` flips (no output of the refusal). `accept 2/5/7/9/1/1b/6/99` all refused with the documented STOP lines; `accept 2` with L1_RULED=yes flips.
- b16: `head=a47cdf6... seven=a47cdf6 branch=take/nlite-int-r5`, `PIN empty: first run, read only`.
- b17 negatives: FINAL5 no -> `STOP C2`; PIN `abc` -> `STOP C2: PIN is not 40 hex characters`; wrong branch -> `STOP C2: the branch nosuch does not exist ...`; positive: `ok C2`, left placeholders 0, 20 rows open; repeat ok.
- b33 before C4: `counts 20 4 2 1 ...`, `STOP C7: 20 lines still hold a <FINAL placeholder`, `STOP C7: 4 lines still hold a LEAD-FILL marker`.
- b18 prints the `_kind` and `exit 3` lines of the stand-in script; b19 `syntax ok`, CR 0, non-ASCII 0, word scan empty; b19 again: `STOP C2b: ... P-4b.sh already exists`.
- WSL blocks as uid 65534 on this kernel: WSL-1 `user: nobody uid=65534`, `dash -n ok`; negative control (no stand-in) P-4b.sh prints nothing, exit 0 (bash and dash); WSL-2 `stand-in pid=12763`, `65534 /proc/12763`, `0 /proc/12763/environ`, `status-uid=65534`, `environ: Permission denied`; WSL-3 `exit=0`, control file `P-4b.sh sha256 21d00f1c...` plus `P-4b-HIT pid=12763` (dash run: same hit, exit 0); WSL-4 `gone`, `standin-gone.txt` = `gone control=489995fee552a42f`.
- b24 SP note: `NOTE lead stand-in pid=12763 <time>` (run twice: two identical lines, as the text says). b26: `dash syntax ok`, `P-4b files ok`. `accept 1 1b` accepted after that.
- b26 negatives: file edited -> `STOP C2c: the first line of the control file does not hold the checksum`; word kill added -> `STOP C2c: the word kill or env.sh`; bad control line -> `STOP C2c: a control line has the wrong shape`; no hit line -> `STOP C2c: the control file has no hit line`; CR -> `STOP C2c: CR in ...`.
- b27 with a wrong BP: `STOP C3: BP (/nonexistent) is not the studio preamble ...`; right BP: brief printed and saved, `ok C3`. b28 before runner lines: `runner lines in PROGRESS.md: 0 (must be 1 or more)`, `strings.txt exists` (no STOP, as the text describes).
- b29: head line + 20 rows (H1, H2 non-empty here because stand-in files hold the strings); b30: `rows filled by this run: 20`, `rows still open: 0`, `ok C4: now run: accept 6`; `accept 6` accepted; with the worktree head moved: `STOP C4: MISMATCH ...`, C9 `STOP C9: PIN is not the tip of branch ...`.
- b31 (C5) prints `known` and the changed lines; b32 (C6): `ACCEPT` and the n8n_kill.py part. b33 (C7) `counts 0 0 2 1 ...`, `ok C7`; negatives: CR -> `STOP C7: PF holds 1 carriage returns`; BOM -> `STOP C7: PF starts with a byte-order mark`; second sha -> `STOP C7: the 40-character shas in PF are [...]`; a `<FINAL` and a LEAD-FILL left -> two STOP lines.
- b34 (C8) lists `nlite-fix5` and `take/nlite-int-r5` lines; b35 `ok C8b: stand-in gone for the current control file`.
- b36 (C9) before `P-3a done`: `STOP C9: the last runner line is not 'P-3a done ...'`; after the line (appended without line end): `(the last line had no line end: one was added)`, `P-3a done ...`, `LEAD-GO RE-PIN <time> pin=a47cdf6... plan=c8d4bb0de1bd4cca`; again: `STOP C9: a LEAD-GO RE-PIN line is already there`.
- b37 (D1): no NEED line -> `STOP D1: no NEED-LEAD R2 line for pid 4242`; with NEED line -> `LEAD-YES R2 pid=4242 <time>`; second -> `STOP D1: a LEAD-YES line ... already there`; after `kill exit=3` -> `STOP D1: a kill exit=3 line exists ...`.
- D2 blocks (own HOME, in WSL-less Linux): b38 prints the last `== P-4b` block; b39 with empty HITPID `STOP D2: HITPID must be digits`; with a pid: prints its command line; b40 prints the last NOTE line; b41 with a live process `ALIVE pid=... n8n-fake hadavin-smoke 20`; b42 with it alive `STOP D2: something of the run is alive; nothing deleted`; `DEL=no` -> `STOP D2: DEL is not yes`; nothing alive + DEL=yes -> `deleted`. (First attempt printed ALIVE for my own tool wrapper because its command line contained the words; the check matches any process whose command line contains `n8n` or `hadavin-smoke`, including a wrapper shell; re-run from a detached script was clean.)
- STOP ids: every `STOP <id>:` printed in blocks has a row in table E, apart from combined rows (A1/A3/A4/A5b, C2b/C2c, C5/C6, C8b/C9) which cover them; checked with a script.
- `norm`: `C:\Users\...`, `C:/Users/...`, trailing slash: all give the same PF. A space in the folder name: `STOP VARS: HB is not a folder` only because my folder does not exist; the later PF path keeps the space.
- Leftover check: no stand-in or fake process left; scratch removed (section 6).

## 5. Citation mismatches (item 3) file:line, claimed, actual
1. LEAD-CHECKLIST-v5.md:8 (glossary, "channel"): "If there is no such window, see open item Q1 in `v10-OPEN-FOR-LEAD.md`". Actual: v10-OPEN-FOR-LEAD.md item 3 "Q1" is about where `BRIEF-PREAMBLE.md` lies on the laptop; the "who to ask" matter is item 2 "L2".
2. LEAD-CHECKLIST-v5.md:88 (A0 heading "open ruling L2, you decide") and LEAD-FILL-list-v5.md:1 ("open question L2 in `v10-OPEN-FOR-LEAD.md`" about CHAIN). Actual: v10-OPEN-FOR-LEAD.md line 4 L2 = "the lead must name the person the checklist tells the user to ask in D2". No item in v10-OPEN-FOR-LEAD.md is about the CHAIN decision.
3. LEAD-FILL-list-v5.md:17: "item L1 of `v9-OPEN-FOR-LEAD.md`". The rest of both files cites `v10-OPEN-FOR-LEAD.md` (item 1 = L1). The v9 file exists and has an L1, so it resolves, but it is the stale file name.
4. LEAD-CHECKLIST-v5.md:4 says only the first marker grep and the four C7 count patterns are word for word the plan's: CONFIRMED (identical text in the plan).
5. v10-OPEN-FOR-LEAD.md:4 (stale PLAN-CHAIN.md values): CONFIRMED at PLAN-CHAIN.md lines 65-66 (777/778, `b0caeb84...`); PLAN-CHAIN.md is out of date in those two places; the checklist values are the right ones.
6. v10-CHANGES.md: all file names in "Files written" exist; "evidence 3 (N1, N3, N4, N5, N5b, N7)" ids exist in evidence-c7h.md (lines 1744, 1764, 1781, 1797, 1909, 1833). Nothing else in v10-CHANGES.md contradicted a file I could read.
No mismatch found in: all sha256 values, line counts 561/587/622/780, marker lines and counts per CHAIN, `<FINAL` lines, A6 counts, UNVERIFIED line numbers, 13.1/13.3 lines, minutes 172/174/176, patch prefixes 9e8d06dd, 8a83abaa, 498c1e5f, 67a0a195537de875, "29 edits and one added" and the list of corrected edits, D2 "line 258 for CHAIN 2 and 3, line 270 for CHAIN 4".
Other notes (not citation mismatches): the plan text itself holds the owner's Windows and WSL user names in paths (plan lines 3, 124, 263 area); the repo rule says no personal data, so the lead may want those paths made generic before the plan is committed (nothing here prints them). The banned-word scan of the checklist, fill list, v10-CHANGES.md and evidence-c7h.md: 0 hits each (10 entries in BANNED).

## 6. Cleanup
Scratch /tmp/c10ev, the symlinks /c and /mnt/c, and my uid-65534 stand-in processes were removed; counts are in the report.
