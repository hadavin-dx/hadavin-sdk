# Mail-path mutant pass 11 on patch r7m (mutants only; EGM goldfish, fallback mode)

Verdict: **NOT CLEAN**. 14 mutants run on the big set: 12 REAL GAPS, 2 KILLED; M9-58 argued EQUIVALENT without a run. 12 rows of the order were NOT run (list first below). Nothing applied, nothing pushed, no gap sent to any builder.

## What I did NOT run or did not check (first)
- Not run on the big set: M9-56, M9-74, M9-75, M9-78, M9-79, M9-82, M10-J02, M10-J06, M10-J09, M10-J12, M10-J13. M9-58 was not run (argued only, below). The 60-minute box and ~9 minutes per surviving mutant (machine busy with other runs) allowed 14 mutants on 2 lanes.
- I did NOT do the separate "narrow-set re-check first" step. Deviation: I ran every row straight on the BIG set (22 files of out/MAIL7/setC.txt + tests/test_r7d..r7l_findings.py incl. r7k and r7l + the group files of the mutant's file, 900 s, `-x`). The big set contains the narrow set, so a narrow-set kill is also a big-set kill; a survivor here is a survivor on both. The first-failing test shown is therefore from the big set.
- tls group: no clean run, no mutants (not in this order).
- The three socket-file tests are still deselected (same as pass 10, sandbox cannot make that socket); the old known-red f1 test is NOT deselected and was green.
- Equivalence of M9-58 rests on a probe plus reading, not on a test run.

## Clean run first (on r7m, tree-M11c)
Union of the big set and all six group files, no `-x`, in a network namespace, loopback only: **2105 passed, 1 skipped, 3 deselected (socket), rc 0, 570 s**. test_r7f_findings f1 passed. No red clean group, so no STOP. Raw: out/M11/cleanA.out and clean-X.log.

## Counts
Run on the big set: 14 (M9-43, 54, 55, 57, 70, 71, 73, 76, 77, 80, 81, 13, 17, 25). KILLED 2 (M9-76, M9-80). SURVIVED 12 = 12 REAL GAPS. M9-58 was not run (argued equivalent only). 11 other rows not run.

## REAL GAPS (mutant survives the big set; each is for the r7n test-first builder)
Order: money and secret first.
| id | file:line | mutation | killing test in words | big-set evidence |
|---|---|---|---|---|
| M9-43 MONEY | src/lead_desk/live_claude.py:512 | worst case counted from the question text only, not the whole request body | For one `qualify` call, capture the amount handed to `ledger.reserve` (or the ledger line) and assert it equals `worst_case_usd(settings, len(exact request body bytes sent))`. The existing test (test_live_claude.py:93) only says the reserve is bigger than the settled cost. | rc 0, 494 s, raw-M9-43.txt |
| M9-81 SECRET | scripts/run_real_check.py:304 | `scrub` replaces the shorter values first | `scrub("x abcdEFGH1234 y", {"A":"abcd","B":"abcdEFGH1234"})` must be `"x <value> y"` (not `<value>EFGH1234`); same with the dict order swapped. No test calls this `scrub` at all (the two test files that mention `scrub(` are other scrubbers). | rc 0, 574 s |
| M9-73 SECRET | scripts/run_real_check.py:1046 | refusal line prints `scrub(str(e))` for every error class, not only ValueError | Make a setting reader raise `OSError` whose text holds a path/value (key file that cannot be opened): the printed line must be the fixed "refused: the config or a setting cannot be used (see scripts/real-run.env.example)" and must not contain the OSError text. | rc 0, 564 s |
| M9-55 | src/lead_desk/crm_hubspot.py:194 | DESK_HUBSPOT_ALLOW_ANY_BASE_URL on for any non-empty text | `from_env` with "no", "0", "false", "y", "" keeps `allow_any_base_url` False and an https non-vendor URL is refused; only "yes" (any case, trimmed) turns it on. The live twin (test_live_claude.py:254 tries several words) is killed; the HubSpot one has no such test. The key could go to a non-vendor host on a mistyped word. | rc 0, 491 s |
| M9-57 | src/lead_desk/crm_hubspot.py:402 | a 408 reply counts as a plain refusal (CrmRefused = "nothing stored") | Fake HubSpot answers 408 to `put` and to `set_fields`: the error must be CrmError with `nothing_stored` False (unclear), not CrmRefused; 400 and 404 stay refusals with `nothing_stored` True. A 408 does not prove nothing was stored, so the desk could treat a stored row as not stored. | rc 0, 518 s |
| M9-54 | src/lead_desk/crm_hubspot.py:394 | contact path uses `quote(email)` (slash kept) instead of `safe=''` | `set_fields("L1","a/b@x.example",...)` against the loopback fake: the path must be `/crm/v3/objects/contacts/a%2Fb%40x.example?idProperty=email` (one segment); also `../x@y.example`. An address with `/` adds path parts to the HubSpot URL. | rc 0, 524 s |
| M9-70 | scripts/run_real_check.py:1055 | banner "worst case mails" not multiplied by the desk processes | Drive `_run` with dry fakes, known `max_sends` (3): stdout must hold "worst case mails: 6". Today only the words "worst case" are asserted (test_r7d_findings.py:122), never a number. | rc 0, 476 s |
| M9-71 | scripts/run_real_check.py:1052 | banner HubSpot calls not multiplied by the desk processes | Same drive with `max_calls` 7 and read cap 5: "worst case HubSpot calls: 14 by the desk + 5 read-back = 19". | rc 0, 597 s |
| M9-77 | scripts/run_real_check.py:545 | `logins >= IMAP_LOGINS_MAX` becomes `>`: one mailbox login too many | Reader against a loopback fake mailbox that never holds the sent mail, with a far time limit: logins per mailbox must equal exactly the banner figure IMAP_LOGINS_MAX + POLL_EXTRA_LOGINS (assert the sum of the two constants, not a literal). | rc 0, 534 s |
| M9-17 | src/lead_desk/smtp_provider.py:257 | provider `send` no longer refuses a non-ASCII recipient | `provider.send(to="é@x.example")` and a full-width address raise SendRefused("recipient is not a plain address") before the password read, the cap count or any socket. The outbox twin (test_odd_recipients_refused_early) is killed; the provider has none. Note: `to` is only checked, the real recipient is the test inbox, so no mail goes to a lead. | rc 0, 425 s |
| M9-25 | src/lead_desk/smtp_outbox.py:149 | a bare 3-character reply line need not be digits | Fake server answers `abc`, `25`, `2x0` (CRLF) to the greeting or EHLO: the send raises the fixed "unreadable reply" error type, never a raw ValueError (`int(b"abc")`), and its text holds no server bytes. | rc 0, 522 s |
| M9-13 (low) | src/lead_desk/smtp_provider.py:126 | provider timeout 0 allowed | settings with timeout_seconds 0 (and from env) are refused; 0.001 is accepted. Twin test_smtp_outbox::test_settings_from_env_and_checks kills the outbox copy. | rc 0, 527 s |


## KILLED
- M9-80 (mask_result lists not walked): tests/test_real_check_dry.py::test_addresses_are_masked_in_a_failure_table (162 s).
- M9-76 (smtp password pre-check not in spaced mode): tests/test_r7f_findings.py::test_f3_good_secret_files_pass_and_a_spaced_password_is_allowed (372 s).

## EQUIVALENT (written argument; not run)
- M9-58 (`_once`: the "no time left" check removed, crm_hubspot.py:269). With `left <= 0` the mutant still starts the worker, but a negative timeout makes `http.client` raise ValueError before any connect, and exactly 0 gives BlockingIOError after at most a bare TCP connect with zero HTTP bytes (probe out/M11/scratch/probe58.py, both cases). The caller then joins with a non-positive wait, sees an empty box and raises CrmError("TimeoutError"), the same class and `nothing_stored` False as the original. Differences left: a stray daemon thread and, in a race, the text "ValueError" instead of "TimeoutError". No bytes reach HubSpot, no counter differs (the call is counted before `_once`). I call it equivalent for outcome, with that race as the honest residue; if you want it pinned, one test: deadline already past -> CrmError("TimeoutError"), server sees no request.

## Not run, with my reading (opinion, not verdict)
M9-56 (user name part of the base URL not refused; password part still is; host unchanged, so low). M9-79 (live worst case not doubled for the crash restart; likely same class as M9-70/71: banner numbers unpinned). M9-74, 75, 78, 82, J02, J06 (a plain bad-JSON text is relabelled "nested too deeply" when read by direct loaders; regfile wraps it again so only direct callers see it), J09 (BOM accepted), J12, J13: unjudged.

## Housekeeping
Trees: tree-M11c (lane A, clean + mutants), tree-M11d (lane B). After the last mutant `diff -rq -x __pycache__ tree-R7M tree-M11c` and `tree-M11d`: empty (restored by sha after every mutant, all "restored-ok" in results-LA.tsv / results-LB.tsv). tree-R7M was only read. Process slips: (1) I started lane B mutants while the clean ran (speculative; the clean came back green so the results stand). (2) I stopped the first lane drivers (bash only, pids 25452 31386) to reorder the queue; their running mutant children finished and restored normally. (3) A checkpoint sleep helper (no tests) ran detached; it ends by itself. Own scratch: /home/user/build/rr6/out/M11 (checkpoint.md, mut11.py, specs.json, results-L*.tsv, raw-*.txt). At the end no runner or lane script of mine is left (checked with ps).
