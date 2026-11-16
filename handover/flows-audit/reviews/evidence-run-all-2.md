# Evidence run: run_all.sh plain, strict, check_secrets (EVIDENCE RUNNER, no judgement)

- HEAD at start (first check): b5e6549836c7921814fdd577c3cd712a614ceb6b
- git status --short handover/flows-audit/flow-check at start: empty
- pgrep -af run_all.sh at start: none (rc=1). No wait needed.
- HEAD just before the chain started: 1f7261bcd39572401db187dc2d1843cdddc7ee40
- HEAD at end of chain: 368ab2b0c68c18e21cdb4c148388f0d0286fec66; HEAD now: 8a3043a5d70445b5ac0274c1394b96abbb8279ef
- CHANGED during the run: HEAD moved (other sessions committed) and the flow-check file hash changed. git status at end shows modified: raw/nested-take-failure.txt, raw/nested-take-failure-b.txt, raw/nested-take-failure-c.txt (these are written by run_all.sh itself).
- Note: the plain run took longer than the 120 s tool limit and ran in the background; a 'REFUSED: another run_all.sh holds the lock' line in the strict output comes from a nested test inside the run (see its text), not from a separate run.

## bash handover/flows-audit/flow-check/run_all.sh
exit code: 1
lines: 55
```
applied [MASKED]
applied F-008-save-runs-for-the-take
checker runs wall time: 0 s; self-test wall time: 7 s
==== real-v5 (THE TAKE) ====
---- default mode must be exit 0; strict mode shows what the owner's two open decisions would do ----
[pristine]
######## pristine real
RESULT: 0 FAIL, 23 WARN
Known open problems: 17
exit=0
[patched]
######## patched real
RESULT: 0 FAIL, 22 WARN
Known open problems: 16
exit=0
[pristine-strict]
######## pristine-strict real
RESULT: 4 FAIL, 19 WARN
Known open problems: 13
exit=1
[patched-strict]
######## patched-strict real
RESULT: 4 FAIL, 18 WARN
Known open problems: 12
exit=1
[pristine-no-baseline] (information only: no excuse for the 2 IF gaps; exit 1 with 2 FAIL is expected)
RESULT: 2 FAIL, 23 WARN
exit=1
==== film-v5 (NOT FOR THE TAKE; shown only, not gating, not added to the real-v5 numbers) ====
[pristine-film]
######## pristine film
RESULT: 0 FAIL, 21 WARN
Known open problems: 15
exit=0
[patched-film]
######## patched film
RESULT: 0 FAIL, 20 WARN
Known open problems: 14
exit=0
[pristine-strict-film]
######## pristine-strict film
RESULT: 4 FAIL, 17 WARN
Known open problems: 11
exit=1
[patched-strict-film]
######## patched-strict film
RESULT: 4 FAIL, 16 WARN
Known open problems: 10
exit=1
[selftest exit=0] SELFTEST: 682 as expected, 0 not as expected, 62 skipped (not applicable)
[take_check.sh exit=5] missing lines: [test_take_check.sh exit 2 (see raw/test-take-check.txt)]
run_all exit status (real-v5 default runs + self-test): 1
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line (hidden characters removed, cut at 300): 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: 
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check
```

## bash handover/flows-audit/flow-check/run_all.sh --strict
exit code: 1
lines: 2
```
applied [MASKED]
applied F-008-save-runs-for-the-take
```

## python3 handover/flows-audit/tools/check_secrets.py
exit code: 1
lines: 1
```
FAIL 1 hits: flow-check/raw/test-take-check.txt:178 token-like (length 47)
```
