Status: resolved (headless: AUTO ACCEPT of every PROPOSE FIX; no ESCALATE needs the user before the fixes, open items are listed at the end)

# Goldfish Annotated Review Report, result round 2

**Target:** `handover/system-map/tools/write_outputs.py` (full file). Findings: `work/result-review-r2.md` (zoom-out Z, design D, comprehension C, codebase-details K).
Counts: 34 findings taken in (Z 5, D 10, C 11, K 8). PROPOSE FIX 31, CONTEST 2 (partial), ESCALATE 1, DECLINE 0. The lead applies the edits; line numbers are those of the file as read in this run (232 lines).

Check on a cited line first: Z-M1 cites a refusal of a second alert channel at `ORDERS.md:197`. `ORDERS.md` has 15 lines (read in this run), so that line does not exist. The Fix plan change below rests on DECISION lines 14 and 16 only. Do not quote `ORDERS.md:197`.

## Group A: Fix plan (generator lines 85-108, 132-137). One edit set for Z-M1, Z-M2, D-B1, D-B2, D-M1, D-M3, C-B1, K-M5, K-N1

### [A1] Z-M1, D-B1, K-M5 - Blocker (design), Major (zoom-out, codebase) - PROPOSE FIX
Rows 1, 3, 4 are labelled "config changes on proven flows only" but add nodes (row 1), a new credential, path and channel (row 3), roles, a schema move and new scopes (row 4). DECISION line 16 says new nodes change the proven flows; DECISION line 14 says the schema and the roles are not in the re-smoke.
Edit (replace `BANDS` at line 85 and the three rows at lines 87, 89, 90):
- New `BANDS = ["before Wed 18 Nov, no new node, no new identity", "before Wed 18 Nov only if the laptop lead chooses it: changes the proven flows, needs a re-smoke", "needs the studio head's yes", "after Wed 18 Nov"]`.
- Row 1 (L6-FD-017, L2-FD-007, L6-FD-026) goes to band 2 with action: "add the missing branch so a lead in state review or unknown ends in a mail or alert, and make the recovery sweep alert on its own database error (a new branch and a changed error setting in mf-recovery). Pass criterion for the re-smoke: 10 test leads give 1 new, 9 duplicates, 1 e-mail, 1 CRM row, and one forced database error gives 1 alert. Rollback: re-import the exported flow files from git." Responsible person: laptop lead. Yes: no. Add column value "risk to the video: yes".
- Row 3 (L6-FD-005, L2-FD-008) goes to band 2: "second alert channel with its own credential, its own path and a heartbeat outside n8n; the laptop lead names the channel and the person who owns it". Yes: yes (new credential).
- Row 4 (L6-FD-006) goes to band 2: "three Postgres roles and a fourth identity for roles and migrations; take table moved to the schema app; own minimum scopes for the count's Gmail and HubSpot credentials". Yes: yes. State once that this touches every Postgres credential and every SQL statement, so it needs the full re-smoke, and the default proposal is after the video.
- Add one line under the table: "Rows in band 2 are NOT recommended before the video by this review; they are listed so the laptop lead can choose."

### [A2] D-B2, Z-M2 (Postgres re-smoke) - Blocker - PROPOSE FIX
Rows 2, 10 and 15 order the work in conflict: saving on before the video (row 15) with no yes; n8n data moved to Postgres after the video (row 10); row 2 needs Postgres-backed n8n first.
Edit: replace rows at lines 88 and 96 by ONE sequence row in band 1 ("before Wed 18 Nov, no new node, no new identity"), ids `L6-FD-001, L2-FD-001, L6-FD-002, L2-FD-002, L2-FD-003`:
"Steps in this order. (1) Start n8n on the one Postgres (this is the re-smoke DECISION lines 8, 14 and 18a already plan; needs a runtime, UNVERIFIED here). (2) Run the planted-data check there and write down what n8n stores, who can read it (n8n role or app role), and what is masked. (3) Only then switch execution saving on; this is a config change, not a node. (4) Write down the prune and retention setting. Stop at the first step that fails." Responsible person: laptop lead. Needs studio head yes: yes (personal data in logs; the three reviewers agree it needs the checks first). Delete the old row 10 and row 15 (they were the same finding L2-FD-003 / L6-FD-001 under another band).
Contest to note: row "needs a runtime" stays UNVERIFIED; the generator must not say "verified".

