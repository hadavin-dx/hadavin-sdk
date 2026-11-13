# rv16 review: sonar-p1-quickwins-v3.patch on db54e13 (third independent reviewer)
Preamble rules used: 5, 6, 7, 12, 13 (I am the reviewer; lead runs EGM), 19. No bible R-numbers (not available in this shell). No pushes. Scratch /tmp/work/rv16-1 (clone r/, base worktree base/, venv/ from requirements-dev.txt via uv, py3.13 and a 3.12 install check). Full suite NOT run. rv7/rv10 reports read only at the end.
Installed in sandbox: mksh, yash, posh, ksh93 (dash, busybox 1.36.1, zsh 5.9 already there). NOT available: bash 3.2, csh/fish, Windows, actionlint, SonarCloud, CI.

## Verdict: no Blocker. 1 Major (scanner silently blanks the rest of a file on a common idiom), 3 Minor, 4 Nit. The guard itself held up against every bypass I could construct.

## Findings (failures first)

### MAJOR 1 - hygiene scanner: a here-string with a literal word (`<<< "abc"`, `<<< abc`) starts a bogus heredoc and blanks the rest of the file; the "ends open" safety net does not catch it
`_scan` skips a `<<<` only at its first `<`; at the second `<` the text `<<< "abc"` looks like `<< "abc"` and `_HEREDOC` matches word `abc`, so everything after the next newline is blanked until a line equal to `abc` or EOF. Measured with `_single_bracket_lines`:
- `grep -q a <<< "abc"\n[ -e x ]\n` -> [] (false negative; expected [2])
- `grep -q a <<<"abc"`, `<<< 'abc'`, `cat <<< abc`, `x=$(cat <<< "abc")` -> all [] ; `<<< "$x"` is fine (word must start with a letter).
- `cat <<< 'x' <<EOF\nb\nEOF\n[ -e x ]` -> [].
`ends_open` is False in all of them, so test_sh_scripts_and_workflow_run_blocks... would pass while hiding a real `[ ` for the rest of the file. NOTES claims a scan slip "cannot silently hide the rest of a file": false for this class.
Mutant S7 (drop the `<<<` exclusion): SURVIVED (46 passed); no shipped probe covers `<<<`.
Same class, delimiter characters: `cat <<'E-1'\nx\nE-1\n[ -e x ]` and `<<E.1` -> [] (regex takes `E`, terminator line `E-1` never equals `E`, blanks to EOF, no open flag). Fix at the choke point: handle `<<<` by consuming all three characters; read the heredoc word as the full shell word (strip quotes, any non-blank chars) and, when a heredoc end line is never found, report ends-open. Add probes for both. No current file in the repo has either idiom (repo scan is clean), so no present miss.

### MINOR 2 - scanner false positives with quoted array keys and regex alternation
Quoted text is blanked to spaces, so these match `[` + blank after a command-start character:
- `declare -A m=(["a"]=1 ["b c"]=2)` and `m=(\n ["k"]=v\n)` -> flagged (FP)
- `[[ $x =~ a|[ ]b ]]` and `[[ $x =~ 'a'|[ ] ]]` -> flagged (FP)
- `echo a \<NL>  [ -e x ]` (continuation line starting with `[` as an argument) and `["$x" = y]` (invalid shell) -> flagged.
A false positive fails the test with a message that points at a line that is fine; none exists in the repo today. Cheap fix: blank quoted text with a non-space placeholder (e.g. `_`) so `["a"]` stays `[___]`.

### MINOR 3 - scanner is quadratic on a long single line; 86 s for 1 MB
`"((" not in text[line_start:i]` is a slice per `<<`. 1 MB line of 150 000 `<<` took 86.1 s (my probe; other 1 MB shapes: 0.2-0.5 s, deep `$(` nesting 20 000 deep 0.02 s, unterminated quote 0.3 s, no hang found). Only reachable by a committed adversarial file, not by any real script, so low risk; fix by tracking "seen `((` on this line" as a flag.

### MINOR 4 - README/NOTES claim "dash stops at once" is not true where a `[[` program is on PATH
`busybox` ships a `[[` applet. With a directory holding a `[[` -> busybox link first on PATH, `dash scripts/reset.sh` passes the guard (the probe `[[ a == a ]]` runs the external program) and then works correctly (my semantics check of 12 expressions: identical to bash; DB outside data kept, rc 2). A `[[` shim that is true only for the probe would pass the guard under dash and then misbehave; that needs a hostile PATH, where `python` could be replaced anyway, so I rate it Minor/Nit for safety. Worth one honest word in NOTES ("a shell where `[[` runs").

