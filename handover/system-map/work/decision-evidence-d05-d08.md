# Evidence check for decisions D-05, D-06, D-07, D-08

Status: DRAFT, unverified

Checker: evidence checker (read-only, no commands run on the system, no sub-agents, no spend). EGM skipped: read-only evidence check; the lead session runs the egm:* review. Made-up data only.

What I did: opened every cited line in the files below and copied the words. I did not run anything. I did not judge the recommendations beyond "does the cited text say what the decision list says it says".

Short names (all under `/home/user/hadavin-sdk/handover/system-map/` unless stated):
- "list" = `work/decision-list-for-lead.md`
- "plan" = `inputs/plan-wp6-resmoke-v5.md`
- "v3" = `inputs/OWNER-STEPS-realrun-v3.md` (archived by decision 10), "v5" = `inputs/OWNER-STEPS-realrun-v5-core-hardening.md`
- "scope" = `inputs/AGENT-SCOPE-DO-AND-DONT.md`
- "one-store" = `inputs/DECISION-one-store.md`
- "decisions" = `inputs/DECISIONS-2026-11-16.md`
- "D04D05" = `decisions/D04-D05.md` (read only), "report" = `drift/REPORT.md`

Result table:

| Row | Verdict |
|---|---|
| D-05 | supported |
| D-06 | supported, but one cite is incomplete and the file to edit is archived |
| D-07 | supported |
| D-08 | supported (as PROPOSED, not DECIDED); one point the cites do not settle |

Things I found that the lead should know before answering (first, because they are the uncertain parts):
1. There are TWO files named `DECISION-one-store.md`: `system-map/DECISION-one-store.md` and `system-map/inputs/DECISION-one-store.md`. They differ (checked with `diff`: line 7 differs, and the `inputs/` copy has extra lines 21 to 28 with the corrections). All line numbers in the list (14, 23, 26, 28) match the `inputs/` copy. I do not know which copy the system-map session is meant to edit. Not resolved.
2. Nothing I read shows that the mail-crash test, the four role checks (P-A1, P-A2, P-C1, P-C2) or the re-test itself has run. The plan's result columns are empty and the list says "none has run". I did not search outside `system-map/`, so "not run" is "no evidence of a run found", not proof it has not run.
3. The program files `scripts/run_real_check_n8n.py` and `scripts/n8n_drive.py` are not in the checkout (list line 26), so anything about what the program does is unverified here.

---

## D-05: the crash limit for "processed once"

**Question in plain words.** The post will say "the same lead id sent twice is processed once". The plan says that must not be called crash-safe until a crash test (stop the system after the mail is sent and before the lead is marked finished, then see if a second mail goes out) passes. Does the owner's step text say the same, and who tells the owner the test result?

**Recommendation (list line 17).** Keep the plan text. Add to the post step: the owner is told the test result before posting.

**Quoted evidence.**
- plan:476 (row DM): "crash with the lead mail stored and its ack held (before MarkDone): ends `unknown` + 1 alert or `done`, `mails == 1` | GO finding for the run if `mails >= 2` (ledger) and it BLOCKS the claim: "DM mails >= 2: 'processed once' does NOT hold for a crash between SMTP send and MarkDone; the take is not claimed crash-safe until fixed or the owner accepts in writing." E MISSED -> one repeat as E2; E2 also MISSED -> the same limit (window untested)". The last two columns (result columns) of the row are empty: `| | |`.
- plan:505: "Row DM in every owner-facing claim (design M4, lead ruling c): if DM shows `mails >= 2`: "'processed once' does NOT hold for a crash between SMTP send and MarkDone; the take is not claimed crash-safe until fixed or the owner accepts in writing." If E and E2 were both MISSED, the same limit applies with "untested" in place of "does NOT hold". Only a DM PASS lets the claim cover that window."
- v5:170 (inside step J "It must NOT say"): "- that the run is crash-safe (unless the rehearsal's crash test passed);"
- v5:172: "The exact final words come from the studio lead after the rehearsal. Until you have them, do not post."
- D04D05:19-20 (read only): the problem is described the same way; line 20 proposes the text to add: "The studio lead tells you the result of the mail-crash test before you post. If it showed a double mail, or the test was not run or missed the moment, do not post the sentence above as it stands. The studio lead gives you the exact limit wording, and you accept it in writing or the post waits."
- report row D-05 (report:35) gives the same fix for the older v3 step 23.
- v3 step 23 (v3:131) has no crash condition at all: "...**a lead sent twice with the same id is processed once**. It must NOT say: the same person through two doors is one lead; no lead data stays in n8n; recovery within 60 s; alert within 30 s."

