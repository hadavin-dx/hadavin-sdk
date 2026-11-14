# Review of core-fix r7m -> r7n (codebase-details reviewer, fallback mode, fresh context)

Verdict: NOT CLEAN. 0 Blocker, 2 Major, 4 Minor, 5 Nit.
Reviewer: egm codebase-details (fallback mode). Own trees: tree-REV7N (plain copy of r7n), tree-REV7N-base (r7m), tree-REV7N2/3 (more copies). Scratch: /home/user/build/rr6/out/REV7N (probes in p/, mutant logs mut1/mutA/mut3/mutimap*.log, checkpoint.md).

## What I did NOT do or conclude (first)
- I did not run the full suite (the builder's 5892 passed is unverified by me). I ran: the new file on r7m, the narrow set (load tests, r7n file, r7i/j/k/l, real_check_dry: 568 passed on pristine r7n), a wider set (18 files, 1226 passed on pristine) for survivors, and tests/test_hygiene + 3 siblings in a staged git copy (283 passed, 4 skipped, as the builder says).
- 38 mutants of mine, plus 6 extra probes. Mutant runs were stopped once and restarted: I let two runners edit one tree copy at the same time (my slip, the tree guard); those results were discarded and re-run; every tree was diffed against pristine r7n afterwards (identical).
- I did not run r7m with the good echo server (EV7N did: 105 leaks on r7m, 0 on r7n; my own probe also found 0 on r7n).
- Windows paths, mypy --platform win32, Docker: not checked.

## Judgement of the coordinator question: builder's _EchoImap test is VACUOUS for "server echoes the LOGIN line"
Probe (out/REV7N/p/probe_echo.py): the builder-style server saw exactly one command, CAPABILITY (answered BAD); the client ended with ImapConnectionError before LOGIN. Confirmed: LOGIN never reached in any of the 6 modes x 3 passwords (tests/test_r7n_findings.py `_EchoImap._serve`, the final `f.write(f"{tag} BAD...")`).
What the test still kills (they work through frame locals/chain on the CAPABILITY failure): scrub mutants R01 (context kept), R03 (frames not cleared), R04, R06, R07, R09.
What survives when the secret can only arrive through the LOGIN echo (mutimap.log; builder test vs a copy of the test with a server that answers CAPABILITY OK then echoes LOGIN):
| mutant | builder test | fixed-server test |
|---|---|---|
| X1 imap_count `_session` abort/OSError branch text += str(e) | survives | 6 failed |
| X2 same, IMAP4.error branch | survives | 2 failed |
| R05 `_ours` always True (never replaced by fixed text) | survives | 2 failed |
| I01 `_session` decorator loses its fallback class | survives (also wide set) | 2 failed |
| X3 `from e` in IMAP4.error branch | survives | survives: EQUIVALENT, the boundary scrubs it |
Rewrite: the server must send `* OK` greeting, answer `CAPABILITY` with `* CAPABILITY IMAP4rev1` + `tag OK`, then echo the LOGIN line in each mode; record that LOGIN was received and assert it (`login_seen == True`) in every mode so a protocol change in imaplib cannot make the test silent again. The patched copy is /home/user/build/rr6/tree-REV7N3/tests/test_r7n_fixed.py (one inserted branch; passes on r7n, kills the four mutants above).
Source: the r7n fix itself looks real (0 leaks with the good server, my deep walk of cause/context/args/dict/frame locals).

## Findings

### MAJOR 1 - the IMAP "server echo" tests do not exercise the case they name
See above. src: tests/test_r7n_findings.py:161-222 (`_EchoImap`), 253-300. Killing: fixed-server test above.

### MAJOR 2 - banner "worst case model cost" in scripts/run_real_check.py:1054-1055 is below what the code can reserve
`q_bytes = len(request_body(live, question_text("L000000000000", f"x@{EMAIL_DOMAIN}")))` is called "the exact bytes" but uses a placeholder 13-character address; the run sends `{tag}-p{i}@example.com` (about 23 characters, plus the twin address). Probe (p/probe_money.py, 12 people, model sonnet, max_tokens 16): banner bytes 372, real maximum body 382 (twin 387); banner total US$0.0814 vs real maximum US$0.0832; r7m's padded banner was US$0.1352 (an upper bound). So the printed "worst case" can be lower than the reserve sum the ledger can hold. The limit actually checked is the per-run cap and the reserve is the exact body (L02 mutant `len(body)-1` killed), so no money is lost, but a printed worst case under the reachable one is a false claim on a money line, and no test catches it (the M43-e test compares to the same placeholder). Fix: use the longest real question (build the plan first and take max over its emails, or an upper bound on lead id and address length). Kill test: assert banner >= worst_case_usd over the real plan.
(run_live_check.py is exact: it sends the same `(lid, em)` list.)

### MINOR 1 - the repo-wide guard is a name list, and can shrink without a test noticing
tests/test_r7n_findings.py:379-450. Planted sites: new top-level adapter with `m.login`, alias import, raw `open(cfg.key_file)`: caught. NOT caught: a file in a sub-package of src/lead_desk or in tools/ (glob is not recursive, `_guard_files`), `getattr(m,"login")(...)`, `m.authenticate`, `login_cram_md5`, `r = read_secret_line; r(p)`, other header names (X-Auth-Token, Api-Key, Proxy-Authorization), other path names (`pw_file`, `credentials`), a lambda; a dead `if False: scrub_error(x)` or an unrelated `scrub_error(...)` call counts as guarded (`_guarded`); a locally defined or foreign `secret_boundary` counts. Vacuity: mutant G01 (scripts dropped from the file list) and G02 (list = scrub.py only) SURVIVE, and no assert that any secret-touching function was found. The module docstring ("fails for a function that touches a secret and uses neither") overstates it. Fix: assert a minimum set of known guarded functions is found, recurse the globs, treat the guard as a tripwire in the docstring.

### MINOR 2 - the fallback is wider than the documented intent
`secret_boundary(fallback)` turns every non-ours `Exception` into a fixed refusal. Effects (probes p/probe_smtp.py, probe_live.py): (a) `SmtpProviderOutbox._dialogue` has an explicit `except (... MemoryError): raise` (tests/test_except_clause_hierarchy.py checks the clause text); now MemoryError leaves as SendAmbiguous("...unexpected error"): safe direction, but the documented behaviour is defeated and no test pins either way (mutant S01 survives). (b) a plain bug (RuntimeError, TypeError) in live `_post_once` / crm `_once` is reported as "could not be reached in time" / "Error": wrong label, hides defects. (c) imap MemoryError becomes ImapCountError. Decide and pin: keep MemoryError out of the fallback (`isinstance(e, MemoryError)` passes through scrubbed) and name the class in the fixed text.

### MINOR 3 - banner numbers of run_live_check not pinned
scripts/run_live_check.py:280-285. Mutant V01 (`min` instead of `max` over the questions) and V02 (`* a.runs` dropped: banner 3x too low at the default) both SURVIVE the narrow and the 18-file wide set. Source is correct today. Add a test with leads of different lengths and runs > 1.

### MINOR 4 - two small test gaps
R08: `secret_boundary` with `isinstance(e, Exception)` dropped (KeyboardInterrupt/SystemExit would be replaced by the fallback) SURVIVES narrow and wide sets. Real r7n is correct (probe: KeyboardInterrupt passes scrubbed). K01: the restore of `_STOP/_ANSWERED/_ERRORS/_STOP_LIMIT` in test_r7k `_fake_pool_context` SURVIVES (the `get_lock` on the fake is what the new test protects; the restore of the flags is unpinned).

### NITS
n1 CHANGELOG.md has no entry for scrub.py, the exact request body and the banner change (only the reworded octal line). n2 scrub_error does not follow `ExceptionGroup.exceptions`, `__notes__`, generators (none used in the repo), and `KeyboardInterrupt/SystemExit` args are not text-scrubbed. n3 `run_real_check.scrub` leaves values shorter than 4 characters unmasked (unchanged from r7m). n4 mypy on imap_count.py shows 3 errors, identical on r7m (not new). n5 exit-3 load run without the logged-vs-intended warning: NOT a defect (the JSON summary on stdout carries both numbers, check_invariants check 1 compares them, an r7j test pins it).

## Items the lead asked about
1. Choke point: probes on r7n (fake echoing LOGIN/AUTH, errors in the middle, imaplib.abort, OSError with path, header echo, odd class with the secret in `__dict__`, explicit and implicit chains, unicode error): no secret in args/dict/cause/context/traceback text/frame locals for imap, smtp (starttls and ssl), live, crm, read_secret_file. `raise failure from None` outside the except block is correct (R10 survivor = EQUIVALENT: context is empty there). Non-error paths unchanged (ValueError for a NaN send timeout still passes; signature, name and doc kept by wraps). Scrub is linear (cycle and 3000-deep chain fine). KeyboardInterrupt/SystemExit pass scrubbed. See Minor 2.
2. Guard: Minor 1.
3. Changed lines: M9-43 reserve is the exact bytes sent (`request_body` is the one builder; L01-L03 killed); ledger math unchanged. Banner: the printed numbers are not used as limits (true: `IMAP_LOGINS_MAX + POLL_EXTRA_LOGINS` printed; loop gives at most 14 logins <= 15) - except the model line, Major 2. Pins on r7m: P54, P57, P25, P55, P17, M13/B03 killed (B03 by an existing dry test).
4. Non-vacuity: new file on r7m base: 33 failed, 64 passed (confirmed; the passing 20 are the listed pins and guard-planted test). 38 own mutants: 26 KILLED, 12 survivors: R08 (REAL GAP), R10, R11 (EQUIVALENT), I01 (REAL GAP, killed by fixed server), I02, S02 (EQUIVALENT: inner handlers already map; unproven for MemoryError), S01 (MemoryError behaviour, Minor 2), V01, V02, G01, G02, K01 (REAL GAP). M81-b (touching values print one marker vs two): EQUIVALENT, both hide the whole value; my variant `end = lo` was killed.
5. Changed existing tests: r7k `_fake_pool_context` not weaker (fake got `get_lock`; flags restored); r7l: only `type: ignore` removed (counts 144 -> 125, noqa 164 = r7m); literals built from parts.
6. Hygiene: ruff 0.17.1 check "All checks passed", format --check "226 files already formatted"; bandit -ll exit 0; no secret literals in added lines (loopback addresses only; hygiene scan 283 passed).
7. Disclosed uncertainties: the "passes on base inside the file, fails alone" test is `test_the_driver_tests_leave_no_fake_flags_behind...`: it runs the repo's own test files; it passed because the base tree had the new r7k test file copied in. With the old r7k test file on r7m sources it FAILS (get_lock), so it is not vacuous. F3/O07 (`if True:` in netconnect `work`): planted by me, the F3 test KILLS it.
