# R7K-RESULTS (builder r7k: pass-9 leftovers, the r7j review, pass-10 gaps)

Base r7j (tree-R7J). Tree: /home/user/build/rr6/tree-R7K. Patches: core-fix-on-frozen-r7k.patch (CRLF), core-fix-on-frozen-r7k-lf.patch, core-fix-r7j-to-r7k-delta.patch; sha256-r7k.txt; apply-matrix-r7k.txt (a-crlf, b-crlf, c-lf all `git apply --check` rc=0); build.log (byte-for-byte same as the tree; delta on r7j gives r7k). Nothing applied or pushed anywhere.

## NOT RUN / NOT CHECKED / NOT DONE (first)
- NOT RUN: the full suite (EV7K does that). Run by me, on the final bytes unless stated: tests/test_r7k_findings.py (139 passed), test_r7f_findings (79 passed, before the last doc edits; source unchanged since), test_r7g/h and the m7 row of r7j (218 passed), test_r7j_findings (39 passed + the row that I changed, which passed alone afterwards). Group runs (mail, live, crm, reg, tls) see "Clean group runs" below. NOT run: the rrc group (run_real_check family, 10 files: I stopped the sequence for time; `scripts/run_real_check.py` was NOT changed, only tested), the whole suite.
- NOT DONE (item 10): the run_real_check mutants M9-68..82 were NOT run by me, as ordered; they are for the next mutant pass. Pass 10 has since found M9-69 (done here, k16) and M9-16 (done here, k17).
- NOT DONE, optional (nit n4): the 62 s real-driver test of r7j stays as it is (it is real by design).
- Not checked: Windows; a machine without IPv6 for real (faked); a real name server.
- Skipped by the machine in earlier rounds: gitleaks tests (program missing); unchanged.

