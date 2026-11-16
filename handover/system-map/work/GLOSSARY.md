# Glossary for the system-map pages (live text; no amendment paragraphs live here)
This glossary serves the pages in handover/system-map/. They map what the lead-intake demo needs before one filmed run (the take) can happen, for the studio lead (a Claude session) and the owner (the human).
Written Mon 16 Nov 2026 by the system-map session. Only meanings found in files are given. Where no file gives a meaning, the entry says "meaning not recorded" and the Unknown list says whom to ask (the lead session first, then the owner). "Line N" on any page means line N of the file that page names; if the page names no file, mark the cite UNVERIFIED. For the one-store decision write "DECISION line N (root copy)" or "(inputs copy)". Old text is in GLOSSARY-history.md (ignore it).

## People and sessions (one table)
| name | what it is | kind |
|---|---|---|
| lead session | the Claude session that gives the system-map session its orders (older pages write "the lead"; it is not the studio lead; never write "lead" alone) | Claude session |
| studio lead | the Claude session that does the technical steps on the take and messages the owner | Claude session |
| core-hardening | a separate Claude session that owns V5 and the held pages | Claude session |
| system-map session | this Claude session; it writes only inside handover/system-map/ | Claude session |
| lane | one helper Claude session given one slice of the review to read (L1 to L6); its output file is a lane page | Claude session |
| studio head | the human who runs the studio; not named. Use "owner" for the written yes; do not use "studio head" in new text | human |
| owner | the human at the laptop who gives the written yes | human |

## Files (one table)
| name | path | what it holds |
|---|---|---|
| held pages | OWNER-VIEW, OWNER-RUN-DAY-CARD, OWNER-CLEANUP-CARD, LEAD-PAGE, TAKE-BLOCKERS, SWEEP, MASTER-MAP, README, QUESTIONS, QUEUE, ORDERS.md, inputs/, tools/, tests/ | pages the lead session or core-hardening own; this session writes a one-line digest of what each cold read found and does not edit them |
| V5 | inputs/OWNER-STEPS-realrun-v5-core-hardening.md | the owner's step list A to J for the filmed run |
| decisions of 16 Nov | inputs/DECISIONS-2026-11-16.md | 12 items; known second-hand only (summary in STATUS-BOARD.md) |
| one-store decision | DECISION-one-store (two copies: root file of 20 lines, inputs/DECISION-one-store.md of 28 lines) | where the demo keeps stored leads; which copy is the source is Unknown. "DECISION line N" means line N of that file |
| OWNER-ONLY | work/OWNER-ONLY.txt (does not exist yet) | would list files only the owner opens; helpers never open them |
| t19 pages | work/t19-*.md | pages about test T19 |
| critical-path-r1 | work/critical-path-r1.md | when the first filmed take can happen |

## Words used on the pages (one definition each)
- **take**: one recorded run of the lead-intake demo on made-up data. The one claim it makes: "a lead sent twice with the same id is processed once". Say "take" only for the filmed run, not for preparation.
- **lead record**: one made-up sales contact. **lead id**: that record's id. **HubSpot**: the sales-contact tool the demo writes contacts to. **n8n**: the tool that runs the demo steps.
- **T19**: the test that sends the same made-up lead twice and expects one mail, one HubSpot write and one stored row (work/t19-gap-facts.md "Purpose"). Not run yet.
- **row N**: row N of the table on that page, unless the page writes "TAKE-BLOCKERS row N".
- **READ / SKIMMED / NOT-READ / OWNER-ONLY**: (a read status, not the file) how much of a file a lane read: all / part / none (so the lane says nothing about that file) / a file only the owner may open.
- **UNVERIFIED**: stated, not checked against a file or command output. **NOT VISIBLE**: the lane could not see it. **NOT FOUND**: searched, not present. **NOT SET / TO DO**: nobody has filled it in.
- **Severity** in a finding row: the lane's own label; the lead session has confirmed none.

D-04 is not unknown: it is the rule that a lead sent twice is processed once (decision-list-for-lead.md, Reading notes).

## Unknown terms: do not use in new text
SWEEP.md is a held page (see Files), not an unknown. Each term below has meaning NOT RECORDED in any file. Ask the lead session (it passes studio terms to the studio lead); if neither answers, ask the owner. If you meet one of these terms, write "term (undefined)" and do not guess. The one-store decision: which copy is the source is also unknown (same asking rule). Find where a term was seen with `grep -rl "<term>" handover/system-map`.
- Ids and names: mf_leads (probably a stored-leads table; UNVERIFIED), stage.journal, D-05, F-008, LP-n, GO-1, k1b, K1b, KeyOk, WARDEN, F8, A4, A13, C1, P3, design 12, the spike, smk_count, drive.py, fill_flows.py, STOP class, freeze input, stand-in, refusal, Route config, desk, rig.
- Versions and phases: film-v5 / real-v5, Mode A, WP6 P11, D1 order, K1 to K6, go1/v3/v4, ONE-PLACE-TABLE, ORDER 002, PLAN section 5.2.
- Job keys (words in a job list): STORE, RETRY, NOTICE, FILTER, COUNTER, LOG, OTHER. Claim types: dead, idle, ops. L6 verdict words: OWNER, NEEDED, CRM-COULD-DO, DUPLICATE, NOT-NEEDED. Claim (as a flow step) is explained in work/not-checked-r2.md Terms.

## Lanes (one line each)
L1, L2, L3, L4, L5 and L6 are the lane names (L1 to L4 read the core-hardening files in four slices, L5 the flow files, L6 whether each part is needed; UNVERIFIED, from the lane pages' own headings). Each lane page (work/L<n>*.md) says in its own first lines what it covers; this glossary does not repeat that. L5a/L5b is an unconfirmed split of L5 (UNVERIFIED, from a hand-back); do not use it until confirmed.
