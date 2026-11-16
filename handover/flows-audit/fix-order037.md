# fix-order037 log (2026-11-16)
Rule (ORDERS.md line 176, item 3 line 177): one filled flow set, real trial-account credential in every phase, no stand-in HubSpot swap.
- QUEUE.md, PLAN-005.md, fill_flows/README.md searched for: stand-in, dummy, placeholder credential, second filled set, refill, rehearsal not in real HubSpot. No text describing a HubSpot credential swap or a refill with the real credential was found.
- fill_flows/README.md step 1 (walk-through): added an ORDER 037 note (one set, real credential, partial fill is only for SUB_WORKFLOW_ID).
- QUEUE.md line 15 (F5): added a note that 'stand-in CRM' means the film-v5 test CRM program, not a credential swap; label need UNVERIFIED.
- PLAN-005.md: no change (only says HubSpot is not visible here).
- Stale text in other files (not edited): see report; CLAIMS-TABLE.md uses 'stand-in' only for film-v5 test programs (not a credential swap).
