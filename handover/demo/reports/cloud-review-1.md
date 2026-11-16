# Review E: egm-codebase-details on patch snapshot 93e738b (saved verbatim in substance by the cloud session; reviewer ran nothing)
Result: 0 Blocker, 6 Major, 9 Minor. Reviewer read gate/desk/db/identity/adapters/lockfile/schema/contract/CONTRACT-DELTA; not server.py, config, tests. No interleaving was run.

| # | Sev | Where | Scenario | Fix proposed |
|---|---|---|---|---|
| 1 | Major | db.py _migrate | Old book: step 1 adds columns + drops view review_items and commits; step 2 (executescript) recreates view. A crash between leaves columns present, view missing; next start returns early, GET /review fails "no such table" | One transaction, or also check sqlite_master for the view; rollback guard; test |
| 2 | Major | desk.py _crm_step; delta line 14 | crm_done mark swallowed on busy after a successful put -> second put after refused->pending; blind CRM gets a double row; non-busy error leaves crm_done 0 | Intent mark before the put; leftover = person (unknown) on blind CRM; fix delta wording |
| 3 | Major | desk.py ~754-758 | Auto-retry only covers refused/unreachable; keyed ambiguous and transient CRM/qualifier errors go to failed at once | Include them in the bounded retry; only blind ambiguous stays unknown |
| 4 | Major | desk.py 662-708 | run_followup checks pending, then label step, then _claim accepts pending OR failed: reaper can claim a failed row and reset the cap | _claim takes from_states; automatic drivers only 'pending'; only retry may take failed |
| 5 | Major | start_background | Reaper only runs if server.main() calls it (lead edit) | Land server.py hook; subprocess test |
| 6 | Major | contract.md 21(4),(5),49-53,61,89,96 | Old contract text now contradicts code | Add strike-list to delta |
| 7 | Minor | reaper 20 s requeue of sending while owner alive | possible 2 CRM puts (blind) | refresh updated_at per stage or raise threshold |
| 8 | Minor | last_error marker overwritten | keyed pending after crash then sender turns blind -> blind resend | own flag; skip when refresh fails |
| 9 | Minor | _decide safety net | RecursionError/DataError leave receipt open | add; narrow ValueError |
| 10 | Minor | reap_once | HTTP GET every second | refresh only when needed |
| 11 | Minor | schema | no index on outcome/state | add partial indexes |
| 12 | Minor | gate.py global | desks on different books serialise; not re-entrant | per-desk gate; document |
| 13 | Minor | lockfile Windows | every OSError = held; loop exhaustion plain OSError | map codes; LockUnavailableError |
| 14 | Minor | _used | retry/resolve do not set it | set in _claim |
| 15 | Minor | migrated old book crm_done=0 | re-put once on blind CRM | backfill crm_done=1 or state in delta |

Checked sound: no nested _write, no network inside a write transaction, atomic claim, no SQL from text, control-char checks before strip.