### [A3] C-B1, D-M3, K-N1, Z-M2 (rows 13-18) - Blocker (comprehension), Major (design), Nit (codebase) - PROPOSE FIX
Lines 100-105: the auto rows copy the first 160 characters of the evidence cell, cut mid-word ("personal na", "made-"). They also repeat ids that rows 1 and 2 cover.
Edit:
- Add `L2-FD-003` to the sequence row of A2 (it is already there) so `named` (line 100) contains it and no auto row is made for it.
- Add an `ACTIONS` dict before line 100 and use it at line 105: `ACTIONS.get(c[0]) or first_sentence(c[3])`, with `first_sentence(t)` = text before the first backtick, cut at the last full stop within 240 characters (never mid-word); append " (full text: Findings)".
- `ACTIONS["L1c-FD-001"] = "run the SonarCloud token in its own job that runs no test code; rotate the token if it was ever on the same runner as test code (studio head says yes, secret change)"`; yes: yes.
- `ACTIONS["L1-FD-021"] = "rename the tracked files and folders that carry a personal name in the path, in a normal commit; rewriting history is a separate step that needs the studio head's yes"`. The lead reads the full finding in `work/merged-findings.md` first and corrects this sentence to match; the cell in the Findings table is cut in this run's view.
- For rows that need the studio head's yes (old rows 16-18), the action cell must say which action is approved, taken from `ACTIONS`.
- After the edit, add a check line in the generator: fail with `sys.exit(1)` if any Fix plan action cell has no sentence-ending character.

### [A4] Z-M2 (two columns) - Major - PROPOSE FIX
Line 132 header becomes `| order | when | finding ids | action | responsible person | needs studio head yes | needs a runtime (UNVERIFIED here) |`. The `when` text is the band label of A1. Keep one band per row; do not use the word "owner" in this table (see C-B2).

### [A5] Z-M2 (lump rows), K-N2 - Major - PROPOSE FIX
Lines 106-108 make rows like "65 Major duplicate findings: ..." with action "work through them". Replace by one row per job key (band 4) built after the ONE-PLACE rows exist: action = "apply the proposals of ONE-PLACE-TABLE.md block KEY: " + "; ".join(`<id>: <proposal>`) over rows whose proposal starts with MERGE-INTO, CHANGE, FIX or ARCHIVE. This needs the move in group E (parse the L6 rows before line 124).

## Group B: Counts and headline (generator lines 36, 60-71, 124-128)

### [B1] Z-M3 - Major - PROPOSE FIX
Add `L6-FD-017` to `DEDUP` (line 36): it restates L2-FD-007 (both are "a lead in state review gets no notice"). After that, add to Counts one more column and one sentence:
- Rule (write it above the table): "A Blocker touches the take when its scope is take-rig or cross-lane and it is not a restated row; build-process and desk rows do not touch the take."
- Add a line `| Blockers that touch the take, deduplicated | n |` where n = count of `ded` rows with severity Blocker and `scope(id)` in (take-rig, cross-lane). Compute n in code; do not type it.
Expected: deduplicated Blockers about 16 (17 minus L6-FD-017). The lead reports the real printed number.

### [B2] Z-M4 (headline) - Major - PROPOSE FIX
Add a section `## Headline` directly under the NOT-READ line (line 126), at most 15 lines: one line per job key (STORE, LOG, FILTER, COUNTER, RETRY, NOTICE, OTHER): `KEY: owner place (UNVERIFIED if so marked) / copies: n / verdicts: OWNER a, NEEDED b, DUPLICATE c, KEEP-CORE d, ...`, then one line each for "open questions for the laptop lead" (cap owner, second alert channel, proof count) and "not visible". Counts per verdict are computed from `rows` (move needed, see group E). One-place owners come from `OWNERLINE`.

### [B3] Z-M4 (row count 49 versus 48) - Major - CONTEST (partial)
Two reviewers (comprehension, codebase-details) recomputed the intro and found 49 job rows plus 10 appendix rows, and both say it matches. The zoom-out count (48) differs. Evidence the zoom-out reviewer could read: the intro at the generator line 210. Resolution without taking a side: replace the typed "49 rows ... 10 build-process rows" (line 210) by numbers computed in code (`len` of the block lists and `len(APPX)`), and the lead runs `grep -c "^| L6-J-" ONE-PLACE-TABLE.md` and reports it in REPORT.md. Not a fix to either number until counted.

