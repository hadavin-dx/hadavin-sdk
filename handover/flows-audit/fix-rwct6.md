# fix-rwct6 (fixer, 2026-11-16): RUNSHEET-WORDING.md (RW) and CLAIMS-TABLE.md (CT)

## Failures and open points first
- check_rw_ct_pairs.py still exits 1: 17 RW paste strings have no CT row (RW-only by design, same 17 as in fix-rwct5.md). Not a defect; the script cannot tell by itself.
- Not checked: no run in n8n; the target files (PLAN-4-NLITE-FROM-LEAD.md, RUN-ON-LAPTOP.md in handover/demo/, OWNER-STEPS-realrun-v3.md in inputs/) were read only, not edited. The lead pastes. Not committed. Backups: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-rwct6/ (both files).
- B-045 and B-046: I did not put the second PLAN:79 sentence into B-045's own paste string (the two sentences are not next to each other, one paste string cannot cover both). Instead B-046 is now the second half of the same edit and both rows say "apply together". If the reviewer wants one row, that needs the lead to allow replacing the whole Concurrency paragraph.
- Wording of the new B-003b/d string ("gets the stored state back and is not run a second time") was not reviewed by anyone else.

## Each Major checked against the source first
1. TRUE. ONS:131 (inputs/OWNER-STEPS-realrun-v3.md) holds the whole post sentence; B-003c replaced only the bold clause, B-219 the whole sentence. Fix: B-003c is now NO PASTE and says B-219 owns ONS:131. B-219 old text now has the bold marks exactly as in the file. Order of application no longer matters (four different lines: PLAN:9, PLAN:57, ONS:135, ONS:131).
2. TRUE. RUN-ON-LAPTOP.md:56 (handover/demo/) ends ", or done without exactly 1 CRM row and 1 mail." B-101 old quote now runs to the full stop in RW and CT (also CT summary row 58).
3. TRUE. PLAN:37 is a table row; the cell is "one contact per lead". B-010 old text is now that cell word for word (RW, CT row 46, CT B-010); CT B-010 short text no longer says "three" ("The recording uses different made-up addresses for different leads.").
4. TRUE. The id A-016f sat in B-003a/b/c/d strings. Now no internal id in them. B-003a (PLAN:9) ends at "an empty lead ID is not rejected today." B-003b and B-003d use one short string that fits inside the quote marks of PLAN:57 and ONS:135; the B-003d note shows how the line reads. Same sweep over all quoted paste strings found one more: A-077b said "see A-021"; replaced by the plain wording of A-021 (RW and CT).
5. TRUE. PLAN:79 second sentence (10 concurrent posts, 9 cached, 0 unknown) contradicts the B-045 string. See open point above: B-046 is DELETE with a reason (it said "Covered by B-045", which was false), B-045 and CT B-045/B-046 say apply both in the same pass.

CT strings: B-003 row now holds both RW strings word for word (PLAN:9 string; PLAN:57 and ONS:135 string), B-101, B-010, B-219, A-077b as in RW (RW wins).

## Real outputs (run from handover/flows-audit, after the edits)
python3 -I tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md -> exit 0
  section '1': 46 rows / '2': 19 / '3': 65 / '7': 41; total rows: 171
  claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 80 | with no row here: []
  claim ids marked UNTRACED there: 50 | with no row here: 43 (scope note unchanged)
  RESULT: PASS
python3 claims-count.py CLAIMS-TABLE.md -> exit 0
  verdicts: {'UNSUPPORTED': 29, 'SUPPORTED': 124, 'UNTRACED': 51, 'OVERSTATED': 54, 'RELAYED-ONLY': 69} total 327
  lanes (A, B incl. X): {'A': 97, 'B': 226, 'X': 4}; to-do rows: 87; offenders: 0 []; ids: 327 unique: 327
python3 tools/check_rw_ct_pairs.py RUNSHEET-WORDING.md CLAIMS-TABLE.md -> exit 1 (by design, see above)
  paste strings in RW: 131 | found word for word in CT: 114
  not found in CT: 17 (V-11, N-5a, N-6, N-9, N-10, N-11b, V-57, P-155, X-5a, X-5b, S5-voice, N-4a, N-4b, N-4c, N-2, S5-a, S5-b: all RW-only rows)
  (the count of strings fell 132 -> 131 because B-003c is now NO PASTE; the first run after my edit showed 18 because A-077b was not yet changed in CT; fixed, rerun gives 17)
python3 -I tools/check_secrets.py -> exit 0: PASS 0 hits in 1750 files
python3 tools/check_refs.py -> exit 0: PASS 5147 references
