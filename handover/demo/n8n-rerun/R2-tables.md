# Tables generated from the raw files (harness/summarise.py). Do not edit by hand.

## Summary (counted from the raw files)

* Variant a, ten at once (attempts 20, invalid 0): 12 of 20 (95% interval 38.7 to 78.1 percent) ended with exactly 1 CRM row and 1 email; runs where the replay added posts: 0 of 20.
* Variant b, ten at once (attempts 21, invalid 1): 20 of 20 (95% interval 83.9 to 100.0 percent) ended with exactly 1 CRM row and 1 email; runs where the replay added posts: 0 of 20.
* Variant c, ten at once (attempts 20, invalid 0): 20 of 20 (95% interval 83.9 to 100.0 percent) ended with exactly 1 CRM row and 1 email; runs where the replay added posts: 0 of 20.
* Variant d, ten at once (attempts 20, invalid 0): 20 of 20 (95% interval 83.9 to 100.0 percent) ended with exactly 1 CRM row and 1 email; runs where the replay added posts: 0 of 20.
* Variant a kill runs: Kill rows where no client lost its connection: 0 of 15 valid kill rows (the result file holds 15 rows). A kill where no client lost its connection may not have taken effect; 0 means every valid kill row did show a lost connection. Rows with killed_pid not true in the raw row: 0 (such a row is never valid; in the 2026-11-09 Windows run this field only recorded that an n8n process was found).
* Variant a kill runs (attempts 15, invalid 0): CRM request in flight (first step): 1 of 5 ended with 1 CRM row and 0 emails after one retry press; the two email points: 3 of 10 ended with 1 CRM row and 1 email.
* Variant b kill runs: Kill rows where no client lost its connection: 0 of 13 valid kill rows (the result file holds 15 rows). A kill where no client lost its connection may not have taken effect; 0 means every valid kill row did show a lost connection. Rows with killed_pid not true in the raw row: 0 (such a row is never valid; in the 2026-11-09 Windows run this field only recorded that an n8n process was found).
* Variant b kill runs (attempts 15, invalid 2): CRM request in flight (first step): 4 of 4 ended with 1 CRM row and 0 emails after one retry press; the two email points: 9 of 9 ended with 1 CRM row and 1 email.
* Variant c kill runs: Kill rows where no client lost its connection: 0 of 15 valid kill rows (the result file holds 15 rows). A kill where no client lost its connection may not have taken effect; 0 means every valid kill row did show a lost connection. Rows with killed_pid not true in the raw row: 0 (such a row is never valid; in the 2026-11-09 Windows run this field only recorded that an n8n process was found).
* Variant c kill runs (attempts 15, invalid 0): CRM request in flight (first step): 5 of 5 ended with 1 CRM row and 0 emails after one retry press; the two email points: 10 of 10 ended with 1 CRM row and 1 email.
* Variant d kill runs: Kill rows where no client lost its connection: 0 of 15 valid kill rows (the result file holds 15 rows). A kill where no client lost its connection may not have taken effect; 0 means every valid kill row did show a lost connection. Rows with killed_pid not true in the raw row: 0 (such a row is never valid; in the 2026-11-09 Windows run this field only recorded that an n8n process was found).
* Variant d kill runs (attempts 15, invalid 0): CRM request in flight (first step): 5 of 5 ended with 1 CRM row and 0 emails after one retry press; the two email points: 10 of 10 ended with 1 CRM row and 1 email.

## Attempts, valid runs and invalid reasons (nothing is dropped without being counted)

An invalid attempt is not a failure of n8n and is not hidden: it is a run that did not meet the rule for a valid run, so it is not counted in any result above. It is listed here with its reason. For the 2026-11-09 run, "kept in invalid/" means that the original run moved those attempts to the folder `published_run/invalid/` and the text in brackets is the label of the file they were moved to; a new run keeps every attempt in its normal result file and names the reason.

An attempt is invalid when: no ten executions listed or no overlap between them (variant d: ten not sent within 100 ms), a wait for quiet ran into its time limit (timeout) or the stand-in could not be reached, or for a kill run the trigger was never seen, no process was killed (taskkill failed or the port was still busy), n8n did not restart, or an execution still showed running after the kill and the retry although nothing else moved (stale_running_after_kill: counted and listed, never part of the valid headline).

Test configuration a default (ten at once): attempts 20, valid 20, invalid 0 (none).
Test configuration b default (ten at once): attempts 21, valid 20, invalid 1 (no overlap x1).
Test configuration c default (ten at once): attempts 20, valid 20, invalid 0 (none).
Test configuration d limit1 (ten at once): attempts 20, valid 20, invalid 0 (none).
Test configuration a (kill runs): attempts 15, valid 15, invalid 0 (none).
Test configuration b (kill runs): attempts 15, valid 13, invalid 2 (stale_running_after_kill x2).
Test configuration c (kill runs): attempts 15, valid 15, invalid 0 (none).
Test configuration d (kill runs): attempts 15, valid 15, invalid 0 (none).
Test configuration e K3 (kill runs): attempts 5, valid 5, invalid 0 (none).
Test configuration e K2 (kill runs): attempts 5, valid 5, invalid 0 (none).
Test configuration e K1 (kill runs): attempts 5, valid 5, invalid 0 (none).
Test configuration e (ten at once): attempts 5, valid 5, invalid 0 (none).

