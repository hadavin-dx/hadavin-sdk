# Independent evidence for LEAD-CHECKLIST-v5.md revision 13 (EVIDENCE RUNNER: raw results, no judgement)

Run 2026-11-16 on Linux (bash, dash, GNU patch, git). Raw output: `raw/c13i/` (this folder). I did not reuse the builder's harness; I built my own under the scratchpad.

## What did not go as clean as the builder's claims, or needs a look (first)
1. **Stale proof for question 6 (C4).** `accept 6` only checks that `proof-6.txt` holds `PIN`. The C4 fill block deletes `proof-6.txt` only in its last branch. If C4 once succeeded, and later `strings.txt` or the plan row changes so the fill block STOPs early (stale rows, string mismatch), the old `proof-6.txt` stays and `accept 6` still passes. I saw this by accident in a first run where my snapshot already held a proof file (`accept 6` exit 0 and C9 exit 0 after a C4 STOP). Not re-run as a clean case; the clean cases N6 and N6c (snapshot taken BEFORE C4, so no old proof) STOP correctly at `accept 6`. This is a real gap in the repeat-run case, not an issue on a first pass.
2. **C3b with a symlinked `PROGRESS.md`** exits 0 (it only reads through the link). Read-only, so no write goes through it; the write blocks (C2b note block, C9) refuse. Listed so you know C3b does not refuse links.
3. **Positive flow did not use the real WSL blocks.** WSL-2 / WSL-3 / WSL-4 need a non-root user and an unreadable `/proc/<pid>/environ`; I am root, so root reads everything. I made `P-4b.control.txt` (`P-4b-HIT pid=4242`) and `standin-gone.txt` by hand in the exact shape the checks expect. C2c, C8b and C9 accepted them. WSL-1 as root correctly STOPs (N8b). WSL-3 with no hit correctly STOPs (N8).
4. In the positive flow the plan text names the real laptop folders for the evidence and pastes folders, so block A8/A9's "evidence folder named in plan" and "pastes folder named in plan" counts printed 0 (my folders differ). Not a checklist failure; those counts are "1 or more" only on the real laptop. I did not check them there.
5. A `cygpath` stub (mine, in `raw/c13i/harness/cygpath-stub.sh`) stood in for Git Bash's `cygpath`, and a bind mount made the path `/z/...` (the checklist requires `/<letter>/...`). Created `/z` (empty folder, outside the scratchpad) as the mount point; the mount itself vanished when my `unshare -m` namespace ended, but **I could not remove `/z`** (the safety check refused `rmdir /z`). Please remove it: `rmdir /z`. I did not touch `/q`.

## (a) Checksums (sha256sum, `raw/c13i/sha256.txt`)
- LEAD-CHECKLIST-v5.md = 33f50ab7b781b965b86c090106230597c4d80445536878eecfa4fb4b622b73b6 (matches the expected value)
- LEAD-FILL-list-v5.md = da2635db2d7c329169eca1aba285e47fd17fd734908bce20dff3a55c122ee9ca (matches da2635db...ee9ca)
- acc5.sh = 4ee334309b17375df29209610bc0094c504286b7a0781410c2a5be54113626e9 (matches 4ee33430...626e9)
- Block A2 of the checklist itself also printed "ok" for the 8 patch/script/list files and the original plan.

## (b) Syntax (`raw/c13i/syntax.txt`, `index.tsv`)
- Fenced blocks extracted from the checklist: 45 (all marked `bash`).
- `bash -n`: 45 of 45 rc=0. `dash -n`: 45 of 45 rc=0. stderr files empty.

## (c) Scratch harness (own build; scripts in `raw/c13i/harness/`)
Setup: a scratch Git Bash-like tree (`HB`, `CH` with copies of `paste-check` and `inputs`), a git repo with a worktree-like folder holding two commits (old, new), the 5 script files that contain the 20 table strings, `strings.txt` (20 rows), CHAIN=4 (final plan). Each checklist block was run in a fresh `bash` with the section-1 variables and helper functions pasted in front, the way the checklist says.

Positive flow (all `exit=0`, 0 STOP lines): A1, A2, A3, A4, A5b, A5b4, A5c, A6 ("ok A6 counts 24 10 2 1", chain mark ok), A7, A8, A9 (after I edited line 3 of PF to the stub path), B1 (`accept 3 4 8`), B2, C1 (20 rows), C2, C2b (extract `P-4b.sh`; syntax, CR, non-ASCII, word scan clean), C2c ("P-4b files ok"), C3, C3b, C4 rows + fill ("rows filled by this run: 20", "rows still open: 0"), `accept 1 1b`, `accept 6`, C5, C6 (ACCEPT), C7 ("ok C7"), C8 ("ok C8"), C8b ("ok C8b"), C9 (wrote the release line). Files: `pos-run-0-chain.txt` (b02 to b13: 12 runs, 12 exit 0, 0 STOP), `pos-run-1.txt`, `pos-run-2a.txt`, `pos-run-2.txt`, `pos-run-3.txt`. (The chain file is from a second, identical run of A1 to A9's first half; the main flow's chain steps ran the same blocks earlier and were also all ok.)

Negatives, each run from a fresh copy of a snapshot (`raw/c13i/negatives/*.txt`, one file per case, `SUMMARY.txt` lists the exit codes per block; 31 case files; control case N0 exits 0,0,0):

