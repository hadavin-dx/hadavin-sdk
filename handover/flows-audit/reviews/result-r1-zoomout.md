# Result review round 1 - zoom-out lens (agent a7518d3448ebfabf1, Sonnet 5.5, read-only)
Saved by the lead session. Reviewer text condensed; every finding kept. Reviewer could not read patches, check_refs.py or REPORT.md in full.

## Counts agree: FLOWS-AUDIT, FINDINGS (525 of 655, 11 folders, 40 files), CUT-LIST, counts.txt (54+54+4+18=130; 525 older).

## (1) Not covered by CUT-LIST/FINDINGS/EXCEPTIONS (only cited as claim sources)
- 7 top-level notes: n8n-a-cause-1.md, n8n-diag-1.md, n8n-kill-between-steps.md, n8n-owns-vs-desk-owns.md, n8n-published-numbers.md, n8n-skip-on-conflict.md, n8n-vs-desk-kill-compare.md (overlap on kill/skip results; no duplicate or idle verdict).
- N8N-ENV-PROBE.md, N8N-RERUN-1.md, K-SERIES-V4.md, DOUBTFUL-SCENE.md (cited once, F-023).
- n8n-flows/PAGE-STATEMENTS-DRAFT.md and PAGE-STATEMENTS-V4-DRAFT.md: draft copies beside PAGE-STATEMENTS-V4.md; CUT-LIST has 0 hits for DRAFT.
- AUDIT-PAGE-STATEMENTS-V4.md and AUDIT-VIDEO-RUNSHEET.md: earlier audits of the same two files.
- Per-folder docs (V3-README, V4-README, FILM-README, NODE-DIFF-vs-film.txt, V5-NODE-DIFF.txt): CUT-LIST moves folders but never lists these.
- sandbox-scratch-logs/mf*.out idle logs; n8n-mainframe/examples/docker-native-pg-shim.py (L2a-14 says "not part of repo" but sits in it).

## (2) Audit sprawl
- Major: FLOWS-AUDIT.md (1447 lines) pastes lane files in; headers for L1 (166/174), L2a (341/349), L2b-1 (406/439), L2b-2 (703/733) appear twice. About 4 forms of each lane (lanes/*.md, .findings.md, .header.md, checkpoint-*.md, .judge.jsonl); canonical one unclear.
- Major: L3-stores counts paragraph muddled ("NOT IN ORDER TEXT 6" then 11 items). EXCEPTIONS.md names 4 exceptions; L3-stores proposes spend ledger as EXCEPTION, EXCEPTIONS.md says "proposed RETIRED".
- Nit: mf_leads.sql copies: CUT-LIST "three", F-001 and L3 "four" (counting mf.py inline). Pick one number.
- Nit: CUT-LIST n8n-flows row says "docs and scripts text" while CUT-LIST line 2 says no script points at a folder.

## (3) One-database decision
Consistent across FINDINGS, EXCEPTIONS, L3-stores. Gaps:
- Major: n8n's own SQLite is a second database in the take (F-011); decision open.
- Major: portal "RETIRED, none found" but grep did not cover the 7 top-level notes or REPORT.md.
- Major: FIX-PLAN has no step closing the journal naming split (stage.journal vs stage-journal.jsonl, T9/L3-15); F-020 does not mention two names.
- Minor stores missed: dn1.py crash.flag (dn1.py:37,88); desk_proxy.py request log (:9); mf.py mf_result_*.json (:365); run_mf.py smoke_readiness.json (:153); n8n-rerun desk_kill.py.txt/skipd.py.txt rows jsonl; dn1_common.py:49 DELETES everything under DN1_DESK_REPO/data (hardcoded default /tmp/rr/t3exp), not an exception row. L3-stores "Stores found: 13" omits them.

## (4) CUT-LIST safety
- B1 (Blocker candidate): archiving v3/v4 before F-001 loses the only mf_leads.sql with alert columns; n8n-table-screen/README.md:17 and v2 README.md:27 point at "DDL in n8n-flows-v4"; v5 folders ship no SQL. CUT-LIST prose list omits those READMEs, V5-README, FILM-README, mf.py. Order missing.
- B2 (Blocker candidate): "n8n-flows (mf-* four files)" folder also holds N8N-START.md, PAGE-STATEMENTS-V4.md, DESIGN-A-README.md, mf_leads.sql, desk doors: row must say "move only the 4 mf-*.json".
- Major: run_dn1.py listed but its chain (dn1.py, dn1_common.py, desk_proxy.py, build_flows.py, n8n-tests/results/) not; mf.py imports dn1_common.py (hidden coupling).
- Major: missing candidates: the DRAFT statements, 7 notes, sandbox-scratch-logs, per-folder README/NODE-DIFF, docker-native-pg-shim.py. V5-README line 1 names "v3 and v4 folders untouched": no check that take docs avoid archived folders.
- Safe: nothing removes a v5 flow, build_mainframe.py, stage_server.py, crm_stub.py or the smtp catcher.

## (5) Owner's duplicates question not answered in plain words
No short answer section exists. Needed: about 5 sentences (11 old copies = 525 of 655 steps; what to keep; 2 copies of intake form/hook; 3-4 copies of the table definition; desk doors writing the retired store; idle test scripts).
Worst wording: (1) FINDINGS uses unexplained labels (take, Tier B, lease, claim, stand-in, doors, UNVERIFIED, IMPOSSIBLE-NOW, rubric, onError continueRegularOutput, T-test, waitForSubWorkflow; class dead/duplicate undefined). (2) F-001 plain meaning buried. (3) "doors", "desk", "claim" each carry several meanings; KEEP-ONE/EXCEPTION undefined.

## Could not verify
Patch contents, CUT-LIST hit counts against a fresh grep, whether the 7 notes and DRAFT files are real duplicates (not diffed), absent desk repo and take scripts.
