# Not checked, round 1 (lane c): what the take on Wed 18 Nov depends on that no file shows was checked
Written Mon 16 Nov 2026 from files only (REPORT.md top block, STATUS-BOARD.md, ORDERS.md, inputs/DECISIONS-2026-11-16.md, cross-read/other-sessions-r2.md). Nothing run. I do not judge design. Dates: take target Wed 18 Nov (not confirmed); latest start Mon 23 Nov before 18:14:40 UTC; money stop Mon 23 Nov 18:29 UTC (23:59 IST).
Who: "lead" = studio lead on the laptop; "owner" = the owner; "cloud" = this session. "Proof file" = a file that does not exist yet.

## Failures and conflicts first (v14 owner sheet vs other sessions)
1. Credentials: v14 C.3 and go item 4 say exactly two (HubSpot take key, sender mail login); the flows-audit checker take_check.sh expects three (Postgres app role, mail, HubSpot). Following v14 would make the owner stop on a correct setup. Nobody is named to type the Postgres one (blank B1). (other-sessions-r2 item 1)
2. n8n sign-in: v14 C.3 has the owner sign in to read the credential list; the run-day card and decision 7 say the owner never signs in (first-visit setup done). One must go.
3. MF_* names: v14 I.6 and B8 name MF_* settings; real-v5 reads only DESK_URL, DESK_TIMEOUT_MS, DESK_ALERT_TO. MF_* belong to film-v5, cut by decision 1.
4. Step 0 of v14 creates then deletes a HubSpot contact with a probe app; decision 2 says the take never deletes. Different identity, but v14 does not say "probe app, not the take key".
5. v14 has had no review yet (four reviews running); v13 failed all four (stranger 8 majors, security 7, adversarial 20). About 20 values only the lead has are blank (L1-L20, B1-B13).

## Not checked, ranked by risk to the money stop and the narrow claim
Narrow claim = "a lead sent twice with the same id is processed once".
| # | Dependency | Who checks | File that would prove it | Deadline |
|---|---|---|---|---|
| 1 | Backstop counter (the program's own ledger) is cumulative, survives retakes, and stops at the cap; 180 vs 189 figure not chosen; retake count not computed | lead | ledger code read at the final head plus one fake-model run log | Tue 17 Nov; before any live key is typed |
| 2 | Program refuses to call the model after 18:29 UTC Mon 23 Nov (end date in code, not by eye) | lead | the date check in run_real_check_n8n.py with a test that fails after the date | Tue 17 Nov |
| 3 | Nothing can spend before the owner's typed y (S9-1/S9-4 deferred, no closed gate exists) | lead | a run log showing no model call before y, on fake model | Tue 17 Nov |
| 4 | Program does not re-read the settings file after start ("do not edit settings after start" is only a rule) | lead | read of the settings loader at the final head | Tue 17 Nov |
| 5 | Run-key cancel: owner cancels the run key and all older model keys the same day; v13 emergency cancel spared the run key | owner, sheet reviewed by security lane | v15 sheet plus owner's pasted "keys listed: 0 active" after the take | take day; no later than Mon 23 Nov |
| 6 | Unique index on lead_key and ON CONFLICT DO NOTHING really exist (claim rests on reading mf-form.json:97 only; "index not seen") | cloud then lead | psql \d output of mf_leads at rehearsal | before first rehearsal, Tue 17 Nov |
| 7 | Real-v5 lease value (45, 20, 120 s all seen in other sets; none read for real-v5) and that a re-claim after a crash may repeat a model call and cost | lead | flow JSON read plus crash-test result (row DM, empty today) | Tue 17 Nov; wording A or B before filming |
| 8 | Two sends of one lead id in a real n8n run give one stored row, one mail, one contact | lead | rehearsal screenshot or Postgres preview (decision 9) | Wed 18 Nov rehearsal |
| 9 | n8n has never been run: import, activation by n8n_api.py, credential ids filled, port 5690 free | lead | n8n_api.py output and the loopback re-smoke log ("real-v5 minus CrmUpsert") | Tue 17 Nov |
| 10 | Take port is named in no file (decision 6; take template has no N8N_PORT line) | lead | the plan with one named port | Tue 17 Nov |
| 11 | Take-branch files are on no pushed branch: run_real_check_n8n.py, fill_flows.py, drive.py, n8n_start.sh, n8n_kill.py. Every cite to them is inferred. Head de6b574 and "13 sends" are unbacked | lead | git ls-files of the final head, listed in the plan | Tue 17 Nov |
| 12 | n8n_kill.py exit 3 (unreadable n8n process) handled as STOP in the plan; plan edit prepared but unrun | lead | plan section P-5 with the check and one kill run | Tue 17 Nov |
| 13 | Postgres and take database names, role, clean start (lead empties mf_leads), alert_* columns present (psql check) | lead | filled run card plus psql output | before rehearsal |
| 14 | HubSpot probe: 7 calls, US$0, scopes, owner pastes PASS/FAIL table; take key read-only and separate | owner (runs), lead (reads) | the pasted table in a file | Tue 17 Nov; owner needs notice |
| 15 | Exit-code rule for case C (error after the y question, mails may exist) not stated by any file; v14 must not claim "exit 1 = nothing sent" | lead | exit codes read from the program at the final head | Tue 17 Nov |
| 16 | Mail: two Gmail app passwords, SMTP credential works, receiver mailbox shown on screen | owner, lead | a sent-and-received made-up mail log | Tue 17 Nov |
| 17 | Proof screen for counts and who films; how the lead sees the pause (card step 17 "UNKNOWN") | lead | rehearsal screenshot | Wed 18 Nov |
| 18 | Run 9514 (full patch run) was on a tree with A-01 and C-01 applied, which decision 4 defers or cuts; no run of the final patch set | cloud (C7) | a run log on the chosen tree | before take; not on the take path |
| 19 | Post wording and who approves it (the one sentence, plus the lead telling the owner the crash-test result) | lead, owner | v15 step J | before posting; Wed 25 Nov 15:00 UTC |
| 20 | "one Postgres server, two databases" caption; DECISION-one-store line 14 still says "ONE database" | cloud | edited line 14 | Tue 17 Nov |
| 21 | Never run anywhere: PowerShell, shellcheck, WSL, the 455 Postgres tests; the owner's steps were never done by a stranger | lead | any run log | Tue 17 Nov, or a "UNVERIFIED" caption in the take notes |

## Not read or not run by this lane
I did not open the flow JSON, mf_leads.sql, or any script; I only read the five named files. Row 6 and 7 are inferred from REPORT.md and other-sessions-r2.md. Whether a Wed 18 Nov take fits is unknown: the owner has not confirmed, and retakes before Mon 23 Nov 18:14:40 UTC are the safety margin, with rows 1 to 3 as the money guard.
