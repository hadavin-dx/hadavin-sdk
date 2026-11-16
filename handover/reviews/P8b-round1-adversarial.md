# P8b round 1, adversarial review (ticket rev 1, 110 lines, 0d04aa3) - agent a6f6ff0598b04f87c
Status: REPORTED (saved by the lead from the hand-back, condensed; model output, not user authority). Worktree not a git repo: 124258b and origin/main content unchecked; the awk script read by hand, not run.
Verdict: not buildable as written: 4 Blocker, 7 Major (ADV-5..11), 6 Minor, 2 Nit.
| id | sev | lines | problem | fix |
|---|---|---|---|---|
| R1-ADV-1 | Blocker | 71,88 | awk row filter /^\| *[A-Z][A-Z]-/ skips ids with a digit or 3 letters (live R2-P5a-ADV-1 Blocker OPEN is skipped) -> exit 0 with an open Blocker. | Match every table row except header/separator; unparseable id = BAD-LAYOUT; fault P12 (R2-PX-1 OPEN row must exit 1). |
| R1-ADV-2 | Blocker | 71-86 | awk exits 0 on zero rows (wrong/empty file). | END: rows==0 -> exit 1; fault P13. |
| R1-ADV-3 | Blocker | 92,17,42 | Drift scope unbounded: whole root README + every frozen ticket; fixes must go in docs PR to core main but handover/ is on the cloud branch; frozen tickets not editable; root README not in Files list; "change nothing in src/" blocks docstring fixes. | Scope to docs/kinds/ plus root README.md line 31 (redaction paragraph); tickets are inputs only, ticket-vs-code differences one line in drift.md, never pass-blocking; add root README to change list. |
| R1-ADV-4 | Blocker | 100,16,96,107 | Done unreachable by P8b alone (hundreds of unresolved rows; BS rows now 1450-1487 = 38 not 25, plus 7 R2 5-col rows); closing work has no owner; counts not reproducible. | Hard dependency: every BLOCKER/MAJOR row FIXED-VERIFIED/WAIVED/OWNER-ONLY/IMPOSSIBLE-NOW before P8b starts; name who closes (lead per package at result review); drop fixed counts or label as of 124258b UNVERIFIED; lead normalises 5-col rows now. |
| R1-ADV-5 | Major | 25-26,21 | Source of "default" unstated; table.py:582-589 DEFAULTS (secrets=fake, signer=none, anchor=none, store=memory, detector=regex, channel=fake); glossary says store default Postgres; a default can itself be DEV_ONLY/NOT_PROD. | Cite DEFAULTS; define default/recommended production/alternative/dev only/not prod; fault: page naming Postgres as config default must be flagged. |
| R1-ADV-6 | Major | 21,110 | "redactor vs detector same?" is answerable from code (table.py:543-557 detector = regex/llm_judge/bedrock_guardrail; guard/__init__ exports redact). | Settle in ticket. |
| R1-ADV-7 | Major | 91,41,59 | T1 cannot catch a new TABLE key (expected.txt hand-made, not evidence); grep may match other 4-space dicts. | comm of TABLE keys vs ls docs/kinds; name expected.txt evidence; fault P14 (fake 9th key). |
| R1-ADV-8 | Major | 40,47-61 | "each check has a planted-fault row" false: T3 and redactor-wording check have none; P10 relies on an LLM skill. | P15 (redactor.md claims look-alike copies of 8-11 char secrets caught) + laptop-tool fault, or drop claim. |
| R1-ADV-9 | Major | 62-93,40 | Step order self-contradictory (faults first vs last; steps 2-3 vs 6; normalisation first vs "now"). | One numbered run order: commit id; P1-P8 awk; build docs; P9-P11 on copies; steps 4-5; drift; fix; ledger checks last. |
| R1-ADV-10 | Major | 63,66 | Commit line first in evidence file overwritten by `>` redirect. | Write commit line first, then >> everywhere. |
| R1-ADV-11 | Major | 89-90,41 | WAIVED criterion (artifact cell names waiver id) checked by nothing. | awk checks field 7 non-empty with waiver-id pattern; fault. |
| R1-ADV-12 | Minor | 16,110 | P8a ticket now exists (db09637). | Read and cite. |
| R1-ADV-13 | Minor | 16,33 | Stale ids (P1 split P1m/P1a/P1b; P6b split P6b1/P6b2). | Update. |
| R1-ADV-14 | Minor | 90,32-35 | Section 9 path check scope unclear; tests/warden_port name scan. | List exact paths; flag warden_port cite. |
| R1-ADV-15 | Minor | 64 | Lead and cloud both edit ledger.md -> merge conflict. | Cloud normalises its own BS/R2 rows to 7 columns now. |
| R1-ADV-16 | Minor | 89 | Laptop ledger_check 9 columns vs cloud 7; no check mapped count equals cloud count. | Add equality check or explain. |
| R1-ADV-17 | Minor | 17,39 | Jargon (memo 6, plan-v3, BS-*). | Explain on first use. |
| R1-ADV-18 | Nit | 25 | Per-row "not yet run live" tag adds nothing. | Once per page. |
| R1-ADV-19 | Nit | 73-75 | printf prints NR line number. | Print id. |
Verified: 17 fields; table.py/config.py/executor.py/contract.py/pyproject cites; plan-v3 and order cites; 585+142=727; 15 pages +index=16; 7-col line 3 and 5-col BS rows; awk behaviours as designed (P2-P8).
Not checked: 124258b/origin/main; ledger counts as of 124258b; ledger_check/ledger_lint/P0d waiver format; drift-report skill on P10; public-repo scan list; uv_build non-Python files; memo 6; mawk vs gawk (not run).
