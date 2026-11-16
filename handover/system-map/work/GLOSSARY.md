# Glossary for the system-map pages (live text; no amendment paragraphs live here)
Written Mon 16 Nov 2026 by the system-map session. Only meanings found in files are given. Where no file gives a meaning, the entry says "meaning not recorded" and the Unknown list names one person to ask. "Line N" on any page means line N of the file that page names; if the page names no file, the cite is UNVERIFIED. Old text is in GLOSSARY-history.md (ignore it).

## People and sessions (one table)
| name | what it is | kind |
|---|---|---|
| lead session | the Claude session that gives the system-map session its orders (older pages write "the lead"; it is not the studio lead) | Claude session |
| studio lead | the Claude session that does the technical steps on the take and messages the owner | Claude session |
| core-hardening | a separate Claude session that owns V5 and the held pages | Claude session |
| system-map session | this Claude session; it writes only inside handover/system-map/ | Claude session |
| lane | one helper Claude session given one slice of the review to read (L1 to L6); its output file is a lane page | Claude session |
| studio head | the human who runs the studio; whether this is the owner is NOT SETTLED | human |
| owner | the human at the laptop who gives the written yes | human |

## Files (one table)
| name | path | what it holds |
|---|---|---|
| held pages | OWNER-VIEW, OWNER-RUN-DAY-CARD, OWNER-CLEANUP-CARD, LEAD-PAGE, TAKE-BLOCKERS, SWEEP, MASTER-MAP, README, QUESTIONS, QUEUE, ORDERS.md, inputs/, tools/, tests/ | pages the lead session or core-hardening own; this session records digests of reads and does not edit them |
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
- **mf_leads**: a table name for stored leads. UNVERIFIED; no file this session holds confirms it.
- **stage.journal**: meaning not recorded (see Unknown).
- **row N**: row N of the table on that page, unless the page writes "TAKE-BLOCKERS row N".
- **READ / SKIMMED / NOT-READ / OWNER-ONLY**: how much of a file a lane read: all / part / none (draw no conclusion) / a file only the owner may open.
- **UNVERIFIED**: stated, not checked against a file or command output. **NOT VISIBLE**: the lane could not see it. **NOT FOUND**: searched, not present. **NOT SET / TO DO**: nobody has filled it in.
- **Severity** in a finding row: the lane's own label; the lead session has confirmed none.

## Unknown: do not use in new text (ask the lead session, who passes studio terms to the studio lead)
D-04, D-05, F-008 and LP-n (meaning unknown), GO-1, k1b, KeyOk, Claim, WARDEN, film-v5 / real-v5, Mode A, WP6 P11, D1 order, K1 to K6, go1/v3/v4, desk, rig, SWEEP.md, ONE-PLACE-TABLE, ORDER 002, PLAN section 5.2, C1, K1b, P3, design 12, the spike, smk_count, drive.py, STOP class, F8, freeze input, A4, A13, fill_flows.py, job keys (STORE, RETRY, NOTICE, FILTER, COUNTER, LOG, OTHER), claim types (dead, idle, ops), L6 verdict words (OWNER, NEEDED, CRM-COULD-DO, DUPLICATE, NOT-NEEDED), "stand-in", "refusal", "Route config". Contact: the lead session.

## Lanes (one line each)
L1 to L6 are lane names; L5a/L5b is a split of L5 that tools/partition.py must still apply (UNVERIFIED, from a hand-back). What each lane covers: meaning not recorded here; see its lane page.
