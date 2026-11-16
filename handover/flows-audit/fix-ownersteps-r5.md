# fix-ownersteps-r5 (fixer log)
Edited only OWNER-STEPS-q16-rows.md. Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-os-r5/. Nothing ran.
- A (crossread item 2): L4 now names all six fill_flows placeholders (fill_flows.py lines 65-72, README lines 9-11); DESK_ALERT_TO rewritten as a literal written by fill_flows, as the lead's statement (ORDERS.md line 81, README line 32); L5 uses the tool's own check command (README ~59 on), not a hand search.
- B (item 4): port 5690 named once, after L6, per DECISIONS line 7.
- C (item 3): lead-only note that realrun-v3 lines 95/103/104 are replaced by decision 2 (DECISIONS line 3).
- D (adversarial items 1, 2): P1, P2 added as "proposed, waiting for the lead (Q22)".
- Owner part unchanged.
Not fixed: exact check command line, which placeholders occur in the real flows, column name lead_key, mailbox emptying method: all left UNVERIFIED for the lead (not read from files).
- Q21 (lead answer, ORDERS.md line 131): Step A cost line now reads "up to 3 live model calls under the owner's standing credits yes; no US$0 claim" (the old US$0 expectation removed); DESK_ALERT_TO route stated as fill_flows literals, frozen tool, no n8n setting change, check = no node reads $env. Saved runs: the sheet has no deletion promise (grep found none); the lead's own optional clean-up is not written in the sheet, as ordered.