**Verdict: supported.**
- The plan lines say what the list says. v5:170 is looser than the plan in three ways, all visible in the quotes: it says only "unless the crash test passed" (no owner written acceptance, no "untested" case when both tries miss the moment, no statement that the owner is told the result); v5:172 gives the studio lead the final words but does not name the crash result.
- Cites are right: plan:476, :505; v5:170; D04D05:20.

**Still unknown.**
- The crash test result: empty today (plan:476 result columns blank). No file I read says it has run.
- Whether the test needs Docker in the cloud session (D04D05:23 says UNVERIFIED).
- Who edits step J in v5: D04D05:9 says no file states the owner of v5 (UNVERIFIED).
- D04D05:20 adds a second limit not in the list row: "inside one take folder" (one paid model call per lead id). The list row does not carry it. That text points to report line 75 (D-18); I did not open D-18, so that part is unchecked here.

---

## D-06: how "executions saved" is set and switched off

**Question in plain words.** n8n keeps a history of each run. For the take the owner allowed saving it (made-up data only). Is the saving switched on once for the whole take through two lines in the take's settings file, or flow by flow? And how are the saved runs deleted afterwards?

**Recommendation (list line 18).** Keep the plan text (saved by lines in `n8n.env`; clean-up removes the database container). Reword v3 line 121.

**Quoted evidence.**
- plan:125: "executions (take) | `EXECUTIONS_DATA_SAVE_ON_SUCCESS=all`, `EXECUTIONS_DATA_SAVE_ON_ERROR=all`, `EXECUTIONS_DATA_SAVE_ON_PROGRESS=false`, `EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS=false` (owner 2026-11-16; made-up data only)". The list says "two lines"; the plan has FOUR `EXECUTIONS_DATA_SAVE_*` lines (two set to `all`, two to `false`). The list's "two lines" is a loose count.
- plan:271 (step 1.2) writes those four lines into `$T/n8n.env` (`printf ... EXECUTIONS_DATA_SAVE_ON_SUCCESS=all EXECUTIONS_DATA_SAVE_ON_ERROR=all ... >> $T/n8n.env`).
- scope:9 (the line starting "PROCEDURE or `n8n.env` content"): "...so save successful production executions ON for the take only; the take data is made up; the lead deletes the executions and turns saving off at clean-up; ... it holds only if the n8n.env content and the clean-up say so)." So the scope file also treats it as a take-wide setting.
- v3:121 (step 22 item 1): "The lead: deletes the 3 credentials in n8n, deletes all saved executions of the take (made-up data only, owner decision 2026-11-16), turns "save successful production executions" back off in each workflow, stops n8n, removes the take folder and the Postgres container."
- Deletion method: plan:97 "(deletion = container removal, 13.6)"; plan:482 (row E5) "execution history saved ON (status counts); deletion = container removal only"; plan:502 "The execution clean-up method at the real take (here deletion = container removal)". Also plan:81 "the execution clean-up method at the real take is undecided (here: container removal)".

**Verdict: supported, with two corrections to the list.**
- (a) Cite wrong in part: the list cites only plan:125 for "clean-up removes the database container". Plan:125 says nothing about clean-up. The right cites are plan:97, :482, :502. Plan:81 also says that for the real take the clean-up method is "undecided".
- (b) The list says v3:121 "words it as a per-flow setting". True for the phrase "back off in each workflow". But the same v3:121 line also says the lead "removes the take folder and the Postgres container", which already covers the global setting and the stored runs.
- (c) v3 is archived by decision 10 (decisions:11: "OWNER-STEPS v4 and later replace v3 (archive v3, never delete)"). I grepped v5 and v4 for "each workflow", "save successful" and `EXECUTIONS_DATA`: the only hit is v5 line 4 (a header). So the per-flow wording exists only in the archived v3. Editing v3:121 edits an archived file; the current v5 has no clean-up wording to fix. I do not know whether the system-map session may edit an archived file.

