# lane3 kill and fault results (own harness; counts taken outside n8n per lead id)
Generated 2026-11-14 17:27Z. n = number of runs behind each row. Flow sets: 11:05Z (59202078), 61e3804b (fixed), 6ebb7f62-v3, 7709d058-v4, 873a908a-film-v4-lease45. Voided runs (my slips) are labelled VOID- in results.jsonl.

## Part 1: kill points, faults, ERROR, burst, GREP

| point | outcome (per lead, counted outside n8n) | n | runs |
|---|---|---|---|
| Fa [flows 11:05Z] | done, attempts=1, intake_mails=1, lead_alerts=0, crm_rows=1, model_calls=1 | 3 | jfa jfa2 jfa3 |
| Fa [flows 61e3804b] | done, attempts=1, intake_mails=1, lead_alerts=0, crm_rows=1, model_calls=1 | 3 | ffa1 ffa2 ffa3 |
| Fb [flows 11:05Z] | unknown, attempts=1, intake_mails=1, lead_alerts=1, crm_rows=1, model_calls=1 | 3 | jfb jfb2 jfb3 |
| Fb [flows 61e3804b] | unknown, attempts=1, intake_mails=1, lead_alerts=1, crm_rows=1, model_calls=1 | 3 | ffb1 ffb2 ffb3 |
| Fc [flows 11:05Z] | unknown, attempts=1, intake_mails=0, lead_alerts=0, crm_rows=1, model_calls=1 | 3 | jfc jfc2 jfc3 |
| Fc [flows 61e3804b] | unknown, attempts=1, intake_mails=0, lead_alerts=0, crm_rows=1, model_calls=1 | 3 | ffc1 ffc2 ffc3 |
| Fc1 [flows 11:05Z] | unknown, attempts=1, intake_mails=0, lead_alerts=1, crm_rows=1, model_calls=1 | 3 | jfc1a jfc1b jfc1c |
| Fc1 [flows 61e3804b] | unknown, attempts=1, intake_mails=0, lead_alerts=1, crm_rows=1, model_calls=1 | 3 | fc1a fc1b fc1c |
| K1 [flows 11:05Z] | done, attempts=2, intake_mails=1, lead_alerts=0, crm_rows=1, model_calls=1 | 3 | j1a j1b j1c |
| K1 [flows 873a908a-film-v4-lease45] | done, attempts=2, intake_mails=1, lead_alerts=0, crm_rows=1, model_calls=1 | 5 | fl45k1a fl45k1b fl45k1c fl45k1d fl45k1e |
| K2 [flows 11:05Z] | done, attempts=2, intake_mails=1, lead_alerts=0, crm_rows=1, model_calls=1 | 3 | j2a j2b j2c |
| K2 [flows 873a908a-film-v4-lease45] | done, attempts=2, intake_mails=1, lead_alerts=0, crm_rows=1, model_calls=1 | 5 | fl45k2a fl45k2b fl45k2c fl45k2d fl45k2e |
| K3 [flows 11:05Z] | unknown, attempts=2, intake_mails=0, lead_alerts=1, crm_rows=1, model_calls=1 | 3 | j3a j3b j3c |
| K3 [flows 61e3804b] | unknown, attempts=2, intake_mails=0, lead_alerts=1, crm_rows=1, model_calls=1 | 3 | fk3a fk3b fk3c |
| K3 [flows 873a908a-film-v4-lease45] | unknown, attempts=2, intake_mails=0, lead_alerts=1, crm_rows=1, model_calls=1 | 5 | fl45k3a fl45k3c fl45k3d fl45k3e fl45k3f |
| K6 [flows 11:05Z] | unknown, attempts=2, intake_mails=1, lead_alerts=1, crm_rows=1, model_calls=1 | 3 | j6a j6b j6c |
| K6 [flows 61e3804b] | unknown, attempts=2, intake_mails=1, lead_alerts=1, crm_rows=1, model_calls=1 | 3 | fk6a fk6b fk6c |
| K6 [flows 873a908a-film-v4-lease45] | unknown, attempts=2, intake_mails=1, lead_alerts=1, crm_rows=1, model_calls=1 | 3 | fl45k6a fl45k6b fl45k6d |
| burst [flows 11:05Z] | done, attempts=1, intake_mails=1, lead_alerts=0, crm_rows=1, model_calls=1 | 3 | jb1 jb2 jb3 |
| burst [flows 61e3804b] | done, attempts=1, intake_mails=1, lead_alerts=0, crm_rows=1, model_calls=1 | 1 | fb1 |
| control1 [flows 11:05Z] | done, attempts=1, intake_mails=1, lead_alerts=0, crm_rows=1, model_calls=1 | 1 | j0 |
| control2par [flows 11:05Z] | done, attempts=1, intake_mails=1, lead_alerts=0, crm_rows=1, model_calls=1 | 2 | jcp2 jcp2 |
| error [flows 11:05Z] | processing, attempts=3, intake_mails=0, lead_alerts=0, crm_rows=0, model_calls=1 | 2 | je1 je2 |
| error [flows 61e3804b] | failed, attempts=3, intake_mails=0, lead_alerts=1, crm_rows=0, model_calls=1 | 3 | ferr1 ferr2 ferr3 |
| error [flows 873a908a-film-v4-lease45] | failed, attempts=3, intake_mails=0, lead_alerts=1, crm_rows=0, model_calls=1 | 3 | fl45err1 fl45err2 fl45err3 |
| grep [flows 11:05Z] | done, attempts=1, intake_mails=1, lead_alerts=0, crm_rows=1, model_calls=1 | 3 | jg1 jg2 jg3 |
| grep [flows 61e3804b + 4 env settings + PRUNE=false] | done, attempts=1, intake_mails=1, lead_alerts=0, crm_rows=1, model_calls=1 | 3 | fjg5 fjg6 fjg7 |
| grep [flows 61e3804b + 4 n8n env settings] | done, attempts=1, intake_mails=1, lead_alerts=0, crm_rows=1, model_calls=1 | 3 | fjg2 fjg3 fjg4 |
| grep [flows 61e3804b] | done, attempts=1, intake_mails=1, lead_alerts=0, crm_rows=1, model_calls=1 | 1 | fjg1 |
| t14 [flows 61e3804b] | no lead, total_stage_requests=0, total_mails=0, alert_mails=0, crm_upserts=0 | 1 | ft14n |

