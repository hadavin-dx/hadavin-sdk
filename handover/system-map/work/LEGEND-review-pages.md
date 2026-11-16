# Legend for the review and resolve pages in work/
Read this first. It is a key, not a finding. Words are defined in work/GLOSSARY.md; if this page and the glossary differ, the glossary wins.

Rule for "UNVERIFIED": every statement on a review or resolve page is UNVERIFIED (stated, not checked against a file or command output) unless the same sentence or table row gives a file name and line number that the writer opened, or says "checked: <command> gave <result>". A page that only says "OK", "confirmed" or "read" with no file and line does not count as saying otherwise. Coverage words are separate: only READ, SKIMMED and NOT-READ say how much of a file a lane opened (see work/GLOSSARY.md); no other word is a coverage word.

- lead session: the Claude session that gives orders to this session (the system-map session). It is not a sales lead.
- studio lead: the Claude session that does the technical steps (running n8n, the rehearsal, the take) and is the only one that messages the owner.
- owner: the human who films and posts.
- studio head: an older name for a person role; nobody is confirmed to hold it. Treat as "unknown". Use "owner" in new text.
- lead-intake demo: the demo that takes a made-up sales contact (a lead record), stores it once, writes one contact in HubSpot (a sales-contact tool) and sends one mail.
- n8n: the ready-made tool that runs the steps of the lead-intake demo as flows.
- take: the one filmed run of the lead-intake demo on made-up data, run through n8n.
- desk: the older demo program; the lead session's decision list says it is retired from the take (UNVERIFIED). Decision list: work/decision-list-for-lead.md.
- SWEEP.md and ONE-PLACE-TABLE.md: the two summary pages. The system-map session makes them by running the program tools/write_outputs.py, which reads the lane pages (L1 to L6) and writes both. Do not edit these two pages by hand: to change one, change the lane page it comes from (or the program) and the system-map session reruns the program. Both are held pages (read, not edited, by this session).
- lane (L1..L6): one cold read of a group of repository files, written to work/L<n>.md.
- job key (STORE, RETRY, NOTICE, FILTER, COUNTER, LOG, OTHER): a label for one job the system does. Meanings are not recorded; see work/GLOSSARY.md before using one. Do not use them in new text.
- verdict words in resolve pages: PROPOSE FIX = the finding is right and a fix is written; CONTEST = the finding is rejected with evidence; ESCALATE = the system-map session cannot decide because a fact or a choice is needed from the lead session; it asks the lead session in work/decision-list-for-lead.md, and the resolve page keeps the item open until the lead session answers (for choices only the owner can make, the lead session passes it on through the studio lead); DECLINE = a Nit, no fix.
- reviewer codes (letters before the finding number): CD = codebase-details reviewer, ZO = zoom-out reviewer, DE = design reviewer, CO = comprehension reviewer. Older pages may use a single letter: Z = zoom-out, D = design, C = comprehension, K = codebase-details. A code like CD-B1 means finding B1 of the codebase-details reviewer (Blocker number 1), not a design finding; DE-M3 means Major 3 of the design reviewer.
- severity: Blocker = a reader cannot act or will act wrongly; Major = a reader may be misled; Nit = style only. B, M and N in a code are the first letters of these.
- NOT RECORDED = the fact was not found in the files read; it is not a statement that it is false.
- Times: UTC first, IST (UTC+5:30) second.
