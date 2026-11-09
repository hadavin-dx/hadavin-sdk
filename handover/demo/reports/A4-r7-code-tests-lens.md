# A4 round 7, code/tests/docs lens (egm-implementation-readiness reviewer, fresh, read-only, nothing run; snapshot /home/user/build/snap/A4r7; saved by the cloud session)
Verdict: no Blocker, no Major. Docs match code on budget (9/10, grace 25, adapter limit 15 refused/14 accepted), strict reaper boundary, exit 4 only for DeskSettingRefused, down CRM with crm_done=2 -> SendUnreachable/pending. All 8 S1i tests exist, names <= 39 chars, each pins its line (two gaps below). 24 test files confirmed; 742 count depends on parametrisation (467 defs), not verified.
Nits:
1 desk.py:957-958 `if not stored[1]: return None` not pinned (UPDATE guard gives same end state; only log differs).
2 test_loss_path_s1i.py:43-44 does not catch revert of `<` in _requeue_sending (desk.py:426); test_requeue_age_boundary_direct covers it.
3 test_mutation_guards.py:200-201 docstring wording wrong ("exactly send timeout + grace old"; "tie ... just under the grace").
4 README:71 "failed after database stayed locked five times" only true if the give-back write also stays locked (README:60 says lock after claim gives the try back).
5 README:59 and :246 "not with an exit code" vs contract.md:22 / server.py:975 "exit code 1": align.
6 README:116-117 old "35 of 37 test cases" line next to 742.
7 desk.py:235-239 declared timeout_seconds NaN/zero/negative passes the check (nan >= 15 is False).
8 desk.py:582 done["requeued"] counts rows seen, not changed.
9 Duplicate coverage with s1g/s1h tests; test_loss_path_s1i.py:57 hard-codes 20; test_exit_steps_run_when_one_raises leaves a daemon reaper thread.
Not read: gate.py beyond constants, adapters/config/contract/schema/db/portal_api/loader/identity/lockfile, tests/support.py, conftest, docs/scripts/n8n, other test files.