## Group C: ONE-PLACE-TABLE rows

### [C1] D-B3 (money cap and COUNTER owner) - Blocker - PROPOSE FIX
Edits:
- `OWNERLINE["COUNTER"]` (line 159) becomes `"PROOF COUNT: recommended owner for the take is stage.journal (the per-lead write-ahead file, DECISION line 17); for the later client portal, core Limits (`src/hadavin_sdk/limits.py:17`). What the take proof reads is UNVERIFIED (take repo NOT VISIBLE)"`. Do not call it a decision; it is a proposal to the laptop lead.
- Add a second owner line in the Money cap section (line 219): `Owner (money cap): none, open. No place enforces a dollar ceiling for the take in the files seen.` The scan (`scan_outputs.py:58`) counts `Owner:` lines per key: either put the money cap under its own key `COUNTER-MONEY` (add to `KEYS` in the scan and to `RANGES`/`Job` headings) or keep one `Owner:` line and write the money-cap line as `Open owner: ...` so the scan stays at one. Recommendation: the second form (no change to the scan), and say so in the table.
- `L6-J-035`: reason must say "enforces a per-lead repeat guard, not a dollar ceiling"; delete the words "the cap in effect" (override via `TEXT[35]`). Keep verdict NEEDED with exception L6-EX-02 only for the repeat guard.
- Move the "name the cap owner" action to band 1 (before Wed 18 Nov, no new node): it is a decision, not a change. Responsible person: laptop lead.

### [C2] D-B3 (LOG and OTHER owners) - Blocker - PROPOSE FIX
- `OWNERLINE["LOG"]`: add the sentence "AUDIT (who approved what) is a second job under this key: place L6-J-014, exception L6-EX-05; Owner for it: none proposed, open". Use the same `Open owner:` form as C1.
- `OWNERLINE["OTHER"]` (line 162): replace "OTHER is not a place" by "identities and roles (L6-J-058) have no single owner yet; Open owner: laptop lead names one (the fix is the three roles of DECISION line 14 plus the migrations identity)". Reason: the least-privilege rule needs a named owner for identities.

### [C3] K-B1 - Blocker - PROPOSE FIX
Rows L6-J-008, 009, 020, 030, 048 (demos/ask-your-data) must not propose ARCHIVE: callers exist at `src/hadavin_sdk/guard/producers.py:63` and `:68`, `pyproject.toml:29`, `tests/demo_askdata/`, `tests/test_stage_names.py:560`, `tests/test_ci_gitleaks_scope.py:174` (reviewer-read; the lead confirms each with `grep -n` before writing it, since only the reviewer read them).
Edit: `CORE = CORE | {8, 9, 20, 30, 48}` (line 171); redefine KEEP-CORE (KEY_TEXT line 13) as "code or gate configuration with callers outside the take (src/, demos/ask-your-data, CI files): out of take scope, never moved"; `TEXT[20]` (line 183) loses "NOT-NEEDED for the take" and says "has callers (see proposal); the take does not use it"; add `PROP` entries `{8, 9, 20, 30, 48: "KEEP-CORE (callers: guard/producers.py:63 and :68, pyproject.toml extra askdata, tests/demo_askdata/); archive only after those references move"}`. Class fix at the choke point: in `render`, if the lane reason contains "no caller" or "nothing calls it" and the row is `src/` or `demos/`, require a `grep` check noted by the lead; add the rule to the sweep Lessons ("before proposing ARCHIVE, grep the registry `guard/producers.py`, `pyproject.toml` and `tests/`").
Sibling search (class-level fix): the lead greps all rows with proposal ARCHIVE for the same registries (`guard/producers.py`, `pyproject.toml`) before regenerating.

### [C4] K-B2 - Blocker - PROPOSE FIX
Rows L6-J-050 and L6-J-057 (appendix) must not propose ARCHIVE of live gate config.
Edit `PROP` and `FORCE`: `FORCE[50] = FORCE[57] = "KEEP-CORE"`; `PROP[50] = "CHANGE (keep the weekly cron and tools/mutation_runner.py, which tests use; bound the curl retry at ci.yml:228 and add a failure notice)"`; `PROP[57] = "KEEP (dependabot.yml and .coderabbit.yaml are live gates; CLAUDE.md lists CodeRabbit as a required pull request gate)"`. The "never archive a module that has a caller" rule becomes a generator assertion: `assert not (prop.startswith("ARCHIVE") and verdict == "KEEP-CORE")`.

