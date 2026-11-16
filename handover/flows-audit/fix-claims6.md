# fix-claims6: CLAIMS-TABLE.md round 6 (fixer, static edits only, nothing run against n8n, Postgres, HubSpot or a network; 2026-11-16)

Backup before the edit: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-claims6.md. Only CLAIMS-TABLE.md and this log were edited. Not committed.

## Counts (python3 claims-count.py CLAIMS-TABLE.md)
- Before: SUPPORTED 123, RELAYED-ONLY 72, OVERSTATED 55, UNSUPPORTED 29, UNTRACED 48 = 327; lanes A 97, B 226, X 4; to-do rows 87; offenders 0.
- After: SUPPORTED 119, RELAYED-ONLY 70, OVERSTATED 61, UNSUPPORTED 29, UNTRACED 48 = 327; lanes unchanged; to-do rows 87 (sub-rows 25b, 25c, 33b, 33c, 33d are not counted); offenders 0.
- Moves: A-002, A-015, A-049, A-024 SUPPORTED to OVERSTATED; A-019 and B-102 RELAYED-ONLY to OVERSTATED.
- Live rows recounted by script over the note tags: 20 live, 67 out (row 14 is now tagged OUT; the old tag count was 21).
- Every count sentence was updated (lines 10, 44, 82 to 84, 89, 132, 178, 180, lane A block, lane B Part 7).

## Findings
Reader B1 (paste cells mix notes): fixed for rows 1, 2, 3, 5, 7, 8, 11, 14 to 17, 25, 28, 30, 31, 32, 33, 36, 39, 78, 85 to 87. All "same string as", "Voice:", "Title:", "Step text:", "Proposed sentence:", veto and audit sentences moved to the note cell. Row 25 split into 25, 25b, 25c; row 33 into 33, 33b, 33c, 33d. Row 33 internal audit sentence moved to a lead-only remark in the note.
Reader B2 / Facts Major 1 (row 14): row 14 retagged OUT (pending the lead; default keep out), same convention for rows 14 to 17 stated in Start here item 8 and in each row. Honest open point written there: RUNSHEET-WORDING.md lists the delete of R:41 lines 2 to 6 as LIVE, the table says OUT for lines 2 and 3; the lead must settle it.
Reader B3: sentence at line 3 pointing to the column "status (who decides)" of "Status at a glance"; no row approved today; "done" column explained.
Reader Major 1: items 10 to 14 reordered, lead-in and "partly superseded" marks added.
Reader Major 2: label block added at the top (Q numbers, Q-A, Q-B, RWQ-5, RWQ-8, r20 to r22 defined from QUESTIONS.md and ORDERS.md; "adversarial read r2 M4" and "REVIEW r1 item N" marked "undefined: lead to name" except what fix-rwct3.md line 14 states).
Reader Major 3: row 29 "so the lead is done" now "the lead record"; row 30 now uses the B-077 string with "the person who receives the alerts".
Reader Major 4 / Facts Major 4: A-002, A-015, A-049 now OVERSTATED; line 203 corrected (row 7 is a rewrite, not "keep and add").
Reader Major 5: heading and D1 to D3 sentences settled (D1 settled, D2 moot, D3 open with default); line 103, order of work step 1, rows 3, 15, 25, 27, 28 "needs" columns fixed.
Reader Major 6: lease, re-pin, K1 to K3B defined in the first glossary block before first use; "claim" and "table" meanings stated at line 8.
Reader Major 7: row 36 now says what to change (line 14 of DECISION-one-store.md, replace the whole sentence).
Reader Major 8: row 33 shortened, rows 25 and 33 split. Rows 7 and 16 are still long (see not done).
Reader Major 9: lines 83 and 84 fixed; the 18 moved claims are itemised (11 SUPPORTED, 6 OVERSTATED, 1 UNSUPPORTED).
Facts Major 2: key now says RELAYED-ONLY = "SUPPORTED ONLY BY RELAYED NUMBER" and the one-verdict rule.
Facts Major 3: A-019 and A-076 both OVERSTATED first; A-021, A-036, A-042, A-050 write "second verdict, not counted:".
Facts Major 5: A-024 and B-102 made OVERSTATED (A-039 and B-077 already were).
Facts Nit 6, 7, 8 fixed from the sources (n=2 stated only at R:90 and P:156; B-136 says write-ahead file only; A-045 quote is only at R:39).
Q22 item 3 (line 153): superseded text added. Check I made: ORDERS.md line 177 says "one filled flow set ... in every phase" and does not use the word loopback; the NOTE of 14:35Z still names a short loopback re-smoke. I wrote both and left the choice to the lead.
P1 stand-in mail drop: ORDER 037 item 3 drops the stand-in HubSpot swap but does not name P1. P1 uses the stand-in mail program on film-v5 flows. I wrote that P1 applies only to the later video, is not a step of the real-v5 take rehearsal, and that the lead confirms.

## Nits skipped (round 6 rule)
Facts Nit 9 (done anyway by the reorder). Facts Nit 10 (B-195 and row 72 verdict basis wording). Reader minor wording in "Words with two meanings" and the duplicate definitions of claim/window in lines 54 to 75 (kept; they agree).

## Checks (from handover/flows-audit)
python3 -I tools/check_secrets.py rc 1 (FAIL: flow-check/raw/test-take-check.txt:177 token-like, a file I did not edit); python3 tools/check_refs.py rc 0 (PASS 5168 references); ruff check . rc 0; ruff format --check . rc 0 (576 files); claims-count.py rc 0.
Also run, not asked: tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md: FAIL, missing rows in RUNSHEET-WORDING.md for A-015, A-024, A-049, B-102 (new) and A-039 (was already missing).