## The rc=1 with "passed" (lead question)
Cause found and proven: `tests/conftest.py::pytest_sessionfinish` is a tree guard. A file of the repository folder that changes during a run sets exit status 1 and prints `REPOSITORY FOLDER CHANGED BY THE TEST RUN (1 files): 'tests/test_r7k_findings.py'`. I was editing my own test file while the group runs were going (mail, crm, tls); live and reg ran with no edit and gave rc=0. The line is in clean-mail.log, clean-crm.log and clean-tls.log of the first sequence (kept in the first-sequence logs: see cleans.log). The driver lo_up-q4g.py only sets a network flag and execs pytest (its rc is pytest's rc). No test leaks a thread or process. Proof of the cure: the second sequence (cleans2.log) ran with no edit and is listed below.

## Per item (needed-check, class, fix or pin, tests, mutants, fail-before on a copy of tree-R7J)
Tests are in tests/test_r7k_findings.py (header table there).

| item | needed-check | class | fix or pin | tests | mutants | fail-before (r7j copy) |
|---|---|---|---|---|---|---|
| step 1: M9-22, 12, 02, 03, 18, 19, 08, 30, 23 | DUPLICATE (the r7i tests kill them) | - | none | r7i tests | all 9 KILLED by r7i tests, 1 to 4 s each, restored by sha | - |
| 1 M9-32 key text in no error | NEEDED | an earlier error kept as `__context__` (it could hold request data); `from None` only hides it from the printout | strip `__context__` and `__cause__` at the choke points: `live_claude._post`, `crm_hubspot._once`, `regfile.read_secret_line` (wrapper) | k1 (echo server 9 cases, unreachable, held call, 10 injected opener errors, CRM sibling, key files) | M9-32, K01-K03 and K13-K25 KILLED | 21 FAIL (chain tests); pure pins pass by design |
| 2 M9-40 lock not obtained: no spend | NEEDED (pin) | no code change | pin: reserve, settle, totals refuse, no row, no network call | k2 | M9-40, K04-K06 KILLED | PIN |
| 3 M9-33 proxy from the environment | NEEDED (pin) | - | child process with proxy variables set, live and adapters | k3 | M9-33 KILLED | PIN |
| 4 M9-34 reply cap boundary | NEEDED (pin) | - | exact cap ok, cap+1 refused, 4096 blocks and a real connection | k4 | M9-34 KILLED | PIN |
| 5 M9-64 over-cap line refused, not split | NEEDED (pin) | - | | k5 | M9-64, K06, K22 KILLED | PIN |
| 6 M9-65 BOM accepted | NEEDED (pin) | - | doc line checked | k6 | M9-65 KILLED | PIN |
| 7 M9-67 errcode prefix | NEEDED (pin) | - | | k7 | M9-67 KILLED | PIN |
| 8 M9-61 NaN/Infinity | NEEDED (pin of the text) | EQUIVALENT mutant, argument below | | k8 | M9-61 SURVIVED (equivalent) | PIN |
| 9 sibling of M9-08, dribbled TLS handshake | NEEDED (pin) | CPython counts the socket time-out of a handshake as a whole, so it ends near the budget | | k9 | - | PIN (passed first time, so no code fix) |
| 10 M9-68..82 | NOT DONE (ordered) | | | | | |
| N05/N06 (lead, EV7H) LOOKUP_HUNG_MAX 9 / 7 | NEEDED | constant not pinned; they SURVIVED the r7f to r7j tests (confirmed by me: 101 s run, both SURVIVED) | the constant is 8 in both places and behaviour: 8 allowed, the 9th refused at once with no thread | k10 | N05, N06 KILLED | PIN |
| review M1 | NEEDED | an invented address (`::1` for localhost) whose refusal replaced the time-out error | `localhost` gives 127.0.0.1 only; in `connect_bounded` a time-out wins over a later refusal (`raise timeout or last or ...`); no time-out: the last error. Stated in the module docstring, docs/limits.md, CHANGELOG. test_r7f_findings now passes fully (79) | k11 | N07, N08, N09, N19, N20 KILLED | FAIL (4 tests incl. the refused-localhost one) |
| review M2 | NEEDED | a timing lower bound that fails under load | deleted (see changed tests) | - | - | - |
| review M3 | NEEDED | an outcome class left out of the exit decision | `driver_error_count` (new), summary key `driver_errors`, `exit_code_and_line` counts all three kinds (exit 3, ONE line, the same number; new text names the driver errors) | k15: fake pool runs the real `main` and `run` with a raising sender (4/4, 2/6, 1/5), the unit table incl. errors only, the exit-0 control | N13-N18 KILLED | FAIL (exit 0 and no line) |
| review m1 | NEEDED | one resource given back twice | `state["released"]` once-only flag in `work` and in the start-failure `except` | k13 (thread that starts and then raises; thread that never starts; more tries than places) | N10, N11, N21 KILLED | FAIL (count -1) for the start-then-raise case; the never-starts case passes alone (its failure in the run is the leaked -1 of the case before) |
| review m2 | NEEDED | a guard without a test (mutant N4) | none | k12 (RuntimeError and KeyboardInterrupt on address 1; the 2nd would connect and is never tried; socket closed) | N4 KILLED | PIN |
| review m3 | NEEDED | the check was narrower than the system | digit addresses are decided by `getaddrinfo(..., flags=AI_NUMERICHOST)` (real function taken at import; cannot hang). 127.1, 0x7f.1, 2130706433 answer 127.0.0.1; `017.0.0.1` is OCTAL for the system and answers 15.0.0.1 (the review said it should be refused; it is not a loopback address and the system would connect to 15.0.0.1 anyway: documented in limits.md and CHANGELOG, pinned as the system's own answer) | k14 | N12, N12b KILLED | FAIL (the four forms went to a look-up thread) |
| review m4 | NEEDED | stale text | comment at the summary and `deadline_count` docstring now say exit code 3; limits.md, load_tools/README.md, CHANGELOG updated | - | - | - |
| nit n2 (two stderr lines) | NEEDED | | WARNING (lines missing) is printed only for an exit-0 run; an exit-3 run prints exactly one ERROR line | k15 (4 cases) | N18 KILLED | FAIL |
| nit n3 (test name) | NEEDED | | renamed `..._prints_no_line` | - | - | - |
| nit n1 ("never more than 8") | NEEDED | the claim was false with m1 | true now (k13) | k13 | | |
| M9-69 (lead, pass 10) Start? answer | NEEDED | mailbox-safety path | pins: every answer but `y` after strip and lower case stops with `stopped, nothing was called`, EXIT_STOPPED (6), and the fake HubSpot, mail server and both mailboxes saw zero calls and no desk book exists; y, Y, ` y `, `y ` (strip applies, so `y ` IS yes), tab-y and `  Y  ` start (checked with a stand-in for `make_plan`); `yes`, ``, ` `, n, N, no, maybe, `yes please`, `yy`, `y y`, `ye`, 1, true, full-width y, ok are NOT yes; EOF, OSError, BrokenPipeError: stopped with the no-terminal line; `--dry-fakes` alone asks; `--assume-yes` alone is refused before any fake starts; both skip the question | k16 | M9-69, N22-N28 (answer in ("", n, no); drop strip; drop lower; and->or; EOF returns 0; startswith y; ask only without dry-fakes) all KILLED | PIN (no source change) |
| M9-16 (pass 10) default mail port | NEEDED | | pin: starttls and unset mode -> 587, ssl -> 465, a set port always wins (7 cases). `smtp_outbox` has no default port (grep: the only site is smtp_provider.py:154) | k17 | M9-16, N29 KILLED | PIN |

M9-61 (equivalent): `parse_constant` refuses NaN/Infinity/-Infinity and `_has_non_finite` refuses what `1e999` becomes, both with the same class and the same text "the file is not JSON that can be read". No test can tell which of the two refused, so removing one is invisible; k8 pins the text for all four inputs at any depth. Not a kill.

Own mutants: K01-K25 (live/crm/regfile chain and lock lines) and N4, N05-N29 (netconnect, load_driver, run_real_check, smtp_provider); 55 specs in all; every one KILLED except M9-61 (equivalent). Runner mutk.py (plants by exact text, runs, restores by sha256; all `restored-ok`), logs mut-results.tsv and raw-*.txt, mutn.log, mutn3.log. N20 first SURVIVED (the real name look-up answered `LocalHost` too); I made the test stricter (cap of 0, so a look-up thread is refused) and it was KILLED.

## Changed or deleted existing tests (old / new side by side)
1. tests/test_r7g_findings.py `test_m1_the_total_limit_holds_over_many_silent_addresses`: old: `assert all(t is not None and 0.24 <= t for _, t in log[:3]), log` (plus the 2 comment lines above it); new: line and comment removed, replaced by a comment naming test_m4. The upper bound `t <= 0.26` and `len(log) == 4` stay. Why not weaker in the part that matters: the exact share is pinned with a fake clock (no sleeping) by test_m4 of test_r7j_findings.py (shares 0.25, 0.3, 0.3, 0.3); the removed line measured real time and failed under load.
2. tests/test_r7j_findings.py `test_m3_localhost_gives_both_loopback_addresses_ipv4_first` -> `test_m3_localhost_gives_the_one_ipv4_loopback_address`: old `[a[4][0] for a in found] == ["127.0.0.1", "::1"] and found[1][0] == socket.AF_INET6`; new `== ["127.0.0.1"] and found[0][0] == socket.AF_INET`. Why: review M1 (the invented `::1`), the behaviour was changed on purpose.
3. tests/test_r7j_findings.py `test_m3_everything_else_still_needs_a_look_up_and_is_refused_at_the_cap`: the case `"127.1"` removed from the list (now a digit address, covered by k14, 5 forms). The other four names stay.
4. tests/test_r7j_findings.py `test_m7_exit_code_3_...`: the call now passes `logged=7 if code == 0 else 5` (old: always 5). Why: with 5 logged of 7 intended an exit-0 run now prints the WARNING (n2); the exit-0 row needs logged == intended to keep its assertion `err == ""`. The WARNING itself is pinned in k15. The 3 other rows unchanged.
5. tests/test_r7h_findings.py `test_a_run_with_nothing_given_up_prints_no_note` -> `..._prints_no_line` (name and docstring only; same assertions).
No test deleted.

## Clean group runs (final bytes, no edit during the run)
Second sequence (cleans2.log), each group plus the r7f, r7g, r7i, r7j and r7k finding files, no edit during the run, final bytes:
- mail: 627 passed, rc=0 (07:49 UTC)
- crm: 499 passed, rc=0 (07:52 UTC)
- tls: 767 passed, rc=0 (07:55 UTC)
This also proves the cause of the earlier rc=1 (same groups, now rc=0). NOT re-run on the final bytes: live and reg (they ran rc=0 in the first sequence at 07:31 and 07:36, before I added k16/k17 test code; no source file changed after those runs, only the test file k and the docs). NOT run: rrc.

## Sweeps
- Key text in exceptions (class of M9-32): every `raise` in live_claude, crm_hubspot, smtp_provider, smtp_outbox, regfile reader. Only three sites kept a context and all three are fixed at the choke point. No logging calls in those modules. The only password use is the AUTH PLAIN token.
- Environment proxy: adapters `_OPENER`, HubSpot opener and live_claude all use `ProxyHandler({})`; `scripts/http_guard.py` has an intentional `use_proxy` option (not a key path).
- Lock not obtained (class of M9-40): `_FileLock` paths all pinned in k2; `lockfile.acquire` (LockHeldError) already tested in test_desk_edge_cases and test_desk_http_edge_cases.
- Double release / double count (class of m1): other counters (`crm_hubspot._call`, `smtp_provider.send`, `server._slots`) were swept in r7j and are decrement-once under one lock; no other site found.
- Suppressions: noqa 175, type-ignore 126, nosemgrep 28, nosec 8 in both tree-R7J and tree-R7K (grep counts equal). I had added one type-ignore in my test file and removed it (cast). Ruff 0.17.1 check and format --check: all clean (223 files).

## Honest limits
- `017.0.0.1` is answered as 15.0.0.1 (octal), as the system does; a person who writes a leading zero gets the system's meaning. Documented.
- A refused look-up for a real name at a full cap is still fail-closed (unchanged).
- k15 runs the real `main` and `run` with the workers in this process (a fake pool): the real spawned pool cannot see a patched sender. The real-driver path is covered by the r7j 62 s test.
- k16 stops the run at `make_plan` for the "start" cases; the rest of the dry run is covered by the existing real_check tests (not run by me in this round except through the groups below).
