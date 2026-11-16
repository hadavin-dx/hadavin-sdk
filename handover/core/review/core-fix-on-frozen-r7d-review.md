# Review of r7d (core-fix-on-frozen-r7d.patch, delta r7c to r7d), fallback goldfish reviewer

Money and mail path, no round cap. Date 2026-11-14. Made-up data, loopback only, no spend. Scratch copies only (cp -a of tree-R7D and tree-R7C under my scratchpad); repo2 and the tree-R7* folders were not edited.

## NOT CHECKED / NOT RUN (first)
- EV7D evidence had NOT landed (no /home/user/hadavin-sdk/handover/core/fix/EV7D-EVIDENCE.md after 3 polls; only /home/user/build/rr6/out/EV7D/ partial files). Nothing here reflects it.
- No full suite. I ran on a copy of tree-R7D: tests/test_r7d_findings.py, test_clock_steps, test_demo_folder_guard, test_portal_demo together: 225 passed (134 s, Python 3.12.3, DPLD_* unset). So the 7 r7c failures are fixed in that copy.
- Fail-before: I could NOT reproduce it myself (the new file on a copy of tree-R7C runs about 10 minutes because the IMAP cases wait out their old limits; my two runs hit my time limit). I read the builder's raw log out/R7D/raw/fb3.log instead: "58 failed, 8 passed", and the failed names cover N1, N2, N3, N4, N5, M1, m3, m4 as claimed. Taken from the log, not re-run.
- PowerShell: read only, never run (reset.ps1, start_all.ps1). Mutation runs: none (no mutant executed by me). gitleaks/hygiene tests: not run. Python 3.13/3.14: not tried.

## Verdict
Not clean. 1 Major (new defect in the M1 fix), 3 Minor, 3 Nit. Every other r7c finding is closed at its choke point (table below).

## Major

### M1-new. load_driver stops a healthy run and calls the desk "unreachable" (the answered flag is never set by a 2xx/4xx)
File: load_tools/load_driver.py:207-212 (send_with_retries) and :399-410 (_note_attempt).
In send_with_retries the loop breaks on any answer that is not a retry code BEFORE `_note_attempt(code)` is reached (line 208 `if not (code in RETRY_CODES or code is None): break`, then line 211 `if _note_attempt(code)`). So `_ANSWERED.set()` runs only for a 503. A desk that answers 202 to every request never sets the flag, and the error counter is cumulative (not "in a row"). After 2 x threads connection errors in the whole run (for example a few resets under load, or the desk dropping connections for a moment), `_STOP` is set and every remaining request is logged `driver:stopped` without being sent; the summary then says the desk "cannot be reached: every request ended in a connection error".
Scenario (made-up stdlib server on 127.0.0.1:18765, answers 202, drops the connection for requests 20 to 39, then answers again):
`python -m load_tools.load_driver --base-url http://127.0.0.1:18765 --scenario burst:100 --log o/req.jsonl --workers 1 --threads 2`
Output: `ERROR: the desk cannot be reached: every request ended in a connection error (is it running?)`, rc=3. Log: 19 lines `202`, 2 lines `error`, 79 lines `driver:stopped` (never sent). The sentence printed is false (19 requests were answered), 79 requests the desk could have taken were silently not sent, and a real load result is thrown away. The builder's test (a desk that accepts and hangs up from the first byte) cannot see this.
Class: a state flag that is set on one of two exit paths of a loop. Siblings: `desk_unreachable()` (line ~535) is per-attempt and fine; no other flag of this kind.
Fix: call `_note_attempt(code)` first in the loop (before the `break` test), so any code sets `_ANSWERED`; count errors "in a row" or only until the first answer (the code already says "no try has had any answer yet"). Test: the server above; assert rc 0 or the real summary, 100 log lines, none `driver:stopped`, and that no "cannot be reached" line is printed.
Related measurement (not a defect): a desk that accepts the connection and never answers (probe passes) ends with exit 3 after 62 s (burst:2000, threads 4), bounded by 2 x the per-try timeout; acceptable.

## Minor

