# Goldfish Annotated Review Report (result review round 1, resolve)

Status: resolved (headless auto accept; the lead of the session applies the edits to tools/write_outputs.py and regenerates)

**Target:** `handover/system-map/tools/write_outputs.py` (full file; generates SWEEP.md and ONE-PLACE-TABLE.md)
**Findings source:** `handover/system-map/work/result-review-r1.md` (reviewers: CD codebase-details, ZO zoom-out, CO comprehension, DE design)

Counts: PROPOSE FIX 31, CONTEST 2, ESCALATE 3, DECLINE 4. Remaining unaddressed after the edits: the three ESCALATE items (they need the studio head or the laptop lead) and the NOT-READ files (183, no continuation lane ordered).

Rules used: severity is only changed by a table clarification or a re-rating row with a reason; every re-rating is listed in the generator in one `RERATE` table so the lead sees it; a core module is never archived (CLAUDE.md "core modules have one source of truth", rule core-modules-one-source-of-truth).

## ESCALATE (list first, they need the owner or the laptop lead)

### E1 [DE-B4 part, L2-FD-018] Keys and credential files tracked in git
*   **Why escalate:** whether the tracked files hold real or made-up secrets, and whether history is rewritten, are the studio head's decisions (secret change, history rewrite of a public repository: CLAUDE.md "No secret change ... unless the owner gives an explicit yes"). The reviewers could not see git history either (CD: "no git in this box"; the "220 MB in history" claim rests on `demo3/REPORT.md:3,5` only).
*   **Edit (Fix plan, new row in band "owner yes needed"):** `| L2-FD-018 | stop tracking the four creds-lane.json files; ROTATION (not archive) of anything real; history rewrite only on the studio head's yes | studio head | yes |`
*   **Edit (Exceptions, new id L6-EX-10):** `| L6-EX-10 | never-delete rule: tracked credential files | a secret is rotated and untracked, not archived; an archived copy would keep it in the repository | studio head | after rotation and untracking | checklist rule "never delete" |`
*   Status of the claim stays UNVERIFIED (git history not in this box).

### E2 [CD-B2, DE-M3 part] Who owns the dollar cap for the take
*   **Why escalate:** DECISION-one-store.md line 9 and 17 say stage.journal is a per-lead write-ahead guard, not a dollar cap, and no file says the take has one. Only the take repo (NOT VISIBLE) can answer.
*   **Edit (Fix plan, band "owner yes needed"):** `| L6-FD-003 | the laptop lead names the take's owner of the dollar cap (money cap); until then the desk SpendLedger, the askdata meter and core Limits are NOT archived | laptop lead | yes |`
*   **Edit (Claims check, new row):** `| the take has a model-call spend cap | DECISION line 17 (implied) | stage.journal is a per-lead repeat guard; no dollar-cap owner in files seen (take repo NOT VISIBLE) | UNVERIFIED |`

### E3 [DE-B1] What the take's proof count reads
*   **Why escalate:** `proof.json` decides PASS from desk statuses (L1c-FD-017) but whether the real take proof reads the desk is in the take repo (NOT VISIBLE).
*   **Edit (ONE-PLACE, rows L6-J-004, J-036 and any desk ARCHIVE):** proposal text becomes `ARCHIVE BLOCKED until the laptop lead shows which counter the take proof reads (take repo NOT VISIBLE)`; "owner yes needed" stays `yes`.

## PROPOSE FIX (Blocker)

