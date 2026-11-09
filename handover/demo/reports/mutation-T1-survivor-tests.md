# T1 report: mutation guards (order 219)

File delivered: /tmp/dpld-t1/tests/test_mutation_guards.py (27 test cases, 22 test functions; ruff check and ruff format --check clean; longest function name 38 characters). Diff: /home/user/build/T1.diff (new file only). I did not touch git or any source file (every mutation was restored and diffed, see below).

## What failed / not checked (first)
- No desk bug found; no source change made.
- Pre-existing failures in OTHER test files, identical with my file moved away (3 failed, 8 passed in tests/test_hygiene.py + tests/test_mutants.py):
  - test_hygiene_scan_public: gitleaks binary not on PATH (environment).
  - test_hygiene_wordlist: HYGIENE_WORDLIST not set (environment).
  - test_mutants.py::test_mutant_no_claim: a real stale test. Its stand-in `always_claimed(self, conn_or_none, lead_id)` has no `from_states` parameter, but `Desk._claim` is now called with three arguments, so it raises TypeError (logged "follow-up failed: TypeError") and the expected "emails == 1" message never appears. Not fixed here (order said one new file); it needs a one-line signature change (`from_states=("pending",)`) by whoever owns that file.
- I ran only my new file plus those two files, not the whole suite.
- Test for survivor 4b: the desk answers the race loser with verdict review / internal_unstorable (202), or duplicate (200) if serialised. That is what the code does (an IntegrityError on the lead insert is in `_UNSTORABLE`, desk.py). I asserted exactly that plus one lead per email_key, one follow-up per lead, no open receipts, no 500/503, 30 rounds. This is a behaviour of the index-only path (the code-level lookup is bypassed in the test); in normal running the lookup finds the winner and the loser is a plain duplicate.

## Survivors: killed (raw: /home/user/build/T1-failbefore.txt; all tests that fail on the mutant are listed, first one first)
| id | test (first failing) | first failing line on the mutant |
|---|---|---|
| 4 unique index -> plain | test_email_key_unique_in_sql (also test_email_key_race_only_index) | tests/test_mutation_guards.py:84 DID NOT RAISE IntegrityError |
| 11 schema 128 -> 127 | test_source_ref_bounds_in_sql (also test_source_ref_128_through_desk) | :60 IntegrityError: CHECK ... BETWEEN 1 AND 127 |
| 12 SOURCE_REF_MIN <= -> < | test_source_ref_one_char_and_empty | :150 assert 400 == 201 |
| 13 claim keeps send_started | test_claim_clears_send_started[states0-pending] | :170 "a claim must clear the send mark" |
| 20 requeue age <= -> < | test_requeue_age_boundary_direct (also ..._in_reaper) | :204 ('sending', None) == ('pending', 'crash_while_sending') |
| 21 stalled receipt <= -> < | test_stalled_receipt_age_boundary | :241 assert None == 'new' |
| 26 own-clock future receipts dropped | test_future_receipt_by_own_clock | :258 assert None == 'new' |

Note on #13: the claim for ("pending","failed") on pending and on failed rows is also tested (parametrized, 3 cases); the failed claim restarts auto_attempts at 1.
Method note: a first pass gave a wrong #21 result because Python reused a stale bytecode file between two same-size mutants in one second; I fixed the harness (PYTHONDONTWRITEBYTECODE, delete cached .pyc before and after every run) and re-ran all 7 and all extras. The numbers above are from the corrected run.

## Extra mutants (12 required; 14 recorded and killed): /home/user/build/T1-extra-mutants.txt
None is in /tmp/ag/mutants.py. All 14 KILLED, first failing test and line recorded there:
E1 ambiguous_prior no longer written on an unclear send; E2 claim also takes `sending`; E3 failed-row claim sets auto count 0; E4 crm_done=1 returns False; E5 intent mark written as 0 (not 2) before the put; E6 mark after put written as 2 (not 1); E7 proven-failed put resets mark to 2 (not 0); E8 requeue sets ambiguous_prior without send_started=1; E9 blind requeue sends a never-started row to unknown; E10 requeue with mode unknown also takes maybe-sent rows; E11 _touch ownership `attempts=?` -> `>=`; E12 _defer_pending token `=` -> `>=`; E13 claim no longer adds one attempt; E14 own-clock stall boundary <= -> <.
Harness: /home/user/build/T1-work/mutate.py (applies exact text, asserts it occurs once, runs only the new file, restores from a copy, checks with cmp/diff). Every restore printed `diff rc=0` (source tree identical to before).

## Stability (unmutated tree)
Three runs in a row: `27 passed in 0.53s`, `27 passed in 0.62s`, `27 passed in 0.55s`. No sleeps; explicit test clock; the race uses run_threads (start barrier), 30 rounds with fresh emails.

## Hygiene
Made-up emails at example.test only; the 128-char request id is built with "x" * 128; no secret-like or IP-like literals; no sub-agents; nothing under /tmp/ag touched; all processes I started have ended.