### [C5] K-M3 - Major - PROPOSE FIX
L6-J-047 reason and L6-FD-016 claim type say "dead" for `src/hadavin_sdk/extract.py`, but `guard/producers.py:36` and `:58` register it and `tests/test_s4_llm_guard.py` imports it.
Edit: `TEXT[47] = "KEEP-CORE: no runtime caller in the take, but registered in the guard registry (`src/hadavin_sdk/guard/producers.py:36`) and used by a test"` (the lead confirms the quote with the citation check; if it does not match, drop the backticks). Add `RETYPE = {"L6-FD-016": ("idle", "no runtime caller; registered in the guard registry and imported by a test")}` applied at line 49 (claim type becomes idle, note appended to the evidence cell). Counts regenerate by themselves.

### [C6] K-M4 - Major - PROPOSE FIX
L6-FD-023, L2-FD-024 say the three log files are empty in all 126 run folders; `work/L2.md:331-333` lists non-empty logs in run folder fl45k6c (849, 655, 853 bytes).
Edit: `NOTE["L6-FD-023"] = NOTE["L2-FD-024"] = "Result review round 2: not all are empty; run folder fl45k6c has crm.log 849, smtp.log 655, stage.log 853 bytes (work/L2.md:331-333). Read 'most'; the lead counts the non-empty files with find and writes the number here"`. Plus `TEXT[23]` already says "most": keep. The lead runs one `find ... -size +0 -name '*.log' | wc -l` for the real number (not done in this run).

### [C7] K-M6, Z-M4, C-M1 (J-005, J-037 verdicts) - Major - PROPOSE FIX
Line 172: `FORCE[5] = FORCE[37] = "DUPLICATE"` (PLAN-002 section 5.3 gives DUPLICATE precedence over NOT-NEEDED when the reason says DUPLICATE). `PROP[5]` and `PROP[37]` become `"MERGE-INTO core Limits, only after the owner of the dollar cap is named; keep both until then"`; the yes column then computes to "yes", which is correct (money path, studio head says yes). Make the NOT-NEEDED definition in KEY_TEXT honest: "NOT-NEEDED: nothing in the files seen calls it for the take; this is not 'safe to remove'. Check callers in `src/`, `pyproject.toml` and `tests/` before any archive."

### [C8] K-N2 - Nit (misleading) - PROPOSE FIX
Two defects:
1. Line 197: `re.search(r"MERGE-INTO ([^;,.)]+)", ...)` stops at `)` but not at `(`, so J-040 ends "(L1-FD-016" with no closing bracket. Fix at the choke point: `r"MERGE-INTO ([^;,.()]+)"` and `.strip()` on the capture.
2. J-028 groups the dead if-nodes `UnknownNewA` and `UnknownNew` (`mf-sub-crm-mail.json:326,358`) with mf-hook, but they are in another file. `PROP[28]` (line 178) gets a second sentence: "The dead if-nodes UnknownNewA and UnknownNew sit in mf-sub-crm-mail.json (lines 326 and 358, reviewer-read); both branches go to OutUnknown, so they decide nothing: remove them there, a separate CHANGE, after the video".

### [C9] D-M5 - Major - PROPOSE FIX
Line 203: state column. Add `CONFLICT = CONFLICT | {1}` (the seed check says the table is in the default schema with one shared credential: CONFLICT for schema and roles). L6-J-003 and L6-J-014 have no checked state: add `UNVERIFIED = {3, 14}` and print `st = "UNVERIFIED (file not read for this row)"` for them. Define OK once: "OK = no conflict found in the files seen".

### [C10] C-M2 - Major - PROPOSE FIX
A row with verdict OWNER and state "PLAN NOT DONE" (L6-J-013) reads as a contradiction. Add one sentence to KEY_TEXT: "OWNER names the place DECISION chooses; state says whether the repo already works that way". Add definitions of CONSISTENT, CONFLICT, UNVERIFIED, Blocker, Major, Nit to KEY_TEXT (they sit only in SWEEP now); copy the severity sentence from line 127.

## Group D: Exceptions, claims, design gaps (generator lines 72-84, 109-123)

