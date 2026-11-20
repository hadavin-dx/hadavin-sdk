# ESCALATIONS of core-b (newest on top)

## E5 (2026-11-20 06:40 UTC) Step B: a hostile re-read found 1 Blocker and 5 Majors in the BUILT code; B is at its 3-try cap, so they go to the lead
- Item: step B code (commits 80a07ce, 6662afe, 358361e). Report with file and line, how to reproduce and the smallest fix for each: tickets/ABC-hostile-review-1.md. Nothing was run by the reviewer; several rest on PostgreSQL behaviour marked UNVERIFIED.
- Blocker 1 and Major 3: the who-else-can-clear check (already with the lead, ORDER 015): it refuses healthy set-ups on managed databases and shared servers, and a plain migrate with no role named skips it.
- Major 2: the runtime role may be able to change its OWN default search path (ALTER ROLE ... SET search_path), after which new processes read a decoy schema it owns and the stop reads OFF. Tests always pin the path in the connection string, so none sees it.
- Major 4: nothing stops reset_credential_ref from naming a secret the runtime reads (a tool secret, a source token); the runtime would then read the reset login at start.
- Major 5: when a reset finds the switch still ON, the command says "Run limits reset again", which steers an operator to erase a stop a colleague has just set.
- Major 6: on PostgreSQL 17 the MAINTAIN right may let the runtime lock the stop table and block every stop; the store connection has no lock timeout.
- Nits 11 to 16 in the report.
- What I did: nothing in step B code. Ticket B has an addendum with the built behaviour; docs unchanged.
- What I recommend the lead does first: 2 and 5 (both change what an operator can rely on), then 4, then 6 on the PostgreSQL 17 run.

## E4 (2026-11-20 06:20 UTC) Step B: the who-else-can-clear check reads every role of the database SERVER; step B has used its 3 fix rounds, so I stop and hand it to the lead
- Item: step B, check who_else_can_clear in src/hadavin_sdk/store/migrate.py (fix round 3, commit 358361e). Tries used: 3 of 3 (first build, fix 2, fix 3). I do not start a fourth.
- What fails: when the stop-state tests run in parallel (pytest -n 3) or two sessions share one PostgreSQL server, an unrelated migrate is refused with "roles other than the reset role could clear a stop ...: sb_mo_453d4178f4" (also sb_wa_...). Those are roles ANOTHER test created at that moment: a member of the owner role, and a member of pg_write_all_data. Run alone, all 176 stop-state tests pass (1 pin fixed). In parallel: 2 failed and 1 to 2 errors, different tests each time. Raw: evidence/landed-tests-run-1.txt; the same cause explains the unexplained error in batch run 2.
- Cause as I read it: the check lists every role in the server that is a member of a role holding the right, and the holders include the OWNER of the tables. On a test server the owner is the superuser login postgres, so any role that any other test makes a member of it is listed. In production the same happens on a shared server: a role of another application that is a member of the owner role refuses this application's migrate.
- What I think the fix is (NOT built): the owner and superusers are outside the guarantee, so a role whose only path to the right is membership in the owner role should be excluded like the owner itself (one clause: NOT pg_has_role(role, owner, 'MEMBER')), or the tests that create such roles run in one xdist group. The first changes what the check promises (a member of the owner is no longer refused; the existing owner-membership check of effective_problems still refuses the NAMED roles).
- Not tried: any change. Branch cloud/core-b, head f390b7d.
- Risk for the lead's batch run: the stop-state role tests can fail at random when run with -n above 1 or beside core-a's role tests on one server. Run tests/test_stop_state_roles.py with -n 1 on its own server until this is decided.

## E3 (2026-11-20 06:22 UTC) Ticket F-install: review round 1 NOT clean (4 Blockers, 19 Majors); five answers need the lead before GO BUILD F-install
- Item: T3, ticket F-install (tickets/F-install.md section RESOLUTION V1 to V12; report tickets/F-install-review-1.md). One round allowed and used; the answers are not re-reviewed.
- LEAD, OK or CHANGE on each: (1) a route name the registry does not hold is priced at the largest worst case over all configured routes instead of refused (keeps the judge test doubles working; production configs cannot have such a name); (2) the in-memory Budget meter refuses with a SIXTH reason "usd_cap" (interface (ii) lists five); (3) evals without --max-usd: in demo the cap is the agent's daily budget, in pilot and prod it is refused; (4) the gate gets audit=None on the eval AND replay command lines (the lead draft sent replay's gate rows to the replay audit sink, which breaks pinned tests and the sink's intent-only rule); (5) injection_check re-raises a meter or gate refusal instead of turning it into an injection flag.
- Behaviour change the owner should know (V5): after the install, a provider error that is not marked as refused before any response keeps the call's worst case booked for at least an hour. A wrong API key or throttling can use up a small daily budget without real spend. ORDER 013's mark removes the certain cases only.
- Dependency: core-c's gate and runmap.enforce_map are marked work in progress on its branch; the lead names the commit in the GO.
- Not tried: a second review round (not ordered).

## E2 (2026-11-20 05:44 UTC) Ticket F-store: review round 1 was NOT clean; resolved in text; no round 2 by order
- Item: T3, ticket F-store (tickets/F-store.md, review tickets/F-store-review-1.md). Tries: 1 review round of 1 allowed.
- Result: 2 Blockers, 19 Majors, 19 Nits from two reviewers. Every Blocker and Major has a text answer in the ticket (section RESOLUTION, R1 to R14). No fresh reviewer has read those answers.
- Three answers change the lead's draft design; the lead must say OK or CHANGE before GO BUILD F: (1) settle_spend returns (row, applied), so a repeated settle writes no second audit row; (2) an expired reservation is always claimed by its first settle, its day and month counters only move upward, and the real cost goes to the run's cost; (3) the expiry age is the larger of 3600 seconds and the existing stuck-run age (max_steps x call_timeout_s x max_attempts + 60), not a bare constant.
- Also for the lead: per-run cost is added by the store inside settle (the two lead drafts differed); an unknown reservation id raises NotFound from both meters (F-install said no-op for Budget).
- Not tried: a second review round (forbidden by ORDER 004 item 3).
- Cross-lane: core-c ESCALATION E2 (the strict mask check would refuse normal runs) is open with the lead and changes ticket F-install; F-install has NOT had its review round yet for that reason and because EGM stages run one at a time.

## E1 (2026-11-20 05:20 UTC / 10:50 IST) Session cron for the one-minute board was refused
- Item: ORDER 003 item 1 (CronCreate with schedule "* * * * *").
- Attempts: 2 (04:5x UTC reason "Destructive or Unwanted Actions"; 05:22 UTC, after the owner typed GO in the session, reason "Undermining Oversight"). Not tried a third time.
- First attempt: The call was denied by the session's permission check ("Destructive or Unwanted Actions"). No raw log file exists; the denial is a tool result in the session.
- Not retried, not worked around (ORDER 003 item 4).
- What I do instead: the fallback written in ORDER 003 item 1: a board at the end of every tool batch through handover/core-b/tools/board.sh. Effect: boards will be more than 1 minute apart whenever one tool batch (for example a long read or a reviewer round) runs longer than that, and no board is written while the session sits idle waiting for an agent.
- Needed from the owner: allow the cron in this cloud session, or accept the fallback rhythm.
