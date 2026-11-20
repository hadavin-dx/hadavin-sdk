# ESCALATIONS of core-b (newest on top)

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