GREP (hits per place; n8n_folder = files under the n8n user folder, postgres_row = counts in the lead row):
- fjg1 [flows 61e3804b]: export_json:email=0; export_json:key=0; export_json:name=0; n8n_folder:email=n8nhome/.n8n/database.sqlite-wal; n8n_folder:key=n8nhome/.n8n/database.sqlite-wal; n8n_folder:name=n8nhome/.n8n/database.sqlite-wal; n8n_log:email=0; n8n_log:key=0; n8n_log:name=0; postgres_row:email=1; postgres_row:key=0; postgres_row:name=1
- fjg2 [flows 61e3804b + 4 n8n env settings]: export_json:email=0; export_json:key=0; export_json:name=0; n8n_folder:email=n8nhome/.n8n/database.sqlite-wal; n8n_folder:key=n8nhome/.n8n/database.sqlite-wal; n8n_folder:name=n8nhome/.n8n/database.sqlite-wal; n8n_log:email=0; n8n_log:key=0; n8n_log:name=0; postgres_row:email=1; postgres_row:key=0; postgres_row:name=1
- fjg3 [flows 61e3804b + 4 n8n env settings]: export_json:email=0; export_json:key=0; export_json:name=0; n8n_folder:email=n8nhome/.n8n/database.sqlite-wal; n8n_folder:key=n8nhome/.n8n/database.sqlite-wal; n8n_folder:name=n8nhome/.n8n/database.sqlite-wal; n8n_log:email=0; n8n_log:key=0; n8n_log:name=0; postgres_row:email=1; postgres_row:key=0; postgres_row:name=1
- fjg4 [flows 61e3804b + 4 n8n env settings]: export_json:email=0; export_json:key=0; export_json:name=0; n8n_folder:email=n8nhome/.n8n/database.sqlite-wal; n8n_folder:key=n8nhome/.n8n/database.sqlite-wal; n8n_folder:name=n8nhome/.n8n/database.sqlite-wal; n8n_log:email=0; n8n_log:key=0; n8n_log:name=0; postgres_row:email=1; postgres_row:key=0; postgres_row:name=1
- fjg5 [flows 61e3804b + 4 env settings + PRUNE=false]: export_json:email=0; export_json:key=0; export_json:name=0; n8n_folder:email=n8nhome/.n8n/database.sqlite-wal; n8n_folder:key=n8nhome/.n8n/database.sqlite-wal; n8n_folder:name=n8nhome/.n8n/database.sqlite-wal; n8n_log:email=0; n8n_log:key=0; n8n_log:name=0; postgres_row:email=1; postgres_row:key=0; postgres_row:name=1
- fjg6 [flows 61e3804b + 4 env settings + PRUNE=false]: export_json:email=0; export_json:key=0; export_json:name=0; n8n_folder:email=n8nhome/.n8n/database.sqlite-wal; n8n_folder:key=n8nhome/.n8n/database.sqlite-wal; n8n_folder:name=n8nhome/.n8n/database.sqlite-wal; n8n_log:email=0; n8n_log:key=0; n8n_log:name=0; postgres_row:email=1; postgres_row:key=0; postgres_row:name=1
- fjg7 [flows 61e3804b + 4 env settings + PRUNE=false]: export_json:email=0; export_json:key=0; export_json:name=0; n8n_folder:email=n8nhome/.n8n/database.sqlite-wal; n8n_folder:key=n8nhome/.n8n/database.sqlite-wal; n8n_folder:name=n8nhome/.n8n/database.sqlite-wal; n8n_log:email=0; n8n_log:key=0; n8n_log:name=0; postgres_row:email=1; postgres_row:key=0; postgres_row:name=1
- jg1 [flows 11:05Z]: export_json:email=0; export_json:key=0; export_json:name=0; n8n_folder:email=n8nhome/.n8n/database.sqlite-wal; n8n_folder:key=n8nhome/.n8n/database.sqlite-wal; n8n_folder:name=n8nhome/.n8n/database.sqlite-wal; n8n_log:email=0; n8n_log:key=0; n8n_log:name=0; postgres_row:email=1; postgres_row:key=0; postgres_row:name=1
- jg2 [flows 11:05Z]: export_json:email=0; export_json:key=0; export_json:name=0; n8n_folder:email=n8nhome/.n8n/database.sqlite-wal; n8n_folder:key=n8nhome/.n8n/database.sqlite-wal; n8n_folder:name=n8nhome/.n8n/database.sqlite-wal; n8n_log:email=0; n8n_log:key=0; n8n_log:name=0; postgres_row:email=1; postgres_row:key=0; postgres_row:name=1
- jg3 [flows 11:05Z]: export_json:email=0; export_json:key=0; export_json:name=0; n8n_folder:email=n8nhome/.n8n/database.sqlite-wal; n8n_folder:key=n8nhome/.n8n/database.sqlite-wal; n8n_folder:name=n8nhome/.n8n/database.sqlite-wal; n8n_log:email=0; n8n_log:key=0; n8n_log:name=0; postgres_row:email=1; postgres_row:key=0; postgres_row:name=1

