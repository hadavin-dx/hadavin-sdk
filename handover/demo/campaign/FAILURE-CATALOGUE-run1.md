# Live-proof campaign: failure catalogue (EVIDENCE RUNNER output, no judgement)

Tree: /tmp/dpld-camp (not edited). Run 2026-11-09 18:49-19:18 UTC (IST = UTC+5:30: 00:19-00:48 on 10 Nov). Runner: `python3 -m live_l2.campaign --only <name> --drain-timeout 120`, one scenario at a time, detached via /home/user/build/campaign/run_all.sh. Raw data: `/home/user/build/campaign/<scenario>/<scenario>/` (requests.jsonl, summary.json, checks.json, checks.txt, samples.jsonl, desk.log, model.jsonl, catcher.jsonl, crm.json, book.sqlite3). Per-scenario `uptime-start.txt`/`uptime-end.txt` sit one level up. Progress log: progress.log.

## Things to read first (what failed / what is uncertain)
- 8 of 20 scenarios have a failing check (model-slow, model-timeout, model-429, model-malformed, model-refusal, model-5xx, model-flaps, catcher-slow). 12 scenarios pass all 7 checks.
- Failing checks are only two kinds: check 5 (model calls per lead above bound 3: 5 calls seen) and check 2 (follow-ups still pending when the drain timeout expired). No run broke check 1, 3 or 4 (receipts, one message per key, CRM rows) and no run recorded a 503 outside dupmix-30pct.
- Drain timeout: I passed `--drain-timeout 120` for the whole campaign (the tool default is 240). The three scenarios that failed on drain (model-slow, model-timeout, catcher-slow) were re-run once with 240; they still failed (rerun dirs `rerun240-<name>/`). In the 240 s re-runs check 7 also fails because the checker's own drain ceiling stays 120 s.
- Other agent load: loadavg stayed between 0.3 and 2.2 (see below), so latency numbers show little inflation by the other agent; I did not see its process names; I cannot rule out some influence.
- There is NO "20 percent failing model" (mixed ok/5xx) mode in the tool; not built. model-5xx (100 percent 5xx) and model-flaps (5xx 5-15 s, timeout 20-25 s, ok otherwise, i.e. about 17 of 30 s failing) were run instead.
- Doors: the load driver alternates the form door and the webhook door request by request (even index form, odd webhook), in bursts, rates and dupmix; dupmix repeats go through the other door at the same moment (half) or the same door later (half). So both doors are used in every scenario.
- "Drain time" = seconds from the last intended send to the book having no pending/sending follow-up (summary.json `drain_seconds_after_load`). null = never drained within the timeout.
- Latency = request round trip at the driver; p50/p95/p99 come from summary.json (p50, p95, max only; p99 not recorded by the tool; for bursts max is the upper bound).
- Restarts: crash scenarios each had 1 restart, exit code 137 (simulated kill), restart about 0.05 s later on the same port.

## Table (one row per scenario)

Counts: req = requests sent; tries = attempts incl. retries; codes are final status per request (attempt codes in brackets when different).

