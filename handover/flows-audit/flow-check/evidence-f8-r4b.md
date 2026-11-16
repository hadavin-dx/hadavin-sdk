# Evidence F8 round 4b (raw output only, no judgement)

HEAD at start: cd3ccd288100d6604ac172317b06cf0c51732287; HEAD at end: f9954a9d9ae1cb26df2ac6113cf245df61c9f4d3 (another session committed during the runs)
sha256 of the scripts at start:
f83cd41175b09b397d6b5f69b957da6ae2885fa3d76159134dcface19657275f  handover/flows-audit/flow-check/take_check.sh
822b5b0ae6859bedaddb746b746f9855bf2a83039a8f772e20b29724ed611bcd  handover/flows-audit/flow-check/run_all.sh
70597a9a03d470bb3cdafa7e2eb2cb932f4dd4493f09016be5f60114dae0e316  handover/flows-audit/flow-check/test_take_check.sh
Patched copy built as run_all.sh does (git apply F-002, F-008; build_mainframe.py MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000): apply rc=0 twice, gen rc=0, 4 flow files.
Scratch: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev8r4 (patched dir /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev8r4/build/g/real; mirror /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev8r4/mirror)

## rc summary
bash -n take_check rc=0
bash -n run_all rc=0
bash -n test_take_check rc=0
test_take_check rc=0
run_all rc=2
run_all rc=0
shellcheck: not installed (command not found), not run
(first run_all attempt with the patched dir as work dir gave rc=2 REFUSED non-empty folder; rerun with a fresh work dir gave rc=0; rc list above has both)

## (2) test_take_check first 15 / last 15
ok   control: the committed pin gives exit 0, or exit 4 with 'pin not yet confirmed by the lead' while its reviewer line names a session; the reviewer line is printed as written; OVERRIDES says none (got exit 4)
ok   Q1/B3: a pin with a person's reviewer line gives exit 5 (a would-be pass with the pin override; 5, never 0); the line is printed as written; the output does not say a person read the pin (got exit 5)
ok   Q1: a reviewer line naming a session and 'lead to confirm' is exit 4 with the plain reason, never 'a person read' (got exit 4)
ok   Q1: '# reviewed by: Audit Session B, 2026-11-16' is exit 4 (got exit 4)
ok   Q1: '# reviewed by: A. Person, 2026-11-16, Lead To Confirm' is exit 4 (got exit 4)
ok   B1a: --write-warn-pin on the pin in use is refused (exit 2) and leaves it unchanged (got exit 2)
ok   B1b: a clean run writes a NEW pin with date and sha256 and exits 4, not 0 (got exit 4)
ok   B1: the written pin carries the '# flows sha256' line
ok   M-3: the written pin says it is not yet read and holds the placeholder line
ok   M-3: a pin whose header still has the placeholder is exit 4 (got exit 4)
ok   M-3: a pin with no 'reviewed by' line is exit 4 (got exit 4)
ok   B1b: the written pin, used as the pin, gives exit 5 (would-be pass with the pin override) (got exit 5)
ok   B1c: --write-warn-pin on an existing file is refused (exit 2) and leaves it unchanged (got exit 2)
ok   B1d: a run with a FAIL writes no pin and keeps exit 1 (got exit 1)
ok   B1e: a changed WARN set prints the difference, writes the new file, exits 4 (got exit 4)
...
ok   M2: the same raw folder with a DIFFERENT TMPDIR is refused, exit 2
ok   M2: the same raw folder given through a symbolic link (and another TMPDIR) is refused, exit 2
ok   M2: the same raw folder given as a relative path from another folder is refused, exit 2
ok   M2: the same raw folder given with a double slash, a link and .. is refused, exit 2
ok   M2: a DIFFERENT raw folder is not blocked by that lock (exit 0)
ok   M2: no lock file was left in either TMPDIR
ok   RUN_ALL_TAKE_FLOWS without RUN_ALL_NESTED is refused, exit 2 (got exit 2)
ok   Q5: a checker that exits 3 is shown as 3 and the take exits 3 (got exit 3)
ok   Q5: a checker that exits 4 is shown as 4 and the take exits 3 (got exit 3)
ok   Q5: a checker that exits 127 is shown as 127 and the take exits 3 (got exit 3)
ok   Q5: a checker that exits 137 is shown as 137 and the take exits 3 (got exit 3)
ok   Q5: --write-warn-pin with a checker that exits 127 writes nothing and exits 3 (got exit 3)
ok   count: mf-form.json with one extra wired step is exit 1 with a node-count FAIL and no orphan FAIL (got exit 1)
ok   count: mf-hook.json with one extra wired step is exit 1 with a node-count FAIL and no orphan FAIL (got exit 1)
test_take_check: 94 of 94 cases as expected, 0 not as expected

