# LEAD CHECKLIST for the re-smoke plan v5 (revision 9, written 2026-11-16). For the lead, in Git Bash on the laptop.
**What "v5" means in this file: always the plan** (`plan-wp6-resmoke-v5.md`). The file names `LEAD-CHECKLIST-v5.md` and `LEAD-FILL-list-v5.md` carry "v5" only because they serve that plan; the number of rewrites of this file is called "revision" (this is revision 9). The patch `plan-v5-repin-v6.patch` is the sixth version of the second patch for plan v5; do not read its "v6" as a plan version.
This file only restates what the patched plan says (RE-PIN line, step P-4b, last check). If this file and the plan differ, the plan is right and this file is wrong: tell the builder. Where a command needs a value that only you know, a line says `EDIT POINT`.
**Not tested on the laptop:** nothing here ran in Git Bash, PowerShell or WSL. The commands ran in plain bash and dash on a Linux container against stand-in folders, stand-in git repositories and a stand-in `cygpath` (evidence-c7g.md, section 13, and the scratch run listed in `REPORT-v9-checklist.md` if present; otherwise the changelog at the bottom says what was run).

## 0. Who is who, and what STOP means
- **lead** = you: the person or session at the laptop who reads this file and types the commands. **owner** = the studio owner; he only types `y`, the challenge and `end` (decision 7 of `DECISIONS-2026-11-16.md`); **this file never asks the owner to paste a command or to decide about a process** (open ruling L1 in `v9-OPEN-FOR-LEAD.md`). **runner** = the agent that executes the plan. **builder** = the agent that wrote this file and the patches. **channel** = the chat where you send the runner messages and where you reach the builder. **pin** = the one commit whose scripts the run tests. **marker** = the text `LEAD-FILL <n>`, a question inside the plan.
- **STOP** = type nothing else from this file. Copy the last lines of output, send them to the builder in the channel, and wait. Each STOP below also says the next action; where it says "move aside", the command is `mv "$X" "$X.old"` (never delete, never overwrite; if `.old` exists use `.old2`).
- Glossary of labels used in this file: **WORDS** = the paragraph on plan line 4 that fixes what each word means. **0.1** = plan step 0.1, where the runner greps every string of the section 11 table at the pin. **S13** = plan section 13, the clean-up at the end. **R2** = plan rule R2: an emergency clean-up kill of an n8n process of this run, allowed only with your permission line. **UNVERIFIED 14 and 15** = plan lines 585 and 586: two sentences saying a fact was not checked; they carry markers 7 and 1, so they change with your answers. **HEAD_PIN** = the 7-character commit in the plan header. **REC** = the runner records the value; any value is accepted.
- **Where a step is answered** (one table; the older mentions are gone): questions 2, 3, 4, 8 in B1; 9 in A9; 5 and 7 in C2; 6 in C4; 1 and 1b in C2b.

