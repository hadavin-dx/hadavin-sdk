# CITATION-FIXES (read of the cited sources; CLAIMS-TABLE.md and lanes13/ not touched)

Basis: CITATION-TRIAGE.md. Every corrected cite below was found by opening the file and reading the line (grep -n plus a read of the line). Nothing was run. Paths are under `handover/demo/` unless stated.

Note on row ids: the "CLAIMS-TABLE.md:NN" line numbers in CITATION-TRIAGE.md and CITATION-CHECK.md do not match the table as it stands now (for example A-021 is now at line 246, not 60 or 172). I therefore name each row by claim id. The triage listed some rows twice (A-021, A-022, A-077, B-187, B-193); they are merged here.

## Failures first (rows I could not resolve)

None. All 19 listed rows were resolved. Two points the lead should know:

1. A-030 (MISSING) has no file fix. The words "could not tell" exist in no file under `demo/`. They are the audit's own wording, so the fix is in the table: drop the quote marks. The quote that really sits at the cited line is "Intake list still empty." (VIDEO-RUNSHEET.md:35).
2. In the MISPAIR spot-check, 1 of 15 was a real error (B-186, see below). The triage called it a mispair, but its alias cite is wrong.

## WRONG FILE (3)

| id | old cite | corrected cite (verified by reading) |
|---|---|---|
| A-055 | n8n-flows/DESIGN-A-README.md:10 for `interval '45 seconds'` | n8n-flows-real-v4/mf-recovery.json:26 (`interval '45 seconds'`; also n8n-flows-real-v5/mf-recovery.json:26 and n8n-flows-real-v4/mf-form.json:97). Keep DESIGN-A-README.md:10 only for the 120 s ("built with lease 120 (older copy; the shipped real and film flows use lease 45)"). |
| RV5 | n8n-flows/mf_leads.sql:4 for the INSERT text | n8n-flows-real-v5/mf-form.json:97 holds `INSERT INTO mf_leads(...) ... interval '45 seconds' ... ON CONFLICT (lead_key) DO NOTHING RETURNING`. Keep n8n-flows/mf_leads.sql:4 for `lead_key text PRIMARY KEY` only. |
| B-192 | n8n-skip-on-conflict.md:44-45 for `lead_key text PRIMARY KEY` | n8n-flows/mf_leads.sql:4 (same text at n8n-flows-v3/mf_leads.sql:5 and n8n-flows-v4/mf_leads.sql:5). For the "20 of 20 bursts" sentence see the WRONG LINE table. |

## WRONG LINE (7 rows in the triage; 4 distinct claims)

| id | old cite | corrected cite (verified by reading) |
|---|---|---|
| B-186 | alias OWNS:7-8 | n8n-owns-vs-desk-owns.md:8 (variants b, c, d, "20 of 20 clean each") and :10 (variant e, "25 of 25 clean", "1 of 50"). Line 7 is variant a. The "Source:" cites n8n-published-numbers.md:16-18 and :26-28 are correct (:16-18 variants b, c, d at 20 of 20; :26 variant e 25 of 25; :28 1 of 50). |
| B-187 | Source n8n-skip-on-conflict.md:44-45, :58 | n8n-skip-on-conflict.md:63 ("kept exactly 1 row in 20 of 20 bursts") and :58 ("new" hits 1, "duplicate" hits 9, 20 of 20 bursts). Lines 44-45 are table rows sk-a and sk-c. Alias OWNS:9 is correct (checked). |
| B-192 | Source n8n-skip-on-conflict.md:44-45 | n8n-skip-on-conflict.md:63 (alias SKIP:63 is right). Line 58 is not needed for this quote. |
| B-193 | Source n8n-skip-on-conflict.md:47 | n8n-skip-on-conflict.md:65 ("made extra rows in 9 of 10 bursts"). Line 47 is the table row dt-ne-ins (9, 10, 1, 9, 3). Alias SKIP:65 is right. Line 47 may stay as the raw numbers. |

## MISSING (1)

