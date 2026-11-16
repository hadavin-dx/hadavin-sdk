# plan-v4 round 1 - structural review (condensed, ids kept)

Target: studio-notes/plan-v4-market-aligned.md vs plan-v3.md. Fresh read-only reviewer. 17 findings, no Blocker, 12 Major, 5 Nit. Nothing edited.
File check: every file v4 names exists (plan-v3, review-plan-3, amendments in studio-notes; lead-fetch in evidence/lead; market-scan-1/2 in reviews/, cited by bare name). "Pass 4", "addenda", "scan table", "earlier fact-check batch", PR numbers are not files: UNVERIFIED.
Arithmetic: cost table correct (240/600/8,004 per year from 20/50/667 per month; 3,600 = 30 x 10 x 12; 60-120; 09:55 UTC = 15:25 IST).

- S1 Major, lines 1-3: v4 "changes v3 only where it says so" but has no list of Added/Changed/Unchanged; v3 is FROZEN and changes only by written amendment (amendments.md); v4 cites none. Fix: Delta-to-v3 section; state how v4 becomes binding (record as amendment after review).
- S2 Major, v4 s4 vs v3 s6: package ids differ with no mapping (P1a/b/c vs P1; P4b1/b2 vs P4b; P5b1..P5b5 meanings differ from v3 R1P/R3a/R5; P2d meaning differs; AK-*, P0t, AK0, JG-3 undefined in v3; PRs 63-86 vs v3's 41-56). Risk: "HOLD P5b2/P5b5" applied to the wrong package that P5c depends on. Fix: mapping table.
- S3 Major: v3 allows cutting P5b2-P5b5 only by an amendment that rewrites dependents (P5c Depends-on); v4 HOLD row omits it. Fix: cite the cut rule in s4 and s10.
- S4 Major: rung legend in s4 (1 no-code, 2 our core, 3 existing free tool, 4 free library, 5 new own code, cited as R447/R448) does not match the seven-rung studio ladder (1 core, 2 client tool, 3 no-code ...); s9 labels differently again. Fix: use studio numbering or rename and explain.
- S5 Major, s5 lines 65-66: paragraph directly after the table, no blank line; renders as a malformed table row. Fix: blank line.
- S6 Major, s5 row 1 vs s2: "Cloud Starter/Pro/Business" with "Business is self-hosted only", while s2 lists Cloud Business at EUR 667 / 40K executions and also calls Business a self-hosted plan. Contradiction; which reading is right UNVERIFIED. 8,004 is monthly equivalent billed annually, not stated. Fix: split rows; state billing basis.
- S7 Major: text promises a total next to every unit price; table has no totals row; EUR and USD mixed with no conversion rule.
- S8 Nit: Make marked NOT READ but cells "one-person team only" and "about USD 5-10" carry no marker.
- S9 Major, s4 P4 row vs s10.1: s4 says run T1 before more P4b1; s10.1 defaults T1 to "no" if the owner does not answer; P4b1 fallback not stated. Fix: state the fallback in both (test own meter only, LiteLLM claim UNVERIFIED).
- S10 Major, s7.4: "about 1 day of agent time" contradicts v3 s10 "Estimates: none until S0 exits".
- S11 Major, s1.3 vs s9: owner decision 3 says do not cut anything connecting to n8n/Make, but s9 gives template packs "CUT-TO-CONFIG+GLUE"; verdict terms (FINISH, KEEP BUILT, ADOPT, HOLD, CUT-TO-CONFIG) undefined and inconsistent between s4 and s9.
- S12 Major: s2 "settled" contains NOT PROVEN items; HOLD/convert items appear in s4 Decision and again in s10; no Status column (DECIDED / OWNER-OPEN / LEAD-DEFAULT).
- S13 Major: T3 and T4 appear nowhere in the s7 work order; no owner or package for T1, T3, T4.
- S14 Nit: evidence cells ("scan table 40-60%", "scan 55-70%...", "scan 3-3", "scan pass 3-4") cite no file/section; UNVERIFIED (scans not opened).
- S15 Nit: row "P0t, AK0, JG-3" holds three items with three statuses in one cell.
- S16 Nit: bare names for scans in reviews/; "pass 4", "addenda" not located; "his words condensed" and "client-chooses rule 6" do not name their sources.
- S17 Nit: Activepieces adapters added though owner decision 1 lists only n8n self-hosted, n8n Cloud, Make; diagram fence has no language tag; s9 (rung table) comes after s8 though it is evidence for s4.
Sections are a flat H2 series 1-10, no skipped levels; cross-references resolve except the broken s5 table.