## 1. Variables (set them in EVERY new Git Bash window; a command that prints `No such file` or a STOP about a variable means you skipped this)
Everything is derived from three values you write once. The block makes no folder and changes no file. EDIT POINTS: `HB` = the folder `Hadavin` in Git Bash form, `<WINUSER>` is your Windows user name (written as `C:/Users/<WINUSER>/Downloads/Hadavin` in the plan); `CH` = the folder `core-hardening` that holds `inputs/` and `paste-check/` (in the repository it is `handover/core-hardening`; on the laptop you know where you put it); `PIN` stays empty until C2; `WTN`, `W3N`, `OLD` are the names in the plan header (round-5 worktree folder, round-3 worktree folder, the old 7-character pin; check them against line 3 of the plan).
```bash
HB=; CH=; PIN=; BR=; FINAL5=no; NAMES_OK=no; PF_CONFIRMED=no; WTN=nlite-fix5; W3N=nlite-fix3; OLD=eec6ba4
PC=$CH/paste-check; W=$HB/_local/scratch/lead-plan-work; PT=$W/inputs/plan-wp6-resmoke-v5.md
PF=$HB/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md; EV=$HB/egm/duplicate-proof-lead-desk/wp6/evidence-2
SM=$HB/_local/scratch/wp6-smoke; SF=$SM/strings.txt; PASTES=$SM/pastes; WT=$HB/_local/scratch/wt/$WTN; W3=$HB/_local/scratch/wt/$W3N
accept() { for n in "$@"; do sed -i "s/LEAD-FILL $n\\b/LEAD-DECIDED $n/g" "$PF"; done; grep -n -o 'LEAD-FILL [0-9][0-9a-z]*' "$PF"; echo "(end of list; CR count in PF: $(grep -c $'\r' "$PF"), must be 0)"; }
for v in HB CH PC; do eval "d=\$$v"; if [ -z "$d" ] || [ ! -d "$d" ]; then echo "STOP: $v is not a folder: '$d' (write HB and CH above)"; fi; done; for v in WT W3; do eval "d=\$$v"; [ -d "$d" ] || echo "note: $v folder not found yet: $d"; done; echo "PF=$PF"; echo "EV=$EV"; echo "PASTES=$PASTES"
```
The paths of `PF` (the plan file the runner reads), `EV` (evidence folder) and `PASTES` (the `pastes\` folder: `_local\scratch\wp6-smoke\pastes`, where the runner writes its paste files and where you save `P-4b.sh` and `P-4b.control.txt`) are the ones the plan names (plan section 2, R5 and P-1); only `HB` is yours. The one check that `EV` and `PASTES` equal the plan's own text is in A9. After you set `PIN` in C2, put the same 40 characters into the `PIN=` of this block, so every new window has it. After C2 also write `BR=` (the branch).
`accept <n> <n>...` (defined above) changes the marker `LEAD-FILL <n>` into `LEAD-DECIDED <n>` in every place of `PF` (`\b` makes `accept 1` leave `1b` alone) and lists what is left. **Editing `PF` by hand:** close the editor before you run any `sed` block, and open the file again afterwards (an editor still open can write an old copy back). After every edit check `grep -c $'\r' "$PF"` prints `0`; if it prints more, run `sed -i 's/\r$//' "$PF"`.

## A. Make the patched plan (do this once; the original is never edited)
The plan needs TWO patches in this order: first `plan-v5-fixes.patch`, then `plan-v5-repin-v6.patch`. The counts in the plan (24, 10, 2, 1) hold only in this order. Do not use `plan-v5-repin-v5.patch` or older (v1 to v4): they fail or give wrong counts.
A1. Make the work folder (the same folder every time, so a new window finds it again). If it exists the command says so and does nothing:
```bash
if [ -e "$W" ]; then echo "work folder exists: go to A2 and A6 to check it. To start again: mv \"$W\" \"$W.old\" and run A1 again"; else mkdir -p "$W/inputs" && cp "$CH/inputs/plan-wp6-resmoke-v5.md" "$W/inputs/" && echo "made $W"; fi
```
A2. Check the original and the two patch files (no carriage returns; checksum of the untouched plan). Everything must print `ok`:
```bash
for f in plan-v5-fixes.patch plan-v5-repin-v6.patch; do [ "$(grep -c $'\r' "$PC/$f")" = 0 ] && echo "ok $f no CR" || echo "STOP $f has CR: get the file again from the repository (git checkout -- the file) and run A2 again"; done; [ "$(sha256sum "$CH/inputs/plan-wp6-resmoke-v5.md" | cut -c1-16)" = 67a0a195537de875 ] && echo "ok original checksum" || echo "STOP: the original plan is not the expected file: get it again from the repository"; [ "$(grep -c $'\r' "$CH/inputs/plan-wp6-resmoke-v5.md")" = 0 ] && echo "ok original no CR" || echo "STOP: original has CR"; cmp "$CH/inputs/plan-wp6-resmoke-v5.md" "$W/inputs/plan-wp6-resmoke-v5.md" && echo "ok work copy equals original (only true before A3)"
```
(The last line differs after A3; that is normal.)
A3. Try the first patch without changing anything (must print `rc=0`; any other number = STOP: the work copy is not the untouched original; `mv "$W" "$W.old"` and start at A1), then apply it (`rc=0`). Run the patch commands inside the work folder:
```bash
cd "$W" && patch -p1 --dry-run < "$PC/plan-v5-fixes.patch"; echo rc=$?
```
```bash
cd "$W" && patch -p1 < "$PC/plan-v5-fixes.patch"; echo rc=$?
```
A4. The same two steps for the second patch (each `rc=0`; otherwise STOP and `mv "$W" "$W.old"`, start at A1):
```bash
cd "$W" && patch -p1 --dry-run < "$PC/plan-v5-repin-v6.patch"; echo rc=$?
```
```bash
cd "$W" && patch -p1 < "$PC/plan-v5-repin-v6.patch"; echo rc=$?
```
A5. If `patch` is not installed in Git Bash (`command not found`), use `git apply` instead (same order; `--check` changes nothing):
```bash
cd "$W" && git apply -p1 --check < "$PC/plan-v5-fixes.patch"; echo rc=$?; git apply -p1 < "$PC/plan-v5-fixes.patch"; echo rc=$?
```
```bash
cd "$W" && git apply -p1 --check < "$PC/plan-v5-repin-v6.patch"; echo rc=$?; git apply -p1 < "$PC/plan-v5-repin-v6.patch"; echo rc=$?
```
If a patch fails halfway (`Hunk #n FAILED`), the work copy is half changed: `mv "$W" "$W.old"` and start again at A1. Never force a patch.
A6. The patched plan is `$PT`. The four counts must be `24`, `10`, `2`, `1`. Any other numbers = the patches were not applied as above: STOP (`mv "$W" "$W.old"`, A1 again):
```bash
grep -c '<FINAL[-]' "$PT"; grep -c 'LEAD-FILL [0-9]' "$PT"; grep -c -E '^[*][*]HEAD_PIN = |^[$]HEAD_PIN = ' "$PT"; grep -c -E '^[*][*]RE-PIN [(]lead only[)]. FOUR places hold' "$PT"
```
A7. List every marker left (17 markers on 10 lines in the patched plan; the list must get shorter and be empty before C7):
```bash
grep -n -o 'LEAD-FILL [0-9][0-9a-z]*' "$PT"
```
A8. Copy the patched plan to `PF`, the path where the runner will read it. From now on `PF` is THE plan file: every edit (B1, A9, C2, C2b, C4) is made in `PF`, never in `PT`, and the last check (C7) reads `PF`. If a file is already at `PF`, the command refuses and prints what to do. (If `$PF.old` already exists use another name; `mv` would silently replace it.)
```bash
mkdir -p "$(dirname "$PF")"; if [ -e "$PF" ]; then echo 'already there: STOP. Run: cmp "$PT" "$PF"  . No output = same as the untouched patched plan, nothing is lost: go on to A9. Output = it was edited: mv "$PF" "$PF.old" (never delete it), run A8 again, make the edits again.'; if [ -f "$EV/PROGRESS.md" ]; then echo "run lines in PROGRESS.md (lines not starting with NOTE lead): $(grep -vc '^NOTE lead' "$EV/PROGRESS.md") - if above 0 a run has begun: do NOT touch PF, tell the builder"; fi; else cp "$PT" "$PF" && cmp "$PT" "$PF" && echo copied; fi
```
A9. Make the plan name the real path (question 9). The plan names its own file in THREE strings on line 3: (1) the Windows form (`C:\Users\...\wp6\plan-wp6-resmoke-v5.md`) that the runner reads in RE-PIN step (e); (2) and (3) the two `PF=...;` strings of the last check and the names check of the plan. The runner opens only (1); (2) and (3) must also be true because the flip below needs both to be found (count 2), and because anyone may paste them from the plan. `cygpath -w` (part of Git for Windows) writes the Windows form. This block checks the three strings, checks that the folder names of `EV` and `PASTES` equal the plan's own text, and prints the counts (1, 2, and at least 1 each for the two folders):
```bash
NEWW=$(cygpath -w "$PF"); echo "windows form: $NEWW"; echo "string (1) found: $(grep -o -F "$NEWW" "$PF" | wc -l) (must be 1)"; echo "strings (2) and (3) found: $(grep -o -F "PF=$PF;" "$PF" | wc -l) (must be 2)"; echo "evidence folder named in plan: $(grep -c -F "$(cygpath -w "$EV")" "$PF") (must be 1 or more)"; echo "pastes folder named in plan: $(grep -c -F "$(cygpath -w "$PASTES")" "$PF") (must be 1 or more)"
```
A wrong number = your real path is not the plan's guess. For strings (1) to (3): open `PF`, go to line 3, replace string (1) by the printed `windows form` and the text after `PF=` and before `;` in (2) and (3) by the value of `PF`; run the block again. For the two folder lines: `HB` is not the plan's folder (fix `HB`, set the variables again; do not edit the plan for this). The runner brief of C3 names the same Windows path.
**Close question 9 only when YOU have decided that the printed `windows form` is the path where the runner will read the plan** (a real folder on the laptop, starting with a drive letter). Then set `PF_CONFIRMED=yes` in this window and run the flip. It changes `LEAD-FILL 9` to `LEAD-DECIDED 9` only when you confirmed, the path starts with a drive letter, and the counts are 1 and 2; otherwise it changes nothing. It prints what is left of `LEAD-FILL 9` (nothing after `left:` is right):
```bash
PF_CONFIRMED=yes; NEWW=$(cygpath -w "$PF"); if [ "$PF_CONFIRMED" = yes ] && printf '%s' "$NEWW" | grep -qE '^[A-Za-z]:\\' && [ "$(grep -o -F "$NEWW" "$PF" | wc -l)" -eq 1 ] && [ "$(grep -o -F "PF=$PF;" "$PF" | wc -l)" -eq 2 ]; then sed -i 's/LEAD-FILL 9/LEAD-DECIDED 9/g' "$PF"; echo "marker 9 flipped; left:"; grep -n -o 'LEAD-FILL 9' "$PF"; echo "(end of list)"; else echo "not confirmed, no drive letter, or counts are not 1 and 2: nothing changed: STOP (fix line 3 of PF, then run this block again)"; fi
```
(`PF_CONFIRMED=yes` is typed by you inside the block on purpose: delete that word if you have not decided.)

## B. Answer the questions that need no commit (file `LEAD-FILL-list-v5.md`)
There are ten questions (1, 1b, 2 to 9). B1 answers 2, 3, 4 and 8 now. For each: if you accept the safe default (read it in `LEAD-FILL-list-v5.md`), flip the marker in every place with `accept`; otherwise replace the text by your answer in an editor (see section 1 on editing). For all four defaults in one command, which also prints what is left:
B1.
```bash
accept 2 3 4 8
```
Question 1 and 1b are answered in C2b, 5 and 7 in C2, 6 in C4, 9 in A9.

## C. Re-pin, in this order (plan: RE-PIN line, "ORDER")
**ROWS command (used in C1 and C4; it is the same command, only `PIN` differs).** It reads the commit checked out in the round-5 worktree and, once `PIN` is set, the line numbers of every string of `strings.txt` AT the pin (not at the moving head). With `PIN` empty it only prints the head and changes nothing. Copy it exactly:
```bash
H=$(git -C "$WT" rev-parse HEAD); echo "head=$H seven=${H:0:7} branch=$(git -C "$WT" rev-parse --abbrev-ref HEAD)"; if [ -z "$PIN" ]; then echo "PIN empty: first run, read only"; elif [ "$(git -C "$WT" rev-parse --verify -q "$PIN^{commit}")" != "$PIN" ]; then echo "PIN is not the full 40-character sha of a commit in this worktree: STOP"; elif [ ! -f "$SF" ]; then echo "strings.txt not written yet (run this paste again after P-3a)"; elif grep -q $'\r' "$SF"; then echo "strings.txt holds a CR (CRLF): STOP"; else [ "$H" = "$PIN" ] || echo "MISMATCH: head differs from PIN, the lines below are read at PIN"; while IFS=$'\t' read -r id f s || [ -n "$id" ]; do if git -C "$WT" cat-file -e "$PIN:scripts/$f" 2>/dev/null; then printf '%s %s %s\n' "$id" "$f" "$(git -C "$WT" grep -n -F -e "$s" "$PIN" -- "scripts/$f" | cut -d: -f3 | paste -sd, -)"; else printf '%s %s FILE-MISSING\n' "$id" "$f"; fi; done < "$SF"; fi
```
C1. Run the ROWS command with `PIN` empty. Output: `head=<40 characters> seven=<7 characters> branch=<name>` and `PIN empty`. If `git` prints `fatal` the folder `$WT` is wrong: STOP, fix `WTN` in section 1 (EDIT POINT), set the variables again. If `branch=HEAD`, the worktree has no branch checked out (detached head): the branch name must then be looked up in C2.
C2. Answer questions 5 and 7, then fill places (1), (2), (3) and the heading of section 11 in `PF`. **Question 5** = is the commit printed by C1 the final head of round 5? The source of truth is the final message of the round-5 builder (the message that says round 5 is final); if you have no such message, answer NO: leave `FINAL5=no` and wait, nothing is filled and the run cannot start (step (e) stops it). **Question 7** = are the folder name `$WTN` and the branch exactly right? If C1 printed `branch=HEAD`, find the branch that holds the commit: `git -C "$WT" branch --contains "$PIN"` (set `PIN` first). Then write in section 1 of this window (EDIT POINT): `PIN=` the 40 characters, `BR=` the branch, `FINAL5=yes`, `NAMES_OK=yes`. This block does all of it only when every check holds: 40 hex characters, the branch name has only safe characters, the branch exists in the worktree and contains the pin. It replaces the 4 sha/branch placeholders (24 `<FINAL` lines in the plan = 4 lines of sha and branch, `<FINAL-SHA-FULL>`, `<FINAL-SHA-7>`, `<FINAL-BRANCH>` on plan lines 2, 136, 251 and `<FINAL-SHA-7>` on line 536, plus the 20 table rows of C4), flips markers 5 and 7, and prints what is left:
```bash
if [ "$FINAL5" != yes ] || [ "$NAMES_OK" != yes ]; then echo "FINAL5 or NAMES_OK is not yes: nothing changed (wait for the builder's final message of round 5)"; elif ! printf '%s' "$PIN" | grep -qE '^[0-9a-f]{40}$'; then echo "PIN is not 40 hex characters: STOP"; elif ! printf '%s' "$BR" | grep -qE '^[A-Za-z0-9._/-]+$'; then echo "BR has unsafe characters or is empty: STOP"; elif [ "$(git -C "$WT" rev-parse --verify -q "$PIN^{commit}")" != "$PIN" ]; then echo "PIN is not a commit of $WT: STOP"; elif ! git -C "$WT" merge-base --is-ancestor "$PIN" "refs/heads/$BR" 2>/dev/null; then echo "branch $BR does not exist in $WT or does not contain PIN: STOP"; else sed -i -e "s|<FINAL-SHA-FULL>|$PIN|g" -e "s|<FINAL-SHA-7>|${PIN:0:7}|g" -e "s|<FINAL-BRANCH>|$BR|g" "$PF"; accept 5 7; echo "left placeholders (sha/branch must be 0): $(grep -c -E '<FINAL-(SHA|BRANCH)' "$PF"); table rows still open: $(grep -c '<FINAL-LINES>' "$PF") (must be 20 until C4)"; fi
```
STOP in this block: send the printed line and the output of C1 to the builder; fix the variable it names; run the block again (it changes nothing when it stops).
C2b. Questions 1 and 1b: write `pastes\P-4b.sh` and `pastes\P-4b.control.txt` (plain ASCII, LF line ends; the runner never writes them). Write them BEFORE C3. The whole recipe (scripts, stand-in, control file) is in `LEAD-FILL-list-v5.md`; the steps in order:
(1) Read the final `n8n_kill.py` at the pin (nothing is written except one file in the work folder; refuses an empty `PIN`) and look at the places that decide what "n8n-shaped" (how the script recognises an n8n process: the function `_kind` and its command-line checks) and "unreadable" (what it does when `environ` cannot be read: the exit 3 path) mean:
```bash
if [ -z "$PIN" ]; then echo "PIN empty: STOP (do C2 first)"; else git -C "$WT" show "$PIN:scripts/n8n_kill.py" > "$W/n8n_kill.at-pin.py" && grep -n -E 'def _kind|environ|cmdline|Permission|exit.3|return 3' "$W/n8n_kill.at-pin.py"; fi
```
Open `$W/n8n_kill.at-pin.py` in an editor for the rest (read only). If your definition differs from the proposal in `LEAD-FILL-list-v5.md` section "PROPOSAL for item 1", edit the saved copy of the script in step (2) and answer question 1 with your text.
(2) Save the proposal script as `P-4b.sh` (extracts the one script block from the list; LF line ends), then check it. The checks are: syntax (`bash -n`), no CR, plain ASCII, and the word scan (the file must not contain the words `kill` or `env.sh`, comments included; the scan must print nothing):
```bash
mkdir -p "$PASTES" && sed -n '/^#!\/bin\/bash/,/^exit 0$/p' "$PC/LEAD-FILL-list-v5.md" > "$PASTES/P-4b.sh" && bash -n "$PASTES/P-4b.sh" && echo "syntax ok" && echo "CR count: $(grep -c $'\r' "$PASTES/P-4b.sh") (must be 0)" && echo "non-ASCII lines:" && { grep -nP '[^\x09\x0A\x20-\x7E]' "$PASTES/P-4b.sh"; echo "(end)"; } && echo "word scan:" && { grep -n -i -E 'kill|env\.sh' "$PASTES/P-4b.sh"; echo "(end: nothing above is right)"; }
```
(3) Open the WSL Ubuntu shell (Start menu, "Ubuntu"; the same user that runs the plan, NOT root; check: `whoami` must print the user in the plan's `/home/<name>/` paths: `grep -o -m1 '/home/[a-z0-9_]*/dlrun' "$PF"` in Git Bash shows it). Git Bash prints the WSL form of your folders; paste its output into the WSL window:
```bash
echo "HBW=$(printf '%s' "$HB" | sed -E 's#^([A-Za-z]):#/mnt/\l\1#')"
```
In the WSL shell (after you pasted the `HBW=` line) run the stand-in recipe, the one-line test and the run of `P-4b.sh` exactly as in `LEAD-FILL-list-v5.md` ("STAND-IN recipe", "ONE-LINE test", "CONTROL FILE steps K1 to K7", using `$HBW/_local/scratch/wp6-smoke/pastes` as the pastes folder). The recipe prints `stand-in pid=<number>`. **Write the pid down in ONE note line per stand-in you start** (a second stand-in = a second note line; the last note line counts; D2 reads the last). In Git Bash. EDIT POINT: `SP=` the digits. The note starts with `NOTE lead stand-in pid=`, never with `LEAD-GO` or `LEAD-YES`. The command refuses a pid that is not digits, makes the folder, adds a missing line end first (the file is append-only: nothing is rewritten) and prints the last two lines:
```bash
SP=; F="$EV/PROGRESS.md"; case "$SP" in ''|*[!0-9]*) echo "SP must be digits: STOP";; *) mkdir -p "$EV"; if [ -s "$F" ] && [ -n "$(tail -c 1 "$F")" ]; then printf '\n' >> "$F"; fi; printf 'NOTE lead stand-in pid=%s %s\n' "$SP" "$(date -u +%Y-%m-%dT%H:%MZ)" >> "$F" && tail -n 2 "$F";; esac
```
(4) When the control file is made (steps K1 to K7), **end the stand-in now** (in the WSL shell: `kill <pid>`, typed by you, the exact pid) and check that it is gone. This check must print `gone` before C9, because a live stand-in would be found by the runner's leftover count as a hit (it also ends by itself after 10 minutes):
```bash
SP=<pid>; if [ -d /proc/$SP ] && tr '\0' ' ' < /proc/$SP/cmdline | grep -q '^n8n-stand-in'; then echo "ALIVE: end it with: kill $SP"; else echo gone; fi
```
(replace `<pid>`; run it in the WSL shell). After the stand-in is gone, flip the markers of questions 1 and 1b in `PF`: `accept 1 1b` (in Git Bash).
C3. Start the runner. The brief below is the message you give the runner agent when you start it (copy the text, fill the angle brackets; no file of this folder holds it). It must begin with the contents of `handover/BRIEF-PREAMBLE.md` (its first line is `STUDIO-PREAMBLE v1` and it must contain `EGM-GATE v1`; a hook refuses a brief without it). Print the filled text with:
```bash
NEWW=$(cygpath -w "$PF"); EVW=$(cygpath -w "$EV"); printf 'You are the RUNNER of the re-smoke plan. Read your steps only from this file: %s (a different copy = STOP). Run step P-3a only (write the glue, the paste files and strings.txt with the Write tool; do NOT write P-4b.sh or P-4b.control.txt, the lead made them). Then append ONE line `P-3a done <UTC time>` to the END of %s\\PROGRESS.md (append only, never rewrite the file), tell the lead "P-3a done" in your reply and STOP. Do not open the plan file again and do not start P-1 until the last line of PROGRESS.md starts with LEAD-GO RE-PIN. Never write, copy or edit a line that starts with LEAD-GO or LEAD-YES; only the lead writes those lines.\n' "$NEWW" "$EVW"
```
Without the sentence `Never write, copy or edit a line that starts with LEAD-GO or LEAD-YES; only the lead writes those lines.` the release line (C9) protects nothing. **Do not edit `PF` between starting the runner and its "P-3a done" message** (the runner reads the plan once, at the start); you edit `PF` again in C4 only after that message, and the runner re-reads it only after C9. Wait for the message.
C3b. Check that the runner writes where you will write (this proves `EV` is right; the folder and file may already exist because of the C2b note, so the test is a line that is NOT yours):
```bash
echo "runner lines in PROGRESS.md: $(grep -vc '^NOTE lead' "$EV/PROGRESS.md" 2>/dev/null) (must be 1 or more)"; tail -n 3 "$EV/PROGRESS.md"; [ -f "$SF" ] && echo "strings.txt exists" || echo "strings.txt missing"
```
A count of 0, or `strings.txt missing`: STOP. Ask the runner in the channel: "Print the full path of the PROGRESS.md you write to and of strings.txt." Compare with `EV` and `SF`. Do not write C9 until the runner's lines appear in YOUR `EV`.
C4. Run the ROWS command a second time with `PIN` set (the 40-character value; the command refuses a shorter one), saving the output, then fill the 20 table rows. Output is 1 `head=` line and 20 rows `ID file lines`: the last field is the list of line numbers where the string stands at the pin. An empty last field = the string is gone at the pin: the row cannot be filled, STOP and tell the builder (the plan table must be edited first). `FILE-MISSING` = the file is not under `scripts/` at the pin: STOP; look it up with `git -C "$WT" ls-tree -r --name-only "$PIN" | grep <file name>` and tell the builder. For `H1` and `H2` (the two files of question 6) an empty last field is accepted and written as `0` (the plan says REC; any value is recorded). `strings.txt holds a CR (CRLF): STOP` = send the runner `CR-FIX strings.txt`. `MISMATCH` = the worktree moved on; the rows are still those of `PIN`; check that `PIN` is the final head.
```bash
H=$(git -C "$WT" rev-parse HEAD); echo "head=$H seven=${H:0:7} branch=$(git -C "$WT" rev-parse --abbrev-ref HEAD)"; if [ -z "$PIN" ]; then echo "PIN empty: STOP"; elif [ "$(git -C "$WT" rev-parse --verify -q "$PIN^{commit}")" != "$PIN" ]; then echo "PIN is not the full 40-character sha: STOP"; elif [ ! -f "$SF" ]; then echo "strings.txt not written yet: STOP"; elif grep -q $'\r' "$SF"; then echo "strings.txt holds a CR: STOP"; else [ "$H" = "$PIN" ] || echo "MISMATCH: head differs from PIN, the lines below are read at PIN"; while IFS=$'\t' read -r id f s || [ -n "$id" ]; do if git -C "$WT" cat-file -e "$PIN:scripts/$f" 2>/dev/null; then printf '%s %s %s\n' "$id" "$f" "$(git -C "$WT" grep -n -F -e "$s" "$PIN" -- "scripts/$f" | cut -d: -f3 | paste -sd, -)"; else printf '%s %s FILE-MISSING\n' "$id" "$f"; fi; done < "$SF"; fi > "$W/rows.txt"; cat "$W/rows.txt"
```
Then fill the rows in `PF` (the block refuses odd values, and prints how many rows it filled; it must print 20 and then `0` open):
```bash
n=0; while read -r id f lines; do case "$id" in [A-Z][0-9]|[A-Z][0-9][0-9]) ;; *) continue;; esac; if [ -z "$lines" ] && { [ "$id" = H1 ] || [ "$id" = H2 ]; }; then lines=0; fi; case "$lines" in ''|*[!0-9,]*) echo "STOP row $id: '$lines' is not a list of numbers"; continue;; esac; sed -i "/^| $id |/s/<FINAL-LINES>/$lines/" "$PF"; n=$((n+1)); done < "$W/rows.txt"; echo "rows filled: $n (must be 20)"; echo "rows still open: $(grep -c '<FINAL-LINES>' "$PF") (must be 0)"; echo "CR count: $(grep -c $'\r' "$PF")"
```
If both numbers are right and no `FILE-MISSING` shows for `H1` and `H2`: `accept 6`.
C5. Read what the new script versions changed in their messages and exit numbers (C6 runs the same command again, saves it and checks it; C5 is only for reading; you may go straight to C6). The command refuses an empty `PIN`:
```bash
if [ -z "$PIN" ]; then echo "PIN empty: STOP"; elif git -C "$WT" cat-file -e "$OLD^{commit}" 2>/dev/null; then echo known; for f in n8n_start.sh n8n_kill.py; do echo "== $f"; git -C "$WT" diff --no-color "$OLD" "$PIN" -- "scripts/$f" | grep -iE '^[-+].*(echo|print|die|refused|confirmed|exit|return)'; done; else echo unknown; D=$(mktemp -d); for f in n8n_start.sh n8n_kill.py; do echo "== $f"; git -C "$W3" show "$OLD:scripts/$f" > "$D/old"; git -C "$WT" show "$PIN:scripts/$f" > "$D/new"; git diff --no-index --no-color -U0 "$D/old" "$D/new" | grep -iE '^[-+].*(echo|print|die|refused|confirmed|exit|return)'; done; rm -r "$D"; fi; echo "== end"
```
C6. Apply the acceptance rule (plan: "Acceptance rule", three kinds of `+` line with `exit`). One block runs the C5 command, saves the output to `$W/out-c6.txt`, runs `acc5.sh` on it and prints the `n8n_kill.py` part to read:
```bash
{ if [ -z "$PIN" ]; then echo "PIN empty: STOP"; elif git -C "$WT" cat-file -e "$OLD^{commit}" 2>/dev/null; then echo known; for f in n8n_start.sh n8n_kill.py; do echo "== $f"; git -C "$WT" diff --no-color "$OLD" "$PIN" -- "scripts/$f" | grep -iE '^[-+].*(echo|print|die|refused|confirmed|exit|return)'; done; else echo unknown; D=$(mktemp -d); for f in n8n_start.sh n8n_kill.py; do echo "== $f"; git -C "$W3" show "$OLD:scripts/$f" > "$D/old"; git -C "$WT" show "$PIN:scripts/$f" > "$D/new"; git diff --no-index --no-color -U0 "$D/old" "$D/new" | grep -iE '^[-+].*(echo|print|die|refused|confirmed|exit|return)'; done; rm -r "$D"; fi; echo "== end"; } > "$W/out-c6.txt" 2>&1; bash "$PC/acc5.sh" < "$W/out-c6.txt"; echo "---- the n8n_kill.py part, read it:"; sed -n '/^== n8n_kill.py/,/^== end/p' "$W/out-c6.txt"
```
It prints `ACCEPT` or `STOP (reason)`. On STOP: do not write the release line; send `$W/out-c6.txt` and the reason to the builder and wait. **What ACCEPT proves, plainly: only that the text `exit 3` or `return 3` exists in the `n8n_kill.py` part. It does not prove that the line is code or that the script really exits 3.** After ACCEPT you read the `+` lines of the `n8n_kill.py` part yourself. The reading rule (three questions; all three must be yes; any no = STOP, send the lines to the builder): (a) every `+` line with `exit` or `return` is one of `exit 2`, `exit 3`, `return 3` or the usual `sys.exit(main())`; (b) the line with `exit 3` or `return 3` is on the path where the script finds a process whose `environ` it cannot read (it refuses and ends with code 3), not on the normal successful kill path; (c) a real kill still ends with the text `confirmed gone` and exit 0 (the plan: `gone` needs `kill exit=0`). To read the whole change: `git -C "$WT" diff "$OLD" "$PIN" -- scripts/n8n_kill.py > "$W/kill.diff"` and open that file in an editor. Exit 3 (also called GONE-FAIL in the plan) means: a process that could not be read exists; the script refuses; R2 is never allowed after it (D1).
C7. Last check on `PF` (the four numbers must be `0`, `0`, `2`, `1`; a `No such file` line = `PF` is not set: section 1):
```bash
grep -c '<FINAL[-]' "$PF"; grep -c 'LEAD-FILL [0-9]' "$PF"; grep -c -E '^[*][*]HEAD_PIN = |^[$]HEAD_PIN = ' "$PF"; grep -c -E '^[*][*]RE-PIN [(]lead only[)]. FOUR places hold' "$PF"
```
C8. Names check on `PF`; it must list only the confirmed folder and branch names (question 7); if a wrong name is listed, edit that place in `PF` and run C7 and C8 again:
```bash
grep -n -o -E "$WTN|${BR:-take/nlite-int-r5}" "$PF"
```
C8b. Last gate before the release: the stand-in must be gone (WSL shell, the command of C2b step (4); it must print `gone`) and the P-4b files must exist:
```bash
ls -l "$PASTES/P-4b.sh" "$PASTES/P-4b.control.txt"; head -n 1 "$PASTES/P-4b.control.txt"; [ "$(sha256sum "$PASTES/P-4b.sh" | cut -d' ' -f1)" = "$(head -n 1 "$PASTES/P-4b.control.txt" | sed 's/^P-4b.sh sha256 //')" ] && echo "control matches P-4b.sh" || echo "STOP: control does not match P-4b.sh: make the control file again (C2b)"
```
C9. RELEASE. Only when C1 to C8b are clean and the runner brief holds the sentence of C3, add ONE line at the END of `PROGRESS.md` in the evidence folder. **The file is append-only: add at the end, never rewrite, shorten or replace it.** The line starts with `LEAD-GO RE-PIN`, a space and your UTC time (`2026-11-16T10:55Z`). The command refuses when a `LEAD-GO` line is already there (a line you do not remember writing = STOP and tell the builder), and when the runner has written no line yet (C3b). If the last line has no line end, it first adds one (only a line end) so your line never glues itself to the runner's line; it prints the last two lines:
```bash
F="$EV/PROGRESS.md"; if [ "$(grep -vc '^NOTE lead' "$F" 2>/dev/null)" -lt 1 ]; then echo "no runner line in PROGRESS.md yet (C3b): STOP"; elif grep -q '^LEAD-GO' "$F" 2>/dev/null; then echo "a LEAD-GO line is already there: STOP"; else if [ -s "$F" ] && [ -n "$(tail -c 1 "$F")" ]; then printf '\n' >> "$F"; echo "(the last line had no line end: one was added)"; fi; printf 'LEAD-GO RE-PIN %s\n' "$(date -u +%Y-%m-%dT%H:%MZ)" >> "$F" && tail -n 2 "$F"; fi
```
This line is a procedural gate (the runner is told to wait for it and not to write it), not a technical lock. Then check that the runner goes on: within about 5 minutes `tail -n 3 "$EV/PROGRESS.md"` must show a new runner line after yours. No new line = the runner reads another folder or waits: ask it in the channel for the full path of the PROGRESS.md it reads.
C10. The runner counts the leftovers itself (before P-1 and again at P-2, on the plan file at the path of question 9, which is `PF`). Its numbers must be the same `0`, `0`, `2`, `1` as your C7. Different numbers = it reads another file than `PF`: it stops and tells you.

## D. During and after the run (only if the runner asks)
D1. R2 (clean-up kill). If the runner needs to end an n8n of this run it writes `NEED-LEAD R2 pid=<digits>` in `PROGRESS.md`. Check that the pid is the one of its register row (the register is the file `_local\agents-register.md` under `HB`, the row of the take n8n) and of the pid file of that n8n (WSL: `cat "$HOME/hadavin-smoke/take-smoke-1/n8n.pid"` for the take; the control n8n keeps its own pid file in a folder under `$HOME/hadavin-smoke/ctl/`; which file name is not verified). Then append the permission line; the command refuses a pid that is not digits and a pid that has no `NEED-LEAD` line, and adds a missing line end first. EDIT POINT: the digits after `PID=`:
```bash
PID=; F="$EV/PROGRESS.md"; case "$PID" in ''|*[!0-9]*) echo "PID must be digits: STOP";; *) if ! grep -qE "NEED-LEAD R2 pid=$PID([[:space:]]|\$)" "$F" 2>/dev/null; then echo "no NEED-LEAD R2 line for pid $PID in PROGRESS.md: STOP"; else if [ -n "$(tail -c 1 "$F")" ]; then printf '\n' >> "$F"; fi; printf 'LEAD-YES R2 pid=%s %s\n' "$PID" "$(date -u +%Y-%m-%dT%H:%MZ)" >> "$F" && tail -n 2 "$F"; fi;; esac
```
After a `kill exit=3` no R2 is allowed, ever. Next action: write nothing, tell the builder in the channel; the plan (S13, steps 13.4 and 13.5) goes on by itself; an n8n of this run still alive after 13.5 = the runner stops and tells you; you decide by hand outside the run what happens to it (open ruling L1 for a process that is not yours).
D2. After a P-4b STOP (the log has a `P-4b-HIT` line): do NOT end the process blind. Work in the WSL Ubuntu shell (not Git Bash: `/proc` exists only in WSL). Set the variable first: paste the `HBW=` line printed by C2b step (3) and then `EV=$HBW/egm/duplicate-proof-lead-desk/wp6/evidence-2`.
(1) The hit lines: the last block that starts with `== P-4b` in `p.log` (a clean run has only that line and `exit=0`):
```bash
awk '/^== /{ if (on) last=buf; on=($0 ~ /^== P-4b/); buf="" } on{ buf=buf $0 "\n" } END{ if (on) last=buf; printf "%s", last }' "$EV/p.log"
```
(2) For each `P-4b-HIT pid=<digits>`, read the command line (replace `<pid>`; this only reads):
```bash
tr '\0' ' ' < /proc/<pid>/cmdline; echo
```
(2b) The stand-in pid you noted in C2b (only reads; the last such line counts; no line printed = you started none, so no process is yours):
```bash
grep -E '^NOTE lead stand-in pid=[0-9]+' "$EV/PROGRESS.md" | tail -n 1
```
(3) Whose process is it? Yours only if its command line starts with `n8n-stand-in` AND its pid is the one in the last note line of (2b). Then you end it yourself by its exact pid (`kill <pid>`, typed by you in this shell, never inside the run). **Any other hit is not yours: do not end it. Write down the pid and the command line, tell the builder in the channel, and leave the run stopped. Who decides about a process that is not yours is an open ruling (L1 in `v9-OPEN-FOR-LEAD.md`); this file does not hand that decision to the owner.** Never end a process by name or pattern.
(4) Resume. The run stays stopped until you send the runner a message. Two ways: (a) normal resume: `P-4b STOP is cleared: run P-3b, then P-4b, then P-5. Do not repeat P-1 or P-2.` (P-3b ties the control file to the `P-4b.sh` that exists now; if you changed `P-4b.sh`, make `P-4b.control.txt` again first, C2b); (b) fresh start: you delete the folder `$HOME/hadavin-smoke` yourself in this WSL shell (a folder made by P-1 only), then message the runner. Check first and delete (the first command lists it; if the listing is empty or the folder is missing, stop and ask; `rm -r` removes only this folder):
```bash
ls "$HOME/hadavin-smoke" && echo "delete it with: rm -r \"$HOME/hadavin-smoke\""
```
```bash
rm -r "$HOME/hadavin-smoke" && echo deleted
```
Message for (b): `Fresh start: restart at P-1; the RE-PIN step (e) counts run first, as the plan says.` The old `LEAD-GO RE-PIN` line stays valid: do not write a second one (C9 refuses it).
D3. **Who deletes `$HOME/hadavin-smoke`, in which case** (never both): (i) after a P-4b stop and a fresh start (D2 (4b)): YOU delete it by hand, because the run is stopped and the runner is not running S13. (ii) at the normal end of the run, or after a `GONE-FAIL` with exit 3 once S13 got to step 13.9: the RUNNER deletes it (plan step 13.9); you delete nothing, and a new run starts at P-1 only after 13.9 has deleted the folder. (iii) in every other case nobody deletes it.

## E. STOP table (what each STOP means and the next action)
| where | STOP text | what to do next |
|---|---|---|
| section 1 | `STOP: HB ... is not a folder` | write `HB` or `CH` (EDIT POINTS), set the variables again |
| A2 | CR in a patch, or checksum wrong | get the file again from the repository (`git checkout -- <file>`), run A2 again |
| A3 to A5 | `rc` not 0, `Hunk FAILED` | `mv "$W" "$W.old"`, start at A1; never force |
| A6 | counts not 24, 10, 2, 1 | same as above |
| A8 | `already there` | follow the printed text (cmp, then A9 or `mv`) |
| A9 | counts wrong | edit line 3 of `PF` or fix `HB` as printed, run the block again |
| C1 to C4 | `fatal`, `PIN is not ...`, `FILE-MISSING`, CR | the text of the step; send the printed lines to the builder |
| C2 | `FINAL5 or NAMES_OK is not yes` | wait for the round-5 builder's final message; nothing was changed |
| C3b | runner count 0 | ask the runner for its PROGRESS.md path (C3b) |
| C6 | `STOP (reason)` | do not write C9; send `$W/out-c6.txt` to the builder |
| C8b | control does not match | make the control file again (C2b) |
| C9 | `no runner line` or `LEAD-GO already there` | see C3b; a line you did not write = tell the builder |
| D1 | `kill exit=3` | no R2; tell the builder; see D1 |
| P-3b (runner) | `P-4b files STOP` or a CR in a P-4b file | you rewrite `P-4b.sh` or the control file (C2b), then message the runner `P-4b files fixed: run P-3b again` |
| P-4b (runner) | `P-4b-HIT` | D2 |

## Changelog (revision 9, 2026-11-16)
Fixes of the stranger review (items 1 to 14) and the contradiction check: where `pastes\` lives (section 1, `PASTES`) and how `EV` is confirmed (A9, C3b, C9); one variables block for every window, fixed work folder, `PIN` guards (items 3, 7); A8 message without backticks and `EV` defined first (4); STOP table and next actions (5); roles and one meaning of "v5" (6, 9); hard-coded user name replaced by `HB` (7); C2 fill commands, branch check, source of truth for the final head (8); C4 fill commands, empty-field and mismatch rules (9); C2b commands, pointers to the criteria, stand-in end check, WSL user check (10); C3 brief text, stop after P-3a, no edits while the runner reads (11); C6 reading rule and exit 3 explained (12); register and pid file, WSL prerequisites, deletion commands and who deletes (13, 8); `accept` helper (14); A9 flip needs your confirmation and a drive letter. Not changed by this revision: the two patch files and their sha256.