The runs of one test configuration are not independent: one n8n process, one database and one laptop serve all of them, one after another. The 95% intervals (Wilson) treat them as independent trials, so they are optimistic (too narrow); read them as a floor on the uncertainty, not as a promise. 20 of 20 clean runs does NOT mean that duplicates cannot happen: it means that none was seen in 20 tries on one machine.

## Machine load before and after each test configuration

| time (UTC) | test configuration | when | CPU idle percent | free RAM MB |
|---|---|---|---|---|
| 2026-11-14T03:47:47.059Z | a default | before | 99.50 | 14296 |
| 2026-11-14T03:48:18.061Z | a default | during | 97.30 | 14198 |
| 2026-11-14T03:48:49.062Z | a default | during | 98.00 | 14203 |
| 2026-11-14T03:49:20.063Z | a default | during | 95.30 | 14172 |
| 2026-11-14T03:49:51.064Z | a default | during | 96.30 | 14199 |
| 2026-11-14T03:50:11.250Z | a default | after | 99.00 | 14200 |
| 2026-11-14T03:50:13.252Z | b default | before | 99.50 | 14208 |
| 2026-11-14T03:50:44.253Z | b default | during | 96.80 | 14197 |
| 2026-11-14T03:51:15.254Z | b default | during | 97.30 | 14241 |
| 2026-11-14T03:51:46.255Z | b default | during | 97.80 | 14500 |
| 2026-11-14T03:52:17.256Z | b default | during | 81.40 | 14426 |
| 2026-11-14T03:52:42.590Z | b default | after | 100.00 | 14477 |
| 2026-11-14T03:52:44.591Z | c default | before | 99.70 | 14477 |
| 2026-11-14T03:53:15.592Z | c default | during | 96.80 | 14449 |
| 2026-11-14T03:53:46.593Z | c default | during | 97.00 | 14397 |
| 2026-11-14T03:54:17.594Z | c default | during | 95.00 | 14511 |
| 2026-11-14T03:54:48.595Z | c default | during | 98.00 | 14503 |
| 2026-11-14T03:55:11.752Z | c default | after | 95.50 | 14428 |
| 2026-11-14T03:55:19.960Z | d limit1 | before | 98.00 | 14360 |
| 2026-11-14T03:55:50.961Z | d limit1 | during | 86.20 | 14071 |
| 2026-11-14T03:56:21.962Z | d limit1 | during | 97.50 | 13994 |
| 2026-11-14T03:56:52.963Z | d limit1 | during | 85.00 | 14012 |
| 2026-11-14T03:57:23.964Z | d limit1 | during | 97.80 | 14031 |
| 2026-11-14T03:57:47.920Z | d limit1 | after | 99.80 | 14070 |
| 2026-11-14T03:57:49.921Z | d kill runs K1 | before | 99.80 | 14070 |
| 2026-11-14T03:58:20.922Z | d kill runs K1 | during | 87.60 | 15034 |
| 2026-11-14T03:58:51.923Z | d kill runs K1 | during | 84.90 | 15023 |
| 2026-11-14T03:59:08.608Z | d kill runs K1 | after | 100.00 | 14275 |
| 2026-11-14T03:59:10.609Z | d kill runs K2 | before | 100.00 | 14302 |
| 2026-11-14T03:59:41.611Z | d kill runs K2 | during | 85.90 | 15040 |
| 2026-11-14T04:00:12.612Z | d kill runs K2 | during | 89.10 | 15025 |
| 2026-11-14T04:00:27.179Z | d kill runs K2 | after | 99.80 | 14247 |
| 2026-11-14T04:00:29.180Z | d kill runs K3 | before | 97.00 | 14246 |
| 2026-11-14T04:01:00.182Z | d kill runs K3 | during | 87.10 | 14968 |
| 2026-11-14T04:01:31.183Z | d kill runs K3 | during | 99.30 | 14989 |
| 2026-11-14T04:01:45.878Z | d kill runs K3 | after | 100.00 | 14280 |
| 2026-11-14T04:01:54.369Z | a kill runs K1 | before | 99.80 | 14297 |
| 2026-11-14T04:02:25.370Z | a kill runs K1 | during | 97.30 | 14220 |
| 2026-11-14T04:02:56.371Z | a kill runs K1 | during | 96.80 | 14227 |
| 2026-11-14T04:03:13.393Z | a kill runs K1 | after | 100.00 | 14244 |
| 2026-11-14T04:03:15.395Z | a kill runs K2 | before | 97.50 | 14293 |
| 2026-11-14T04:03:46.396Z | a kill runs K2 | during | 95.70 | 14220 |
| 2026-11-14T04:04:17.397Z | a kill runs K2 | during | 70.70 | 14073 |
| 2026-11-14T04:04:33.137Z | a kill runs K2 | after | 99.00 | 14203 |
| 2026-11-14T04:04:35.138Z | a kill runs K3 | before | 100.00 | 14204 |
| 2026-11-14T04:05:06.139Z | a kill runs K3 | during | 97.00 | 14285 |
| 2026-11-14T04:05:37.141Z | a kill runs K3 | during | 97.30 | 14249 |
| 2026-11-14T04:05:54.838Z | a kill runs K3 | after | 99.70 | 14249 |
| 2026-11-14T04:05:56.840Z | c kill runs K1 | before | 97.50 | 14257 |
| 2026-11-14T04:06:27.841Z | c kill runs K1 | during | 96.80 | 14257 |
| 2026-11-14T04:06:58.842Z | c kill runs K1 | during | 96.50 | 14285 |
| 2026-11-14T04:07:17.071Z | c kill runs K1 | after | 99.80 | 14282 |
| 2026-11-14T04:07:19.072Z | c kill runs K2 | before | 97.50 | 14281 |
| 2026-11-14T04:07:50.074Z | c kill runs K2 | during | 96.50 | 14242 |
| 2026-11-14T04:08:21.075Z | c kill runs K2 | during | 96.50 | 14249 |
| 2026-11-14T04:08:39.491Z | c kill runs K2 | after | 99.20 | 14247 |
| 2026-11-14T04:08:41.492Z | c kill runs K3 | before | 99.50 | 14253 |
| 2026-11-14T04:09:12.494Z | c kill runs K3 | during | 96.50 | 14283 |
| 2026-11-14T04:09:43.495Z | c kill runs K3 | during | 95.80 | 14259 |
| 2026-11-14T04:10:01.185Z | c kill runs K3 | after | 99.50 | 14288 |
| 2026-11-14T04:10:03.186Z | b kill runs K1 | before | 97.70 | 14335 |
| 2026-11-14T04:10:34.188Z | b kill runs K1 | during | 96.20 | 14223 |
| 2026-11-14T04:11:05.189Z | b kill runs K1 | during | 87.40 | 14213 |
| 2026-11-14T04:11:25.000Z | b kill runs K1 | after | 99.80 | 14207 |
| 2026-11-14T04:11:27.001Z | b kill runs K2 | before | 97.50 | 14237 |
| 2026-11-14T04:11:58.003Z | b kill runs K2 | during | 96.80 | 14194 |
| 2026-11-14T04:12:29.004Z | b kill runs K2 | during | 96.30 | 14198 |
| 2026-11-14T04:13:00.005Z | b kill runs K2 | during | 96.50 | 14181 |
| 2026-11-14T04:13:31.006Z | b kill runs K2 | during | 98.80 | 15185 |
| 2026-11-14T04:13:44.015Z | b kill runs K2 | after | 99.80 | 14270 |
| 2026-11-14T04:13:46.017Z | b kill runs K3 | before | 97.30 | 14274 |
| 2026-11-14T04:14:17.018Z | b kill runs K3 | during | 95.00 | 14246 |
| 2026-11-14T04:14:48.019Z | b kill runs K3 | during | 74.60 | 14288 |
| 2026-11-14T04:15:19.020Z | b kill runs K3 | during | 82.50 | 14236 |
| 2026-11-14T04:15:50.021Z | b kill runs K3 | during | 97.00 | 14288 |
| 2026-11-14T04:16:04.878Z | b kill runs K3 | after | 100.00 | 14289 |
| 2026-11-14T04:16:07.463Z | e kill runs K3 | before | 98.80 | 14285 |
| 2026-11-14T04:16:38.464Z | e kill runs K3 | during | 100.00 | 14668 |
| 2026-11-14T04:17:09.465Z | e kill runs K3 | during | 100.00 | 14706 |
| 2026-11-14T04:17:40.467Z | e kill runs K3 | during | 99.80 | 14336 |
| 2026-11-14T04:18:11.468Z | e kill runs K3 | during | 100.00 | 14696 |
| 2026-11-14T04:18:42.469Z | e kill runs K3 | during | 67.60 | 14753 |
| 2026-11-14T04:19:13.470Z | e kill runs K3 | during | 99.80 | 14689 |
| 2026-11-14T04:19:44.471Z | e kill runs K3 | during | 99.70 | 14699 |
| 2026-11-14T04:20:15.473Z | e kill runs K3 | during | 99.00 | 14684 |
| 2026-11-14T04:20:46.474Z | e kill runs K3 | during | 99.80 | 14709 |
| 2026-11-14T04:21:17.475Z | e kill runs K3 | during | 97.30 | 14349 |
| 2026-11-14T04:21:48.476Z | e kill runs K3 | during | 100.00 | 14702 |
| 2026-11-14T04:22:11.147Z | e kill runs K3 | after | 100.00 | 14717 |
| 2026-11-14T04:22:13.149Z | e kill runs K2 | before | 99.30 | 14717 |
| 2026-11-14T04:22:44.150Z | e kill runs K2 | during | 100.00 | 14668 |
| 2026-11-14T04:23:15.151Z | e kill runs K2 | during | 100.00 | 14720 |
| 2026-11-14T04:23:46.153Z | e kill runs K2 | during | 99.80 | 14321 |
| 2026-11-14T04:24:17.154Z | e kill runs K2 | during | 99.50 | 14691 |
| 2026-11-14T04:24:48.155Z | e kill runs K2 | during | 69.40 | 14414 |
| 2026-11-14T04:25:19.156Z | e kill runs K2 | during | 99.30 | 14693 |
| 2026-11-14T04:25:50.157Z | e kill runs K2 | during | 66.30 | 15157 |
| 2026-11-14T04:26:21.158Z | e kill runs K2 | during | 97.20 | 14691 |
| 2026-11-14T04:26:52.159Z | e kill runs K2 | during | 99.50 | 14676 |
| 2026-11-14T04:27:23.161Z | e kill runs K2 | during | 99.80 | 14391 |
| 2026-11-14T04:27:54.162Z | e kill runs K2 | during | 95.80 | 14689 |
| 2026-11-14T04:28:14.528Z | e kill runs K2 | after | 100.00 | 14714 |
| 2026-11-14T04:28:16.529Z | e kill runs K1 | before | 99.80 | 14716 |
| 2026-11-14T04:28:47.531Z | e kill runs K1 | during | 99.80 | 14688 |
| 2026-11-14T04:29:18.532Z | e kill runs K1 | during | 99.70 | 14702 |
| 2026-11-14T04:29:49.533Z | e kill runs K1 | during | 99.80 | 14386 |
| 2026-11-14T04:30:20.534Z | e kill runs K1 | during | 99.30 | 14710 |
| 2026-11-14T04:30:51.536Z | e kill runs K1 | during | 47.90 | 14443 |
| 2026-11-14T04:31:22.537Z | e kill runs K1 | during | 100.00 | 14713 |
| 2026-11-14T04:31:53.539Z | e kill runs K1 | during | 93.20 | 14712 |
| 2026-11-14T04:32:24.540Z | e kill runs K1 | during | 100.00 | 14693 |
| 2026-11-14T04:32:55.541Z | e kill runs K1 | during | 99.00 | 14714 |
| 2026-11-14T04:33:26.542Z | e kill runs K1 | during | 99.80 | 14348 |
| 2026-11-14T04:33:57.543Z | e kill runs K1 | during | 97.00 | 14701 |
| 2026-11-14T04:34:18.193Z | e kill runs K1 | after | 100.00 | 14710 |
| 2026-11-14T04:34:20.194Z | e ten at once | before | 100.00 | 14718 |
| 2026-11-14T04:34:51.196Z | e ten at once | during | 97.50 | 14675 |
| 2026-11-14T04:35:22.197Z | e ten at once | during | 99.30 | 14662 |
| 2026-11-14T04:35:53.198Z | e ten at once | during | 100.00 | 14667 |
| 2026-11-14T04:36:24.199Z | e ten at once | during | 99.80 | 14656 |
| 2026-11-14T04:36:55.200Z | e ten at once | during | 99.30 | 14648 |
| 2026-11-14T04:37:19.816Z | e ten at once | after | 99.30 | 14674 |

