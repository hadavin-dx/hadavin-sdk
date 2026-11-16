# Evidence check for decisions D-01 to D-04 (read-only; made-up data only)

Status: DRAFT, unverified

Written Mon 16 Nov 2026 by an evidence-check session. Reader: the lead session. Nothing was run. Every quote below was read from the file on disk at the line given. I did not open any program (`scripts/run_real_check_n8n.py` is not in the checkout), so nothing here says what the program does.

Short names (same as work/decision-list-for-lead.md): "v3" = inputs/OWNER-STEPS-realrun-v3.md; "v5" = inputs/OWNER-STEPS-realrun-v5-core-hardening.md; "plan" = inputs/plan-wp6-resmoke-v5.md; "scope" = inputs/AGENT-SCOPE-DO-AND-DONT.md; "DEC" = inputs/DECISIONS-2026-11-16.md; "store" = inputs/DECISION-one-store.md. The decision list gives no "A or B" letters, so "recommendation" below means what its table row says.

## Finding that affects all four rows (read first)
The recommendations for D-01, D-02, D-03 and the first half of D-04 say "change steps v3 line N". But DEC line 11 (decision 10) says: "OWNER-STEPS v4 and later replace v3 (archive v3, never delete)". decisions/D04-D05.md line 5 says: "v3 is archived (decision 10), do not edit it." So an edit to v3 is edit-to-an-archived-file. The live file is v5. I searched v5 for the v3 passages:
- v3 line 75 (port 5678): v5 has no port number 5678, 5679 or 5690 at all (grep found none). The n8n step in v5 is line 90 and says only "The studio lead sends you the n8n address".
- v3 line 78 (Postgres password): v5 has no step where the owner sets a Postgres password (grep for "password" finds only app passwords and the n8n owner login; the word "Postgres" appears only at v5:22, 91-less, 208, 213).
- v3 line 69 (HubSpot read-only token): v5 has no read-only-token step (v4 diff list line 13 says the HubSpot and key steps were cut as done).
So D-01 and D-02 may be mostly moot in v5, and the useful edit for D-03 is in v5 lines 127 and 130, not v3:69. The lead should decide whether to answer D-01 to D-03 as "no edit needed, v3 is archived" or to point the edit at v5.

## D-01: which n8n does the owner type secrets into (port 5678 or the take's own port)

Question in plain words: v3 tells the owner to open n8n at port 5678. Is that the owner's own n8n (wrong place for the take's secrets)?

Recommendation (decision list): keep the plan text (take n8n at 5690); change v3 line 75.

Evidence quoted:
- v3:75: "open it in your Windows browser at the address the lead gives (it should be `http://localhost:5678` or similar; UNVERIFIED that Windows reaches WSL there, WP6 check (e))."
- DEC:7 (decision 6): "Ports: rehearsal 5690; the real take uses its own free port too (5678/5679 are the owner's own); the plan names it in one place."
- plan:121: "ports (127.0.0.1) | take n8n 5690, broker 5691; control n8n 5692, broker 5693; ... Owner's 5678/5679 recorded in P-1 and 13.7, never touched"
- plan:271: "N8N_LISTEN_ADDRESS=127.0.0.1 N8N_PORT=5690 N8N_RUNNERS_BROKER_PORT=5691"

