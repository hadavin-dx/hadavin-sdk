# v19 owner sheet, security/money review (egm, uncapped path; condensed copy), 2026-11-16
Read only; nothing run. Verdict: NOT handover-ready. 1 Blocker (known, unfixed), 6 Majors, 6 Nits.
## Blocker
B1 The take program deletes contacts today (Open 1; Note 0.1; AGENT-SCOPE:20). R5/R7 treat a delete line as a stop, so with current code the owner must type n and no run is possible. "Take never deletes" reaches the owner only via note G1, which he is told not to read. Needs the lead's code fix shown at the final head, or the owner changing decision 2 in writing. Open 26 (no second way) and Open 27 (no lead-side shut-down mechanism) also gate the run.
## Majors
- M-A 6.2 (line 78) says "no valid key besides the keys you know"; R4 (line 27) says no valid key besides run-<run name>, which does not exist yet at 6.2. Fix: 6.2 "no valid key at all"; say what to do with a second old key.
- M-B Nothing but one human stops spending at 18:29 UTC on 23 Nov and slack is zero: check 2 allows cancel-by = window end; G30 has no mechanism; end-date refusal UNVERIFIED; key has no expiry or per-key limit. Fix: cancel-by at least 10 min before window end; no 23 Nov run unless end-date refusal shown at final head; second alarm.
- M-C R3 step 2 accepts "key no longer listed" as cancelled; absence also from pagination, filters, hide-cancelled, failed load. Fix: absence counts only if count dropped by one with filters off, or page shows cancelled. The cancelled word is supplied by the lead who never sees the page (circular).
- M-D Word that ends a FREEZE not named (R8, lines 31/33).
- M-E Sheet understates lead's reach as same Linux user (clipboard, screen, keystrokes via Windows side from WSL); yes line (74) names only reading the key file. Fix: widen yes sentence or say "never" is a promise only.
- M-F AGENT-SCOPE:22 typed worst-case figure prompt: Note :136 calls it stale by decision S9-2, but a decision cannot change code. If the program prompts, R6/R10 force a FREEZE with the key live. Lead must state from code at final head.
## Nits
N-1 R8 charset vs yes line containing $ and <. N-2 cancel-by time has no rule for what happens at that time. N-3 stray app password on screen needs revoking, not key cancel. N-4 close normal-profile model-account tabs before film pause (7.6). N-5 7.2 fingerprints one file; sample label implies whole program. N-6 pgrep -af prints full command lines.
## v18 M1-M8 / N1-N8
M1 closed in intent (adds M-A); M2 closed; M3 partly (clipboard window, weak cancelled-word fallback); M4 partly (no mechanism, zero slack); M5-M7 closed (M6 adds N-1); M8 closed; N1-N8 closed (N2 equality gives zero slack).
## Sound
Shell charset blocks chaining; printf builtin keeps key out of command line; precedence R2/R3 then R1 then R10 consistent; map cross-references match. Arithmetic all recomputed correct.
## Not checked
check-v19.py and v19-CHANGES, v18 stranger review, menus/commands on Windows/WSL/consoles, real take program behaviour (Open 25/28, G18), credit expiry, word count.
