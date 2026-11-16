# P1d plan review round 4: zoom-out (condensed by the lead session)
Verdict: 0 Blocker, 5 Major, 7 Nit. Rulings 165/166/167 not reopened.
Major
- M-1 pipeline step b2 (noise deletion before fold) duplicates d; cut b2 (v0,a,b1,c,d). Make d conditional on H37 finding a non-AKIA kind. Affects M5, M6, PIPELINE_VIEWS.
- M-2 fast path is premature: only V9 scratch evidence. Build straight pipeline; add fast path only if BS-4 shows p95 > REDACT_BUDGET_S/4. Else delete line 115, the line-146 bullet, M20.
- M-3 residue test runs undo(shown) as a second form; no row or mutant needs it (undo is already step a). Keep only if a named row needs it; write the M11-style decision rule in BS-0.
- M-4 learning pass runs the full pattern table on every deleting view (main cost). Measure: learn on {a,last} or last+v0; keep a view only if a row fails without it. Add to BS-0/BS-2.
- M-5 two mechanisms for "not approvable" may contradict: requests.summary stores fallback line, approve re-check runs on stored summary, so it would pass. State which text is stored; BS-0(d) decides; M21/H40 depend on it. If fallback line is stored, display_withheld field is simpler.
Nit
- N-1 "only two new constants" wording is wrong (PIPELINE_VIEWS, WITHHELD_NOTICE, P1D_APPLIED, texts); drop PIPELINE_VIEWS assert; P1D_MIN_KEY_CHARS may be dead if TN_MIN>=8.
- N-2 pseudocode carries regex/char-class detail; state source, move classes to fixtures.
- N-3 _learn_unknown returns dict in pseudocode, set[str] in interface; align.
- N-4 keep gate._defang private; only sanitise_text(defang=) public.
- N-5 card text and fallback line overlap; consider one wording.
- N-6 evidence.grounded row: pin test only; say the single changed line per file for judge/bedrock/evals.
- N-7 recount mutants after cuts; M24/M25 are row assertions.
Not flagged: rung table, A1/A8 triggers, S11/S16/S6 scope, defang move and & stop-set.