### 1 [CD-B1, ZO-B2, DE-B2] ARCHIVE proposed for live core code, the rig, CI and a credential
*   **Justification:** core modules have callers (`deferred.py:11`, `cli.py:36`, `app.py`, `agent_loop.py`) and DECISION line 15, 17 and 18c plan the later portal and the journal move on core store kinds. A move to `archive/` breaks imports and the repo guard tests. NOT-NEEDED for the take is a take-scope statement and must not become a repo-wide move.
*   **Edit in `write_outputs.py`:**
    *   Replace the proposal logic with a dict `PROPOSAL = {n: text}` and these default values: OWNER/NEEDED -> `keep`; any row whose `where` starts with `src/` or whose name contains "core " -> `KEEP-CORE (out of take scope; no move)`; kill-rig rows (J-010, J-017) -> `KEEP (test evidence; fix plan rows 1 and 3 need the rig)`; CI rows (J-022, J-033) -> `KEEP (CI)`; J-058 credential -> `CHANGE (replace by three least-privilege roles, see Fix plan)`; J-059 -> `STOP (process waste, not a file)`; J-023 -> `FIX THE HARNESS (it recreates the empty files every run); no archive`; ARCHIVE is allowed ONLY for handover/, demo/, desk, snapshot and patch-chain rows.
    *   Add verdict `KEEP-CORE` to the verdict list and to the key text; rows J-006, 007, 021, 031, 032, 038, 045, 046, 047, 056 get verdict `KEEP-CORE`, exception `none`. They no longer count as NOT-NEEDED. (Plan 5.3 says NOT-NEEDED is only "nothing calls it": these have callers.)
    *   J-007 reason text: add "imported by `src/hadavin_sdk/deferred.py:11` and `src/hadavin_sdk/cli.py:36`".
*   **Scan impact:** `scan_outputs.py` verdict check must accept KEEP-CORE (one-line change in its allowed list; the lead edits the script and its test).

### 2 [CD-B2, DE-M3, ZO-M2] COUNTER is two jobs
*   **Justification:** stage.journal stops a second model call for the same lead (idempotency); the SpendLedger, the askdata meter and core Limits enforce a dollar ceiling (`meter.py:211`, `limits.py:17`). Different jobs. The independent count is the proof count.
*   **Edit:** split the job key block `## Job: COUNTER` into two blocks `## Job: COUNTER (proof count)` and `## Job: COUNTER (money cap)` inside the same registry key; each has exactly one `Owner:` line:
    *   proof count: `Owner: the independent count (code NOT VISIBLE: take repo, owner UNVERIFIED; a stand-in n8n Code node exists and was never run in real n8n, L6-FD-018)`.
    *   money cap: `Owner: UNVERIFIED: no owner of a dollar cap for the take is identified (see E2); stage.journal is the per-lead repeat guard (L6-EX-02)`.
    *   Rows: J-034 and J-036(desk counts) -> proof count; J-035, J-005, J-037, J-038 -> money cap; J-037 and J-005 verdict `NOT-NEEDED for the take until the cap owner is named` with proposal `KEEP until E2 is answered` (no MERGE-INTO core Limits, no ARCHIVE).
    *   `scan_outputs.py` counts `Owner:` per block; the two blocks give 8 `Owner:` lines in total; the lead updates the expected count (7 -> 8) in its check or keeps the key name `COUNTER` with a `(proof count)` / `(money cap)` suffix that the scan strips.
*   Fix plan row 3 text: replace "archive the other five counters" by `list the five other counters (stage.journal, desk SpendLedger, askdata meter, core Limits, k1b cap, eval counter: six places in total, L6-FD-003) and keep all until E2 is answered`.

