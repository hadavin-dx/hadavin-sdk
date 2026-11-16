# F1 review round 1: egm:egm-zoom-out (agent a4ea6ce33ec6be4f8), condensed by flows-audit 2026-11-16
Read lines 1-146, 200-270, 520-612 only; verified no node claims. Content strong; not usable in 5 minutes as it stands.
| id | sev | finding | fix |
|---|---|---|---|
| R1-01 | Blocker | verdict words and where-column abbreviations (R, P, PLAN, ONS, DOUBTFUL, V5, OWNS) not explained at top | 5-line legend above the list; file name plus line in the where column |
| R1-02 | Blocker | pipes inside quoted claims shift columns in B-010, B-011, B-199, B-200 | replace inner pipes with " / " in lane B and the list; recount |
| R1-03 | Blocker | A-019 (final caption, 'measured at lease 45 s: 18 kill runs') missing from the list because verdict starts with SUPPORTED; A-017/A-051/A-081 point to it | filter on any cell containing OVERSTATED or UNSUPPORTED; add A-019 with the F-003 caption |
| R1-04 | Blocker | rows without a literal replacement: A-007, A-017, A-073, A-081, B-032, B-045, B-046, B-037, B-093..095, A-042; A-051 and A-076 too long | one literal string or the word DELETE per row; decisions block at top |
| R1-05 | Major | list in file order, 44 lane B rows irrelevant to the take | two tables: change before the take (by scene/line), and fix when next touched |
| R1-06 | Major | about 25 rows cannot change the take (plan text, prototype, stale notes, public numbers) | move to table 2; keep B-183 and X-4 visible |
| R1-07 | Major | duplicates: A-023/A-075, A-021/A-077, seven columns A-040/041/042/B-085, 'lease plus 25-30 s' A-017/051/073/081/B-032/B-056 | merge clusters, several locations per row |
| R1-08 | Major | A-017/A-051 safe wording gives a relayed number against the lead's 'no number until measured' rule | mark needs lead decision; default wording: delete the number |
| R1-09 | Major | A-030 and A-035 same scene 9 claim, wording not paste-ready (needs rehearsal) | one sentence, 'valid only after rehearsal confirms', say who runs it |
| R1-10 | Major | stale owner steps buried at line 583; steps 4 and 6 hedged though FACTS says all done | move to top 3-line block; treat 4 and 6 as done, do not ask |
| R1-11 | Major | breaks of lead answers buried (Q6 A-001/008/026; Q8 A-040/042/R:88; Q7 no sentence; 17:05Z rows) | 6-line break list at top |
| R1-12..16 | Minor/Nit | script counts noise; A-005 cropping wording; B-010 engineering wording; stale status line; truncated quotes | plain count line; DELETE or shorter; first 8-10 words of quote |
