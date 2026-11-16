# fix-citations (static fix of cites only; no verdict or claim wording changed)

## Not done / not clean (first)
- The raw checker /tmp/citecheck/citecheck.py now reports 167 failing quote rows, not 157 (cites 199 -> 244, resolved 244, out of range 0, unresolvable 0). Why: it tests every quote of a row against every cite of that row. The fixes ADD the correct source cite next to the contradicting cite (A-021, A-022, A-055, A-077, B-101, B-111, B-186, B-187, B-192, B-193), so the checker pairs more quotes with the wrong file. Not real errors; I read each corrected line instead (see CITATION-FIXES.md). I did not overwrite CITATION-CHECK.md (rerun output went to the scratchpad).
- Alias script (below) flags 27 of 326 claim rows; I read all 27: 26 are splitter artefacts (quote cut at a slash, bracket, nested quote or elided parenthetical; text present at the alias line). 1 was a real error: B-122 cited START:13 but the quote and the three names are at N8N-START.md:7 and :9-11. Fixed. So 1 of the ~110 unsampled MISPAIR rows was a real cite error.
- Not checked: whether each cite proves the verdict; the 68 F6-AUDIT fragment rows; SCENE-FLOW-MAP.md.

## Done (CLAIMS-TABLE.md, lanes13/claims-A.md, lanes13/claims-B.md, by claim id)
- A-021, A-022, A-077, B-101, B-111: source cites added next to the contradiction cites (quote lines and K3B/K3 lines).
- A-055: n8n-flows-real-v4/mf-recovery.json:26 (also real-v5 :26, real-v4 mf-form.json:97) for 45 s; DESIGN-A-README.md:10 kept for 120 s.
- RV5 (the INSERT line in the notes): n8n-flows-real-v5/mf-form.json:97 added; mf_leads.sql:4 kept for the key.
- A-030: quote marks dropped round could not tell (CLAIMS-TABLE.md row 109; the A-030 rows elsewhere had no quote marks there).
- B-186: OWNS:7-8 -> OWNS:8, :10. B-187: source :44-45 -> :63, :58. B-192: source -> :63 and n8n-flows/mf_leads.sql:4 for the key. B-193: source :47 -> :65 (:47 kept as raw numbers).
- B-122: START:13 -> START:7, :9-11 (found by the alias script).

## Command outputs
- citecheck: {'cites': 244, 'resolved': 244, 'oor': 0, 'qf': 115, 'qn': 167, 'unres': 0} (before: 199 cites, 157 not found).
- column check (own script, header cell count vs every row, 3 files): column offenders 0.
- verdict recount: lanes A+B 327 {SUPPORTED 114, RELAYED-ONLY 69, OVERSTATED 49, UNSUPPORTED 25, UNTRACED 70}; CLAIMS-TABLE 327, same split.
- Scripts: scratchpad apply.py, alias3.py, chk.py (session scratchpad).
