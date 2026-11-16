# Independent evidence and citation check of hand-off v13 (record only)
Runner did not build v13. Originals untouched; work on scratch copies. No spend, no push, no live model call. EGM skills cannot be invoked from this agent; the lead runs EGM.

## Mismatches and uncertainty (first)
1. NO-MATCH (minor): `audit/chain.py:140` (other-tracks:142) is described as a hit of the claim-word grep; the line has none of the five words and `src` is outside that grep's scope.
2. Wrong raw-file cite: v13.md:453 cites `raw-pg-b1-v13.txt` for "16 checks, all refused". The 16 are in `raw-pg-real-code-v13.txt` (v13.md:273 cites it correctly). `raw-pg-b1` holds 8 hostile statements only.
3. Builder's "7" for the `llm` import-cycle group is an undercount (omits `llm.common`, `llm.retry`). Independent: 9 today, 10 planned (planned merge gives sizes [10,4,3,3,2,2]). The doc admits the difference.
4. Tests passing a NetworkLLM into `app.build`: 26 `build(llm=)` calls (builder's grep saw 19 lines; multi-line calls missed), 0 pass a NetworkLLM.
5. Present-tense wording over planned names: `max_requests` (v13.md:287); `allow_group_read`, `fileguard.py` (other-tracks:81). Row 45 of the settled list: `injection_check(..., spend="flag")` is a planned keyword; the line today has 3 arguments.
6. Hot-file table: 16 file/PR pairs are named by neither row (mostly the serial spend chain). No cross-track conflict missed.
7. Checker weakness shown by negative control: a range-only cite moved inside the same file is NOT flagged by the program. The 287 range-only cites were checked by my reading line text, not by the program.
8. Named evidence not in the folder yet: `mutants.py`, `reserve_table.py`, `masking_damage.py`, `needed-check/`.
Not run: Postgres 17.10 (only 16.15 installed).

## Checks
| check | exit | result | raw file |
|---|---|---|---|
| class A cites (436 rows) | 0 | all MATCH except items 1, 2, 5 | cites-table.tsv |
| 70 builder ANCHOR-MISS rows | 0 | all 70 read by line text: 70 MATCH (row 45 noted) | anchor-miss-settled.tsv |
| negative control | 0 | broken name-cite flagged; moved range-only cite not flagged | neg-control-cites-table.tsv |
| import cycles live / planned | 0 | 9 / 10 | raw-graph-live-v13.txt, raw-graph-planned-v13.txt |
| builder graph rerun | 0 | reproduced (needs --table) | raw-builder-graph-rerun.txt |
| build(llm=) count | 0 | 26 calls, 0 NetworkLLM | raw-count-build-llm-v13.txt |
| hot files | 0 | see item 6 | raw-hotfiles-v13.txt |
| Postgres 16.15 B1/M1/M3/real-code | 0 | identical; real-code 47 of 47; timings within about 10% | raw-pg-*-indep.txt |
| 14 merge ids, 7 sessions, E0 ids | 0 | confirmed | cites-table.tsv |
| banned-vendor scan (list read at run time, 10 entries) | 0 | 0 hits (both cases) in both docs, this folder, builder folder | raw-banned-scan-v13.txt |
