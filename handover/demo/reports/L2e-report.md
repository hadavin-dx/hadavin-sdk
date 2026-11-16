# L2e report (builder L2e, duplicate-proof-lead-desk, live-proof tools)

EGM review: lead runs it. Work tree: /tmp/dpld-l2e (copy of /tmp/dpld-camp3; the campaign tree was never written to). No commit, no PR, no sub-agent, no live call.

## What failed, is uncertain, or was not checked (first)
* The full pytest run has 2 red tests, both expected: `test_hygiene_scan_public` (no gitleaks binary on this machine; the pattern scan before it passed) and `test_hygiene_wordlist` (private word list not set). Full run: `2 failed, 1013 passed, 1 skipped in 370 s` (/home/user/build/L2e-fullpytest.log). Two small tests (`test_all_failed_book_breaks_scenario_cap`) were added after that run started; the three changed test files were run again afterwards: `349 passed` (tools, new file, smtp).
* mypy: one error, the old one (`check_invariants.py:27 Cannot assign to final name SEND_MAX_ATTEMPTS`). I fixed two new ones I had introduced (a Counter name reuse, an unused ignore, an Optional index).
* Mutation pass: 75 mutants, 72 killed, 3 survive. All three are equivalent (no test can tell the difference), see below. Not a gap I could close by a test.
* No scenario was re-run live (forbidden: the campaign is using the other tree). The new campaign code paths (`run_group`, boot failure, `_run_workers`) are tested with small stand-ins, not with a real 20-scenario campaign. A real campaign run on the new code is NOT done.
* Recheck of run 1: six folders are red (the desk never drained; red in run 1 too), `dupmix-30pct` fails check 5 (35 leads called the model 2 to 3 times under mode `ok`, bound 1; cannot tell a race from a re-ask on that log), five model folders exit 3 (rerun needed). Details: /home/user/build/L2e-recheck.md. Run 1 had stored no bounds, so today's catalogue bounds were used (the BOUNDS line says so).
* Fake-model and `desk.py` were read, not changed. F1 was confirmed by reading desk.py (CRM step is written before the send).
* The check-6 per-scenario ceilings are 0 except `dupmix-30pct` at 0.10: that number is the first campaign's measured 0.0596 plus margin, a regression guard, not a derived limit. Said so in README-L2.md.

## Fixes (each finding: what changed, test that fails on the old code)
Fail-before run: new `tests/test_live_l2_e.py` + new smtp tests copied into a copy of /tmp/dpld-camp3: `60 failed, 173 passed` (/home/user/build/L2e-failbefore.txt). Honest note: the tests that PASS on the old code are the F6 mutation-killers for rules that already existed (foreign receipt, stray mail, CRM twice, extra vs not_leads, wrong recipient case, receipt-number mismatch, no follow-up row, no verdict, review verdict, lead-count, CRM extra, no send time) and the regression guards (clean book passes, parent-alive worker sends, EHLO then HELO 5xx refused, MemoryError not swallowed). Their proof is the mutation pass, not fail-before.
* F1: check 4 now fails `sent-without-crm:<lead>` when a `sent` lead has crm_done != 1; synthetic all-sent, crm_done 0, empty CRM book fails.
* F2: `failed` needs a last_error; `max_failed` is derived from the fault window (`min(leads, ceil(rate x (window s + 1 s per window)))`, arithmetic printed in the scenario table in README-L2.md); leads submitted in a healthy window (3 s after a recovery, 2 s before the next fault) must be `sent`; synthetic all-failed books fail for `catcher-down` (cap 160) and `model-flaps` (cap 170).
* F3: `Expect` (per-scenario evidence, stored in summary.json): model log must cover every lead (empty or result-only log fails), down modes really called, non-200 results for rate_limit/server_error, catcher record with the mode, drop-after-data needs an unknown, no mail inside a down window. `harness_faults` fails a missing or late event (> 1.5 s) and a live event thread.
* F4: leads with more than one call counted (cap 8 in crash scenarios), no arrival after a 200 answer, at most 5 down calls per lead, CLI default bound is 1. On a log with no arrival lines the "asked after an answer" rule is not judged (a race looks the same) and recheck says RERUN.
* F5: facts file stores `intended_list` and `distinct_request_ids`; check 1 compares by identity (`missing-from-log`, `not-intended`) and by distinct count.
* F6: tests listed above; check 6 prints "report only" without a ceiling, and every scenario states one; mutation pass over check_invariants.py (script /home/user/build/L2e-mutate.py restores the file in a `finally`, works on git-free copies; results /home/user/build/L2e-mutation.json, log .log, first two passes kept as -pass1 and -pass2).
* F7: driver pool replaced by `_run_workers` (processes watched; a worker that exits non-zero or passes its deadline is reported and stopped; getppid orphan guard). Tests with a worker that exits and one that hangs.
* F8: `--intended` with a missing facts file exits 2.
* F9: boot failure is recorded as a failed scenario and the campaign continues; `malformed_label` and `slow` under a short client timeout count as model down; crash scenarios use a 15 s retry window (validated, `--retry-window`); README-L2.md has the model log format, book columns, drain marker, intended_list, scenario table (pinned by a test); catcher records a malformed charset (`undecodable`) instead of losing it; recipient compare ignores case; recheck stores/uses the run's bounds (summary.json `bounds`; fallback to the catalogue with a printed BOUNDS line).
* SMTP (`src/lead_desk/smtp_outbox.py`, tests in tests/test_smtp_outbox.py, rules in the module docstring): `_ADDRESS` refuses `, ; " ( )`; a bare 3-digit reply is accepted; EHLO 5xx falls back to HELO (a HELO refusal is SendRefused); NaN or infinite timeout is a ValueError (settings and send); an unexpected exception maps to SendAmbiguous once the text began and SendUnreachable before (also in connect); MemoryError is never caught.

## Mutation survivors (3 of 75, all equivalent)
* `c2 drop sum` and `c2 drop rows`: `total == len(leads)` and `len(followups) == len(leads)` say the same thing while the schema's CHECK limits states and a foreign key ties follow-ups to leads. Kept both (one reads as "states add up", the other as "one row per lead").
* `c4 drop not_leads`: a CRM row for a non-lead is always also an `extra` row, so the pass/fail result is the same; the count stays in the detail line.

## Gates
`ruff check` clean, `ruff format --check` clean (68 files), hygiene pattern scan passes, new test names at most 39 characters.

## Files changed
live_l2/{check_invariants,campaign,load_driver,recheck,catcher}.py, live_l2/README-L2.md, src/lead_desk/smtp_outbox.py, tests/test_live_l2_tools.py (adapted), tests/test_smtp_outbox.py (new tests), tests/test_live_l2_e.py (new).
Deliverables in /home/user/build: L2e.diff (apply-check on a fresh copy of /tmp/dpld-camp3: applies, result identical to /tmp/dpld-l2e), L2e-failbefore.txt, L2e-recheck.md, L2e-mutation.json/.log, L2e-mutate.py, L2e-fullpytest.log, L2e-checkpoint.md.
