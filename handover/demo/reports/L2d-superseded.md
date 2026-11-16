# L2d: which numbers of the first campaign cannot be trusted (superseded)

Source: /home/user/build/campaign/FAILURE-CATALOGUE.md (run 1, 2026-11-09 18:49-19:18 UTC, i.e. 00:19-00:48 IST on 10 Nov),
made with the checker and driver of /tmp/dpld-camp (before L2c). Re-checked offline with the fixed checker
(`python -m live_l2.recheck`, per scenario: /home/user/build/L2d-recheck/<scenario>.txt and .json; the saved folders were
only read, the book is copied to a temporary folder first; I verified no file under campaign/ is newer than my start).

## What is wrong with the old numbers, in plain words (first)
1. Every "7/7 pass" is suspect. The old checker passed a book where every lead was lost, an empty or short request log,
   receipts with no verdict, a stale book, and an `unknown` follow-up with no reason. A pass proved less than it said.
   (The offline recheck below shows which passes survive.)
2. Check 5 used one global bound of 3. The desk legitimately asks the model on each of up to 5 automatic tries while the
   model is down. The five "check 5 fail" rows (model-429, model-malformed, model-refusal, model-5xx, model-flaps) were
   false alarms by the old bound: they are within the stated bound of 6 and pass now. The same old check counted
   finished calls, not arrivals, so calls cut short in model-timeout are not in its counts ("149 calls", "204 calls"
   are lower bounds, not counts).
3. The old bound of 3 also hid the opposite fault: dupmix-30pct was reported "7/7 pass", but with the model answering
   (mode ok) the fixed bound of 1 call per lead FAILS it: 879 calls for 840 leads, one lead asked 3 times (at +0 s, +1.9 s
   and +24 s). That is the shape of ORDER 221 item M2 (label step before the claim, the reaper calls the model again), not
   a checker artefact. Needs the desk M2 patch and a live re-run to confirm.
4. catcher-slow did not test what it claims. The catcher answered after 3 s against a 5 s send timeout, so no send could
   become "maybe sent"; the numbers "106 sent / 143 sent" describe slow sending, not the ambiguous path. The fixed
   scenario uses 7 s against a 2 s timeout; no run of it exists yet.
5. The drain verdicts for model-slow, model-timeout and catcher-slow ("pending 170", "pending 200", "pending 93") are
   still reproduced by the fixed checker (the desk really did not finish), so those three are real failures, not checker
   noise. Their cause is not known (stuck desk or just slow); not examined here.
6. The request log was written by a driver that did not catch every kind of broken HTTP reply and whose count was not
   compared with the intended count by the checker. In all saved folders logged = intended (checked now through the
   facts files: lines = intended for all 23 folders), so the request counts and the status mix stand. Latency numbers
   (p50, p95, max) are driver-side measurements and stand as measurements; they have not been re-measured with the new
   driver, and the saved facts files carry no run marker, so a stale-book test by marker was not possible for them (the
   test by id prefix and by email was done and passes).

## Per scenario (fixed checker, offline; "must re-run" = needs a live desk)
| Scenario | Run 1 said | Now | Failing check / run fault | Re-run on a live desk? |
|---|---|---|---|---|
| burst-10, burst-200, burst-1000, rate-20x60 | 7/7 | PASS | none | Not needed for the checks; re-run once with the new driver to get a run marker and fresh latency numbers |
| crash-A, A2, B, D1, D2 | 7/7 | PASS | none (bound 2 = 1 + slack; unknown ceiling 8) | No, same as above |
| catcher-down | 7/7 | PASS | none | No |
| catcher-drop-after-data | 7/7 | PASS | none (200 unknown, each with a message and a fitting reason) | No |
| model-429, model-malformed, model-refusal, model-5xx | check 5 fail (5 > 3) | PASS | none (5 calls per lead, bound 6) | No |
| model-flaps | check 5 fail | PASS with RERUN note | none; but the saved model log has no arrival lines, so calls cut short by the 2 s timeout may be missing | Yes (recheck exit code 3) |
| dupmix-30pct | 7/7 | FAIL | check 5: 879 calls for 840 leads, most for one lead 3, bound 1 | Yes, after the desk M2 patch (and to confirm the cause) |
| model-slow | fail 2 | FAIL | checks 2 and 7: desk never drained (170 pending) | Yes, after M2 (a 3 s model call is what trips the reaper) |
| model-timeout | fail 2 | FAIL | checks 2 and 7: never drained (200 pending); RERUN: no arrival lines | Yes |
| catcher-slow | fail 2 | FAIL | checks 2 and 7: never drained; RERUN: 3 s catcher cannot cause ambiguity | Yes, with the fixed scenario (7 s catcher, 2 s send timeout) |
| rerun240-model-slow, rerun240-model-timeout, rerun240-catcher-slow | fail 2 and 7 | FAIL | same as their first runs (checks 2 and 7, never drained) | Covered by the re-runs above |

Totals of the offline recheck: 23 folders; 15 pass clean, 1 passes with a RERUN note (model-flaps), 7 fail
(dupmix-30pct; model-slow, model-timeout, catcher-slow and their three 240 s re-runs).

## Numbers of run 1 that need no change
Requests sent and status mix (201/200 counts), 503 counts and rate in dupmix-30pct (taken from the request log, not from
the old checker), restart counts and exit codes 137, machine specs and loadavg, desk resource peaks. They are measurements,
not check verdicts.

## Numbers of run 1 that must not be quoted any more
"12 of 20 scenarios pass all 7 checks"; "failing checks are only check 5 and check 2" (check 5 failures were false alarms,
dupmix has a real check 5 failure); "highest load where all 7 passed" is still true for burst 1000 and 20/s on the offline
recheck but is not a live proof until re-run with the new driver; "bound 3" anywhere; the model-call counts of
model-timeout; everything said about catcher-slow ambiguity.
