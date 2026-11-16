# Annotated resolve report: result review round 1 (egm:egm-resolve, auto accept by the lead's instruction)
Status: resolved (fixes applied; verification pending in evidence-2.md)
Inputs: result-r1-design.md (D), result-r1-zoomout.md (Z), result-r1-codebase.md (C). No severity was changed by the resolve step. Contests need checkable evidence; none was contested except where noted.

| id | source | sev | category | what was done | where |
|---|---|---|---|---|---|
| D-M1 / C-M3 | patch F-003, F-004 contradictions | Major | PROPOSE FIX | patches regenerated: every stale "45 s unmeasured/NOT RUN" line rewritten (scene 4 cells, lease bullet, recovery bullet, time-box line, risk 2, open question 5, statement 17 Tag/Test/Raw, Honest limits line); caption says "relayed ... not seen by us"; real CRM line 4 now scenes 1 to 4 | patches/F-003, F-004 |
| D-M2 | patch F-002 verdict word, test, contract, rebuild evidence, trim | Major | PROPOSE FIX | verdict "retry" with reason; sender contract in code comment and in F-002 row; Valid trims the key; rebuild re-run by me (3 new nodes, Valid and Claim changed, recovery and sub unchanged, no dangling edge); independent re-run required in evidence-2.md; new 422/503 test is a laptop task (T1) | patches/F-002, FINDINGS F-002 |
| D-M3 / Z-B1 / Z-B2 | CUT-LIST order and n8n-flows row | Major (Z called them Blocker candidates) | PROPOSE FIX | ORDER OF WORK added (F-001 first, copy SQL, update prose, then archive); n8n-flows row now "only the 4 mf-*.json, folder stays" | CUT-LIST.md |
| C-M1 | F-012 42 s only for film | Major | PROPOSE FIX | headline reworded; real-v5 HubSpot node has no timeout; LIMIT 1 proposal; Major kept with the reason stated (D asked for that) | FINDINGS F-012 |
| C-M2 | F-014 wording | Major | PROPOSE FIX | repeat is about every 12 minutes, not every sweep; no cap stays | FINDINGS F-014 |
| C-M4 | ranking and F-023 | Major | PROPOSE FIX | rows reordered take first then severity (ids unchanged); F-023 now "take" | FINDINGS.md |
| D claims S8, S17, S5 | verdict labels | Nit | PROPOSE FIX | S8 BACKED, S17 and S5 UNVERIFIED; totals 28 / 4 / 15 / 36 = 83 | lanes/L3-claims.md |
| D stores row count | 14 not 13 | Nit | PROPOSE FIX | counts rewritten, 14 rows, class totals add up | L3-stores.md, F-019 |
| D-add 1 to 6, Z-3 | placeholders, shared mail channel, HubSpot, DESK_ALERT_TO, review-state leads, retention, dn1_common delete | Major x3, Nit x3 | PROPOSE FIX | new findings F-029 to F-034 (DESK_ALERT_TO folded into F-014 and F-018); ledger rows added | FINDINGS.md, LEDGER-ROWS.md |
| D F-001 comment, migration | patch F-001 | Nit | PROPOSE FIX | comment names real-v5 and film-v5; ALTER lines added | patches/F-001 |
| C F-008 six vs five | title | Nit | PROPOSE FIX | six = five database nodes + RunSub, RunSub added to "where" | FINDINGS F-008 |
| C F-006, F-007 | line refs | Nit | PROPOSE FIX | lines :4/:11/:12 and :153/:158/:159/:164 cited | FINDINGS |
| Z (1) uncovered documents | 7 notes, DRAFT files, earlier audits, per-folder docs, logs | Major | PROPOSE FIX | added to CUT-LIST as candidates; "duplicate" of the DRAFT and 7 notes marked UNVERIFIED (not diffed line by line) | CUT-LIST.md |
| Z (2) sprawl | FLOWS-AUDIT duplicated lane headers; 4 forms per lane; spend ledger disagreement; copies count | Major | PROPOSE FIX | 125 duplicate lines removed; section 4 is now one copy of the lane files; lanes/README.md names the canonical file; EXCEPTIONS and L3-stores agree (spend ledger = proposed EXCEPTION, RETIRED only if no live model call); copies = 4 (3 files + inline) | FLOWS-AUDIT.md, lanes/README.md, EXCEPTIONS.md |
| Z (3) missed stores, portal grep scope, journal naming | store list | Major | PROPOSE FIX | small stores added; portal search scope stated; naming split put in F-020 | L3-stores.md, F-020 |
| Z (5) plain-words answer, undefined labels | wording | Major | PROPOSE FIX | six-sentence answer and a glossary at the top of FINDINGS.md | FINDINGS.md |
| Z remaining wording | many rows still use take, lease, doors in the cells | Nit | DECLINE (partly) | the glossary defines them once; cell wording not rewritten row by row | recorded, not fixed |
| C F-001 "byte-identical" | reviewer read only | Nit | none needed | lead ran cmp (v3 == v4), unchanged; evidence-2.md re-checks | evidence-2 |

Escalated to the lead or owner (cannot be fixed here): n8n SQLite versus the one-database rule (F-011), stage journal owner and trigger (F-020), spend ledger decision, second alert channel (F-030), HubSpot options (F-033), retention (F-032), all items needing n8n runtime, HubSpot, SMTP, the desk repo or the lane3 raw files, DECISION-one-store.md (absent), the CUT-LIST yes.
Count: accepted fixes 17 groups, contested 0, escalated 6 groups, declined 1 (row-by-row wording).
