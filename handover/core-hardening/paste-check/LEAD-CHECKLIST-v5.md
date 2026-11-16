# LEAD CHECKLIST v5 (written in the v6 fix pass, 2026-11-16). For the lead, in Git Bash on the laptop.
This file only restates what the patched plan says (RE-PIN line, step P-4b, last check). If this file and the plan differ, the plan is right and this file is wrong: tell the builder. Every command below was copied by a script from the patched plan, not retyped. Where a command has a value you must write yourself, the line above it says `EDIT POINT`.
**Not tested on the laptop:** nothing here ran in Git Bash, PowerShell or WSL; the commands ran in plain bash and dash on a Linux container against stand-in folders and stand-in git repositories (evidence-c7g.md).
Words used: **lead** = you; **runner** = the agent that runs the plan; **pin** = the one commit whose scripts the run tests; **marker** = the text `LEAD-FILL <n>`, a question in the plan.

## A. Make the patched plan (do this once; the original is never edited)
The plan needs TWO patches in this order: first `plan-v5-fixes.patch`, then `plan-v5-repin-v6.patch`. The counts in the plan (24, 10, 2, 1) hold only in this order. Do not use `plan-v5-repin-v5.patch` or older (v1 to v4): they are replaced and fail or give wrong counts.
A1. Go to the folder `core-hardening` (the folder that holds `inputs\` and `paste-check\`) and make a work folder:
```bash
cd <path>/core-hardening && W=$(mktemp -d) && mkdir "$W/inputs" && cp inputs/plan-wp6-resmoke-v5.md "$W/inputs/" && cd "$W" && pwd
```
A2. The copy must be the untouched original: first 16 characters of the checksum `67a0a195537de875`, and no carriage return (the count must print `0`; if it prints a number above 0 the file was changed to CRLF, STOP and get the original):
```bash
sha256sum inputs/plan-wp6-resmoke-v5.md | cut -c1-16; grep -c $'\r' inputs/plan-wp6-resmoke-v5.md
```
A3. Try the first patch without changing anything (must print `rc=0`), then apply it (`rc=0`). `PC` is the folder `core-hardening/paste-check` (EDIT POINT: write its real path):
```bash
PC=<path>/core-hardening/paste-check; patch -p1 --dry-run < "$PC/plan-v5-fixes.patch"; echo rc=$?
```
```bash
patch -p1 < "$PC/plan-v5-fixes.patch"; echo rc=$?
```
A4. The same two steps for the second patch (each must print `rc=0`):
```bash
patch -p1 --dry-run < "$PC/plan-v5-repin-v6.patch"; echo rc=$?
```
```bash
patch -p1 < "$PC/plan-v5-repin-v6.patch"; echo rc=$?
```
A5. If `patch` is not installed in Git Bash (the command prints `command not found`), use `git apply` instead: it ships with Git for Windows. It was tested here on the same files and gave the same result as `patch`. Same order, same folder (the `--check` form changes nothing):
```bash
git apply -p1 --check < "$PC/plan-v5-fixes.patch"; echo rc=$?; git apply -p1 < "$PC/plan-v5-fixes.patch"; echo rc=$?
```
```bash
git apply -p1 --check < "$PC/plan-v5-repin-v6.patch"; echo rc=$?; git apply -p1 < "$PC/plan-v5-repin-v6.patch"; echo rc=$?
```
If a patch fails halfway (a line such as `Hunk #n FAILED`), the plan copy is half changed: delete the work folder and start again at A1. A patch applied in the wrong order fails; never force it.
A6. The patched plan is now `$W/inputs/plan-wp6-resmoke-v5.md`. Before any question is answered the four counts must be `24`, `10`, `2`, `1` (EDIT POINT: `PF` is the patched file in your work folder):
```bash
PF="$W/inputs/plan-wp6-resmoke-v5.md"; grep -c '<FINAL[-]' "$PF"; grep -c 'LEAD-FILL [0-9]' "$PF"; grep -c -E '^[*][*]HEAD_PIN = |^[$]HEAD_PIN = ' "$PF"; grep -c -E '^[*][*]RE-PIN [(]lead only[)]. FOUR places hold' "$PF"
```
Any other numbers = the patches were not applied as above: STOP.
A7. List every marker (question) that is left:
```bash
grep -n -o 'LEAD-FILL [0-9][0-9a-z]*' "$PF"
```

## B. Answer the questions (file `LEAD-FILL-list-v5.md`)
B1. Answer the ten questions (1, 1b, 2 to 9). If you accept the safe default, change the marker to `LEAD-DECIDED <n>`; otherwise replace the text by your answer. Change the marker in EVERY place (the list names them).
B2. You write two files yourself, plain ASCII with LF line ends: `pastes\P-4b.sh` and `pastes\P-4b.control.txt`. Recipe, stand-in and one-line test: `LEAD-FILL-list-v5.md`, section "PROPOSAL for item 1". Run the one-line test BEFORE you rely on the check. Do this before step C1.

## C. Re-pin, in this order (plan: RE-PIN line, "ORDER")
C1. Read the commit that is checked out in the round-5 worktree. EDIT POINT: leave `PIN=` EMPTY on this first run (the command then only shows the commit and changes nothing). Copy the command exactly as it is:
```bash
WT=C:/Users/rakes/Downloads/Hadavin/_local/scratch/wt/nlite-fix5; SF=C:/Users/rakes/Downloads/Hadavin/_local/scratch/wp6-smoke/strings.txt; PIN=; H=$(git -C "$WT" rev-parse HEAD); echo "head=$H seven=${H:0:7} branch=$(git -C "$WT" rev-parse --abbrev-ref HEAD)"; if [ -z "$PIN" ]; then echo "PIN empty: first run, read only"; elif [ "$(git -C "$WT" rev-parse --verify -q "$PIN^{commit}")" != "$PIN" ]; then echo "PIN is not the full 40-character sha of a commit in this worktree: STOP"; elif [ ! -f "$SF" ]; then echo "strings.txt not written yet (run this paste again after P-3a)"; elif grep -q $'\r' "$SF"; then echo "strings.txt holds a CR (CRLF): STOP"; else [ "$H" = "$PIN" ] || echo "MISMATCH: head differs from PIN, the lines below are read at PIN"; while IFS=$'\t' read -r id f s || [ -n "$id" ]; do if git -C "$WT" cat-file -e "$PIN:scripts/$f" 2>/dev/null; then printf '%s %s %s\n' "$id" "$f" "$(git -C "$WT" grep -n -F -e "$s" "$PIN" -- "scripts/$f" | cut -d: -f3 | paste -sd, -)"; else printf '%s %s FILE-MISSING\n' "$id" "$f"; fi; done < "$SF"; fi
```
Output: `head=<40 characters> seven=<7 characters> branch=<name>`. Decide whether this commit is the final head of round 5 (question 5). Nothing is filled until you say so.
C2. Fill places (1), (2) and (3) of the plan (the three placeholders in angle brackets starting with `FINAL`; the plan names the four places). Use the 40 characters, the 7 characters and the branch from C1.
C3. The runner runs step P-3a and tells you (it writes `strings.txt`). Wait for that message.
C4. Run the fill command a second time. EDIT POINT: write the 40-character commit after `PIN=` (the same value as place (2)); the command is otherwise identical to C1. Rows are read at that commit, not at the moving head:
```bash
WT=C:/Users/rakes/Downloads/Hadavin/_local/scratch/wt/nlite-fix5; SF=C:/Users/rakes/Downloads/Hadavin/_local/scratch/wp6-smoke/strings.txt; PIN=; H=$(git -C "$WT" rev-parse HEAD); echo "head=$H seven=${H:0:7} branch=$(git -C "$WT" rev-parse --abbrev-ref HEAD)"; if [ -z "$PIN" ]; then echo "PIN empty: first run, read only"; elif [ "$(git -C "$WT" rev-parse --verify -q "$PIN^{commit}")" != "$PIN" ]; then echo "PIN is not the full 40-character sha of a commit in this worktree: STOP"; elif [ ! -f "$SF" ]; then echo "strings.txt not written yet (run this paste again after P-3a)"; elif grep -q $'\r' "$SF"; then echo "strings.txt holds a CR (CRLF): STOP"; else [ "$H" = "$PIN" ] || echo "MISMATCH: head differs from PIN, the lines below are read at PIN"; while IFS=$'\t' read -r id f s || [ -n "$id" ]; do if git -C "$WT" cat-file -e "$PIN:scripts/$f" 2>/dev/null; then printf '%s %s %s\n' "$id" "$f" "$(git -C "$WT" grep -n -F -e "$s" "$PIN" -- "scripts/$f" | cut -d: -f3 | paste -sd, -)"; else printf '%s %s FILE-MISSING\n' "$id" "$f"; fi; done < "$SF"; fi
```
Output: 20 rows `ID file lines`. Replace the placeholder of each row in the section 11 table (place 4) by the printed lines. Special outputs: `strings.txt holds a CR (CRLF): STOP` (send the runner `CR-FIX strings.txt`), `FILE-MISSING` (the folder is wrong, STOP), an empty last field (the string is gone, edit the plan), `PIN is not the full 40-character sha ...: STOP`, `MISMATCH` (the worktree moved on; the rows are still those of `PIN`; confirm that `PIN` is the final head).
C5. Read what the new script versions changed in their messages and exit numbers. EDIT POINT: write the 40-character commit after `PIN=` (empty = the command prints `PIN empty: STOP`). Run the command and keep the whole output:
```bash
WT=C:/Users/rakes/Downloads/Hadavin/_local/scratch/wt/nlite-fix5; W3=C:/Users/rakes/Downloads/Hadavin/_local/scratch/wt/nlite-fix3; PIN=; if [ -z "$PIN" ]; then echo "PIN empty: STOP"; elif git -C "$WT" cat-file -e eec6ba4^{commit} 2>/dev/null; then echo known; for f in n8n_start.sh n8n_kill.py; do echo "== $f"; git -C "$WT" diff --no-color eec6ba4 "$PIN" -- "scripts/$f" | grep -iE '^[-+].*(echo|print|die|refused|confirmed|exit|return)'; done; else echo unknown; D=$(mktemp -d); for f in n8n_start.sh n8n_kill.py; do echo "== $f"; git -C "$W3" show "eec6ba4:scripts/$f" > "$D/old"; git -C "$WT" show "$PIN:scripts/$f" > "$D/new"; git diff --no-index --no-color -U0 "$D/old" "$D/new" | grep -iE '^[-+].*(echo|print|die|refused|confirmed|exit|return)'; done; rm -r "$D"; fi; echo "== end"
```
C6. Apply the acceptance rule to that output (plan: "Acceptance rule", with the three kinds of `+` line with `exit`). The script `paste-check/acc5.sh` applies the same rule: save the output to a file and run `bash "$PC/acc5.sh" < out.txt` (prints `ACCEPT` or `STOP (reason)`). **What ACCEPT proves, plainly: only that the text `exit 3` or `return 3` exists in the `n8n_kill.py` part. It does not prove the line is code or that the script really exits 3. You must read the `+` lines of the `== n8n_kill.py` part yourself before you go on.** On STOP do not write the release line (step C9).
C7. Run the last check. EDIT POINT: `PF` is the path of the filled plan at the place where the runner will read it (question 9; the value below is only a guess). The four numbers must be `0`, `0`, `2`, `1`:
```bash
PF=C:/Users/rakes/Downloads/Hadavin/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md; grep -c '<FINAL[-]' "$PF"; grep -c 'LEAD-FILL [0-9]' "$PF"; grep -c -E '^[*][*]HEAD_PIN = |^[$]HEAD_PIN = ' "$PF"; grep -c -E '^[*][*]RE-PIN [(]lead only[)]. FOUR places hold' "$PF"
```
C8. Run the names check; it must list only the confirmed folder and branch names (question 7); if a wrong name is listed, edit that place and run it again:
```bash
PF=C:/Users/rakes/Downloads/Hadavin/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md; grep -n -o -E 'nlite-fix5|nlite-int-r5' "$PF"
```
C9. RELEASE. Only when C1 to C8 are clean, add ONE line at the END of `PROGRESS.md` in the evidence folder `evidence-2\` (make the folder and the file if they do not exist). **The file is append-only: add at the end, never rewrite, shorten or replace it.** The line must START with these words, then a space and your UTC time:
```bash
LEAD-GO RE-PIN <UTC time>
```
This line is a procedural gate (the runner is told to wait for it and not to write it), not a technical lock: you check that no such line is there before you write yours.
C10. Put the filled plan at the path of question 9. The runner then counts the leftovers itself (before P-1 and again at P-2). Any other result = the runner stops and tells you.

## D. During and after the run (only if the runner asks)
D1. If a clean-up kill of an n8n of this run is needed (plan rule R2), the runner writes `NEED-LEAD R2 pid=<digits>`. Check that the pid is the one in its register row, then append ONE line at the end of `PROGRESS.md` (EDIT POINT: the pid): `LEAD-YES R2 pid=<digits> <UTC time>`. After a `kill exit=3` no R2 is allowed, ever; you decide by hand outside the run.
D2. After a P-4b STOP (a hit line): do NOT end the process blind. You end only a process you started yourself (the stand-in of the P-4b control); for any other hit, tell the owner the pid and the command line (`tr '\0' ' ' < /proc/<pid>/cmdline`) and the owner decides; whoever decides ends it by its exact pid, outside the run; the plan lists where the run resumes (P-4b step, "Resume rules").
