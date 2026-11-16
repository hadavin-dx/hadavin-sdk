# apply-v13.py: turns LEAD-CHECKLIST-v5.rev12.md into revision 13 (reads rev12, writes the given output). Usage: python3 apply-v13.py IN OUT
import re, sys
src = open(sys.argv[1], encoding='utf-8').read()
t = src

def sub(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, (n, old[:90])
    t = t.replace(old, new)

# ---------- labels ----------
sub('(revision 12, written 2026-11-16)', '(revision 13, written 2026-11-16)')
sub('(this is revision 12)', '(this is revision 13)')
sub('(see `v12-CHANGES.md`)', '(see `v13-CHANGES.md`)')
sub('the numbers in the tables below were recomputed for revision 11 from rebuilt scratch plans (CHAIN 2, 3, 4). The tests of revision 11 are in `evidence-c11.md` (written by the builder, not by an independent runner; the same limits: no Git Bash, no WSL, no n8n).',
    'the numbers in the tables below were recomputed for revision 11 from rebuilt scratch plans (CHAIN 2, 3, 4). The tests of revision 11 are in `evidence-c11.md` (by the builder) and `evidence-c11-independent.md` (by an independent runner); the tests of revision 13 are in `evidence-c13.md` (by the builder, same limits: no Git Bash, no WSL, no n8n; harness in plain bash with a stand-in `cygpath`).')
sub('you write two small files that check that no unreadable n8n process is left behind (plan step P-4b)',
    'you write two small files that look for an unreadable process that has `n8n` in its command line (plan step P-4b; an unreadable process with another name is NOT found, see the limit in C2b)')

# ---------- section 0: STOP and exit code ----------
sub('A STOP block changes nothing unless its text says it did.',
    'A STOP block changes nothing unless its text says it did. **Since revision 13 a block that printed a STOP line ends with exit code 1** (check with `echo $?` right after the block), so a script that tests only the exit code also sees the STOP; a block that printed no STOP ends with 0. The helper functions return 1 the same way. A later block refuses to run on the result of an earlier STOP through a proof file (`a2-ok.txt`, `rows.rc`, `proof-6.txt`, `proof-c6.txt`, `proof-c8.txt`, `standin-gone.txt`), not through the exit code.')

# ---------- section 1: helper list, flip, pfok, nolink ----------
sub('(`hbok`, `evok`, `aside`, `planok`,', '(`hbok`, `evok`, `pfok`, `nolink`, `aside`, `planok`,')
old_flip = [l for l in t.split('\n') if l.startswith('flip() {')][0]
new_flip = ('pfok() { if [ -f "$PF" ] && [ ! -L "$PF" ]; then return 0; fi; echo "STOP PF: the plan file PF ($PF) does not exist or is a symbolic link (a link could send a change to another file). Next: do A8 (copy the patched plan); if PF is a link, tell the builder, then aside \\"\\$PF\\" and do A8 again (every fill made in PF is lost)."; return 1; }\n'
 'nolink() { local f; for f in "$@"; do if [ -L "$f" ]; then echo "STOP LINK: $f is a symbolic link; it must be a plain file. Next: write nothing; tell the builder, then aside \\"$f\\" and make the file again with the step that writes it."; return 1; fi; done; return 0; }\n'
 'flip() { pfok || return 1; for n in "$@"; do sed -i "s/LEAD-FILL $n\\\\b/LEAD-DECIDED $n/g" "$PF" || { echo "STOP B1: sed could not change PF. Next: close the editor and the program that holds PF; run the block again."; return 1; }; done; }')
sub(old_flip, new_flip)

# p4bcheck and c7check: refuse links / missing PF
sub('p4bcheck() { local B K ok f; B="$PASTES/P-4b.sh"; K="$PASTES/P-4b.control.txt"; ok=1; for f in',
    'p4bcheck() { local B K ok f; B="$PASTES/P-4b.sh"; K="$PASTES/P-4b.control.txt"; ok=1; nolink "$B" "$K" || return 1; for f in')
sub('c7check() { local r a b c d cr bom u nu; r=0;', 'c7check() { local r a b c d cr bom u nu; pfok || return 1; r=0;')

# ---------- diffwords (observation 1) ----------
lines = t.split('\n')
i = [k for k, l in enumerate(lines) if l.startswith('diffwords() {')][0]
assert lines[i+3].rstrip().endswith('echo "== end"; return 0; }'), lines[i+3][-80:]
new_dw = [
 'diffwords() { local f D O O3; pinok || { echo "STOP C5: PIN is empty or not a 40-character commit of $WT. Next: do C2."; return 1; }',
 '  printf \'%s\' "$OLD" | grep -qE \'^[0-9a-f]{7,40}$\' || { echo "STOP C5: OLD is [$OLD], not 7 to 40 lowercase hex characters (a commit sha). An empty value, a name such as HEAD or a value that starts with - is refused, so it can never reach git as an option or as a name that moves. Next: write the old pin of line 3 of the plan (7 characters) as OLD in section 1, set the variables."; return 1; }',
 '  O=$(git -C "$WT" rev-parse --verify -q "$OLD^{commit}" 2>/dev/null); if [ -n "$O" ]; then [ "$O" != "$PIN" ] || { echo "STOP C5: OLD is the same commit as PIN, so the diff would be empty. Next: check OLD against line 3 of the plan; tell the builder."; return 1; }; echo known; for f in n8n_start.sh n8n_kill.py; do echo "== $f"; git -C "$WT" diff --no-color "$O" "$PIN" -- "scripts/$f" | grep -iE \'^[-+].*(echo|print|die|refused|confirmed|exit|return)\'; done',
 '  else O3=; [ -d "$W3" ] && O3=$(git -C "$W3" rev-parse --verify -q "$OLD^{commit}" 2>/dev/null); [ -n "$O3" ] || { echo "STOP C5: the old commit $OLD is neither in $WT nor in the round-3 worktree $W3. Next: check W3N and OLD against line 3 of the plan; tell the builder."; return 1; }; [ "$O3" != "$PIN" ] || { echo "STOP C5: OLD is the same commit as PIN, so the diff would be empty. Next: check OLD against line 3 of the plan; tell the builder."; return 1; }',
 '    echo unknown; D=$(mktemp -d) || { echo "STOP C5: mktemp failed. Next: check the temp folder and the disk, then run C5 again."; return 1; }; for f in n8n_start.sh n8n_kill.py; do echo "== $f"; git -C "$W3" show "$O3:scripts/$f" > "$D/old" && git -C "$WT" show "$PIN:scripts/$f" > "$D/new" || { echo "STOP C5: git show failed for scripts/$f. Next: tell the builder."; rm -r "$D"; return 1; }; git diff --no-index --no-color -U0 "$D/old" "$D/new" | grep -iE \'^[-+].*(echo|print|die|refused|confirmed|exit|return)\'; done; rm -r "$D"; fi; echo "== end"; return 0; }',
]
lines[i:i+4] = new_dw
t = '\n'.join(lines)
sub('`OLD` the old 7-character pin' if False else 'the names in the plan header (round-5 worktree folder, round-3 worktree folder, the old 7-character pin; check them against line 2 and 3 of the plan)',
    'the names in the plan header (round-5 worktree folder, round-3 worktree folder, the old 7-character pin; check them against line 2 and 3 of the plan; `OLD` must be 7 to 40 lowercase hex characters: C5 and C6 refuse anything else, also `HEAD` and a value that starts with `-`)')

# ---------- chain_step (observation 6): patch must exist ----------
lines = t.split('\n')
i = [k for k, l in enumerate(lines) if l.startswith('  if command -v patch > /dev/null 2>&1; then (cd "$W"')][0]
assert lines[i+1].startswith('  elif [ "$5" = both ]') and lines[i+2].startswith('  else echo "STOP $1: the program patch is not installed')
new_cs = '  command -v patch > /dev/null 2>&1 || { echo "STOP $1: the program patch is not installed (command -v patch finds nothing in this shell). Next: nothing was changed. Install patch (Git for Windows has it under usr/bin; check PATH), open a new Git Bash window, set the variables, run this block again. There is no git apply fallback any more."; return 1; }\n  (cd "$W" && patch -p1 -N -t --dry-run < "$PC/$2" > /dev/null && patch -p1 -N -t --no-backup-if-mismatch < "$PC/$2" > /dev/null) || { echo "STOP $1: patch failed. Next: aside \\"$W\\", start at A1; never force."; return 1; }'
lines[i:i+3] = [new_cs]
t = '\n'.join(lines)
sub('A5. If `patch` is not installed in Git Bash (`command not found`), A3 and A4 use `git apply` by themselves (same checksums; they print no hint, only `ok`). **Patch 3 and chain step 4 cannot be done without `patch`** (git apply fails on patch 3; tested): then write `CHAIN=2` in section 1, set the variables, and go on. A6 expects the checksum of the CHAIN you wrote. If your work folder lies inside a git repository, `git apply` may skip files, so the blocks refuse `git apply` there (they print a STOP): install `patch` or move `HB` outside the repository.',
    'A5. **Every chain step needs the program `patch`** (revision 13: the earlier `git apply` fallback is gone, because without `patch` A3 and A4 printed only `ok` and gave no hint that a different tool had been used; patch 3 never worked with `git apply` anyway). If `patch` is missing, A3, A4 and A5b print `STOP <id>: the program patch is not installed` and change nothing: install it (Git for Windows has it under `usr/bin`), open a new Git Bash window, set the variables, run the block again. The tools check in A0 prints `missing patch` first.')
sub('| 2 | the original plan, repaired (patch 1) and made ready for re-pinning (patch 2: the four placeholder places, the P-4b check, the release line) | 172 min = 2 h 52 min | `patch` or `git apply` |',
    '| 2 | the original plan, repaired (patch 1) and made ready for re-pinning (patch 2: the four placeholder places, the P-4b check, the release line) | 172 min = 2 h 52 min | `patch` |')
sub('| 3 | CHAIN 2 plus the two gate rows (patch 3): a pass/fail check after S10 that one message id sent twice and ten times is processed once | 174 min = 2 h 54 min | `patch` (git apply cannot do patch 3) |',
    '| 3 | CHAIN 2 plus the two gate rows (patch 3): a pass/fail check after S10 that one message id sent twice and ten times is processed once | 174 min = 2 h 54 min | `patch` |')
sub('Tools check (run it once; it only reads): `patch` is needed for CHAIN 3 and 4,', 'Tools check (run it once; it only reads): `patch` is needed for every CHAIN,')
sub('no `patch` for patch 3, or `git apply` refused inside a git repository) | read the line: it says either "go to A6" (nothing changed), "run A2", or `aside "$W"` and start at A1; never force a patch; no `patch` and patch 3 = `CHAIN=2` |',
    'or the program `patch` is not installed) | read the line: it says either "go to A6" (nothing changed), "run A2", "install patch" or `aside "$W"` and start at A1; never force a patch |')

# ---------- A1, A2 ----------
sub('echo "ok A1: made $W"; fi; fi\n', 'echo "ok A1: made $W"; fi; else false; fi\n')
sub('if [ ! -f "$PC/$f" ]; then echo "STOP A2: $f is missing in $PC. Next: get the folder again from the repository (section 0b)."; bad=1; continue; fi;',
    'if [ ! -f "$PC/$f" ]; then echo "STOP A2: $f is missing in $PC. Next: get the folder again from the repository (section 0b)."; bad=1; continue; fi; if [ -L "$PC/$f" ]; then echo "STOP A2: $f in $PC is a symbolic link. Next: get the file again as a plain file from the repository (section 0b)."; bad=1; continue; fi;')
sub('else echo "A2 is not clean: A3 to A5b4 refuse to run until it is."; fi; fi; }', 'else echo "A2 is not clean: A3 to A5b4 refuse to run until it is."; false; fi; fi; }')

# ---------- A8 (PF link, stray files, rc) ----------
old = 'hbok && planok "$PT" A8 && { mkdir -p "$(dirname "$PF")"; if [ -e "$PF" ]; then if cmp -s "$PT" "$PF"; then echo "ok A8 (PF already equals the untouched patched plan; nothing changed): go on to A9"; else echo "STOP A8:'
new = 'hbok && planok "$PT" A8 && { r=0; mkdir -p "$(dirname "$PF")"; if ls "$W/inputs" 2>/dev/null | grep -qE \'[.](orig|rej)$\'; then echo "STOP A5c: a .orig or .rej file is in $W/inputs; A8 refuses. Next: aside \\"$W\\", start at A1."; r=1; elif [ -L "$PF" ]; then echo "STOP PF: PF ($PF) is a symbolic link. Next: tell the builder; aside \\"\\$PF\\" and run A8 again."; r=1; elif [ -e "$PF" ]; then if cmp -s "$PT" "$PF"; then echo "ok A8 (PF already equals the untouched patched plan; nothing changed): go on to A9"; else r=1; echo "STOP A8:'
sub(old, new)
sub('echo "run lines in PROGRESS.md (lines not starting with NOTE lead): $(grep -v \'^NOTE lead\' "$EV/PROGRESS.md" | grep -c .)"; fi; else cp "$PT" "$PF" && cmp "$PT" "$PF" && echo "ok A8 copied"; fi; }',
    'echo "run lines in PROGRESS.md (lines not starting with NOTE lead): $(grep -v \'^NOTE lead\' "$EV/PROGRESS.md" | grep -c .)"; fi; else cp "$PT" "$PF" && cmp "$PT" "$PF" && echo "ok A8 copied" || { echo "STOP A8: the copy failed. Next: check the folder and the disk; nothing else changed."; r=1; }; fi; [ "$r" = 0 ]; }')

# ---------- A9: flip failure ----------
sub('then flip 9; echo "ok A9: marker 9 flipped; left:"; grep -n -o \'LEAD-FILL 9\' "$PF"; echo "(end of list)"; else',
    'then flip 9 && { echo "ok A9: marker 9 flipped; left:"; grep -n -o \'LEAD-FILL 9\' "$PF"; echo "(end of list)"; }; else')

# ---------- B2 ----------
sub('elif [ ! -f "$PF" ]; then echo "STOP B2: PF does not exist yet. Next: do A8 first."; else k=',
    'elif ! pfok; then false; else k=')
sub('if [ "$k" = 1 ]; then sed -i "s|$OLDT|$NEWT|" "$PF" && echo "ok B2: outcome A written into PF"; fi; accept 2; fi; fi; }',
    'if [ "$k" = 1 ]; then if sed -i "s|$OLDT|$NEWT|" "$PF"; then echo "ok B2: outcome A written into PF"; accept 2; else echo "STOP B2: sed could not change PF. Next: close the editor; run the block again."; fi; else accept 2; fi; fi; fi; }')

# ---------- C2 (observation 5, 1) ----------
sub('hbok && { if [ "$FINAL5" != yes ] || [ "$NAMES_OK" != yes ]; then echo "STOP C2:',
    'hbok && { if ! pfok; then false; elif [ "$FINAL5" != yes ] || [ "$NAMES_OK" != yes ]; then echo "STOP C2:')
sub('grep -qE \'^[A-Za-z0-9._/-]+$\'; then echo "STOP C2: BR has unsafe characters or is empty.',
    'grep -qE \'^[A-Za-z0-9._/][A-Za-z0-9._/-]*$\'; then echo "STOP C2: BR has unsafe characters, starts with -, or is empty.')
sub('"$PF"; flip 5 7; echo "ok C2"; left; echo "left placeholders (sha/branch must be 0): $(grep -c -E \'<FINAL-(SHA|BRANCH)\' "$PF"); table rows still open: $(grep -c \'<FINAL-LINES>\' "$PF") (must be 20 until C4)"; fi; }',
    '"$PF" && flip 5 7; then echo "ok C2"; left; echo "left placeholders (sha/branch must be 0): $(grep -c -E \'<FINAL-(SHA|BRANCH)\' "$PF"); table rows still open: $(grep -c \'<FINAL-LINES>\' "$PF") (must be 20 until C4)"; else echo "STOP C2: the change of PF did not work. Next: close the editor and any program that holds PF; tell the builder; run C2 again (it is safe to repeat)."; fi; }')
sub('else sed -i -e "s|<FINAL-SHA-FULL>|$PIN|g"', 'elif sed -i -e "s|<FINAL-SHA-FULL>|$PIN|g"')
sub('The block does everything only when every check holds: 40 hex characters, a branch name with safe characters,',
    'The block does everything only when every check holds: PF exists and is not a symbolic link, 40 hex characters, a branch name with safe characters (not starting with `-`),')

# ---------- C2b step (2): save P-4b.sh, banned word STOP; limit sentence ----------
sub('{ grep -n -i -E \'kill|env\\.sh\' "$PASTES/P-4b.sh"; echo "(end: nothing above is right)"; }; [ "$(tail -n 1',
    '{ grep -n -i -E \'kill|env\\.sh\' "$PASTES/P-4b.sh"; echo "(end: nothing above is right)"; [ "$(grep -c -i -E \'kill|env\\.sh\' "$PASTES/P-4b.sh")" = 0 ] || echo "STOP C2b: the word kill or env.sh is in P-4b.sh (lines above). Next: aside \\"$PASTES/P-4b.sh\\" and run this block again; tell the builder."; } || bw=1; [ "$(tail -n 1')
sub('(2) Save the proposal script as `P-4b.sh` (extracts', '(2) **What `P-4b.sh` can and cannot find (stated limit).** It prints a line only for a process of YOUR user that has `n8n` in its command line (any letter case) and whose `environ` cannot be read. It does not look at any other process: an unreadable process with another name (for example a process started under a different command line) is NOT detected, by this script or by any other block of this file. **The lead must check that by eye** before C9, in WSL, with a read-only command: `ps -u "$(id -u)" -o pid,args` (every process of the user with its command line), and tell the builder about any process you cannot explain. The same holds for the control file: it proves only that the script found the stand-in, which has `n8n` in its name.\nSave the proposal script as `P-4b.sh` (extracts')

sub('else mkdir -p "$PASTES" && sed -n', 'else bw=0; mkdir -p "$PASTES" && sed -n')
sub('|| echo "STOP C2b: the saved P-4b.sh does not end', '|| { bw=1; echo "STOP C2b: the saved P-4b.sh does not end')
sub('Next: run A2; then aside \\"$PASTES/P-4b.sh\\" and run this block again."; fi; }', 'Next: run A2; then aside \\"$PASTES/P-4b.sh\\" and run this block again."; }; [ "$bw" = 0 ]; fi; }')
# ---------- WSL-3/4: symlinks, rc ----------
sub('else T=$(mktemp) || { echo "STOP C2b: mktemp failed. Next: check the disk and /tmp, run WSL-3 again."; T=; }; if [ -n "$T" ]; then',
    'elif [ -L P-4b.sh ] || [ -L P-4b.control.txt ]; then echo "STOP LINK: P-4b.sh or P-4b.control.txt is a symbolic link. Next: write nothing; tell the builder."; else T=$(mktemp) || { echo "STOP C2b: mktemp failed. Next: check the disk and /tmp, run WSL-3 again."; T=; }; if [ -n "$T" ]; then')
sub('cat "$T"; fi; rm -f "$T"; fi; fi\n', 'cat "$T"; fi; rm -f "$T"; [ "$rc" = 0 ] && [ -s P-4b.control.txt ]; else false; fi; fi\n')
sub('elif [ ! -s P-4b.control.txt ]; then echo "STOP C2b: P-4b.control.txt is missing or empty.',
    'elif [ -L P-4b.control.txt ] || [ -L standin-gone.txt ]; then echo "STOP LINK: P-4b.control.txt or standin-gone.txt is a symbolic link. Next: write nothing; tell the builder."; elif [ ! -s P-4b.control.txt ]; then echo "STOP C2b: P-4b.control.txt is missing or empty.')

# ---------- SP note (C2b) ----------
old = 'case "$SP" in \'\'|*[!0-9]*) echo "STOP C2b: SP must be digits. Next: write the pid printed by WSL-2 and run again.";; *) if evok; then if [ -s "$F" ] && [ -n "$(tail -c 1 "$F")" ]; then printf \'\\n\' >> "$F"; fi; printf \'NOTE lead stand-in pid=%s %s\\n\' "$SP" "$(date -u +%Y-%m-%dT%H:%MZ)" >> "$F" && tail -n 2 "$F"; fi;; esac'
new = 'case "$SP" in \'\'|*[!0-9]*) echo "STOP C2b: SP must be digits. Next: write the pid printed by WSL-2 and run again.";; *) if evok; then if [ -L "$F" ] || { [ -e "$F" ] && [ ! -f "$F" ]; }; then echo "STOP LINK: $F is a symbolic link or not a plain file. Next: write nothing; tell the builder."; else if [ -s "$F" ] && [ -n "$(tail -c 1 "$F")" ]; then printf \'\\n\' >> "$F"; fi; printf \'NOTE lead stand-in pid=%s %s\\n\' "$SP" "$(date -u +%Y-%m-%dT%H:%MZ)" >> "$F" && tail -n 2 "$F" || echo "STOP C2b: the note could not be written (read-only file?). Next: nothing was noted; tell the builder."; fi; else false; fi;; esac'
sub(old, new)

# ---------- C3b ----------
old = 'hbok && { echo "runner lines in PROGRESS.md: $(grep -v \'^NOTE lead\' "$EV/PROGRESS.md" 2>/dev/null | grep -c .) (must be 1 or more)"; tail -n 3 "$EV/PROGRESS.md"; if [ -f "$SF" ]; then echo "strings.txt exists"; else echo "STOP C3b: strings.txt is missing. Next: ask the runner (see below)."; fi; }'
new = 'hbok && { n=$(grep -v \'^NOTE lead\' "$EV/PROGRESS.md" 2>/dev/null | grep -c .); echo "runner lines in PROGRESS.md: $n (must be 1 or more)"; tail -n 3 "$EV/PROGRESS.md"; r=0; if [ "$n" = 0 ]; then echo "STOP C3b: no runner line in PROGRESS.md. Next: ask the runner (see below)."; r=1; fi; if [ -f "$SF" ]; then echo "strings.txt exists"; else echo "STOP C3b: strings.txt is missing. Next: ask the runner (see below)."; r=1; fi; [ "$r" = 0 ]; }'
sub(old, new)

# ---------- C4 fill ----------
sub('grep "^| $sid |" "$PF" | grep -q -F -e "$ss"', 'grep "^| $sid |" "$PF" | tr -d \'\\\\\' | grep -q -F -e "$ss"')

sub('hbok && { if [ "$(cat "$W/rows.rc" 2>/dev/null)" != 0 ]; then echo "STOP C4: the rows block above has not run clean',
    'hbok && { if ! pfok; then false; elif [ "$(cat "$W/rows.rc" 2>/dev/null)" != 0 ]; then echo "STOP C4: the rows block above has not run clean')
sub('echo "ok C4: now run: accept 6"; fi; fi; }', 'echo "ok C4: now run: accept 6"; else echo "STOP C4: the rows are not all filled (open $o, bad $bad) or H1 or H2 is FILE-MISSING; question 6 stays closed. Next: tell the builder; C4 stays open."; fi; fi; }')

# ---------- C6 (observation 2): text only; rc ----------
sub('sed -n \'/^== n8n_kill.py/,/^== end/p\' "$W/out-c6.txt"; fi; }', 'sed -n \'/^== n8n_kill.py/,/^== end/p\' "$W/out-c6.txt"; [ "$r" = ACCEPT ]; fi; }')
sub('**What ACCEPT proves, plainly: only that the text `exit 3` or `return 3` exists in the `n8n_kill.py` part. It does not prove that the line is code or that the script really exits 3.**',
    '**What ACCEPT proves, plainly: only that the text `exit 3` or `return 3` exists in the `n8n_kill.py` part. It does not prove that the line is code or that the script really exits 3.** It is a text check and stays one on purpose (decision of revision 13): ACCEPT is also printed for `print("exit 3")` (not an exit at all), for `EXIT 3` in any letter case and for `os._exit(3)` (a real exit, but not a form the plan names; `evidence-c13.md` has the raw output). A stricter pattern would not help: a text check cannot tell code from a string or a comment on the same line, the plan\'s own acceptance rule is a text rule, and `acc5.sh` is fingerprinted in A2. The reading rule below is the real check, and it is yours.')
sub('(a) every `+` line with `exit` or `return` is one of `exit 2`, `exit 3`, `return 3` or the usual `sys.exit(main())`;',
    '(a) every `+` line with `exit` or `return` is one of `exit 2`, `exit 3`, `return 3` or the usual `sys.exit(main())`, and each is code: a line where `exit 3` is only text inside quotes or inside `print(` (for example `print("exit 3")`) is not an exit, answer no;')

# ---------- C8 (proof for C9) ----------
sub('hbok && { if [ -z "$BR" ]; then echo "STOP C8: BR is empty. Next: do C2 (BR and WTN), then C8 again."; else bad=0;',
    'hbok && { rm -f "$W/proof-c8.txt"; if ! pfok; then false; elif [ -z "$BR" ]; then echo "STOP C8: BR is empty. Next: do C2 (BR and WTN), then C8 again."; else bad=0;')
sub('[ "$bad" = 0 ] && echo "ok C8"; fi; }', 'if [ "$bad" = 0 ]; then sha256sum "$PF" | cut -c1-64 > "$W/proof-c8.txt" && echo "ok C8"; else echo "STOP C8: see the lines above. Next: fix them, then C7 and C8 again."; fi; fi; }')
sub('Expected: `ok C8`. (The plan', 'Expected: `ok C8` (it writes the proof file `proof-c8.txt` with the checksum of `PF`; C9 refuses without it and refuses if `PF` changed after it). (The plan')

sub('then echo "STOP C8: the plan still names its guess $guess in $(printf \'%s\\n\' "$names" | grep -c -x -F -- "$guess") places,', 'then cnt=$(printf \'%s\\n\' "$names" | grep -c -x -F -- "$guess"); echo "STOP C8: the plan still names its guess $guess in $cnt places,')
# ---------- C8b ----------
old = 'hbok && { p4bcheck; if [ "$(cat "$PASTES/standin-gone.txt" 2>/dev/null)" = "gone control=$(sha256sum "$PASTES/P-4b.control.txt" | cut -c1-16)" ]; then echo "ok C8b: stand-in gone for the current control file"; else echo "STOP C8b: standin-gone.txt is missing or belongs to another control file. Next: run WSL-4 again."; fi; }'
new = 'hbok && { r=0; if ! p4bcheck; then r=1; elif [ -L "$PASTES/standin-gone.txt" ]; then echo "STOP LINK: standin-gone.txt is a symbolic link. Next: write nothing; tell the builder."; r=1; elif [ "$(cat "$PASTES/standin-gone.txt" 2>/dev/null)" = "gone control=$(sha256sum "$PASTES/P-4b.control.txt" | cut -c1-16)" ]; then echo "ok C8b: stand-in gone for the current control file"; else echo "STOP C8b: standin-gone.txt is missing or belongs to another control file. Next: run WSL-4 again."; r=1; fi; [ "$r" = 0 ]; }'
sub(old, new)

# ---------- C9 ----------
sub('hbok && { F="$EV/PROGRESS.md"; if [ ! -d "$EV" ]; then echo "STOP C9: EV is not an existing folder. Next: check EV and A8."; elif ! pinok;',
    'hbok && { F="$EV/PROGRESS.md"; if [ ! -d "$EV" ]; then echo "STOP C9: EV is not an existing folder. Next: check EV and A8."; elif [ -L "$F" ] || { [ -e "$F" ] && [ ! -f "$F" ]; }; then echo "STOP LINK: PROGRESS.md is a symbolic link or not a plain file: nothing is written through it. Next: tell the builder."; elif ! pinok;')
sub('elif [ "$(cat "$PASTES/standin-gone.txt" 2>/dev/null)" != "gone control=$(sha256sum "$PASTES/P-4b.control.txt" | cut -c1-16)" ]; then echo "STOP C9: the stand-in is not proven gone',
    'elif [ -L "$PASTES/standin-gone.txt" ] || [ "$(cat "$PASTES/standin-gone.txt" 2>/dev/null)" != "gone control=$(sha256sum "$PASTES/P-4b.control.txt" | cut -c1-16)" ]; then echo "STOP C9: the stand-in is not proven gone')
sub('elif [ ! -f "$SF" ]; then echo "STOP C9: strings.txt is missing. Next: C3b."; elif grep -q',
    'elif [ "$(cat "$W/proof-c8.txt" 2>/dev/null)" != "$(sha256sum "$PF" | cut -c1-64)" ]; then echo "STOP C9: C8 has not printed ok for this PF (no proof-c8.txt, or PF changed after C8). Next: run C7 and C8 again."; elif [ ! -f "$SF" ]; then echo "STOP C9: strings.txt is missing. Next: C3b."; elif grep -q')
sub('else if [ -s "$F" ] && [ -n "$(tail -c 1 "$F")" ]; then printf \'\\n\' >> "$F"; echo "(the last line had no line end: one was added)"; fi; printf \'LEAD-GO RE-PIN %s pin=%s plan=%s\\n\' "$(date -u +%Y-%m-%dT%H:%MZ)" "$PIN" "$(sha256sum "$PF" | cut -c1-16)" >> "$F" && tail -n 2 "$F"; fi; }',
    'else if [ -s "$F" ] && [ -n "$(tail -c 1 "$F")" ]; then printf \'\\n\' >> "$F" && echo "(the last line had no line end: one was added)"; fi; printf \'LEAD-GO RE-PIN %s pin=%s plan=%s\\n\' "$(date -u +%Y-%m-%dT%H:%MZ)" "$PIN" "$(sha256sum "$PF" | cut -c1-16)" >> "$F" && tail -n 2 "$F" || echo "STOP C9: the line could not be written (read-only file or no space?). Next: nothing was released; check that you may write PROGRESS.md; tell the builder."; fi; }')
sub('`strings.txt` exists; no `LEAD-GO RE-PIN` line is there yet', '`strings.txt` exists; C8 printed ok for the `PF` as it is now (`proof-c8.txt`); `PROGRESS.md` is a plain file, not a symbolic link; no `LEAD-GO RE-PIN` line is there yet')

# ---------- D1 ----------
sub('if ! hbok || [ ! -d "$EV" ]; then echo "STOP D1: wrong shell or EV is not a folder. Next: section 1."; elif [ "$((10#$PID))" -lt 2 ]',
    'if ! hbok || [ ! -d "$EV" ]; then echo "STOP D1: wrong shell or EV is not a folder. Next: section 1."; elif [ -L "$F" ] || { [ -e "$F" ] && [ ! -f "$F" ]; }; then echo "STOP LINK: PROGRESS.md is a symbolic link or not a plain file: nothing is written through it. Next: write nothing; tell the builder."; elif [ "$((10#$PID))" -lt 2 ]')
sub('printf \'LEAD-YES R2 pid=%s %s\\n\' "$PID" "$(date -u +%Y-%m-%dT%H:%MZ)" >> "$F" && tail -n 2 "$F"; fi;; esac;; esac',
    'printf \'LEAD-YES R2 pid=%s %s\\n\' "$PID" "$(date -u +%Y-%m-%dT%H:%MZ)" >> "$F" && tail -n 2 "$F" || echo "STOP D1: the line could not be written (read-only file?). Next: no permission was given; tell the builder."; fi;; esac;; esac')

# ---------- D2 intro: limit ----------
sub('(3) Whose process is it? Yours only if', '(3) **Limit:** a hit line exists only for a process with `n8n` in its command line; an unreadable process with another name is not listed (see C2b step 2). Whose process is it? Yours only if')

# ---------- table E ----------
sub('| ASIDE | `aside` could not move',
    '| PF | the plan file `PF` does not exist or is a symbolic link | do A8 first; for a link tell the builder, then `aside "$PF"` and A8 again |\n| LINK | a file that must be a plain file (`PROGRESS.md`, `P-4b.sh`, `P-4b.control.txt`, `standin-gone.txt`, a file of `$PC`) is a symbolic link | write nothing; tell the builder; `aside` the link and make the file again with the step that writes it |\n| ASIDE | `aside` could not move')
sub('| C8b / C9 | a condition of the release is not met (PIN not the branch tip, no C6 ACCEPT, P-4b files, stand-in not proven gone, last runner line not `P-3a done`, strings.txt missing, a LEAD-GO line already there) |',
    '| C8b / C9 | a condition of the release is not met (PIN not the branch tip, no C6 ACCEPT, C8 not ok for this `PF`, P-4b files, stand-in not proven gone, last runner line not `P-3a done`, strings.txt missing, a LEAD-GO line already there, the line could not be written) |')
sub('| C5 / C6 | PIN empty, old commit not found in `$WT` or `$W3`, `git show` failed, or acc5.sh printed STOP |',
    '| C5 / C6 | PIN empty, `OLD` not 7 to 40 lowercase hex characters (also `HEAD` or a value starting with `-`), `OLD` the same commit as `PIN`, old commit not found in `$WT` or `$W3`, `git show` failed, or acc5.sh printed STOP |')
sub('| C8 | BR empty, the plan still names', '| C8 | PF missing, BR empty, the plan still names')
sub('| C2 | FINAL5 or NAMES_OK not yes, PIN or BR wrong,', '| C2 | PF missing, FINAL5 or NAMES_OK not yes, PIN or BR wrong (BR must not start with `-`),')
sub('| C3b | strings.txt missing or the runner count is 0 |', '| C3b | strings.txt missing or the runner count is 0 (both print STOP) |')
sub('| C2b / C2c | a P-4b file is missing, has CR or non-ASCII, holds a banned word,', '| C2b / C2c | a P-4b file is missing, has CR or non-ASCII, holds a banned word (also when saving it in step 2),')

# ---------- changelog ----------
sub('## Changelog\n', '## Changelog\nRevision 13 (2026-11-16): fixes of the hostile-input observations 1 to 7 of the independent evidence run `evidence-c11-independent.md`: `OLD` must be hex and differ from `PIN`, `BR` must not start with `-`; `acc5.sh` stays a text check and the text now says what it accepts; every STOP ends the block with exit code 1 (blocks tested are listed in `evidence-c13.md`); C8 writes `proof-c8.txt` and C9 refuses without it; C9, D1 and the stand-in note refuse a symbolic `PROGRESS.md` and print STOP when the write fails; `PF` missing or a symbolic link is refused (`STOP PF`), also the control file, `P-4b.sh`, `standin-gone.txt` and the files of `$PC` (`STOP LINK`); A3, A4 and A5b print STOP when `patch` is missing (the `git apply` fallback is removed); the limit of `P-4b.sh` is stated in C2b step 2; table in `v13-CHANGES.md`.\n\n')

# ---------- exit-code wrap of every STOP echo in the pasted blocks ----------
lines = t.split('\n')
out = []; inblk = False; bi = -1
pat = re.compile(r'echo "STOP (?:[^"\\]|\\.)*"')
for ln in lines:
    if ln == '```bash':
        inblk = True; bi += 1; out.append(ln); continue
    if ln == '```':
        inblk = False; out.append(ln); continue
    if inblk and bi not in (0, 1, 2):
        ln = pat.sub(lambda m: '{ ' + m.group(0) + '; false; }', ln)
    out.append(ln)
t = '\n'.join(out)
open(sys.argv[2], 'w', encoding='utf-8').write(t)
print('written', sys.argv[2], len(t.split('\n')), 'lines')