### m1. N1 exit code 2: matches the script's documented contract, but contradicts the exit-code spec and constants
scripts/run_real_check.py:1034 refusal goes through the common handler (EXIT_REFUSED = 2). src/lead_desk/constants.py:33-34 says "4 a bad setting or path", and the spec given for this round says 4 for a bad setting or path; docs/settings.md:146-149 documents 2 "refused at the start (a missing or bad setting ...)" for this script. The review text said "exit 1" and the builder reports the deviation openly. Judgement: 2 is consistent inside the script and with its docs, so I do not ask for 1; but "one number, one meaning" is broken by the docs and the constants comment disagreeing. Fix (pick one, state it): either change every settings refusal of run_real_check to EXIT_BAD_SETTING_OR_PATH and the doc line, or correct the constants comment and docs/limits.md to say run_real_check uses 2 for settings. Test pins whichever is chosen.

### m2. Some CONTROL labels are false or empty
Honest: R7D-RESULTS item 5/6 admit no mutant was run. But labels name mutants as if checked:
- tests/test_r7c_clean_tree_guard.py: "mutant: tree_guard skips this kind of entry" is on all 13 tests, including test_an_unchanged_tree_reports_nothing and test_the_session_hook_stays_quiet_when_nothing_changed. A tree_guard that skips an entry kind cannot fail a test whose expected answer is "nothing changed"; those two are killed only by a guard that invents changes. The label is false for them (logic, not run).
- "passes on r7b" on the session-hook tests holds only with the r7c test-side helper copied in (builder item 6 says so; my r7c review measured two of them failing on the old test side). The comment itself does not say it.
- The 26 + 19 + 8 lines "passes on the frozen tree and pins behaviour that must stay" are one generic sentence for 53 functions; "changed test" is put on tests whose diff is only the label (test_reset_scripts, test_crm_hubspot).
Fix: label only what was run; for the 13, give the two no-change tests their own mutant text ("report a change that did not happen") and add "(with the r7c helper)" to the passes-on-r7b line, or run the named mutants once and cite the result.

### m3. Portal Stub records the query but nothing asserts it
tests/test_portal_demo.py:188-203: `Stub.queries` is filled and never read in any test (grep). The Stub now ignores `?limit=N`, so no test in this file proves the portal still sends `?limit=200` (demo_only/portal_demo.py:102). Not a weakening of an old assertion (the old key could not carry a query at all, hence the 5 KeyError failures), but the recorded list is dead. Fix: one assertion in a portal test that every recorded query equals `limit=200`.

## Nit

### n1. N6 (secret file checked once, re-read by the child) is neither fixed nor stated
r7c mail-path N6: no doc line, no child re-check was added (grep docs and README: nothing). Fix-dont-defer: one sentence in docs/real-services.md ("secret files are checked before the question and read again by each program; a file changed in between is refused by that program").
### n2. hubspot_probe `_why(status, body, _token="")` keeps an unused parameter "for old callers" (scripts/hubspot_probe.py). No old caller exists in tracked files; remove it.
### n3. imap_count.py docstring says the timer is needed "so a drip of handshake bytes cannot stretch it (the socket time-out alone restarts with every byte)". Measured: both handshake tests (silent and drip, total 1.5 s, step 30 s) end in 1.5 s, but CPython's own handshake loop already bounds the whole handshake by the socket timeout, and `sock.shutdown` in the timer runs on the socket object that `wrap_socket` has already detached, so it likely raises and is swallowed. The bound is real and tested; the comment explains the wrong mechanism. Fix the comment or drop the timer if a mutant without it still passes (not run).