## Part 2: alert cases on the v3 and v4 flows (case column: v3A means case A, whichever flows column; )

| flows | case | run | reached | intake mails | alerts | CRM rows | alert times (s) | alert_attempts |
|---|---|---|---|---|---|---|---|---|
| 6ebb7f62-v3 | v3A | v3a1 | alert_sent true | 1 | 1 | 1 | [240] | 3 |
| 6ebb7f62-v3 | v3A | v3a2 | alert_sent true | 1 | 1 | 1 | [270] | 3 |
| 6ebb7f62-v3 | v3B20 | v3b20a | alert_sent true | 1 | 1 | 1 | [50] | 1 |
| 6ebb7f62-v3 | v3B90 | v3b90a | alert_sent true | 1 | 2 | 1 | [120, 120] | 2 |
| 6ebb7f62-v3 | v3B90 | v3b90b | alert_sent true | 1 | 2 | 1 | [120, 120] | 2 |
| 6ebb7f62-v3 | v3B90 | v3b90c | alert_sent true | 1 | 2 | 1 | [90, 120] | 2 |
| 6ebb7f62-v3 | v3C | v3c1 | alert_sent true | 1 | 1 | 1 | [690] | 5 |
| 6ebb7f62-v3 | v3C | v3c2 | alert_sent true | 1 | 1 | 1 | [690] | 5 |
| 7709d058-v4 | K1 | v4k1a | None | 1 | 0 | 1 | None | - |
| 7709d058-v4 | K1 | v4k1b | None | 1 | 0 | 1 | None | - |
| 7709d058-v4 | K2 | v4k2a | None | 1 | 0 | 1 | None | - |
| 7709d058-v4 | K3 | v4k3a | None | 0 | 1 | 1 | None | - |
| 7709d058-v4 | K3 | v4k3b | None | 0 | 1 | 1 | None | - |
| 7709d058-v4 | K6 | v4k6a | None | 1 | 1 | 1 | None | - |
| 7709d058-v4 | K6 | v4k6b | None | 1 | 1 | 1 | None | - |
| 7709d058-v4 | v3A | v4a1 | alert_sent true | 1 | 1 | 1 | [270] | 3 |
| 7709d058-v4 | v3A | v4a2 | alert_sent true | 1 | 1 | 1 | [270] | 3 |
| 7709d058-v4 | v3B780 | v4b780a | alert_sent true | 1 | 1 | 1 | [720] | 2 |
| 7709d058-v4 | v3B90 | v4b90a | alert_sent true | 1 | 1 | 1 | [120] | 1 |
| 7709d058-v4 | v3B90 | v4b90b | alert_sent true | 1 | 1 | 1 | [120] | 1 |
| 7709d058-v4 | v3B90 | v4b90c | alert_sent true | 1 | 1 | 1 | [120] | 1 |
| 7709d058-v4 | v3C | v4c1 | alert_sent true | 1 | 1 | 1 | [750] | 5 |
| 7709d058-v4 | v3C | v4c2 | alert_sent true | 1 | 1 | 1 | [750] | 5 |
| 7709d058-v4 | v3KS | v4ks1 | alert_sent true | 1 | 1 | 1 | [780] | 2 |
| 7709d058-v4 | v3KS | v4ks2 | alert_sent true | 1 | 1 | 1 | [780] | 2 |

