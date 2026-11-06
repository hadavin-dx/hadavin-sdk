# P4a round 11 disposition (author answer to `P4a-round11-resolve.md`)

Written 2026-11-06 about 02:35 UTC (08:05 IST) by the revision 12 author. Target: `handover/tickets/P4a.md` revision 12 (FINAL, FROZEN; LEAD-ORDERS orders 1-17). Status words: applied, contested, declined. No finding was left open. No review round 12 follows (order 16 item 3).

| finding id | decision | where in the revision 12 ticket |
|---|---|---|
| M-1 (Major) | applied | C13p clause 2 (price 3.123457, 301-byte prompt, literals 0.01630017 and 0.04890049, exact-ceiling check); mutant a2-60; line 68 sentence ("W, one request's worth") |
| M-2 (Major) | applied | P4a-1 Depends-on ("P4c-2 AND P4b2-a"); Answer first 2 (nothing in code enforces the live-call rule); Done interim sentence; CHANGELOG entry (6) of P4a-2 |
| N-1 | applied | title and "FROZEN at revision 12" line; orders 1-17; PL60 to PL63 marked CONFIRMED; checklist 6 status list; Done sentence ("two rounds" only for built code) |
| N-2 + correctness N1, line 342 half | applied | C13(k): `loop.py:211-214`, `:200-202`, `:74`, 216 lines |
| N-2 + correctness N1, line 19 half | contested (as the resolve decided) | `replay.py:236` is right; the real line 19 error is fixed under N-3 |
| N-3 + correctness N5 + sibling | applied | "What revision 11 changes" item 4 (rewritten site list); `_sha` with `surrogatepass` in the `k1b/replay.py` interface bullet; C13(k) clause 2; mutant a2-61; CHANGELOG entry (7); PL64 |
| N-4 + correctness N2 | applied | `cli.py:241` (four places); count command pinned (169 now, 171 after P4a-2; 6 to 8 in `k1b/replay.py`) in item 7 of "What revision 11 changes" and the P5b2 relay |
| N-5 | applied | a2-11e deleted; no bool clause (`config.py` bullet, C8, Notes for P4d); rule "every id is one hunk and counts" in the mutants paragraph; a1-28 and a1-29 stay two hunks (U4 text); all "or 81", "or 80", "45 if", "35 if" text deleted; PL65 |
| N-6 | applied | P4a-1 Depends-on (P1m, P3a and the five P4d pull requests) |
| N-7 | applied | Lead merge-time checklist (item 0 is the gate; P4b1 revision 1 on disk); Answer first 2 |
| N-8 (a), (b), (c) | applied | a2-48b rows and C13p/C13q text (kill condition; the resolve's example number 0.015657 not used, see below); a2-33 one variant; P4a-1 CHANGELOG entry (4) |
| correctness N3 | applied | `tests/test_k1b_replay.py:388` (two places) |
| correctness N4 | applied | C13(k): `ScriptedLLM([tool_reply("no_such_tool", q=s), step2])`, no subclass, UNVERIFIED marker removed |
| correctness N6 | contested (as the resolve decided) | nothing to change; grep evidence in the resolve |
| correctness wording notes | applied | `common.py:65-83` (`tools_for`) in three places; the retried lambda in the "Where `reply()` runs" bullet |
| "Held" and "Verified" (record) | declined (record only) | counts only change through the rows above; see Counts |

## Errata I found myself (not in the resolve), checked against `tickets/P4d.md` on disk (revision 10, read only)
| item | decision | where |
|---|---|---|
| settle-excess floor constant named in the `defaults.py` order, in the constant list and in PL45 (P4d withdrew its PL19) | applied (removed everywhere) | Named constants bullet; Hot files text; PL45 |
| "settle-above-reserved bound is P4d's PL19" | applied | Notes for P4d (5): no bound; a settle books the full actual and never refuses (P4d PL10 and PL22) |
| P4b1 caller rule (P4d PL23: a sent call is never released) | applied | "Settle in finally"; Notes for P4d (5b) |
| order 14 item 3 (book the upper bound) and P4a depends on P4d | checked, already the ticket's rule | "What revision 12 changes" item 4 |

One deviation, stated plainly: the resolve's N-8(a) example value 0.015657 is not written into the ticket, because I could not reproduce it; the ticket says any value other than the literal 0.016260 kills the mutant.

## Counts
- Resolve rows: 15 (13 applied, 1 contested for the whole row = correctness N6, 1 declined = the record). N-2's line 19 half is the contested part of an applied row.
- Mutants: P4a-1 36, P4a-2 47 (46 minus a2-11e plus a2-60 and a2-61), total 83. Test rows 34. C13 sub-rows 19; C13 killed list 19. PENDING LEAD numbers in use 53 (1 to 11, 24 to 65), live 45. v1.1 rows 37.
- New PENDING LEAD: 64 (replay crash fix inside P4a-2), 65 (counting rule and the cut of a2-11e). PL60 to PL63 CONFIRMED by order 16 item 3.