## Ten at once, then the same ten again as a replay (variants a to d)

The replay is sent as soon as the first ten have been quiet for at least 3 seconds (the published run waited about 5 seconds), so the replay timing differs a little and replay numbers are not strictly comparable to the published run.

### Variant a (n8n default concurrency)

Valid runs 20. Runs ending with exactly 1 CRM row and 1 email: 12 of 20 (95% interval 38.7 to 78.1 percent). Runs with more: 8 of 20 (95% interval 21.9 to 61.3 percent).
Final (CRM rows, emails) after the ten: (1, 1) x12, (2, 2) x1, (3, 3) x2, (5, 5) x3, (6, 6) x1, (7, 7) x1.
Posts added by the replay (CRM, emails): (0, 0) x20.

| run | replies (10 hits) | CRM / email after hits | replay added CRM / email |
|---|---|---|---|
| 1 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 2 | 200x5, 500x5 | 5 / 5 | +0 / +0 |
| 3 | 200x7, 500x3 | 7 / 7 | +0 / +0 |
| 4 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 5 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 6 | 200x5, 500x5 | 5 / 5 | +0 / +0 |
| 7 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 8 | 200x5, 500x5 | 5 / 5 | +0 / +0 |
| 9 | 200x2, 500x8 | 2 / 2 | +0 / +0 |
| 10 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 11 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 12 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 13 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 14 | 200x3, 500x7 | 3 / 3 | +0 / +0 |
| 15 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 16 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 17 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 18 | 200x6, 500x4 | 6 / 6 | +0 / +0 |
| 19 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 20 | 200x3, 500x7 | 3 / 3 | +0 / +0 |