### 3 [ZO-B1, DE-M9, CD-M1, CD-M6, CD-N5] Blocker count inflated; severities do not follow the table
*   **Justification:** the severity table must be applied once. Rig evidence is not the take; double counting from L6 restates L2 originals.
*   **Edit:** (a) severity table text in the SWEEP intro becomes: `Blocker = contradicts DECISION-one-store.md in the TAKE, or touches money, credentials, mail or personal data, or a claim that a reader would act on is false. A wrong count or number that changes no action is Major (not Blocker).` (b) add `RERATE = {"L4-FD-004": ("Blocker", "Major", "count slip, no action changes"), "L3-FD-040": ("Blocker", "Major", "no claim sentence; source review says 0 Blocker"), "L2c-FD-001": ("Blocker", "Major", "shell hygiene; no real call shown"), "L6-FD-017": ("Major", "Blocker", "lead lost, no mail (severity table: mail)"), "L2-FD-007": ("Major", "Blocker", "same"), "L1-FD-021": ("Major", "Blocker", "false claim in live text"), "L1c-FD-001": ("Major", "Blocker", "credential on same runner as test code")}` applied when the Findings table is written: the cell shows `Blocker (was Major: reason)` style via a new last column `rerated`. (c) NEW finding row `L6-FD-026 | ops | Blocker | the recovery sweep swallows database errors (continueRegularOutput) so a Postgres hiccup stops recovery with no notice | evidence from L6-J-041 (`mf-recovery.json` quote copied from the L6 row) | DECISION line 7 | RETRY`. (d) Counts table gets two lines: `raw` (all rows) and `deduplicated` (rows minus the L6 restatements: L6-FD-001, L6-FD-002, L6-FD-005 each duplicate an L2 original; L4-FD-003/L4c-FD-011, L4-FD-005/L4c-FD-012, L2-FD-001/L2c-FD-010 pairs), header `Counts (raw rows; deduplicated number below)`. (e) add a column `scope` to the Findings table with values `take-rig` (go1 flows), `take-repo NOT VISIBLE`, `build-process`, `core`.
*   Contest: none of the rows is lowered below what the table says; each demotion cites the new table sentence.

### 4 [DE-B1] Desk ARCHIVE could remove what the proof reads
*   Accepted, see E3 for the exact edit; additionally Fix plan row 7 text: `after E3 is answered and the pending security patches (L4c-FD-001..003) are finished`.

### 5 [DE-B3, CD-M3] Turning on execution saving puts lead data into the one Postgres
*   **Edit (Fix plan row 2):** `| L6-FD-002, L2-FD-002 | BEFORE switching execution saving on: run the planted-data check (GREP) on Postgres-backed n8n; write down what is stored, who can read it (n8n role versus app role), the prune and retention setting and what is masked; then switch saving on in the take flows | laptop lead | yes |` (owner yes becomes `yes`).
*   Claims check new rows: `no lead data reaches n8n's store | L2-FD-002 | made-up e-mail, name and key canary found in n8n files with saving off | CONTRADICTED (rig)`; `DB_POSTGRESDB_SCHEMA works for import and start | DECISION UNVERIFIED item 6 | not run | UNVERIFIED`.

### 6 [DE-B4] Fix plan has no row for most Blockers
*   **Edit:** replace Fix plan row 9 ("all Major findings") by generated rows, one per Blocker id that is not already named in rows 1 to 8, built from the Findings table at write time: `| N | <id> | <first sentence of the evidence cell, cut to 160 chars> | laptop lead | <yes if id mentions credential/spend/desk, else no> |`. Then three rows for Majors by claim type (duplicate, dead, idle) with the id list.
*   Add the band column (see 10).

### 7 [DE-B5] Lead lost with no notice; sweep swallows errors
*   Accepted, see item 3 (RERATE for L6-FD-017 and L2-FD-007, new L6-FD-026). Fix plan row: `| L6-FD-017, L2-FD-007, L6-FD-026 | every lead must end in a terminal state a person sees; the sweep must alert on its own database error | laptop lead | no |` in band "before the video" (config on proven flows only).

### 8 [DE-B6, ZO-M6] NOTICE shares fate with what it reports
*   **Edit (NOTICE block):** add a paragraph above the table: `Alert mail (L6-J-051) and lead intake mail (L6-J-052) use ONE SMTP credential (mf-mail-smtp) and run inside the same n8n and the same Postgres. If mail, n8n or Postgres is down, nobody is told. Needed: a second channel with its own credential and a heartbeat watched from outside n8n. The new NOTICE owner for that channel is not named yet: ESCALATE to the laptop lead.` Fix plan row 4 text: `give the alert its own credential and its own path, plus a heartbeat check from outside n8n; name the second channel (needs the laptop lead's decision)`. This is a fourth ESCALATE-type open question; it is recorded in Exceptions note, not as a separate item.

