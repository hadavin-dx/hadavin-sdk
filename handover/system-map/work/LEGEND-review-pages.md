# Key to the words on the review and resolve pages in work/
This page is a key to the words used on those pages. It is not a finding. work/GLOSSARY.md is the fuller list of defined words; if this page and the glossary differ, the glossary wins.

Every statement is UNVERIFIED unless the same sentence or row names a file and line the writer opened, or says "checked: <command> gave <result>". "OK" or "confirmed" alone does not count. Separately, READ, SKIMMED and NOT-READ say how much of a file a lane opened; they are defined in work/GLOSSARY.md.

- lead session: the Claude session that gives orders to this session (the system-map session). It is not a sales lead.
- studio lead: the Claude session that does the technical steps (running n8n, the rehearsal, the take) and is the only one that messages the owner.
- owner: the human who films and posts.
- studio head: UNVERIFIED; read it as the studio lead only after the studio lead confirms. Do not use it in new text; write "owner" or "studio lead".
- lead-intake demo: the demo that takes a made-up sales contact (a lead record), stores it once, writes one contact in HubSpot (a sales-contact tool) and sends one mail.
- n8n: the ready-made tool that runs the steps of the lead-intake demo as flows.
- take: the one filmed run of the lead-intake demo on made-up data, run through n8n.
- desk: meaning not recorded (no file read says whether it is a demo or a program). The lead session's decision list may mention it as retired from the take (UNVERIFIED). Do not use it in new text.
- decision list (work/decision-list-for-lead.md): the page where the system-map session asks the lead session for a fact or a choice it cannot settle itself.
- SWEEP.md and ONE-PLACE-TABLE.md: the two summary pages. The system-map session makes them by running the program tools/write_outputs.py, which reads the lane pages (L1 to L6) and writes both. Do not edit these two pages by hand: to change one, change the lane page it comes from (or the program) and the system-map session reruns the program. Both are held pages (pages another session owns; the system-map session reads them and never edits them, see work/GLOSSARY.md).
- lane (L1..L6): one helper Claude session given one slice of the review to read (a cold read, with no other context); its output file is a lane page, work/L<n>.md (see work/GLOSSARY.md).
- Old labels STORE, RETRY, NOTICE, FILTER, COUNTER, LOG and OTHER appear in old pages. Look them up in work/GLOSSARY.md and do not write them in new text.
- verdict words in resolve pages: PROPOSE FIX = the finding is right and a fix is written; CONTEST = the finding is rejected with evidence; ESCALATE = the system-map session cannot decide because a fact or a choice is needed from the lead session; it asks the lead session in work/decision-list-for-lead.md, and the resolve page keeps the item open until the lead session answers (for choices only the owner can make, the lead session passes it on through the studio lead); DECLINE = a Nit, no fix.
- reviewer codes (letters before the finding number): CD = codebase-details reviewer, ZO = zoom-out reviewer, DE = design reviewer, CO = comprehension reviewer. Older pages may use a single letter: Z = zoom-out, D = design, C = comprehension, K = codebase-details. A code like CD-B1 means finding B1 of the codebase-details reviewer (Blocker number 1), not a design finding; DE-M3 means Major 3 of the design reviewer.
- severity: Blocker = a reader cannot act or will act wrongly; Major = a reader may be misled; Nit = style only. B, M and N in a code are the first letters of these.
- NOT RECORDED = no file the writer read states this fact, so it is unknown; it does not mean the fact is false. (NOT-READ is different: it says a lane opened none of a given file.)
- Times: UTC first, IST (UTC+5:30) second.
