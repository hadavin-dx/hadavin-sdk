# Demand lines 1 (lead order 57, A2 DEMAND rule)

Written 2026-11-06 by the cloud session. Read-only evidence check: for each ticket not in the safety chain and not one of the three deferred tickets, is there a core-chain item, or a named client or product need, that a ticket, `freeze-list.md`, `studio-notes/GAPS.md` or `reviews/rung-audit-1.md` states? Nothing was run. Line numbers are from today's files and move. A build note BN-n (DEMAND, lead order 57) was appended to each ticket.

Rules I applied: (1) a dependency from a deferred ticket (AK-G16, AK-G15, AK-G1; `freeze-list.md:34`) does not count. (2) A dependency from a ticket that itself has no demand does not count (so demand is followed down the chain). (3) The GAPS.md core-slice (`GAPS.md:54`) is a reviewer's recommendation that 'needs your yes' (`GAPS.md:51`); I counted it as a stated product need but marked where it is the only evidence. (4) No client is named anywhere in the evidence except the Jagrat chat-ops ticket JG-3, whose order-47 files are PAUSED (`GAPS.md` section D). I invented none.

| ticket | DEMAND (one line) | evidence cite | verdict |
|---|---|---|---|
| AK-G2 | gap-register item G2 (inbound triggers and connectors, severity BLOCKER, `studio-notes/GAPS.md:11`) and the recommended core slice, which says the slice 'also needs' the first inbound trigger (G2, G15, G14) (`studio-notes/GAPS.md:54`; that slice order is marked 'needs your yes', `GAPS.md:51`) | GAPS.md:11; GAPS.md:54 | HAS-DEMAND |
| AK0 | NONE FOUND in the tickets or freeze-list (candidate to DEFER) | AK2a.md:92 (only dependent, itself NO-DEMAND); AK1.md:96 | NO-DEMAND |
| AK1 | AK-G2-a needs AK1-a (`tickets/AK-G2.md:133`; AK1 names used, `AK-G2.md:15`), and AK-G2 has demand (see its note) | AK-G2.md:133; JG-3.md:29 | HAS-DEMAND |
| AK2a | NONE FOUND in the tickets or freeze-list (candidate to DEFER) | GAPS.md:53; AK1.md:86 | NO-DEMAND |
| AK4a | NONE FOUND in the tickets or freeze-list (candidate to DEFER) | GAPS.md:20 (register only) | NO-DEMAND |
| P4b1 | P4a (safety chain): its merge sequence is P4a-1, P4a-2, P4b1-a, P4b1-b in one sitting (`tickets/P4a.md:97`), and `freeze-list.md:26` says P4b1 has no `request_bound` text so 'lead gate item 0 for P4a fails today' | P4a.md:97; freeze-list.md:26; P4b2.md:91 | HAS-DEMAND |
| P4b2 | P4a (safety chain): P4a-1's live-call rule waits 'until P4c-2 AND P4b2-a have merged' (`tickets/P4a.md:21`); P4a section 8.4 hands booking of a timed-out request 2 to P4b2-a (`tickets/P4a.md:123`) | P4a.md:21; P4a.md:123; AK1.md:96 | HAS-DEMAND |
| P4c | P4a (safety chain): P4a-1's live-call rule waits 'until P4c-2 AND P4b2-a have merged' (`tickets/P4a.md:21`) | P4a.md:21; AK-G2.md:133; AK1.md:96 | HAS-DEMAND |
| P5a | P5c needs P5a and P5b3 (`tickets/P5c.md:151`, `:704`: 'the real needs are P5a and P5b3'), and P5b1 lists P5a as merged-first (`tickets/P5b1.md:61`) | P5c.md:151; P5c.md:704; P5b1.md:61 | HAS-DEMAND |
| P5b1 | P5b2 lists P5b1 as merged-first (`tickets/P5b2.md:22`) and P5b3 depends on P5b2 (`tickets/P5b2.md:100`), which P5c needs (`tickets/P5c.md:151`) | P5b2.md:22; P5b2.md:100; P4b2.md:91 (order only) | HAS-DEMAND |
| P5b2 | P5b3 depends on P5b2 (`tickets/P5b2.md:100`; the CSV is used by P5b3 only, `tickets/P5b2.md:198`), and P5c needs P5b3 (`tickets/P5c.md:151`, `:704`) | P5b2.md:100; P5b2.md:198; P5c.md:704 | HAS-DEMAND |
| P5b3 | P5c needs P5a and P5b3 (`tickets/P5c.md:151`, `:704`) | P5c.md:151; P5c.md:704 | HAS-DEMAND |
| P5b4 | NONE FOUND in the tickets or freeze-list (candidate to DEFER) | P5b5.md:26; P6b2.md:275; P5c.md:151 | NO-DEMAND |
| P5b5 | NONE FOUND in the tickets or freeze-list (candidate to DEFER) | P8a.md:32 (blanket); P5c.md:704 | NO-DEMAND |
| P5c | AK-G2-a needs P5c (`tickets/AK-G2.md:133`); AK1-b needs P5c-1 and P5c-2, AK1-c needs P5c-3 (`tickets/AK1.md:96`); P6a-2 depends on P5c (`tickets/P6a.md:92`); the recommended slice lists P5c (`studio-notes/GAPS.md:54`). | AK-G2.md:133; AK1.md:96; P6a.md:92; GAPS.md:54 | HAS-DEMAND |
| P6a | AK-G2-b needs P6a-1 (`tickets/AK-G2.md:133`); the recommended slice lists P6a (`studio-notes/GAPS.md:54`; slice order needs the lead's yes, `GAPS.md:51`) | AK-G2.md:133; GAPS.md:54 | HAS-DEMAND |
| P6b1 | AK1-c needs P6b1 (`tickets/AK1.md:96`); the recommended slice lists P6b1 (`studio-notes/GAPS.md:54`) | AK1.md:96; GAPS.md:54 | HAS-DEMAND |
| P6b2 | NONE FOUND in the tickets or freeze-list (candidate to DEFER) | P2a.md:33 (order); AK-G16.md:191 (deferred); GAPS.md:54 | NO-DEMAND |
| P8a | WEAK, inferred: the demos pin old core copies (`tickets/P8a.md:40`), and `studio-notes/GAPS.md:54` moves 're-pinning the other three demos' to the background, which leaves the Intake demo's re-pin in the slice | P8a.md:40; GAPS.md:54 (inferred) | HAS-DEMAND |
| P8b | NONE FOUND in the tickets or freeze-list (candidate to DEFER) | P1.md:25; P5a.md:263 (weak) | NO-DEMAND |

## Tickets without demand (question for lead)

- AK0: AK2a.md:92 (only dependent, itself NO-DEMAND); AK1.md:96
- AK2a: GAPS.md:53; AK1.md:86
- AK4a: GAPS.md:20 (register only)
- P5b4: P5b5.md:26; P6b2.md:275; P5c.md:151
- P5b5: P8a.md:32 (blanket); P5c.md:704
- P6b2: P2a.md:33 (order); AK-G16.md:191 (deferred); GAPS.md:54
- P8b: P1.md:25; P5a.md:263 (weak)

Question: defer these (frozen, not deleted, not built until a DEMAND line exists), as with AK-G16, AK-G15 and AK-G1? Knock-on effects:
- AK0 and AK2a go together (AK2a needs AK0, `AK2a.md:92`).
- P5b4, P5b5 and P6b2 go together (P5b5 needs P5b4, `P5b5.md:26`; P6b2 needs P5b4, `P6b2.md:275`). P8a's line 32 lists every v1 row as a dependency, so it must be amended if they are deferred.
- P8b has only weak mentions.

## Weak or conditional demand (listed HAS-DEMAND above; lead may want to overrule)
- P8a: inferred from `GAPS.md:54` only.
- P5a, P5b1, P5b2, P5b3, P4c: demand holds only through P5c (and, for P4c, P4a's live-call rule) while `GAPS.md:54` lists them in the background group; their demand is a chain need, not a slice need. P4b2 lists P5b1 for file order only.
- AK1: demand is AK-G2-a plus JG-3. If AK-G2 is deferred it drops to JG-3 (a PAUSED order-47 ticket).
- AK-G2: its demand is `GAPS.md` G2 (BLOCKER) and the slice recommendation, not a client. `GAPS.md:54` says the slice also needs G15 (queue), which order 57 deferred; the two statements pull in opposite directions.

## What I could not place
- Nothing was ambiguous enough to leave without a note. The kit plan (`studio-notes/kit-plan-v2.md`) and `LEAD-ORDERS.md` were not read, since the order allows only tickets, `freeze-list.md`, `GAPS.md` and `reviews/rung-audit-1.md`; they may state demand I did not see.
