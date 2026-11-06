# Freeze list (orders 16 to 18), written 2026-11-06 03:40 UTC / 09:10 IST

Status: all packages below are FROZEN on paper. No fresh Goldfish review followed the final revision of P2a, P2d, P3a, P4a, P4d (lead answer A in order 19: one egm review of each frozen revision is the first step of its build lane, scheduled by the lead; P4a first). Nothing here was run except the P2a probes on a throwaway PostgreSQL 16.15 (`evidence/P2a-round8-probes.md`). Every count below comes from the author's report or from my own grep of the file; none comes from running code.

| Package | Final revision | Ticket commit (author's) | Freeze-line commit | Lines | Mutants (author's count) | Open lead items |
|---|---|---|---|---|---|---|
| P1 text-normalising guard | 16 | da0b49c | da0b49c | 363 | 21 re-pointed/new groups; 108+k runs | PL35-52 answered (order 19 C) |
| Look-alike design | draft 11 | d3e8239 | d3e8239 | 242 | 68 names, 22 deleted, 46 live | PL-LK-57..61 answered (order 19 B) |
| P2a stop state | 10 | 2744e50 | a1cd389 | 480 | 178 (175 if reconciliation cut) | PL34-36 answered (F) |
| P2d redact/runmap | 6 | 7bc5d85 | bcad11a | 378 | 93 whole ticket (104 with the 11 strict xfails) | L23/L24 confirmed (E) |
| P3a migrations guard | 10 | 3a7f85d | ef60ec7 | 201 | 120 distinct | L18-L20 answered (F) |
| P4a money booking (k1b, llm) | 12 | 27c0dce (pushed as 2826fa8) | 2826fa8 | 573 | 83 (36 + 47) | PL60-65 answered (D) |
| P4d spend/settle | 10 | 00455d6 | d872810 | 316 | unchanged from rev 9 (a1 6, i 27, w 19, b 43, c 6) | PL22/23 answered (D) |

Open v1.1 items: each ticket keeps its own v1.1 table in plain words (P4a 37 rows by the author's count; P2a six new rows; counts for the others not re-counted by me). P1 moved enclosed/dingbat forms, mixed modifier-letter copies and further blank glyphs to v1.1.

## Merge order and conflicts (from my grep of each ticket; "mentions" is a text count, NOT a checked list of edits)
- Order the tickets themselves state: P1m, P1a, P1b first; P2a-1 BEFORE P4a-1 (PL63); P4a depends on P4d (all five P4d PRs, plus P3a and P1m, through P2a-1: `P2a.md:22`); P2d-2 depends on P1b, P1a, P2d-1; P2d-2b after P2d-2.
- Hot files (mention counts P1 / P2a / P2d(+design) / P3a / P4a / P4d):
  - `guard/tools.py`: P1 14, P2a 3, P2d 8 (+design 11), P4a 3, P4d 1. The look-alike check and P2d touch it; P2a/P4a/P4d mentions are probably cites, UNVERIFIED.
  - `guard/runmap.py`: P1 8, P2d 31 (+design 16). `LookalikeCopy` must also go into the `except (InputTooLarge, TooDeep)` tuple (design review COR-M).
  - `guard/redact.py`: P1 5, P2d 29. `guard/textnorm.py`: P1 9, P2d 5.
  - `defaults.py`: P1 18, P2a 6, P2d 26, P4a 21, P4d 12. ORDER IS NOT AGREED: `P4a.md:144` and `P2d.md:33` disagree about where P2d-1 goes; P2a PENDING LEAD 35 asks. The lead decides before the builders start.
  - `config.py`: P4a 28, P4d 10, P2a 7. `models.py`: P4a 28, P4d 17, P2a 6. `cli.py`: P2a 14, P4a 10, P3a 7, P4d 5. `store/migrate.py`: P2a 4, P3a 7, P4d 6. `k1b/loop.py`: P4a 47, P4d 9. `k1b/replay.py`: P4a 28.
  - `CHANGELOG.md` and `.github/workflows/ci.yml`: every ticket (append-only conflicts).
- Relay errata not yet delivered to other tickets (found by authors, still open): `P4b1.md:71` "downward once" should read "once, in either direction"; `P4b1.md:69` stale ValueError sentence; `P4b1` caller rule (never release a reservation for a sent call, P4d PL23); `P4b2.md:164` drop P3a from the `cli.py` order list; P5b2 counts; P6b1 "Ask:" item (P4d). P4b1 is still revision 1 and has no `request_bound` text, so lead gate item 0 for P4a fails today.

## Honest gaps
- Final revisions of five packages are unreviewed text (new P4a clauses a2-60/a2-61, the `_sha` surrogate fix, the P2a guard-trigger line, P2d's 93-mutant set).
- P2a trigger fix tested only as a superuser owner on PostgreSQL 16.15; the lead's condition is a test on 16 AND 17 by the builder.
- The P2d-2 mutant counts (93/141 rows) leave out the design's strict xfails (104/152 with them); the design's section 8 still says "41 live", stale against its own 46.
- Sonnet authors, not Opus egm-draft, wrote these revisions (accepted by the lead, order 19 G).

## DEFERRED (lead order 57 A2, 2026-11-06): frozen, NOT deleted, NOT built until a DEMAND line exists
| Ticket | Why deferred (lead's words, summarised) | What it needs to un-defer |
|---|---|---|
| AK-G16 (Kubernetes deploy kit) | no client or chain item asks for it; 25-35 h estimated; project-shaped, so it fails the genericity rule | a named client need or a core-chain dependency, written as a DEMAND line |
| AK-G15 (person queue) | wait for a client use case; its data/API contract stays in the GAPS doors | same |
| AK-G1 (chat) | wait for a client use case; its data/API contract stays in the GAPS doors | same |
Rung-table notes already appended to these three (AK-G16 BN-37, AK-G15 BN-29, AK-G1 BN-32) and the accepted AK-G16 cuts stay as written; the freeze stands. Order 57 A3: the shared source scanner is NOT built; revisit only if three of the five tickets build. A4: G14 gets no ticket (lead builds it from the studio portal kit).