### 9 [DE-M4, CD-N2] LOG owner is two things
*   **Edit:** `OWNERLINE["LOG"] = "n8n execution history in Postgres (DECISION line 16)"`; J-014 (mf_leads lifecycle rows) verdict NEEDED with exception L6-EX-05; L6-EX-05 text: `mf_leads holds the latest state per lead, not an append-only history; it cannot show a double send or a sequence. It is state, not audit. The audit gap is open (an append-only event table was ruled out before the video by DECISION line 16).`

### 10 [ZO-M3, DE-M5] Fix plan order and bands
*   **Edit:** add a column `band` to the Fix plan: `before the video (Wed 18 Nov, config on proven flows only)`, `owner yes needed`, `after the video`. Row mapping: rows 2 (after the planted-data check), 4 (credential and path), 5 (three roles incl. a fourth admin/migrations identity), L6-FD-017, L6-FD-026, PR body correction -> `before the video`; desk archive, superseded versions, counters decision, key rotation -> `owner yes needed`; kill-test re-run on Postgres (needs a runtime, tracked by the re-smoke plan, DECISION line 14), merge of mf-hook into mf-form (needs a composite key, see 20), node-retry change (see 20) -> `after the video`. New row: `| L1-FD-003, L1c-FD-007 | archive superseded patch, PR-text and evidence versions (about 519 KB) | studio head | yes |`.

## PROPOSE FIX (Major)

### 11 [CO-1..5] Opening key for both files
*   **Edit:** new function `KEY_TEXT` written under the title of both files (plain words; each sentence says who does what):
    *   take = the lead-intake automation that Hadavin will show in the video; its code repository `duplicate-proof-lead-desk` is not in this box and the laptop lead checks it locally; that is why every NOT-NEEDED verdict says "UNVERIFIED for the take repo".
    *   laptop lead = the engineer who gave the order; sales lead = a person who sends a request through the form; studio head = the owner who says yes to money, archive and secret changes (replace every "owner yes" by "studio head says yes" and every unqualified "lead" by "laptop lead" or "sales lead").
    *   DECISION-one-store.md = the laptop lead's written decision that the take keeps its data in one Postgres (three stores by design: n8n data, mf_leads, stage.journal); "DECISION line 14" means line 14 of that file.
    *   job key = the kind of job a place does: STORE (holds data), LOG (record of what ran), FILTER (decides what enters, such as duplicate checks), COUNTER (counts for proof or for a money cap), RETRY (runs stuck work again), NOTICE (tells a person), OTHER.
    *   verdicts: OWNER = the one place that does this job; NEEDED = a second place the take must keep, allowed by an exception id; DUPLICATE = a copy of what the job owner place already does; CRM-COULD-DO = the customer system (CRM) may do this itself, only a dated source proves it, otherwise UNVERIFIED; NOT-NEEDED = nothing in the files seen calls it (UNVERIFIED for the take repo); KEEP-CORE = shared core code, out of take scope, never moved.
    *   proposals: keep, KEEP-CORE, CHANGE, MERGE-INTO <place>, ARCHIVE (move to `archive/<same path>` after the studio head says yes; never delete), STOP.
    *   ids: `L1c-FD-021` = lane L1, `c` = continuation lane, FD = finding, number; kinds S store, W workflow, X script, J job, K credential, C component.
    *   words: desk = the older lead desk program with its own SQLite file and portal (web screens), retired from the take by DECISION line 15; rig = the kill-test setup that crashes the flows on purpose; journal = a file that records each model call before it is made (write-ahead); lease = a time limit during which one run owns a lead; sweep = the recovery flow that runs every 30 s (not this SWEEP file); claim = the first database insert that reserves a lead (n8n node "Claim"), never the claim type column; "claim type" = category of a finding; "Claims check" = statements made in files and whether they hold; seed row = one of six places DECISION lists.
*   `OWNER` in the "owner yes needed" column header becomes `studio head yes needed`; "Owner:" lines become `Job owner place:`. **Scan impact:** the lead changes the regex in `scan_outputs.py` (one line) and its tests.

