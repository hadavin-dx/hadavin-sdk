# P1d-a plan review round 3 (2nd EGM pass on rev 5), resolve (egm:egm-resolve, Opus 5.5 through the Skill tool)
Status: resolved. Target: handover/tickets/P1d-a.md rev 5 -> rev 6. Inputs: round3-readiness.md (0B/5M/5N), round3-design.md (0B/5M/8N). 23 findings, merged into 12 groups. Result: 23 PROPOSE FIX (all applied in rev 6), 0 CONTEST, 0 ESCALATE to the owner, 0 DECLINE. Four lead questions keep a DEFAULT written into the ticket (ORDER 193). Redaction path, no round cap: a fresh plan pass follows rev 6.

| group | findings merged | sev | decision written into rev 6 |
|---|---|---|---|
| G1 two redactor leaks | R-M4 (INFO-K41 password leak), NEEDS LEAD 4 | Major | FIX IN THIS TICKET. New row K41 (fb, card and model): `"a"*41 + "password=hunter22 x"` masks the value; the builder replaces the plain entry's key-length bound with one a long prefix cannot defeat; BS-0 must show the base leak (STOP if it does not). A15 gets killer K41, so no expected survivor (49 mutants, all with a killer). |
| G2 named entities in BS-1 | R-M1 | Major | S5x expected string by the rule "a named entity `&name;` that `html.unescape` changes is read as one character of the value"; hidden 0 stays exact where the sample has no entity; where it has one the gate is the same rule, and an OVERMASK ceiling is stated: at most the entity length, counted per shape, reported not gated beyond it. |
| G3 base and order conflict | R-M2, D-M5 | Major | Rebase protocol: base moves when A7 (P1b final head) is stable; the build waits for it; BS-0 is re-run in full on the new base (all fixtures regenerated); the three-line order "P1b, P1d-a, P1d" of the ticket Depends line is the one rule. |
| G4 T1 selector | R-M3 | Major | T1 asserts `defang_text(second return)` only when `hasattr(gate, "defang_text")`; otherwise the base form (so T1 stays pb). |
| G5 build phases | R-M5 | Major | Four ordered phases, each ends with the named test set green: (1) redactor split; (2) gate flag, `defang_text`, `undefang_text`; (3) channel and Slack wiring; (4) mutants then BS-1. |
| G6 choke point | D-M2 | Major | Link safety lives at one place: `gate.finalise(text)` is NOT added (it would be a new public name); instead an AST test `test_every_card_exit_wraps_defang_text` fails if a function that returns card text in `channel.py` or `slack_channel.py` does not end in a `defang_text` call; mutant A44 removes one wrap. |
| G7 differential claim | D-M3 | Major | G-TXT differential compares against a frozen base `clean(x)` (fixture `p1d_a_gate_base.json` holds the outputs); claim reduced to "only more withholding". |
| G8 fixtures with fake credentials | D-M4 | Major | Fixtures built from parts; local gitleaks and semgrep run on the diff before the pull request; result in the evidence file. |
| G9 Alternatives and Risks | D-M1 | Major | Two new tables: Alternatives considered (undefang inside `_neutralise`; a `finalise` step; `parse_qsl`) with reasons; Risks (8 rows). Rung-4 claim "does not run inside our run map" was UNVERIFIED: wording changed to "not evaluated; reasoned only". |
| G10 nits on audit items | D-N1..N4 | Nit | Single-dependency line (no vendor, stdlib `html` only); least-privilege line (Postgres trust is local only); `#` fragment row noted as non-goal N6; BS-1 alphabet exclusions stated with their reason. |
| G11 housekeeping | D-N5..N8, R-N3..N5 | Nit | Undefang before the size check noted; model line per ORDER 232; hours restated; CHANGELOG comma rule; prototype D1/D3 for one hour before the build (BS-0 step 0); A27/A31 indentation fixed in the mutant table text; sketch wording. |
| G12 other `clean()` callers | R-N1, R-N2 | Nit | BS-0 grep terms extended with `clean(`, `display_hash`, `requests.py`, `cards.py`, notify; NEW_SURFACE helper rule (one helper in the corpus tool returns the missing-name marker). |

## Open questions for the lead (all have a DEFAULT; the build does not wait)
1. BS-1 gates (NEEDS LEAD 1): DEFAULT as proposed; no pull request until answered.
2. Wide-dot hosts: DEFAULT a ledger row for P1d.
3. Stored-card `[.]` read as `.`: DEFAULT yes, as written.
4. K41: DEFAULT fixed here (G1).
