# Glossary for the system-map pages (live text; no amendment paragraphs live here)
Three different things, never mixed: lead session = the Claude session that gives orders to the system-map session; studio lead = the Claude session that does the technical steps and is the only one that messages the owner; owner = the human at the laptop (older pages also say "studio head"; whether that is the same person is UNVERIFIED, so do not equate them). The word "lead" alone is never used for a session in new text; for a sales contact write "lead record" or "lead id".
This glossary serves the pages in handover/system-map/. They map what the lead-intake demo needs before one filmed run (the take) can happen, for the studio lead (a Claude session) and the owner (the human).
What the demo does: the lead-intake demo takes a made-up sales lead, stores it once, writes one HubSpot contact and sends one mail. The take is the filmed run that shows one claim: a lead sent twice with the same id is processed once.
More terms: V5 is defined once, in the Files table below. T19 and D-04 are defined once each, in "Words used on the pages" below. Held pages = pages another session owns; the system-map session reads them but never edits them (list in ORDERS.md). Digest = the system-map session's one-line note of a helper agent's report, in work/agent-reports-batch4.md. Cold read = a helper agent that reads one page with no other context and lists what it cannot follow. Real-run file = a file from a run on real accounts; the rule for it is "Real-run files" under "Rules for writing pages". UNVERIFIED (from a hand-back) = a helper agent said it, and nobody has checked the file.
Written Mon 16 Nov 2026 by the system-map session.

## Rules for writing pages
- Only meanings found in files are given. Where no file gives a meaning, the entry says "meaning not recorded"; the Unknown table says whom to ask.
- "Line N" on a page means line N of the file that page names; if no file is named, mark the cite UNVERIFIED.
- For the one-store decision write "DECISION line N (root copy)" or "(inputs copy)"; root copy = handover/system-map/DECISION-one-store.md, inputs copy = handover/system-map/inputs/DECISION-one-store.md.
- Two copies of a file: quote both side by side and say the current copy is unknown.
- Real-run files: a real-run file is a file from a run on real accounts. No helper opens one. The list of such files is work/OWNER-ONLY.txt (not created yet); until it exists, open no real-run file without the lead session's yes. Only the owner opens them.
- Old text is in GLOSSARY-history.md (ignore it).

## Who orders whom (read this first)
The lead session gives orders to the system-map session (this one) through ORDERS.md. The system-map session writes only inside handover/system-map/ and reports through files and STATUS-BOARD.md. The studio lead is a different Claude session that does the technical steps and is the only session that messages the owner; the system-map session never messages the owner. The core-hardening session owns V5 and the held pages.

## People and sessions (one table)
| name | what it is | kind |
|---|---|---|
| lead session | the Claude session that gives the system-map session its orders. Old pages say "the lead" or "the lead decides"; read that as lead session. New text must say "lead session" and never "lead" alone for a session. It is not the studio lead. For a sales contact write "lead record" or "lead id" | Claude session |
| studio lead | the Claude session that does the technical steps on the take and messages the owner | Claude session |
| core-hardening | a separate Claude session that owns V5 and the held pages | Claude session |
| system-map session | this Claude session; it writes only inside handover/system-map/ | Claude session |
| lane | one helper Claude session given one slice of the review to read (L1 to L6); its output file is a lane page | Claude session |
| studio head | the word older pages use for a human who runs the studio; not named. UNVERIFIED whether it is the owner: do not equate them. Use "owner" for the written yes; do not use "studio head" in new text | human |
| owner | the human at the laptop who gives the written yes | human |

## Files (one table)
| name | path | what it holds |
|---|---|---|
| held pages | listed in the table "Held pages" below | pages this session only digests and never edits |
| V5 | inputs/OWNER-STEPS-realrun-v5-core-hardening.md | the owner's steps A to J for the filmed run. This row is the one definition of V5. Why it is called v5: not recorded. Other pages say "V5 (see work/GLOSSARY.md)" |
| decisions of 16 Nov | inputs/DECISIONS-2026-11-16.md | 12 items; known second-hand only (the original is held by the lead session) (summary in STATUS-BOARD.md) |
| one-store decision | DECISION-one-store (two copies: root file of 20 lines, inputs/DECISION-one-store.md of 28 lines) | where the demo keeps stored leads. The lead-intake demo = the demo that takes a made-up sales lead, stores it once, writes one HubSpot contact and sends one mail. Which of the two copies is current: the lead session has not answered; cite both. "DECISION line N" means line N of that file |
| OWNER-ONLY | work/OWNER-ONLY.txt (not created yet) | would list the real-run files only the owner opens; the rule is "Real-run files" under "Rules for writing pages" |
| t19 pages | work/t19-*.md | pages about test T19 |
| critical-path-r1 | work/critical-path-r1.md | when the first filmed take can happen |

