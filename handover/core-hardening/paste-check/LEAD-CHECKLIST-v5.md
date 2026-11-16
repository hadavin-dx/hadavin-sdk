# LEAD CHECKLIST v5 (written in the v6 fix pass, 2026-11-16). For the lead, in Git Bash on the laptop.
This file only restates what the patched plan says (RE-PIN line, step P-4b, last check). If this file and the plan differ, the plan is right and this file is wrong: tell the builder. Every command below was copied by a script from the patched plan, not retyped. Where a command has a value you must write yourself, the line above it says `EDIT POINT`.
**Not tested on the laptop:** nothing here ran in Git Bash, PowerShell or WSL; the commands ran in plain bash and dash on a Linux container against stand-in folders and stand-in git repositories (evidence-c7g.md).
**Variables are per window.** `W` (work folder), `PC` (the folder `paste-check`), `PT` (patched plan in the work folder) and `PF` (the filled plan at the runner path) exist only in the Git Bash window where you set them. If you open a new window, or a command prints `No such file`, set them again (A1, A3, A6, A8) before you go on.
**Order of work (round 4 fix):** A (make the plan, copy it to `PF`, check the path), B (answer the questions that need no commit), C (re-pin: questions 5, 7, 6 and 1 are answered inside C1, C2, C4 and C2b), D (only if the runner asks). Every edit of the plan is made in `PF`, never in `PT`.
Words used: **lead** = you; **runner** = the agent that runs the plan; **pin** = the one commit whose scripts the run tests; **marker** = the text `LEAD-FILL <n>`, a question in the plan.

