# fix-f1-r3: CLAIMS-TABLE.md after reader review round 3 (final pass)

Not done / not verified first:
- No fresh reviewer read the new text (final pass, no further review rounds). Wording is mine, unchecked by a second reader.
- Owner-action explanations (laptop settings, app passwords, 6-digit challenge) are summaries; I did not re-read OWNER-STEPS-realrun-v3.md in full. The Start-here part points to it for details.
- F-01 itself still cannot be read (review-codebase-1.md absent); described only from AGENT-SCOPE:20 and ORDERS.md.
- The "legend repeats glossary" nit was left (Legend items 1 to 4 stay).
- Row 16 "no expiry" reworded to "no deletion step in the flows we read"; I did not search the flows for a prune job.
- "Coordinator" rename was applied to Start-here, glossary, checks, decisions and Table 1/2 rows; the verbatim lane sections (from "# LANE A") were not edited, they still say "the lead". Text meant to be pasted into the video keeps "the lead" (= lead record), stated in the glossary.

Done:
- Purpose paragraph first; history sentence removed from the opening.
- Owner's actions in order (written yes, laptop settings, typed confirmations, watch and post, revoke app passwords, delete contacts), each explained; order of work for agent and coordinator kept.
- "lead" split: lead record / coordinator, defined; applied across the top part and mixed rows.
- Short list of rows and scenes that can break the take (rows 3, 7, 39, 10, 11, 23, 29, 6, 9, 15, 22, 25, 27, 28, 13).
- Labels defined before use: P3 alias dropped (checks P1, P2, P4a, P4b, P4c); UNTRACED vs UNSUPPORTED; node; lane A; D1 to D3; Q4 to Q8 and ORDER 013; 17:05Z; IF plus alert; stand-in drop; branch; lease; RELAYED-ONLY name tied to the lane wording; SUPPORTED = "file text says so; not run".
- Contacts-stay conflict stated per coordinator order 017 with the two disagreeing files; F-01 explained.
- n8n SQLite statement tied to one earlier smoke run; "the lead-table database".
- D1 line fixed: exceptions rows 3, 25, 27, 28 named.
- Count chain 79 to 76 to 74 explained; script saved as handover/flows-audit/claims-count.py and cited with the command.
- The 14 lane B files listed (15 paths because V5-README.md has two copies).
- "contact number" now "the id HubSpot gives each contact"; stray timestamp lines removed (2).

Evidence (command: python3 -I handover/flows-audit/claims-count.py handover/flows-audit/CLAIMS-TABLE.md):
- verdicts: SUPPORTED 114, RELAYED-ONLY 69, OVERSTATED 49, UNSUPPORTED 25, UNTRACED 70, total 327 (lane A 97, B 226 + X 4)
- offenders: 0 (7 cells and 8 pipes per claim row; 11 cells in 77 to-do rows); 327 ids, 327 unique.
Files changed: CLAIMS-TABLE.md, claims-count.py (new), fix-f1-r3.md. lanes13/claims-A/B untouched.