## Held pages
Owners are as recorded in the table but unconfirmed; ask the lead session. This session only writes a one-line digest of each cold read and never edits these pages.
| page | owner |
|---|---|
| OWNER-VIEW.md | core-hardening session |
| OWNER-RUN-DAY-CARD.md | core-hardening session |
| OWNER-CLEANUP-CARD.md | core-hardening session |
| LEAD-PAGE.md | lead session |
| TAKE-BLOCKERS.md | lead session |
| SWEEP.md | lead session |
| MASTER-MAP.md | lead session |
| README.md | lead session |
| QUESTIONS.md | lead session |
| QUEUE.md | lead session |
| ORDERS.md | lead session |
| inputs/ (folder) | lead session |
| tools/ (folder) | lead session |
| tests/ (folder) | lead session |

## Words used on the pages (one definition each)
- **take**: one recorded run of the lead-intake demo on made-up data. The one claim it makes: "a lead sent twice with the same id is processed once". Say "take" only for the filmed run, not for preparation.
- **lead record**: one made-up sales contact. **lead id**: that record's id. **HubSpot**: the sales-contact tool the demo writes contacts to. **n8n**: the tool that runs the demo steps.
- **T19**: the test that sends the same made-up lead record twice and expects one mail, one HubSpot write and one stored row in the demo's database (which store: see work/t19-gap-facts.md "Purpose"). Not run yet.
- **row N**: row N of the table on that page, unless the page writes "TAKE-BLOCKERS row N".
- **READ / SKIMMED / NOT-READ / OWNER-ONLY-FILE** (a read status of a file, not the file itself): READ = a lane opened all of it. SKIMMED = it opened part. NOT-READ = it opened none, so it says nothing about the file. OWNER-ONLY-FILE = it did not open the file because only the owner may.
- OWNER-ONLY (the list file work/OWNER-ONLY.txt, see Files table) and OWNER-ONLY-FILE (a read status) are two different things.
- **UNVERIFIED**: stated, not checked against a file or command output. **NOT VISIBLE**: the lane could not see it. **NOT FOUND**: searched, not present. **NOT SET / TO DO**: nobody has filled it in.
- **Severity** in a finding row: the lane's own label; the lead session has confirmed none.

- **D-04**: one row id, defined in drift/REPORT.md (table row D-04): the public post would say more than the written decisions and the evidence allow. The question to the lead session about it is row D-04 in work/decision-list-for-lead.md. The one wording that is allowed is "a lead sent twice with the same id is processed once" (ORDERS.md, lead session answer of 13:08 UTC). D-04 is not a rule about processing and not a test; any older page that uses it for something else is wrong. D-04 blocks the post, not the take.
- **laptop lead**: used on SWEEP.md and ONE-PLACE-TABLE.md for the one who gave the written work order (ORDERS.md) to this session. That matches "lead session", but no file says so; in new text write "lead session". Meaning of "laptop lead" itself: not confirmed.

