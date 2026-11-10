# P1d-a plan, pass 4 (round 5 files), resolve (egm:egm-resolve, Opus 5.5 through the Skill tool). Status: resolved. Ticket rev 8.
Inputs: round5-readiness.md (2B/5M/7N), round5-design.md (0B/5M/6N). 25 findings in 10 groups: 25 PROPOSE FIX, 0 CONTEST, 0 ESCALATE, 0 DECLINE. Probe P8 (`handover/evidence/P1d-a/probes-r6/`) ran before the fixes were written. A fresh pass follows (redaction: no cap).

| group | findings | sev | decision written into rev 8 |
|---|---|---|---|
| G1 timing claim wrong | design M1, N8 | Major | Admitted: the P7 sentence "0.17-0.5 s on both" was wrong (probe.out: 0.85 and 0.9 s against 0.29 s). P8 at 262,144 characters: P7 form up to 3.4x slower than base (3.22 s vs 0.96 s). Fix: atomic key run, not slower than base on any probed input. HL1a (65,536 chars, 2.0 s) and HL1b (262,144 chars, under 4.0 s, at most 2 x base + 0.5 s, doubling at most 3.0). |
| G2 N8 / K42d leak | design M3, N9 | Major | Atomic form probed, linear, keeps every P7 row; N8 deleted; K42d-e and K43c-d are fb and assert the secret is hidden; K42a/c assert SV_B absent and `<SECRET_` present. |
| G3 benign over-mask | design M2 | Major | BS-1 shape S8 (25 benign long keys; P8: base 0, new 25); number and DEFAULT to the lead (NEEDS LEAD 1); risk row. |
| G4 BTK1 / N7 | readiness B2, design M4 | Blocker | Probed the card path on base: `https://...` becomes `[link removed]` even in a span; a bare domain stays. BTK1 now the bare domain (base `evil.com`, after `evil[.]com`); BTK2 and MENT1 added; the gate removes mentions inside spans (P8), so N7 is rewritten and NEEDS LEAD 5 closed. |
| G5 one card helper | design M5, N6 | Major | `channel.redact_for_card`; hook renamed `_neutralise_for_redaction`; AST test over every `neutralise=` caller, `cards.py` by symbol; docstring warning on the `defang=True` default; A1, A2, A3, A11, A44 rewritten. |
| G6 alphabet counts | readiness B1 | Blocker | 72 and 66 (list unchanged), counts spelled out. |
| G7 mutants | readiness M3, M4, M5, M6, nit only_test | Major | A13 killer Z1 (Z4 pinned explained); A29 old text; marker comments KRUN-PLAIN, KRUN-QUERY, KLB-QDQ, KLB-QSQ make every `old` one literal; KEYSFX and KW not shared; A59, A60 (time) and A61, A62 (`(?!=)`) new; time mutants killed by HL1a, elapsed time measured after return, runner fields; killer cells without parentheses. 64 mutants by script. |
| G8 order and ledger | readiness M7 | Major | ORDER 230 item 2 governs; PARALLEL-PLAN row A4 corrected; cilint-001 has no ledger row: alias row added OPEN (NEEDS LEAD 6); builder report R9 named (NEEDS LEAD 7). |
| G9 IDF padding | design N7 | Nit | `=(?!=)`; rows Q23, Q23c; shape S7c (710 samples). |
| G10 nits | readiness nits, design N10-N11 | Nit | R3 lines 591-616; imports stated; S7b/S7c in guarantee column; count script named (`count_rows.py`: 98 rows, fb 52, pb 43, ow 3); `test_patterns_kinds`; Leak defined; REAL lines: first run is BS-1. |

## Open for the lead (defaults in the ticket)
1. BS-1 gates incl. S7b, S7c and the S8 over-mask count. DEFAULT accepted as over-mask (ORDER 166 item 2).
6. Ledger alias for cilint-001. DEFAULT: added by the cloud session (done, OPEN).
7. Earlier builder report's two failing properties. DEFAULT: run as written, nothing weakened.