| scenario | works | breaks | cause (raw data only) | status | numbers | first failure point |
|---|---|---|---|---|---|---|
| burst-10 | all | nothing | n/a | 7/7 pass | req 10, tries 10; 201x10; lat p50 0.041 p95 0.046 max 0.046 s; retries 0; 503 0; drain 0.71 s; restarts 0 | none |
| burst-200 | all | nothing | n/a | 7/7 pass | req 200; 201x200; p50 0.522 p95 0.72 max 0.87 s; send lag max 0.38 s; retries 0; 503 0; drain 1.81 s; desk peak 92 MB, 172 threads, 432 fds | none |
| burst-1000 | all | nothing | n/a | 7/7 pass | req 1000; 201x1000; p50 0.944 p95 1.138 max 1.491 s; send lag max 3.38 s; retries 0; 503 0; drain 8.22 s; desk peak 305 MB, 1002 threads, 2867 fds | none |
| rate-20x60 | all | nothing | n/a | 7/7 pass | req 1200 (20/s x 60 s); 201x1200; p50 0.010 p95 0.481 max 1.774 s; retries 0; 503 0; drain 3.21 s | none |
| dupmix-30pct | all 7 checks | 503s seen by clients, then retried to success | 76 attempts got 503 (rate 0.0596) first at 15.75 s after load start; cause of 503 not stated in data (the desk limits from S1b; unknown which) | 7/7 pass | req 1200 (20/s, 840 firsts + 360 repeats); final 201x1022, 200x178; attempts 1276 (201 1022, 200 178, 503 76); 76 requests retried once, 0 ended on 503; p50 0.772 p95 6.024 max 8.145 s; drain 0.51 s; 840 leads, 1007 receipts, 840 messages; model calls 879 for 840 leads (max 3 for one lead, bound 3) | first 503 at 15.75 s |
| crash-A | all | 25 attempts failed during restart | desk killed at 3.0 s (exit 137), restart ~0.05 s later; client saw 1 RemoteDisconnected and 24 ConnectionRefused, retried OK | 7/7 pass | req 400; 201x400; tries 425; p50 0.010 max 0.04 s; drain 0.21 s; restarts 1 (137) | 3.0 s (crash) |
| crash-A2 | all | 25 attempts failed during restart | same shape as crash-A | 7/7 pass | req 400; 201x400; tries 425 (1 RemoteDisconnected, 24 refused); max 0.038 s; drain 0.20 s; restarts 1 (137) | 3.0 s |
| crash-B | all | 24 attempts failed during restart | same shape | 7/7 pass | req 400; 201x400; tries 424 (1 RemoteDisconnected, 23 refused); max 0.047 s; drain 0.31 s; restarts 1 (137) | 3.0 s |
| crash-D1 | all | 20 attempts failed during restart | desk down about 1 s; connection refused only | 7/7 pass | req 400; 201x400; tries 420 (20 refused); max 0.052 s; drain 0.31 s; restarts 1 (137) | 3.0 s |
| crash-D2 | all | 20 attempts failed during restart | same | 7/7 pass | req 400; 201x400; tries 420 (20 refused); max 0.056 s; drain 0.20 s; restarts 1 (137) | 3.0 s |
| model-slow (model answers after 3 s) | requests accepted (201x300, p50 0.01 s); 130 follow-ups sent in 120 s drain window | follow-ups not finished | desk.log repeats "follow-up not driven now: all drive places are taken; the reaper drives it later"; 3 s per model call limits how many follow-ups run at once; the exact limit is not in the data | 6/7 pass; fail check 2 (pending 170 + sent 130 = 300). Rerun with 240 s: still fail checks 2 and 7 (pending 132, sent 168) | req 300 (10/s x 30 s); 201x300; retries 0; 503 0; drain never reached (120 s and 240 s); model calls 130 / 168 | at drain timeout (check 2); first pending seen from the start of load (model busy) |
| model-timeout | requests accepted (201x200) | no follow-up finished | desk.log "follow-up step 1 failed: QualifierTimeout"; fake model holds 15 s, desk waits 5 s, model log shows status 499 x149 (client gone); 0 messages | 6/7 pass; fail check 2 (pending 200, sent 0). Rerun 240 s: still fail 2 and 7 (pending 200, 204 model calls all 499) | req 200; 201x200; retries 0; 503 0; drain never reached | at drain timeout; no lead ever left pending |
| model-429 | all checks except 5 | model calls above bound | model answers 429; 1000 calls for 200 leads, 5 per lead; all 200 leads ended failed (0 messages, 0 CRM rows) | 6/7 pass; fail check 5 (most for one lead 5; bound 3) | req 200; 201x200; retries 0; 503 0; drain 15.33 s | check 5 evaluated at end; 5 calls per lead for every lead |
| model-malformed | same as model-429 | model calls above bound | model returns malformed JSON; 1000 calls, 5 per lead; 200 failed | 6/7 pass; fail check 5 | drain 16.24 s; otherwise same as model-429 | same |
| model-refusal | same | model calls above bound | model refuses; 1000 calls, 5 per lead; 200 failed | 6/7 pass; fail check 5 | drain 16.33 s | same |
| model-5xx (100% 5xx) | same | model calls above bound | model returns 5xx; 1000 calls, 5 per lead; 200 failed | 6/7 pass; fail check 5 | drain 15.34 s | same |
| model-flaps | 299 of 300 follow-ups sent; no duplicates | model calls above bound | 593 calls for 300 leads, max 5 per lead; 1 lead failed (during outage windows 5-15 s and 20-25 s) | 6/7 pass; fail check 5 | req 300 (10/s x 30 s); 201x300; retries 0; 503 0; drain 0.21 s; sent 299, failed 1 | check 5 at end; max 5 calls for one lead |
| catcher-down (mail server down 5-20 s) | all | nothing | 297 sent, 3 failed (no message); 300 CRM rows, 300 calls | 7/7 pass | req 300; 201x300; retries 0; drain 0.21 s | none |
| catcher-drop-after-data | all | nothing | mail server drops after DATA: 200 follow-ups ended "unknown" (allowed by check 3), 200 messages present | 7/7 pass | req 200; 201x200; drain 0.21 s; unknown 200 | none |
| catcher-slow (mail answers after 3 s) | requests accepted (201x200) | follow-ups not finished | desk.log "all drive places are taken"; 106 sent in 120 s window; rerun 240 s: sent 143, pending 56, sending 1 | 6/7 pass; fail check 2 (pending 93 + sending 1). Rerun: fail 2 and 7 | req 200; 201x200; retries 0; 503 0; drain never reached | at drain timeout |

