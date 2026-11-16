# Evidence: recompute of lane3 kill-test numbers (EVIDENCE RUNNER, no judging)
Source: origin/demo/lane3 (sha in raw-lane3/source-sha.txt), files handover/demo3/kill/data/results.jsonl (128 rows) and RESULTS.md, read via `git show`; source untouched.
Files in raw-lane3/: results.jsonl, RESULTS.md (copies), recompute.py, recompute-output.txt, grep-claims.txt, source-sha.txt.
Commands: `python3 -I recompute.py results.jsonl > recompute-output.txt`; `git grep -n -F "<phrase>" origin/demo/lane3 -- handover/demo3/kill/`.

## Format notes
- First row keys: label, point, t_start, error, t_end (an early failed control run). Rows differ in keys; lease-45 rows carry `flows == "873a908a-film-v4-lease45"`.
- Case names in the file are K1, K2, K3, K6 (and "error"). There is NO "K3B" label in results.jsonl or RESULTS.md. RESULTS.md Part 4 says: file's K3 = the demo session's K3B; file's K6 = demo's K3.
- "Kept" defined by me as: flows==lease45, point in K1/K2/K3/K6, label not starting "VOID". Voided = label prefix "VOID-".

## Claimed vs recomputed
| # | Claim | Recomputed | Match |
|---|---|---|---|
| 1 | 18 kept lease-45 rows | 18 (23 lease-45 rows = 18 kept + 2 VOID + 3 error-case rows) | yes |
| 2 | kill_to_final_s min/max/median 60.1 / 61.9 / 60.85 | 60.1 / 61.9 / 60.85 | yes |
| 2b | kill_to_final_s = restart_s + recovery_s within 0.5 s | 0 violating rows; max diff 0.1 (fl45k3c) | yes |
| 3 | K1 5, K2 5, K3B 5, K3 3 | K1 5, K2 5, K3 5, K6 3 (file names; K3B=file K3, K3=file K6 per RESULTS.md Part 4) | yes, with name mapping |
| 4 | CRM called twice in 13 of 18 | Field `crm_upsert_events` (count of CRM upsert calls seen) == 2 in 13 of 18 (K2 5, K3 5, K6 3); == 1 in the 5 K1 rows. Final `crm_rows` == 1 in all 18; `counts.stage_calls` == 1 in all 18; `stage_requests` == 2 in all 18 | 13 yes, by that field only |
| 5 | voided runs | see below | |
| 6 | mail before kill | see below | |
| 7 | "80 kills" / "0 doubled" / "0 lost" in folder | "80 kills": 0 files. "0 doubled": 2 files (COMPARE-demo.md:5, RESULTS.md:100). "0 lost": 3 files (COMPARE-demo.md:5, RESULTS.md:100, PLAN-V3-ALERT.md:24). All hits in COMPARE-demo.md and RESULTS.md are the DEMO session's column ("done, 0 lost, 0 doubled, n = 20"), not lane3's own measurement; lane3's column reads "1 CRM row, 1 intake mail". PLAN-V3-ALERT.md:24 hit not read in full beyond the cut line. | see text |

## 5. Voided runs
- VOID-fl45k3b (K3): t_start 17:09:59Z, t_end 17:16:35Z, reached_terminal false, kill_to_final_s 338.7, recovery_s 331.2, no final state, no error text in the row. RESULTS.md only says "Voided runs (my slips) are labelled VOID-"; it gives no reason for this run. Reason not recorded.
- VOID-fl45k6c (K6): 17:10:42Z to 17:11:35Z, error "RuntimeError: fakes_not_up". Row-level reason only; RESULTS.md gives none beyond "my slips".
- Overlap in time: fl45k3b window 17:09:59-17:16:35 overlaps kept runs fl45k2d (17:08:02-17:10:00), fl45k2e, fl45k6a, fl45k3d, fl45k6b and VOID-fl45k6c. Overlap by itself is normal in this file (pairs such as fl45k2a/fl45k1a start in the same second, so runs were parallel); I cannot tell from the data whether the overlap caused the void. Also: the 17:09:59 start equals fl45k3a's t_end (17:09:59), and fl45k3c started 17:16:35 exactly at k3b's end.

## 6. Mail before kill vs not (kept rows)
Field `rows_at_kill` = [lead, state, attempts, crm-flag, crm-id] only; it has no mail field, and `lead_mail_stored` is absent in lease-45 rows. Evidence available is the final `counts.mail_to_intake`:
- K1 (5) and K2 (5): mail_to_intake 1, alert 0, CRM flag at kill "f".
- K3 (5): mail_to_intake 0, alert 1, CRM flag at kill "t" (crm-1). So the intake mail was not delivered in all 5; the file itself does not show whether it was sent before the kill, only that none was recorded afterwards.
- K6 (3): mail_to_intake 1, alert 1, total_mails 2, CRM flag "t".
Whether the harness deliberately withholds the mail in K3 is stated only in RESULTS.md Part 4 ("killed when the mail connection opens, mail not delivered"); not independently checked from harness code.

## Could not compute
- Reason for the two voids (not in the data).
- Whether any mail was sent before the kill (no such field).
- The claim wording "80 kills" does not exist in the folder; the number of lease-45 kill runs is 18 kept (+2 void); total rows with a kill point (K1/K2/K3/K6, all flows) were not summed by me for an 80 total.
- Did not run the harness; only the stored file was recomputed.