### 12 [CO-6..20] Other wording
*   **Edit:** in the generated tables replace "place" in the `copy` column header with `what`; define status words in Claims check intro: `PROVEN = a raw file shows it; CONTRADICTED = a raw file shows the opposite; UNVERIFIED = needs a runtime or a file not in this box`; Lessons: prefix each bullet with a plain label ("For the audit checklist:", "For studio memory:", "For agent briefs:", "For lane method:"); the Fix plan names `finding ids` and what each id is in a short phrase.
*   Rows J-018, J-039 and J-059 move to the appendix (item 13), so the "place" wording problem disappears for them.

### 13 [ZO-M1] Over-built table
*   **Edit:** after the seven job blocks add `## Appendix: build-process rows (not places of a take job)` holding J-012, J-018, J-022, J-033, J-039, J-040, J-049, J-050, J-057, J-059, same eight columns. The job blocks keep only the places a job runs in. Counts in the intro: `49 rows in job blocks, 10 in the appendix`.

### 14 [ZO-M4, CD scope, DE-N6] NOT-READ on the first screen
*   **Edit:** the SWEEP intro gets a line `NOT-READ files: L1c 18, L3c 66, L4c 99 (183 in total). Unread means UNVERIFIED, not clean.` Delete the sentence in the Exceptions note that says the unread folders "mention no mf_leads"; replace by `The lead may order one more continuation lane for these three lists.` Claims check last row becomes `every file under handover/ was read | lane Coverage tables | 183 files NOT-READ | CONTRADICTED`.

### 15 [ZO-M5, DE-M2, CD-M1] Verdict mixes status and conflict
*   **Edit:** new column `state vs DECISION` in ONE-PLACE rows: `OK`, `PLAN NOT DONE` (n8n SQLite, saving none: DECISION line 8 already records the SQLite correction; lines 14 and 16 are the plan), `CONFLICT` (desk still built, one shared credential). Claims check rows 3 and 4 status become `PLAN NOT DONE (rig evidence; the take flows film-v5 and real-v5 are NOT VISIBLE)` instead of CONTRADICTED. Seed check rows for n8n data and process logs use `PLAN NOT DONE`. Findings L2-FD-001 and L6-FD-001 get the word "rig" in `scope`. L2-FD-001 and L6-FD-001 wording: "every kill run" becomes "the kill harness (static inference from `harness.py:34`; the GREP result shows SQLite in 11 runs)".

### 16 [CD-M2] L2-FD-008 / L6-FD-005 overstated
*   **Edit (text of the finding rows by the generator as an override map `TEXT_FIX`):** replace "when the mail server is slow, a lead ends unknown with no alert, nobody is told" by "fault Fc holds every SMTP connection for the whole run (a total mail outage); within the 330 s window plus 20 s settle no alert was seen; Fc1 (first connection only) gave lead_alerts=1 in 6 of 6 runs (`RESULTS.md:14`); the design point stands: when mail is fully down there is no second channel". Claim type stays `unverified`; severity stays Blocker only for the single SMTP credential part (item 8).

### 17 [CD-M4] Security patches pending
*   **Edit (Exceptions):** `| L6-EX-11 | desk stop-or-archive | L4c-FD-001 (key to vendor), L4c-FD-002 (n8n API key to a second server), L4c-FD-003 (real-spend consent flag) are fixed only in pending patches | laptop lead | the three patches are applied | DECISION line 15 |`.

### 18 [CD-M5] CRM upsert not archived
*   **Edit:** J-027 verdict `CRM-COULD-DO` (UNVERIFIED), proposal `KEEP until a dated source shows the CRM does this; the keyed upsert is what keeps crm_rows=1 under retries (RESULTS.md, L6-FD-008)`; owner yes `no`. J-011 evidence: replace `fakes.py:75` by `handover/system-map/DECISION-one-store.md:11 "HubSpot (CRM) and Gmail"` plus the note `real HubSpot and Gmail NOT VISIBLE`.

