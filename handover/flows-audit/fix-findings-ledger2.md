# fix-findings-ledger2 (fixer, 2026-11-16, static)
Edited only FINDINGS.md and LEDGER-ROWS.md. Backups in the scratchpad.
1. FINDINGS.md:99 reworded: "until T19, T20 and T21 pass on the patched copy" (open-question clause removed).
2. LEDGER-ROWS.md:3 area cell "T19/T20 Wed" -> "T19-T21 Wed".
3. LEDGER-ROWS.md:3 F-002 fix cell re-copied from FINDINGS.md:109 fix cell; equality check True (15062 chars both), diff empty.
4. Where cells of F-002, F-003 (already had prefix), F-007, F-008: handover/demo/ added to n8n-flows*, n8n-mainframe paths; all resolve under handover/demo.
5. F-007 problem cell: VIDEO-RUNSHEET.md:36 reworded to what it shows (K3 and K3B are n8n kills, a different fault). F-037: N8N-START.md:13 only says the setting must be false; dn1_common.py:16 sets it.
Tools: count_findings, check_refs, check_names PASS; check_secrets FAIL on flow-check/raw/test-take-check.txt:178 (other agent); ruff format --check: 2 py files would be reformat (not mine).
