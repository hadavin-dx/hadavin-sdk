# Stand-in sweep r1 (read-only checker, 2026-11-16)

Test applied: ORDER 037 item 3 (ORDERS.md:177): one filled flow set, real trial credential in every phase, no stand-in HubSpot swap. STALE = text saying practice run, re-smoke, T19-T21 or clean-up runs against a stand-in/loopback that answers like HubSpot. Film-only stand-in (scenes 5-11, film-v5), test-harness files, history lines and reviewer-name "stand-in" are NOT STALE.

## STALE and UNSURE table

| file:line | class | owner of file | reason |
|---|---|---|---|
| CLAIMS-TABLE.md:153 | STALE | audit (this lane) | Q22 item 3 says the take lead id was "not in the loopback re-smoke"; under ORDER 037 the re-smoke is the real-HubSpot filled set, no loopback run exists. No SUPERSEDED mark here (QUESTIONS.md:331 has one for the same sentence). |
| QUESTIONS.md:155 | UNSURE | audit | Glossary row "loopback" defines it as a run against local stand-in programs and is marked PARTLY SUPERSEDED, but the old definition stays and the note itself says "whether other services stay local stand-ins is not stated" (lead to confirm). |
| QUESTIONS.md:529 | UNSURE | audit | Old Q26 item 1 quote "loopback re-smoke 3.5-4.5 h" is marked SUPERSEDED for the length only; the "loopback" word is not flagged under ORDER 037 (history line, low risk). |
| CLAIMS-TABLE.md:148 | UNSURE | audit | P1: "rehearsal step 3: laptop agent runs the stand-in drop five times" on the film flows. It is a mail stand-in, not HubSpot, so ORDER 037 may not cover it, but it is a rehearsal run on a second (film) flow set, which conflicts with "one filled flow set" if it is still planned. Lead to say. |
| ID-VID-CHECK.md:40 | UNSURE | audit | "T18 covers this on the stand-in only, not run": T18 is an old stand-in test; FINDINGS.md:31 calls T17/T18 history, but this row does not say what proves the case on the real-trial flows (T19-T21). |
| CITATION-CHECK.md:243 | UNSURE | audit (tool-made list) | Quotes PLAN-4-NLITE-FROM-LEAD.md:122 "T17 (stand-in CRM answers with only id...)"; it is a citation of a source file outside this folder that may itself be stale, not the audit's own claim. |
| ORDERS.md:95 (lead's, report only) | STALE | lead | Item (8) "no real-account smoke beyond the loopback re-smoke plus one made-up lead" and item (12) "first laptop rehearsal after the loopback re-smoke". |
| ORDERS.md:147 (lead's, report only) | STALE | lead | "then loopback re-smoke 3.5-4.5 h"; already superseded by ORDER at :160 on length, and by ORDER 037 on "loopback". |
| ORDERS.md:160 (lead's, report only) | STALE | lead | "short loopback re-smoke ... about 1 hour"; wording now wrong under ORDER 037 (re-smoke uses real trial credential). |

## NOT STALE (all other hits, grouped)

- FINDINGS.md:18 (definition of stand-in), :31 (already says T17/T18/M0/M1/K1 on old stand-in flows are history and names ORDER 037), :35, :120 (45 s figure measured on stand-in film-v4: history, number cut), :124/:125/:145 (F-005, F-006, F-033: film-only stand-in CRM), :130 (F-013: stage service stand-in, not HubSpot), :148 (F-036 "loopback" = network bind, not a run), :109 two long hits (curl test against a made-up stand-in webhook server on 2026-11-16: a dated tooling test, not a plan for the practice run).
- LEDGER-ROWS.md:3 (same two test-tool hits as FINDINGS:109), :6, :22, :38, :41 (same as FINDINGS rows).
- EXCEPTIONS.md:4, :11, :19 (test-only stand-in files retired from the take); CUT-LIST.md:12, :31 (file names); F6-AUDIT.md:40 (T-HANG stage stand-in sleeps: a test design).
- F6B-AUDIT.md:9, :23, :25, :47, :81, :101 (film set scenes 5-11 and the two-recovery-flows risk, all film-only; the cut-from-video notes are present).
- ID-VID-CHECK.md:24 (film CrmUpsert "proves nothing about real HubSpot"), :26 (mf.py harness), :63 (scene 5 film).
- CITATION-CHECK.md: all other hits (:40, :66, :88-90, :178, :198-199, :219, :254, :272-281, :321, :362, :367) are quotations of source lines or file names; "loopback" at :198, :362, :367 is network binding or the film-flow address, not a run.
- FLOWS-AUDIT.md: all 32 hits (:66, :76, :82-96, :169, :309-311, :405, :683, :917, :975-1022, :1242, :1294, :1335-1382, :1398, :1417-1419, :1434, :1450). It is the static 2026-11-16 reading of the files; stand-in text describes film flows or test harness files; :1417 already says "the real take uses HubSpot". One soft spot, :1434 T4 "... and the stand-in's crm.log.jsonl" names the stand-in log as a place the CRM id appears: fine for film, not for the take (low; folded in, not flagged).
- ORDERS.md (lead's): :58 (Q6 film scene 5 wording), :12/:84/:132/:144 matched on the substring "stand" only (false hits), :173-177 (ORDER 037 itself).
- QUESTIONS.md: :61, :128, :319, :516 substring false hits; :104, :245, :253 (film-v5 stand-in scenes 5-11, not in video); :175, :224-226 (ORDER 037 handling); :331, :378 (already marked PARTLY SUPERSEDED); :361, :451, :463 (the word "stand in" meaning a person standing in as reviewer; "stand-in word list" for reviewer names).
- flow-check/README.md:32, :36, :49, :78, :82, :89, :92 (reviewer-name stand-in pin, name-word lists, Python version test stand-in; nothing about HubSpot).
- CLAIMS-TABLE.md: :18, :36, :61, :124, :127, :142, :159, :207, :226, :279, :329-347, :354-355, :365-403, :427-436, :459, :531-546, :596-601, :677, :697, :731, :773, :800-820: film scenes 5-11 captions, V7 history on v3 flows, harness files, or Q6 wording rules. :88, :109, :166, :48, :847 substring false hits (standing yes).
- STATUS-BOARD.md and PLAN-005.md: 0 hits.

## What I did not check

- RUNBOOK.md, TAKE-CHECKLIST.md, FIX-PLAN.md (skipped by order).
- .sh and .py files (fill_flows/*, flow-check/take_check.sh, run_all.sh, test_*.sh, tools/scratch/edit_findings.py list hits only; flow-check/README.md checked, scripts not read). Other .md files in flows-audit not on the list (REPORT.md, LESSONS.md, QUEUE.md, PLAN-002.md, STATUS-007.md, RUNSHEET-WORDING.md, SCENE-FLOW-MAP.md, OWNER-STEPS-q16-rows.md, checkpoint/fix-*.md and others) not swept.
- Long hit lines were read through a 110-300 character window around each keyword, not whole lines; a stale sentence elsewhere in the same long table row could be missed.
- RUNBOOK v4 (outside this checkout) not read; the ORDER 037 text was taken from ORDERS.md:177 only.
- Nothing edited outside this report.
