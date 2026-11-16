# fix-rswording8: round 2 fix of RUNSHEET-WORDING.md (2026-11-16)

Checkpoint 20 min (14:13Z = 19:43 IST): file rebuilt by script, gates run. The 40 min box was not used up.

## Done
- One status per row inside the id cell (PASTE, DELETE, HELD, NO PASTE, SUPERSEDED) plus an empty APPROVED field; words defined once at the top; status table generated (PASTE 56, DELETE 30, HELD 81, SUPERSEDED 12, NO PASTE 6; 185 rows).
- Verdict counts fixed to 119/70/62/27/49 = 327 (coordinator finding); old 176-row coverage text replaced.
- 12 SUPERSEDED duplicates, new rows A-016h, A-020b, A-010c, B-172b, B-173b, N-1b, X-6a/b/c, B-150c; B-032, A-005, A-084 etc. HELD.
- Viewer strings: "e-mail message", "table row", no lane3/K3B in viewer text (kept only in note lines P:150/P:153, stated).
- Rejected and relayed strings removed from notes; CUT, NOT USED, REVIEW r1 reworded; IST added after UTC times.
- Q31 items 40-46 appended to QUESTIONS.md.

## Gates (run from handover/flows-audit)
- check_runsheet_paste.py: RESULT: PASS (185 rows; 86 flagged, none without a row; 48 UNTRACED, 41 without row)
- Table separators equal header column count: 0 mismatches (own script).
- ruff check: All checks passed! ruff format --check: 595 files already formatted. check_refs: PASS 5167 references.

## NOT done / not verified (honest gaps)
- Exact-sentence cells copied from memory of sources were NOT re-diffed against every source file. Notably B-037 and B-196 are marked BLOCKED (exact text not read).
- Sections 0b/0c step text, section 4 (RWQ ranges) and the Q ranges were only patched by search-and-replace (CUT/CU(T) wording, lead record, mail), not fully rewritten. Steps 7, 8, 10 may still hold old phrasing such as "mail"; a fresh read is needed.
- Some paste cells still contain "the lead ID/lead table" (valid terms) but one-word-"mail" cleanup in paste cells was regex-based.
- Differences to CLAIMS-TABLE.md are in Q31 items 41-42 (this file wins).
- Nothing ran in n8n; nothing committed.