### Variant b (n8n default concurrency)

Valid runs 20. Runs ending with exactly 1 CRM row and 1 email: 20 of 20 (95% interval 83.9 to 100.0 percent). Runs with more: 0 of 20 (95% interval 0.0 to 16.1 percent).
Final (CRM rows, emails) after the ten: (1, 1) x20.
Posts added by the replay (CRM, emails): (0, 0) x20.

| run | replies (10 hits) | CRM / email after hits | replay added CRM / email |
|---|---|---|---|
| 1 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 2 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 3 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 4 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 5 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 6 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 7 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 8 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 9 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 10 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 11 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 12 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 13 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 14 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 15 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 16 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 17 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 18 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 19 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 20 | 200x1, 500x9 | 1 / 1 | +0 / +0 |

### Variant c (n8n default concurrency)

Valid runs 20. Runs ending with exactly 1 CRM row and 1 email: 20 of 20 (95% interval 83.9 to 100.0 percent). Runs with more: 0 of 20 (95% interval 0.0 to 16.1 percent).
Final (CRM rows, emails) after the ten: (1, 1) x20.
Posts added by the replay (CRM, emails): (0, 0) x20.

| run | replies (10 hits) | CRM / email after hits | replay added CRM / email |
|---|---|---|---|
| 1 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 2 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 3 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 4 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 5 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 6 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 7 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 8 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 9 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 10 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 11 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 12 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 13 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 14 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 15 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 16 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 17 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 18 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 19 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 20 | 200x1, 500x9 | 1 / 1 | +0 / +0 |

