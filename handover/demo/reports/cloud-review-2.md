# Review E2 (round 2): egm-codebase-details on fix4 snapshot 1933731 (static reading, ran nothing)
Round-1 fixes verified by reading: atomic migration, reaper never claims failed, cap for all causes, ambiguous_prior check, per-book gate, Windows lock codes. 4 Major, 8 Minor new.
| # | Sev | Where | Scenario | Fix |
|---|---|---|---|---|
| M1 | Major | db.py _BACKFILL crm_done | Backfill assumes attempts>0 and label => CRM asked; false on first-release Retry path (claim first, CRM later): failed/internal:CrmError row gets crm_done=1, CRM row never created | no backfill 1 for failed internal:%; unknown origin => 2; migration test |
| M2 | Major | desk.py 723-747, 922-936 | no ownership token: reaper requeues a stalled row, T2 claims, T1 wakes and its _mark_crm matches state=sending => two CRM puts on blind CRM; T1 may overwrite T2 result (ABA) | use claim's attempts value as token in _mark_crm/_touch/_record_send_result; touch before qualifier |
| M3 | Major | desk.py 431-433, 289-294 | deterministic plain exception in decide: 500, receipt open, reaper re-runs forever, O item not actionable | count failures; after K write review/internal_error |
| M4 | Major | resolve / crm_unconfirmed | person has no correct exit: sent marks lead sent without an email; not_sent resets mark => second CRM put | decision crm_present (sets crm_done=1, state failed); reject sent for crm_unconfirmed |
| m1 | Minor | HttpCrm.capability None after restart | keyed re-put never triggers after crash; stale cached keyed | HttpCrm.refresh() at startup |
| m2 | Minor | _pending_to_unknown | last_error not set | set ambiguous_prior |
| m3 | Minor | requeue | endless requeue of hanging send; 15 s retry window | check count at requeue |
| m4 | Minor | capability cached 30 s | keyed->blind restart window | refresh before ambiguous_prior send; tuple swap |
| m5 | Minor | replay drives follow-up at once | 5 replays burn the cap | drive only if due |
| m6 | Minor | crm_done=1 best-effort write | fail leaves 2 | same retried transaction |
| m7 | Minor | gate_for aliasing | chdir, hard links, :memory: per thread | resolve once in Config |
| m8 | Minor | due[:20] | starvation, serial drives | time budget per pass |
Not checked: server.py, tests, HTTP-layer hostile input, Windows runtime.
