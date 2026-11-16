# Mail-path pass 7 review of patch r7c (INCOMPLETE: mutation step not run)

Reviewer: EGM goldfish, fallback mode. Date 2026-11-14 (UTC). Patched tree: /home/user/build/rr6/tree-R7C. Scratch copy used: /home/user/build/rr6/tree-M7C. Nothing in repo2, tree-R7B or tree-R7C was edited. Loopback only, made-up data, no spend, no "Start?" prompt answered yes.

## What did NOT get done (read first)
1. Step (b), the 25+ mutants, is NOT done. 54 mutants are written (/home/user/build/rr6/out/MAIL7/work/specs7.json, runner mut7.py) but none was run. No killed or survived counts exist. Reason: the clean-tree baseline of the 22-file mail test set (setC.txt) was still running at the 8-minute limit; it showed 3 failures (around 84-90%) whose names I never got, so mutant runs would give false kills. Do not read this report as mutation-checked.
2. The builder's claim that the D05/D11/D20 mutant kills hold is NOT verified by mutation. I only verified the behaviour by loopback probe (below). The builder says the D05/D11/D20 tests also pass on old code; I did not re-check that.
3. Baseline result (command: runset.sh on tree-M7C, output work/baseline-C.txt): 3 failed, 1104 passed, 1 skipped in 438 s, rc=1. The 3 failures are all the [socket] case of tests/test_r7_no_replace_of_special.py (counters writer, flag writer, check-and-open output). Cause not investigated (could be the scratch-copy path or the sandbox; not proven). They are not mail tests, but the mutant runs must deselect them first.
4. Not checked: STARTTLS plaintext injection, HELO fallback, IPv6 and hostname forms, the run_real_check Start? flow beyond the live-key case, load_tools beyond the catcher host restriction.

## Prior findings, verified by code read plus loopback probe with a fake server
- D05 (IMAP below TLS 1.2): server saw only CAPABILITY, no LOGIN. OK.
- D11 (SMTP below TLS 1.2): ssl mode gives SendRefused; starttls mode server saw EHLO, STARTTLS, no AUTH. OK.
- F-B (bad secret files refused before Start?): fixed for HubSpot key, SMTP password and IMAP passwords (run_real_check.py check_secret_files 656-675). NOT fixed for the live model key: see N1.
- F-C (multi-line SMTP reply cap): fixed for continuation lines; final line not counted: see N3.
- F-A (IMAP total deadline): holds inside greeting, line and literal reads (greeting drip, total 2.0 s ended at 2.0 s with ImapTotalTimeout). Does not hold for connect and handshake: see N2.
- D20: test exists; mutant kill not verified.

## Clean results
- run_live_check.py: 20 key-file variants (CRLF, BOM, two lines, NBSP, ESC, bad UTF-8, NUL, short, empty, 2 MB, no newline, padded, VT, FIFO, symlinks, dangling, directory). No key text in any output; fixed refusal lines; refused before the cost line; no ledger created.
- CA file: cadata replaces system authorities (1 cert loaded against 122 system ones). CERT_REQUIRED, check_hostname and min TLS 1.2 hold. Key-only, CRL-only, empty, junk, CR-only, DER+trailing files refused with fixed text, no path shown.
- HubSpot base URL: lookalike hosts refused (only a homograph label under the real vendor suffix passes; not exploitable).
- SMTP smuggling (bare LF/CR dot lines, NEL, LS, FF, VT, NUL): no bare CR/LF reaches the wire; dot stuffing works. ssl-mode silent or drip server stays inside the 2 s budget.

## Findings (killers: /home/user/build/rr6/out/MAIL7/killers/test_m7_new.py, 8 cases, all fail on r7c; run from /tmp)