### Variant d (concurrency limit 1)

Valid runs 20. Runs ending with exactly 1 CRM row and 1 email: 20 of 20 (95% interval 83.9 to 100.0 percent). Runs with more: 0 of 20 (95% interval 0.0 to 16.1 percent).
Final (CRM rows, emails) after the ten: (1, 1) x20.
Posts added by the replay (CRM, emails): (0, 0) x20.

| run | replies (10 hits) | CRM / email after hits | replay added CRM / email |
|---|---|---|---|
| 1 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 2 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 3 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 4 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 5 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 6 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 7 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 8 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 9 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 10 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 11 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 12 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 13 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 14 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 15 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 16 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 17 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 18 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 19 | 200x1, 500x9 | 1 / 1 | +0 / +0 |
| 20 | 200x1, 500x9 | 1 / 1 | +0 / +0 |

## Kill runs (variants a to d): n8n killed, restarted, retry pressed once per crashed entry

The letters K1, K2 and K3 in the raw files name different moments for variants a to d (CRM first, then email) and for variant e (email first, then CRM). This file names the moment in words and gives the letter only so that the raw file can be found. For variants a to d: K1 = email request in flight (CRM already stored), K2 = email stored with its reply held for 3 seconds, K3 = CRM request in flight (first step, the email is never sent).

### Variant a

Kill points here: K1 = email request in flight (CRM already stored); K2 = email stored, its reply held; K3 = CRM request in flight (first step, email never sent).

| point | run | CRM / email at kill | after in-flight requests ended | list after restart | retry presses | final CRM / email | crashed entry visible | valid |
|---|---|---|---|---|---|---|---|---|
| K1 | 1 | 2 / 0 | 2 / 1 | crashed x10 | 10 | 2 / 1 | yes | yes |
| K1 | 2 | 4 / 0 | 4 / 3 | crashed x10 | 10 | 4 / 3 | yes | yes |
| K1 | 3 | 1 / 0 | 1 / 1 | crashed x3, success x7 | 3 | 1 / 1 | yes | yes |
| K1 | 4 | 1 / 0 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K1 | 5 | 5 / 0 | 5 / 5 | crashed x5, success x5 | 5 | 5 / 5 | yes | yes |
| K2 | 1 | 4 / 3 | 4 / 3 | crashed x10 | 10 | 4 / 3 | yes | yes |
| K2 | 2 | 1 / 1 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K2 | 3 | 7 / 7 | 7 / 7 | crashed x8, success x2 | 8 | 7 / 7 | yes | yes |
| K2 | 4 | 4 / 3 | 4 / 3 | crashed x10 | 10 | 4 / 3 | yes | yes |
| K2 | 5 | 7 / 7 | 7 / 7 | crashed x8, success x2 | 8 | 7 / 7 | yes | yes |
| K3 | 1 | 0 / 0 | 2 / 0 | crashed x5, success x5 | 5 | 2 / 0 | yes | yes |
| K3 | 2 | 0 / 0 | 7 / 0 | crashed x9, success x1 | 9 | 7 / 0 | yes | yes |
| K3 | 3 | 0 / 0 | 1 / 0 | crashed x10 | 10 | 1 / 0 | yes | yes |
| K3 | 4 | 0 / 0 | 3 / 0 | crashed x10 | 10 | 3 / 0 | yes | yes |
| K3 | 5 | 0 / 0 | 2 / 0 | crashed x10 | 10 | 2 / 0 | yes | yes |

