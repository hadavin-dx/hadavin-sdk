# S1e report: AI step only after the claim (desk.py)

EGM review: lead runs it. I did not commit or open a PR.

## What failed / is uncertain (first)
- Full pytest (detached, /home/user/build/S1e-full.log): 3 failed, 634 passed, 1 skipped in 340 s. Two failures are the expected
  test_hygiene ones (tools missing: test_hygiene_scan_public, test_hygiene_wordlist). The third, tests/test_mutants.py::test_mutant_no_claim,
  is a FLAKY test that already exists. I ran it 25 times on the original A4r3 (3 failures) and 25 times on my copy (3 failures),
  so it is not caused by this change. It is a timing race in the two-concurrent-Retry mutant check (retry_twice_body). I did NOT fix it
  (outside this brief; needs its own look). Next step: lead decides whether a fixer takes it.
- Test (c) (model raises) fails on the old code ONLY on the claim-count assertion (`attempts`), not on the try count or last_error:
  those were already right before. So (c) mostly pins the kept behaviour; it does not by itself prove a bug.
- Not checked: no real model, no live reaper thread (reap_once called directly with the desk clock), no Windows run.

## Change (src/lead_desk/desk.py, one hunk in `_run_followup` plus the `run_followup` docstring)
- Removed the pre-claim `self._label_step(lead_id)` call and its `_defer_pending(... internal:<class>)` handler. The model step now runs only in
  `_after_claim`, after the claim and the `_touch`. One claimed row = one model call; the reaper only drives `pending` rows, a claimed row is `sending`.
- `state0` no longer reads auto_attempts (it was only used for the removed `_defer_pending` token).
- `_defer_pending` is now unused in src (still called by tests test_m5_stale_defer_changes_nothing, test_defer_pending_counts_one_try); I left it to keep the hunk small.
  Decision for the lead: delete it together with those two tests, or keep.

## Documented behaviour check (contract.md, README.md, CONTRACT-DELTA.md)
- A failing model step used to give: auto_attempts+1, row `pending`, last_error `internal:<class>`, `failed` at the cap (5 tries).
  Now (via `_after_claim` -> `_abort_unsent` -> `_record_send_result(_pending_or_failed)`): the claim adds the try, the row goes back to `pending` with
  `internal:<class>`, `failed` at 5. Same effect. Test (c) checks all five tries.
- One difference: `attempts` (claim count) now also counts these tries (it stayed 0 before). CONTRACT-DELTA already says "`attempts` counts the tries", so this matches the text.
- A locked database in the model step: now the try is given back (existing documented behaviour, CONTRACT-DELTA line 79); before, a lock pre-claim left the row untouched. Same effect.
- contract.md line 22 rule (4) said the AI step "can run twice when two requests drive the same new lead": no longer true, rewritten. CONTRACT-DELTA.md has a new "Round S1e" entry.
  README.md has no statement that needed change (grepped "twice", "AI step", "label").

## Siblings
Every `_label_step` caller: `_after_claim` (after the claim, ok) and `_crm_step` (only after the claim, ok). The reaper (`reap_once`) and the start-up sweep only call `run_followup`.
Retry (`retry`) claims first, then `_after_claim`. No other model call or slow external call runs on a `pending` row before a claim.

## Tests (tests/test_ai_after_claim.py, names under 39 chars, no IP-like or long literals)
- test_reaper_does_not_ask_model_again: slow model (3 s hold), drive thread, clock advanced past the grace, reap_once: calls == 1.
- test_two_drives_ask_model_once: two concurrent run_followup: calls == 1.
- test_model_error_is_one_try_each: raising model, 5 tries, each exactly one call, pending with internal:RuntimeError, failed at cap, then not driven again.
- Old code (A4r3) + new tests: 3 failed (calls 2 == 1 twice; attempts 0 != 1). Yours: 3 passed. Raw: /home/user/build/S1e-failbefore.txt.

## Gates
ruff check src tests: All checks passed. ruff format --check: 37 files already formatted. mypy --strict desk.py: no issues.

## Files
- /home/user/build/S1e.diff (diff -ruN, a/ b/, caches excluded; 4 files: desk.py, contract.md, CONTRACT-DELTA.md, tests/test_ai_after_claim.py)
- apply-check: `patch -p1 --dry-run` on a fresh copy of A4r3: all four files OK.
- /home/user/build/S1e-failbefore.txt, /home/user/build/S1e-full.log
- Work tree: /tmp/dpld-s5 (old-code comparison copy: /tmp/dpld-s5-old)
