# R7H-RESULTS (builder, patch round r7h, money and mail path)

## NOT DONE / NOT CHECKED (first)
- runfinal (one file per process, staged git copy) was still running when the box ended: 17 of 32 files seen, all passed (hygiene 24, vendor_hosts 6, nosemgrep_form 114, stall_eviction 36, server_hardening 24, main_reaper 2, load_tools 80, load_driver_facts 5, burst_retry 18, r7d 66, r7f 79, r7_mail_context 68, real_check_dry 79, r7c mail 4+3, cli_refusals 125, crm_hubspot 56, smtp_provider 62). Not seen to finish: live_claude, env_numbers, ca_file_reads, r7_inputs_and_replies, infra, class_names, hubspot_probe, r6_refusals, special_output_files, r7e, r7m_new, config. Lines in runfinal.txt are the truth.
- r7g (60), file_call_guard (11), r7h (49) re-run on a fresh staged copy of the FINAL tree: all passed (fin-*.log).
- Final fail-before run on an r7g copy was NOT redone with the final test file; the earlier one (18 failed, 31 passed, onr7g.log) used the earlier file. The 31 that pass on r7g: thread-site controls, NOT-NEEDED code-point proof, and the M9 order tests.
- M9-02: NOT a code defect. smtp_provider.send reads the password (line 259) before attempts += 1 (268); live_claude (key before ledger.reserve), crm_hubspot._call (key before call counter), imap_count (password before connect), smtp_outbox (no secret file) were checked. r7h adds the missing pin: tests test_order_* in tests/test_r7h_findings.py. They pass on r7g by design; they FAIL on the mutated copies (M9-02: 4 failed, M9-L/H/I: 4 each). The M9-02 pin is inside the final run (r7h file 49 passed).
- M9-22, M9-12 (and M9-03, 08, 18, 19): NOT worked on (time). Looked only: smtp_outbox.send has no empty-send-key refusal visible before _build at ~line 216 (the one I saw at ~225 is in the code path I read; not tested); smtp_provider final reply uses code // 100 != _POSITIVE_DONE (line 351) and login refusal at 335. Lead: start r7i for these.
- Two slips: I typed a device path inline in an experiment script (tool denied; rewritten with Write using socketpairs) and once in a harmless sed. No effect.

## Items
- m1 NEEDED, fixed: imap host isascii; siblings fixed: SMTP from_env (_ascii_host), envnum.split_url (Kelvin host passed a vendor suffix), run_real_check child_environment (upper()). NOT-NEEDED with reason: is_loopback_host, server Host header (latin-1), n8n scheme, http_guard scheme, http_address, casefold dedupe, recipient compare.
- m2 NEEDED, fixed: even share; 8 silent + good at 1.2 s tried all 9; documented in docs/limits.md.
- n1 NEEDED, fixed: LOOKUP_HUNG_MAX = 8, refusal with the fixed text, count recovers; tested.
- Thread sites: desk reaper catches BaseException per pass (tested); _Lingerer: real defect fixed (fd >= 1024 made select raise ValueError, loop spun with no traceback; now poll); http_guard head timer: OSError only, caught (tested).
- (a) gaierror: every look-up failure is now OSError with the one fixed text; r7g test changed (see below).
- (b) burst exit code: rc 0 by contract (load_tools/README, r7f did the same). Added given_up count and a NOTE on stderr; rc 3 stays for nothing-answers or stopped-early. Tests plus mutants.

## Changed tests (stricter, same property)
- test_r7g: gaierror test now asserts OSError type exactly with the fixed text (was pytest.raises(gaierror)).
- test_r7g: total-limit test now len(log)==4 and each slice <= 0.26 (was 3); mutant A03 now killed by the r7h overrun test.
- test_file_call_guard: new row src/lead_desk/server.py select.poll.

## Mutants (restored by sha each): mutants.txt 15/15 killed (H01-H04, S01-S03, A03, K01-K04, T01-T03); mutants2.txt 9/10 killed at first (M9-02, M9-L, M9-H, M9-I, G01-G04, G06); T04 survived (vacuous wait), test fixed, mutants2b.txt T04 killed.

## Numbers
ruff 0.17.1 check passed, format --check 220 files formatted. Suppressions 175/126/8/32/7 unchanged. Patches rebuilt after the last edit: sha256-r7h.txt; apply matrix a-crlf, b-crlf, c-lf rc=0; BYTE-FOR-BYTE-SAME; DELTA-ON-R7G-GIVES-R7H.