Kill rows where no client lost its connection: 0 of 15 valid kill rows (the result file holds 15 rows). A kill where no client lost its connection may not have taken effect; 0 means every valid kill row did show a lost connection. Rows with killed_pid not true in the raw row: 0 (such a row is never valid; in the 2026-11-09 Windows run this field only recorded that an n8n process was found).

Email request in flight (CRM already stored) (raw file point K1): 5 valid runs, final (CRM, email) (1, 1) x2, (2, 1) x1, (4, 3) x1, (5, 5) x1; crashed entry visible 5 of 5.

Email stored, its reply held (raw file point K2): 5 valid runs, final (CRM, email) (1, 1) x1, (4, 3) x2, (7, 7) x2; crashed entry visible 5 of 5.

CRM request in flight (first step, email never sent) (raw file point K3): 5 valid runs, final (CRM, email) (1, 0) x1, (2, 0) x2, (3, 0) x1, (7, 0) x1; crashed entry visible 5 of 5.

### Variant b

Kill points here: K1 = email request in flight (CRM already stored); K2 = email stored, its reply held; K3 = CRM request in flight (first step, email never sent).

| point | run | CRM / email at kill | after in-flight requests ended | list after restart | retry presses | final CRM / email | crashed entry visible | valid |
|---|---|---|---|---|---|---|---|---|
| K1 | 1 | 1 / 0 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K1 | 2 | 1 / 0 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K1 | 3 | 1 / 0 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K1 | 4 | 1 / 0 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K1 | 5 | 1 / 0 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K2 | 1 | 1 / 1 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K2 | 2 | 1 / 1 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K2 | 3 | 1 / 1 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K2 | 4 | 1 / 1 | 1 / 1 | crashed x9, running x1 | 9 | 1 / 1 | yes | NO: stale_running_after_kill |
| K2 | 5 | 1 / 1 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K3 | 1 | 0 / 0 | 1 / 0 | crashed x10 | 10 | 1 / 0 | yes | yes |
| K3 | 2 | 0 / 0 | 1 / 0 | crashed x10 | 10 | 1 / 0 | yes | yes |
| K3 | 3 | 0 / 0 | 1 / 0 | crashed x10 | 10 | 1 / 0 | yes | yes |
| K3 | 4 | 0 / 0 | 1 / 0 | crashed x10 | 10 | 1 / 0 | yes | yes |
| K3 | 5 | 0 / 0 | 1 / 0 | crashed x9, running x1 | 9 | 1 / 0 | yes | NO: stale_running_after_kill |

Kill rows where no client lost its connection: 0 of 13 valid kill rows (the result file holds 15 rows). A kill where no client lost its connection may not have taken effect; 0 means every valid kill row did show a lost connection. Rows with killed_pid not true in the raw row: 0 (such a row is never valid; in the 2026-11-09 Windows run this field only recorded that an n8n process was found).

Email request in flight (CRM already stored) (raw file point K1): 5 valid runs, final (CRM, email) (1, 1) x5; crashed entry visible 5 of 5.

Email stored, its reply held (raw file point K2): 4 valid runs, final (CRM, email) (1, 1) x4; crashed entry visible 4 of 4.

CRM request in flight (first step, email never sent) (raw file point K3): 4 valid runs, final (CRM, email) (1, 0) x4; crashed entry visible 4 of 4.

### Variant c

Kill points here: K1 = email request in flight (CRM already stored); K2 = email stored, its reply held; K3 = CRM request in flight (first step, email never sent).

