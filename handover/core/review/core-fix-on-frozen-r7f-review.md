# Review of r7f (core-fix-on-frozen-r7f.patch, delta r7e to r7f), fallback goldfish reviewer

Frozen tree 49d3c859 plus core-fix-on-frozen-r7f.patch; tree /home/user/build/rr6/tree-R7F; delta core-fix-r7e-to-r7f-delta.patch (16 files). Money and mail path, no round cap. I changed no tree: all work in a copy under /home/user/build/rr6/tmp-REV7F (repo/, stage/, mutA/), loopback only (every run under `unshare -n` with the lo_up driver), made-up data, no spend. One test process at a time. The builder's R7F-RESULTS.md claims were treated as unverified.

## NOT RUN / NOT CHECKED (first)

- The full suite on the r7f tree was NOT run by me. I ran: the 22 files the builder did not run (all 22), plus test_r7f_findings, test_file_call_guard, test_hubspot_probe, test_r7m_new, test_hygiene, test_vendor_hosts. The other ~112 files I did not run.
- The "fails on the frozen tree" labels of the m1 fix (10 cases of test_special_output_files, hang_up-error of test_portal_demo) were NOT re-run against the frozen tree. I read the label text and the diff only.
- The IPv6/second-address finding (m1 below) is from reading the code; I did not build a blackholed-address test.
- The pass 8 mail review items were not re-walked one by one; I re-ran a 13-mutant sample (point 6).
- Not run: PowerShell, Python 3.13/3.14, real services, gitleaks history scan (the hygiene test warns "skipped"; set DPLD_REQUIRE_SCAN is not set in my run).

## Verdict: NOT CLEAN

Counts: 0 blocker, 2 major (M1, M2), 2 minor (m1, m2), 1 nit (n1).

## Major

### M1. netconnect: a name look-up that raises a non-OSError gives a traceback on stderr and an IndexError (regression against r7e)

`src/lead_desk/netconnect.py` `resolve_bounded`: the helper thread catches only `OSError`. `socket.getaddrinfo` raises `UnicodeError` (a ValueError) for a label longer than 63 characters, an empty label, or a lone surrogate. The thread then dies, `threading.excepthook` prints the full traceback of the helper thread to stderr, and the `finally` sets `done` with `box` still empty, so the caller does `box[0]` and gets `IndexError: list index out of range`.

Proof (made-up host, run in my copy): `connect_bounded("a"*70 + ".example", 9, 1.0)` and `connect_bounded("\udcff.example", ...)` print "Exception in thread name-lookup: Traceback ... UnicodeError: label empty or too long" and raise IndexError.

Reachable: `REAL_IMAP_n_HOST` is not validated anywhere (run_real_check.imap_settings takes `env.get(p + "HOST", ...)` as it is; `ImapSettings` checks only the user). I called `counts_by_key(ImapSettings(<70-char label>, ...))` with a valid password file: r7f raises `IndexError` out of the mailbox read (and prints the thread traceback); r7e (tree-R7E, same call) gave the fixed line `ImapCountError: the mailbox user or password has characters the mailbox login cannot carry` (wrong wording, but one line, no class name). `run_real_check.py` only catches ImapCountError there (line 524), so an IndexError would end that script in a traceback. SMTP host is checked by a label regex, so there the path is closed, but the SMTP error text would carry the class name (`SendUnreachable("IndexError")`) if a caller passes another host.

This breaks the defect rule (no traceback, no Python class name, one refusal line plus a fixed exit code). The docs claim in limits.md ("the same time-out error ... at the limit") does not cover it.

Fix at the choke point: in `work()` catch `Exception` (not only OSError) and store it; in `resolve_bounded` turn any stored non-OSError into `OSError("the host name cannot be looked up")` (fixed text, no host, no class name); never index an empty box (treat an empty box as the same OSError). Add tests: label of 64 and 70 characters, empty label, lone surrogate, NUL in the name: each gives one OSError with the fixed text, nothing on stderr (`capfd`), and no IndexError; end to end for the mailbox read (one ImapCountError line) and the sender (SendUnreachable). Prove they fail on r7f.

