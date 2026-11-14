# lane3 kill and fault results (own harness; counts taken outside n8n per lead id)
Generated 2026-11-14 17:22Z. n = number of runs behind each row. Flow sets: 11:05Z (59202078), 61e3804b (fixed), 6ebb7f62-v3, 7709d058-v4.

## Part 1: kill points, faults, ERROR, burst, GREP (flows 11:05Z and 61e3804b)

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

## Part 2: alert cases on the v3 and v4 flows (case column: v3A means case A, whichever flows column)

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

## Part 3: recovery seconds (K1, K2, K3, K6) on v4 (lease 120 s, folder n8n-flows-v4) and film-v4 (lease 45 s). Voided runs are labelled VOID- in results.jsonl and left out.

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
