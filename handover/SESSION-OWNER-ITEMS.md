# Owner items from plan A18 (v4.3), for the lead to carry in one message (order 150). Source: plan-v4-3.md section 11 (lines 574-615) and the OWNER DECISIONS block

## OWNER DECISIONS still open (order 145 item 3; the lead carries them, nobody decides them here) [AUTHOR]
- **O3 reconciliation.** Bible rule R368 asks us to compare the messages we received with the sender's own list of ids. v1 does NOT do this (section 4.5). Until the owner answers, no quote promises it, and the quote sentence of section 4.5 applies.
- **O4 where the door runs in pilot and prod.** In v1 the door runs only in a demo-stage server. Hosting it for pilot or prod is the deferred ticket AK-G16. Until the owner answers, no quote prices the door's hosting ("door stack: NOT PRICED").
- Eight more owner items (O1, O5-O11) and every lead item are in section 11.

## Section 11 rows that name an owner (O1, O5-O11)
Each table is ranked: the item needed earliest comes first. The ids are labels only (O = owner item, L = lead item) and are cited elsewhere in this file. **There is no O2** (plan v4.1's two licence items became one item, O1) and no L1 is open (closed by order 145 item 1); the ids are kept stable because reviews and order 145 cite them. [AUTHOR: note moved above the table]
| 1 | O7 | P5b2 (built, PR 85): keep, or replace by ast-grep rules (a cut also rewrites P5c's Depends-on, plan-v3.md:149). Gain if replaced: less code of our own to maintain; loss: the built class judgements and the PR 85 work, plus an amendment [AUTHOR] | the PR 85 merge, then P5c build start | default: keep as built |
| 2 | O8 | P6b1 (built, PR 86): keep, or turn into a config or doc check. Gain if changed: less code; loss: the llm kind no longer refuses a training-allowed provider setting by itself [AUTHOR] | the PR 86 merge | default: keep as built |
| 3 | O10 [AUTHOR] | P5a's codes table, validation text and mutant file as stdlib enum, pydantic and nothing (order 70 item 3 "approved in principle"; order 70 item 3 also says no owner yes is needed because the code is unbuilt, so this item may be closed by the lead: lead item L9 asks) | P5a build start | default: CUT-TO-CONFIG+GLUE as order 70 item 3 plans |
| 4 | O11 [AUTHOR] | the dated exception "Postgres is the only pilot and prod store for inbound sources, spend reservations and multi-tenant row-level security", review_by 2027-01-31, with SQLite (P7l) as the named outline (section 6.2) | the first pilot | recommend: yes, with the date |
| 5 | O1 | the licence line of section 4.7, and whether Hadavin may build or run flows inside a client's n8n for a fee | the first quote that names n8n | default: no quote names n8n until he or a lawyer confirms |
| 8 | O5 | Activepieces shown as an option | the next options list for a client | default: shown, no pack |
| 9 | O9 | lift the deferral of AK-G15, AK-G1, AK-G16 (each separately). AK-G2 is NOT deferred (it is ACTIVE, `freeze-list.md:48`); its start is lead item L10 [AUTHOR] | work item 9.5 | default: stay deferred |
| 10 | O6 | a live Make trial for T5 needs a real account | a Make pack | default: no live Make trial |
| 1 | L9 | the two-vocabulary rule of section 0.5 (ruling 1 named four words; R448 needs its tokens in the rung table); and whether O10 needs the owner at all (order 70 item 3 says not) [AUTHOR] | the freeze read | confirm; close O10 as a lead decision |
| 10 | L11 [AUTHOR] | wording and date of the Postgres dated exception (section 6.2), for the owner's yes (O11) | the first pilot | review_by 2027-01-31, as the llm exception |
