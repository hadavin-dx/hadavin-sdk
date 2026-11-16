# fix-f8-r10d: fixes for the two reviews of F8 diff r10c (FIXER log)
Made-up data only; no secret printed. Words here are unverified except where raw command output is pasted.

## FAILURES AND UNCERTAIN POINTS FIRST
1. I did not commit; `git status --short flow-check` is empty at the end only because someone else's "board" snapshot commits (seen in `git log`: 286960246, bbac73e38, 681cc3f45) already contain my edits. I did not run `git add` or `git commit`.
2. MY SLIP: for the A2 mutation proof I first wrote a temporary copy named `flow-check/run_all_mut.sh`. A board snapshot commit (286960246, 12:17:13Z) captured it in git. I deleted the file; `git status` showed ` D flow-check/run_all_mut.sh` for a moment. I did not touch the git index. The file may still be in git history/index: the lead decides (`git rm --cached` is not mine to run). The second mutation proof was done by editing `run_all.sh` in place and restoring it byte for byte (`cmp` printed "restored").
3. Unexplained: during one run, `raw/selftest-new.txt` (192 lines) and `raw/test-take-check.txt` (36 lines) were seen cut short although the script printed exit 0 for both. Another session writing the same shared `raw/` folder at the same time is the likely cause (this is exactly B4), but I did not prove it. Both final runs afterwards were complete (see below). A final run with its own raw folder (RUN_ALL_RAW) gave the same result as the default one.
4. Not checked: a non-root permission case; a hostile node name that imitates an output line (reviewer B minor); the swap race A-B-A (reviewer B minor); `PATH`/`BASH_ENV` hardening of take_check.sh (reviewer B minor); lint scope mismatch from reviewer A (ruff format of inputs/*.md and bandit on tools/scratch are outside flow-check, outside my allowed folder; I ran ruff and bandit on flow-check only). The `check_flows.py` logic was not touched.
5. The pin's `# reviewed by:` line is still the flows-audit session line (a person must confirm it; I cannot). A bare `take_check.sh --flows <patched>` therefore still exits 4 (`pin not yet confirmed by the lead`). Next step: the lead reads the 4 WARN lines and the flows sha, then replaces that one line with `# reviewed by: NAME, YYYY-MM-DD`.
6. The flows sha256 now pinned (989f5529...) was taken from one run_all.sh generation of the patched copy; later runs reproduce it (every run in this log exited 5 with "WARN set equals ..." and no sha mismatch), so the generator is deterministic in my 5 runs. It will have to be re-pinned by a person whenever a patch or the generator changes.

## What was fixed (each confirmed against the scripts first)
| Id | Reviewer claim | Confirmed? | Fix |
|---|---|---|---|
| A1 | pin line 1 says a person read each one | yes (take-warns.pin:1) | line 1 now says only the WARN lines are hashed and comment lines are not protected |
| A2 | tcfail wanted line may be on any line | yes (run_all.sh tcfail) | wanted text must be on a line starting `!!! ` or `FAIL `; three cases that wanted a `WARN ` line now want the `!!!` line and check the file-specific WARN line separately; key-check-absent now prints its own `!!! The take needs F-002 ...` line |
| B1 | no enforced sha of the flow files | yes | pin header `# flows sha256 (...)`; missing line or different sha = exit 4; `--write-warn-pin` writes the line; sha problem is allowed to be rewritten by a new pin |
| B2 | reviewer line keywords only | yes | grammar `NAME, YYYY-MM-DD[, note]`, name of letters/space/./'/- with 3+ letters, no stand-in word (tbd, x, claude, agent, session, bot, assistant, model, lead, person, placeholder...), real date, not in the future |
| B3 | TAKE_CHECK_TEST=1 + leaked overrides gives exit 0; --flows text wrong | yes | a would-be pass with an override is exit 5; TAKE_CHECK_FLOWS plus --flows = exit 2 REFUSED; top block prints the real source (--flows / TAKE_CHECK_FLOWS / built-in default) |
| B4 | shared raw folder, no lock | yes | run_all.sh takes flock on a lock file in the temp folder named after the raw folder; second run = exit 2 REFUSED; `--lock-only` for the test |
| minor | flow_snapshot after first reads | yes | snapshot function and first call moved above has_keyok |
| minor | NO PIN WRITTEN message says "exits 1" | yes (text said the number, could differ from the real one) | text now points to the FINAL line; header text for --write-warn-pin exits corrected (1, 2, 3, 4) |
| minor | sha256sum | cut failures unchecked | yes | `sha_stdin` helper: failure = `UNAVAILABLE`, loud `!!!` line, exit 4; also for the pin hash and the new pin hash |
| minor | RUN_ALL_TAKE_FLOWS honoured without NESTED | yes | refused (exit 2) without RUN_ALL_NESTED, also DROP_LEAD, PLANT_TCFAIL_FLOWS, PLANT_TCFAIL_WANT, LOCKFILE |
| minor | selftest summary = tail -n 1 | yes | grep of `^SELFTEST: `; missing line = exit 1 |
| minor | tcfail first line shown | found by me: the new sha `!!!` line hid the FAIL line | a `FAIL ` line is shown before a `!!! ` line |
| minor | README drift, piping | yes | README updated (exit 5, flows sha, reviewer grammar, lock, hooks, "do not pipe into tail/grep") |
run_all.sh: its stand-in reviewer line is now `Runall Standin, <today>` (it must pass the new grammar); its take call expects exit 5.

## Tests added to test_take_check.sh (68 cases now; 41 before this round counted 41 as_expected on the old script)
A1, B1 (2), B2 (10 bad lines plus 1 good), B3 (4), snapshot order, sha256sum failure, B4 (2), hook refusal, the flows sha line in a written pin. Four older cases changed their expected exit from 0 to 5 because of B3. In run_all.sh a fourth nested run (nested-d) tests A2.

## PROOF: the new test script run against the OLD scripts (backup in scratchpad/bak-f8r10d: take_check.sh, run_all.sh, take-warns.pin)
(command: bash old-run/flows-audit/flow-check/test_take_check.sh <patched real folder> <scratch>, old take_check.sh, old run_all.sh, old pin, new test file)
FAIL Q1/B3: a pin with a person's reviewer line gives exit 5 (a would-be pass with the pin override; 5, never 0); the line is printed as written; the output does not say a person read the pin (got exit 0)
FAIL B1: the written pin carries the '# flows sha256' line
FAIL B1b: the written pin, used as the pin, gives exit 5 (would-be pass with the pin override) (got exit 0)
FAIL M-2: the top block and the FINAL line print the combined sha256 of the four flow files (and one per file); exit 5 = would-be pass with the pin override (got exit 0)
FAIL M1/B3: with the test flag the override is allowed, still printed, and a would-be pass is exit 5 (got exit 0)
FAIL A1: line 1 of take-warns.pin does not claim that a person read each line
FAIL B1: a changed flow file with the same counts and the same WARN lines is exit 4 (got exit 0)
FAIL B1: a pin without the flows sha256 line is exit 4 (got exit 0)
FAIL B2: reviewer line 'claude agent, 2026-11-16' is exit 4 (got exit 0)
FAIL B2: reviewer line 'TBD' is exit 4 (got exit 0)
FAIL B2: reviewer line 'x, 2026-11-16' is exit 4 (got exit 0)
FAIL B2: reviewer line 'Test Reviewer' is exit 4 (got exit 0)
FAIL B2: reviewer line 'Test Reviewer, 2026-13-45' is exit 4 (got exit 0)
FAIL B2: reviewer line 'Test Reviewer, 2999-01-01' is exit 4 (got exit 0)
FAIL B2: reviewer line ', 2026-11-16' is exit 4 (got exit 0)
FAIL B2: reviewer line 'R2D2 4, 2026-11-16' is exit 4 (got exit 0)
FAIL B2: reviewer line 'Some Assistant, 2026-11-16' is exit 4 (got exit 0)
FAIL B2: reviewer line 'Name Placeholder, 2026-11-16' is exit 4 (got exit 0)
FAIL B2: 'Jane Q. Roe-Smith, 2026-11-16, read all 4 WARN lines' is accepted (would-be pass with the override: exit 5) (got exit 0)
FAIL B3: test flag plus a leaked TAKE_CHECK_CK (and the pin override) is exit 5 with the FINAL line saying 5, not exit 0 (got exit 0)
FAIL B3: TAKE_CHECK_FLOWS and --flows both set is exit 2 (got exit 0)
FAIL B3: a folder taken from TAKE_CHECK_FLOWS is printed as coming from the variable (got exit 0)
FAIL snapshot order: a flow file written by the first python3 read is caught (got exit 0)
FAIL sha256sum failure: exit 4 with a loud line, no empty hash (got exit 4)
FAIL B4: a second run_all.sh on a locked raw folder is refused, exit 2 (got exit 2)
FAIL B4: with nobody holding the lock, run_all.sh --lock-only takes it and exits 0 (got exit 2)
FAIL RUN_ALL_TAKE_FLOWS without RUN_ALL_NESTED is refused, exit 2 (got exit 2)
test_take_check: 41 of 68 cases as expected, 27 not as expected
rc=1

## PROOF for A2 (mutation): run_all.sh edited in place to the old grep (wanted text on any line), run, then restored (cmp: restored)
[take_check.sh exit=5] missing lines: [nested run with a planted wanted text on a non-loud line: want exit 1 and the 'not on a !!! or FAIL line' report, got exit 0 (see nested-take-failure-d.txt)]
run_all exit status (real-v5 default runs + self-test): 1
rc=1

## FINAL RUNS (patched scripts)
--- bash flow-check/run_all.sh <fresh dir>, own raw folder (RUN_ALL_RAW) ---
[selftest exit=0] SELFTEST: 682 as expected, 0 not as expected, 62 skipped (not applicable)
[take_check.sh exit=5] missing lines: none
run_all exit status (real-v5 default runs + self-test): 0
rc=0
--- bash flow-check/run_all.sh <fresh dir>, default raw folder ---
run_all exit status (real-v5 default runs + self-test): 0
rc=0
ok   Q2: extra.json written after the checker ran is exit 4 with the loud line (got exit 4)
/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/final11755

[exited with code 0]
--- bash flow-check/test_take_check.sh <patched dir> <fresh scratch> ---
test_take_check: 68 of 68 cases as expected, 0 not as expected
ttc_rc=0
--- ruff check flow-check/*.py: All checks passed! (rc 0); ruff format --check: 2 files already formatted (rc 0); bandit -ll -r flow-check -q: no output, rc 0. (No .py file was edited by me.) ---
--- cleanup: git clean -n flow-check listed only flow-check/handover/ (existing before my work, not mine, left alone); then git checkout -- flow-check/raw flow-check/selftest-output; git status --short flow-check is empty. ---