### [D1] D-B4 - Blocker - PROPOSE FIX
Add a claim row (line 109 list): `("the independent count is independent and read-only", "DECISION line 11; ONE-PLACE-TABLE COUNTER", "the only artefact seen is an n8n Code node stand-in (L6-J-034), run in the same n8n and the same Postgres, checked in node only; a real n8n run is NOT VISIBLE; the count's identity and the negative test 'the count identity can write nothing' are in no file seen", "UNVERIFIED")`. Add to Fix plan band 1 (decision only): "say whether the count runs outside n8n; name its identity". Do not change the verdict of the count's place.

### [D2] D-M1 - Major - PROPOSE FIX
Add a Fix plan row (band 3, after the video, same row group as row 4) listing negative tests that exist in no file: alert credential, heartbeat identity, stage.journal writer, the count's Gmail and HubSpot scopes. Add one sentence to the row 4 action: "the n8n role and the app role both live inside the same n8n, so a compromise of n8n gives both; this is stated as a limit, not a fix". DECISION line 14 says three roles; the SWEEP says four: write "three roles in DECISION line 14 plus a fourth identity proposed here; DECISION has not been updated" (ESCALATE item 1 below).

### [D3] D-M2 - Major - PROPOSE FIX
L6-EX-05 and L6-EX-07 name exposures (double alert, a second n8n, review state with no notice, mf-hook key without a source column) as "accepted" while untested. Edit `EX`: change the removal-trigger cells from "none" to dated, testable triggers: EX-07 "test: kill a send in flight and count alerts; do before accepting"; EX-05 "event table (after the video) or the count proves a double send"; and add the sentence "not accepted until tested; listed as a defect with this next step". Add a Claims-check row `("every lead reaches a terminal state and nothing is sent twice", "ORDERS rule on lost and double messages", "state review gets no mail (L2-FD-007); mf_leads keeps only the latest state (L6-EX-05); the double-send window is untested", "UNVERIFIED")`. Add to the Fix plan (band 3): "check the take does not use mf-hook before the video" as a decision for the laptop lead (cheap, no change).

### [D4] D-M4 - Major - PROPOSE FIX
Line 82 (L6-EX-10) widens to three named items, each with who says yes and a removal trigger: (a) tracked credential files (`creds-lane.json`): untrack and rotate, studio head yes; (b) the four n8n working folders with encryption keys (about 220 MB in history): move to `archive/` or untrack, never delete, history rewrite only on the studio head's yes; (c) the SQLite files holding the planted made-up personal data: move out of the tracked tree after the Postgres move, studio head yes. Add: "after a rotation, the lead checks that the rotated values are stand-ins, not real keys (UNVERIFIED here)". Exceptions EX-03, 04, 05, 06, 08: replace "none: ..." by a real trigger, or move them out of the Exceptions table (see D5). EX-04 text "meant to hold no lead data" stays but the reason adds "CONTRADICTED by L2-FD-002 (Claims check)".

### [D5] C-M3 - Major - PROPOSE FIX
EX-03, 04, 05, 06, 08 say "not an exception to the one-store rule" yet sit in Exceptions. Rename the section sub-heads: `Exceptions to the one-store rule` (EX-01, 02, 05) and `Accepted second places that are not exceptions` (EX-03, 04, 06, 08, 09). Keep the ids so the NEEDED rows still resolve; the scan only needs the id. State in the definition line (line 135) which is which.

### [D6] D-M6 - Major - PROPOSE FIX
Add three Claims-check rows with status UNVERIFIED and a reason: "single dependency for the take: n8n (all flows), one SMTP server and the model behind stage have no alternative or trigger written (checklist dependency question); Postgres in DECISION line 18c is already listed"; "SECURITY (egress, retention, redaction), OPS and the workflow walk (kill, restart, out-of-order input, huge input) are not answered for the take: take repo NOT VISIBLE, no runtime"; "tenant isolation: N/A for one client" (already L6-FD-028). Reason text must say "not checked", not "fine".

### [D7] D-B1 part about tests / re-smoke criterion - covered in A1.

## Group E: wording and structure (comprehension) - one edit set in KEY_TEXT (lines 7-18)

### [E1] C-B2 (owner) - Blocker - PROPOSE FIX
Reserve "owner" for the place. Rename the person columns "owner" in Fix plan (line 132) and Exceptions (line 135) to "responsible person". Replace "owner yes" by "studio head yes" in all strings (`grep -n owner` over the generator; "the owner of the dollar cap" becomes "the place that holds the dollar cap" or "the person who names the cap place"). Define: "Job owner place = a place, never a person. Responsible person = the human who does or approves a step." Replace "The studio head = the owner who says yes" (line 9) by "the studio head = the person who runs the studio and says yes to money, archive moves and secret changes".

