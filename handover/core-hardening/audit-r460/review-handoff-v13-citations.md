# Hand-off v13 citation check (EVIDENCE RUNNER, condensed copy of the report), 2026-11-16
Folder of raw output: audit-r460/evidence-handoff-v13-independent/ (00-SUMMARY.md, cites-table.tsv, anchor-miss-settled.tsv). Originals not edited. Not run: Postgres 17.10 (only 16.15 installed; CI uses 17.10); EGM skills.

## Failures and uncertainty first
1. NO-MATCH (minor): audit/chain.py:140 (other-tracks:142) is described as a claim-word grep hit; the line holds none of the five words and src is outside that grep.
2. Wrong raw-file cite: v13.md:453 cites raw-pg-b1-v13.txt for "16 checks, all refused"; the 16 are in raw-pg-real-code-v13.txt (v13.md:273 is right). raw-pg-b1 holds 8 hostile statements only.
3. The builder's "7" for the llm import-cycle group is an undercount (omits llm.common, llm.retry): 9 today, 10 planned (group sizes [10,4,3,3,2,2]).
4. Tests passing a NetworkLLM into app.build: 26 build(llm=) calls, 0 pass a NetworkLLM (builder's grep saw 19, missing multi-line calls).
5. Present-tense wording over planned or non-existing names: max_requests (v13.md:287); allow_group_read and fileguard.py (other-tracks:81); injection_check(..., spend="flag") (v13.md:243; the line has 3 arguments today).
6. Hot-file table: 16 file/PR pairs named by neither row, mostly the serial spend chain; no cross-track conflict missed.
7. Checker weakness: a broken name cite is flagged, but a range-only cite moved to another line in the same file is not; the 287 range-only cites were verified by reading, not by the program.
8. Evidence files the doc names that are not in the folder: mutants.py, reserve_table.py, masking_damage.py, needed-check/.

## Results
Class A cites 436 rows: all MATCH except items 1, 2, 5. 70 builder ANCHOR-MISS rows settled by reading (70 MATCH, row 45 planned keyword). Negative control: broken name cite flagged, moved range-only cite not. Import cycles 9 live, 10 planned. Postgres 16.15 B1, M1, M3, real-code: identical results, real-code 47 of 47 passing, timing within about 10% (+0.25 to +0.30 ms per lowering vs the doc's +0.28). 14 merge ids, 7 sessions, E0 ids, counts of .chat( and Limits( confirmed. Banned-vendor scan 0 hits.
