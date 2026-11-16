# L2d report (builder; EGM review: lead runs it)

## What failed, is uncertain or was not done (first)
- NOT done: ORDER 221 item M2 (desk.py label step before the claim). It is a desk patch, outside this task. The fixed checker now
  shows it on saved data: dupmix-30pct, 879 model calls for 840 leads, one lead asked 3 times (+0 s, +1.9 s, +24 s). Not
  proven to be M2; needs the desk patch and a live re-run.
- NOT run: any live campaign (no live desk run). The offline recheck is the only new evidence on saved data.
- Honest correction of the order: B1's headline case (every lead lost) was ALREADY caught by L2c's "lead-count" rule. I ran the
  synthetic book on the L2c checker: it fails (check 2 offender `lead-count`; NULL variant also check 7). What L2c still missed,
  and what is new: a stale book (extra receipts), another run's ids/prefix, no run marker, a phantom lead with the right
  count (found by email now), a `review` verdict on a driver request, accounting intended = logged = receipts.
- M1 was ALREADY done by L2c (`_post` catches every exception; the worker writes a line for every taken item). Added tests
  (3 reply kinds) which pass on the old code, plus one real gap fixed: a failed log write killed the worker thread and left the
  rest of its queue unsent.
- SMTP m2 was ALREADY handled for UnicodeError/ValueError (fuzzed 20,000 random inputs on the L2c code: only SendRefused).
  Real gap fixed: `email.errors.MessageError` (not a ValueError) would have escaped as "maybe sent".
- Ceilings are my choices: model bound 1 when the model answers, +1 slack in kill scenarios, 5+1 = 6 when the model is ever
  down. The old "2 slack" was a guess; the new one-call slack is also a stated choice (a kill can lose one answer).
- Recheck of saved data lacks a run marker (old facts files): the stale-book-by-marker test could not run there; the id-prefix
  and email matching ran and pass.
- mypy: 3 errors, the same 3 as on the L2c tree (check_invariants.py:24 final name, desk_launcher.py:37); none in changed code.
- Another agent's pytest (pid 3576, 3175) was running at the same time; my full run took 344 s under that load.

## Fixes
- check_invariants.py: check 1 = three-way accounting (intended, logged, receipts), `stale-book`, `foreign-id`/`foreign-receipt`
  (facts `id_prefix`), `other-run` (facts `run_id` in every receipt payload). Check 2 = leads matched by email to the
  request ids (`no-lead:`, `foreign-lead:`), `review:` verdicts fail. Check 3 accepts `failed` with a message when
  last_error is ambiguous/crash_while_sending/ambiguous_prior (m6); `unknown` with message and reason was already ok. Check 5
  default ceiling 6 (slack 1). New `read_facts`.
- load_driver.py: `run_id`, message carries `Run <id>.`, facts get `id_prefix`, `run_id`, `distinct_request_ids`,
  `email_domain`; worker survives a failed write.
- campaign.py: `Scenario.model_bound` and `model_bound_for` (per scenario, in the README table), passed to the checker.
- recheck.py: passes facts (prefix defaults to the scenario name) and the per-scenario bound.
- smtp_outbox.py: `_connect` builds the socket itself (socket.create_connection calls getaddrinfo even for an address; no
  resolver call remains, tested by making getaddrinfo/gethostbyname raise), whole remaining budget for one address,
  `_addresses()` splits the budget evenly if there are several, IPv6 zone names refused, MessageError -> SendRefused.
- README-L2.md updated (facts fields, checks 1/2/3/5, generated scenario bound table). This closes L2c's README gap.

## Evidence (raw files in /home/user/build/)
- L2d-failbefore.txt: new test files on /tmp/dpld-camp2 code: 19 failed (names listed; note at the end lists which new tests
  pass on old code and why). Final: two test files 270 passed (22 s).
- L2d-full.log: full suite once, detached: 2 failed, 902 passed, 1 skipped (344 s). The 2 failures are exactly
  test_hygiene.py::test_hygiene_scan_public and ::test_hygiene_wordlist (no git repo / no word list). The 9 failures L2c saw
  in other tests are not present in this run (I did not investigate why).
- ruff check: All checks passed. ruff format --check: 66 files already formatted. mypy: see above.
- Hygiene by grep on added lines: no IP-like literal except the allowed loopback one, no 32+ hex or 40+ token in code/docs;
  my new test names are all under 40 characters (older names of 40+ characters from earlier work remain; they are not mine).
- L2d.diff: 8 files, a/ b/ paths. Apply-check on a fresh copy of /tmp/dpld-camp2: `patch -p1` applies cleanly, every
  patched file is byte-identical to /tmp/dpld-l2d.
- L2d-superseded.md and L2d-recheck/<scenario>.txt|json: recheck of all 23 saved folders: 15 pass clean, 1 passes with a RERUN
  note (model-flaps), 7 fail (dupmix-30pct check 5; model-slow, model-timeout, catcher-slow and their 3 re-runs: checks 2 and
  7, desk never drained). Saved folders only read.

## Files
Changed (in /tmp/dpld-l2d): live_l2/{README-L2.md,campaign.py,check_invariants.py,load_driver.py,recheck.py},
src/lead_desk/smtp_outbox.py, tests/{test_live_l2_tools.py,test_smtp_outbox.py}.
Deliverables: /home/user/build/{L2d.diff,L2d-report.md,L2d-failbefore.txt,L2d-full.log,L2d-superseded.md,L2d-recheck/}.
Untouched: /tmp/dpld-camp2, s3, s4, s5, /tmp/ag, campaign/. I removed my own temp copies. No processes of mine remain.
