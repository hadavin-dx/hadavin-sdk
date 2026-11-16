# evidence-f8-r8 (raw record; no judgement)
head sha: 6d7bb3136c6956eafa9e5df8c3ae9ea7e10c394d  date: 2026-11-16T13:58:07Z
sha256 first16: take_check.sh=57f3a6376d2cf3cb test_take_check.sh=71a6c4cc0d20fe17 run_all.sh=6985b853388d2a34
git status at start (flow-check dir): clean; note: '../TAKE-CHECKLIST.md' shows modified after my runs (not touched by me)

## (1) bash -n: all three rc=0 (take_check.sh, test_take_check.sh, run_all.sh)

## (2) test_take_check.sh
Command: bash test_take_check.sh   (no argument) -> rc=2, 'usage: bash test_take_check.sh PATCHED_REAL_DIR [SCRATCH_DIR]'
The suite needs a PATCHED real-v5 folder. run_all.sh builds it as WORKDIR/g/real.
(2a) bash test_take_check.sh <WORKDIR from plain run_all>/g/real <new scratch>  -> rc=0
last 5 lines:
ok   Q5: a checker that exits 137 is shown as 137 and the take exits 3 (got exit 3)
ok   Q5: --write-warn-pin with a checker that exits 127 writes nothing and exits 3 (got exit 3)
ok   count: mf-form.json with one extra wired step is exit 1 with a node-count FAIL and no orphan FAIL (got exit 1)
ok   count: mf-hook.json with one extra wired step is exit 1 with a node-count FAIL and no orphan FAIL (got exit 1)
test_take_check: 444 of 444 cases as expected, 0 not as expected
FAIL lines: 0
(2b) bash test_take_check.sh ../../demo/n8n-flows-real-v5 <new scratch> (UNPATCHED real-v5 dir) -> rc=1
last 5 lines:
ok   Q5: a checker that exits 137 is shown as 137 and the take exits 3 (got exit 3)
ok   Q5: --write-warn-pin with a checker that exits 127 writes nothing and exits 3 (got exit 3)
FAIL count: mf-form.json with one extra wired step is exit 1 with a node-count FAIL and no orphan FAIL (got exit 1)
FAIL count: mf-hook.json with one extra wired step is exit 1 with a node-count FAIL and no orphan FAIL (got exit 1)
test_take_check: 400 of 444 cases as expected, 44 not as expected
FAIL lines: 44

## (3) previous-round script
Used take_check.sh from commit d67756e63 (git log -- take_check.sh: 44229c549, c62c17440, 03502f556, d67756e63...; 5fa6a2b2b does not exist in this repo; d67756e63 = last commit before evidence-f8-r7.md at a44c3da18), sha256 first16 8c87bbac42fc57bd
Command: TEST_TAKE_SCRIPT=<scratch>/old/flows-audit/flow-check/take_check.sh bash test_take_check.sh <patched real> <new scratch>  -> rc=1
last lines:
447:test_take_check: 200 of 443 cases as expected, 243 not as expected
failing count: 243 FAIL lines; summary 'test_take_check: 200 of 443 cases as expected, 243 not as expected'
Two count: cases got exit 2 (rest are reviewer-line cases)
Full FAIL list (first 30):
FAIL reviewer line [no] 'Pat Llamas, 2026-11-16' reason has 'rule: listed word llama' (got exit 0: ok)
FAIL reviewer line [no] 'Pat Cla.ude, 2026-11-16' reason has 'rule: listed word claude' (got exit 0: ok)
FAIL reviewer line [no] 'Pat O L L M, 2026-11-16' reason has 'rule: name word too short' (got exit 0: ok)
FAIL reviewer line [no] 'Pat Q Roe, 2026-11-16' reason has 'rule: name word too short' (got exit 0: ok)
FAIL reviewer line [no] 'Pat Smith -, 2026-11-16' reason has 'rule: name word too short' (got exit 0: ok)
FAIL reviewer line [no] 'Pat Cl͏aude, 2026-11-16' reason has 'rule: hidden character' (got exit 0: ok)
FAIL reviewer line [no] 'Pat Smith, 2026-11-16, read Cl͏aude' reason has 'rule: hidden character' (got exit 0: ok)
FAIL reviewer line [no] 'Pat Smith, 2026-11-16, ok️' reason has 'rule: hidden character' (got exit 0: ok)
FAIL reviewer line [no] 'Pat️ Smith, 2026-11-16' reason has 'rule: hidden character' (got exit 0: ok)
FAIL reviewer line [no] 'ㅤㅤㅤ, 2026-11-16' reason has 'rule: hidden character' (got exit 0: ok)
FAIL reviewer line [no] 'Pat Smithㅤ, 2026-11-16' reason has 'rule: hidden character' (got exit 0: ok)
FAIL reviewer line [no] 'Pat Smith, 2026-11-16, noteㅤhere' reason has 'rule: hidden character' (got exit 0: ok)
FAIL reviewer line [no] 'Pat Smith, 2026-11-16, a b' reason has 'rule: hidden character' (got exit 0: ok)
FAIL reviewer line [no] 'Patᅟ Smith, 2026-11-16' reason has 'rule: hidden character' (got exit 0: ok)
FAIL reviewer line [no] 'Pat ́́́, 2026-11-16' reason has 'rule: hidden character' (got exit 0: ok)
FAIL reviewer line [no] '́́́, 2026-11-16' reason has 'rule: hidden character' (got exit 1: REFUSED (rule: name characters): the name must start with a letter)
FAIL reviewer line [no] 'Pat Smith, 2026-11-16, ́ x' reason has 'rule: hidden character' (got exit 0: ok)
FAIL reviewer line [no] 'Pat Smith, 2026-11-16, 5́' reason has 'rule: hidden character' (got exit 0: ok)
FAIL reviewer line [no] 'Pat Smith, 2026-11-16, xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FAIL reviewer line [no] 'Pat Cl-aude, 2026-11-16' reason has 'rule: listed word claude' (got exit 0: ok)
FAIL reviewer line [no] 'Pat Cla'ude, 2026-11-16' reason has 'rule: listed word claude' (got exit 0: ok)
FAIL reviewer line [no] 'Pat Bo.t, 2026-11-16' reason has 'rule: listed word bot' (got exit 0: ok)
FAIL reviewer line [no] 'Pat A-I, 2026-11-16' reason has 'rule: listed word ai' (got exit 0: ok)
FAIL reviewer line [no] 'Pat G-P-T, 2026-11-16' reason has 'rule: listed word gpt' (got exit 0: ok)
FAIL reviewer line [no] 'Pat L-L-M, 2026-11-16' reason has 'rule: listed word llm' (got exit 0: ok)
FAIL reviewer line [no] 'Pat Smith, 2026-11-16, Cl@ude' reason has 'rule: listed word claude' (got exit 0: ok)
FAIL reviewer line [no] 'Pat Smith, 2026-11-16, Cl_aude' reason has 'rule: listed word claude' (got exit 0: ok)
FAIL reviewer line [no] 'Pat Smith, 2026-11-16, Cl-aude' reason has 'rule: listed word claude' (got exit 0: ok)
FAIL reviewer line [no] 'ВОТ Smith, 2026-11-16' reason has 'rule: listed word bot' (got exit 0: ok)
FAIL reviewer line [no] 'Pat ΑΙ, 2026-11-16' reason has 'rule: listed word ai' (got exit 0: ok)

