# Resolve round 17 (builder's own table; the EGM review of the result is for the studio lead)
Sources: review-r16-security.md, review-r16-naive.md, review-r16-evidence.md, evidence-r16-independent/00-TABLE.md. Output: EDITS.md (r17), verify17.py (built by mk-verify17.py from verify16.py plus r17-section.py and r17-plants.py), `v17-check-output.txt` (FAILURES 0; controls 198 caught, 0 missed), `v17-on-r16-output.txt` (FAILURES 98 on round 16).
| Finding | Status | Where | Verified by |
|---|---|---|---|
| Security N1 | OWNER-OPEN (options and sentence written) | ND16, key step A | r17 N1 checks |
| Security minors 1 to 8 | FIXED-UNVERIFIED | key steps C, D, G, E-09, E-62, front matter | r17 F-3, F-8, m4, m7 |
| r16 NOT DONE: E-09 to K-8, E-12 labels, E-37 (4) | FIXED-UNVERIFIED | E-09, E-12, E-37, Appendix K-8 | r17 m4, K-8 moved, F-9 E-37 |
| Naive F-1 to F-9 | FIXED-UNVERIFIED | card, E-16, E-55, D, E, F, G | r17 F-1 to F-9 and controls |
| Naive F-10 | PARTLY (see r17-CHANGES 1.6c) | E-16 | none |
| Naive F-11 to F-15 | FIXED-UNVERIFIED except F-15 internal codes in AGENT-SCOPE rows | R7, front matter | r17 checks |
| Runner (1) B03 to B10 | FIXED-UNVERIFIED | pins and plants | r17pin-B03..B10 |
| Runner (2) 15 missed | FIXED-UNVERIFIED | pins, scans | r17pin-m.., r17abs, r17ord-code, r17dec-code |
| Runner (3) "row E-48" | FIXED-UNVERIFIED | Appendix K intro | r17row-e48 |
| Runner (4) word counts | EXPLAINED for E-48; method fixed | r17-CHANGES 5 | WORDS line |
| L-LEN | NOT MET (lead question) | r17-CHANGES 3 | wc -w 20,436 |
