# C6f round 2 final check (egm design, blockers/majors only), condensed copy, 2026-11-16
Verdict: c6f fixes both Blockers and most Majors of the c6e round 2 reviews; follows the 11 decisions. Preface fixes were already applied in the body (stale preface now removed by lead).
Majors (all applied by lead in REPORT-c6f.md after this review):
1. film-v5 plan lines: grep finds 120, 236, 284, 298, 543 (not 126 by name); G-1 would pass with film-v5 left at 120/236/284. -> cites corrected.
2. Q7 default conflicted with decisions 2/8 (7 live calls, create+delete). -> default changed: step 0 is the ONE lead only if one create and no delete, else lead answers Q7 first.
3. Q9 default "yes" brought back the cut caption number. -> default now NO time caption until lead accepts.
4. D5a/D5b S9-5/S9-12/S9-3 not checked in v9; G-14 stays open (honest, acceptable).
5. Gate list of 15 has unknown items (F-003 patch G-8, G5, ROLE1); Q1-dependent rows cannot proceed on defaults.
Not checked: run sheet, page statements, mf.py, lane3 harness, real-v5 JSON, n8n_start.sh, Q15 text (only Q14 read), lane3 numbers, banned count (lead ran count earlier: 0), time window 12:30 to 06:30 UTC looks derived.