| Case | What I changed | Result |
|---|---|---|
| N1 x6 | OLD = `HEAD`, `abc12` (5 hex), `-p`, empty, `ABCDEF1` (upper case), valid sha + `;touch .../PWNED` | C5 exit 1 with the "not 7 to 40 lowercase hex" STOP, C6 exit 1, C9 exit 1 ("C6 has not printed ACCEPT"); no `PWNED` file was created |
| N2, N2b | OLD = PIN (7 and 40 characters) | C5 exit 1 ("same commit as PIN"), C6 exit 1, C9 exit 1 |
| N3 | `PROGRESS.md` is a symlink | C9 exit 1 (STOP LINK); C3b exit 0 (see item 2) |
| N3c | `PROGRESS.md` symlink to a victim file, note block with SP=4242 | exit 1 (STOP LINK); victim file unchanged (`victim`) |
| N4 | PF is a symlink | C7, C4 fill, C8, C2 all exit 1 (STOP PF); C9 exit 1 |
| N4b | control file symlink | C2c, C8b, C9 exit 1 (STOP LINK, then "do not pass C2c") |
| N4c | `standin-gone.txt` symlink | C8b exit 1 (STOP LINK), C9 exit 1 |
| N4d | `P-4b.sh` symlink | C2c, C8b, C9 exit 1 |
| N5 | PF missing | C7, C4 fill, C8, C9 exit 1 (C4 rows helper itself exit 0: it does not read PF) |
| N6 | snapshot before C4; `strings.txt` S7 row keeps the backslashes (`\|`) | C4 rows exit 0; C4 fill exit 1 ("strings.txt does not match the plan table"); `accept 6` exit 1; C9 exit 1 |
| N6b | same, S7 row without backslashes (the correct form) | C4 fill exit 0, `accept 6` exit 0 (the rev-13 `tr -d '\\'` fix works) |
| N6c | S3 string not in the plan row | C4 fill exit 1, `accept 6` exit 1 |
| N7 | banned word `kill` inserted in the list's script (C2b step 2) | first run exit 1 (STOP names the word), second run exit 1 (file exists), C2c exit 1, C8b exit 1, C9 exit 1 |
| N7b | banned word `env.sh` inserted | C2b exit 1, C2c exit 1, C9 exit 1 |
| N8 | WSL-3 (as root, no hit line): P-4b.sh prints exit=0 but no hit line | WSL-3 exit 1 (STOP), WSL-4 exit 1 (control missing), C2c exit 1, C8b exit 1, C9 exit 1 |
| N8b | WSL-1 as root | exit 1 ("wrong folder, root user ...") |
| N8c | P-4b.sh changed after the control file was made | C2c, C8b, C9 exit 1 (checksum line) |
| N8d | control file without hit line | C2c, C8b, C9 exit 1 |
| N8e | `standin-gone.txt` for another control file | C8b, C9 exit 1 |
| N9 | no `patch` on PATH (own PATH folder, no `patch`; `command -v patch` empty), from state after A2 | A3 exit 1 ("patch is not installed ... no git apply fallback"); A4 exit 1; A6 exit 1; plan file unchanged by A3 (checksum still the original-derived value shown in A4's STOP) |
| N9b | CR in PF | C7 exit 1, C9 exit 1 |
| N9c | PF edited after C8 | C9 exit 1 |
| N9d | second 40-character sha in PF | C7 exit 1, C9 exit 1 |
| N9e | `proof-c6.txt` missing | C9 exit 1 |

The missing-`patch` case (row N9) is saved as `raw/c13i/N9-missing-patch.txt` (not in `negatives/`). In it the plan file stayed at checksum 67a0a195537de875 (unchanged).

## Raw counts
- Fenced blocks: 45; bash -n pass 45; dash -n pass 45.
- Positive flow: 32 block runs saved (12 + 7 + 4 + 8 + 1), all exit 0, 0 STOP lines.
- Negative cases: 31 files in `negatives/`, incl. 1 control (N0). Every negative produced at least one STOP and exit 1 in its failing block; every later gating block I ran after the failure (C6, C9, C8b, C2c, C7 as listed) refused with exit 1, except the two read-only exceptions in items 1 and 2 above.
- `acc5-cases.sh` (builder's file, run by me once): "cases ok=18 bad=0".
- Banned-word scan of all my raw files against the BANNED list of `tests/test_no_reference_material.py` (13 words): 0 hits.

## What I did NOT check
- Git Bash, WSL (real Ubuntu), PowerShell, Windows paths and CRLF handling, real `cygpath`, real n8n. All of the above are absent here.
- The real WSL-2/WSL-3/WSL-4 flow with an unreadable process (I am root); the stand-in files were written by hand.
- CHAIN 2 and CHAIN 3 (I ran CHAIN 4 only); the chain checksums for them were not re-derived.
- C9's line written to the real laptop; `LEAD-GO` line content other than that it was appended once.
- Whether the plan's text in other places (not the blocks) is clear for a reader; not my task.
- Some STOP branches never triggered: A9 other STOPs, C2b step 1 (b19), C3 (wrong BP), C8 name-guess STOP branches, D1/D2 blocks (b38 to b44), B1 `accept 2` with L1 open, chainmark mismatches, A5b4 other STOPs, the unreadable-process limit text, `hbok` quote/`..` rejections.
- Decisions on the checklist wording, and `acc5.sh` accepting `print("exit 3")` (builder's stated limit; not re-tested beyond `acc5-cases.sh`).
- The harness fakes: the old/new commits are made up, the worktree's HEAD branch is `main` (the branch `take/nlite-int-r5` points to the same commit).