Check 5 note: bound is 3 model calls per lead; the five scenarios above saw 5, which is the retry count the desk applies (cause of the number 5 vs the bound is for the builder; I did not read the code).
"Possible desk bug, for the builder": (1) model-429, -malformed, -refusal, -5xx, -flaps exceed the 3-call bound with 5 calls per lead; (2) model-slow, model-timeout and catcher-slow leave follow-ups pending beyond 120 s and 240 s (model-timeout: no lead completed in 240 s).

## CAPACITY (from the data only)
- Bursts: 10, 200, 1000 requests all passed 7/7, all 201, zero 503, zero retries. Highest burst run and passed: 1000 (both doors, 500 each). No larger burst was run, so no first failing burst size exists in this data.
- Steady rate: 20 requests/s for 60 s (1200) passed 7/7. Dupmix 20/s with 30 percent repeats passed 7/7 but produced 76 503s (5.96 percent of attempts, all recovered by retry). 503 first appeared at 15.75 s into the dupmix run. No steady rate above 20/s was run.
- Highest load where all 7 passed: burst 1000 and 20/s. First load where a check failed: none from load alone; all failures came from fault modes (model or mail server), not from request volume.
- Desk resource peaks: burst-1000 305 MB RSS, 1002 threads, 2867 open files (ulimit -n 20000).

## Machine specs and load
- Start 18:49:28 UTC: nproc 4; load average 0.36 0.25 0.30; ulimit -n 20000; somaxconn 4096; free -m total 16086, used 794, free 14104; Python 3.13.18; kernel Linux 6.18.44.
- End: see machine-end.txt (load 0.21 0.32 0.44, 19:18:45 UTC).
- Load average at the start and end of every scenario: progress.log (START/END lines, columns 1/5/15 min) and `<scenario>/uptime-start.txt`, `uptime-end.txt`. Range seen: 0.33 to 2.15 (1-minute), highest at the start of crash-A, right after dupmix-30pct. Reruns: progress-rerun.log.

## Not run / not checked
- Any burst above 1000 or rate above 20/s; no scenario beyond the 20 listed; no 20-percent-failing-model mode (does not exist); no run with the other agent absent for comparison.
- Latency p99 is not recorded by the tool (p50, p95, max only).
- Cause of the 76 503s in dupmix-30pct not examined in the desk code; cause of "5 calls per lead" not examined in code (record only).
- Retry of an erroring tool: not needed, no tool traceback occurred (runner_error null in all summaries).
- Per-scenario check 7 uses a 120 s ceiling even in 240 s reruns.
- Did not verify what the other agent was running; loadavg only.
- Cleanup: `ps` shows no desk, fake, catcher, driver or run_all/run_rerun processes left from this campaign.
