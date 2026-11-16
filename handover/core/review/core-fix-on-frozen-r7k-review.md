# Review of the r7k delta (r7j to r7k): codebase-details goldfish, fallback mode

Reviewer: egm codebase-details (fallback), fresh context. Own copy: /home/user/build/rr6/tree-REV7K (tree-R7J + the delta patch; byte-identical to tree-R7K except caches). Scratch: /home/user/build/rr6/out/REV7K. Date 2026-11-14, about 55 min.

## VERDICT: NOT CLEAN. Blockers 0, majors 2, minors 2, nits 3.

## First: what I did NOT run, and my own slips
- NOT run: the full suite, run_real_check family (rrc), Windows, a machine without IPv6, a real name server, real mail or model.
- NOT run: my own mutants on the wide set for O02, O04, O05 (killed on the wide set by r7j, see below) and O12 (boundary `<=` to `<`, a time-limit edge; judged equivalent, not proven). I stopped the last runner at the time box and restored by hash (netconnect.py was mutated at that moment; restored from the clean copy, `cmp` equal, no leftover runner).
- NOT checked: whether the key can be read from the traceback frames (`tb_frame.f_locals`); only exception text, repr, args, attributes, cause and context chains were checked (same scope as the builder's helper).
- Slip 1: two of my mutant runners shared one temp folder name (O24). Runner 1 got a CRASH (temp folder gone) and runner 2's O24 result is tainted. I re-ran O24 alone with its own folder (KILLED, see table).
- Slip 2: my first wide run put `tests/test_load_tools.py` after the r7k file; three of my "KILLED" results (O07, O22, O12) came from the test pollution of finding F2, not from the mutant. I re-ran O07 and O22 with the load tests first; both SURVIVED (genuine). O12 not re-run.
- Two runners at once at most (one for part of the time); busy loops for the load test were not test processes.

## Findings

### F1 (MAJOR, mail secret path) the mailbox password stays reachable through `__context__` of `ImapCountError`/`ImapConnectionError`
- Where: src/lead_desk/imap_count.py:298-306 (the three `except` clauses at the end of `_session`); they all use `raise ... from None`, which only hides the context from a printed traceback; `__context__` still holds the imaplib error.
- Evidence (probe, scratch, run by me): /home/user/build/rr6/out/REV7K/test_probe_imap.py with /home/user/build/rr6/out/REV7K/fake_imap_echo.py (the repo's FakeImap whose NO reply to LOGIN repeats the line it received). Output: chain is `ImapCountError('the mailbox could not be read')` then `error(b'login LOGIN "reader-user" "<the real password>"')`. The printed traceback does not contain the password (`from None`), the chain does.
- Class: exactly the class of M9-32 (the builder's own words: "an earlier error kept as `__context__`; `from None` only hides it from the printout"). The builder swept `live_claude._post`, `crm_hubspot._once` and `regfile.read_secret_line` and wrote that only three sites kept a context. The mailbox reader is a fourth site. Needs a server that echoes the login line (a hostile or broken server), so it is not a normal-path leak, but k1 itself defines the bar (no text in the chain).
- Fix at the choke point: in `_session` (or a wrapper like the regfile one) clear `__context__` and `__cause__` of the `ImapCountError`/`ImapConnectionError` before raising; `_password()` is fine (its FileRefused is cleaned in regfile).
- Killing test in words: a fake mailbox server (TLS, like FakeImap) answers LOGIN with `NO` plus the received line; call `counts_by_key` with a password file; assert the password appears in no text of the exception chain, using the existing `_assert_no` helper of tests/test_r7k_findings.py. Fails on r7k (my probe), passes once the context is cleared.
- Also swept, found clean: smtp_provider (AUTH token only inside one `_command`, replies parsed to a number, errors give `type(e).__name__`, `from e` chains hold only the fixed `_Closed` texts or OS errors that carry no data), smtp_outbox (no login), server.py and desk.py (log lines use `type(e).__name__`), scripts/hubspot_probe.py and scripts/n8n_api.py (answers and texts dropped; `raise SystemExit from None` keeps a context but a SystemExit is never printed with it), run_real_check.py (prints `str(e)` of fixed-text classes only).
- Can `__context__` itself carry a key in the three fixed sites? After the fix no: the top error's context is set to None, which drops the whole chain below it. Remaining path: `err.__cause__ = None` in `_post` is never needed because every `LiveError` in `_post_once` is raised `from None` (mutant O22 survived, equivalent, nit n1).

### F2 (MAJOR, test quality) the new k15 tests leave `load_driver._ERRORS` (and `_STOP`, `_ANSWERED`, `_STOP_LIMIT`) replaced for every later test in the same process
- Where: tests/test_r7k_findings.py:940-960 (`_fake_pool_context`): its fake `Pool.__enter__` calls the real initializer `load_driver._init_worker`, which sets module globals to `types.SimpleNamespace(value=...)` objects (no `get_lock`). `monkeypatch` restores only `get_context` and `START_LEAD_SECONDS`.
- Evidence: raw run /home/user/build/rr6/out/REV7K/pollute.log: `pytest tests/test_r7k_findings.py tests/test_load_tools.py -k "k15 or retry_outlasts"` gives `FAILED tests/test_load_tools.py::test_retry_outlasts_a_desk_restart ... AttributeError: 'types.SimpleNamespace' object has no attribute 'get_lock'` (1 failed, 15 passed). Control, same tests in the other order: pollute-ctl.log, 16 passed. No other test file in r7j uses `initializer` (grep).
- Why it matters: the suite is green only because the default order puts `test_load_tools.py` before `test_r7k_findings.py`. xdist (the studio rule files mention xdist workers) or a random order fails a real test depending on which worker gets which file. It also disturbed my wide mutant runs (slip 2).
- Fix: restore the four globals after each k15 test (a fixture with `monkeypatch.setattr(load_driver, name, old)` for each, or a `monkeypatch.setattr(load_driver, "_init_worker", ...)` stand-in that sets and later restores). Killing test: run k15 and `test_retry_outlasts_a_desk_restart` in that order in one process; must pass.

### F3 (minor, test gap) m1 is only half pinned: the thread that ends AFTER the start-failure path already gave the place back
- Mutant O07 (`if not state["released"]:` in `work` replaced by `if True:`) SURVIVES on the wide set re-run (load tests first, 502 s, raw in w4/). The k13 `_StartsThenFails` case ends the thread before the `except` path runs; the other order (the except path releases first, the thread ends later and decrements again, count -1, cap drifts above 8) is untested. That order is the real race behind m1.
- Killing test in words: a Thread stand-in whose `start()` begins a thread that waits on an event, then raises; after `resolve_bounded` has raised, release the event, wait for the thread, assert `hung_lookups() == 0` (never -1) and that 8 places still exist.

### F4 (minor, behaviour change to state plainly) `localhost` no longer reaches an IPv6-only listener
- netconnect now answers `localhost` with 127.0.0.1 only. A mail host named `localhost` whose server listens on `::1` only is refused. Documented in docs/limits.md and CHANGELOG ("IPv4 only"), so not a doc defect; listed so the owner knows it is a decision, not a side effect. Not checked on a real dual-stack machine.

### Nits
- n1: `err.__cause__ = None` in live_claude._post is unreachable today (equivalent mutant O22 survives on the wide set). Harmless defence in depth.
- n2: an exit-3 load run now prints no "N intended, M logged" warning (only the ERROR line); a run that lost log lines AND gave up requests loses that hint (check_invariants.py check 1 still fails it). By design (n2 of the r7j review); say so in the README if wanted.
- n3: `0177.0.0.1` also becomes 127.0.0.1 and `1.2.3` becomes 1.2.0.3 (system rules, see item m3 below); not a defect.

## Per item of the brief

(1) Source changes
- M1: right. `localhost` gives `[127.0.0.1]` only; in `connect_bounded` `raise timeout or last or OSError(...)`: a time-out beats a later refusal (probed by killing N08/N09/N19/N20 and my O09/O10/O11). test_r7f_findings passed inside my wide runs (1685 passed in raw-O22-wide, only F2's pollution failed); I did not run r7f alone, so this is indirect. Callers: imap_count treats a TimeoutError as "not repeated" (stricter), no weakening.
- m1: slot released exactly once in both orders by the code (flag under the lock in `work` and in the `except`). Code correct; test half missing (F3). Note a KeyboardInterrupt between thread start and the `except` can make the running count transiently lower than the real thread count (nit-level, signal timing only).
- m2: a non-OSError on address 1 is re-raised at once by the unchanged `if not isinstance(e, OSError): raise`; pinned (N4 killed).
- m3: AI_NUMERICHOST in the calling thread cannot hang (no name server; my check: `getaddrinfo("017.0.0.1", ..., AI_NUMERICHOST)` gives `15.0.0.1`). The claim is right for glibc (leading 0 is octal; I also saw 0177.0.0.1 give 127.0.0.1, 127.1, 0x7f.1, 2130706433 give 127.0.0.1, `""` and `08.0.0.1` refuse). It does not change the destination: r7j sent the same string to the same system look-up in a thread. The loopback http guards (config.py:189, crm_hubspot.py:166) compare the host text with exact strings, so `127.1` or `0177.0.0.1` stay refused there. The only change is that these forms skip the cap. Full-width digits are kept out by the `isascii()` guard (the system would accept them: I saw `１２７.0.0.1` answer 127.0.0.1). Not checked: musl or Windows octal rules.
- M3: `driver_error` counted in `exit_code_and_line`: exit 3, one line, same count n = given_up + stopped + errors; no double count (`_stopped_line` overwrites `gave_up` to "stopped"; `desk_unreachable` is False for driver errors because `attempts` is empty). Mutants O14-O20 and N13-N18 killed.
- M9-32: three fixed sites correct (chain cleared at `_post`, `_once`, `read_secret_line`); the sweep missed imap_count (F1).

(2) Non-vacuity (new test file alone, tree copy, one runner, restore by hash, all `restored-ok`; raw in /home/user/build/rr6/out/REV7K/muta.out and mutown.out)
- KILLED by tests/test_r7k_findings.py alone: M9-32, M9-33, M9-34, M9-40, M9-64, M9-65, M9-67, N05, N06, M9-69, M9-16.
- My own 24 mutants on changed lines: narrow set (r7k file alone) KILLED 16: O01 (flag removed), O06, O08, O09, O10, O11, O13, O14-O21 (O21 = crm keeps context), O23. SURVIVED narrow 8: O02, O03, O04, O05, O07, O12, O22, O24.
- Survivors on the wide set (31 files: the 22 of setC, r7d..r7k, r7m, smtp_outbox, reply-cap, load tools, 900 s): O03 KILLED (r7g, 64-letter name); O05 KILLED (r7j, zone name); O24 KILLED (r7g test_m1_a_first_address_that_never_answers..., re-run alone); O07 SURVIVED (F3); O22 SURVIVED (equivalent, n1); O02 (`not host` dropped) and O04 (`or None` dropped): equivalent by reading (an empty name gives gaierror and so None; getaddrinfo never returns an empty list), not run on the wide set; O12 not re-run (boundary).
- The r7k file alone does not kill O03 (a name such as `a..b` or a 64-letter label reaching `_without_lookup` is only pinned by older r7g tests): fine, but the k14 list could include it.

(3) Timing flakiness of the 139 tests: three runs, 139 passed each (27.3 s, 27.7 s, 31.8 s with three busy loops running). No flake seen. Order dependence is F2.

(4) Changed existing tests, old vs new:
- test_r7g 0.24 lower bound removed: the upper bound `<= 0.26` and `len(log) == 4` stay; the exact share is pinned by a fake clock (r7j test_m4) and my mutant O24 (`own = left`) is killed by an r7g test; not weaker for the rule that matters, weaker only as a real-time lower bound, which is what failed under load. Accepted.
- test_r7j localhost: changed on purpose with M1, new assertion is stricter on the family (`AF_INET`) . Accepted.
- test_r7j `127.1` removed from the needs-a-look-up list: moved to k14; my O01/O03 style mutants on that line are killed. Accepted.
- test_r7j m7 `logged=7 if code == 0 else 5`: the exit-0 row now asserts `err == ""` with logged == intended; exit-3 rows with 5 of 7 logged now also pin that no WARNING appears (stricter). Accepted.
- test_r7h rename: name and docstring only. Accepted.

(5) Hygiene: suppression counts equal r7j by my grep (noqa 175, type: ignore 126, nosemgrep 29 by my pattern, nosec 8, pragma no cover 6, skip/xfail 52 both trees). The key in the new tests is built from parts (FAKE_KEY imports); the only non-loopback addresses in tests are 10.0.0.x and 15.0.0.1 (documentation of the octal result), no real key or account. ruff check and ruff format --check clean (src, load_tools, tests). Docs match code: limits.md (localhost, time-out wins, once-only release, digit forms), load_tools/README.md and CHANGELOG say exit code 3 and `driver_errors`; I found no stale "exit code stays 0" (the load_driver comments and docstrings were updated; limits.md line 101 says exit code 3). Docs do not mention F1 (new).

(6) M9-61 equivalent claim: correct. Without `parse_constant`, NaN/Infinity/-Infinity parse to floats that `_has_non_finite` refuses with the same class and text (a stack walk, no recursion); `1e999` needs `_has_non_finite` (K13/K14-style mutants kill that side). `parse_constant` is therefore redundant defence in depth; survivor is equivalent, not a gap.

## Counts
Blockers 0; majors 2 (F1, F2); minors 2 (F3, F4); nits 3.
Next step for the author: fix F1 at `_session` with its killing test, fix F2 by restoring the globals, add the F3 test, then re-run the new file in both orders with the load tools.
