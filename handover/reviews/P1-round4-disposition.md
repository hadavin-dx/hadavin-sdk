# P1 round 4: disposition of every finding (applied to P1.md revision 6)

Written 2026-11-05 17:50 UTC (23:20 IST). Source: `P1-round4-resolve.md`. Merged pairs have one row each, same location.

| Finding | Status | Ticket location (field > part) |
|---|---|---|
| ADV-R4-A1 | applied | Words (hidden channel); Interface > Signals (six-part `has_hidden_channel`, `Variation_Selector` set, run-length rule); Tests > P1a new mutants |
| ADV-R4-A2 | applied (one addition: keycap ASCII+FE0F+U+20E3 accepted) | Interface > Signals; Decisions 4(e) |
| ADV-R4-A3 | applied, narrowed: needle minimums 6/8/6 as ordered; measured rates quoted, digits 8 recommended | Interface > `prepare_needles`; Tests > false-refusal rows; Stated limits (4); Decision 5 |
| ADV-R4-A4 | applied (merged with COR-C4, C12) | Header; The three pull requests; Not in v1 (P1c outline); v1.1 table; Interim rule |
| ADV-R4-A5 | applied (merged with COR-C5) | Files > P1m suppressions 1-4; Tests > 764 rewrite, 1545, `_pid_alive`; PENDING LEAD 22 |
| ADV-R4-A6 | applied | Tests > Golden test, Test 2 CI step, `check_history_append_only`, negative check |
| ADV-R4-A7 | applied | Mutation plan > meta-tests, import-time named killers |
| ADV-R4-B1 | applied (merged with B11) | Interface > `deny_hit` (clock, deadline from call entry, total budget); Tests > clock rows |
| ADV-R4-B2 | applied, narrowed: frozen `PreparedNeedles`; reason enum not added | Interface > `PreparedNeedles`; v1.1 table |
| ADV-R4-B3 | applied, narrowed: entities only, rows and v1.1 row, no decoders | Interface > `line_view` limits; Stated limits (3); Tests > gap 7 row |
| ADV-R4-B4 | applied (with B5) | Interface > P1b readings (Mn/Me over-match); Tests > over-match rows |
| ADV-R4-B5 | applied (with B4) | Interface > P1b readings (squash); Tests > over-match rows |
| ADV-R4-B6 | applied | Files > THIRD-PARTY-NOTICES.md (non-circular test, pinned sha256) |
| ADV-R4-B7 | applied | Tests > Golden test (time reported, 30 s limit to `perf`) |
| ADV-R4-B8 | applied (with COR-C15) | Tests > Golden test (one Python); Evidence > Python versions (3.12/3.14 report-only) |
| ADV-R4-B9 | applied | Evidence commands per PR; Interface > `prepare_needles` whole-list failure and lint |
| ADV-R4-B10 | applied | Interface > ID view, mixed needles; Tests > other P1b tests |
| ADV-R4-B11 | applied (merged with B1) | Interface > `deny_hit`; Tests > clock rows |
| ADV-R4-B12 | applied (merged with COR-C14; ratification sentences for the lead) | Decisions > B12/C14 sentences |
| ADV-R4-N1 | applied (merged with COR-C9) | Interface > Views (no `view()`, no `is_empty_key`) |
| ADV-R4-N2 | applied (errors merged, `ScanBudgetExceeded` and unused subclasses dropped) | Interface > Errors |
| ADV-R4-N3 | applied | The three pull requests > Why P1m exists |
| COR-C1 | applied | Files > P1m; Tests > P1m tests (21 + 7 killers); Mutation plan |
| COR-C2 | applied (relay; P2a must drop its copy) | The three pull requests; Decision 8 overlap; cross-ticket list in the report |
| COR-C3 | applied (weighted rule kept, SEAM-1 text owned by P1a) | Interface > Input rules, size rule and SEAM-1; Decisions (P2d conflict note) |
| COR-C4 | applied (merged with ADV-R4-A4) | Header; Not in v1 |
| COR-C5 | applied (merged with ADV-R4-A5) | Files > suppressions; PENDING LEAD 22 |
| COR-C6 | applied | Existing core code reused (`runmap.py` 145-146, 139-147) |
| COR-C7 | applied | Tests > P1m fail-before (verdicts, `allow_crash`, `_RETARGET` override) |
| COR-C8 | applied (28 re-pointed) | Mutation plan > P1a |
| COR-C9 | applied (merged with ADV-R4-N1) | Interface > Views, empty-result definitions |
| COR-C10 | applied (introspection test widened) | Interface > FOLD_VERSION; Tests > P1a new tests |
| COR-C11 | applied | Interface > `deny_hit` and caller rules/lint |
| COR-C12 | applied (merged with ADV-R4-A4) | Header; three-PR section; Files per PR |
| COR-C13 | applied | Files > P1a (`defaults.py`, CHANGELOG order); Decision 8 |
| COR-C14 | applied (merged with ADV-R4-B12) | Decisions > B12/C14 sentences |
| COR-C15 | applied (merged with ADV-R4-B8) | Evidence commands per PR |
| COR-C16 | applied | Tests > manifest test 2529 copied and edited by P1m and P1a |
| COR-C17 | applied | Files > Vendoring (10,864 = 9,862+692+129+181; 13.6 % proxy ratio); Tests > counts |

Counts: 39 rows (7 A + 12 B + 3 N + 17 COR = 39 ids); applied 39 (of which narrowed 3: ADV-R4-A3, ADV-R4-B2, ADV-R4-B3); contested 0; declined 0.
Applied with one addition of mine: ADV-R4-A2 (keycap form). Not instructed but chosen: size-rule conflict with the P2d round-1 resolve (followed round 4). Digit-only minimum applied as 6 (ordered); 8 is recommended in Decision 5.
Verified by me: cites re-read in code (see ticket section 'Checked in revision 6'). Unverified: everything in the ticket's UNVERIFIED section.
