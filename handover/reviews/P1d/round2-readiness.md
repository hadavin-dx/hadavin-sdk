# P1d plan review round 2: egm-implementation-readiness (Sonnet), condensed by me from the inline report

Verdict: NO, a builder could not implement without open impactful decisions. 2 Blockers, 14 Majors, 6 Nits. Reviewer ran no code, read no source. Round 3 needed (no cap).
Round-1 still open: design-1-5 (textnorm minimum unstated), 1-6 (numbers missing), 1-10 (M6/M10/M17 equivalent, M8 unkillable), IR-1-5, IR-1-9 (H29 passes on base), IR-1-11 (F03/F04/F12/F13/F17), IR-1-15 (5 baseline failures deferred to BS-0), IR-1-17 (M15/M19 killers in design note; M21, M27 vague), IR-1-18 (5 open questions).

BLOCKERS
B1 Refusal behaviour contradicts itself: item 7 `_blocks` fixed card without buttons; item 8 `requests.summary` swaps inputs for "Inputs: not shown..." through the normal path (likely approve buttons); G3/ruling 3 say "not posted". Callers cards.py:59, channel.py:104/111 (notify, post_card), slack_channel.py:197 not decided; item 9 "nothing raises" unlisted. Fix: one table caller | behaviour | buttons yes/no | pinning test.
B2 healing_views and learning pass not specified: no step list, order or closure rule (is squeezed derived from every fixed-point view or source only? is case-folded view also squeezed?); lowercase view cannot match case-sensitive AKIA[A-Z0-9]{16} (H32 needs case-insensitive or upper-cased view; which patterns; what string is kept). Squeezed pass joins words across spaces; default pattern set must be written now (e.g. fixed-width AKIA/ASIA only). Fix: pseudocode for both.
MAJOR
I-1 learning function unnamed/no signature (BN-P1d-3, R5 need it); how seed entries are told apart in Mapping; mapping direction.
I-2 finish(source, shown, mapping) cannot express window rule (known set across windows; extra= hook for P2d-2); N3 vs BN-P1d-5 vs sibling report inconsistent.
I-3 where reused gate code lives (guard/runmap importing private names from approvals/gate = layering inversion/import cycle); M5 ruling and vulture entry depend on it.
I-4 put-back rule only a pointer to designs/lookalike-leak.md s5; quote formula (c, e, scan keys, tally).
I-5 _blocks call arguments (mapping, hook) unspelled; M27 needs input where only joined text holds a known value.
D-1 constants P1D_MAX_VIEWS/WINDOW_CHARS/OVERLAP/MAX_TEXT_CHARS/MIN_KEY_CHARS have no values or decision rule; BS-4 has no pass criterion; overlap both a constant and "derived from patterns"; some patterns have no max width.
D-2 windowing bypassable by padding > overlap above cap; state guarantee ends at cap or withhold above hard max; at 0.21 s/3000 chars budget 6 s runs out ~85,000 chars.
D-3 InputTooLarge: withhold or propagate? X03 vs M25/except line; log `reason=` per case.
D-4 ViewTooShort exact-substring fallback has no min length/boundary: short values withhold any text containing them (new false-withhold source; BS-1 ceiling 0 may be unreachable). Set min/boundary + F rows.
D-5 B-row boundary assumes unstated textnorm minimum; M20/M21 undefined; B originals need mixed case or lower-case rows pass on base.
D-6 no cost/latency numbers (prototype 7-11x slower: 0.03->0.21 s at 3,000 chars; 0.24->2.69 s at 30,000); F11 no number; X01/X02 wall-clock. Give ceiling + machine-independent test.
D-7 H27 expected string left to builder; assert something true both ways (db01.corp span absent).
D-8 H35/unanchored shape only AKIA/ASIA; other \b-anchored kinds same hole (S10); list kinds or justify; add to BS-2.
D-9 open questions still open; write assumed answer + rows that flip; Q3 no decision route: decide or state refused request expires.
D-10 SECRET & change has no regex; say whether , ) > end the value.
M-1 equivalent mutants: squeezed view makes M6 (killers H01-H06) and M10 (H20) equivalent; H28 is real killer for M6/M3; M17 maybe equivalent (put-back also withholds H22/H25). Show per mutant a row where only that step decides or declare equivalent.
M-2 H29 and pb rows H07-H09/H17/H19 pass on base: cannot kill M7/M8; need fail-before row needing the tag view or declare M8 equivalent.
M-3 killers without literals: M15, M19 (design note), M27, M21.
F-1 fixtures: F03, F04, F12, F13, F17 no literal; S no charset/case; H23/H32 need mixed case; X03/W construction recipe; C05 label contradicts input.
P-1 fail-before base contradictory (precondition 1 textnorm on base vs 0dabf1f where missing textnorm = AssertionError); define base as post-P1b main; pin scan_holds error classes at BS-0.
T-1 template fields missing: Rollback (tag pre-P1d, non-revertible, loud-failure test), files list with reasons (tests/test_p1d_*.py, tests/p1d_mutants.py, CHANGELOG, evidence, vulture entry), Done= with CI gates, exact evidence commands (uv run --all-extras --group test ...), BS-1..3 script/corpus/seed.
W-1 card has two literal texts (item 7 vs owner wording); WITHHELD_NOTICE form; log line lacks approval id.
NITS: N-1 precondition 1 importorskip garbled; N-2 "~" line numbers; N-3 no rows for %2E / &#64; encoded e-mail; N-4 BS-5 no decision rule; N-5 H30 raw summary pins defence in depth, say so; N-6 k1b.redaction.sensitive false-positive rows (bypass_cache, pass_through); ruling 5 hard dependency has no enforcing branch/gate named.
