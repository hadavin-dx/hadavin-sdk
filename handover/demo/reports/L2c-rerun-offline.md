# L2c: which campaign results can be re-checked offline

Command per scenario: `PYTHONPATH=src:. python -m live_l2.recheck /home/user/build/campaign/<s>/<s>` (read-only; the book is copied to a temp folder). Raw log: /tmp/l2c-recheck-all.log. All 20 scenario folders existed and held summary.json.

Limits of an offline recheck: the crash flag is only inferred (absent file = consumed, plus events_fired); restarts come from summary.json; the catcher mode comes from catcher.mode. Nothing here proves the desk would behave the same on a new run.

## Re-checked offline, all 7 checks hold, no run fault, no RERUN reason (16)
burst-10, burst-200, burst-1000, rate-20x60, dupmix-30pct, catcher-down, catcher-drop-after-data, crash-A, crash-A2, crash-B, crash-D1, crash-D2, model-429, model-5xx, model-malformed, model-refusal.
Caveat: catcher-drop-after-data and crash-* hold under the new ceilings (max_unknown), whose size is my choice (DRIVE_MAX = 8 for crashes; none for drop-after-data).

## Must be re-run (4)
- catcher-slow: FAILS offline (check 2 and 7, "the desk never drained": 93 pending, 1 sending at the end, drain marker null). Also catcher mode was `slow 3` against a 5 s send timeout, so nothing could become ambiguous. The campaign config is changed (slow 7, send timeout 2 s): re-run.
- model-slow: FAILS offline (check 2 and 7; 170 of 300 still pending, drain marker null). The drain never happened in the old run, so the saved data cannot tell a slow desk from a stuck one. Re-run with the new drain handling.
- model-timeout: FAILS offline (200 pending, nothing sent, drain null) and has no arrival lines in model.jsonl, so check 5 may undercount. Re-run.
- model-flaps: all 7 checks hold, but model.jsonl has no arrival lines (timeout-mode calls are logged only after the hold), so check 5 may undercount. Re-run (exit 3).

Honest note: the three drain failures are real findings of the old data, not recheck bugs: drained_ts is null in all three. I did not investigate whether the desk was stuck or only slow; the new campaign (supervisor join, drain marker with timed_out) is what answers that.
