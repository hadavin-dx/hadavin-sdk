# L2c report (builder; no review verdict)

## What failed or is uncertain (first)
- NOT run: a real campaign re-run with the new harness, the mutation runs, the git-based hygiene tests (tree is not a git repo, HYGIENE_WORDLIST unset), and the campaign.main-level wiring of driver_exit (covered only through the pure `harness_faults`). 
- Full suite (new tree): 9 failed, 814 passed, 1 skipped. The SAME 9 fail on the old tree (581 passed there, the two touched test files deselected): test_flow::test_failed_retry, test_retry_twice_concurrent, test_hardening_cloud_b::test_f14_lock_file_unopenable, 4 in test_hygiene (no git repo / no wordlist), test_infra::test_demo_adapters, test_mutants::test_mutant_no_claim. I did not diagnose them; not caused by L2c (they fail before it). Per the fix-not-defer rule this is a gap: the lead should assign them.
- I DISAGREE with the reviewer on one item: a hang-up right after the 354 reply stays SendAmbiguous (not Unreachable). The text went out; nothing tells whether the server kept it; Unreachable lets the blind desk retry and may send a second email. A test pins Ambiguous. Lead decides.
- Hostnames are now refused: SmtpSettings.host must be an IP literal (so no resolve-then-connect fallthrough, bounded by one budget). "localhost" and "[::1]" raise ValueError. I did not find anything in the allowed files relying on a hostname, but I did not check desk.py/server.py config defaults beyond the tests passing.
- Ceilings are my choices: crash-* max_unknown = DRIVE_MAX (8); model bound = SEND_MAX_ATTEMPTS + 2 = 7 (the +2 is a stated guess); catcher-drop-after-data and catcher-slow max_unknown = none.
- Offline recheck of the saved campaign: 16 of 20 pass; 3 FAIL on the new drain rule (catcher-slow, model-slow, model-timeout: drain marker null, many leads still pending) and model-flaps needs a rerun. I did not investigate whether the desk was stuck or just slow. See L2c-rerun-offline.md.

## Fail-before (L2c-failbefore.txt)
New tests run on the OLD files: 233 collected, 116 failed, 117 passed. 177 test ids are new: 103 fail on old; 74 pass on old (pins of behaviour that was already right, e.g. the 108-case line-splitter matrix mostly, and E). 13 old tests fail on old only because their fixtures use the new API. New tree: 234 passed (final run, 3 files).

## Fixes (sections A-D, F)
- smtp_outbox.py: header-breaker check (CR, LF, all control chars, 0x7f-0x9f, U+2028/9, splitlines) on send_key, to, subject -> SendRefused before the network; ASCII-only mail_from; IP-literal host; budget exhausted before the text -> Unreachable (nothing sent), after the text started -> Ambiguous; 5xx to DATA -> Refused; non-ASCII replies handled.
- check_invariants.py: checks 1-3 and 5-7 tightened (empty/short request log fails; NULL-outcome receipts, ghost "new" verdicts and lead-count mismatch fail; per-recipient duplicate count; every unknown/failed needs a fitting last_error and stays under the scenario ceiling; model calls counted from `arrival` lines, default bound 7; null drain marker, open work and a timed-out drain fail); new CLI flags --facts/--intended/--max-unknown/--max-failed; facts file required (exit 2 if missing).
- fake_model.py: arrival line at call start, `event` field on results.
- load_driver.py: any exception in a post is caught and logged; every taken item is logged (finally); dupmix cannot exceed total-1 repeats; pool/part-file errors reported; exit 1 if logged != intended.
- campaign.py: per-scenario ceilings, catcher-slow made able to cause ambiguity (slow 7 s vs 2 s timeout), supervisor joined before stopping procs, no restart on non-137 exit, desk exit code 2 at start raises, `harness_faults()` into the summary and the worst-case verdict, max_lag_s and send_spread_s recorded (not asserted).
- recheck.py (new): offline rerun of the 7 checks plus run faults; exit 0/1/2/3.
- Finding E: identity.check_payload already rejects control characters (Cc, and Zl/Zp via has_invisible_format) in `name`; pin tests added, they pass on old and new. No code change.

## Tests added
tests/test_live_l2_tools.py (planted faults for every check change, driver, campaign faults, supervisor, recheck, E pins) and tests/test_smtp_outbox.py (data_554, hangup_354, non-ASCII greeting/final, budget gone after 354, 108-case splitter matrix, IP-literal host, ASCII from). Names are at most 39 chars (hygiene pattern).

## Gate evidence
ruff check, ruff format --check, mypy smtp_outbox.py: all clean. Three-file run: 234 passed in 17.33 s. Hygiene patterns checked by grep against the old tree: identical.

## Files
/home/user/build/L2c.diff (8 files, a/ b/ paths, `patch -p1` applies cleanly to a copy of /tmp/dpld-camp and the result equals /tmp/dpld-l2c for those files), L2c-failbefore.txt, L2c-final-run.txt, L2c-rerun-offline.md, L2c-checkpoint.md, /tmp/l2c-recheck-all.log, /tmp/l2c-full.log, /tmp/l2c-full-old.log. live_l2/README-L2.md NOT updated (still describes bound 3 and old log formats): a leftover gap.
No processes of mine left running; /tmp/dpld-camp and /tmp/ag untouched.