## (3) run_all first 15 / last 15
applied F-002-take-key-check-and-claim-error-path
applied F-008-save-runs-for-the-take
checker runs wall time: 0 s; self-test wall time: 6 s
==== real-v5 (THE TAKE) ====
---- default mode must be exit 0; strict mode shows what the owner's two open decisions would do ----
[pristine]
######## pristine real
RESULT: 0 FAIL, 23 WARN
Known open problems: 17
exit=0
[patched]
######## patched real
RESULT: 0 FAIL, 22 WARN
Known open problems: 16
exit=0
...
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
COMMITTED PIN (take-warns.pin) reviewer line, as written: 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: a bare take_check.sh exits 4 until the lead replaces that line (this run used a stand-in line, so its take check could pass).
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check

## (5) hostile reviewer lines, mirror copy, bare take_check.sh --flows <patched>
[TBD.] line='TBD., 2026-11-16' rc=4 :: NOT A PERSON'S NAME AND A DATE :: FINAL: take_check exit status 4. Flow files sha256 (four files, combined): 989f552965a1b155...
[Claude-Code] line='Claude-Code, 2026-11-16' rc=4 :: NOT A PERSON'S NAME AND A DATE :: FINAL: take_check exit status 4. Flow files sha256 (four files, combined): 989f552965a1b155...
[N/A] line='N/A, 2026-11-16' rc=4 :: NOT A PERSON'S NAME AND A DATE :: FINAL: take_check exit status 4. Flow files sha256 (four files, combined): 989f552965a1b155...
[Zed] line='Zed, 2026-11-16' rc=0 ::  :: FINAL: take_check exit status 0. Flow files sha256 (four files, combined): 989f552965a1b155...
[O'Brien] line='O'Brien, 2026-11-16' rc=0 ::  :: FINAL: take_check exit status 0. Flow files sha256 (four files, combined): 989f552965a1b155...
[Aaa] line='Aaa, 2026-11-16' rc=4 :: NOT A PERSON'S NAME AND A DATE :: FINAL: take_check exit status 4. Flow files sha256 (four files, combined): 989f552965a1b155...
[Pat O.L.L.M.] line='Pat O.L.L.M., 2026-11-16' rc=0 ::  :: FINAL: take_check exit status 0. Flow files sha256 (four files, combined): 989f552965a1b155...
[future date] line='Pat Smith, 2027-01-01' rc=4 :: NOT A PERSON'S NAME AND A DATE :: FINAL: take_check exit status 4. Flow files sha256 (four files, combined): 989f552965a1b155...
[before pin date] line='Pat Smith, 2026-11-15' rc=4 :: NOT A PERSON'S NAME AND A DATE :: FINAL: take_check exit status 4. Flow files sha256 (four files, combined): 989f552965a1b155...
[session in name] line='Pat Session, 2026-11-16' rc=4 :: pin not yet confirmed by the lead :: FINAL: take_check exit status 4. Flow files sha256 (four files, combined): 989f552965a1b155...
[control valid] line='Pat Smith, 2026-11-16' rc=0 ::  :: FINAL: take_check exit status 0. Flow files sha256 (four files, combined): 989f552965a1b155...

## (6) concurrent run_all, same raw folder
second run_all rc=2
REFUSED: another run_all.sh holds the lock for the raw folder /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev8r4/raw6; wait for it to end, or use another raw folder (RUN_ALL_RAW is for the nested tests only)
first run_all rc=0
