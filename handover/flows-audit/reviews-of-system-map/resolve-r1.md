# Goldfish Annotated Review Report (egm:egm-resolve, round 1 of max 2)

Status: resolved (lead instruction: judge on evidence, PROPOSE FIX for valid findings, no questions; ESCALATE items go to the laptop lead; no severity changed except three CONTESTs below, each with a rubric reason)

**Target:** outputs of cloud session system-map (branch cloud/system-map, head 707768f), read-only. **Inputs:** lane-R5-B, -M1, -M2, -D, -Z, -C and evidence-5.md in this folder. 32 merged findings (from 6 lanes: about 150 lane findings and rows, deduplicated).

Counts by category: PROPOSE FIX 28, ESCALATE 4, CONTEST 0 whole findings (3 severity CONTESTs: XR-14, XR-15, XR-18, reviewer Blocker to Major by the PLAN-005 rubric), DECLINE 0.

ESCALATE first (need facts outside every file the reviewers could read): XR-21, XR-23, XR-30, XR-32.

Rubric used (PLAN-005): Blocker = could lose or double-apply a lead or mail, leak, or a published claim is false; Major = wrong failure path, a second store, or an unbacked claim; Nit = naming or leftovers.

## Prioritized findings

### XR-1 [table: COUNTER] - Severity: Major
* **Sources:** R5-D-1, R5-C-12, R5-Z-17
* **Discrepancy:** COUNTER Owner line names stage.journal as the proof-count place; the table's own OWNER row (J-034) and DECISION-one-store.md:11 name the independent count that reads HubSpot and Gmail. stage.journal holds per-lead model-call start/finish only (DECISION:9) and cannot count mails or CRM rows.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** ONE-PLACE-TABLE.md:72 (Owner line), SWEEP.md:12
* **Change:** Owner line: 'proof count = the independent count (own read-only credential, reads CRM and mailbox; DECISION:11). stage.journal = per-lead model-call guard only (row J-035), not a count.' Make J-034 the Owner row.

### XR-2 [table: STORE J-005] - Severity: Major
* **Sources:** R5-D-3a, R5-Z-15
* **Discrepancy:** Desk SpendLedger is called DUPLICATE of stage.journal, but the table says three times (lines 81,83,87) that stage.journal is not a dollar ceiling. SpendLedger is the only dollar-ceiling copy seen, so it is the money-cap candidate, not a duplicate.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** ONE-PLACE-TABLE.md:28 (J-005), SWEEP.md fix plan rows 18-24
* **Change:** Change verdict to NEEDED-OPEN (money-cap candidate) until decision (a) is made; remove 'MERGE'.

### XR-3 [table: STORE J-037 and KEEP-CORE J-008] - Severity: Major
* **Sources:** R5-D-3b, R5-Z-15, L5a-FD-004 (M2 lane)
* **Discrepancy:** Askdata meter called DUPLICATE of core Limits with MERGE-INTO, and the same meter files are KEEP-CORE in J-008. Core Limits.charge is a plain booking plus a separate blocked() read (limits.py:17-30); the meter has atomic reserve before the call and settle after (meter.py:211-229). A merge loses reserve-before-call. Two verdicts for the same files; a merge is a money-path change for a later portal not built.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** ONE-PLACE-TABLE.md:88 (J-037), :31 (J-008)
* **Change:** J-037 verdict KEEP-CORE (same as J-008); proposal: 'no merge until Limits can express reserve-before-call; money path, uncapped review'. Strike MERGE-INTO from fix plan rows 18-24.

### XR-4 [table: RETRY J-042 and fix plan row 11] - Severity: Major
* **Sources:** R5-D-4, R5-Z-16
* **Discrepancy:** Node retry on Qualify and CrmUpsert is called DUPLICATE of the recovery sweep and proposed for trim, but it does a different job (fast in-run retry inside the 120 s lease; the sweep only acts after the lease ends). The row itself says the trim is not implementable as written. stage.journal caps the paid call and the CRM upsert is keyed, so the retry is safe.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** ONE-PLACE-TABLE.md:98 (J-042), SWEEP.md:372 (row 11)
* **Change:** J-042 verdict NEEDED (fast-path layer); delete 'trim node retry' from row 11; keep the dead-node removal as its own step with a re-run.

