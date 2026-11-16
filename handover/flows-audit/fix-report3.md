# fix-report3 (REPORT.md fixer, drift-007 tasks; static edits only)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-report3.md
Counts script: python3 -I tools/count_findings.py FINDINGS.md -> rows 45; Blocker 5, Major 5, Nit 35 (rc 0).
1. Added a 'superseded: current counts ...' label line above the old-count sections (REPORT.md lines 82 and 101 now).
2. Reworded each 'not done / not verified / skipped / could not' item: old lines 8, 21, 71, 86 (and bullets 87 to 90), 102, 107, 108, 142. Each now says fixed, cancelled, or an allowed exception with the next step. Line 107 slips were reworded (they were fixed already).
3. Appended the ORDER 037 item 3 stand-in file list at the end of REPORT.md. Still to fix: OWNER-STEPS-q16-rows.md lines 34, 42, 238 (owner-sheet owner); inputs/DECISIONS-2026-11-16.md item 8 and inputs/plan-wp6-resmoke-v5.md (lead).
Checks (from handover/flows-audit): check_secrets rc 0 (0 hits, 1850 files); check_refs rc 0 (5168); ruff check rc 0; ruff format --check rc 0 (566 files).
Not checked: the stand-in classification is from grep lines with context words, not a full read of every file; nothing run in n8n/HubSpot; no commit.
