# v18 security/money review (uncapped path, egm-design, condensed copy), 2026-11-16
Verdict: NOT handover-ready. 0 new Blockers, 6 Majors (+2 readiness Majors), 8 nits. Arithmetic all correct. Ran nothing; take program, flows, model program not in checkout.
## Majors
- M1 R4 (no valid key besides run-<name>) is checked at 5.6 before the older key is cancelled at 6.2: fails by construction. Fix: check R4 after 6.2 and at 7.1; at 5.6 the older key is allowed if the numbers message names it.
- M2 R2 only lets owner cancel keys named exactly run-<name>; a typo (run-dem7) leaves a live key that may not be cancelled. Fix: also allow a key created today after starting section 6 whatever its name.
- M3 key stays on clipboard 6.4 to 6.6 (lead could read it from WSL); `ps`/`pgrep` print command lines (say: any long secret-looking string = R1); R3 step 2 cancelled-word check has no fallback (add "key no longer in list counts as cancelled").
- M4 Lead-side stop after window end not written: lead stops model program only after owner's "model key cancelled". Fix: lead duty to stop model program and deactivate flows at alarm time, never later than 18:29 UTC, independent of owner's word.
- M5 Yes line says worst-case total US$run total but real exposure is whole prepaid balance (US$189); sample shows Credit 189 beside "Highest balance you accept 20" which by R4 means no run. Fix sample (e.g. 200) and say real exposure is the balance.
- M6 R9 charset allows & and spaces; values typed into shell (cd, ls -l, ps -p, pgrep -af) can chain commands. Forbid & ? % ~ for values typed into the shell or require quoted form; scope "values lead sends" to "values you type".
- M7 7.7 "wait until prompt returns, do R3 first" vs R3 "right after end": say "type end, then immediately R3, do not wait".
- M8 Alarm formula omits owner's minutes at "Type y" and setup; put them into the run length or define latest start as time of `cd`.
## Nits
N1 G25 older-key sentence not in yes line; N2 times "on the run date" vs B on 23 Nov; N3 R7 @example.com vs take-prep contact; N4 5.7 grep -F substring (anchor); N5 R9 mixes film rules and charset; N6 say bash (read -rs -p); N7 expected counts must not change after y; N8 8.4 "put back Recall" = setting it had before.
## v17 Blockers: older key deadlock mostly closed (M1 remains); circular formula closed; cancel-before-read closed; failed key save closed; FREEZE after y closed; end override closed; delete by id closed; R9 charset partly; take program deletes not fixed in code (G1 NO, honest).
