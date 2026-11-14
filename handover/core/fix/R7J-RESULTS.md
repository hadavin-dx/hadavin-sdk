# R7J-RESULTS (builder r7j, fixes for the r7h review)

Base r7i (tree-R7I). Tree: /home/user/build/rr6/tree-R7J. Patches and sha256: this folder (sha256-r7j.txt, apply-matrix-r7j.txt: a-crlf, b-crlf, c-lf all `git apply --check` rc=0; build.log: byte-for-byte same as the tree, delta on r7i gives r7j).

## NOT RUN / NOT CHECKED / NOT DONE (first)
- NOT RUN: the full suite (EV7J does that). Run by me: tests/test_r7j_findings.py (42 tests, all pass, incl. the 62 s real-driver test), test_r7h, test_r7g, test_r7i, test_crm_hubspot, test_file_call_guard, test_hygiene, test_nosemgrep_form, test_load_tools, test_burst_retry, test_load_driver_facts (logs t3.log, final1.log, final2.log). Not run: Windows, IPv6 on a real machine without IPv6 (faked by a socket constructor raising errno 97), a real hung name server.
- Skipped by the machine: 3 to 4 tests (gitleaks program missing).
- NOT DONE: nothing from the m1-m7, n1-n3 list. m8 (pass-9 items) was done in r7i. J04b is an equivalent mutant (argument below), not a kill.
- Timing note: one r7g test (4 silent addresses) has a lower bound only on the first three addresses (the last gets what is left, which timing makes smaller: measured 0.1985).

## Per item (needed-check, class, fix, tests, mutants, fail-before)
| item | needed-check | class | fix | tests (tests/test_r7j_findings.py) | mutants | fail-before on a copy of tree-R7I |
|---|---|---|---|---|---|---|
| m1 | NEEDED | an operation that can fail for one address was outside the per-address try | `netconnect.connect_bounded`: socket made inside the try, closed only if made; OSError (errno 97) = this address failed, next is tried; non-OSError still ends the call | test_m1_* (3: errno 97 IPv6 then IPv4 with a listener; all families fail -> last error; RuntimeError not swallowed) | J01 killed | the first two FAIL |
| m2 | NEEDED | counter read before the slot is reserved (check-then-act race) | `_count["running"]` checked and raised under the lock BEFORE the thread starts, lowered in `work` when the thread ends, given back if `Thread.start` raises. `hung_lookups()` now = threads running (name kept; doc says so) | test_m2_* (20 concurrent callers with a 0.15 s slow start and cap 3: calls == 3, peak threads <= 3, all 20 get the one text; two waiting callers both counted; failed start gives the place back) | J02, J02b, J02c, J03 killed | the 20-callers and the two-waiting tests FAIL; the start-failure test is a PIN of new code (r7i had no reservation) |
| m3 | NEEDED | refusal by a cap for work that cannot hang | `_without_lookup`: IP address in digits (no `%`, ASCII) and `localhost` answered by the calling thread, no thread, no count (localhost = 127.0.0.1 then ::1) | test_m3_* (6 literals + both loopback order + connect + 5 names that still go the normal way) | J04, J04c, J04d, J04e, J04f killed; J04b equivalent | literals tests FAIL (refused at cap) |
| m4 | NEEDED | one-sided pin | fake-clock test with exact shares 0.25, 0.3, 0.3, 0.3 (also pins the last address) ; r7g test lower bound added | test_m4_* ; r7g `test_m1_the_total_limit_holds...` | O4 killed | PIN (rule unchanged, passes by design) |
| m5 | NEEDED | portability | `pytest.importorskip("resource")`; SO_LINGER built with struct.pack in the platform form; tests for no-poll branch, poll unit (ms), poll error | test_m5_* (3) | O8, O9 killed | PIN |
| m6 | NEEDED | untested wiring | real driver run (always 503, burst:3, 62 s): summary given_up 3, intended 3, exit 3, one line; fake-run test with intended 7, logged 5 | test_m6_* (2) | O5, O6, O6b killed | FAIL (exit code and line changed by m7) |
| m7 | NEEDED (lead decision: exit 3) | exit code hid a failed run | `load_driver.exit_code_and_line` (the one place): exit 3 and ONE line whenever given_up + stopped > 0 (given-up only: new text with n = given_up + stopped and both numbers named; stopped only: the old text unchanged). limits.md, load_tools/README.md, CHANGELOG say it plainly: a slow desk that used to pass now fails | test_m7_* (5 rows: (0,0)->0, (1,0), (0,1), (2,3), (5,0) -> 3; line count == decision count; one line) | J08, J08b, J09, J10, J11, O20 killed | FAIL for the given-up rows |
| n1 | NEEDED (one text) | second fixed text | `raise last or OSError(LOOKUP_REFUSED_TEXT)`; docs say so | test_n1 (fake look-up returns []) | J05 killed | FAILS |
| n2 | NEEDED | checked text is not used text (non-ASCII digits, Kelvin sign) | `crm_hubspot.archive`: `isascii() and isdecimal()`; `_confirm_existing`: returned email must be ASCII before lower() | test_n2_* (7 bad ids, one good id, Kelvin email, ASCII control) | J06, J06b, J07 killed | FAIL |
| n3 | NEEDED (pin) | race branch unpinned | no code change; test patches the wait to say "time is up" after the thread ended | test_n3 | O1 killed | PIN |
| O20 | NEEDED | NOTE not printed on a stopped run | gone: ONE line for both kinds with both numbers | test_m7 mixed row | O20 (no line when both kinds) killed | FAIL for the mixed row |

