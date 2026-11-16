# Campaign run 2 re-checked offline with the L2e checker (EVIDENCE: recheck output, not judged by the checker's author)
Date: see git log. Command per scenario: `PYTHONPATH=src:. python -m live_l2.recheck <saved dir>` on the L2e tree (/tmp/dpld-l2e); raw output per scenario in run2-recheck-l2e/<scenario>.txt.
Result: 17 of 20 scenarios still hold all 7 checks (exit 0, no run faults, no RERUN reason) under the stricter checker (checks for lost leads, CRM-before-send, healthy-window sends, evidence, counts by identity). 3 fail, as in the live verdicts:
- model-slow: checks 2, 3, 4, 5, 7. 168 sent, 132 pending at the end of the 240 s drain (132 leads from a healthy window not sent). Check 4: 167 CRM rows for 168 leads marked done, 1 missing (cause not yet known; long-drain re-run in progress to see whether it is a snapshot effect).
- model-timeout: checks 2, 5, 7. 200 pending, 0 sent, 210 model calls for 162 leads (max 3 for one lead, bound 6), 38 leads never tried.
- catcher-slow: check 7 only (drain 218.56 s; checker ceiling 120 s). All 200 ended unknown with one mail each.
The saved run 2 folders stored no bounds, so the catalogue bounds of today were used (BOUNDS line in each file). Not re-run live: the live re-run on the final tree is still to do.
