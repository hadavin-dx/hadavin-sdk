# Citation check of patches r3 (egm-codebase-details a7a9c8a7), saved condensed by flows-audit. Reviewer words unverified; I re-checked items 28 and 34 myself.
Matches the flow files (file:line): 45 s lease mf-hook.json:97, mf-form.json:97, mf-recovery.json:26; 30 s check mf-recovery.json:2,9-10; attempts < 3 :26, >= 3 :102; saves none (mf-hook/mf-form :424-426, mf-recovery :337-339, mf-sub-crm-mail :809-811); mail_sent ordering mf-sub-crm-mail.json:202 -> SendMail :265 -> MarkDone :284, unknown :307/:330; states processing/done/review/unknown; 720 s alert window mf-recovery.json:124; 160 s arithmetic; 59.6 s and 59.4 s (V7 L20-21, n=20, lease 20 s v3); T14 V7 L7; T15 V7 L25; K3/K3B V7 L22-23.
## Problems (Major unless noted)
11 144.3 s, n=1, lease 120 s: no readable raw source anywhere under handover (only second-hand in REPORT.md, PAGE-STATEMENTS-V4.md, AUDIT-*.md). Patches already say "relayed, report not seen"; keep it labelled relayed and never film it.
12 13 minutes / 780 s: only relayed (PAGE-STATEMENTS-V4.md:134,156, REPORT.md:73); flow files give 12 min (720 s, mf-recovery.json:124; V4-README.md:9 "up to 12 min", "12 to 13 min for hung SMTP"). Not in the video.
23 T13 "3 at once plus a database kill" is not in V7 (only AUDIT-VIDEO-RUNSHEET.md:19); n=13 and "raw not re-read" match V7 L14, L19.
24 K4/K5 "not run": V7 L1 scope is v3 only; "not run on real-v5" is not backed.
30/31 "8 of 18 ended unknown", 60.1-61.9 s: relay HB194 only; the lines are deleted by the patch.
32 V7 L12 still says "B90 n=2"; the settled n=3 has no raw source in the tree.
36 "Total: 19 statements" cannot be confirmed from the hunks alone.
5 old totals 355/380 s only in removed text and demo/REPORT.md:72. 35 example.com UNVERIFIED (flagged in the patch).
## Reviewer errors I corrected
28 AF1 272.1 s: the checker said not in V7; it IS in V7 line 4 (first table, AF1, "first alert 272.1 s"). 34 lanes7/evidence-patches-r4.txt exists (flows-audit/lanes7/); build_mainframe.py exists under handover/demo/n8n-mainframe/ per the evidence run (find here only listed scratch copies).
## Not checked
inputs/ and lanes in depth; raw V7 mf_result files (laptop only); lane3, HB180/186/189/194 raw (not in tree).