## Part 3: recovery seconds on v4 (lease 120 s) and film-v4 (lease 45 s)

| flows | point | n | final state(s) | intake mails | alerts | CRM rows | recovery s median / max | kill to final s median / max |
|---|---|---|---|---|---|---|---|---|
| 7709d058-v4 | K1 | 2 | done | 1 | 0 | 1 | 144.3 / 144.3 | not recorded |
| 7709d058-v4 | K2 | 1 | done | 1 | 0 | 1 | 144.2 / 144.2 | not recorded |
| 7709d058-v4 | K3 | 1 | unknown | 0 | 1 | 1 | 144.3 / 144.3 | not recorded |
| 7709d058-v4 | K6 | 2 | unknown | 1 | 1 | 1 | 144.3 / 144.4 | not recorded |
| 873a908a-film-v4-lease45 | K1 | 5 | done | 1 | 0 | 1 | 52.9 / 54.9 | 60.8 / 61.9 |
| 873a908a-film-v4-lease45 | K2 | 5 | done | 1 | 0 | 1 | 52.9 / 52.9 | 60.9 / 61.2 |
| 873a908a-film-v4-lease45 | K3 | 5 | unknown | 0 | 1 | 1 | 52.9 / 54.9 | 60.4 / 61.6 |
| 873a908a-film-v4-lease45 | K6 | 3 | unknown | 1 | 1 | 1 | 52.8 / 54.8 | 60.1 / 61.5 |

## Part 4: comparison with the demo table

# Comparison with the demo session's numbers (written AFTER my numbers were saved; their files: K-SERIES-V4.md, V7-NUMBERS-lead-read.md)
Names differ: my K3 (killed when the mail connection opens, mail not delivered) = their K3B. My K6 (killed after the mail was stored) = their K3. Same results: K3B/my K3 1 CRM row, 0 intake mails, 1 alert, unknown; K3/my K6 1 / 1 / 1, unknown. My ERROR (CRM answers 500 to every call) = their T15: failed, 0 CRM rows, 0 mails, 1 alert. My A (alert refused twice) = their AF1: first alert 272 s there, 240 to 270 s here.
| Item | Demo (laptop, v3, lease 20 s) | Mine (cloud, my own harness) | Same? |
|---|---|---|---|
| K1, K2 end state | done, 0 lost, 0 doubled, n = 20 | done, 1 CRM row, 1 intake mail, n = 5 each at lease 45 s (and 1 to 2 at lease 120 s) | yes |
| K3 / K3B and my K6 | unknown, 1 alert, n = 20 each | unknown, 1 alert, n = 5 and 5 (lease 45 s) | yes |
| Kill to final seconds, K1 | 18.0 / 29.65 / 59.6 (min / median / max) | lease 45 s: 60.1 to 61.9, median 60.8; lease 120 s: not recorded (144 s from n8n up plus 7 s restart = about 151, computed) | different leases, so no direct match. Spread differs: mine has almost none (60.1 to 61.9). I did not find the reason; my guess: my restart always makes the recovery timer start at the same moment, theirs varies. NOT verified. |
| ERROR / T15 | failed, 1 alert, 3 of 3 | failed, 1 alert, 3 of 3 (lease 45 s) | yes |
| Duplicate alert | B90 never run before; README predicted it | v3: 2 alerts in 3 of 3; v4: 1 alert in 3 of 3 | new from me |
| Kill while the alert send waits (KS) | not in their list | v4: 1 alert, 13 min late, 2 of 2 | new from me |
| Hold 780 s / SMTP dead 600 s | not in their list | v4: 1 alert each (720 s / 750 s) | new from me |
Not compared: T8, T10, T11, T13, T14 on v4 (I did not run them on v4; T14 and burst ran on my fixed flows earlier, see RESULTS.md Part 1).
