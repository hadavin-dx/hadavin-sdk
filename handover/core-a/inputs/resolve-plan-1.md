# Resolution of plan review round 1 (lead, 2026-11-20). Reports: review-plan-1-zoom-out.md, -readiness.md, -design.md, -codebase.md. Result: plan-v2.md
Totals: 18 Blockers, 41 Majors, 19 Nits across four `egm:*` reviewers (model fable). All ACCEPTED unless listed under CONTEST. No finding was dismissed.

| Finding | Decision | Where in plan-v2 |
|---|---|---|
| Zoom-out B1, design tiering, M3-M5, M7-M9, M11: scope too wide, no cut line | ACCEPT: tier 1 = nine guarantee items; everything else tier 2 with ledger rows; no deferral lifted | s.1 default 1, s.3, s.4 |
| Zoom-out B2, design D5.2, D12: Postgres-only guarantees | ACCEPT: NOT RUN = not done, not merged; 50 separate connections | s.6 phase 3, s.8 |
| Zoom-out B3, readiness B6, design D16-D17: single run then fixes | ACCEPT: one campaign + one confirming run on the final tree; fix loop written; cut rule | s.1 default 4, s.6 phases 3-4 |
| Zoom-out B4, codebase B2: audit A-01 unowned | ACCEPT: tier-1 item 4 | s.3 |
| Codebase B1, zoom-out B4, design D12: no live executor | ACCEPT with a default: writes done by the client's tool this round, executor stays off, AK-G15 tier 2 | s.1 default 3, s.4 |
| Codebase B3, readiness M3, design D4: migration numbers, CHANGELOG | ACCEPT: CHANGELOG fix in item 1; numbers only at integration; no durable DB | s.3 item 1, s.5 |
| Design D1, D2, readiness M1, M2: theme lanes, hot files, stubs | ACCEPT: SPINE / TEXT / DOOR with file ownership, patch requests, interface tickets first, stub must pass the contract test | s.5, s.6 phase 1 |
| Design D3, readiness B2, B5: integration and CI path | ACCEPT: integration branch is the test vehicle, tagged in dependency order; sequential ready PRs; tree-hash equality; handover branches never merged; code on wip/cloud-* branches | s.5, s.6 phases 3 and 5 |
| Readiness B1: inputs unreachable in the cloud | ACCEPT: allowlisted inputs folder | s.5 |
| Readiness B3, M4, M10: bases, SHAs, head choices | ACCEPT in part: base = origin/main 51c9fc4fb; PR branches read-only inputs; head choices made in tickets from baseline evidence with lead verdict (the baselines are the Phase 0 work now running) | s.5 |
| Readiness B4, M7: where Phase 3 runs, runner separation | ACCEPT: laptop, runner spawned by the lead on a clean checkout; capability probe in ORDER 002 Q1 | s.6 phase 3 |
| Design D5, D7: money and door invariants | ACCEPT: tickets must carry them as numbered invariants; door = one private endpoint reusing hmac_v0 | s.3 items 2 and 7, s.6 phase 1 |
| Design D8, D9, D13, D15, D10, D11; zoom-out M12 | ACCEPT: WSGI host shape; single-dependency notes; RLS traps recorded for tier 2 with tenant in the ledger key now; credential scope stated as UNVERIFIED accepted risk; scanner fallback; model exception | s.1 default 5, s.3, s.5, s.6 phase 5 |
| Codebase M1, M3-M9, zoom-out M1, M6: reuse existing code | ACCEPT: s.2 lists what exists; gate specified as LLM Protocol wrapper; one meter; text-safety, bounded call, time window, effect-once delta moved to tier 2 | s.2, s.3, s.4 |
| Readiness M5, M8, M11, nits | ACCEPT: exit artifact and gate per phase; stall rule; ticket fields; builders per session; trailer | s.5, s.6 |
| Design D14: lead holds requester, executor and approver roles in the build | ACCEPT: wiring reviewed by a reviewer not briefed on the answer; owner's explicit yes for money, door and identity PRs | s.6 phases 4-5 |

## CONTEST
- Zoom-out N1/N2 (no outline at all for Make, Activepieces, Presidio): CONTESTED with the design reviewer: the no-single-dependency rule requires one alternative outlined with its trigger. Decision: half-page outlines, no code.
- Zoom-out M2 (cut the door to a ledger call): partly contested with the design reviewer: a ledger API that n8n calls is itself an endpoint that must authenticate its caller. Decision: n8n is the public receiver; the core has one private signed endpoint.
- Zoom-out M10 (tenant isolation not needed for one client per deployment): accepted for RLS policies (tier 2); the tenant column in the ledger key stays tier 1 because the ledger is permanent.
- Readiness M6 (lane-level run): accepted as ONE run per lane at the end of its coding; this fits the owner's "code first, then test".

## Open for the owner (defaults already taken; he may veto)
Default 3 (who performs approved writes this round), the tier split, and the explicit yes that will be asked before merging the money, door and identity PRs.
