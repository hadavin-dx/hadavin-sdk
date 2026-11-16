# F5 review round 1: egm:egm-comprehension (agent abaf92c58b1d1335f), naive reader, condensed by flows-audit 2026-11-16
Judged wording only; did not verify any claim; read CLAIMS-TABLE.md lines 1-146 only. Clean: no "one database"; "approval"/"audit" only in quoted originals; HubSpot not named in scenes 1-4; A-016 narrow claim kept; no bank/queue/gate.
| id | sev | where | finding | fix |
|---|---|---|---|---|
| W-01 | Major | whole file | no marker whether a sentence is SPOKEN, ON SCREEN or LEAD ONLY; paste cells end with instructions to the lead | add column Goes where; split 'sentence to paste' from 'note to lead' |
| W-02 | Blocker | A-021, A-057, A-076, A-077 | spoken 'one alert' while file says alert can repeat, no cap | spoken: 'an alert e-mail is sent to the person in charge'; 'one' only for the observed run |
| W-03 | Blocker | A-021, A-077 vs A-035 | 'nobody can say whether the mail went' while scene 9 shows the mail in the list | use A-035 wording: n8n got no confirmation, so it cannot know if the mail arrived |
| W-04..05 | Major | A-030, A-035 | 'took' and 'went' ambiguous | 'The test mailbox received the mail but cut the connection without confirming...' |
| W-06 | Major | A-017/019/051/081 | caption holds K1, lane3, film-v4, relayed, 'cloud session' | viewer line: 'In earlier tests on similar test flows, recovery took about a minute (5 runs, 60 to 62 seconds). This run was not timed.'; sources lead-only |
| W-07 | Major | A-017, A-073, B-032, B-156 | 'lease' unexplained | 'n8n waits 45 seconds before another run takes over a lead that stopped' |
| W-08 | Major | A-010, A-053, A-040 | 'address', 'e-mail', 'mail' ambiguous | 'e-mail address' vs 'e-mail message' |
| W-09 | Major | A-010, A-053 | 'the request', 'records', 'no expiry' unclear | plain sentence: n8n may keep a copy of the submitted form until saved runs are deleted; the lead table keeps them too |
| W-10 | Major | A-040, A-042 | 'safe columns' reads as privacy guarantee; 'take one picture' | 'six columns, none holds a name or e-mail address'; 'capture one screenshot' |
| W-11 | Major | N-1 | built alert text 'A person decides.' implies a decision step | add spoken line or change alert text (FIX-PLAN item 7) |
| W-12 | Major | N-3 | state 'review' reads as approval queue | 'only marked in the table; no alert is sent, so someone has to check the table' |
| W-13..15 | Major | scene 5 labels, A-008 | variant wording long/jargon; mail pane unresolved; meta sentence 'say on screen' | pane tag 'Test copy of the CRM (customer list)'; resolve mail pane before filming; drop meta sentence |
| W-16..21 | Major | A-005, A-016, A-073/076 vs A-081 pooled numbers, A-059/073/076/077 internal names (T8, harness, lane3, K3=K3B), A-023/075, A-021 | plain-word fixes; pooled range contradicts the file's own rule; page statements audience unknown | one rule on numbers; mark page statements lead-only or rewrite; 'not lost' leans on 2 runs |
| W-22..25 | Nit | take vs screenshot; column names; nested quotes; claim/window two meanings | one name per column; single quotes |
