# Campaign 3 (EVIDENCE RUNNER, no judgement). Tree /tmp/dpld-camp3b, 2026-11-09, UTC (IST = +5:30)

## What failed / what is uncertain (first)
- model-timeout did NOT drain even with a 1200 s drain wait: the runner gave up at about 20:50:16 UTC (start 20:29:53, i.e. about 1203 s). Final: pending 199, failed 1, sent 0, 0 emails, 0 CRM rows. Checks 2 and 7 FAIL. 646 model calls for 200 leads (max 5 per lead, bound 6); all 646 desk log lines are "follow-up steps 1-2 failed after the claim: QualifierTimeout". It was still retrying; I did not run it longer, so I do not know whether it ever drains.
- model-slow drained (673.6 s after the load) but check 7 still FAILS because the checker's ceiling is 120 s (a separate setting; the runner's wait is not the ceiling). I did not change it.
- catcher-slow drained (218.7 s) and fails only check 7 for the same reason (ceiling 120 s). All 200 follow-ups end `unknown` (SendAmbiguous), 200 messages kept, 1 per recipient: a person would have to confirm 200 sends (check 3 accepts this by design).
- model-slow check 4 now PASSES (300 CRM rows, allowed 300 to 300, 0 missing). The missing row L96160012c970 of run 2 did not recur, so no lead to dump. This run used 300 requests (run 2 had a different count); lead ids differ between runs, so I cannot say whether run 2's gap was a timing artefact (CRM dump taken before drain) or a fixed defect. The run 2 data is consistent with the former but I did not prove it.
- Not the same conditions as run 2: tree /tmp/dpld-camp3b (private copy); I did not diff it against /tmp/dpld-camp3.

## Numbers
| scenario | start UTC | end UTC | drain after load | checks 1..7 | sent/pending/failed/unknown | max model calls per lead (bound) | CRM rows vs done | loadavg start (1/5/15) | loadavg end |
|---|---|---|---|---|---|---|---|---|---|
| model-slow | 20:18:08 | 20:29:53 | 673.6 s | P P P P P P F | 300/0/0/0 | 1 (1) | 300 vs 300 | 1.87 0.81 0.60 | 4.60 3.23 2.01 |
| model-timeout | 20:29:53 | 20:50:16 | never (1200 s wait) | P F P P P P F | 0/199/1/0 | 5 (6), 646 calls | 0 vs 0 | 4.60 3.23 2.01 | 0.04 0.26 0.79 |
| catcher-slow | 20:50:16 | 20:54:16 | 218.7 s | P P P P P P F | 0/0/0/200 (200 msgs) | 1 (1) | 200 vs 200 (200 unknown allowed) | 0.04 0.26 0.79 | 0.00 0.11 0.60 |

Check 7 detail: model-slow 673.23 s, catcher-slow 218.41 s (ceiling 120 s). Desk log "all drive places are taken": 209 / 100 / 99 lines. Loadavg at the end of model-slow (4.60) is higher than elsewhere; the loadavg is read after the run, I did not identify the cause. Emails: model-slow 300 (1 per recipient), model-timeout 0, catcher-slow 200 (1 per recipient).

## Raw files
/home/user/build/campaign3/<scenario>/stdout.log, /home/user/build/campaign3/<scenario>/<scenario>/{checks.txt,checks.json,summary.json,desk.log,model.jsonl,catcher.jsonl,crm.json,book.sqlite3,requests.jsonl,drain.json}; progress.log; run3.sh. Checkpoints: /home/user/build/campaign3-checkpoint.md.

## Not checked
Whether model-timeout drains with a longer wait (arithmetic from run 2: up to 5 tries x 2 s x 200 leads, run one at a time); why loadavg was 4.6 at the end of model-slow; no tests (tools/outbox) re-run; recheck module not run; per-30 s arrival rates not recomputed; no audit of the desk code.
Processes: started 1 detached script (run3.sh) plus 3 campaign runs; all exited; `pgrep -f live_l2` = 0 at the end. Stopped by me: 0 needed (all ended on their own). Cited R-numbers: none looked up (preamble file is a pointer to studio bible not on this machine).