Verdict: SUPPORTED on the substance (5678 is the owner's own n8n; v3 would point at it). CITE IMPRECISE on one point: plan:121 and plan:271 are the loopback rehearsal ("re-smoke", plan line 5), and DEC:7 says 5690 is the "rehearsal" port and that the real take uses "its own free port too". So "the take n8n runs at 5690" is true for the rehearsal only; the real take port is not in any file. The recommendation text "Keep the plan text (take n8n on port 5690)" should read "rehearsal n8n on 5690; real take port to be named".

Still unknown: the real take port (nobody named it; plan section 10, plan:505, lists no `N8N_PORT` line for the take template); whether v3 or v5 is the file that gets the edit (see top finding); whether the owner still needs to open n8n at all (v5:90 says "only if the studio lead asks"; DEC:8 says first-visit setup is already done).

## D-02: one Postgres password or separate roles with their own password files

Question in plain words: v3 says the owner types one Postgres password into n8n, the one set when the database starts. The plan builds several database logins, each with its own password file. Which is right for the take?

Recommendation: keep the plan text (separate roles and password files); change v3 line 78.

Evidence quoted:
- v3:78: "**Postgres**: host, database, user as the lead names them; password = the one you set in WSL when you start the database (the lead gives the start command; you type the password)."
- plan:122: "superuser `postgres` (setup only, `pg.pw`); `smk_n8n` (`pg-n8n.pw`; owns database `n8n` ...); `smk_app` (`pg-app.pw`; ... SELECT/INSERT/UPDATE on `app.mf_leads`, search_path app); `smk_count` (`pg-count.pw` ... SELECT on `app.mf_leads` ...)"
- plan:126: "credentials ... `smkPg00000000001` (user `smk_app`)"
- plan:127: "32 hex x4 (superuser, n8n, app, count passwords)"
- store:14: "three least-privilege roles (n8n, the app role the n8n Postgres nodes use, a read-only role for the independent count)"
- DEC:4 (decision 3): "ROLES-PROPOSAL (four logins) is PARKED as client build / after the video; read-only group L is not run before the video; no new lanes on it."
- plan:505 (section 10): the lead "sets the take's real-v5 Postgres credential to the app role and the take script's count user to the read-only role".

Verdict: PARTLY SUPPORTED. The plan does build four separate passwords for the REHEARSAL (plan:122, :127), and v3:78 does describe one owner-set password, so v3 and the plan disagree. But two files weaken "keep the plan's roles for the take": (1) DEC:4 parks a "ROLES-PROPOSAL (four logins)" until after the video; the files do not say whether that is the same thing as the plan's four password files (UNVERIFIED), and if it is, the take may run with fewer roles; (2) store:20 says the question "whether the real-v5 flows' Postgres access uses the three roles above or one role today" is "Not decided / UNVERIFIED". The rehearsal also generates the passwords with `openssl` by the lead (plan:270), which is different from the owner typing his own password.

Still unknown: whether the real take uses one role or three; who creates the app-role password for the real take and how the owner uses it without the lead reading it (v5:57 "Never send the studio lead a password"); whether ROLES-PROPOSAL = the plan's roles. Suggest the lead's answer waits on that, or says "other:" with the role count for the take.

## D-03: HubSpot app 1 is read-only, but `end` may delete

Question in plain words: the owner is told to make a read-only HubSpot token. If the program's last step (`end`) deletes the made-up contacts, a read-only token fails after the mails are sent. Does the take delete or not?

Recommendation: change v3 line 69 to say the token is read-only only after `end` stops deleting; until then the owner deletes leftover contacts by hand.

Evidence quoted:
- v3:69: "App 1 for the take program, scope contacts **read** only."
- DEC:3 (decision 2): "TAKE IDENTITY is read-only: the take never deletes contacts; leftover made-up contacts are listed by lead key and contact id and the owner deletes them by hand in HubSpot after the take".
- scope:20: "at the end ARCHIVE the take's own HubSpot contacts, which the code does as a DELETE call (`run_real_check_n8n.py:1051`, `crm_hubspot.py:504-509`, per `review-codebase-1.md` F-01)"; "NOTE (F-01, CODE-CHANGE-NEEDED, not fixed here): OWNER-STEPS:69 sets HubSpot app 1 to read-only, but the archive is a DELETE: a read-only token passes the pre-take GET probe and fails only at archive after the sends".
- v5:127: "The program then deletes this run's contacts." and v5:130: "If the HubSpot key the program uses cannot delete contacts, the deletion can fail after the sends."
- decisions/M17-end-never-deletes.md (line 3): "Decision proposed ... Status: PROPOSED, on HOLD ... Unchecked: what `end` does today ... assume `end` may permanently delete until the lines are quoted." Its "Quoted lines" section is empty.

Verdict: SUPPORTED. The conflict is real in the documents (scope:20 says the code deletes; DEC:3 says the take never deletes). The recommended wording follows both: read-only only after the program is changed, hand deletion until then. Two corrections: (1) v3 is archived, so the live place is v5:127 and v5:130 (v5 has no read-only-token step; v5:130 is where "key cannot delete" appears), and decisions/M17-end-never-deletes.md already lists V5 lines 124-130 as the sentences to change, so D-03 overlaps M17; (2) drift/REPORT.md line 1 says row D-03 is stale (decisions 1, 2, 5, 12; M17), so its old "read and write" fix text must not be used.

Still unknown: what `end` really does today (the code cites in scope:20 were not opened; the program is not in this checkout); who changes the program and by when (M17 gives a proposed due time of Tue 17 Nov 03:30 UTC / 09:00 IST, "nobody has agreed"); whether the owner may start the by-hand delete before a release message is sent (M17: undecided).

## D-04: the post claims more than "the same lead id sent twice is processed once"

Question in plain words: the owner's public post text lets him also say the code caps spending, asks the model once per lead and counts mails and contacts with a separate check. Do the files support that, or only the one sentence?

Recommendation: keep only the claim "the same lead id sent twice is processed once"; remove the longer claim from v3:131 and v5:164.

Evidence quoted:
- v3:131: "our code caps the spend, asks the model once per lead and counts the mails and contacts on its own credentials; **a lead sent twice with the same id is processed once**."
- v5:164: "our code caps the spend, asks the model once per test person, and counts the mails and contacts with a separate check of ours; **\"the same lead id sent twice is processed once\"**"
- v5:171 (already in the "must NOT say" list): "that the count is made with an independent login (until that login is built and shown to run)."
- DEC:2 (decision 1): "narrow claim: a lead sent twice with the same id is processed once".
- scope:15-16: the cap "(backstop setting, US$180 of 189 at the time of writing, checked by a human)"; "The cap and the window end are `stage.env` settings, a BACKSTOP checked by a human, not a guarantee"; "'One paid call per key' holds per take folder only".
- store:28 (c): "The read-only count role is not built (one `PG_USER` via `docker exec psql`): the count is not yet an independent-credential check."
- decisions/D04-D05.md:12-13: "Decision 1 (16 Nov) allows ONE claim ... The spend limit is a setting a person checks, not a guarantee. The count with its own separate login is not built."

Verdict: SUPPORTED. All three overclaims (spend cap, once-per-lead model call, separate count) are contradicted or weakened by scope:15-16 and store:28. One cite note: the decision list cites "steps v5:171"; that line already forbids the independent-login claim, so v5 is half-fixed already, and only v5:164 still carries it. Also v3 is archived, so the edit belongs in v5:164 only.

Still unknown: the owner's choice whether a longer architecture sentence stays (decisions/D04-D05.md:16: it must not mention the cap or the separate count login); who may edit v5 step J (decisions/D04-D05.md:9 says "No file states who owns it (UNVERIFIED)"); whether "asks the model once per test person" can be said at all (scope:14 calls "one paid call per key" an upper bound and per take folder only).

## Summary table

| Row | Recommendation supported? | Cite problems | Open |
|---|---|---|---|
| D-01 | Supported (5678 is the owner's own) | 5690 is the rehearsal port, not the real take port (DEC:7); v3 is archived and v5 has no port text | real take port not named |
| D-02 | Partly supported | store:20 and DEC:4 leave the real take's role count open; v3 archived, v5 has no password step | roles for the take; who makes the app-role password |
| D-03 | Supported | live edit place is v5:127 and v5:130, not v3:69; overlaps M17 (on HOLD, "Quoted lines" empty) | what `end` does today; who changes the program |
| D-04 | Supported | v5:171 already holds the independent-login ban; only v5:164 needs the edit | owner choice on a longer sentence; who edits step J |

Not checked: the program and flow files (not in the checkout); any run result; whether v3 is physically archived (decision 10 says so; I did not look for an archive folder).