**Still unknown.**
- Whether the flow JSON files carry their own save setting that overrides the global lines. The plan's check (12.5b, plan:404) only shows that the total of saved runs is above 0; it does not prove who set it. Not verified because the flow files were not read.
- What the real take (not the re-test) does for clean-up: plan:81 says undecided.
- Whether container removal really deletes all saved runs: this is the plan's own statement, not tested.

---

## D-07: the one-store decision text still describes an old plan

**Question in plain words.** The decision file for "one database for the take" (line 14) describes n8n's own data as "in its own schema or database" and says the three database roles and the `app` area are not in the re-test. The current plan builds a separate database called `n8n` and does build and test the roles. Which text is right?

**Recommendation (list line 19).** Keep the plan text (no schema line; database named `n8n`). Mark one-store line 14 as stale.

**Quoted evidence.**
- plan:272 (step 1.2b): "n8n engine = the one Postgres, its own database, through the n8n role: ... `DB_POSTGRESDB_DATABASE=n8n DB_POSTGRESDB_USER=smk_n8n` ... No `DB_POSTGRESDB_SCHEMA` line (n8n's default schema `public` inside database `n8n`)."
- plan:122: roles `smk_n8n` (owns database `n8n`), `smk_app`, `smk_count`, with their rights.
- plan:281 (step 1b.2, the script): `CREATE DATABASE n8n OWNER smk_n8n;` ... `CREATE SCHEMA app;` ... `GRANT SELECT, INSERT, UPDATE ON app.mf_leads TO smk_app;` ... `GRANT SELECT ON app.mf_leads TO smk_count;`.
- one-store:14 (decision 1, still in the old words): "n8n's internal data in its own schema or database, our claim table `mf_leads` in an `app` schema, three least-privilege roles ... Open: whether n8n honours DB_POSTGRESDB_SCHEMA for both the import commands and `n8n start` (UNVERIFIED item 6); the `app` schema, the three roles and saved execution history are NOT in the re-smoke (listed as not proven)." The same line also cites "wp6/plan-wp6-resmoke-v1.md", an older plan version than the current v5.
- one-store:26 (correction a): "...which for the re-smoke lives in a SEPARATE database `n8n` owned by the role `smk_n8n` (the lead's instruction 2026-11-16; before that n8n ran on its default SQLite...)". The same file therefore contradicts itself.
- decisions:11 (decision 10): "Wording: "one Postgres server with two databases (n8n's own and the take's)"; fix DECISION-one-store line 14."
- plan:456 (rung table row): "Postgres roles, separate database | ... | `DECISION-one-store.md:14`; design M1 | nothing | CUT-TO-CONFIG". The plan itself cites line 14 as its source for the roles.
- report:37 rates D-07 "Major" (the list says rows D-06 to D-08 are rated Major at report lines 36-38; I confirmed the three rows sit on report lines 36, 37, 38).

**Verdict: supported.** All cites open at the quoted words. Decision 10 independently asks to fix line 14, which makes the recommendation stronger than the list says.

**Corrections / notes.**
- The recommendation says "mark line 14 as stale". Decision 10 says "fix line 14" (change the wording), not only mark it. These are different edits; the list does not note that. The report's own fix for D-07 (report line 37) is "Replace in DE:14: ...", a replacement, not a stale mark.
- The "NOT in the re-smoke" statement in line 14 is also false against plan:281 and plan:99 ("Proven by this run ONLY if S1b passes (three roles; negative tests N1-N10...")).
- Two copies of the file exist (see top note 1).

**Still unknown.**
- Whether n8n 2.x honours `DB_POSTGRESDB_SCHEMA` (UNVERIFIED item 6): moot for the plan, which sets none.
- Whether the plan v5 itself passes: not run, as far as I can see.
- plan:272 says `smk_n8n` owning `public` inside database `n8n` is enough for n8n's migrations: plan:284 marks this "UNVERIFIED 4".

---

## D-08: how the table `mf_leads` is found (schema versus search path)

**Question in plain words.** The claim table `mf_leads` sits in a database area called `app`. The program that reads the counts and the n8n flows ask for `mf_leads` without saying `app`. A database login finds it only if its "search path" (the list of areas it looks in) includes `app`. The plan sets that per login. The decision file still says "qualify it in code or fix the search path" and calls it a code change. Which is the decided way?

