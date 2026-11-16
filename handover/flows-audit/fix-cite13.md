# fix-cite13
Backups: scratchpad copies of FINDINGS.md and LEDGER-ROWS.md (before edit).
1) FINDINGS line 63: B-136 quote marked shortened, CLAIMS-TABLE wording given in full (verified at CLAIMS-TABLE.md:827).
2) F-013 FINDINGS line 130: 'says that is deliberate' replaced by 'states it as the decided design' (PLAN-4:79 checked: no word deliberate). LEDGER-ROWS F-013 row had no such cite; unchanged.
3) F-028 (both files): added note that L3-20 is a wrong number (720 s vs 750 s), not a stale cross reference (lanes/L3.findings.md:26 checked).
--- python3 tools/count_findings.py
rows 45 unique 45
| Blocker | 5 | 0 | 5 |
| Major | 5 | 0 | 5 |
| Nit | 1 | 34 | 35 |
| all | 11 | 34 | 45 |
sev {'Blocker': 5, 'Major': 5, 'Nit': 35}
exit 0
--- python3 tools/check_refs.py
PASS 5166 references
exit 0
--- python3 tools/check_secrets.py
FAIL 1 hits: flow-check/evidence-f8-r8.md:55 token-like (length 152)
exit 1