## (4) run_all.sh
Plain: cd flow-check; bash run_all.sh <new WORKDIR>  -> rc=0 (wall 3m14s)
last 20 lines:
######## patched film
RESULT: 0 FAIL, 20 WARN
Known open problems: 14
exit=0
[pristine-strict-film]
######## pristine-strict film
RESULT: 4 FAIL, 17 WARN
Known open problems: 11
exit=1
[patched-strict-film]
######## patched-strict film
RESULT: 4 FAIL, 16 WARN
Known open problems: 10
exit=1
[selftest exit=0] SELFTEST: 682 as expected, 0 not as expected, 62 skipped (not applicable)
[take_check.sh exit=5] missing lines: none
run_all exit status (real-v5 default runs + self-test): 0
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: take_check.sh refuses it (REFUSED (rule: listed word session): the line contains the whole word 'ses
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check

Strict: bash run_all.sh --strict <new WORKDIR>  -> rc=1
last 20 lines:
######## patched film
RESULT: 4 FAIL, 16 WARN
Known open problems: 10
exit=1
[pristine-strict-film]
######## pristine-strict film
RESULT: 8 FAIL, 13 WARN
Known open problems: 7
exit=1
[patched-strict-film]
######## patched-strict film
RESULT: 8 FAIL, 12 WARN
Known open problems: 6
exit=1
[selftest exit=0] SELFTEST summary line missing in raw/selftest-new.txt
[take_check.sh exit=5] missing lines: none
run_all exit status (real-v5 default runs + self-test): 1
real-v5 placeholder ids: 6 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: take_check.sh refuses it (REFUSED (rule: listed word session): the line contains the whole word 'ses
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
Strict first selftest/exit lines:
50:[selftest exit=0] SELFTEST summary line missing in raw/selftest-new.txt
52:run_all exit status (real-v5 default runs + self-test): 1

## (5) restore
git status --short in flow-check after runs: empty (raw/ and selftest-output unchanged or ignored; __pycache__ is ignored). Restored: nothing. ../TAKE-CHECKLIST.md is modified (' M'), not by my commands; left alone.

## (6) hostile inputs: bash take_check.sh --check-reviewer-line LINE   (today UTC 2026-11-16)
1 'Иван Петров, 2026-11-16' (Cyrillic name) rc=0 msg=ok
2 'Pаt Smith, 2026-11-16' (Cyrillic а in Pat) rc=1 REFUSED (rule: mixed alphabets): one word mixes Latin letters with Cyrillic or Greek letters (look-alike letters)
3 'Pat<U+200B> Smith, 2026-11-16' rc=1 REFUSED (rule: hidden character): ... (U+200B)
4 'Pat Smith, 2026-11-16, a' + 1100 x (len 1124) rc=1 REFUSED (rule: too long): the line is longer than 1000 characters
5 'Cl4ud3 Smith, 2026-11-16' (leetspeak) rc=1 REFUSED (rule: name characters): the name may hold only letters, spaces, dots, apostrophes and hyphens (no digits or other signs)
6 'Pat Cl@ud3, 2026-11-16' rc=1 REFUSED (rule: name characters): same message
7 'Pat Smith, 2026-11-16' (valid) rc=0 ok
8 'Pat Smith, 2026-11-18' (two days ahead) rc=1 REFUSED (rule: future date): 2026-11-18 is more than one day ahead of today (UTC)
9 'Pat Smith, 2026-11-17' (one day ahead) rc=0 ok
10 'Pat Smith, 2026-11-16<U+202E>, ok' (RTL override) rc=1 REFUSED (rule: hidden character): ... (U+202E)
