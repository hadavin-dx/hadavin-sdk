# F1 review round 1: egm:egm-codebase-details (agent aa845b0544ceeec0d), condensed by flows-audit 2026-11-16
Spot-checked 38 rows; every checked quote exact, every cited line right, no wrong verdict among checked rows; lane A counts 12/12 add up; no safe wording uses approval, audit trail or one database. 2 Blockers, 10 Majors, 8 Nits. Not checked: most lane B rows (read by grep), mf-hook.json in full, FINDINGS beyond F-005/006/007/042, raw relayed files.
| id | sev | row | finding | fix |
|---|---|---|---|---|
| R1-01 | Blocker | A-076 | safe wording assigns the pooled 60.1 to 61.9 s range (all 18 runs, P:149) to K1 and K2 only | per-kill: K1 5 runs median 60.8 max 61.9; K2 5 runs median 60.9 max 61.2 (relayed); no low end |
| R1-02 | Blocker | A-033, A-030, A-035, A-021 | wordings state as fact that n8n could not tell whether the mail went; T12 not run; if SendMail does not error, lead ends done not unknown | add 'only if the rehearsal shows the mail step ended in error'; required pre-take check |
| R1-03 | Major | A-021, A-057, A-076 | 'one alert' but alert can repeat (A-023, A-075, B-077, B-150, F-014) | 'an alert (normally one)' |
| R1-04 | Major | A-019, A-050, A-036 | mixed-verdict rows missing from the 68-row list | add; filter on any cell containing the word |
| R1-05 | Major | A-040..042 | six columns true for table-screen v2 only; v1 selects seven | name the file in the evidence cell |
| R1-06 | Major | R:30 | 'No address on screen except example.test' not covered; real mail panes show throwaway addresses | add row OVERSTATED |
| R1-07 | Major | P:151, P:152 | per-kill numbers uncovered | add rows |
| R1-08 | Major | R:23 last sentence | '70 to 75 s estimate' contradicted by relayed 45 s data | add row; plan on about 60 to 62 s relayed |
| R1-09 | Major | B-032, B-056 | 'not measured at 45 s' conflicts with the relayed 45 s figure | mention relayed K1 median 60.8 max 61.9 |
| R1-10 | Major | P:156 | 'up to 13 minutes late' uncovered | add to A-023 |
| R1-11 | Major | R:39, R:40, R:41 l6, R:87(5), P:51, P:56, P:111 | uncovered flow claims | one row each |
| R1-12 | Major | R:31 | 'key L plus 16 hex' not verified | add row; verify Valid in mf-form |
| R1-13..20 | Nit | A-007/A-053 only after F-008; A-016 expected not observed; B-046 only callers during the in-flight call; B-054 evidence cell; X-1 'a failed alert send is retried'; A-075 statement 9 not 1; B-159 OS error only; A-004 stage env may build a live qualifier: no live call without owner numbers | as stated |
