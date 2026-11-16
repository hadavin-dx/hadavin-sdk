# v6 open questions only the studio lead can answer (each with the missing input)

L1-L18 carry over from v5 (same numbers; updated where v6 changed). L19 and up are new. The owner sheet shows the default for each (run card, rows 1-12).

| # | Question | Exact missing input | Owner sheet place |
|---|---|---|---|
| L1 | Which folder holds `scripts/run_real_check_n8n.py` for the retire check, and does it need the run folder? | folder and exact command line | step I.4 |
| L2 | v6 treats the run name as needed BEFORE step A (it is the setting `TAKE_TAG` in the run settings file and in the test addresses; source: v3 lines 97 and 170). Confirm; give the accepted pattern | pattern; confirmation | Words box "Run name" |
| L3 | How does mail addressed to an `example.com` test address reach the receiver label `demo`? | the mail path (plan does not say) | Words box "Test person" |
| L4 | Run date, how many days or hours before it steps B-D start, latest start time, deadlines for watching (H) and clean-up (I); whether the aim of posting by Wed 18 Nov (ORDERS 017) changes the run date | dates and times in UTC and IST | Dates, run card rows 1, 3, 7 |
| L5 | Worst-case price per model call and the money spent so far | numbers | What the run can cost, step A |
| L6 | Path of `stage.env` (in the re-smoke it is in the take folder, plan 1.2; for the real run nothing says) and is it safe for the owner to open | path, confirmation | step A |
| L7 | Who films, starts the recording, edits, and tells the owner the contact list is filmed | names or roles | run card row 4, steps D, F |
| L8 | Who types the n8n stop and restart during the run (v3 says the lead does it by hand; the scope sheet says "by hand"; no input says who types) | person and exact command | run card row 5, table row "Run: n8n stop and restart" |
| L9 | Is the label `demo` already made and a filter applying it (not in FACTS) | yes/no, how | step C.1 |
| L10 | Is an n8n sign-in needed at all (FACTS says the n8n account and its connections exist; the re-smoke imports credentials and flows through the command line, plan 2.3-2.6); the connection list differs (v3: HubSpot, mail sending, database; FACTS: HubSpot, Claude, Gmail); address, secret file per connection, show command | all | run card row 9, step C.3 |
| L11 | How long does HubSpot keep a deleted contact (step 0 shows permanent vs archived but not the duration) | duration | Words box "Delete" |
| L12 | Is a trial run on the live accounts done before the recording run | yes/no | run card row 6 |
| L13 | Names of the secret files and their folder; does `shred` exist in the owner's WSL | list; yes/no | step I.6, step 0 |
| L14 | Does a Gmail list row show another address (sender column); which Gmail screen is safe to film; may the receiver's own address show | check result | step D.1 |
| L15 | Which screens are the proof-screen candidates (v6: n8n list of runs only if n8n sign-in is asked) | list | step E, run card row 10 |
| L16 | Who checks the post text against the must-not-say list | name | step J, run card row 11 |
| L17 | Path of the run settings file and a promise to keep it until the retire check passes | path | Words box, step I.4 |
| L18 | Final claim words after the rehearsal | text | step J |
| L19 | Step 0: which script copy is current? v6 read a copy under `/tmp/c8b/.../hubspot_probe.py` (evidence folder), not a current one. Folder to `cd` to, secret file name holding the key the run program will use, what a pass looks like for this run (all rows PASS or SKIPPED per the script's exit code), whether a failed "delete" row blocks the run or means hand deletion | folder; file name; rule | step 0 |
| L20 | Rehearsal-pass gate before the written yes: no plan or order names it (v5 invented it). Keep it as the lead's gate? | yes/no | step A |
| L21 | Retire check tests only the mailbox and HubSpot logins (scope sheet section 3: 2 of 4 secrets). Who retires the model key and the database passwords, and how is it checked? | person, check | step I.5 |
| L22 | Is the HubSpot private app deletion (v3 step 22.3) still wanted? It is not in the FACTS owner-only list. Which secret file belongs to which private app (no mapping exists)? | yes/no; mapping | step I.2 |
| L23 | Names of the app passwords to revoke (v3 names them `desk-read`, `desk-send`; FACTS says the owner saved new ones) | names | step I.1 |
| L24 | Does the Chrome profile `demo-take` already exist; is C.2 wanted (not in FACTS) | yes/no | step C.2 |
| L25 | Is the failed-run clean-up (step G, from v3 step 20) wanted as written (not in FACTS) | yes/no | step G |
| L26 | How long is a normal run, and how long may it show no new line before the owner tells the studio lead | minutes | run card rows 3, 12 |
| L27 | Which tool the owner uses to crop screenshots (v6 names the Windows Snipping Tool, path not checked) | confirm | step I.1 |
| L28 | The memory files named in FACTS-ALREADY-DONE were not readable here; confirm the v3-only steps (C.1, C.2, D, G, I.2-I.7) against memory | check result | CHANGES file, memory-check table |