| id | old cite | corrected cite |
|---|---|---|
| A-030 | VIDEO-RUNSHEET.md:35 for "could not tell" | cannot find: no file under `demo/` contains "could not tell" (grep over all `*.md` outside the audit files). VIDEO-RUNSHEET.md:35 does contain "Intake list still empty." (the quote). The nearest real wording is VIDEO-RUNSHEET.md:37 (scene 8): "outcome unknown, nobody can say whether the mail went". Fix: drop the quote marks round "could not tell" (audit's own words) or quote line 37 as written. |

## MEANING DIFFERS (8 rows in the triage; 5 distinct claims)

These are findings the audit already records. The edit is only to put each cite next to the right statement. All lines read.

| id | old cite | corrected cite |
|---|---|---|
| A-021 | VIDEO-RUNSHEET.md:90, PAGE-STATEMENTS-V4.md:150 and :153 for the words "mail not yet delivered" | Quote "killed after the mail left" is at VIDEO-RUNSHEET.md:90 and n8n-flows/PAGE-STATEMENTS-V4.md:150, :153 (correct). "mail NOT yet delivered" (K3B) is at n8n-mainframe/mf.py:158, RUN-ON-LAPTOP.md:67 and V7-NUMBERS-lead-read.md:9; K3 (mail delivered) is at mf.py:164, RUN-ON-LAPTOP.md:67, V7-NUMBERS-lead-read.md:8. |
| A-022 | mf.py:151-164 for the "lane3" names | Quotes: VIDEO-RUNSHEET.md:24 ("Lane3 K3 = killed after the CRM write") and n8n-flows/PAGE-STATEMENTS-V4.md:20 (lane3 K3 = this page's K3B; lane3 K6 = demo K3), also :150. mf.py:151-164 defines K1, K2, K3B, K3 and holds no "lane3" name: the evidence of the real names. |
| A-077 | mf.py:158 as support for the quote | Quote at n8n-flows/PAGE-STATEMENTS-V4.md:150 and :153; mf.py:158 (K3B: mail NOT yet delivered) is the contradiction. |
| B-101 | mf.py:83 as support for the quote | Quote at RUN-ON-LAPTOP.md:56 ("lost = ... (done, unknown, failed or review)"). mf.py:83 reads `o["lost"] = r["state"] not in ("done", "unknown", "failed") or ...`, so review counts as lost. Keep as finding. |
| B-111 | DOCKER-PROBE.md:5 as support for the quote | Quote at RERUN-RUNBOOK.md:42 (tag pull and first two digest pulls got 429; third digest pull worked in 9 s). DOCKER-PROBE.md:5 says the tag pull failed twice and the digest pull worked on the third try after waits (9 s). The counts differ; DOCKER-PROBE.md:5 is the source. |

## MISPAIR spot-check: 15 of 125

Method: I listed the MISPAIR rows of the triage that name a claim id (about 52 rows; the other rows are F6-AUDIT fragments), drew 15 with a seeded random shuffle, took each quote from CITATION-CHECK.md, and read the alias line named in the claim row. Not sampled: the 68 F6-AUDIT fragment rows and the rest of the alias rows. The result below covers the 15 only.

Result: 14 of 15 were genuine mispairs (quote present at the alias line, or a fragment of the row's own prose). 1 of 15 (B-186) was a real error (wrong alias line).

| id | alias cite checked | result |
|---|---|---|
| A-060 | P:49 | mispair: quote at n8n-flows/PAGE-STATEMENTS-V4.md:49 |
| V4 | none (quotes are cut prose: " of the desk repo, ", "VIDEO-RUNSHEET.md") | mispair: fragment of the row's own prose |
| PLAN-4 | none (quotes are cut prose) | mispair: fragment of the row's own prose |
| B-013 | PLAN:39 | mispair: quote at PLAN-4-NLITE-FROM-LEAD.md:39 |
| B-041 | PLAN:77 | mispair: "bad_key" at PLAN-4-NLITE-FROM-LEAD.md:77 |
| B-043 | PLAN:78 | mispair: quote at PLAN-4-NLITE-FROM-LEAD.md:78 |
| B-045 | PLAN:79 | mispair: "ONE in-process lock (single flight)" at :79 |
| B-047 | PLAN:79 | mispair: "makes no second call" at :79 |
| B-057 | PLAN:126 | mispair: ".drop = 1" at :126 |
| B-080 | DOUBTFUL:12 | mispair: "272.1 s" at DOUBTFUL-SCENE.md:12 |
| B-099 | RUN:27 | mispair: quote at RUN-ON-LAPTOP.md:27 |
| B-106 | RUN:67-68 | mispair: "kill point reached in every sample" at RUN-ON-LAPTOP.md:68 |
| B-112 | RERUN:62 | mispair: quote at RERUN-RUNBOOK.md:62 |
| B-185 | OWNS:6-7 | mispair: "default duplicate node let duplicates through" at n8n-owns-vs-desk-owns.md:6, "clean in 12 of 20" at :7 |
| B-186 | OWNS:7-8 | REAL ERROR: the quotes are at :8 and :10, not :7-8 (listed above under WRONG LINE) |

Implication for the lead: the triage's claim "in every alias case I checked, the quote is present at the alias line" does not hold for B-186. Since 1 of 15 sampled was real, an unsampled real error among the other ~110 alias mispairs is possible; a script that resolves the aliases and re-tests the quote at the alias line would settle it. I did not write or run one (static task).

## Not checked

- Whether each evidence cite proves the audit verdict (only quote presence and meaning at the cited lines).
- The 68 F6-AUDIT fragment rows and the mispair rows outside the sample.
- No file outside this one was changed.
