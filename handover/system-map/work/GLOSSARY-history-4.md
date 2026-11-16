# Glossary for the system-map pages (live text; no amendment paragraphs live here)
This glossary serves the pages in handover/system-map/. They map what the lead-intake demo needs before one filmed run (the take) can happen, for the studio lead (a Claude session) and the owner (the human).
Written Mon 16 Nov 2026 by the system-map session.

## Rules for writing pages
- Only meanings found in files are given. Where no file gives a meaning, the entry says "meaning not recorded"; the Unknown table says whom to ask.
- "Line N" on a page means line N of the file that page names; if no file is named, mark the cite UNVERIFIED.
- For the one-store decision write "DECISION line N (root copy)" or "(inputs copy)"; root copy = handover/system-map/DECISION-one-store.md, inputs copy = handover/system-map/inputs/DECISION-one-store.md.
- Old text is in GLOSSARY-history.md (ignore it).

## Who orders whom (read this first)
The lead session gives orders to the system-map session (this one) through ORDERS.md. The system-map session writes only inside handover/system-map/ and reports through files and STATUS-BOARD.md. The studio lead is a different Claude session that does the technical steps and is the only session that messages the owner; the system-map session never messages the owner. The core-hardening session owns V5 and the held pages.

## People and sessions (one table)
| name | what it is | kind |
|---|---|---|
| lead session | the Claude session that gives the system-map session its orders (older pages write "the lead"; it is not the studio lead; "lead" alone is banned for a session; for a sales contact write "lead record" or "lead id") | Claude session |
| studio lead | the Claude session that does the technical steps on the take and messages the owner | Claude session |
| core-hardening | a separate Claude session that owns V5 and the held pages | Claude session |
| system-map session | this Claude session; it writes only inside handover/system-map/ | Claude session |
| lane | one helper Claude session given one slice of the review to read (L1 to L6); its output file is a lane page | Claude session |
| studio head | the human who runs the studio; not named. Use "owner" for the written yes; do not use "studio head" in new text | human |
| owner | the human at the laptop who gives the written yes | human |

## Files (one table)
| name | path | what it holds |
|---|---|---|
| held pages | listed in the table "Held pages" below | pages this session only digests and never edits |
| V5 | inputs/OWNER-STEPS-realrun-v5-core-hardening.md | the owner's step list A to J for the filmed run |
| decisions of 16 Nov | inputs/DECISIONS-2026-11-16.md | 12 items; known second-hand only (summary in STATUS-BOARD.md) |
| one-store decision | DECISION-one-store (two copies: root file of 20 lines, inputs/DECISION-one-store.md of 28 lines) | where the demo keeps stored leads. Two copies exist (20 and 28 lines). Which one is current is open; the lead session has not answered. Until it does, cite both. "DECISION line N" means line N of that file |
| OWNER-ONLY | work/OWNER-ONLY.txt (does not exist yet) | would list files only the owner opens; helpers never open them |
| t19 pages | work/t19-*.md | pages about test T19 |
| critical-path-r1 | work/critical-path-r1.md | when the first filmed take can happen |

## Held pages (owner of each held page is unknown: core-hardening session or lead session; one row each; this session writes a one-line digest of what each cold read found and does not edit them)
| page | owner |
|---|---|
| OWNER-VIEW.md | core-hardening session (see the note above this table) |
| OWNER-RUN-DAY-CARD.md | core-hardening session (see the note above this table) |
| OWNER-CLEANUP-CARD.md | core-hardening session (see the note above this table) |
| LEAD-PAGE.md | lead session (see the note above this table) |
| TAKE-BLOCKERS.md | lead session (see the note above this table) |
| SWEEP.md | lead session (see the note above this table) |
| MASTER-MAP.md | lead session (see the note above this table) |
| README.md | lead session (see the note above this table) |
| QUESTIONS.md | lead session (see the note above this table) |
| QUEUE.md | lead session (see the note above this table) |
| ORDERS.md | lead session (see the note above this table) |
| inputs/ (folder) | lead session (see the note above this table) |
| tools/ (folder) | lead session (see the note above this table) |
| tests/ (folder) | lead session (see the note above this table) |

## Words used on the pages (one definition each)
- **take**: one recorded run of the lead-intake demo on made-up data. The one claim it makes: "a lead sent twice with the same id is processed once". Say "take" only for the filmed run, not for preparation.
- **lead record**: one made-up sales contact. **lead id**: that record's id. **HubSpot**: the sales-contact tool the demo writes contacts to. **n8n**: the tool that runs the demo steps.
- **T19**: the test that sends the same made-up lead twice and expects one mail, one HubSpot write and one stored row in the demo's database (which store: see work/t19-gap-facts.md "Purpose"). Not run yet.
- **row N**: row N of the table on that page, unless the page writes "TAKE-BLOCKERS row N".
- **READ / SKIMMED / NOT-READ / OWNER-ONLY-FILE**: (a read status, not the file). READ = a lane opened all of it. SKIMMED = part. NOT-READ = none, so the lane says nothing about it. OWNER-ONLY-FILE = a lane did not open it because only the owner may how much of a file a lane read: all / part / none (so the lane says nothing about that file) / a file only the owner may open.
- **UNVERIFIED**: stated, not checked against a file or command output. **NOT VISIBLE**: the lane could not see it. **NOT FOUND**: searched, not present. **NOT SET / TO DO**: nobody has filled it in.
- **Severity** in a finding row: the lane's own label; the lead session has confirmed none.

D-04 is not unknown: it is the rule that a lead sent twice is processed once (decision-list-for-lead.md, Reading notes).

## Unknown terms: do not use in new text
Each term has meaning not recorded in any file. Ask the lead session first (it passes studio terms to the studio lead), then the owner. If you meet one, write "term (undefined)" and do not guess. "Pages" = up to three pages that use it now (computed by search on 16 Nov).
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

Job keys: STORE, RETRY, NOTICE, FILTER, COUNTER, LOG, OTHER (meanings not recorded; they label what a flow step is for). Claim types: dead, idle, ops (meanings not recorded). L6 verdict words: OWNER, NEEDED, CRM-COULD-DO, DUPLICATE, NOT-NEEDED. Claim (as a flow step) is explained in work/not-checked-r2.md Terms.
The one-store decision's source copy is also unknown (same asking rule).

## Lanes (one line each)
L1, L2, L3, L4, L5 and L6 are the lane names (meaning taken from the lane pages' headings, not confirmed: L1 to L4 read the core-hardening files in four slices, L5 the flow files, L6 whether each part is needed). Each lane page (work/L<n>*.md) says in its own first lines what it covers; this glossary does not repeat that. L5a/L5b is an unconfirmed split of L5 (UNVERIFIED, from a hand-back); do not use it until confirmed.