### NIT 5 - surviving mutants (no behaviour loss today)
- M6 guard `&& echo bash` -> `; echo bash` SURVIVES: equivalent only because `set -e` is active before the guard (dash kills the `$( )` on the failed subshell). Shipping form with `&&` is correct without `set -e` too (I removed `set -eu`: M14 still refuses). So the `&&` is load-bearing but untested; a test running `dash -c` of the guard line without -e would pin it.
- S1 scan without `exec [` survives (no probe; builder listed `exec` in the regex but only `command`/`time` have probes).
- S9 workflow `shell:` key assertion removed survives (no workflow sets `shell:` today; the assertion is untested).
- `posh` (a pure POSIX shell) is refused, same message: correct.

### NIT 6 - Sonar acceptance is unverifiable here
`https://sonarcloud.io/api/rules/show?key=...&organization=hadavin-dx` returns only metadata (no description text) for shell:S7688 ("Use "[[" instead of "[" for conditional tests"), githubactions:S6506 ("HTTPS should be enforced on HTTP clients following redirects"), githubactions:S8541 ("Python package manager scripts should not be executed during installation", CWE-506/829, MEDIUM security), text:S6389, python:S5863. So whether `--only-binary=:all:` vs space form, or `--proto '=https' --proto-redir '=https' --tlsv1.2`, silences S8541/S6506 is UNVERIFIED; the issue messages only print "--only-binary :all:". Issue list check: S7688 offsets (reset.sh 15,20,20,25,28,33; start_all.sh 12,12,16,16) are all converted; no `[ ` command remains in any tracked .sh (grep) or lint.yml; text:S6389 x2 and S5863 touched (scan test + test file pass). Prediction only; the new guard `case` has no `[` command, so I expect no new S7688.

### NIT 7 - pre-existing, unchanged
portal_demo.js:10 shows `scripts/reset.sh` to run directly while git mode is 100644 (Permission denied). Not changed here.

## What I verified, with evidence

Guard bypass attempts (made-up DB in a temp dir outside the repo; `DESK_DB_PATH` outside data/; scratch files only):
- Feature probe `case "$( (eval '[[ a == a ]]') 2>/dev/null && echo bash)"`: PASS in bash, bash --posix, busybox sh/ash, zsh, zsh --emulate sh/ksh, mksh R59, ksh93u+m, yash 2.55 (yash has `[[` as a keyword); REFUSE in dash and posh.
- reset.sh with outside DB, BASH_VERSION unset and exported, in 11 shells x 2 = 22 runs: dash and posh refuse with the new message (rc 2, DB kept); all other shells run to the data/ refusal (rc 2, DB kept). Base (db54e13) kept the DB too, in every shell, because `[ ]` works in dash; the deletion risk exists only for the `[[` form, which the guard now covers.
- `[[` semantics under every shell that passes the probe: 12 expressions (`!= "True"`, `-e` on present/absent file, `-n`, `== "Z"`, `!= off`, `||` of two `-e`) identical to bash in bash, bash --posix, mksh, yash, ksh93, busybox sh, zsh, zsh --emulate sh.
- Exported function shadow: `BASH_FUNC_eval%%=() { return 1; }` under bash: guard refuses (false refusal, safe, rc 2); `return 0`: passes, then the data/ check refuses (rc 2, DB kept); under `bash --posix` bash rejects the function ("`eval': is a special builtin"). dash does not import functions. `eval` is a special builtin and cannot be shadowed by PATH.
- Hostile PATH: busybox `[[` applet link (works as bash, Minor 4); always-true `[[` shim: guard passes, then `[[ "$inside" != "True" ]]` is true -> "refused: not inside data/" (safe); picky shim (true only for `a == a`): guard refuses under dash.
- set -e: the guard sits after `set -eu`; failure inside `$( )` is the left side of `&&`, no abort; `;` variant equals `&&` only because of set -e (Nit 5).
- Behaviour unchanged vs base under bash: reset.sh happy path in data/ with pid files none/empty/stale/foreign: identical outcomes in 8 shells x 4 states, base vs v3 (files left, rc, stdout; only the printed pid differs). start_all.sh with stub python, 15 mode/env cases (keyed, blind, bogus, extra arg, DESK_LEADFLOW_FILE off/empty/x.json/a_b.json, DESK_NUDGE_TO set/empty, DESK_PORT/FAKES_URL, BASH_VERSION exported): rc, stdout, stderr, pid/log files, args and DESK_*/PYTHONPATH env each stub saw identical base vs v3 (3 "DIFF" lines in my harness were temp-dir names in a sed error and a re-used DB dir of mine, not script differences). start_all.sh under mksh, yash, ksh93, busybox sh, zsh, zsh --emulate sh, bash --posix: output identical to bash.
- Documented usage: README (59, 66, new 68) says `bash scripts/...`; `sh scripts/...` was the only usage the refusal changes; portal_demo.js only shows `scripts/reset.sh` (shebang bash); CI workflows do not call the scripts; `.ps1` scripts untouched, no parity change; tests/test_mode_safety ps-missing test passes (guard is a builtin).
- Windows safety: new bash/dash tests are `skipif(WINDOWS ...)`, `_run` powershell branch unchanged, `.gitattributes` forces eol=lf for *.sh/*.yml so the `#!/usr/bin/env bash\n` start check holds, workflow tests only read files, PyYAML in requirements-dev-win.txt (not executed on Windows).
- Gates (DPLD_REQUIRE_SCAN=1, GITLEAKS_BIN=/tmp/work/gl/gitleaks 8.30.1): `pytest tests/test_hygiene.py tests/test_reset_scripts.py tests/test_workflow_files_parse.py tests/test_mode_safety.py`: 154 passed, 8 skipped (all 8 = playwright not installed), 0 failed; gitleaks/scan/scrub tests (6) ran and passed. ruff check clean; ruff format --check 146 files clean; mypy linux and `--platform win32` no issues in 26 files; bandit -ll -r src exit clean (only comment warnings). `uv pip install --require-hashes --only-binary=:all: -r requirements-dev.txt` works on py3.12 and 3.13 (CI uses 3.12). I used uv, not `uv run --group test` (repo has no `test` group, as earlier reviewers saw).
- Scanner probes: 80 snippets + 40 more (shell idioms, repo-style scripts, run blocks, heredocs, continuations, `${#a}`, `${x//[ ]/_}`, `case` patterns `[a-z]*`, `[[ == [a-z]* ]]`, `[[ =~ [\\ ] ]]`, arrays `(a [1]=b)`, comments, `$'..\'..'`, backticks, nested `$( )` in `"..."`, `$(( ))` with shifts, `exec`, `elif`, `until`, `select`, `|&`, `{ }`, `( )`): all correct except findings 1 and 2 above and the builder's own listed holes (`test`, `sudo [`, `env X=1 [`, `$( )` inside heredoc body). `test -e x` is not flagged by design.
- Own mutants (24 total; edit, run, revert; originals restored, `git status` shows only the 10 patch files): reset/start guards removed (both), exit 2->0, probe `test a = a`, probe by BASH_VERSION, `!= "True"` -> `==`, `-n`->`-z`, `&&`->`||` in the leadflow line, pid `||`->`&&`, ps `&&`->`||`, Z `==`->`!=`, alive `!=`->`==`, `!= off`->`!= of`, reset pid `-e`->`-s`, scanner: no `!`, comments not blanked, ends-open always False, `$'` dropped, heredoc never blanked, dq backslash dropped, run blocks not scanned: KILLED. Survived: M6 `;` (equivalent under set -e), M14 guard without set -e (equivalent, still refuses), S1 `exec`, S7 `<<<`, S9 workflow shell key.
- Earlier findings closed: rv10 Major 1 (exported BASH_VERSION bypass) closed by the feature test (measured); rv10 Minor 2 (scan holes) mostly closed, with the new holes above; rv10 Minor 3 (pip `=:all:`) done, test requires it; rv10 Minor 5 (pid -e/-s mutant) KILLED by test_reset_sh_deletes_an_empty_pid_file (I re-ran it: 1 failed); rv7 items 1-6 closed per rv10 and still present.

## Not checked
bash 3.2 (not installable; `[[ ]]` with `==`, `-e`, `-n` has existed since bash 2.02, so I expect no difference, unverified); csh/fish (cannot parse the file, nothing runs); Windows; real CI, actionlint, SonarCloud; the full suite; combined test run with P2/P3.

## Files
Patch: /tmp/demo-lead/handover/demo/sonar/sonar-p1-quickwins-v3.patch. Probes and harness in /tmp/work/rv16-1 (probe.py, probe2.py, probe3.py, run1.sh, run2.sh, run3.sh, mut.py, mut.out). Head: db54e13 + v3 patch.