### N1 Major: live model key file is not checked before Start?
scripts/run_real_check.py check_secret_files (656-675) skips the live model key. Probe: config /home/user/build/rr6/out/MAIL7/probes/rc/cfg-bad.env with DESK_LIVE_KEY_FILE ending in a non-breaking space, run with --live-model. Output ended `Start? [y/N] stopped, nothing was called`. Same class as old F-B. Secret text was not echoed. Fix: after the live settings are built, call read_secret_line(live.key_file, ...) and map the error to the setting-name refusal line, before the cost lines. Test: test_m7_a_bad_live_key_file_is_refused_before_the_start_question.

### N2 Minor: IMAP total deadline does not cover connect and TLS handshake
imap_count.py _BoundedImap passes timeout=step to the socket, so connect plus handshake last up to timeout_seconds. Probe p_imap: silent TCP server, total 2.0, step 10.0 took 10.0 s. Zero or negative total still connects first. The module docstring ("one step can still last up to timeout_seconds more") is stale. Fix: override _create_socket to use min(timeout, time left) and raise ImapTotalTimeout when nothing is left. Test: test_m7_the_total_time_limit_also_holds_for_the_connection_and_the_tls_handshake.

### N2b Minor: ImapSettings accepts bad times
imap_count.py:79-88 validates only the user. total_seconds nan or inf silently disables the deadline (probe p_imap2: greeting drip ran 10.2 s against 2.0 s for a finite total). timeout_seconds nan, 0, negative raise a raw ValueError; inf raises OverflowError. Host and port unchecked. Fix: require finite, > 0 and <= a maximum for both times, as ProviderSettings and HubspotSettings do. Test: test_m7_a_total_limit_that_is_not_a_positive_finite_number_... (4 cases).

### N3 Nit: final SMTP reply line not counted in the cap
smtp_outbox.py _read_reply (139-167): continuation lines add to `used`, the final line does not. A reply of about 68,412 bytes was accepted against a 65,536 cap; a 30,000-byte final line was refused. Excess is at most about one recv (4 KB). Fix: add the final line length to `used` and refuse when over. Test: test_m7_the_whole_smtp_reply_including_its_last_line_stays_under_the_cap.

### N4 Minor: hubspot_probe masks the token only by exact match
scripts/hubspot_probe.py:159-172 _why does msg.replace(token, "***"). A server echoing a truncated, upper-cased, percent-encoded or zero-width-interleaved token (or its tail) gets up to 100 characters printed, e.g. `key ending 89abcdef`. n8n_api.py keeps no bodies, which is the safer pattern. Fix: print only category and status, or refuse a message sharing a 6-character run with the token. Test: test_m7_a_server_that_echoes_a_changed_token_does_not_get_it_printed.

### N5 Nit: weaker key reader in the fake model server
demo_only/fake_model_server.py (~line 307) reads --key-file with .decode().strip() (accepts multi-line and Unicode-whitespace keys) instead of read_secret_line. Fake key only; sibling of the old M27 class. Fix: use read_secret_line.

### N6 Nit (inherent): secret files are checked once, re-read later
check_secret_files validates before Start?; the children re-read afterwards. A file changed in between is refused later by the child (fixed-text path) but after real calls may have begun. State it in the README or re-check in the child before the first call (already refused there).

### N7 Note: equivalent-mutant candidates
math.isfinite in the ProviderSettings and HubSpot timeout checks is redundant with the range test (0 < nan <= X is false); in send() it only turns nan into a ValueError instead of the default budget. Mutant C05 covers this; unrun.

## Mutation table
Written, not run: 54 mutants (A01-A15 imap_count, B01-B04 smtp_outbox cap, C01-C10 smtp_provider, D01-D05 regfile, E01-E07 run_real_check/run_live_check, F01-F03 live_claude, G01-G03 crm_hubspot, T01-T05 tls_trust, P01 prior D05, P02 prior D20, C09 prior D11). Likely survivors to check first: A12, A08, A04, A03, B-series, D01-D03, C03, C05, E05, E06, G03. Killed 0, survived 0, unknown 54.

## Verdict
Not clean. N1 is a Major (a bad key reaches the Start? question). The no-round-cap rule means another pass is needed after fixes, and the mutation step must be run on the fixed tree.
