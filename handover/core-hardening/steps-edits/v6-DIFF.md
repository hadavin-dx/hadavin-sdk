# v6 vs v5: what changed (short)

Added
- Step 0: HubSpot delete check (ORDER 017): `--plan` first, key from a named secret file through `HUBSPOT_PROBE_TOKEN`, 7 calls, US$0, owner pastes the PASS/FAIL table; says what the table tells the lead.
- The run card (12 rows with defaults) so open items that decide owner actions are visible in the sheet.
- One table of every owner step: step | who | typed or clicked | where | expected (ORDER 019), with "open" rows.
- Intro paragraph limiting what lead messages may change; statement that the owner creates no accounts, mailboxes, keys, HubSpot account and does not start Docker.
- Words: contact, lead id, model settings file, run settings file, spending backstop, proof screen, label `demo`, crash-safe, independent count, saved runs, company address, hook door.
- Step E: how long, finished sign, stuck rule; exit codes for too-fast answer and failed login; TAKE_MIN_ANSWER_SECONDS; rare exit-3/120 cases.
- Step F: consequences of an early `end`, HubSpot search for the run name.
- Step G: Trash check, subject filter. Step I: crop tool, app-password names from the lead, retire check covers 2 of 4 secrets, who removes what, mapping question for private apps.
- Step J: two more must-not-say lines (one database, hard spend limit).

Changed
- Run name needed before step A (setting `TAKE_TAG`); two settings files named separately.
- Counts: A and B one each; C one or unknown with alert (was "exactly 3 and 3").
- C.3 n8n sign-in: no new login, only if the run card says; no "new, empty database" claim.
- "example.com: nothing is sent" removed; mail path declared unexplained.
- Cost wording: at most one paid call per test person, recorded before; not "never paid twice".
- Latest start 18:14:40 UTC = 23:44:40 IST (was "about 18:15").
- Post: latest time Wed 25 Nov 15:00 UTC = 20:30 IST; aim Wed 18 Nov (ORDERS 017).
- Cross-reference "step 6" fixed to item 5. Rehearsal gate marked as the lead's own. Empty Trash checked first.
- "(path not checked)" tags on each click path in B, C, G, I; steps from v3 only are tagged "not in the lead's done-or-owner-only list".
- "What is not proven yet" shortened.

Removed
- "The studio lead's instructions win over this sheet."
- "Choose a new n8n password" and "create an owner login".
