# P2d round 1: disposition of every finding (ticket revision 2)

Written 2026-11-05 about 18:00 UTC (23:30 IST) by the drafting agent. Applies `P2d-round1-resolve.md`. Ticket: `handover/tickets/P2d.md` revision 2. "Applied" = the ticket text now does what the resolve says; nothing was run to prove it (text only). Places are ticket sections: Words, Two PRs, Facts (V1..V15), Fields-1 (P2d-1 template fields, by field name), Fields-2 (P2d-2), Tests (moved table, new rows), Mutation, Evidence, Classes, v1.1, P5c, L1..L12.

| id | sev | status | where in revision 2 | note |
|---|---|---|---|---|
| ADV-F1 | major | applied | Fields-1 Tests ("How old code is built"); Evidence step 2 | old tree = P1a head with only redact.py and runmap.py reverted; P1a defaults.py hunk present; collection error counts as a ticket defect; a grep check is in the command |
| ADV-F2 | major | applied (same as COR-C1) | Fields-1 files (constants stay); v1.1 V1; Mutation (N2 removed) | constants move cut, so N2 and the unkillable literals are gone |
| ADV-F3 | major | applied | v1.1 V1, V2, V3, V4, V5; Fields-1 files | constants move, THREAD-1, SEAM-4 cut; SEAM-1 goes to P1a (L4); WARDEN strip deferred with trigger |
| ADV-F4 | major | applied (with F6, COR-C4) | Two PRs; Fields-2; GAP-1, P1B-1; L2 | split into P2d-1 and P2d-2, P2d-2 waits for P1b; plan row with owner, order, start condition; no calendar date possible (exception: third item must finish first) |
| ADV-F5 | major | applied, narrowed | Fields-1 Interface ("Written spelling in the map"); MAP-1/2/3; N9, N10; L1, L5 | written slice stored; distinct number, NOT a new placeholder grammar (PLACEHOLDER in runmap.py would not see it); hard-guard fallback named. Gap found: placeholders of withheld lines keep the folded spelling (L5) |
| ADV-F6 | major | applied | Two PRs; GAP-1/P1B-1 (imperative xfail on behaviour); Fields-1 depends-on (P1b obligation to run tests and ALIGN-1) | no strict xfail tied to a P1b name |
| ADV-F7 | major | applied | Tests (status codes, honest rule); moved table; Evidence step 2 | every U row probed on the old tree per row; no module-level P2d-only import (getattr for FOLD_NOTE) |
| ADV-F8 | major | applied | Fields-1 Interface ("Honest cost statement", margin rule); Evidence step 6; L6 | worst-case wall time comes from the evidence runner, not the probe; probe figures marked UNVERIFIED; lower cap proposed only if margin under 2x (probe suggests 1.47x, so expect it) |
| ADV-F9 | minor | applied | Mutation (N8 rewritten, N3 dropped as duplicate of existing mutant 21) | N8 not run (no suite run allowed); the runner runs it first |
| ADV-F10 | minor | applied, adapted | ALIGN-1 row; Facts V13 | the repo has no `slow` marker (only live, perf); used `perf` to avoid editing pyproject.toml, which P1a also edits. Lead may prefer a new marker |
| ADV-F11 | minor | applied | Fields-1 Interface (Budget and cap, "Direct calls"); BAN-1; V7 | direct `redact()` budget statement added, ban test pinned |
| ADV-F12 | minor | applied | Evidence step 0 (blocking gate); L12 | owned by the lead |
| ADV-F13 | minor | applied | P5c section note (marked UNCHECKED until the P5c ticket cites it) | |
| ADV-F14 | nit | applied | ERR-1 row | args check only; no `__cause__` assertions |
| COR-C1 | major | applied (same as ADV-F2) | as ADV-F2 | |
| COR-C2 | major | applied | FOLD-NOTE-1 row; N6 | literal pinned |
| COR-C3 | major | applied | ERR-1, SEAM-2 rows; Facts V3; v1.1 V3 | patch `redact_mod.fold`, `cache_clear()` first, spy must see at least 2 calls; SEAM-4 cut |
| COR-C4 | major | applied (with ADV-F4, F6) | as ADV-F4 | |
| COR-C5 | minor | applied | Mutation (rows 5, 7, 12, 20 "rewrite snippet") | constants-move snippet change is gone |
| COR-C6 | minor | applied | MID-1 row; N11; test 29 note | test 29 proves only index 0 |
| COR-C7 | minor | applied | Mutation (R1, R2, R3 for runmap.py); BUDGET-1, BUDGET-2 | whether R1 reports kill or crash is UNVERIFIED |
| COR-C8 | minor | applied (with ADV-F1) | Fields-1 files; moved row 32 | getattr everywhere, including test 32 |
| COR-C9 | minor | applied | moved table rows 22, 27, 30 | labels and import list corrected; I re-read batch2 lines 344-354 for row 22 |
| COR-C10 | minor | applied, partly open | header probe rule; L3; V9 | figures marked "probe, UNVERIFIED by review"; whether probes count under order 7(2) is a lead question (L3). I ran one read-only import check |
| COR-C11 | minor | applied, but the premise is wrong | Facts V15; Fields-1 depends-on and Interface; L4 | resolve assumes P1a has a plain NFKD sum. P1.md rev 5 line 35 does not (w(c) with MAX_VALUE_LEN 3). I stated the refusals and asked the lead (new L4) |
| COR-C12 | minor | applied | Fields-1 depends-on; Two PRs | P2a and P4d ahead of P2d-1 |
| COR-C13 | nit | applied | Interface signature | keyword-only |
| COR-C14 | nit | applied | Fields-1 files; V10 | "43 lines" |
| COR-C15 | nit | applied | Interface (guarantee sentence, three cases) | |

**Counts:** 29 findings. Applied 29 (3 of them with a stated narrowing or adaptation: ADV-F5, ADV-F10, COR-C11). Contested 0. Declined 0. Merged pairs: ADV-F2 = COR-C1; ADV-F1 + COR-C8; ADV-F4 + ADV-F6 + COR-C4 + COR-C11 (dependency); ADV-F7 + COR-C9.

**Things the resolve did not cover, found while applying (all in the ticket, as PENDING LEAD):** L4 (P1a size rule differs from the resolve's assumption), L5 (withheld-line placeholders hold the folded spelling), the missing `slow` marker, and the `tests/test_redact*.py` glob in the plan's done command matching no file today.

**Not checked:** nothing in revision 2 was run against the tests; every label marked U, every probe figure, N8 and the PR #50 GitHub state are UNVERIFIED (ticket "UNVERIFIED" section).