### XR-5 [table + cut list: ARCHIVE rows with referrers] - Severity: Major
* **Sources:** R5-D-5, R5-Z-8, R5-Z-9, R5-Z-10, R5-Z-11, R5-Z-12, R5-C-9
* **Discrepancy:** Rule text 'nothing with a caller is archived' (table lines 3, 12) is false for five ARCHIVE rows: J-012 (checklist.py:111 writes CARRY-OVER-CHECKLIST.md; five referrers to AB-PAPER.md), J-019 (evidence/ folder is the source of numbers-audit.md; paused-b21/22/23 hold open NOT DONE state; REPORT-archive referenced at demo3/REPORT.md:46, register.md:327), J-039 (archives test counts but fix row 10 says reconcile; ORDERS.md, INT-1.md, register.md are live), J-049 (run_h.sh:9 is cited by two Blockers; run_c.sh says 'Starts after run_b.sh'; the row's own text says 'bound or archive'), J-055 (REVIEW-v4-fresh.md and REVIEW-real-run-v6-fresh.md are the evidence for L4c-FD-001 and L4c-FD-003). The caller grep was never reported (REPORT.md:4).
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** ONE-PLACE-TABLE.md:3,12,36 area rows J-012,J-019,J-039,J-049,J-055
* **Change:** J-012, J-055: KEEP until referrers are updated (archive only the DO-NOT-USE chains with 0 referrers). J-019: archive only files with 0 referrers; keep paused-b21/22/23 and evidence/summary.md. J-039: replace ARCHIVE with 'reconcile' (matches row 10). J-049: proposal 'bound each loop' not archive. Add to the table header the grep command and its result for every ARCHIVE row. Amend the rule line to 'archived only after the referrer list is empty or updated'.

### XR-6 [cut destination] - Severity: Major
* **Sources:** R5-Z-13
* **Discrepancy:** The archive destination archive/<same path> is outside handover/. CLAUDE.md (Design rules, last bullet): 'no private notes outside handover/'. These files include the owner's full name and a login in 79 paths (L1-FD-021), and the CI allowlist guards handover/ only (.github/workflows/ci.yml:198-222). No archive/ folder exists.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** ONE-PLACE-TABLE.md:12,29; SWEEP.md fix plan rows 8-12,18-24
* **Change:** Destination = handover/archive/<same path>. Add the new folder to the CI allowlist and the hygiene scan in the same step. State that git history still holds old copies.

### XR-7 [table: FILTER J-028] - Severity: Major
* **Sources:** R5-Z-14, R5-D per-job, L2-FD-004 (M1 lane)
* **Discrepancy:** mf-hook is MERGE/remove, with the reason 'never POSTed by any test'. harness.py:26 lists mf-hook in FLOWS, harness.py:114-116 imports it, prepare_probe.py:17 holds its id; deletion conflicts with 'nothing is deleted'. The row bundles two things: the second public entry flow, and dead nodes UnknownNewA/UnknownNew (mf-sub-crm-mail.json:326,358). mf-hook and mf-form share the key space (lead_key from message_id vs submission_id) so a collision could drop a lead.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** ONE-PLACE-TABLE.md:64 (J-028)
* **Change:** Split into two steps: (1) take side: do not import or activate mf-hook (closes a second public webhook); (2) later: remove the dead nodes with a re-run. Change 'nothing is deleted' to 'nothing is deleted without a re-run' (28, 42, 18, 40 are removals/merges).

### XR-8 [table: OTHER J-058 and fourth identity] - Severity: Major
* **Sources:** R5-D-8, R5-C-8
* **Discrepancy:** J-058 is the live shared Postgres credential used by every node but is labelled NOT-NEEDED (a skimmer could delete it). The target also proposes a fourth identity (migrations) in the OTHER block, J-058 and fix plan row 24 as a plain CHANGE; DECISION-one-store.md:14 says three roles (n8n, app, read-only count). Only row 6 says the DECISION is not changed.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** ONE-PLACE-TABLE.md:123-129; SWEEP.md:367,385
* **Change:** J-058 verdict CHANGE (in use, split into the three roles). Write 'a fourth identity for migrations would change DECISION:14: laptop lead decides' in the OTHER block and row 24.

### XR-9 [table: 'one place per job'] - Severity: Major
* **Sources:** R5-Z-17, R5-C-14, R5-D-10, R5-D-11
* **Discrepancy:** The table and headline say one owner per job and one Postgres, but: COUNTER has two owners (XR-1) and none for the money cap; LOG owner (n8n history in Postgres) does not exist in the flows today (all saving 'none'); FILTER has three dedupe layers with different keys; STORE is three places by DECISION (one a file); OTHER proposes none. 'Open owner: none' for the money cap is UNVERIFIED (take repo not visible), not 'none'. Only LOG, FILTER, RETRY, NOTICE, STORE name a verified place.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** ONE-PLACE-TABLE.md:1,40,72,81,123-125; SWEEP.md:25
* **Change:** Reword 'one place per job' to 'one proposed owner per job; 5 of 7 verified in the rig, 2 open (COUNTER: independent count not shown to run outside n8n; OTHER: none)'. Replace 'Open owner (money cap): none' with 'UNVERIFIED; options: stage.journal is not a ceiling; provider-side limit; core Limits reserve-before-call'.

### XR-10 [table: state column 'OK'] - Severity: Major
* **Sources:** R5-Z-5, R5-C-16
* **Discrepancy:** State OK means 'no conflict with DECISION', yet J-025 (review-state row) and J-041 (recovery sweep) are OK/keep while the sweep rates them Blockers L2-FD-007 and L6-FD-026. Neither has a proposal. A review-state lead is stored and told 'review', is excluded from the sweep and from alerts, so nobody is told. (By the PLAN-005 rubric both are Major, see XR-25.)
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** ONE-PLACE-TABLE.md:13,61,97,114
* **Change:** Rename OK to NO-CONFLICT; for J-025 add proposal 'send a notice for review rows (new node: decision for the lead, default after the video; video script must say review requests are not handled)'; for J-041 'stop swallowing DB errors (continueRegularOutput) or alert on repeated skip'.

### XR-11 [table: NOTICE J-052] - Severity: Major
* **Sources:** R5-Z-1
* **Discrepancy:** Row says the intake mail is 'a notice to the lead, not to our person'. mf-sub-crm-mail.json:208-212 sends to the fixed internal address intake@example.test with text 'made-up thank-you text' and the lead id in the subject; nothing goes to the lead's own address; harness.py:221 counts it as mail_to_intake. Take repo not visible: whether the take differs is UNVERIFIABLE. Lead re-read confirmed the node lines.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** ONE-PLACE-TABLE.md (J-052 row)
* **Change:** Reword: 'one mail to a fixed internal address with the lead id; no mail to the sender in the rig'. Add: video claims about who receives mail must be checked against the take's own flow.

### XR-12 [fix plan row 1] - Severity: Major
* **Sources:** R5-D-2, R5-Z-4
* **Discrepancy:** Row 1 sits in the band 'a decision or a config change: no new node', but step 3 'switch execution saving on' edits all four flow files (saveDataSuccessExecution and saveDataErrorExecution = 'none': mf-form.json:424-425, mf-hook.json:424-425, mf-recovery.json:384-385, mf-sub-crm-mail.json:743-744) and re-imports them; it needs the 10-request re-run, has no pass criterion or rollback, and error saving stays none so failed runs stay invisible. Turning saving on also puts the made-up name and e-mail into n8n history: one more copy of personal data.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** SWEEP.md:362 (row 1)
* **Change:** Row 1 step 3: 'edit the two settings in the 4 flow files (success AND error), re-import, re-run the 10-request test; pass = executions list shows runs and a planted canary is masked; rollback = re-import old files'. Add a STORE row: where personal data is held (mf_leads, n8n history, CRM, mailbox).

### XR-13 [fix plan rows 15, 16, 17] - Severity: Major
* **Sources:** R5-D-6, R5-C-2, R5-C-27
* **Discrepancy:** Same-class key-exposure Blockers are banded differently: row 15 (L4c-FD-001, vendor's default address) AFTER the video, row 16 (L4c-FD-002, key to a second server on redirect) BEFORE, with no reason. Rows 15-17 hold a finding, not an action; row 15 is cut mid-sentence ('which touches. (full text: Findings)'); 'pending patch', 'codeant', 'apply order matters' are unexplained. The desk is retired from the take (DECISION:15) and no desk code is in the tree.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** SWEEP.md:376-378
* **Change:** Put 15 and 16 in the same band; write each as an action ('do not run the desk in the take, or apply patch X then re-run test Y'); complete the cut text; explain 'codeant' (a code-scanning service) and the patch order in one line each.

### XR-14 [decision (a): dollar-cap place] - Severity: Major
* **Sources:** R5-C-3, R5-D decisions, R5-D-10
* **Discrepancy:** Not decidable as posed: fix row 2 proposes stage.journal, which the table says three times is not a dollar ceiling; no figure and no candidate list. Options missing: provider-side spend limit (tool ladder rung 2), core Limits/meter reserve-before-call, a cap of one call per lead times the test requests. Reviewer severity Blocker; CONTEST: by the PLAN-005 rubric this is Major (it cannot lose or double-apply a lead or mail, leak, or make a published claim false).
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** SWEEP.md:16,363; ONE-PLACE-TABLE.md:81-87
* **Change:** State the question as: 'where does the dollar cap live (one of: provider-side limit / core Limits reserve-before-call / per-lead one-call guard plus request cap)?' with cost, effort, and what each leaves open.

### XR-15 [decision (b): second alert channel and watcher] - Severity: Major
* **Sources:** R5-C-4, R5-D decisions
* **Discrepancy:** Not decidable: no candidate channels, cost, watcher or effort; ORDERS.md:197 already records 'no second alert channel now (open item)'. The evidence for the need is weaker than presented (see XR-26). A cheaper option without a new node is not listed (an outside watcher on the count's own result). Reviewer severity Blocker; CONTEST to Major (rubric).
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** SWEEP.md:366; ONE-PLACE-TABLE.md:110
* **Change:** List at least two candidate channels and a watcher, cost, effort; state that the need is a permanent mail/n8n/Postgres outage (shared credential mf-mail-smtp), not a slow SMTP.

### XR-16 [decision (c): what the proof counter reads] - Severity: Major
* **Sources:** R5-D-7, R5-C-5
* **Discrepancy:** A fact to look up, not a decision: DECISION:11 already says the independent count reads HubSpot and Gmail. 'Counter' is undefined. The real open question is decision 4: the only count code seen is a stand-in Code node (proof.json), 'checked in node only' (J-034), so it is not shown to run outside n8n. Desk archive rows (004,016,029,036,044,054) are blocked on this; they should be blocked on 'does the take proof read desk /counts' (DECISION:6,15 say no).
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** SWEEP.md:16,363; REPORT.md:7; ONE-PLACE-TABLE.md:76
* **Change:** Delete decision (c) from the open list; add its answer from DECISION:11. Re-block desk archive rows on 'desk /counts not read by the take proof' (a yes/no check).

### XR-17 [decision (d): key rotation / history rewrite, and decision lists differ] - Severity: Major
* **Sources:** R5-C-6, R5-D decisions 4
* **Discrepancy:** Consequences are not stated (a history rewrite changes every commit id in a public repo; which keys are real is UNVERIFIED; exception L6-EX-10 not shown). Fix row 7 mixes untrack/rotate, move to archive/ and rewrite in one cell. SWEEP.md:16-17 and REPORT.md:7 list the open decisions differently (R5-C reads a studio-head key decision; R5-D reads the fourth decision as 'independent count outside n8n; three roles vs a fourth identity').
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** SWEEP.md:16-17,368; REPORT.md:7
* **Change:** Make one list used in SWEEP headline, REPORT and fix plan. Split row 7 into three rows (untrack; rotate if real; rewrite history, with its consequence in one sentence).

### XR-18 [headline counts and missing decisions] - Severity: Major
* **Sources:** R5-C-1, R5-C-7, R5-C-17, R5-C-22
* **Discrepancy:** Headline lists only row 7 as open for the studio head, yet the before-18-Nov band needs a yes on seven mandatory rows (1,3,7,13,14,16,17) plus optional 5 and 6, and 19 table rows say 'yes needed'. A fifth decision (one more lane for 183 NOT-READ files: 18+66+99 = 183, correct) is missing. Headline omits the 10-row appendix (counts 49 + 10 = 59 are right, per-job keyed totals are 12,11,10,7,10,7,2) and gives no Blocker count. Reviewer severity Blocker for the first item; CONTEST to Major (rubric).
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** SWEEP.md:5-17,360-378; ONE-PLACE-TABLE.md:14
* **Change:** Add one line: 'Needs a yes: N rows (list ids). Open decisions: 5 (list). Blockers: 16 after merging duplicates (see REVIEW).' Fix '1 rows'. Delete the reference to 'severity cells' at table line 14 or add the column.

### XR-19 [fix plan: bands and order] - Severity: Major
* **Sources:** R5-C-18..21, R5-D bands, R5-D-5
* **Discrepancy:** The 'order' column is not an order of work (bands interleave: before 1,2,3,7,13,14,16,17; optional 4,5,6; after 8-12,15,18-24); no priority among the eight before-video rows; no effort against the two days left; row 1 has no fallback. Band label 'decision or config change, no new node' does not fit rows 3 (PR bodies), 7, 13 (renames), 14, 16. Row 4 (silent drop of a review-state request) defaults AFTER and is safe only if the video script says review-state requests are not handled; no row scopes that claim. Row 11 says studio-head yes 'no' for J-028/J-042, the table says 'yes' for both. Rows 18-24 ask one yes per block while items are blocked. Row 10 (reconcile) conflicts with row 21 (archive). 'PR #1', 'three live pull request bodies' unexplained. Bands are real but wrongly labelled.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** SWEEP.md:360-385
* **Change:** Rename band 1 'decision, config change or text change (no new node)'; add an effort and a first/second order inside band 1; add to row 4 the video-script sentence; align row 11 yes column with table; split rows 18-24 per item with their blocker; resolve row 10 vs 21 (see XR-5).

### XR-20 [wording: terms a stranger misreads] - Severity: Major
* **Sources:** R5-C-10, -11, -15, -23, -24, -25; R5-Z wording; R5-Z-18
* **Discrepancy:** 'lead' means laptop lead (SW:378), the sales request, and the person who sent it; 'owner' is 'a place, never a person' (OPT:7) but J-037 and J-012 say 'needs owner yes'; 'copy' column holds OWNER rows; KEEP-CORE includes CI files, J-050 is KEEP-CORE with CHANGE; J-010/J-017 NOT-NEEDED with KEEP; CONFLICT vs PLAN NOT DONE used for one situation (J-001, J-002, J-013); sweep, claim, heartbeat, counter, take, journal each carry two or more meanings; used before explained: L6-EX-01..11 (EX-11 gates every desk archive), re-smoke, planted-data check, 'DECISION seed row six', 'Lane wording', k1b, creds-lane.json, CodeRabbit, SonarCloud, DeepSource, codeant, Semgrep, film-v5/real-v5; 'exception' never defined.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** ONE-PLACE-TABLE.md:3,7-16,34,39,62,138,158; SWEEP.md:24,362,373
* **Change:** Add a 12-line word list at the top of the table (one meaning each). Rename: 'laptop lead' / 'studio head' / 'request'; verdict KEEP-CORE -> KEEP-IN-SDK; NOT-NEEDED+KEEP -> KEEP-RIG; use CONFLICT only; define exception in one sentence and list L6-EX-01..11 in an appendix.

### XR-21 [missed: public webhooks without authentication] - Severity: Major
* **Sources:** R5-Z-2
* **Discrepancy:** mf-form and mf-hook are public POST webhooks with no authentication setting (grep '"authentication"' in mf-form.json = 0 hits, lead re-check); the dedupe key is caller-chosen; any fresh id yields a CRM row, a mail and one paid model call; the table says no place holds a dollar cap. MASTER-MAP L2-WK-001/013 note 'no auth set' but no SWEEP finding or table row exists. Rig runs on 127.0.0.1, so exposure depends on how the take is reached: UNVERIFIABLE.
* **AI Suggestion:** ESCALATE
* **Proposed edit (location):** SWEEP.md (new finding); ONE-PLACE-TABLE.md FILTER block
* **Change:** Add finding: 'webhook has no authentication; with no dollar cap a caller can spend by sending fresh ids'. Severity Major (Blocker if the take is reachable from the internet). The laptop lead states how the take is reached.

### XR-22 [missed: dedupe key only submission_id] - Severity: Major
* **Sources:** R5-Z-3
* **Discrepancy:** Key is only the caller-chosen submission_id (mf-form.json:27, PK lead_key mf_leads.sql:5): the same e-mail with a new id is a new lead (second model call and second mail; only the CRM upsert merges on e-mail). An empty or missing submission_id gives one shared key or a null-key insert error; Claim has no onError and execution saving is off, so a lead could be lost with no trace (runtime UNVERIFIED). MASTER-MAP L2-WK-001 notes 'empty body gives empty lead_key'; SWEEP does not pick it up.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** SWEEP.md (new finding); ONE-PLACE-TABLE.md J-024
* **Change:** Add finding (Major; Blocker if a keyless lead is dropped with no trace). Fix: reject empty id with a visible reply; say in J-024 what the key is.

### XR-23 [missed: n8n env access setting] - Severity: Major
* **Sources:** R5-Z-6
* **Discrepancy:** Harness sets N8N_BLOCK_ENV_ACCESS_IN_NODE='false' (harness.py:35, lead re-read): any expression can read the process environment (database password, encryption key); flows already use $env.MF_STAGE_URL, $env.MF_CRM_URL (mf-sub-crm-mail.json:19,75). Whether the take copies it is UNVERIFIABLE. Not in table or sweep.
* **AI Suggestion:** ESCALATE
* **Proposed edit (location):** SWEEP.md (new finding); ONE-PLACE-TABLE.md OTHER
* **Change:** Add finding (Major): 'env access from nodes is allowed; set N8N_BLOCK_ENV_ACCESS_IN_NODE=true in the take if no flow needs it, or pass URLs as flow parameters'. Laptop lead checks the take.

### XR-25 [sweep: Blocker severity] - Severity: Major
* **Sources:** R5-B (all rows), evidence-5
* **Discrepancy:** Of the 20 raw Blocker rows: 20 of 20 facts are CONFIRMED against the cited lines (evidence-5 shows every cited line exact). By the PLAN-005 rubric only 4 distinct issues stand as Blocker: L1c-FD-021 (false claim in live PR text), L2-FD-002 (+ leak half of L6-FD-001: made-up e-mail, name and key canary in n8n's own file), L2-FD-008 (= L6-FD-005: mail lost with no alert), L4c-FD-002 (key forwarded after redirect, printed in traceback). 13 rows are Major (L1-FD-021, L1c-FD-001, L2-FD-001, L2-FD-003, L2-FD-007, L2-FD-018, L4c-FD-001, L6-FD-002, L6-FD-003, L6-FD-004, L6-FD-006, L6-FD-017, L6-FD-026) and 1 is Nit (L4c-FD-003). The lane header said 11; recounting its row list gives 13 (lane slip, corrected here). Duplicates: L6-FD-002 = L2-FD-003, L6-FD-017 = L2-FD-007, L6-FD-005 = L2-FD-008, L6-FD-001 = L2-FD-001 + L2-FD-002 (16 distinct, matching the target's own dedupe). Of the 4 standing Blockers: L1c-FD-021 and L4c-FD-002 depend on patch/paste state UNVERIFIED; the first-three statements stand on the rig only (take flows not visible).
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** SWEEP.md:35-355 severity cells; REPORT.md headline '10 Blockers touching the take'
* **Change:** Re-rate the 13 rows to Major and L4c-FD-003 to Nit; merge the four duplicate pairs; headline: '4 Blocker issues, 12 Major, ... (rubric in PLAN-005)'. Keep row ids.

### XR-27 [sweep: rows with no claim] - Severity: Major
* **Sources:** R5-M1 structural
* **Discrepancy:** 12 of 70 sampled Major rows (lines 61-200) have no claim sentence, only quotes (L3-FD-002, 007, 009, 011, 013, 015, 021, 023, 031, 036, 038, 041). The quotes exist on the cited lines; whether they support a claim cannot be judged. L3-FD-040 itself says 'claim sentence missing'. A Major with no stated claim is a defect.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** SWEEP.md lane L3-FD rows (about 41 rows)
* **Change:** Write one claim sentence per L3-FD row, or demote the row to Nit 'unreviewed quote'.

### XR-28 [sweep: wrong or overstated rows] - Severity: Major
* **Sources:** R5-M1, R5-M2
* **Discrepancy:** Wrong or partly wrong: L1-FD-025 (cited line is the branch-protection line; '45 to 116 never run' mixes the Windows laptop skip with the Linux no-Playwright count), L3c-FD-007 (cited lines show fix-5 majors 2, 1B+2, 4, 3, not rising), L3c-FD-018 (numbers belong to different heads: 2513 on 2ce1f98 vs 3683 on later main), L4-FD-011 (ORDERS.md:348 says PR #4 merged as 61ded9eb, so 'no file says which head is current' is false), L4-FD-021 (cites hang/RESULTS.md:1-10; the counts are not there), L5a-FD-008 (meter.py:35 is a unit constant, evalrun.py:36 an e-mail regex, not money or thresholds). Overstated: L1-FD-010, L1-FD-032 (mf_leads itself was proven: WP6 smoke P11), L2c-FD-002, L2c-FD-008, L2-FD-016, L3c-FD-005. L4-FD-013 severity wrong (sonar-project.properties line 4 projectKey is not a secret: a scanner false positive).
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** SWEEP.md rows named
* **Change:** Per row: L1-FD-025 cite :164 and split 45/116; L3c-FD-007 delete 'rise'; L3c-FD-018 name the head per number; L4-FD-011 delete or cite ORDERS.md:348; L4-FD-021 cite the right file; L5a-FD-008 delete the two false items; L4-FD-013 to Nit; overstated rows: reword as the lane notes say.

### XR-29 [sweep: Major severity inflation] - Severity: Major
* **Sources:** R5-M1, R5-M2
* **Discrepancy:** Of the 105 Majors sampled by the reviewers: 44 are Nit by the rubric (M1 27, M2 17), 12 have no claim sentence (XR-27), 1 is a meta row, 48 agree Major (M1 31, M2 17). Leftover copies, internal count slips, rig-only and retired-desk items, stale rule pointers are Nit. The 105 sampled are half of 209; the unsampled 104 are NOT-CHECKED.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** SWEEP.md Major rows listed in lane files
* **Change:** Re-rate the 44 named rows (lane files list the ids). Run the same check on the other 104 (a continuation lane).

### XR-30 [sweep: possible Blockers hidden as Major] - Severity: Major
* **Sources:** R5-M1
* **Discrepancy:** L3-FD-011: docs/settings.md says a bad DESK_BIND value stops the start but the desk starts with garbage (false doc sentence; Blocker if that doc is published). L2-FD-019: the fake CRM matches 'lead id OR e-mail' (mf-form.json:97, fakes.py:103); if the real HubSpot also merges on e-mail, two leads become one CRM row (lead loss). Both UNVERIFIABLE here.
* **AI Suggestion:** ESCALATE
* **Proposed edit (location):** SWEEP.md L3-FD-011, L2-FD-019
* **Change:** Laptop lead checks (a) whether docs/settings.md is published, (b) HubSpot match rule on e-mail. Then re-rate.

### XR-32 [not judged by the reviewers (cannot-judge rows)] - Severity: Major
* **Sources:** R5-D per-row, R5-Z not-checked
* **Discrepancy:** Table rows the reviewers could not judge: J-003 (real stage.journal not visible), J-011 (HubSpot/Gmail), J-014 (table says file not read), J-020 (PII masking UNVERIFIED), J-027 (CRM-COULD-DO needs a dated vendor source), J-053 (table screen UNVERIFIED), and the desk rows J-004, J-016, J-029, J-036, J-044, J-054 (no desk code in the tree; 'block until desk patches applied' is odd for retired code). Row J-034 got no separate verdict from R5-D (read through XR-1).
* **AI Suggestion:** ESCALATE
* **Proposed edit (location):** ONE-PLACE-TABLE.md rows named
* **Change:** Laptop lead or studio head with the take repo and desk repo checks these 12 rows; take repo not visible here (third party/owner).

### XR-24 [missed rows] - Severity: Nit
* **Sources:** R5-D-12, R5-Z-7
* **Discrepancy:** Not in the table: the take's secret file and n8n.env (DB and SMTP passwords; DECISION:14); the stage.journal writer identity (DECISION:17); attempts and alert_attempts counters in mf_leads (recovery:26,124); heartbeat/watcher; SMTP, HubSpot and count credentials; backup/restore and whether data survives a container restart (one lost volume loses credentials, flows and lead rows).
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** ONE-PLACE-TABLE.md appendix
* **Change:** Append 6 rows with verdict and proposal.

### XR-26 [sweep: Blocker L2-FD-008 evidence] - Severity: Nit
* **Sources:** R5-D-9, lane-R5-B L2-FD-008
* **Discrepancy:** The Blocker leans on lead_alerts=0 from a test the author called flawed (questions-for-lead.md:12 'a flaw of my test as much as of the flow'). The alert flow has backoff and re-claim (mf-recovery.json:124,204), so a slow SMTP is re-alerted; the Blocker holds for a permanent mail, n8n or Postgres outage (shared credential mf-mail-smtp: recovery:196, sub-crm-mail:227). 'Fc never re-run on v3,v4,go1' is not backed by COMPARE-demo.md:12.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** SWEEP.md row L2-FD-008
* **Change:** Replace primary evidence with the shared-credential outage argument; drop the 'never re-run' sentence or cite a source.

### XR-31 [citation hygiene and wording] - Severity: Nit
* **Sources:** R5-B, R5-M1, R5-C-26..29
* **Discrepancy:** Counts off by small amounts: 8 files not 9 and 79 hits (L1-FD-021); 224 vs 226 (L4-FD-004); 116 vs 117 (L1c-FD-020); OPT:98 says lines 35 and 91 but cites 36; J-023 'all 126 run folders' vs a non-empty fl45k6c; row 22 missing bracket; J-039 'ARCHIVE of test counts' unclear; after archive moves, evidence citations (about 60 paths) break and no note says they are updated.
* **AI Suggestion:** PROPOSE FIX
* **Proposed edit (location):** as named
* **Change:** Correct the counts; add one line 'citations are updated in the same step as each move'.
