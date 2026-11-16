# F6 fix round 1: change log
- Section 1(c): rewritten; m0() tests hook plain and repeat on test-built flows; hook invalid address, missing key, error and kill paths untested; line cites fixed (mf.py:121-124, :125-126, m1 :129-134).
- F6-01: CrmUpsert no-timeout made real-v5 only (film-v5 has 10 s, 2 tries); executionTimeout-below-lease idea removed (40 s risk), per-node timeouts on real CrmUpsert and SendMail only, test first; added "retry" must also go in the F6-03 table; added stage_failed/lost_claim answered "processing" 200 and recovery 3 tries then failed; folded in F6-05 (missing row).
- F6-03: array/object message_id reworded to "outcome unknown: error or coercion"; contract table must include reply values.
- F6-04: door-column idea dropped; plan claim limit (PLAN-4-NLITE-FROM-LEAD.md:9) stated; Nit.
- F6-05: merged into F6-01.
- F6-06: rewritten to match 1(c).
- F6-07 (new): missing/empty/non-string message_id; Nit for take, Major for client build; 422 guard and T20-style test proposed.
- Counts line updated. F6-02 unchanged.