**Recommendation (list line 20).** Keep the plan text (role-level `search_path = app`; flows use `mf_leads` unqualified) and write it into one-store as PROPOSED, not DECIDED.

**Quoted evidence.**
- plan:281: `ALTER ROLE smk_app SET search_path = app;` and `ALTER ROLE smk_count SET search_path = app;`
- plan:284: "The flows only use `executeQuery` with unqualified `mf_leads` (film-v5: no DELETE, CREATE, TRUNCATE), so SELECT/INSERT/UPDATE plus `search_path=app` is the full need of `smk_app`."
- plan:289 (the four probes, in step 1b.3): `q P-A1 smk_app postgres "SHOW search_path"; q P-A2 smk_app postgres "SELECT count(*) FROM mf_leads"; q P-C1 smk_count postgres "SHOW search_path"; q P-C2 smk_count postgres "SELECT count(*) FROM mf_leads"`. Expected (plan:293): "P-A1 and P-C1 `app`; P-A2 and P-C2 `0` (the unqualified `mf_leads` of `n8n_drive.py` resolves through the count role's search path)."
- plan:505: "...the lead ... sets the take's real-v5 Postgres credential to the app role and the take script's count user to the read-only role with `search_path=app`; edits AGENT-SCOPE lines 7-10 ..." (this is a config step by the lead, after the checks pass).
- one-store:28 (correction c, left open): "OPEN, CODE-CHANGE-NEEDED (M-1, not fixed here): `mf_leads` is placed in an `app` schema above, but `n8n_drive.py:40-41` queries an unqualified `FROM mf_leads` as one `PG_USER`; if the table is in `app` and the role's search_path lacks it, every table read fails ... Fix in code (qualify as `app.mf_leads` ...) or state the search_path / public-table choice here and in the runbook. The read-only count role is not built (one `PG_USER` via `docker exec psql`): the count is not yet an independent-credential check."
- one-store:23 (owner confirmation, open corrections): "(b) mf_leads sits in an `app` schema but n8n_drive.py:40-41 queries an unqualified mf_leads with one PG_USER: qualify it or fix search_path; (c) the read-only count role is not built (one PG_USER via docker exec psql)."
- scope line 20 (also called CODE-CHANGE-NEEDED about a different item, the HubSpot archive; the list's reason text for D-08 that "SC:20 ... still call it CODE-CHANGE-NEEDED" is from report row D-08, not something I re-read in scope:20 for the search path).
- plan:81 (carried item 6): "the count role's password is never exercised (`n8n_drive.Table` uses `docker exec` over the trusted local socket)".
- plan:99: least privilege "Proven by this run ONLY if S1b passes ... and the independent count (`smk_count`) really ran through those roles."
- decisions:4 (decision 3): "ROLES-PROPOSAL (four logins) is PARKED as client build / after the video; read-only group L is not run before the video; no new lanes on it."

**Verdict: supported, as PROPOSED.** The plan does make the choice (config: role-level search path) and gives four probes for it. None has a result yet, so "PROPOSED, not DECIDED" matches the evidence; calling it DECIDED would claim more than the plan shows. Cites are right: plan:281, :284, :289, :505; one-store:23, :28. Minor: the list cites plan:293 only for the expected results, which is where the P-A1 to P-C2 expected values sit; the probe commands are at plan:289.

**Still unknown (the parts the cites do not settle).**
- Whether the real program (`n8n_drive.py`) will use the count login at all. Plan:81 says the count role's password is never exercised because the program uses `docker exec` with one user. Plan:289 tests the role with `psql` (privileges only), not through the program. So the probes prove the role's settings, not that the program's count reads go through it. The program is not in the checkout.
- Whether decision 3 (decisions:4, "four logins parked", "read-only group L is not run before the video") conflicts with the plan's three roles plus the count role. I read it as a different, larger proposal and not a conflict, but no file says so. A lead ruling would settle it.
- Whether the read-only count login is "built" for the take: one-store:28 and :23 say not built; plan:505 says the lead sets it after the checks pass. That is a config step in the plan; whether the program accepts a separate count user (code) is unverified.
- Probe results: none seen.
