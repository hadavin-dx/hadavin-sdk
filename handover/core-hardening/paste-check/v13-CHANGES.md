# Checklist v5, revision 13: changes (failures and gaps first)

## What is not fixed, or not proven
- Obs 2 (`acc5.sh` accepts `print("exit 3")`, `EXIT 3`, `os._exit(3)`): NOT tightened. Decision: it stays a text check on the added `+` lines. A text check cannot tell code from a string or comment, the plan's rule is itself a text rule, and `acc5.sh` is fingerprinted in A2 (changing it changes the fill list proof too). The checklist now says plainly what it does not prove. Re-run on the final file: it still ACCEPTs those four lines (`acc5-cases.sh`: 18 ok, 0 bad).
- Obs 6 (patch missing prints nothing): I could not reproduce silence; rev 12 printed "ok A3" through a `git apply` fallback with no hint. I added the explicit `command -v patch` STOP and removed the `git apply` fallback.
- Obs 7: only a stated limit was added (an unreadable process with no n8n in its name is not detected; the lead must check it). No detection was added.
- Not tested: Git Bash, WSL, PowerShell and n8n are absent here (plain bash only). A real unreadable process (root reads all; a stub was used). CHAIN 3 and 4 blocks (A5b, A5b4) were not re-run. Some STOP branches were never triggered (A9 other STOPs, C2b step 1, C3, D2 (2b), C2 `sed` failure). The added `ps -u` command was not run. Exit codes of blocks without a STOP were not checked exhaustively.
- The `return 1 2>/dev/null || exit 1` pattern was not used: pasted into an interactive terminal it would close the lead's window. Used `{ echo "STOP ..."; false; }` instead (works pasted and sourced).
- Leftover: symlink `/q` (to the scratch folder) could not be removed; the safety check refused `rm /q`. The owner or lead may remove it.

## Rev-12 bugs found while testing (fixed)
- C4 fill compared a `strings.txt` column with the plan row using `grep -F`, but the plan escapes `\|`, so a row would STOP forever. Fixed with `tr -d '\\'`.
- C8b printed "ok" after a P-4b STOP. C2b step 2 returned 0 after a banned-word STOP. Both fixed.

## Fixes by observation
1. C5/diffwords: `OLD` must match `^[0-9a-f]{7,40}$` (so no leading `-`), resolved with `rev-parse --verify -q "$OLD^{commit}"`, refused if equal to the pin, git called with `--`, resolved shas used.
3. Every STOP echo is wrapped `{ echo "STOP ..."; false; }` so the block ends with 1 (all bash blocks except the first three definition blocks). Later blocks still refuse through proof files. Header text and table E updated.
4. C9: refuses a `PROGRESS.md` symlink; prints STOP when the write fails (tested with `chattr +i`).
5. New `pfok` (PF must exist and not be a symlink), new `nolink` (STOP LINK for symlinks); `flip` uses `pfok`; C2 no longer prints ok when PF is missing; control file and `standin-gone.txt` refused as symlinks.
6. `chain_step` checks `command -v patch` with a STOP.
7. P-4b: one sentence stating the limit.

## Fingerprints
`LEAD-FILL-list-v5.md` da2635db...ee9ca and `acc5.sh` 4ee33430...626e9 unchanged. New checklist sha256: 33f50ab7b781b965b86c090106230597c4d80445536878eecfa4fb4b622b73b6 (360 lines; rev 12 kept as `LEAD-CHECKLIST-v5.rev12.md`).