## A. Make the patched plan (do this once; the original is never edited)
The plan needs TWO patches in this order: first `plan-v5-fixes.patch`, then `plan-v5-repin-v6.patch`. The counts in the plan (24, 10, 2, 1) hold only in this order. Do not use `plan-v5-repin-v5.patch` or older (v1 to v4): they are replaced and fail or give wrong counts.
A1. Go to the folder `core-hardening` (the folder that holds `inputs\` and `paste-check\`) and make a work folder:
```bash
cd <path>/core-hardening && W=$(mktemp -d) && mkdir "$W/inputs" && cp inputs/plan-wp6-resmoke-v5.md "$W/inputs/" && cd "$W" && pwd
```
A2. The two patch files must have no carriage return either (set `PC` first, EDIT POINT: the real path of `core-hardening/paste-check`; both counts must print `0`; a number above 0 = STOP, get the files again). Then the copy must be the untouched original: first 16 characters of the checksum `67a0a195537de875`, and no carriage return (the count must print `0`; if it prints a number above 0 the file was changed to CRLF, STOP and get the original):
```bash
PC=<path>/core-hardening/paste-check; grep -c $'\r' "$PC/plan-v5-fixes.patch" "$PC/plan-v5-repin-v6.patch"; sha256sum inputs/plan-wp6-resmoke-v5.md | cut -c1-16; grep -c $'\r' inputs/plan-wp6-resmoke-v5.md
```
(`grep -c` prints one `name:0` per patch file; the plan copy prints `0`. `grep -c` ends with exit code 1 when the count is 0: that is normal here.)
A3. Try the first patch without changing anything (must print `rc=0`), then apply it (`rc=0`). `PC` is the folder `core-hardening/paste-check` (set in A2; set it again if you are in a new window):
```bash
patch -p1 --dry-run < "$PC/plan-v5-fixes.patch"; echo rc=$?
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
A6. The patched plan is now `$W/inputs/plan-wp6-resmoke-v5.md`. Before any question is answered the four counts must be `24`, `10`, `2`, `1` (`PT` is the patched file in your work folder):
```bash
PT="$W/inputs/plan-wp6-resmoke-v5.md"; grep -c '<FINAL[-]' "$PT"; grep -c 'LEAD-FILL [0-9]' "$PT"; grep -c -E '^[*][*]HEAD_PIN = |^[$]HEAD_PIN = ' "$PT"; grep -c -E '^[*][*]RE-PIN [(]lead only[)]. FOUR places hold' "$PT"
```
Any other numbers = the patches were not applied as above: STOP.
A7. List every marker (question) that is left:
```bash
grep -n -o 'LEAD-FILL [0-9][0-9a-z]*' "$PT"
```
A8. Copy the patched plan to the path where the runner will read it (question 9). EDIT POINT: write the real path in Git Bash form after `PF=` (the value below is only a guess; the folder is made if it does not exist). From now on `PF` is THE plan file: every edit of the plan (B1, A9, C2, C2b, C4) is made in this copy `PF`, never in `PT`, and the last check (C7) reads `PF`. If a file is already at `PF`, the command refuses and prints what to do next:
```bash
PF=C:/Users/rakes/Downloads/Hadavin/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md; mkdir -p "$(dirname "$PF")"; if [ -e "$PF" ]; then echo "already there: STOP. Next: run  cmp \"\$W/inputs/plan-wp6-resmoke-v5.md\" \"\$PF\"  . No output = same as the untouched patched plan, nothing is lost: go on to A9. Output = it was edited (an earlier attempt or an earlier run): move it aside with  mv \"\$PF\" \"\$PF.old\"  (never delete it, never overwrite it), run A8 again, and make the edits again. If PROGRESS.md in the evidence folder already has lines of a run: do NOT touch PF, ask the owner."; else cp "$W/inputs/plan-wp6-resmoke-v5.md" "$PF" && cmp "$W/inputs/plan-wp6-resmoke-v5.md" "$PF" && echo copied; fi
```
(If `$PF.old` already exists, use another name such as `$PF.old2`: `mv` would silently replace it.)
A9. Make the plan text name the real path (question 9). The plan names the plan file in THREE strings on its line 3: (1) the Windows form that the runner reads in RE-PIN step (e) (`C:\Users\...\wp6\plan-wp6-resmoke-v5.md`); (2) and (3) the two `PF=...;` strings inside the last check and the names check of the plan. Only (1) is used: the runner opens that Windows path. (2) and (3) are not used by this checklist (C7 and C8 use `PF` from A8); they only have to be true if someone pastes them from the plan. Check all three against the real `PF` (`cygpath -w` is part of Git for Windows; it writes the Windows form of a path):
```bash
NEWW=$(cygpath -w "$PF"); echo "windows form: $NEWW"; echo "string (1) found: $(grep -o -F "$NEWW" "$PF" | wc -l) (must be 1)"; echo "strings (2) and (3) found: $(grep -o -F "PF=$PF;" "$PF" | wc -l) (must be 2)"
```
Both numbers right = nothing to do. A wrong number = your real path is not the guess: open `PF`, go to line 3, replace string (1) by the printed `windows form`, and replace the text after `PF=` and before the `;` in strings (2) and (3) by the value of `PF`; run the command again; it must print 1 and 2. (The runner brief of C3 must name the same Windows path.) Not run on the laptop: `cygpath` does not exist in the Linux test container; the command was tested with a stand-in function that prints a fixed Windows path (evidence section 13).

## B. Answer the questions that need no commit (file `LEAD-FILL-list-v5.md`)
There are ten questions (1, 1b, 2 to 9). Answer them where the answer is known, in this order, all edits in `PF` (never in `PT`): questions 2, 3, 4 and 8 now (B1); 9 in A9; 5 and 7 in C2 (they need the output of C1); 6 in C4 (it needs the output of C4); 1 and 1b in C2b (they need the final-head `n8n_kill.py`).
B1. For each question you answer now: if you accept the safe default, change the marker `LEAD-FILL <n>` to `LEAD-DECIDED <n>`; otherwise replace the text by your answer. Change the marker in EVERY place (the list names the plan line of each place). Edit `PF`, never `PT`. After each batch of edits list what is left (the patched plan lists 17 markers on 10 lines; the list only has to get shorter; it must be empty before C7):
```bash
grep -n -o 'LEAD-FILL [0-9][0-9a-z]*' "$PF"
```

## C. Re-pin, in this order (plan: RE-PIN line, "ORDER")
C1. Read the commit that is checked out in the round-5 worktree. EDIT POINT: leave `PIN=` EMPTY on this first run (the command then only shows the commit and changes nothing). Copy the command exactly as it is:
```bash
WT=C:/Users/rakes/Downloads/Hadavin/_local/scratch/wt/nlite-fix5; SF=C:/Users/rakes/Downloads/Hadavin/_local/scratch/wp6-smoke/strings.txt; PIN=; H=$(git -C "$WT" rev-parse HEAD); echo "head=$H seven=${H:0:7} branch=$(git -C "$WT" rev-parse --abbrev-ref HEAD)"; if [ -z "$PIN" ]; then echo "PIN empty: first run, read only"; elif [ "$(git -C "$WT" rev-parse --verify -q "$PIN^{commit}")" != "$PIN" ]; then echo "PIN is not the full 40-character sha of a commit in this worktree: STOP"; elif [ ! -f "$SF" ]; then echo "strings.txt not written yet (run this paste again after P-3a)"; elif grep -q $'\r' "$SF"; then echo "strings.txt holds a CR (CRLF): STOP"; else [ "$H" = "$PIN" ] || echo "MISMATCH: head differs from PIN, the lines below are read at PIN"; while IFS=$'\t' read -r id f s || [ -n "$id" ]; do if git -C "$WT" cat-file -e "$PIN:scripts/$f" 2>/dev/null; then printf '%s %s %s\n' "$id" "$f" "$(git -C "$WT" grep -n -F -e "$s" "$PIN" -- "scripts/$f" | cut -d: -f3 | paste -sd, -)"; else printf '%s %s FILE-MISSING\n' "$id" "$f"; fi; done < "$SF"; fi
```
Output: `head=<40 characters> seven=<7 characters> branch=<name>`. Decide in C2 whether this commit is the final head of round 5 (question 5). Nothing is filled until you say so.
C2. Answer questions 5 and 7, then fill places (1), (2) and (3) in `PF` (the copy made in A8; never `PT`). Question 5: is the commit printed by C1 the final head of round 5? Question 7: are the folder `nlite-fix5` and the branch printed by C1 exactly right? Flip the markers of questions 5 and 7 as in B1 (`LEAD-DECIDED 5`, `LEAD-DECIDED 7`, in every place). Fill the three placeholders in angle brackets that start with `FINAL` in places (1), (2) and (3) (the plan names the four places) with the 40 characters, the 7 characters and the branch from C1. Then put the 40 characters into the variable for the next steps: `PIN=<the 40 characters>` (set it again in every new window).
C2b. Question 1 and 1b: write `pastes\P-4b.sh` and `pastes\P-4b.control.txt` (plain ASCII, LF line ends; the runner never writes them). The file to read first is the final `n8n_kill.py`; read it at the pinned commit (the command only reads; if `PIN` is not set in this window it prints an error and nothing else):
```bash
git -C C:/Users/rakes/Downloads/Hadavin/_local/scratch/wt/nlite-fix5 show "$PIN:scripts/n8n_kill.py" | less
```
What counts as n8n-shaped and as unreadable comes from that file (question 1; the proposal in `LEAD-FILL-list-v5.md` is only a start). Recipe, stand-in and one-line test are in `LEAD-FILL-list-v5.md`, section "PROPOSAL for item 1" (run them in the WSL Ubuntu shell as the same WSL user that runs the plan, not as root; run the one-line test BEFORE you rely on the check). **Write down the pid that the stand-in recipe prints (`stand-in pid=<number>`) in a note in `PROGRESS.md` (append at the end, as in C9); you need it in D2 to tell your own process from a foreign one.** The stand-in's command line starts with `n8n-stand-in`. Flip the markers of questions 1 and 1b in `PF` as in B1. Do this before C3 (the runner starts at C3 and needs both files at the end of P-3a).
C3. Start the runner. The brief is the message you give the runner agent when you start it (you write it; no file of this folder holds it). It must name the plan file by the Windows path of A9 (the runner reads its steps from that file; a different copy = STOP) and must contain this sentence, word for word: `Never write, copy or edit a line that starts with LEAD-GO or LEAD-YES; only the lead writes those lines.` If the sentence is missing, add it. Without it the release line (C9) protects nothing. The runner then runs step P-3a and tells you (it writes `strings.txt`). Wait for that message.
C4. Run the fill command a second time. EDIT POINT: write the 40-character commit after `PIN=` (the same value as place (2)); the command is otherwise identical to C1. Rows are read at that commit, not at the moving head:
```bash
WT=C:/Users/rakes/Downloads/Hadavin/_local/scratch/wt/nlite-fix5; SF=C:/Users/rakes/Downloads/Hadavin/_local/scratch/wp6-smoke/strings.txt; PIN=; H=$(git -C "$WT" rev-parse HEAD); echo "head=$H seven=${H:0:7} branch=$(git -C "$WT" rev-parse --abbrev-ref HEAD)"; if [ -z "$PIN" ]; then echo "PIN empty: first run, read only"; elif [ "$(git -C "$WT" rev-parse --verify -q "$PIN^{commit}")" != "$PIN" ]; then echo "PIN is not the full 40-character sha of a commit in this worktree: STOP"; elif [ ! -f "$SF" ]; then echo "strings.txt not written yet (run this paste again after P-3a)"; elif grep -q $'\r' "$SF"; then echo "strings.txt holds a CR (CRLF): STOP"; else [ "$H" = "$PIN" ] || echo "MISMATCH: head differs from PIN, the lines below are read at PIN"; while IFS=$'\t' read -r id f s || [ -n "$id" ]; do if git -C "$WT" cat-file -e "$PIN:scripts/$f" 2>/dev/null; then printf '%s %s %s\n' "$id" "$f" "$(git -C "$WT" grep -n -F -e "$s" "$PIN" -- "scripts/$f" | cut -d: -f3 | paste -sd, -)"; else printf '%s %s FILE-MISSING\n' "$id" "$f"; fi; done < "$SF"; fi
```
Output: 20 rows `ID file lines`. Question 6 (the folder of `run_real_check_n8n.py` and `real-run-n8n.env.example`, rows H1 and H2) is answered by these rows: a count of 0 is fine (REC); `FILE-MISSING` = STOP (look up the folder); then flip the marker of question 6 in `PF` as in B1. Replace the placeholder of each row in the section 11 table (place 4) of `PF` by the printed lines. Special outputs: `strings.txt holds a CR (CRLF): STOP` (send the runner `CR-FIX strings.txt`), `FILE-MISSING` (the folder is wrong, STOP), an empty last field (the string is gone, edit the plan), `PIN is not the full 40-character sha ...: STOP`, `MISMATCH` (the worktree moved on; the rows are still those of `PIN`; confirm that `PIN` is the final head).
C5. Read what the new script versions changed in their messages and exit numbers. EDIT POINT: write the 40-character commit after `PIN=` (empty = the command prints `PIN empty: STOP`). Run the command and read the whole output (C6 runs it again, saves it and checks it; C5 is only for reading; if you prefer, go straight to C6):
```bash
WT=C:/Users/rakes/Downloads/Hadavin/_local/scratch/wt/nlite-fix5; W3=C:/Users/rakes/Downloads/Hadavin/_local/scratch/wt/nlite-fix3; PIN=; if [ -z "$PIN" ]; then echo "PIN empty: STOP"; elif git -C "$WT" cat-file -e eec6ba4^{commit} 2>/dev/null; then echo known; for f in n8n_start.sh n8n_kill.py; do echo "== $f"; git -C "$WT" diff --no-color eec6ba4 "$PIN" -- "scripts/$f" | grep -iE '^[-+].*(echo|print|die|refused|confirmed|exit|return)'; done; else echo unknown; D=$(mktemp -d); for f in n8n_start.sh n8n_kill.py; do echo "== $f"; git -C "$W3" show "eec6ba4:scripts/$f" > "$D/old"; git -C "$WT" show "$PIN:scripts/$f" > "$D/new"; git diff --no-index --no-color -U0 "$D/old" "$D/new" | grep -iE '^[-+].*(echo|print|die|refused|confirmed|exit|return)'; done; rm -r "$D"; fi; echo "== end"
```
C6. Apply the acceptance rule to the output of C5 (plan: "Acceptance rule", three kinds of `+` line with `exit`). One ready block does it all: it runs the C5 command again, saves the whole output to `out.txt` in the folder where you are, runs `acc5.sh` on it (the script applies the same rule) and then prints the `n8n_kill.py` part so that you can read it. EDIT POINT: write the 40 characters after `PIN=` (empty = it prints `PIN empty: STOP` and `acc5.sh` prints `STOP`); `PC` is the folder set in A2 (set it again in a new window):
```bash
{ WT=C:/Users/rakes/Downloads/Hadavin/_local/scratch/wt/nlite-fix5; W3=C:/Users/rakes/Downloads/Hadavin/_local/scratch/wt/nlite-fix3; PIN=; if [ -z "$PIN" ]; then echo "PIN empty: STOP"; elif git -C "$WT" cat-file -e eec6ba4^{commit} 2>/dev/null; then echo known; for f in n8n_start.sh n8n_kill.py; do echo "== $f"; git -C "$WT" diff --no-color eec6ba4 "$PIN" -- "scripts/$f" | grep -iE '^[-+].*(echo|print|die|refused|confirmed|exit|return)'; done; else echo unknown; D=$(mktemp -d); for f in n8n_start.sh n8n_kill.py; do echo "== $f"; git -C "$W3" show "eec6ba4:scripts/$f" > "$D/old"; git -C "$WT" show "$PIN:scripts/$f" > "$D/new"; git diff --no-index --no-color -U0 "$D/old" "$D/new" | grep -iE '^[-+].*(echo|print|die|refused|confirmed|exit|return)'; done; rm -r "$D"; fi; echo "== end"; } > out.txt 2>&1; bash "$PC/acc5.sh" < out.txt; echo "---- the n8n_kill.py part, read it:"; sed -n '/^== n8n_kill.py/,/^== end/p' out.txt
```
It prints `ACCEPT` or `STOP (reason)`, then the part to read. **What ACCEPT proves, plainly: only that the text `exit 3` or `return 3` exists in the `n8n_kill.py` part. It does not prove the line is code or that the script really exits 3. You must read the `+` lines of the `== n8n_kill.py` part yourself before you go on.** On STOP do not write the release line (step C9).
C7. Run the last check on `PF`, the filled copy at the runner path (A8; if `PF` is not set in this window, set it again as in A8 but WITHOUT the `cp`). The four numbers must be `0`, `0`, `2`, `1`:
```bash
grep -c '<FINAL[-]' "$PF"; grep -c 'LEAD-FILL [0-9]' "$PF"; grep -c -E '^[*][*]HEAD_PIN = |^[$]HEAD_PIN = ' "$PF"; grep -c -E '^[*][*]RE-PIN [(]lead only[)]. FOUR places hold' "$PF"
```
C8. Run the names check on `PF`; it must list only the confirmed folder and branch names (question 7); if a wrong name is listed, edit that place in `PF` and run C7 and C8 again:
```bash
grep -n -o -E 'nlite-fix5|nlite-int-r5' "$PF"
```
C9. RELEASE. Only when C1 to C8 are clean (and the runner brief of C3 holds the sentence), add ONE line at the END of `PROGRESS.md` in the evidence folder `evidence-2\` (the runner's `run.sh` makes the folder; if you write the line first, the command below makes the folder and the file). **The file is append-only: add at the end, never rewrite, shorten or replace it.** The line starts with `LEAD-GO RE-PIN`, a space and your UTC time in the form `2026-11-16T10:55Z`. The command refuses when a `LEAD-GO` line is already there (a line you do not remember writing = STOP and tell the owner). If the file exists but its last line has no line end, the command first adds one (only a line end, nothing else is changed), so that your line never glues itself to the runner's last line; it prints the last two lines so that you can see this. EDIT POINT: `EV` is the evidence folder in Git Bash form (the value below is a guess):
```bash
EV=C:/Users/rakes/Downloads/Hadavin/egm/duplicate-proof-lead-desk/wp6/evidence-2; F="$EV/PROGRESS.md"; mkdir -p "$EV"; if grep -q '^LEAD-GO' "$F" 2>/dev/null; then echo "a LEAD-GO line is already there: STOP"; else if [ -s "$F" ] && [ -n "$(tail -c 1 "$F")" ]; then printf '\n' >> "$F"; echo "(the last line of PROGRESS.md had no line end: one was added)"; fi; printf 'LEAD-GO RE-PIN %s\n' "$(date -u +%Y-%m-%dT%H:%MZ)" >> "$F" && tail -n 2 "$F"; fi
```
This line is a procedural gate (the runner is told to wait for it and not to write it), not a technical lock.
C10. The runner now counts the leftovers itself (before P-1 and again at P-2) on the plan at the path of question 9, which is `PF` from A8. Any other result = the runner stops and tells you.

## D. During and after the run (only if the runner asks)
D1. If a clean-up kill of an n8n of this run is needed (plan rule R2), the runner writes `NEED-LEAD R2 pid=<digits>` in `PROGRESS.md`. Check that the pid is the one in its register row (the pid in the `n8n.pid` file of that n8n). Then append the permission line with this command; it refuses a pid that is not digits and a pid that has no `NEED-LEAD` line, and it adds a missing line end first, like C9. EDIT POINT: the digits after `PID=` (and `EV` as in C9):
```bash
EV=C:/Users/rakes/Downloads/Hadavin/egm/duplicate-proof-lead-desk/wp6/evidence-2; F="$EV/PROGRESS.md"; PID=; case "$PID" in ''|*[!0-9]*) echo "PID must be digits: STOP";; *) if ! grep -qE "NEED-LEAD R2 pid=$PID( |\$)" "$F" 2>/dev/null; then echo "no NEED-LEAD R2 line for pid $PID in PROGRESS.md: STOP"; else if [ -n "$(tail -c 1 "$F")" ]; then printf '\n' >> "$F"; fi; printf 'LEAD-YES R2 pid=%s %s\n' "$PID" "$(date -u +%Y-%m-%dT%H:%MZ)" >> "$F" && tail -n 2 "$F"; fi;; esac
```
After a `kill exit=3` no R2 is allowed, ever; you decide by hand outside the run.
D2. After a P-4b STOP (the log shows a `P-4b-HIT` line): do NOT end the process blind. Work in the WSL Ubuntu shell, not in Git Bash (`/proc` exists only in WSL, and the pid must be the WSL pid). EDIT POINT: `EV` in WSL form (`/mnt/c/...`).
(1) Where the hit lines are: the log `p.log` in the evidence folder; the last block that starts with `== P-4b` holds them (the block of a clean run has only that line and `exit=0`):
```bash
EV=/mnt/c/Users/rakes/Downloads/Hadavin/egm/duplicate-proof-lead-desk/wp6/evidence-2; awk '/^== /{ if (on) last=buf; on=($0 ~ /^== P-4b/); buf="" } on{ buf=buf $0 "\n" } END{ if (on) last=buf; printf "%s", last }' "$EV/p.log"
```
(2) For each `P-4b-HIT pid=<digits>`: read the command line (replace `<pid>`; this only reads):
```bash
tr '\0' ' ' < /proc/<pid>/cmdline; echo
```
(3) Whose process is it? The stand-in of the P-4b control is yours only if its command line starts with `n8n-stand-in` AND its pid is the `stand-in pid=` you wrote down in C2b (it ends by itself after 10 minutes, and step (5) of the positive-control instructions ends it by hand). Then you end it yourself by its exact pid (`kill <pid>` typed by you, in this shell, never inside the run). Any other hit (a different command line or a different pid) is not yours: tell the owner the pid and the command line; the owner decides; whoever decides ends it by its exact pid, outside the run. Never by name or pattern.
(4) Resume: the run stays stopped until you send the runner a message. Either (a) normal resume: `P-4b STOP is cleared: run P-3b, then P-4b, then P-5. Do not repeat P-1 or P-2.` (P-3b reads and ties the control file to the `P-4b.sh` that exists now; if you changed `P-4b.sh`, make `P-4b.control.txt` again first, C2b), or (b) fresh start: you delete the folder `$HOME/hadavin-smoke` yourself in the WSL shell (a folder made by P-1 only; check with `ls "$HOME/hadavin-smoke"` first) and send `Fresh start: restart at P-1; the RE-PIN step (e) counts run first, as the plan says.` The plan (P-4b step) names the same two ways. The old `LEAD-GO RE-PIN` line stays valid: do not write a second one (C9 refuses it).
