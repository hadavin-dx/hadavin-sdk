# A4 round 9, code/tests/docs lens (egm-implementation-readiness reviewer, fresh, read-only, nothing run; snapshot /home/user/build/snap/A4r9; saved by the cloud session)

ROUND-9 REVIEW, code/tests/docs lens, snapshot /home/user/build/snap/A4r9. Read-only. Nothing was run, so I have not verified that the tests pass or the 800/797/1/2 counts.

VERDICT: no Blocker. Four Majors, in two groups. Three are doc claims that the code or the cited tests do not back. One is a test that cannot fail for the reason it names. The numbers 9/30/25/15/24, the caps 4/8/8/4 (24 workers), the names ModelAnswerLost/CrmUnreachable/ModelTimeout and exit codes 1, 2 and 3 all match the code. Exit code 4 is Major 1.

MAJOR

1. README.md:246 and contract.md:72, start-up step (4), have a stale exit-4 condition.
   - Both say the AI adapter's `timeout_seconds` is "not below the stuck grace minus its margin" (the old 15 s limit).
   - The code (desk.py:276, server.py:972-973) refuses anything above `MODEL_CALL_BUDGET_SECONDS` (9 s). The README at :58 and contract.md:22 say so correctly.
   - contract.md:3 says the contract wins where code and contract disagree, so this is a genuine contract error.
   - Fix: replace the text with "or is above the 9 s model budget".

2. README.md:57 and contract.md:22 overclaim the aging of `model_busy` rows.
   - Both say the give-back "does NOT refresh updated_at, so such rows age into the stalled list". README:57 also says the row "is NOT stamped".
   - The claim SQL (desk.py:146) sets `updated_at=now`, and the first `_touch` in `_after_claim` stamps again. The give-back only skips a third stamp.
   - A row refused in the race path gets a fresh stamp every 5 s. It never ages if the shortage is, for example, 2 abandoned plus 2 busy healthy calls.
   - Only the all-abandoned path (`_closed_kind`, desk.py:1099, no claim made) really keeps the age.
   - `test_busy_give_back_keeps_the_age` (s1k:373) and `test_busy_give_back_race_keeps_age` (s1k:415) take `stamped` after the claim. They pin only "no extra stamp", so they do not support the README sentence.
   - Fix: narrow the wording to "a row whose slots are all held by abandoned calls is not claimed and ages".

3. `test_answer_lost_real_lock_keeps_try` (s1k:692) does not pin its name, and README.md:59 cites it for "the try stays used up".
   - The real lock held by the other connection also blocks the give-back write (`_give_back` goes through `_locked_retry`).
   - Reverting `ModelAnswerLost` to a give-back gives the same result: row `sending`, `auto_attempts` 1, then the reaper puts it back as pending/1/`crash_while_sending`.
   - The real pins are s1h:94 `test_model_stamp_lock_spends_the_try`, which uses `lock_writes_after_answer` and lets the give-back through, and s1j:258 `test_locked_stamp_cannot_ask_for_ever`.
   - Fix: rename the s1k test (it covers the reaper path), or drop it from the README's "try stays used up" citation.

4. README.md:71 and gate.py:29-32 say a drive makes "at most three bounded adapter calls" and the worst pass is "10 + 27 + 18 = 55 s". That is wrong for two paths.
   - After an `OutboxModeMismatch`, `_refresh_outbox` runs two more bounded reads (desk.py:1546). A drive can then be model 9 + crm 9 + send 9 + 18 = 45 s.
   - A leftover `crm_done=2` adds `_refresh_crm`, and a migrated row with no label also adds the model call.
   - The worst case is therefore about 73 s, or 45 s for the drive alone.
   - Related code gap: `validate_model_budget` covers one bounded call plus one stamp write. In the `ambiguous_prior` path, `_send_claimed` (desk.py:1506) makes two serial reads (up to 18 s) before the `send_started` stamp, and `_crm_step` returns early without a stamp. With lock trouble that is 18 + 15 = 33 s, over the 30 s grace. This is a small window, but it breaks the "24 < 25" invariant that the docs present as general.

