# P1 round 5: disposition of every finding (applied to P1.md revision 7)

Written 2026-11-05 18:45 UTC (00:15 IST on 2026-11-06). Source: `P1-round5-resolve.md` (28 rows covering 32 ids). Merged pairs have one row each, same location. Statuses: applied / applied, narrowed (as the resolve narrowed it) / applied with an addition of mine / contested / declined. "Ticket location" is field > part of `handover/tickets/P1.md` (names, not line numbers, because lines move).

| Finding | Status | Ticket location (field > part) |
|---|---|---|
| ADV-R5-1 + COR-C2 | applied | Words (hidden channel (c)); Interface > Signals (rules 5 and 6, "The invisible set", `_EXCLUDED`, "Probe and cross-check", "Not in the set", "Enumeration test" with rows and 3 mutants); Mutation plan > P1a new mutants. Correction of the resolve text: U+180E, U+2061 to U+2064 and U+206A to U+206F are Cf, so they come in through the Cf class; the reviewers' cite `invoicecheck.py:345-346` is really `_IGNORABLE` 343-348 and `_DELETE` 349-351 (re-read). Cross-check with Intake: equal in both directions (3,741 code points). |
| ADV-R5-2 | applied, narrowed (no "more than one tag text" rule) | Interface > P1b: the one DENY call (`prepare_needles` order of checks, step 2 and 3); `deny_hit` (b); Tests > Other P1b tests (entity-written tag needle row, expanded over-long row); Mutation plan > P1b new mutants |
| ADV-R5-3 | applied, narrowed (stated limit, no accept-rule) | Interface > Signals (end of the rows: flag emoji refused, row); v1.1 table (subdivision flags); Stated limits (5) |
| ADV-R5-4 + COR-C3 | applied | Interface > Signals rule 3 (selector after a non-selector base, one per base, stated 64-byte capacity), rule 4; added rows; Mutation plan > P1a new mutants; Decision 4(e) |
| ADV-R5-5 + COR-C6 | applied (figures corrected: about 4 % at 50,000, about 20 % at 250,000; exact chance 4.9 % and 22 %) | Interface > `prepare_needles` (prototype paragraph, correction note); Stated limits (4); Decision 5; UNVERIFIED |
| ADV-R5-6 + COR-C9 | applied | Interface > `deny_hit` ("Total budget over several prepared lists" rule k x (budget + S) <= 6.0); Prototype cost and the constants (budget 2.0, hostile pair now returns True by deadline); Constants in `defaults.py`; Tests > clock rows and perf rows; Decision 5 |
| ADV-R5-7 | applied (with a finding of mine: with scan 6, id 8, digits 6 the digit rule binds nowhere) | Interface > `prepare_needles` (order of checks, final key, additional rule, consequence); Tests > Other P1b tests (minimum rows with patched constants); Mutation plan > P1b new mutants (3); Which view each caller uses |
| ADV-R5-8 | applied (plus an extension of mine: P1b also re-runs P1a's new mutants) | Mutation plan > meta-test (g), "P1b re-derives and re-runs the earlier mutants", How many |
| ADV-R5-9 | applied | Decisions (all ten items written out; real list; `b13ff07` named for provenance only) |
| ADV-R5-10 | applied, narrowed (no new class map) | Tests > Generated-table test for letters that read as digits (probe: 71 entries, 62 not Nd; decision per digit value; widened alphabet) |
| ADV-R5-11 | applied | Interface > `prepare_needles` (empty list raises, `allow_empty`); Tests > Other P1b tests (empty list, copy, deepcopy, replace, pickle rows); Mutation plan > P1b new mutants; UNVERIFIED |
| ADV-R5-12 | applied | Interface > Views (`id_key` is not for DENY); `deny_hit` paragraph; Which view each caller uses |
| ADV-R5-13 | applied | Existing core code reused (checked, not relevant: `k1b/atomic.py`, `stats.py`, `evals.py`, `store/memory.py`, `tests/contracts`; 0 hits by command) |
| ADV-R5-14 | applied (which tickets edit `defaults.py` is UNVERIFIED) | Files > P1a change (`defaults.py` order); Decision 8 |
| ADV-R5-15 | applied | Existing core code reused (high bits); Tests > Other P1b tests (high bits, minimum case counts, patch point of each clock row) |
| COR-C1 | applied | Tests > Golden test > Test 2 (CI step with `if: github.event_name != 'schedule'`, zero-base `case`, why, rules); Decision 3 |
| COR-C4 | applied (CUT; the mutant is equivalent) | Interface > Constants in `defaults.py` (digit table note); Mutation plan > P1a new mutants (import-time paragraph); How many (arithmetic: P1a new 13 + 2 - 1 + 5 = 19; distinct mutants 21 + 28 + 19 + 21 = 89; runs 21 + 47 + 68 = 136) |
| COR-C5 | applied | Tests > gap table rows "7 entities, line breaks" (needle `12345678`) and "Ze" (levels stated: key-set and `deny_hit` with needles of at least 8 characters; key claims probed) |
| COR-C7 | applied | Tests > P1m fail-before (both overrides at 1812 and 1873, loop 1886-1889, 21 of 21 match once by command, name lines re-derived) |
| COR-C8 | applied | Interface > Pin check (`expected: str \| None = None`, read at call time, row and mutant) |
| COR-C10 | applied | The three pull requests > "P1m OWNS" overlap row; Decision 8; Decisions > Relays (P2a) |
| COR-C11 | applied | Interface > FOLD_VERSION (`41740c11` is in `textnorm_manifest.json`, not in the header) |
| COR-C12 | applied | Header "Labels in brackets"; Rules and sources cited |
| COR-C13 | applied (CUT) | Tests > Python versions (no 3.14 probe claim); v1.1 table (3.14 probe) |
| COR-C14 | applied, narrowed | Files > P1m suppressions item 2 (inline literal first; lines 1957 and 2051 confirmed to have no `noqa` by `grep -n`); PENDING LEAD 22 |
| COR-C15 | applied (relay) | Decisions > Relays for other tickets (P2d cites to be by item name) |
| COR-C16 | applied | Header (convention); cites fixed: `CHILD_ENV` 84, `crash_type` 1180, `_bidi_lines` 1003, ruff `extend-select` `pyproject.toml:72` (the review says 74; 72 is the line, 74 the next table header) |
| COR-C17 | applied | Interface > Views (`_keyset_encode` private); Files > Vendoring (10,864 split: 10,554 data and generated table, 310 hand-written); Mutation plan (size-check mutant reworded); P1b same_person (Li Na, Lina on purpose); The three pull requests > P5a dependency |

Counts: table rows 28; ids 32 (ADV 15, COR 17; merged pairs 4: ADV-R5-1 = COR-C2, ADV-R5-4 = COR-C3, ADV-R5-5 = COR-C6, ADV-R5-6 = COR-C9). Applied 32 ids (28 rows): of which narrowed 6 rows (ADV-R5-2, ADV-R5-3, ADV-R5-10, COR-C4 as a cut, COR-C13 as a cut, COR-C14); contested 0; declined 0.
Applied with an addition or finding of mine: ADV-R5-7 (the digit rule binds nowhere with the proposed numbers), ADV-R5-8 (P1b also re-runs P1a's new mutants), ADV-R5-1 (a correction of two facts in the resolve text), ADV-R5-5 (my disagreement with the resolve's reason for keeping 6; the ticket still says 6 as ordered).
Verified by me by command: see the ticket section "Checked in revision 7". Unverified: everything in the ticket's UNVERIFIED section (no suite, ruff, bandit or mutation run; DerivedCoreProperties.txt not read; the copy and pickle bypass not tried).
