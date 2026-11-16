# Glossary for the lane pages (L1, L2, L3, L4, L5b, t19 pages, critical-path-r1). Written 16 Nov 2026 by the system-map session. Only meanings found in files are given; the rest say "meaning not recorded".

## Who is who (one place; details in the lines below)
| name | what it is | owner |
|---|---|---|
| lead session | the Claude session that gives the system-map session its orders | Claude session |
| studio lead | the Claude session that does the technical steps on the take and messages the owner | Claude session |
| core-hardening | a separate Claude session that owns V5 and the held pages | Claude session |
| studio head | the human who runs the studio (whether this is the owner is NOT SETTLED) | human |
| owner | the human at the laptop | human |

## Unknown: do not use in new text (meaning not recorded; ask the lead session)
D-04, D-05, F-008, LP-n, GO-1, k1b, KeyOk, Claim, WARDEN, film-v5, Mode A, stage.journal, job keys (STORE, RETRY, NOTICE, FILTER, COUNTER, LOG, OTHER). Nobody has filled these in yet.


- **lane** = one helper Claude session given one slice of the review to read; its output file is a **lane page** (L1, L2, L3, L4, L5b are the lane names). **held pages** = pages the lead session or core-hardening own; this session only records digests of reads of them and does not edit them. **t19 pages** = the work/t19-*.md pages about test T19 (send the same made-up lead twice; expect 1 mail, 1 HubSpot write, 1 stored row). **critical-path-r1** = work/critical-path-r1.md, the page that answers when the first filmed take can happen. **system-map session** = this Claude session, which writes only inside handover/system-map/.
- **OWNER-ONLY** = a file the owner may open and nobody else; it may hold secrets, so helpers never open it (work/OWNER-ONLY.txt lists them; that file does not exist yet).
- **Where to ask** for any term marked 'meaning not recorded': the lead session (the Claude session that gives this session its orders). The lead session passes studio-specific terms on to the studio lead.
- **take** = one recorded run of the lead-intake demo, filmed on made-up data (OWNER-VIEW.md, "Words"). The video claim is only "a lead sent twice with the same id is processed once".
- **lead record** = one made-up sales contact record (older pages write just "lead" for it). **lead id** = that record's id. **lead session** = the Claude session that gives the system-map session its orders (older pages write just "the lead" for it; it is not the same as the studio lead). **studio lead** = the Claude session that does the technical steps on the take and messages the owner. **HubSpot** = the sales-contact tool the demo writes contacts to. **one-store decision** = the decision file about keeping the demo's stored leads in one place. **studio head** = the human who runs the studio (whether this is the owner is NOT SETTLED). **owner** = the human at the laptop who gives the yes; whether they are also the studio head is unsettled. **core-hardening** = a separate Claude session that owns the held pages.
- **DECISION line N** = line N of the one-store decision file. Two copies exist and disagree (root file of 20 lines vs inputs/DECISION-one-store.md of 28 lines); which is the source is an open question for the lead session. A line number is only checkable against the file the page names; where a page does not name it, treat the cite as UNVERIFIED.
- **decision 1..12 (16 Nov)** = the 12 items of inputs/DECISIONS-2026-11-16.md, known second-hand only (summary in STATUS-BOARD.md).
- **READ / SKIMMED / NOT-READ / OWNER-ONLY** = how much of a file a lane read: all of it / part of it / none of it (draw no conclusion) / a file only the owner may open.
- **UNVERIFIED** = stated but not checked against a file or a command output. **NOT VISIBLE** = the lane could not see it. **NOT FOUND** = searched, not present. **NOT SET / TO DO / meaning not recorded** = nobody has filled it in yet.
- **job keys** (STORE, RETRY, NOTICE, FILTER, COUNTER, LOG, OTHER) = labels a lane gave each job it listed; meaning of each beyond its name: not recorded.
- **claim type** (dead, idle, ops, ...) = the lane's own label for a finding; the full list: not recorded.
- **mf_leads** = a table name for stored leads. UNVERIFIED; not confirmed in any file this session holds.
- **stage.journal, Mode A, film-v5 / real-v5, WP6 P11, D1 order, K1..K6, go1/v3/v4** = meaning not recorded.
- **Severity** in a finding row = the lane's own label; the lead session has not confirmed any (cells say "Lead (unconfirmed)" where changed).

## Added 16 Nov 2026 (from cold reads 1035-1038; every meaning below is marked as what is recorded, not confirmed)
- the take: the one filmed run of the lead-intake demo on made-up data (meaning from decision 1 of 16 Nov, second-hand). It is also used loosely for the preparation steps; pages should say "the take" only for the filmed run.
- desk, rig, SWEEP.md, ONE-PLACE-TABLE, ORDER 002, PLAN section 5.2, C1, K1b, P3, design 12, the spike, smk_count, drive.py, STOP class, F8, freeze input: meaning not recorded. Do not rely on a page's use of them until the studio lead defines them.
- T19: the plan's test that sends the same made-up lead twice and expects one mail, one HubSpot write and one stored row (see work/t19-gap-facts.md "Purpose").
- row N: on a page with a table, "row N" means that page's table row N unless the page says "TAKE-BLOCKERS row N" (TAKE-BLOCKERS.md). Pages that break this rule are listed as findings, not fixed.
- verdict words in L6 (OWNER, NEEDED, CRM-COULD-DO, DUPLICATE, NOT-NEEDED): meaning not recorded.
- amendment paragraphs ("r11", "r13" and so on): paragraph labels, not file versions; the one that says it wins is the one to read.
