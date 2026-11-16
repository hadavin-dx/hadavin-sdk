# Checklist revision 9: stranger read (egm-comprehension), condensed copy, 2026-11-16
Read only; nothing run. Not read: plan, patches, acc5.sh, apply-v10 script, evidence-c7g.md. 1 Blocker-group (4 items), 12 Majors, many Nits. CL = LEAD-CHECKLIST-v5.md, FL = LEAD-FILL-list-v5.md, PC = PLAN-CHAIN.md.
## Blocker
1. A2 (CL 38, 209) stops on any CR; remedy "git checkout -- the file" recreates CRs on Git for Windows (core.autocrlf=true); autocrlf only mentioned at C2c (CL 127); acc5.sh never CR-checked; how files reached the laptop is not said.
2. C2c/C8b (CL 129, 167): `dash -n` probably missing in Git Bash; ok=0 silently, no STOP line; C9 unreachable. (Same as adversarial Major 7.)
3. CL 116 WSL path sed expects `C:`; `/c/Users/...` form matches nothing, prints wrong HBW with no error; HB form not fixed (CL 14 says Git Bash form and writes C:/...); a space in the user name breaks unquoted HBW.
4. FL 49 / CL 118: "write the control file" has no command; K3/K4 use relative pastes/P-4b.sh, current folder never stated.
## Major
5. Missing `patch`: A3 prints STOP, E table says restart at A1; only A5 mentions git apply; CHAIN must then be 2 but default is 3.
6. Re-running A3/A4/A5b4 after success prints STOP and tells the lead to discard good work.
7. CHAIN choice has no basis in the checklist (172/174/176 min only in PC); value 3 preset; not rechecked per window.
8. C2 plan lines "2, 136, 251, 536" hold for CHAIN=2 only.
9. "(1), (2), (3)" used for four different things (A9, C2, FL 17, C2b); section 11 heading never named place (4).
10. STOP has two meanings (section 0 definition vs "fix X and run again"; E table a third).
11. C7 STOP names no fixes (four counts, CR, BOM removal command, several 40-hex strings).
12. C4 empty last field / FILE-MISSING ends "tell the builder" with no continuation.
13. C2b step (2) overwrites P-4b.sh on re-run; "saved copy" ambiguous; no place/format for "answer 1 with your text".
14. How to start the runner and reach the builder not stated (tool, session, BRIEF-PREAMBLE path; "fill angle brackets" but none printed; "channel" ambiguous).
15. C5/C6 can ACCEPT after a failed `git show` in W3 (missing worktree only prints a note).
16. D2 fresh start can delete under a live process; two adjacent code blocks pasteable together; "stop and ask" names nobody; depends on open L1.
17. PC 20, 39, 53 write `b0caeb84c5a28a9d` (3x) but real first 16 are `b0caeb84c5a28a94`; PC 5-6, 27 still say two patches. (Chain round 2 changed the final sha to 28f92c5d1211207c: CL 54, 56, 64 still name the old one and say "rc 0 even when edits fail", no longer true.)
## Nits (headline)
Undefined terms: Q18 item 2, proposal 3, R5, RE-PIN step (e), round-5 builder, the tar, take/ctl, p.log, v9/v10, gate rows. "Step" has five meanings. CL 3 says C7 verbatim but C7 is the c7check helper. E table rows do not match printed texts, no rows for A2, A5c, C2c, C7, C8, C10. C8 no expected output, hardcoded take/nlite-int-r5. `<pid>` placeholder fails if pasted. python3 may not exist in Git Bash. `mv W W.old` has no .old2 fallback. Blank line counts as a runner line. C4 "rows filled: 20" counts rows read. A8 mv wipes decisions after edits. "tell me" (FL 46, 48) does not say who.
## Prior v8 findings
Closed: 1, 2 (mostly), 3, 4, 8, 12, 14, many nits. Partly: 5, 6, 7, 9, 10, 11, 13. New: CHAIN gap, v9/v10 names.
## Not understood
What the smoke run tests and why P-4b scans for unreadable n8n; which shell the runner uses (Windows path read, WSL commands run); what "round-5 builder's final message" is and where to get it; what text LEAD-FILL 1/1b should hold and where; what "gate rows" are.