| point | run | CRM / email at kill | after in-flight requests ended | list after restart | retry presses | final CRM / email | crashed entry visible | valid |
|---|---|---|---|---|---|---|---|---|
| K1 | 1 | 1 / 0 | 1 / 1 | crashed x4, success x6 | 4 | 1 / 1 | yes | yes |
| K1 | 2 | 1 / 0 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K1 | 3 | 1 / 0 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K1 | 4 | 1 / 0 | 1 / 1 | crashed x5, success x5 | 5 | 1 / 1 | yes | yes |
| K1 | 5 | 1 / 0 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K2 | 1 | 1 / 1 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K2 | 2 | 1 / 1 | 1 / 1 | crashed x9, success x1 | 9 | 1 / 1 | yes | yes |
| K2 | 3 | 1 / 1 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K2 | 4 | 1 / 1 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K2 | 5 | 1 / 1 | 1 / 1 | crashed x10 | 10 | 1 / 1 | yes | yes |
| K3 | 1 | 0 / 0 | 1 / 0 | crashed x7, success x3 | 7 | 1 / 0 | yes | yes |
| K3 | 2 | 0 / 0 | 1 / 0 | crashed x9, success x1 | 9 | 1 / 0 | yes | yes |
| K3 | 3 | 0 / 0 | 1 / 0 | crashed x3, success x7 | 3 | 1 / 0 | yes | yes |
| K3 | 4 | 0 / 0 | 1 / 0 | crashed x9, success x1 | 9 | 1 / 0 | yes | yes |
| K3 | 5 | 0 / 0 | 1 / 0 | crashed x3, success x7 | 3 | 1 / 0 | yes | yes |

Kill rows where no client lost its connection: 0 of 15 valid kill rows (the result file holds 15 rows). A kill where no client lost its connection may not have taken effect; 0 means every valid kill row did show a lost connection. Rows with killed_pid not true in the raw row: 0 (such a row is never valid; in the 2026-11-09 Windows run this field only recorded that an n8n process was found).

Email request in flight (CRM already stored) (raw file point K1): 5 valid runs, final (CRM, email) (1, 1) x5; crashed entry visible 5 of 5.

Email stored, its reply held (raw file point K2): 5 valid runs, final (CRM, email) (1, 1) x5; crashed entry visible 5 of 5.

CRM request in flight (first step, email never sent) (raw file point K3): 5 valid runs, final (CRM, email) (1, 0) x5; crashed entry visible 5 of 5.

### Variant d

Kill points here: K1 = email request in flight (CRM already stored); K2 = email stored, its reply held; K3 = CRM request in flight (first step, email never sent).
The "list after restart" of variant d holds fewer executions than for a to c (it lists 1 to 3, not ten). The author did not investigate why; with the concurrency limit of 1, n8n runs one execution at a time, which may be the reason (a guess, not verified).

| point | run | CRM / email at kill | after in-flight requests ended | list after restart | retry presses | final CRM / email | crashed entry visible | valid |
|---|---|---|---|---|---|---|---|---|
| K1 | 1 | 1 / 0 | 1 / 1 | crashed x1 | 1 | 1 / 1 | yes | yes |
| K1 | 2 | 1 / 0 | 1 / 1 | crashed x1 | 1 | 1 / 1 | yes | yes |
| K1 | 3 | 1 / 0 | 1 / 1 | crashed x1 | 1 | 1 / 1 | yes | yes |
| K1 | 4 | 1 / 0 | 1 / 1 | crashed x1 | 1 | 1 / 1 | yes | yes |
| K1 | 5 | 1 / 0 | 1 / 1 | crashed x1 | 1 | 1 / 1 | yes | yes |
| K2 | 1 | 1 / 1 | 1 / 1 | crashed x1 | 1 | 1 / 1 | yes | yes |
| K2 | 2 | 1 / 1 | 1 / 1 | crashed x1 | 1 | 1 / 1 | yes | yes |
| K2 | 3 | 1 / 1 | 1 / 1 | crashed x1 | 1 | 1 / 1 | yes | yes |
| K2 | 4 | 1 / 1 | 1 / 1 | crashed x1 | 1 | 1 / 1 | yes | yes |
| K2 | 5 | 1 / 1 | 1 / 1 | crashed x1 | 1 | 1 / 1 | yes | yes |
| K3 | 1 | 0 / 0 | 1 / 0 | crashed x1 | 1 | 1 / 0 | yes | yes |
| K3 | 2 | 0 / 0 | 1 / 0 | crashed x1 | 1 | 1 / 0 | yes | yes |
| K3 | 3 | 0 / 0 | 1 / 0 | crashed x1 | 1 | 1 / 0 | yes | yes |
| K3 | 4 | 0 / 0 | 1 / 0 | crashed x1 | 1 | 1 / 0 | yes | yes |
| K3 | 5 | 0 / 0 | 1 / 0 | crashed x1 | 1 | 1 / 0 | yes | yes |

Kill rows where no client lost its connection: 0 of 15 valid kill rows (the result file holds 15 rows). A kill where no client lost its connection may not have taken effect; 0 means every valid kill row did show a lost connection. Rows with killed_pid not true in the raw row: 0 (such a row is never valid; in the 2026-11-09 Windows run this field only recorded that an n8n process was found).

Email request in flight (CRM already stored) (raw file point K1): 5 valid runs, final (CRM, email) (1, 1) x5; crashed entry visible 5 of 5.

