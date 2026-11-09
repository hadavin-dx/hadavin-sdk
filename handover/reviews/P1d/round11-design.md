# P1d rev 11 plan review round 11, design (egm-design, sonnet), behaviour and spec gaps only (ORDER 191)
Verdict: 0 Blockers, 1 Major, 4 Nits. Read-only; ran nothing. textnorm/P1a/P1b claims unverified (not on this branch). runmap.py anchors 438, 441-443, 447-448, 477-478 match; RS-5 "454-473" is about 449-471. Line-join rule works on the covered shapes; rulings 165-168, 180, 188 kept.

MAJOR M1. A prior value planted INSIDE an unknown key defeats learning (P1d-learn "Blanked view", vb replaced by " "; test_line_join_rule_never_hides_an_unknown_key). Call 1 has password=PV so PV is a prior value. Call 2 has AKIA**IOSF + PV + ODNN7EXAMPLE**: sweep masks PV copy, shown text leaks AKIA, IOSF, ODNN7EXAMPLE; blanking PV to a space breaks the key so nothing is learned. Same input with PV known in the same call IS learned. Options: (1) run patterns on two blanked variants (space and empty string); (2) apply the line-join rule to prior values instead of blanking (departs from letter of ORDER 188 (a), needs lead); (3) state as measured limit N11 + row + property case. Property test must include "inside the key".

NITS
- N1. Wrapped-key limit N10 is attacker-controllable (anyone controlling line breaks can pick a first line of 8+ characters after the prefix); CHANGELOG wording understates it. H31 (7-char first line is learned) vs WRAP-AKIA (12 not): say H31 is the ORDER 188 fail-before row or add a pinned "tail is shown" row.
- N2. Residue-withheld document ends with note document_too_large (P1d NOTICE_HANDLING "document" row, X01): misleading; use document_withheld or document the mapping.
- N3. P1d-learn and P1d-gate lack template fields (source of code / not taken, neutral default / alternative, existing core code reused); P1d-learn lacks race/process-tests line; stale "Plan rounds: round 9" in P1d DEFAULT PENDING LEAD (2).
- N4. "p1dl_blank" cache key is frozenset of prior values, rebuilt per call as run map grows; add a "call N" measurement to BS-4L like BS-4.
