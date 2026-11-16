# REVIEW.md 580-884 round 47b stranger read (egm-comprehension), security path. Saved by flows-audit, condensed; unverified; static. NOT read: 1-579 and 885+. 1 Blocker, 14 Majors, minors. UTC/IST all correct. Commit id lines at 749, 763, 768, 770, 868, 878, 880 (not printed).
B1 Z1 part (4) L596, Z17 L618, Z2 L603: wiped-host and lagging-host start sequence contradicts itself ((4)(a) no previous (B) needed; Z17 needs it; Z2 compares with previous accepted (B); (4)(c) refuses lower counter yet says lagging host is given missing files).
M1 test count stale: L650/L785 "71 in Z block, 110 in all" with Z1 24 tests; Z1 lists 26 (L602); per-item sum 47 + Z1 26 = 73, total 112.
M2 Z2 says process kind not a (B) field yet lists it as LOOSENING; map L640 and Z8 put it inside (B); PROTECT-ONLY undefined (Z1(7) defines ACT, COUNTER-CONFIRMED, STOP-ALWAYS).
M3 L603 "release key alone can already refuse every ACT start" has no cited check; build digest (A) unclassified in Z2 lists (if unclassified every release needs next key, contradicting L625/L649).
M4 Z6 L607 alarm needs signature count/signer not in log entry fields (Z1 part (2) L594).
M5 Z6 "no pilot starts until second log exists (OL-20)" vs Z1(8) two options "accept in writing" / second log; no default; outage limit has no value.
M6 Z11 L612 two defaults (AUDIT PROPOSAL (4) closable on a note vs RECOMMENDED (4),(5),(7) not closable); L678/688 "tables stand".
M7 L679 vs Z13/O: which criteria may be reported "met (advisory, one person)" before criterion (8) exists.
M8 Defaults missing: re-check interval N, Z6 start-entry interval; max run time 24h lead to confirm.
M9 Z1(5) L597 override: nonce issued by same host; replay of captured (nonce, signatures) not addressed on wiped host.
M10 stale names/counts after Z6/Z10: L655 login counts (12/5/16/18), holds vs hold-place/hold-lift, operator vs operator-stop/operator-reset, approver-proof-checker; "script" fix-review40.md is a log.
M11 L653 verifier person answer depends on Decision 27 needing Decision 26; no date for 26; Z16 end of 2026-11-18 UTC.
M12 "Q1" means three things (L617, L653 question (1), L752).
M13 L763 evidence gap: encoding probe not re-run; 25-pass difference "explained" but deselected set not checked (L758).
M14 "checked and correct" claims with no cited check (L592, 604, 608, 784/785); L763 692 vs 707 difference not confirmed.
Minors: L650 re-run rule vacuous; OL-22 vs open question 5 numbering; Z2 "raised" for loosening; Z16 builder-name due today; L711 undated; L712 trigger list omits Decisions 8, 9a/9b, 11, 13, 18, 23; L715 self-reference X-5.1; L717/L730 no due date/default; L721 4 combinations no default; L749 Decision 23b owner and date missing; L767 "5 scratch-tree failures" undefined.
