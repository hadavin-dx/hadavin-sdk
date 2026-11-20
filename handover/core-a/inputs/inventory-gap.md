# Core gap analysis (read-only Fable Explore agent, 2026-11-20; condensed by the lead)
Repo `projects\hadavin-sdk`, origin/main = 51c9fc4fb (PR #99, 2026-11-13); nothing merged since. States below were read from git/gh by the agent; "per note" = read in a handover file, UNVERIFIED. The full 60-row table is only in the agent hand-back of this lead session; the decisions are here.

## Read first
- Newest plan is NOT plan-v4-market-aligned: `plan-v4-3` (amendment A18) on `origin/cloud/core-hardening:handover/studio-notes/` (with v4-1, v4-2) reverses: P2d ON in v1 (not off); P5c pattern backend default, Presidio optional extra (missed 13 of 30 hostile inputs); AK-G2 own code, no pg-boss/Graphile wrap.
- Core was paused (lead order 2026-11-13) and the cloud session stopped 2026-11-16 ("nothing reviewed clean"). Owner 2026-11-20 chat order: complete the core modules today with cloud sessions = the un-pause and the lift (defaults recorded in plan-v1).
- Deferred on paper (order 57/59, owner yes needed): AK-G15, AK-G1, AK-G16, AK0, AK2a, AK4a; paused (order 49): AK-G17 SSO, JG-1..5.

## State by module (verified from git/gh unless marked)
MERGED on main: P0a (#71), P0t (#67), P1m mutation runner (#61 #62), P3a-1 (#68), P6a-1 (#72), PEEL (#87).
OPEN PRs (all stacked/CONFLICTING/draft or red CI; none merge-ready): text chain #63 P1a (red) -> #70 P1b -> #77 P2d-1; money chain #66 P4d-a1 (green, closest) -> #75 P4d-a2/b -> #76 P2a-1 -> #78 P4a -> #86 P6b1 and #75 -> #79 P4b1; diagnostics chain #74 P5a (red) -> #80 P5b1 -> #85 P5b2 (held O7); stand-alone #73 P3a-2 (3 heads), #83 P0t follow-up, #89 runner keywords (security red), #84 evidence workflow (red), #91 scan-config guard; stale #41 #43 #47 #48 #49 #50; Dependabot #92 #93 #95 #96 (one failure each), #94 green.
BRANCH-ONLY: AK-G2-a `core/ak-g2-a` (8 commits, 23 files, triggers/ledger.py, migration 0006_inbound, 2 failed tests per PARKED.md), AK1-a `core/ak1-a` (pipeline/step.py; 148 failed in builder's own DB per PARKED.md), P1d-a `core/P1d-a`, P6a nits, T1/T2 tests `core/T1-T2-tests`, plus unplanned Q8a/Q8b/Q8c/PR-H and lead-desk promotion branches (none review-clean).
NOT STARTED: P1c, P1d rest, P2d-2/2b, P4b2, P4c, P4e (waits owner), P5b3, P5b4 (deferred), P5b5 (deferred), P5c (4 PRs), P6b2 (deferred), P8a/b/c, AK-G2-b (signed door), AK1-b (outbound gate), AK1-c (wiring + tenant RLS), AK2b/c/d, AK3, AK4b, AK5 recipes, AK6-8, channel kind + template packs, portal (no code on main; plans say client's own tool by default), AK-G17.
Merge-number clash: `0006_spend_reservations.sql` (money chain) vs `0006_inbound.sql` (ak-g2-a); P2a-1 adds 0007. First to merge takes the number (amendment A3).

## Plan conflicts and risks the lead must settle
1. Two money designs: P4b1 chain (#75/#79) vs the cloud audit's S-1/S-2a (limits.py and Store counters); audit Blockers C-01 (zero price switches limits off), A-01 (parked audit events never written; chain.py reconcile has no tick caller), X-02 (spend checked before, charged after, no reservation).
2. AK1 naming: plan says AK1a/1b/1c (tenant / gate / wiring); ticket says AK1-a = step contract + tenant key helper.
3. CHANGELOG names `0006_evidence.sql`, main ships `0005_evidence.sql`; README says demos are invoice/PO and document Q&A, only ask-your-data exists.
4. G5: `approvals/gate.py:42` and `guard/redact.py:16` promise a second leak check that has no code (lead dropped it, ORDER 009, text not reworded).
5. Memory rule says portal modules and SSO are core; plans say no default portal; SSO paused.
6. In pilot/prod the core carries out no approved action today (audit; not re-read): the separate-executor guarantee is still to build.
7. `sources/kubernetes.py` is a specific reader inside core (against the generic rule); `extract.py` has no caller.

## Agent's suggested lanes (adopted with changes in plan-v1)
A doors: #83, #89 -> #73 P3a-2 -> AK1-a -> AK-G2-a -> AK-G2-b -> template pack -> demo promotions. B money then guarantee kit: #66 -> #75 -> #76 -> #78 -> #79 (+T1) -> P4b2 -> P4c -> #86 -> AK1-b -> AK1-c -> AK-G15, AK-G1. C text/redaction/diagnostics then kit: #63+#70 -> P1c -> #77 -> P1d -> #74 -> #80 -> #85 -> P5b3 -> P5c -> P6b2 -> AK4a, AK2a, AK-G16, recipes; portal and AK-G17 last.
Joins that cannot be avoided: AK1-b (B) needs P5c-1/2 (C); AK-G1-a (B) needs AK1-a (A); AK-G16-a (C) needs P2a-1 and P4b2 (B); AK4a-3 (C) needs AK1-b (B). Hot files shared by chains: hot-file rule 10.