Email stored, its reply held (raw file point K2): 5 valid runs, final (CRM, email) (1, 1) x5; crashed entry visible 5 of 5.

CRM request in flight (first step, email never sent) (raw file point K3): 5 valid runs, final (CRM, email) (1, 0) x5; crashed entry visible 5 of 5.

## Variant e: status column and a re-send job every 15 seconds (blind mail stand-in)

The letters K1, K2 and K3 in the raw files name different moments for variants a to d (CRM first, then email) and for variant e (email first, then CRM). This file names the moment in words and gives the letter only so that the raw file can be found. For variant e: K3 = email request in flight (row still pending), K2 = email stored with its reply held (row pending), K1 = CRM request in flight (last step, email already sent). "Blind mail stand-in" means the fake mail server stores every email it is sent and cannot recognise a repeat.

### Email request in flight (row pending) (raw file point K3)

Kill points of variant e: K1 = CRM request in flight (last step, email already sent); K2 = email stored, its reply held (row pending); K3 = email request in flight (row pending).

Cells are CRM posts / email posts / database status.

| run | at kill | after in-flight settled | +5s | +15s | +25s | +40s | +60s | re-send job posts (email/CRM) | client replies | valid |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0/0/pending | 0/1/pending | 1/2/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/1 | RemoteDisconnectedx10 | yes |
| 2 | 0/0/pending | 0/1/pending | 1/2/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/1 | 200x1, RemoteDisconnectedx9 | yes |
| 3 | 0/0/pending | 0/1/pending | 0/1/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/1 | 200x2, RemoteDisconnectedx8 | yes |
| 4 | 0/0/pending | 0/1/pending | 2/3/sent | 2/3/sent | 2/3/sent | 2/3/sent | 2/3/sent | 2/2 | 200x3, RemoteDisconnectedx7 | yes |
| 5 | 0/0/pending | 0/1/pending | 1/2/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/1 | 200x7, RemoteDisconnectedx3 | yes |

### Email stored, its reply held (row pending) (raw file point K2)

Kill points of variant e: K1 = CRM request in flight (last step, email already sent); K2 = email stored, its reply held (row pending); K3 = email request in flight (row pending).

Cells are CRM posts / email posts / database status.

| run | at kill | after in-flight settled | +5s | +15s | +25s | +40s | +60s | re-send job posts (email/CRM) | client replies | valid |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0/1/pending | 0/1/pending | 1/2/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/1 | 200x1, RemoteDisconnectedx9 | yes |
| 2 | 0/1/pending | 0/1/pending | 1/2/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/1 | 200x4, RemoteDisconnectedx6 | yes |
| 3 | 0/1/pending | 0/1/pending | 1/2/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/1 | 200x2, RemoteDisconnectedx8 | yes |
| 4 | 0/1/pending | 0/1/pending | 1/2/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/1 | 200x1, RemoteDisconnectedx9 | yes |
| 5 | 0/1/pending | 0/1/pending | 0/1/pending | 1/2/sent | 1/2/sent | 1/2/sent | 1/2/sent | 1/1 | RemoteDisconnectedx10 | yes |

### CRM request in flight (last step, email already sent) (raw file point K1)

Kill points of variant e: K1 = CRM request in flight (last step, email already sent); K2 = email stored, its reply held (row pending); K3 = email request in flight (row pending).

Cells are CRM posts / email posts / database status.

| run | at kill | after in-flight settled | +5s | +15s | +25s | +40s | +60s | re-send job posts (email/CRM) | client replies | valid |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 0/0 | 200x2, RemoteDisconnectedx8 | yes |
| 2 | 0/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 0/0 | RemoteDisconnectedx10 | yes |
| 3 | 0/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 0/0 | RemoteDisconnectedx10 | yes |
| 4 | 0/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 0/0 | 200x9, RemoteDisconnectedx1 | yes |
| 5 | 0/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 1/1/sent | 0/0 | 200x9, RemoteDisconnectedx1 | yes |

At the two email points (K3 and K2 together): 10 of 10 (95% interval 72.2 to 100.0 percent) ended with 2 or more emails; 1 of 10 (95% interval 1.8 to 40.4 percent) ended with 2 CRM rows. Status not `sent` at 60 s in 0 of 15 kill runs.

Gaps (ms) between two re-send emails for the same address when less than 1 s apart: [32].

Ten at once for e: 5 runs; final (CRM, email) (1, 1) x5; 35 s later (1, 1) x5; replies 200x10 x5.

## Cross-check against the stand-in's own log

The final counts of each run (ten-at-once after the replay; kill runs after the retry) compared with the posts the fake server logged for that address: 138 runs equal, 0 differ (kill runs that do not count are left out: 2).

## SHORTFALL (fewer valid runs than expected)

* g3 b K2: expected 5 valid kill runs, found 4
* g3 b K3: expected 5 valid kill runs, found 4
