# fix-cite12 (fixer; input reviews/citation-r10.md)

Each target was opened and confirmed by me before editing. No cite lives in an owner-busy file (CLAIMS-TABLE, RUNSHEET-WORDING, RUNBOOK, TAKE-CHECKLIST, FIX-PLAN): "owner file busy" = none. Only single-line Edit calls; no whole-file rewrite; no Q31 text touched.

| # | where | before | after | how confirmed |
|---|---|---|---|---|
| 1 | FINDINGS.md F-046 and LEDGER-ROWS.md F-046 | CLAIMS-TABLE.md row B-054 (line 559) | CLAIMS-TABLE.md row B-054 | row B-054 is at line 717 not 559 (grep); id kept, number dropped |
| 2 | QUESTIONS.md item 29 | flow-check/run_all.sh (line 96) | flow-check/run_all.sh (the grep for the text "ACCEPTED: recovery flow not part of the take") | the grep sits at run_all.sh:99; line 96 is a comment |
| 3 | QUESTIONS.md Q300 intro and item 3 | RUNSHEET-WORDING "rule 7" (line cite and "rule 7 forbids them") | CLAIMS-TABLE.md sentence 'the words "normally one" are forbidden' | grep: that sentence is in CLAIMS-TABLE.md; "normally one" not in RUNSHEET-WORDING.md; its rule 7 is the numbers rule |
| 4 | QUESTIONS.md Q318 intro | FINDINGS.md lines 115, 117, 150 | FINDINGS.md rows F-011, F-041 and F-044 | actual lines are 115, 118, 151 |
| 5 | QUESTIONS.md L16 row and V1-V20 row | "values only the lead can give" | "Values only the lead can supply" | heading at OWNER-STEPS-q16-rows.md:305 |
| 6 | QUESTIONS.md item 29 | take_check.sh "the header comment and the recovery-flow check" | "the recovery-flow check, found by the text ..." | phrase is in the check logic, not a header comment |
| 7 | FINDINGS.md row 70 (T15/T18 cite) | RUN-ON-LAPTOP.md:27 | demo/RUN-ON-LAPTOP.md, the line starting "T15 (new)", states this for T15 only and does not name T18 | line 27 names T15 only; grep T18 in demo/RUN-ON-LAPTOP.md = 0 hits |

## Not fixed / uncertain
- Item 7: I made the text honest about T18 but did NOT find where T18's "0 CRM rows" is actually stated. Someone should locate the real source for T18 and cite it.
- I did not re-read the other cites in the report beyond these seven.

## Commands run (output)
- python3 tools/check_refs.py: `PASS 5166 references`
- ruff format --check .: `599 files already formatted`
- python3 -I tools/count_findings.py FINDINGS.md: Blocker 5, Major 5, Nit 35, all 45 (printed, not compared against an expected number by me)