### 19 [DE-M1, DE-M7] Single database, ops and tenant isolation
*   **Edit (new SWEEP finding rows by generator `EXTRA_FINDINGS`):** `L6-FD-027 | ops | Major | one Postgres holds intake, claim state, recovery, n8n data and the execution log: if it is down everything stops; backup, restore test, volume persistence, retention, start/stop/kill and egress answers are not in any file seen | DECISION line 14 | STORE`; `L6-FD-028 | unverified | Major | tenant isolation: the take has one client; N/A for a single-client take if confirmed; the app schema has no source or tenant column | DECISION line 14 | STORE`. Claims check: `Postgres sits behind n8n's credential layer (no single dependency) | DECISION line 18c | no kind with an alternative is described | UNVERIFIED`. (n8n itself is not flagged: no-code tools are owner-approved, tool ladder rung 3.)

### 20 [DE-M5 part, CD-M5] Proposals that touch proven flows
*   **Edit:** J-028 proposal `MERGE-INTO mf-form AFTER THE VIDEO; the key must become source plus id (L2-FD-004: ids from two sources can collide and a lead is wrongly dropped)`; J-042 proposal `AFTER THE VIDEO; n8n Retry On Fail cannot filter by error type (UNVERIFIED), so "only transient HTTP errors" is not implementable as written; removing it also makes recovery wait for the 120 s lease`; J-043 add `double-alert window if a send was in flight at the kill (not tested; two n8n at once not tested)` to the reason.

### 21 [DE-M6] Least privilege of the target design
*   **Edit (Fix plan row 5 text):** `three Postgres roles (n8n, app, read-only count) PLUS a fourth identity for roles, schemas and migrations; each with a negative test (the role is refused what it must not do); name the exact tables the count role may read; give the count's Gmail and HubSpot credentials their own minimum scopes`; owner yes `yes`.

### 22 [DE-M8, CD seed] Claims missing
*   Accepted, rows added under 5 and 19 plus: `stage.journal is independent of the flow identity | DECISION line 17 | nothing shows who can write the file or whether two stage processes run at once | UNVERIFIED`; `process output files hold no lead data | L6-EX-04 | lead data was found in the n8n database (L2-FD-002) | UNVERIFIED`. EX-04 text: `stage stderr and result.json` (DECISION line 10), not "stage stdout".

## PROPOSE FIX (Nit worth fixing)

### 23 [CO-21, ZO-N1, CD-N1] Truncated proposal cells
*   **Edit:** cause is a `|` inside the cell text. In `write_outputs.py` add `esc = lambda s: s.replace(" | ", " / ")` and apply to every cell value (reason, proposal, evidence), and re-check with `scan_outputs.py`.

### 24 [CD-N5 part] Evidence mismatches
*   **Edit (TEXT_FIX map):** J-023 reason: `most of the 378 log files are empty (check: count lines per file; one run folder fl45k6c has non-empty logs)`; J-022 evidence: drop `ci.yml:36 "timeout-minutes: 30"`, cite `.github/workflows/ci.yml` header line that names the workflow (lead picks the line, must exist); J-020: remove "unredacted by design" and write `query text passes clean() (terminal escapes stripped, `ledger.py:3`); whether masking of personal data happens is UNVERIFIED`; J-042: `retryOnFail` is `false` on the mail node (`mf-sub-crm-mail.json:230`); only lines 36 and 92 show 3 tries; L2c-S-008 does not prove SQLite (says "not stated"): J-002 cites `harness.py:34` and `RESULTS.md:40` only.

### 25 [CD-N4] mf_leads and seed rows
*   **Edit:** seed row 2 status: `CONSISTENT for the table; CONFLICT for the schema (mf_leads.sql:4 creates it in the default schema, DECISION line 14 says schema app) and for roles`. Seed row 6 evidence: add `NOT VISIBLE: real HubSpot and Gmail` and drop the circular DECISION-only support: status `CONSISTENT with DECISION; real run UNVERIFIED`.

