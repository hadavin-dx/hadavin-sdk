# Drift report (egm:egm-drift-report), 2026-11-16, run by the lead in the main session
Scope: the audit documents against each other and against the sources in handover/demo, after result review round 2 (head after commit 40162b6 plus the fixes listed below). Commands: a python script comparing FINDINGS.md and LEDGER-ROWS.md severities, grep of counts and F-ids across documents, grep of dn1_common and 60.1 across documents. Output was read by me; not saved as a separate raw file.

## FINDINGS.md vs LEDGER-ROWS.md
- No drift: 34 ids on both sides, severities identical (2 Blocker, 23 Major, 9 Nit) after round 2.

## FINDINGS.md short answer
- Drift found and fixed: item 3 said "F-001, the one Blocker" while F-002 became a Blocker in round 2. Now reads "F-001, one of two Blockers; the other is F-002".
- Header and counts line now agree (34 = 2 + 23 + 9).

## FIX-PLAN.md vs FINDINGS.md
- Every F-id in FIX-PLAN exists in FINDINGS. Nine findings are not named one by one (F-014 to F-017, F-021, F-022, F-025 to F-027) but are covered by the ranges "F-012 to F-018", "F-019 to F-023", "F-024 to F-028"; no drift.

## CUT-LIST.md vs FINDINGS.md F-034 vs mf.py
- Aligned after round 2: all three say dn1_common.py stays (mf.py:8 imports it) and F-034 is fixed by a path guard.

## FLOWS-AUDIT.md and lanes/L3-stores.md
- FLOWS-AUDIT.md still holds the older text of the lane reports (L3-stores copy, line 1463: the destructive path); consistent with F-034. The L3 copies state facts, not actions, so the round 2 wording changes (cut list, F-013) need no change there.

## lanes/L3-claims.md
- S26 and S52 quote the ORIGINAL VIDEO-RUNSHEET.md captions (pre-patch, "18 kill runs, 60.1 to 61.9 s"). They are source quotes, so they correctly differ from the patched caption in patches/F-003. Not drift.

## Not checked
- Whether the per-node tables in FLOWS-AUDIT.md section 3 match the sources beyond the counts checked by tools/check_counts.py and check_names.py.
- Anything needing n8n runtime, HubSpot, the desk repository or the lane3 raw files (UNVERIFIED in FINDINGS).
- ledger_check (`egm\tools\ledger_check.py`) does not exist in this cloud repository; LEDGER-ROWS.md rows are all OPEN (not FIXED-VERIFIED) because the patches are proposals the lead applies on the laptop.