NIT

5. contract.md:72 (1) lists the `FD_RESERVE_ITEMS` and omits "abandoned adapter workers" (24, constants.py:151). The listed items sum to 26 and the real total is 50 of the 64. README:245 sends the reader there.
6. README.md:266 and config.py:43 describe `send_timeout_seconds` as "wait per network step, also for the CRM call". It is now also the total deadline, `min(value, 9 s)`, for the CRM put, send and reads.
7. README.md:101-104, the mutation check, omits that the `test_mutant_no_claim` stand-in now also forces `exclusive=False` on `_bounded`. The stand-in is correct and still pins the weakened claim:
   - With the real claim switched off, two concurrent blind sends each get 0.5 s of delay.
   - Without the stand-in, the guard would refuse the second send and hide the fault (`test_mutants.py:72-82`).
   - Say so in the README ("two protections removed" is now three switches).
8. README.md:56-57 and contract.md cite `test_hung_calls_are_capped` for "at most 5 asks". That test (s1j:144) uses cap 2. The 5-ask pin is `test_hung_tries_end_in_failed`.
9. README.md:57 says "starts 8 drives at once". The test (s1k:326) starts 8 threads that call `_ask_model` directly.
10. README.md:57 and contract.md:113 say `hung_workers` is "shown" in the portal summary. It is JSON only; nothing in `src/lead_desk/portal` references it.
11. contract.md:199 is garbled.
    - "F6 (...), F8 (...) was FIXED in round 8" leaves F6's status unclear.
    - The F8 "fixed" line is accurate, and README:60 matches it.
    - The header "Not changed in fix 7" now contains a round-8 fix.
    - "this round's assignment" is ambiguous.
12. gate.py:37-39 says the 3-busy-wait result write plus "one more" gives the grace. `SENDING_GRACE_BUSY_WAITS` is 5, so the comment is stale.
13. s1k:147 `"k1a" not in str(rig.outbox.keys())` is vacuous, because keys are lead ids, not "k1a". Use `stuck not in`. `outbox.count == 1` already covers the point.
14. s1j:206 `test_declared_just_over_budget_refused` duplicates s1k:560 `test_declared_above_budget_is_refused`.
15. Unpinned guards:
    - the `_closed_logged` dedupe;
    - `_tagged` cleanup on a non-exclusive call or a failed thread start;
    - the refresh cap of 4 (README:60 claims it; no test);
    - the `crm_busy` give-back from a cap, as opposed to exclusivity.
16. `Config` (config.py:62) accepts NaN for `send_timeout_seconds`, because only `<= 0` is checked. The new `_call_deadline` then waits on NaN, and `int(inf + 25)` in `stuck_grace_seconds` overflows. This predates S1k but is now on the critical path.
17. `test_workers_stay_within_the_cap` (s1k:365) checks `started == 4` immediately after joining the drivers, without polling. On a starved 4-core box, an uncaught worker start could undercount. Use `wait_for`. The pin against a "reserve after start" revert is probabilistic, not certain; reverting the reservation gives a near-certain failure but not a guaranteed one.
18. README:101-104 and the Python version "3.13.18" in README:85 and :113 are unverified by me.

TIMING FLAKES (loaded 4-core machine)

- Medium: `SHORT = 0.2` s (s1k:25) is also the deadline for healthy in-process fakes under the `quick` fixture, plus the model budget in s1j (`SHORT` there too). A 200 ms scheduler stall on a healthy call turns it into a spurious timeout.
  - Exact-sequence assertions would then break: `entered == [lid, lid]` in `test_keyed_send_timeout_same_key`, and the "sent" waits in the reaper tests.
  - Use 0.5 to 1 s; the hung path costs only that much more.