Mutant raw list: mutants-j.txt (one line per mutant: file, KILLED with the first failing test, restored-by-sha). Runner: mut.py (plants, runs the r7j file, restores by sha; all restored). 27 mutants: 26 killed, 1 equivalent. Reviewer mutants: O1, O4, O5, O6, O8, O9, O20 all killed by new tests. Own mutants (on changed lines): J01, J02, J02b, J02c, J03, J04, J04b-f, J05, J06, J06b, J07, J08, J08b, J09, J10, J11, O6b.
J02c was killed as an ERROR at the setup of the next test (the count never goes down, so the fixture's "look-ups ended" wait times out): a kill, not a failure of an assertion.
J04b (remove `not host.isascii()` in the literal test): equivalent on this Python (3.12.3): `ipaddress.ip_address` itself refuses full-width digits (ValueError, checked in the venv), so the text goes the normal way either way. The check is kept as a guard for Pythons whose `ipaddress` accepts such digits. `localhost` has its own ASCII check (J04d killed).

## Changed or deleted existing tests (old / new side by side)
1. tests/test_r7h_findings.py `test_the_burst_where_three_of_four_requests_were_given_up_ends_with_exit_code_0_and_a_note`: old `rc == 0` and `err.startswith("NOTE: 3 of 4 requests were not accepted") and "exit code stays 0" in err`; new (renamed `..._exit_code_3_and_one_line`) `rc == 3`, `err.startswith("ERROR: 3 of 4 requests were not accepted") and err.count("\n") == 1`. Why not weaker: the lead decision reversed the contract; the new test pins exit code, count and exactly one line.
2. tests/test_r7h_findings.py `test_a_stopped_run_still_ends_with_exit_code_3`: old `_main_with(..., stopped=1, given_up=1)` and "1 of 4 requests were never sent or were given up"; new `stopped=1` (given_up 0) with the same assertions. Why: with both kinds the line now names the total (given-up + stopped); the mixed case is pinned in test_m7 (2, 3). Same strength for the stop-only property.
3. tests/test_r7g_findings.py `test_m1_the_total_limit_holds_over_many_silent_addresses`: old `all(t <= 0.26 ...)`; new the same plus `0.24 <= t` for the first three addresses (exact rule in test_m4). Stricter.
4. tests/test_r7h_findings.py linger test: `import resource` became `pytest.importorskip("resource")`; SO_LINGER bytes literal became `struct.pack` (same bytes on Linux: `b"\x01\0\0\0\0\0\0\0"` = pack("ii", 1, 0)). Same assertions.
No test deleted. Existing netconnect tests (hung_rig cap tests, r7g shims) pass unchanged.

## Sweeps
- Socket creation outside a try (class of m1): src, scripts, load_tools, demo_only, tools. Found: `smtp_outbox._connect` (own try, maps to SendUnreachable: fine), `scripts/run_real_check.free_port` (with-statement, fails the check: fine), `reset_check`/`burst`/fakes use `create_connection` (stdlib tries every address). No other site.
- Counter read before the slot is reserved (class of m2): `server._Lingerer.add` (check and insert under one lock), `crm_hubspot._call` (cap check and increment under one lock), `smtp_provider.send` (same), server `_slots` (under `_slot_lock`). No other site.
- isdigit/isnumeric/isalnum/isalpha/isdecimal/`\d` on values that reach a URL, path, command or file name: found and fixed `crm_hubspot.archive` and the returned-email compare. NOT-NEEDED: `smtp_outbox` lines 149/152 act on bytes (ASCII only); `desk.py:2266` `item_id[1:].isdecimal()` feeds an SQL parameter only, after `_exists` validated the id with the ASCII rule at 2256; the rest already have `isascii()`.
- Suppressions unchanged: noqa 175, nosemgrep 28 lines, type-ignore 126 lines (grep on tree-R7I and tree-R7J, identical). Ruff 0.17.1 check and format --check: all clean (194 files).

## Honest limits
- The cap now also refuses a legitimate look-up when more than 8 callers look up at the same moment (fail-closed, stated in limits.md).
- `localhost` is answered as 127.0.0.1 then ::1 without asking the system; a machine that maps `localhost` elsewhere is not followed (documented in limits.md via "answered at once").
- The m6 real-run test takes about 62 s by nature (the retry time is a code constant).