## Closure of r7c findings (my checks)
- M1 load_driver dead desk: closed for a closed port: burst:100000 on 127.0.0.1:1 gives the one line `ERROR: the desk cannot be reached: nothing answers at that address (is it running?); no request was sent`, rc=3, 0.4 s, no log files made. New defect in the mid-run stop: see M1-new. Probe happens after path checks; base URL is already limited to loopback and http/https by `http_address(LOOPBACK_HOSTS)` (load_driver.py:609), so the probe connects only to this computer.
- M2/N1 live key before Start?: closed. check_one_secret("DESK_LIVE_KEY_FILE", ...) at run_real_check.py:1034, inside the refusal try, before the cost lines; message names the setting only, scrubbed. Same reader as live_claude.py:429. Exit code: see m1.
- m1/N3 SMTP cap: closed. The check now sits before the bare-code and final-line branches (smtp_outbox.py:147), `used + end + 2 > cap`; the old post-hoc check removed. Boundary tests exist (read in the new test file; not re-run alone).
- m2 CONTROL labels: comment-only, partly false: see m2 above.
- m3 reset.ps1: closed. Test-Path, Remove-Item (pid file and 9 files) all -LiteralPath; grep of every tracked .ps1 for Test-Path/Get-Item/Remove-Item/Get-Content/Set-Content/Copy-Item/Move-Item/Out-File/Get-ChildItem/Resolve-Path without -LiteralPath: none left. Not run in PowerShell.
- m4 start_all.ps1: read: settings in one try/catch before anything starts (exit 4, one fixed line), both Start-Process calls in try/catch routing to Stop-Start with code 4, Stop-Start default 3 kept; a failure after the first process started stops it. Reads right; untested in PowerShell. start_all.sh reads tries, pause, port before starting anything: right.
- m5/N2 connect and handshake deadline: closed (see n3 for the comment). ImapSettings: probed nan, inf, 0, -1, True, "5", 3601, 10**400, Decimal, Fraction, None: all one `ImapSettingRefused` line; 1, 3600, 0.001 accepted. Port 70000, -1, empty host, host with a newline: clean `ImapConnectionError` ("the mailbox could not be read"), no trace, no value echoed.
- N2b: closed for the times. N4 hubspot_probe: closed (only a fixed-list category is printed, no server text; sibling grep for `.replace(token|key|secret|password)` in src, scripts, demo_only, load_tools, tools: none; `scrub` in run_real_check masks by exact value but prints only setting names). N5 fake_model_server: closed, uses read_secret_line; the empty key file is refused by it. Secret-reader siblings: every key/password reader (live_claude, run_live_check, smtp_provider, crm_hubspot, n8n_api, fake_model_server) goes through regfile.read_secret_line (smtp password via read_secret_file, a thin wrapper); no `.read().strip()` of a secret left.
- N6: open (n1). N7 (equivalent mutant note): not addressed, no action needed.

## Changed old tests: old vs new, weaker?
- test_hubspot_probe token echo: new is stricter (no server text at all). OK.
- test_hubspot_probe cleanup test: assertion unchanged (reworded comment). OK.
- test_r5_refusals load driver: still exit 3 and one line; new line text matches the new refusal; the mid-run case is a separate test (which misses M1-new). OK as a change, incomplete as coverage.
- test_script_number_limits key cap: now `reads == [cap + 1]` through the one reader and the specific refusal text; the cap is still proven, a 3 MB file is still not read whole. Not weaker.
- test_real_check_dry banner: key file now written first; same assertions. OK (a missing key has its own test).
- test_portal_demo Stub: see m3. test_demo_folder_guard: copies tree_guard.py next to conftest (conftest imports it unconditionally); the guard it tests (missing demo folder stops the run) is unchanged. test_clock_steps: the fix is a `# wall-clock:` marker and a restructured wait; the test still patches time.sleep. OK. test_r7_no_replace_of_special: short relative socket name after chdir, restored in finally. OK.
- test_r7c_start_all_parity: new asserts `"[int]$Code = 3" in PS and "exit $Code" in PS and "exit 3" in SH`: text pins only (no PowerShell run); not weaker than before. No test was deleted in the delta (I read the delta file list: tests only added or edited).

## Exit-code and guarantee table
Mail/secret: secrets never printed (setting names only: yes); bad secret refused before reserve or connection (library yes; run_real_check now yes for HubSpot, SMTP, IMAP and the live key); named CA replaces system authorities, CERT_REQUIRED, check_hostname, TLS 1.2 floor: tls_trust.py untouched in the delta; IMAP total deadline now covers connect, handshake, reads, sends (DNS excepted, stated in the docstring); replies over cap refused whole: IMAP literal and SMTP (final line now counted); HubSpot and model replies not re-read this round.
Exit codes: load_driver 3 (closed port), 4 (path), 2 (usage) as spec; run_real_check bad live key 2 (m1).

## Not done by me (fix-dont-defer)
Mutants of the new load_driver stop logic and the IMAP _create_socket; the PowerShell scripts; EV7D evidence; the stray file "a<newline>b" writer (builder still has not found it; item 3 of R7D-RESULTS: it needs a named owner and date, the guard stays).
