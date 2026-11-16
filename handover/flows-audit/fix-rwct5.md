# fix-rwct5 (fixer, 2026-11-16): RUNSHEET-WORDING.md and CLAIMS-TABLE.md

## Failures and open points first
- The new checker still exits 1: 17 RW paste strings have no CT row to hold them. They are by design (rows that exist only in RUNSHEET-WORDING.md). Not a defect, but the script cannot tell by itself; it lists them.
- Nothing ran in n8n. Static text edits only. Not committed. Backups: scratchpad bak-rwct5/.
- The ONS file (inputs/OWNER-STEPS-realrun-v3.md) and PLAN-4 were read only, not edited. The B-003 rows say what the lead must paste there.
- Not verified: that the lead accepts the long B-003 string inside the PLAN:57 and ONS:131 sentences (grammar fits; wording not reviewed).

## Fixes
1. B-003 split into B-003a (PLAN:9), B-003b (PLAN:57), B-003c (ONS:131), B-003d (ONS:135), each with its own exact old sentence copied from the file (PLAN:9 and :57 and ONS:131, :135 checked by sed). PLAN:184 holds no such sentence (it states the narrow claim), so it has no row; CT rows B-003 (line ref and action) and the broad-sentence note were corrected the same way. Row count 168 -> 171 (section 3: 62 -> 65), text updated.
2. CT line about ONS:131 and :135: ONS file is inputs/OWNER-STEPS-realrun-v3.md; both lines hold the broad sentence, now have rows.
3. check_rw_ct_pairs.py written (tools/), ruff check and format clean. First run: 129 strings, 96 not found. Classification:
   - 18 rows had no CT row at all (RW-only by design): V-11, N-5a, N-5b, N-6, N-9, N-10, N-11b, V-57, P-155, X-5a, X-5b, S5-voice, N-4a, N-4b, N-4c, N-2, S5-a, S5-b. Four of those 18 (N-5b, N-1-type copies) have the same string as a row that does match, so only 17 stay unmatched in the final run.
   - 67 were real mismatches (CT held a shorter paraphrase or an older text; examples B-010, B-042, B-101, A-016b, A-087b, A-040). RW wins: each CT action cell now ends with the RW string word for word, labelled "if the shorter text above differs, this string wins".
   - 2 were contradictions (B-045, B-054: CT said say nothing, RW has a plan-file string): CT now says "nothing in the video; the plan file gets the string".
   - Result after fixes: 132 strings, 115 found, 17 not found (all RW-only by design, listed above).
4. Nits: A-020 line column now R:33, R:41 in both files (R:90 is the A-019 caption; VIDEO-RUNSHEET line 90 holds no A-020 text). CT A-053 action cell now starts with "not pasted". CT A-087 now holds the second replacement string (time cell).

## Outputs
- check_runsheet_paste.py: total rows 171, 80 flagged ids all have rows, RESULT: PASS.
- claims-count.py: verdicts 29/124/51/54/69 = 327, offenders 0, ids 327 unique.
- ruff check: All checks passed; ruff format --check: already formatted.
- check_secrets.py: PASS 0 hits in 1734 files.
