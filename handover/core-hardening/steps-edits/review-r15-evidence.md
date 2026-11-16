# EDITS r15 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw output: evidence-r15-runner/ (00-SUMMARY.md, mutations.md, mutate-run.txt, mychk.py, mutate.py, sha-before/after). Recorded, not judged.

## Failures and deviations first
1. verify15.py missed 9 of 60 planted mutations (the runner's own checker caught 60 of 60 but was tuned against the unmodified file, so that is weaker evidence than verify15's 51 of 60). Missed: #15 not-looking wait removed in key step H; #17 typing-rule definition wait removed; #18 E-09 sub-step a scope list shortened; #19 shred `ls -l` check removed; #22 `shred -u` replaced by `rm`; #24 take-folder prefix rule removed; #31 and #32 alarm names swapped; #51 key-shaped string with the sk-ant-api03 pattern (verify15's pattern `sk-[A-Za-z0-9]{20,}` does not match hyphens after `sk-`).
2. verify15.py was not run in place (it writes scratch15/ beside itself); a byte-identical copy ran in a mirror tree; mutation runs used NO_NEG=1; its internal controls ran once: 129 "NEG ... caught", 0 "NOT CAUGHT". The runner's own first runs had false alarms, fixed in its checker, not in EDITS.md.

## Results
- sha256 before/after identical for EDITS.md (274,049 bytes), EDITS.round14.md, verify15.py, 6 inputs.
- verify15.py as is: exit 0, FAILURES 0; 59 rows, 60 OLD texts, 47 Apply-now applied; Hold 12; files OWNER-STEPS 40, AGENT-SCOPE 15, DECISION-one-store 4.
- Runner checker: exit 0, 0 fails; ids unique and in order E-01 to E-61 without 10 and 35; index rows match headers; all 60 OLD blocks occur once at the stated line; 119 UTC = IST pairs all +5:30; 61 weekday/date pairs right; 18:19 = 23:49 and 18:29 = 23:59 never crossed; no 18:04 in any NEW text; every "latest start" is 18:00 UTC = 23:30 IST (so ORDERS L-23NOV 18:04 vs 18:00 is still the lead's confirmation o); no internal codes in OWNER-STEPS NEW text; every "please stop looking" followed by the wait; all 12 Hold rows carry a HOLD G label and gate.
- Apply-now rows applied in order to scratch copies: all 47 OLD texts matched once (scratch line counts 313, 37, 29); inputs unchanged.
- Banned scan 0 of 10; secret-shaped scan 0.

## Not run
Wording or meaning; whether OLD texts are the right things to replace; Hold rows beyond labels; EDITS.round14.md beyond sha; the builder's chk15.py; any program the steps describe.