### M2. r7e M1 is only partly closed: a run that stopped a request early can still end rc 0 with no line

`load_tools/load_driver.py` counts `summary["stopped"]` only from lines whose final status is `driver:stopped` (requests never sent). A request that was already in its retry loop when the run-wide stop was set is logged with `gave_up: "stopped"` and `final_status: "error"`, not `driver:stopped`. If another in-flight request is then answered late, `unreachable` is false, `stopped` is 0 and the run ends rc 0.

Proof (server written by me, loopback: the first real request is answered with 202 after 2 s, every other connection is closed at once; `burst:2`, 1 worker, 2 threads): rc 0, stdout `{"final_status": {"202": 1, "error": 1}, ..., "stopped": 0, "unreachable": false}`, no ERROR line; the log shows `('error', 'stopped', 4 attempts)` and `(202, None, 1)`. So one request was given up by the stop, the run ended 0, and nothing says so. The M1 test only covers the case where unsent `driver:stopped` lines exist.

Also docs/limits.md now states "a run that is stopped early ... ends with exit code 3 and a line": false for this case.

Fix: count both `driver:stopped` and `gave_up == "stopped"` lines (or use `stop.is_set()` in the parent), and give the STOPPED_EARLY line with the right count; add a test with this server pattern (fails on r7f); keep the doc sentence true.

The other patterns I tried behave as the builder says: only 202 (rc 0), only 429 (rc 0, final 429 for all), 503 for 3 s then 202 (rc 0), 503 for ever (rc 0 after the 30 s limit, final 503, `gave_up: deadline`), drops for 3 s then answers (rc 3, "cannot be reached", true because nothing ever answered; stopped lines present), drops 6 connections then answers (rc 0, all 202). No false "cannot be reached" line in any of them.
Observation, not a defect of the stop rule: first request answered, all later connections dropped (`burst:4`): rc 0 with `error: 3` after the 30 s per-request limit (`gave_up: deadline`). No stop is involved; the later check counts the lost requests. I list it so the owner knows rc 0 does not mean all requests were accepted.

## Minor

### m1. netconnect: the time is shared by all addresses, so a silent first address blocks the others (by reading, not run)

`connect_bounded` gives each address "the time that is left". `socket.create_connection` (r7e) gave each address the full timeout in turn. With a dual-stack host whose first (IPv6) address silently drops packets, the first connect now uses the whole limit and the IPv4 address is never tried (`left <= 0` then TimeoutError). For a mailbox read the limit is min(step 30 s, total). Fix: give each address a slice (for example the time left divided by the addresses still to try, with a floor), and add a test with a fake two-address look-up whose first address is a listener that never accepts. The docstring "each address ... with the time that is left" and imap_count's "for each address" comment should then match.

### m2. docs and the M2 sentence

limits.md claims exit code 3 for every early-stopped run (see M2), and the new "Name look-up" paragraph does not mention that a bad host name is refused by the same path (add after M1 is fixed). Fix both in the same piece of work.

## Nit

### n1. netconnect closes the socket only on OSError

`sock.close()` is in `except OSError`; a KeyboardInterrupt during `connect` leaves the socket to the garbage collector. Use `except BaseException: sock.close(); raise` for non-OSError. Low risk.

## Points asked for

