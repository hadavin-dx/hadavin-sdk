# fix-cite10 (2026-11-16)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-cite10.md. Only QUESTIONS.md edited (24 lines changed). No commit.
## FINDINGS.md cites (read FINDINGS.md myself; each replaced with a row/heading pointer, wording otherwise unchanged)
- :108 F-002, :110 F-007, :114 F-008, :115 F-011, :128 F-013, :111 F-031, :117 F-041, :150 F-044 -> "FINDINGS.md row F-xxx" (every F-id verified present as its own row, e.g. F-002 at line 109, F-007 at 111, F-031 at 112)
- Q4/Q6/Q7/Q8 line 242 cites (:115, :123, :111, :124) -> rows F-011, F-006, F-031, F-023
- Q9 line (:125 :129 :134 :137 :139 :146 :147 :149 :150 :151) -> one row each, ids listed
- Q-answer line (:122 :123 :124) -> rows F-005, F-006, F-023; line 336 (F-002 :108 ...) -> rows
- 'lines 122-125, 129-151' -> 'the FINDINGS.md rows with those numbers'
- FINDINGS.md:89 (BEFORE/AFTER) -> the paragraph 'Counts after ORDER 007 ...' above the counts table (line 88)
- FINDINGS.md:65 (r8 said MATCH, but it is a heading) -> section 'Verdict per part of the build'
## Other bare-line cites (r8 MISMATCH)
- OWNER-STEPS-q16-rows.md :16, 'lines 20 and 227', 'lines 33 and 53' -> entry names (file was rewritten; 'Step D' now defined near line 248, 'A retake' near 51)
- EXCEPTIONS.md:16 -> 'AUDIT TEXT ONLY paste at its top' (phrase is on line 14)
- PLAN-4 line 106 / PLAN-4:106 / PLAN-4-NLITE-FROM-LEAD.md:106 -> 'notice text in item 4 of its list' (line 106 does hold it)
- Q26 item 5: reworded so item 5 is cited only for 'Row 4 comes first'; 30 min stays with Q27 item 6
- take_check.sh:60 (2 places) -> line dropped; the 'saved runs deleted' sentence is NOT in flow-check/take_check.sh; marked UNVERIFIED where it is
## Not changed
- 'ORDERS.md line 132 item 13' is in RUNBOOK.md:204, not QUESTIONS.md (out of my edit scope). ORDERS.md line 132 holds items 1..3 of the Q21 answer; RUNBOOK.md cite needs fixing (item number).
- QUESTIONS.md cites 'ORDERS.md line N' (many), QUEUE.md line 8, CLAIMS-TABLE.md lines: not in r8 MISMATCH list, not rechecked.
## Checks
grep -c 'FINDINGS.md:[0-9]' = 0; L rows 33 before and after; check_secrets rc 0 (PASS 0 hits); check_refs rc 0 (5168 refs); ruff check rc 0; ruff format --check rc 0; check_counts.py PASS 52 files/655 nodes; check_names.py PASS 655 rows.