- Low: `test_stop_waits_only_its_timeout` (s1k:528) asserts `< 1.2 s` for a 0.2 s join, and that the reaper is still alive before the 1.5 s deadline. It needs a stall of more than 1 s to fail.
- Low: the abandoned stand-ins wait `release.wait(8)`. A test body stalled for more than 8 s would see its "hung" workers end on their own.
- Others (the real-lock tests, `test_thread_start_failure_is_busy`, the cap tests) are deterministic. The `Barrier` timeouts of 15-20 s are fine.

ONE-BY-ONE ON THE TESTS YOU ASKED ABOUT

- `test_workers_stay_within_the_cap`: pins the exact cap (a `>` instead of `>=` would fail); see nit 17.
- `test_full_model_cap_shows_the_row`: pins the `_closed_kind` check (reverting makes `attempts` 1). It does what it says.
- `test_full_cap_logs_once`: pins the `_busy_logged` dedupe and the error line. Fine.
- `test_thread_start_failure_is_busy`: pins the `RuntimeError` handler and the slot release. Fine.
- `test_blind_retry_waits_for_old_send` and `test_blind_crm_timeout_is_unknown`: pin `exclusive`. Reverting gives `entered == [lid, lid]` or `crm_busy` missing.
- `test_hung_workers_are_counted`: pins the `_abandoned` accounting and the counts/summary keys. Fine.
- `test_stop_waits_only_its_timeout`: pins the `_retiring` tracking.
- `test_late_send_writes_nothing` and `test_late_crm_put_writes_nothing`: structural, since the worker never writes the database. They would pass if the worker did write, unless it altered the row between `before` and `after`.
- `tests/support.py` `lock_writes_after_answer`:
  - Sound on CPython 3.11+. `sys._getframe(2)` is the writing function, because frame 1 is `_GeneratorContextManager.__enter__`; `co_qualname` needs 3.11+.
  - The nested `attempt` and `store` qualnames contain `_touch` and `store`. It raises before the gate, so no gate leak, and the real `_locked_retry` loop runs.
  - Nits: the substring match is permissive (`"store"` would also match any future `*store*` function); it locks every matching write permanently after `answered`, not "the one write" its docstring says; and a typo in `where` fails loudly rather than silently.
- Test-name lengths: every new name in test_loss_path_s1k.py is at most 37 characters (the longest is `test_declared_above_budget_is_refused`), so all are within 39.
- Other checks:
  - Test names cited in README and contract all exist, including `test_label_store_needs_the_claim` (s1i), `test_reaper_needs_age_above_grace` (s1i) and `test_unsent_row_at_cap_fails_visibly` (s1h).
  - Counts are consistent across README:85, :113 and contract.md:3 (797+1+2=800; 26 files, which matches the file listing).
  - `portal_fixtures/summary*.json` carry `hung_workers`.
  - No stale "grace 25", "margin 10/15" or "declared limit 15" remain except as labelled history (README:58, contract.md:22). The "a lock gives the try back" statements in README:59/:71 and contract.md:22/:74/:183 are all qualified with the ModelAnswerLost exception.

NOT READ
- `/home/user/build/snap/A4r9/src/lead_desk/server.py`, except main() lines 960-1015 and greps.
- `src/lead_desk/portal_api.py`, except lines 225-270 and greps for the card wording.
- `src/lead_desk/adapters.py`, `config.py`, `db.py`, `loader.py`, `lockfile.py`, `identity.py`, `hooks.py`: grep hits only.
- `demo_only/*` (FakeCrm, KeyedOutbox, BlindOutbox, RecordedQualifier internals).
- `tests/conftest.py` (the `env` fixture).
- `tests/test_flow.py`, except `retry_twice_body`.
- All other test files, and `tests/portal_fixtures` content (the glob listed the files; the hits for `hung_workers` came from a grep).
- `tests/test_mutants_round2.py` and `tests/test_mutation_guards.py`, which may interact with `_bounded`.
- `docs/n8n-recipe.md`, `SECURITY.md`, `versions.md`, `pyproject.toml`, `scripts/*`, `n8n/*`, the CI workflows.
- Not run or verified: any test, the 800 count, the 1 skipped test, Python 3.13.18.