1. netconnect (new code). Late answer: never used (the result of a late look-up is dropped; no connection is made after the wait times out). Thread: `daemon=True`, named "name-lookup", does not keep the process alive; the leak is one thread per timed-out look-up until the system answers (stated in limits.md; with a dead name server and many retries threads can pile up, bounded by the number of calls). Host name or secret in a log: the thread name is fixed; its traceback text does not hold the host (checked in the output above) but the traceback itself is the defect in M1. Race: a result written after the wait ended is ignored, `box` is written once. IPv6: getaddrinfo is called with no family, so both families come back; the sharing of time is m1. Exception paths: gaierror (empty name, spaces, NUL, "999.1.1.1", ".", "xn--a.example") all end as OSError with no traceback; UnicodeError family is M1. Tests `test_f6_*` do not cover M1 or m1.
2. Cipher words. On OpenSSL 3.0.13 I listed `get_ciphers()` for 14 cipher strings. All 13 ciphers with `Au=None` have names starting `ADH-` or `AECDH-` (incl. `AECDH-NULL-SHA`), so the new words cover every anonymous cipher; no anonymous cipher is missed. The old word "anon" refused 0 names for `ALL:@SECLEVEL=0` (confirmed gap), the new words refuse 12; `ALL:!aNULL:@SECLEVEL=0` and `ALL:!aNULL:!eNULL:@SECLEVEL=0` refuse 0 (correct: no weak word left); `DEFAULT` refuses 0. Test setup change in test_r7m_new.py: it does NOT weaken the test. Before, the client offered anonymous ciphers, so the new cipher check could refuse the context for the wrong reason. Now the cipher check passes and the version check is what refuses: I replaced `if conn.version() not in TLS_OK_VERSIONS:` with `if False:` in a copy and test_r7m_new fails (`test_f1_smtp_login_never_goes_out_over_a_tls_version_below_1_2[ssl]`). Limit unchanged and stated in the docstring: a lowered level with no weak cipher left is not detected.
3. M1 of r7e: see M2 above. NOT closed.
4. hubspot_probe `_mask`: returns the fixed text "(id hidden)" for any value; the owners line prints a count; `_why` prints a category only from a fixed word list; the delete warning shows the probe's own made-up email or the fixed mask. The 3 new tests pass (point 8). Closed.
5. `book_folder_in_repo` with a data link: a live link and a dangling link both end with `Failed: data in the repository folder is a link ...`; the link target stayed empty and the link stayed; a plain call still works and removes the `data` folder it made. Closed.
6. CONTROL tests against mutants. I ran 13 (each: the single test on a clean copy, then on the mutant copy, `-x`): I10, S06, R08, P04, L05, V03 (spec file MAIL8), A07, A12, A14, B02, G03, T01, T02 (spec file MAIL7). All 13 pass clean and fail on the mutant. I did not check that each failure is for the named reason beyond the test name (`--tb=no`). Not run: the other 58 CONTROL tests.
7. Suppressions: same counts in tree-R7E and tree-R7F for noqa (175), type: ignore (126), nosec (8), nosemgrep (31), S603 (7), pragma no cover (6), pytest.mark.skip (52), xfail (0), `ruff: noqa` (1). netconnect adds none. Changed existing tests, old against new: test_r7m_new line 57 (setup only, see point 2); test_file_call_guard (two table rows removed, two added with reasons; the new rows are exactly the calls in netconnect); test_hubspot_probe (one assertion added, none removed); test_portal_demo and test_special_output_files (comment lines only); tests/support.py (refusal added). None weakened, none deleted.
8. The 22 files the builder did not run: all run by me together on a staged copy (git init, git add -A, no commit, /home/user/build/rr6/bin on PATH, under unshare): 422 passed, 1 skipped, rc 0 (log /home/user/build/rr6/tmp-REV7F/run22.log). Also test_r7f_findings + test_file_call_guard + test_hubspot_probe + test_r7m_new + test_hygiene + test_vendor_hosts: 176 passed.

## Closure of r7e findings

- M1: NOT closed (M2 here).
- m1 (labels): the label text is now as the builder describes; the claim about the frozen tree was not re-run by me.
- m2 (real-services.md): closed, the new sentence says what the code does.
- m3 (data link): closed (point 5).
- n1 (no total limit for a run): closed as a stated limit (limits.md says it plainly with the 62.7 s figure), but the new sentence about exit code 3 is not always true (M2).

## Next step

Fix M1, M2, m1, m2, n1 in one batch (r7g), with tests that fail on r7f, then one independent pass; do not rely on the builder's mutant table for the new lines.
