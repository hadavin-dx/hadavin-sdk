# CITATION-TRIAGE (static read of the cited files; no edits to CLAIMS-TABLE.md)

Input: CITATION-CHECK.md, 157 failing quote rows (matches the check).

## Counts per class

- MEANING DIFFERS: 8 (the cited file says something different from the quote)
- WRONG FILE: 3 (text exists, but in another file)
- WRONG LINE: 7 (text exists in the cited file, at another line)
- MISSING: 1 (text is in no cited file)
- PARAPHRASE: 13 (same meaning, different words or marks)
- MISPAIR: 125 (not a real mismatch: the checker attached the quote to the wrong cite, or the quote is a fragment of the row's own prose (not one of the four requested classes; added so nothing is hidden))

Real citation errors needing an edit: WRONG LINE 7, WRONG FILE 3, MISSING 1. MEANING DIFFERS 8 rows are findings the audit already states in the row (none is a hidden contradiction).

Why so many MISPAIR rows: CLAIMS-TABLE rows quote a source document through a short alias (R:32 = VIDEO-RUNSHEET.md:32, P: = PAGE-STATEMENTS-V4.md, RUN: = RUN-ON-LAPTOP.md, PLAN: = PLAN-4-NLITE-FROM-LEAD.md, DOUBTFUL: = DOUBTFUL-SCENE.md, OWNS: = n8n-owns-vs-desk-owns.md, SKIP: = n8n-skip-on-conflict.md, V5: = V5-README.md, RERUN: = RERUN-RUNBOOK.md, DESIGN: = DESIGN-A-README.md, BM: = build_mainframe.py). The checker did not resolve aliases and tested the quote against the evidence cite instead. In every alias case I checked, the quote is present at the alias line.

Not checked: whether each evidence cite (second column) proves the audit verdict; only quote presence and, for the rows below, the meaning of the cited lines. F6-AUDIT rows: all 68 are fragments; their cites were spot-checked as listed in the table.

## Rows that are not PARAPHRASE and not MISPAIR (fix or finding)

| Class | Source row | Claim id | Cited | What the file says | Proposed correction |
|---|---|---|---|---|---|
| MEANING DIFFERS | CLAIMS-TABLE.md:60 | A-021 | VIDEO-RUNSHEET.md:90-90, PAGE-STATEMENTS-V4.md:150-150, PAGE-STATEMENTS-V4.md:153-153 | Cited VIDEO-RUNSHEET.md:90 and PAGE-STATEMENTS-V4.md:150,153 say K3B/K3 are spoken as "killed after the mail left". "mail not yet delivered" is in mf.py:158 (K3B), RUN-ON-LAPTOP.md:67 and V7-NUMBERS:9. The row records this conflict (F-007). | No change to the cites; keep the row as a finding. Add mf.py:158 and RUN-ON-LAPTOP.md:67 as the source of the quote. |
| MEANING DIFFERS | CLAIMS-TABLE.md:172 | A-021 | mf.py:158-158, mf.py:164-164 | Quote is VIDEO-RUNSHEET.md:90 (correct). Cited mf.py:158 says K3B = mail NOT yet delivered. Row already records this (F-007, UNSUPPORTED for K3B). | Cite VIDEO-RUNSHEET.md:90 for the quote and mf.py:158, :164 for the contradiction. |
| MEANING DIFFERS | CLAIMS-TABLE.md:173 | A-022 | mf.py:151-164 | Quotes are VIDEO-RUNSHEET.md:24 and PAGE-STATEMENTS-V4.md:20 (both present). mf.py:151-164 defines K1, K2, K3B, K3 but has no "lane3" names. Row already records the conflict (F-007). | Cite VIDEO-RUNSHEET.md:24 and PAGE-STATEMENTS-V4.md:20 for the quotes; keep mf.py:151-164 as the evidence of the real names. |
| MEANING DIFFERS | CLAIMS-TABLE.md:173 | A-022 | mf.py:151-164 | Quotes are VIDEO-RUNSHEET.md:24 and PAGE-STATEMENTS-V4.md:20 (both present). mf.py:151-164 defines K1, K2, K3B, K3 but has no "lane3" names. Row already records the conflict (F-007). | Cite VIDEO-RUNSHEET.md:24 and PAGE-STATEMENTS-V4.md:20 for the quotes; keep mf.py:151-164 as the evidence of the real names. |
| MEANING DIFFERS | CLAIMS-TABLE.md:227 | A-077 | mf.py:158-158 | Quote is PAGE-STATEMENTS-V4.md:150 and :153 (present). mf.py:158: K3B = mail NOT yet delivered. Row already records this (F-007). | Cite PAGE-STATEMENTS-V4.md:150,153 for the quote; mf.py:158 for the contradiction. |
| MEANING DIFFERS | CLAIMS-TABLE.md:227 | A-077 | mf.py:158-158 | Quote is PAGE-STATEMENTS-V4.md:150 and :153 (present). mf.py:158: K3B = mail NOT yet delivered. Row already records this (F-007). | Cite PAGE-STATEMENTS-V4.md:150,153 for the quote; mf.py:158 for the contradiction. |
| MEANING DIFFERS | CLAIMS-TABLE.md:436 | B-101 | mf.py:83-83 | Quote is RUN-ON-LAPTOP.md:56 (final states include "review"). mf.py:83 treats only done, unknown, failed as final, so review counts as lost. Row already records this (F-031). | Keep as a finding; cite RUN-ON-LAPTOP.md:56 for the quote and mf.py:83 for the code. |
| MEANING DIFFERS | CLAIMS-TABLE.md:450 | B-111 | DOCKER-PROBE.md:5-5 | Quote is RERUN-RUNBOOK.md:42 (tag pull and first two digest pulls got 429; third digest pull worked in 9 s). DOCKER-PROBE.md:5 says the tag pull failed twice and the digest pull worked on the third try. Counts differ; row already says the probe is the source. | Keep as a finding; cite RERUN-RUNBOOK.md:42 for the quote and DOCKER-PROBE.md:5 for the correction. |
| WRONG FILE | CLAIMS-TABLE.md:206 | A-055 | n8n-flows/DESIGN-A-README.md:10-10 | "interval '45 seconds'" is not in DESIGN-A-README.md:10 (that line says "built with lease 120 (older copy; the shipped real and film flows use lease 45)"). It is in n8n-flows-real/mf-recovery.json:26 and mf-form.json:97 (same text in the other flow folders). | Cite n8n-flows-real-v4/mf-recovery.json:26 for the 45 s; keep DESIGN-A-README.md:10 for the 120 s. |
| WRONG FILE | CLAIMS-TABLE.md:307 | RV5 | n8n-flows/mf_leads.sql:4-4 | The INSERT text is in the built flows (n8n-flows-real*/mf-form.json:97, mf-hook.json:97), not in n8n-flows/mf_leads.sql. mf_leads.sql:4 only has "lead_key text PRIMARY KEY". | Cite n8n-flows-real-v5/mf-form.json:97 for the INSERT and mf_leads.sql:4 for the key. |
| WRONG FILE | CLAIMS-TABLE.md:555 | B-192 | n8n-skip-on-conflict.md:44-45 | "lead_key text PRIMARY KEY" is in n8n-flows/mf_leads.sql:4 (also v3, v4 copies line 5), not in n8n-skip-on-conflict.md. | Cite n8n-flows/mf_leads.sql:4 for the key. |
| WRONG LINE | CLAIMS-TABLE.md:545 | B-186 | n8n-published-numbers.md:16-18, n8n-published-numbers.md:26-28 | Row cites OWNS:7-8. "Variant e ... 25 of 25" is n8n-owns-vs-desk-owns.md:10 (line 8 holds variants b, c, d). | Change OWNS:7-8 to OWNS:8 and :10. |
| WRONG LINE | CLAIMS-TABLE.md:546 | B-187 | n8n-skip-on-conflict.md:44-45, n8n-skip-on-conflict.md:58-58 | Check cited n8n-skip-on-conflict.md:44-45 (five-sample table rows sk-a, sk-c) and :58. The words "exactly 1 row in 20 of 20 bursts" are at :63; "1 new, 9 duplicate in 20 of 20 bursts" is at :58. | Change source cite to n8n-skip-on-conflict.md:58 and :63. |
| WRONG LINE | CLAIMS-TABLE.md:546 | B-187 | n8n-skip-on-conflict.md:44-45, n8n-skip-on-conflict.md:58-58 | Check cited n8n-skip-on-conflict.md:44-45 (five-sample table rows sk-a, sk-c) and :58. The words "exactly 1 row in 20 of 20 bursts" are at :63; "1 new, 9 duplicate in 20 of 20 bursts" is at :58. | Change source cite to n8n-skip-on-conflict.md:58 and :63. |
| WRONG LINE | CLAIMS-TABLE.md:546 | B-187 | n8n-skip-on-conflict.md:44-45, n8n-skip-on-conflict.md:58-58 | Check cited n8n-skip-on-conflict.md:44-45 (five-sample table rows sk-a, sk-c) and :58. The words "exactly 1 row in 20 of 20 bursts" are at :63; "1 new, 9 duplicate in 20 of 20 bursts" is at :58. | Change source cite to n8n-skip-on-conflict.md:58 and :63. |
| WRONG LINE | CLAIMS-TABLE.md:555 | B-192 | n8n-skip-on-conflict.md:44-45 | Check cited n8n-skip-on-conflict.md:44-45 (five-sample table). The sentence is at :63 (the alias SKIP:63 in the row is right). | Change source cite :44-45 to :58 and :63. |
| WRONG LINE | CLAIMS-TABLE.md:556 | B-193 | n8n-skip-on-conflict.md:47-47 | Check cited n8n-skip-on-conflict.md:47 (five-sample table row dt-ne-ins). The sentence "extra rows in 9 of 10 bursts" is at :65 (alias SKIP:65 is right). | Change source cite :47 to :65. |
| WRONG LINE | CLAIMS-TABLE.md:556 | B-193 | n8n-skip-on-conflict.md:47-47 | Check cited n8n-skip-on-conflict.md:47 (five-sample table row dt-ne-ins). The sentence "extra rows in 9 of 10 bursts" is at :65 (alias SKIP:65 is right). | Change source cite :47 to :65. |
| MISSING | CLAIMS-TABLE.md:46 | A-030 | VIDEO-RUNSHEET.md:35-35 | "could not tell" is in no file under demo/ (only in audit working files). VIDEO-RUNSHEET.md:37 (scene 8) says "outcome unknown, nobody can say whether the mail went". | Drop the quote marks (it is the audit's own wording) or quote VIDEO-RUNSHEET.md:37 as written. |

## PARAPHRASE rows

| Source row | Claim id | What the file says |
|---|---|---|
| CLAIMS-TABLE.md:48 | A-036 | VIDEO-RUNSHEET.md:38 reads: Alert mail with subject "[demo] Lead desk: mail outcome unknown for the lead id" (word "with" and quote marks differ). |
| CLAIMS-TABLE.md:68 | B-183 | n8n-owns-vs-desk-owns.md:5: "**The desk owns** (repo text, mostly not tested by me): a receipt first, a keyed claim..." (bold marks, elided bracket). |
| CLAIMS-TABLE.md:78 | B-010 | PLAN-4-NLITE-FROM-LEAD.md:78 is a table row; the quote joins its cells with " / ". |
| CLAIMS-TABLE.md:79 | B-011 | PLAN-4-NLITE-FROM-LEAD.md:79 is a table row; the quote joins its cells with " / ". |
| CLAIMS-TABLE.md:85 | B-093 | FAILED-TAKE-NOTE.md:16 has the same words with bold/quote marks placed differently. |
| CLAIMS-TABLE.md:86 | B-094 | FAILED-TAKE-NOTE.md:17 has the same words with bold/quote marks placed differently. |
| CLAIMS-TABLE.md:87 | B-095 | FAILED-TAKE-NOTE.md:19 has the same words with bold/quote marks placed differently. |
| CLAIMS-TABLE.md:93 | B-150 | DESIGN-A-README.md:15 has "state unknown + one alert" and :32 has "unknown (... a person decides, 1 alert)". |
| CLAIMS-TABLE.md:103 | B-182 | n8n-owns-vs-desk-owns.md:4: "**n8n owns** (stated by the lead): intake, field mapping, the ten-at-once trigger..." (bold marks). |
| CLAIMS-TABLE.md:240 | A-090 | smtp_catcher.py:26 comment: "answer 451 (try later) to the next N recipients whose address contains text". |
| CLAIMS-TABLE.md:297 | PLAN-4 | PLAN-4 line 53 and 153 say "OWNER-STEPS v2 Phase D"; line 176 says "OWNER-STEPS plans Phase 0"; the row joins the two. |
| CLAIMS-TABLE.md:433 | B-098 | build_mainframe.py:114 comment reads "{success: true}" (space after the colon); cited as BM:114. |
| CLAIMS-TABLE.md:436 | B-101 | mf.py:83 reads o["lost"] = r["state"] not in ("done", "unknown", "failed") or (...); spaces and an elided tail differ. |

## MISPAIR rows (listed so every row is accounted for)

| Source row | Claim id | Quotes | Note |
|---|---|---|---|
| CLAIMS-TABLE.md:82 | B-045 | 1 | Fragment of the row's own prose (cut at a backtick), not a file quote. |
| CLAIMS-TABLE.md:167 | A-016 | 1 | Quote found at VIDEO-RUNSHEET.md:32 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:206 | A-055 | 2 | Quote found at VIDEO-RUNSHEET.md:57 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:210 | A-060 | 1 | Quote found at n8n-flows/PAGE-STATEMENTS-V4.md:49 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:240 | A-090 | 1 | Quote found at VIDEO-RUNSHEET.md:40 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:243 | A-093 | 1 | Quote found at n8n-flows/PAGE-STATEMENTS-V4.md:51 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:293 | V4 | 3 | Fragment of the row's own prose (cut at a backtick), not a file quote. |
| CLAIMS-TABLE.md:297 | PLAN-4 | 1 | Fragment of the row's own prose (cut at a backtick), not a file quote. |
| CLAIMS-TABLE.md:332 | B-013 | 2 | Quote found at PLAN-4-NLITE-FROM-LEAD.md:39 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:349 | B-030 | 1 | Quote found at PLAN-4-NLITE-FROM-LEAD.md:57 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:353 | B-034 | 1 | Quote found at PLAN-4-NLITE-FROM-LEAD.md:57 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:355 | B-036 | 1 | Quote found at VIDEO-RUNSHEET.md:22 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:360 | B-041 | 2 | Quote found at PLAN-4-NLITE-FROM-LEAD.md:77 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:362 | B-043 | 1 | Quote found at PLAN-4-NLITE-FROM-LEAD.md:78 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:364 | B-045 | 3 | Quote found at PLAN-4-NLITE-FROM-LEAD.md:79 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:365 | B-046 | 3 | Quote found at PLAN-4-NLITE-FROM-LEAD.md:79 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:366 | B-047 | 2 | Quote found at PLAN-4-NLITE-FROM-LEAD.md:79 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:376 | B-057 | 1 | Quote found at PLAN-4-NLITE-FROM-LEAD.md:126 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:397 | B-070 | 1 | Quote found at DOUBTFUL-SCENE.md:3 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:407 | B-080 | 1 | Quote found at DOUBTFUL-SCENE.md:12 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:408 | B-081 | 1 | Quote found at DOUBTFUL-SCENE.md:12 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:413 | B-086 | 1 | Quote found at VIDEO-RUNSHEET.md:30 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:414 | B-087 | 1 | Quote found at DOUBTFUL-SCENE.md:13 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:432 | B-097 | 1 | Quote found at RUN-ON-LAPTOP.md:22 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:433 | B-098 | 1 | Wording is the audit's own (not a file quote). |
| CLAIMS-TABLE.md:434 | B-099 | 1 | Quote found at RUN-ON-LAPTOP.md:27 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:436 | B-101 | 1 | Wording is the audit's own (not a file quote). |
| CLAIMS-TABLE.md:437 | B-102 | 1 | Quote found at RUN-ON-LAPTOP.md:63 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:440 | B-105 | 1 | Quote found at RUN-ON-LAPTOP.md:66 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:441 | B-106 | 1 | Quote found at RUN-ON-LAPTOP.md:68 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:449 | B-110 | 1 | Quote found at RERUN-RUNBOOK.md:25 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:451 | B-112 | 1 | Quote found at RERUN-RUNBOOK.md:62 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:509 | B-158 | 1 | Quote found at RUN-ON-LAPTOP.md:44 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:510 | B-159 | 2 | Quote found at n8n-flows/DESIGN-A-README.md:28 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:511 | B-160 | 1 | Quote found at n8n-flows/DESIGN-A-README.md:28 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:532 | B-177 | 3 | Quote found at n8n-flows-film-v5/V5-README.md:19 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:533 | B-178 | 1 | Quote found at n8n-flows-film-v5/V5-README.md:20 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:544 | B-185 | 1 | Quote found at n8n-owns-vs-desk-owns.md:6 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:545 | B-186 | 1 | Quote found at n8n-owns-vs-desk-owns.md:8 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:578 | B-207 | 2 | Quote found at flows-audit/inputs/OWNER-STEPS-realrun-v3.md:23 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| CLAIMS-TABLE.md:603 | R1 | 2 | Wording is the audit's own (not a file quote). |
| CLAIMS-TABLE.md:610 | B-078 | 1 | Quote found at VIDEO-RUNSHEET.md:38 (the row's short alias cite, e.g. R/P/RUN/PLAN/DOUBTFUL/OWNS/SKIP/V5/RERUN/DESIGN); the checker paired it with the evidence cite. |
| F6-AUDIT.md:28 | line 28 | 2 | Prose fragments; cites spot-checked as listed above. |
| F6-AUDIT.md:30 | F-009 | 5 | Prose fragments; cites spot-checked as listed above. |
| F6-AUDIT.md:40 | F6-01 | 26 | Prose fragments; cites spot-checked as listed above. |
| F6-AUDIT.md:41 | F6-02 | 10 | Prose fragments; cites spot-checked as listed above. |
| F6-AUDIT.md:42 | F6-03 | 6 | Prose fragments; cites spot-checked as listed above. |
| F6-AUDIT.md:43 | F6-04 | 3 | Prose fragments; cites spot-checked as listed above. |
| F6-AUDIT.md:44 | F6-06 | 3 | Prose fragments; cites spot-checked as listed above. |
| F6-AUDIT.md:45 | F6-07 | 5 | Prose fragments; cites spot-checked as listed above. |
| F6-AUDIT.md:49 | F-010 | 6 | Prose fragments; cites spot-checked as listed above. |
| F6-AUDIT.md:66 | F6-03 | 2 | Prose fragments; cites spot-checked as listed above. |
