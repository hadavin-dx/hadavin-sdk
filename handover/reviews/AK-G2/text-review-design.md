# AK-G2 build-start text review: egm-design (condensed, saved by cloud session 2026-11-09)
Verdict: NOT buildable as written. 2 Blockers, 7 Majors, 7 Nits. Text only, nothing run.
B-1 BN-24/BN-26/L15/L16/D10/D13 contradict: -a would ship with the runtime role able to do needs_person->received (message re-run hole on a money path). Fix: new BN, -a trigger refuses that move for every role except the future re-run owner role; tests reopen via migrator fixture; say which rows apply to -a.
B-2 Build order cannot start: no P4c-2/P5c/AK1-a branch, P4d/P2a-1/P3a-2 unmerged. Lead decided the peel (ORDER 174); build it.
M-1 Injected clock cannot be met: finish/release/reopen_inbound take no `now`; stores stamp models.now()/SQL now(). Add `now` args + PG test that SQL now() absent.
M-2 "No new identity" breaks one-identity-per-function: door and dispatch share the runtime role. Define door role (INSERT/SELECT) and dispatch role, negative tests; or lead item with trigger (AK-G16). Test source principal_id is not approver-capable.
M-3 Not one choke point: Runtime.handle(run_id=None) default; no sibling grep; name bug class "one delivery, N runs" (R368). Guard test or StartRun only path.
M-4 Fail-before thin: only D0 fails on base. Add R2 (8 threads), convert repro R1/R1b/R3 to base-failing rows via naive-door shim.
M-5 Missing mutants: tenant dropped from delivery_key; hash key ignored; max_open counts only received; _classify rule order; StartRun omits run_id; old secret still accepted. BN-24 reuses id M-b29 (rename); evidence lines 383-384 stale ranges.
M-6 ~29 build notes override body; stale "nine methods", inbound_infra_stops, compare_ids. Lead-added consolidated "as built" appendix (BN-30), over-250-lines reason in first lines.
M-7 Slice delivers no usable product (no operator list/reopen, orphan sources make tick exit 1). Say so in Done; gate pilot on AK-G15/G16.
M-8 Rolling deploy mixes hash keys (per-process key-check cache). Re-read stored check every receive_inbound.
trigger_kind 'webhook': models.py:94 and 0001_core.sql:10 allow event/schedule/user only; runs use "event"; add one sentence + assertion in D1/D12 (Nit, Major if audit must filter by origin).
Nits: T5 recordings need aud; log-safety of 64-bit check; reuse rows never purged; one body_days; purge is cross-tenant; unknown-vs-known source leak; M-a71/BN-24 mutant ids confusing. Wording: "trigger" x3, "source" clash with sources/, "receipt" overloaded, internal ids in prose.
Not reviewed: other tickets, round1-3 reports, any Postgres behaviour.