### 26 [DE-N4, ZO] Exceptions without removal trigger
*   **Edit:** EX-03, 04, 05, 06, 08 removal trigger `none: not an exception to the one-store rule (it is a place DECISION allows or a part of a flow)`.

### 27 [DE-N3, CO-23] Verdict wording for not-visible and non-places
*   **Edit:** TAKE-REPO row verdict `N/A: not visible`; Counts table header `Counts (raw rows; deduplicated number below)`.

### 28 [CO-22] Rule sentence
*   **Edit:** intro line: `Every copy except the job owner place, NEEDED rows and KEEP-CORE rows has a proposal.`

### 29 [DE-N7, CD-N7] check_citations does not prove support
*   **Edit (SWEEP intro, one sentence):** `The citation check proves each quoted line exists, not that it supports the claim; support was checked by sample by the result reviewers.`

### 30 [CD-M2 note, ZO-M2] L6-J-052 same credential
*   Covered by item 8.

### 31 [DE-M3, CD-M6] L3-FD-040 and L2-FD-018 text
*   **Edit (TEXT_FIX):** L3-FD-040 gets a claim sentence: `a round-12 design review of a paused patch is cited; its own text says 0 Blocker, 2 Major; kept as Major (RERATE)`.

## CONTEST

### C1 [ZO-B1, CD-M1 part] "Rate rig-versus-DECISION conflicts as 'carry into the take'; demote L2-FD-001, L6-FD-001, L2-FD-003, L6-FD-002 from Blocker"
*   **Evidence:** the rig's SQLite engine and saving-none are measured facts for every kill number the take quotes (`harness.py:34`, `RESULTS.md:40`, `mf-form.json:424`); DECISION line 8 itself says the first smoke ran on SQLite, so the numbers measured on it do not prove the Postgres target. The severity table says Blocker for "contradicts DECISION in the take" and the take flows are NOT VISIBLE, so the lead needs to see them first on the page. They stay Blocker with scope `take-rig` and state `PLAN NOT DONE` (item 15 gives the label that removes the over-reading). Only the Claims-check status changes.

### C2 [CD-N5, DE-N1 part] "Fix the harness instead" for the 378 empty log files, and the double-alert window as a Nit
*   **Evidence for the contest of the Nit rating only:** the double-alert window changes mail behaviour (severity table: mail) and stays in the reason text of J-043 (item 20) rather than being dropped. No change of the reviewers' severity; recorded as accepted with the text above.

## DECLINE
*   D1 [CD-N5] L6-J-020 deeper audit of pipeline.py: nothing to change beyond item 24.
*   D2 [DE-N1] separate test for "two n8n at once": needs a runtime; recorded under item 20 as UNVERIFIED, no new row.
*   D3 [CO-24] dates and IST in SWEEP: the document is about a repository, not scheduling; the REPORT status blocks carry UTC and IST.
*   D4 [CO-25 part] Lessons labels beyond item 12: done there.

## Order of application for the lead
1. Apply items 1, 2, 11, 13, 15, 23 to `write_outputs.py` (structure and wording: new verdict, split COUNTER, key text, appendix, column, escaping).
2. Apply items 3, 5, 6, 7, 10, 14, 17, 19, 21, 22, 26 (severity table, RERATE, new findings, fix plan bands, exceptions, claims).
3. Apply text overrides 9, 16, 18, 20, 24, 25, 27, 28, 29, 31.
4. Update `scan_outputs.py` (KEEP-CORE verdict, `Job owner place:` line, COUNTER suffix) and its tests; run all tests; regenerate; run `check_citations.py` over the outputs; then evidence-2 and a fresh round-2 review (max 2 rounds; after round 2 only Blocker and Major).
5. Handoff counts: accepted fixes 31, contested 2, escalated 3 (E1 key rotation and history, E2 dollar-cap owner, E3 proof-count source; the NOTICE second channel is a fourth open question inside item 8), declined 4, remaining unaddressed: 183 NOT-READ files and anything that needs a runtime.