### [E2] C-B3 (lead) - Blocker - PROPOSE FIX
Rename in all generated text: the sales request becomes "request" or "sales request" in prose (table `mf_leads` keeps its name); "laptop lead" stays; never write bare "the lead". Replace "lead decides" in `RERATE` L1-FD-021 text by "laptop lead decides" and explain "the order" = "the written work order (ORDERS.md) the laptop lead gave this session". Define "Hadavin" = the studio (one-person AI studio) the repository belongs to; the studio head is its head. "Client" = a company that buys a build; in demos the client is made up. `"Session lead"` / "the lead may force-push" in L2-FD-018's text: change to "only the laptop lead may force-push; the Fix plan asks the studio head's yes first" and say that is a two-step rule (resolves C-M8 third point).

### [E3] C-M4, C-M5, C-M6, C-M7 - Major - PROPOSE FIX
Add a glossary block to KEY_TEXT (about 12 short lines), alphabetical, only for labels used in the outputs: canary (a planted fake value used to see whether it leaks), claim (three uses, renamed: "claim insert" for the database step, "claim type" for the finding category, "check statement" for the Claims check), flow, heartbeat, k1b, core Limits, DeadLetter, SpendLedger, film-v5, real-v5, lead states (review, unknown, failed), schema app, stand-in, sweep, take, proof (what the video shows: 10 test requests give 1 new, 9 duplicates, 1 e-mail, 1 CRM row), the video (Wed 18 Nov), this box (this repository checkout without the take repo). Widen the job-key definitions: COUNTER also holds test totals and slot limits; FILTER also holds outbound action gates and scans; LOG also holds audit chains and evidence reports; OTHER holds the identity job. State: "a job key sorts every part of the repository, including build-process parts; those are in the appendix". Id kinds: add WK workflow walk, T test, D doc, EX exception.

### [E4] C-M8 - Major - PROPOSE FIX
Severity cells: `RERATE["L1-FD-021"]` text becomes "false claim in live text, plus personal data in file paths (laptop lead confirms)" and the open-question wording "lead decides" is removed from the cell (it goes to the Fix plan). Replace `"same: a lead in state review..."` (line 28) by "same finding as L2-FD-007; counted once in the deduplicated row" and the matching text for L6-FD-017. Explain "was Major" in the intro once: "was = the lane's candidate severity".

## Escalations (need the laptop lead or the studio head)
1. ESCALATE (D-M1): DECISION line 14 says three roles; the review proposes a fourth identity. The text of DECISION is the laptop lead's; this session may not change it. Next step: the laptop lead decides and updates DECISION; this review writes "proposed, not decided".
2. Open and unchanged by these edits: owner of the dollar cap, owner of the second alert channel, what the take proof counter reads, key rotation and history rewrite (studio head), 183 unread files, everything that needs a runtime.

## Contested (2, both partial)
- B3 (Z-M4 count 48): two other reviewers counted 49 plus 10; resolved by computing the count in code and the lead's `grep -c` (above).
- Z-M1 citation `ORDERS.md:197`: the line does not exist (file has 15 lines); the finding itself stands on DECISION 14 and 16 and is accepted.

## Nits: all fixed in the same push, no new review (round cap)
C8 (J-040 bracket, J-028 file), A3 (cut-off cells), E4 ("same:" wording). Nothing is declined.

## Order for the lead (one batch, one regeneration)
1. Edit KEY_TEXT, RERATE, NOTE, DEDUP, TEXT, PROP, FORCE, CORE, CONFLICT, EX, claims, fixrows, OWNERLINE (groups A-E). 2. Move the L6 row parse, `verdict` and `CORE/FORCE/PROP` block above line 124 so the headline and the Fix plan can use them. 3. `python3 tools/merge.py .`, `python3 tools/write_outputs.py .`, `python3 tools/scan_outputs.py .`, the unit tests, `python3 tools/check_citations.py` (new backtick quotes must match). 4. `grep -c "^| L6-J-"` and the printed deduplicated Blocker numbers go into REPORT.md. 5. Commit and push; no third result round.