## Terms with no recorded meaning
Rule: never use these terms in new text. If an older page uses one, write "term (undefined)" and do not guess; mf_leads may be written "stored-leads table (name unconfirmed)". Rows marked "no live page" need no action. "Pages" = up to three pages that use the term now (found by search on 16 Nov).
Who can answer: ask the lead session (the Claude session that gives the system-map session its orders; it passes studio questions to the studio lead). Only the studio lead may message the owner; the system-map session never does.
| term | pages |
|---|---|
| mf_leads (probably a stored-leads table; UNVERIFIED) | DECISION-one-store.md, MASTER-MAP.md, ONE-PLACE-TABLE.md |
| stage.journal | DECISION-one-store.md, MASTER-MAP.md, ONE-PLACE-TABLE.md |
| D-05 | LEAD-PAGE.md, ORDERS.md, QUESTIONS.md |
| F-008 | FINAL-CROSSCHECK.md, LEAD-PAGE.md, MASTER-MAP.md |
| LP-n | ORDERS.md, agent-reports-batch4.md, decision-list-for-lead-history.md |
| GO-1 | MASTER-MAP.md, SWEEP.md, L2.md |
| k1b | MASTER-MAP.md, ONE-PLACE-TABLE.md, SWEEP.md |
| K1b | MASTER-MAP.md, L5a.md, L5b-history.md |
| KeyOk | agent-reports-batch4.md, row1-builder-brief-history.md, t19-and-stored-data-steps.md |
| WARDEN | MASTER-MAP.md, L5b-history.md, L5b.md |
| F8 | SWEEP.md, L3c.md, agent-reports-batch3.md |
| A4 | LEAD-NOTICE-batch-1.md, agent-reports-batch4.md, critical-path-history.md |
| A13 | agent-reports-batch4.md, decision-list-for-lead-history.md, decision-list-for-lead.md |
| C1 | LEAD-PAGE.md, MASTER-MAP.md, ONE-PLACE-TABLE.md |
| P3 | SWEEP.md, L1c.md, L4.md |
| design 12 | MASTER-MAP.md, SWEEP.md, L5a.md |
| the spike | SWEEP.md, L5a.md, merged-findings.md |
| smk_count | agent-reports-batch4.md, t19-row-and-steps-r3.md |
| drive.py | agent-reports-batch4.md, row-dm-plain.md, t19-row-and-steps-r3.md |
| fill_flows.py | LEAD-PAGE.md, MASTER-MAP.md, ONE-PLACE-TABLE.md |
| STOP class | agent-reports-batch4.md, t19-row-and-steps-r3.md |
| freeze input | agent-reports-batch4.md, t19-gap-facts.md, t19-gaps-r2.md |
| stand-in | LEAD-PAGE.md, MASTER-MAP.md, ONE-PLACE-TABLE.md |
| refusal | FINAL-CROSSCHECK.md, LEAD-PAGE.md, MASTER-MAP.md |
| Route config | FINAL-CROSSCHECK-history.md, FINAL-CROSSCHECK.md, LEAD-PAGE.md |
| desk | DECISION-one-store.md, FINAL-CROSSCHECK.md, LEAD-PAGE.md |
| rig | ARCHITECTURE-AUDIT-CHECKLIST.md, DECISION-one-store.md, FINAL-CROSSCHECK.md |
| film-v5 / real-v5 | no live page |
| Mode A | DECISION-one-store.md, MASTER-MAP.md, L1.md |
| WP6 P11 | DECISION-one-store.md, MASTER-MAP.md, ORDERS.md |
| D1 order | MASTER-MAP.md, L1.md, agent-reports-batch4.md |
| K1 to K6 | no live page |
| go1/v3/v4 | agent-reports-batch4.md |
| ONE-PLACE-TABLE | FINAL-CROSSCHECK.md, MASTER-MAP.md, ONE-PLACE-TABLE.md |
| ORDER 002 | ORDERS.md, PLAN-002.md, REPORT.md |
| PLAN section 5.2 | L6.md, agent-reports-batch4.md |

Job keys: STORE, RETRY, NOTICE, FILTER, COUNTER, LOG, OTHER (meanings not recorded; do not use). Claim types: dead, idle, ops (meanings not recorded; do not use). L6 verdict words: OWNER, NEEDED, CRM-COULD-DO, DUPLICATE, NOT-NEEDED. Claim (as a flow step) is explained in handover/system-map/work/not-checked-r2.md, section Terms.

## Lanes (one line each)
L1, L2, L3, L4, L5 and L6 are the lane names (meaning taken from the lane pages' headings, not confirmed: L1 to L4 read the core-hardening files in four slices, L5 the flow files, L6 whether each part is needed). Each lane page (work/L<n>*.md) says in its own first lines what it covers; this glossary does not repeat that. L5a/L5b is an unconfirmed split of L5 (UNVERIFIED, from a hand-back); do not use it until confirmed.
