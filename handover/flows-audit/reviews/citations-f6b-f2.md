# Citation check: F6B-AUDIT.md and reviews-of-core-patches/REVIEW.md

Checker: citation checker (static, read-only). Date 2026-11-16. Nothing run except two Python one-liners (Decimal arithmetic; pydantic Route validation) and `patch --dry-run` / a patched COPY of src+tests in the scratchpad. No repo file other than this report was written. Not committed.

## Source situation (read first)
- F6B-AUDIT.md sources (`handover/demo/n8n-mainframe/`, `n8n-flows-*-v5/`, `SCENE-FLOW-MAP.md`, `FINDINGS.md`, `PLAN-002.md`, `mf.py`, `run_mf.py`) are all present. Every F6B line cite below was checked line by line.
- REVIEW.md cites the tree at commit b4cce5b and the three patches. Neither `handover/core-hardening/` nor b4cce5b is in this checkout (no .git). The patches exist OUTSIDE the checkout at `/tmp/ch/handover/core-hardening/patches-ready/` (A-01, C-01, G5-wording, DEAD-MAN-CHECK.md); I used that copy. `/home/user/hadavin-sdk/src` is a LATER tree: the patches apply with offsets (config.py +9 and +28 lines). So REVIEW.md line numbers in config.py cannot be confirmed exactly; where I could not, I say SOURCE ABSENT. I confirmed content and patched-tree lines by applying the patches to a copy.

## FAILURES FIRST

| doc line | cite | what the file really says | verdict |
|---|---|---|---|
| REVIEW.md:22 (C-1) and :11, :17 | "Today 'NaN' crashes `load_config` with a raw traceback and 'Infinity' passes. Verified above." | The "verified above" (line 17) covers only the Decimal arithmetic, which is true (`Decimal('NaN') <= 0` raises `InvalidOperation`, an ArithmeticError; `Decimal('Infinity') > 0` is True; also `min(NaN, 1) <= 0` raises). But the premise is FALSE with the pinned library: with pydantic 2.14.1 (pyproject.toml:16, uv.lock:1651) `Route(input_usd_per_mtok='NaN' / 'Infinity' / 'sNaN' / '-Infinity')` is refused with a ValidationError "Input should be a finite number", in the unpatched checkout AND in the patched copy. So the patched `min(...) <= 0` never sees a non-finite value. Only `'0'` and `'-1'` pass the field. I did not run `load_config` end to end; I ran `Route(...)` directly. The b4cce5b pydantic pin is not known. The Major C-1 and the "(a) ... So R1-01/F1 is real" claim rest on a premise the checkout contradicts. | WRONG (premise) |
| REVIEW.md:11 | "0 Blocker, 6 Major, 14 Nit/Minor ... 17 PROPOSE FIX, 0 CONTEST, 0 ESCALATE, 3 DECLINE" | The tables hold 19 rows: C-1..C-6 (6), A-1..A-9 (9), G-1..G-2 (2), D-1..D-2 (2). Majors 6 (C-1, C-2, A-1, A-2, A-3, G-1) OK. DECLINE 3 (C-4, C-5, A-9) OK. So Nit/Minor = 13 (not 14) and PROPOSE FIX = 16 (not 17). | WRONG (count) |
| REVIEW.md:15 | "22 demo tests did not collect (askdata missing)" | evidence-13.md:13: "22 collection errors (20x ModuleNotFoundError askdata, 2x FileNotFoundError) all under tests/demo_askdata". They are collection errors, and 2 of 22 are a missing file, not the askdata module. | WRONG (minor wording) |
| REVIEW.md:26 (C-5) | "the error match (`config.py:453`)" | Taken from review-codebase-r1.md:14 ("match=\"zero or negative price\" works (config.py:453)"). In the patched copy the message `routes with a zero or negative price` is at config.py:401 (test match at tests/test_c01_route_limits.py:28). Line 453 of the patched copy and of the checkout is `_read_yaml` / `load_yaml`, not an error match. In the b4cce5b tree this line cannot be checked. | WRONG vs patched copy; base tree SOURCE ABSENT |
| F6B-AUDIT.md:58 (and :90 area) | "`V5-NODE-DIFF.txt` = the list of allowed differences ... (in `handover/demo/`)" | The file is `handover/demo/n8n-flows-real-v5/V5-NODE-DIFF.txt`. `handover/demo/V5-NODE-DIFF.txt` does not exist. | WRONG (path) |
| F6B-AUDIT.md:54 and :62 | "`F6-01` ... entry door findings (F6-01 to F6-07)" | F6-AUDIT.md has rows F6-01, 02, 03, 04, 06, 07. There is no F6-05 row; F6-AUDIT.md:63 says it was merged into F6-01. | WRONG (minor: range includes a missing id) |
| F6B-08 (F6B-AUDIT.md:86) | "real-v5 json:250-262" for "Every30s feeds MarkFailed, ClaimStuck, AlertClaim" | `n8n-flows-real-v5/mf-recovery.json`: MarkFailed link at 255, ClaimStuck at 260, AlertClaim at 265. The range 250-262 omits the AlertClaim link. Cites 255 and 260 are exact. | WRONG (minor: range short by 3 lines) |
| F6B-13 (F6B-AUDIT.md:91) | "`SCENE-FLOW-MAP.md:43-45`" for scenes 6 to 8 | Lines 43, 44, 45 are scenes 7, 8, 9. Scene 6 is line 42. | WRONG (minor: off by one scene) |
| F6B-14 (F6B-AUDIT.md:92) | "`SCENE-FLOW-MAP.md:39`" for "scene 2 shows nothing on a re-take" | Line 39 is scene 3 ("Same lead again": Claim `ON CONFLICT ... DO NOTHING`, `repeat: true`). It supports the mechanism but it is scene 3, not scene 2. | OK as mechanism, WRONG scene label |

## ABSENT / not checkable

| doc line | cite | note | verdict |
|---|---|---|---|
| REVIEW.md:19-27 (C-1, C-2, C-3, C-6) | config.py:40-47, :344, :356-358 | Base tree b4cce5b absent. In this checkout the same code is at config.py:43-56 (`_money`, `Money`), :360 (`executor_timeout_s`), :384-386 (`llm_judge` names a route). Offsets of +9 / +16 / +28 are consistent with the patch offsets (+9, +28). review-codebase F1 puts `Money` at base line 47, which matches the end of 40-47. Content matches. | OK by content; exact lines SOURCE ABSENT |
| REVIEW.md:3, :14, :17, :58 | "b4cce5b", "branch bf5f18383" | No git history here. SUMMARY.md (heavy-test-lane) names b4cce5b and tip bf5f18383. Not verifiable against a commit. | ABSENT |
| REVIEW.md:32 (A-1) | "ORDER 009 Q-X1" | Present as "ORDER 009 ... Q-X1" in `/tmp/ch/handover/core-hardening/AUDIT-FINDINGS.md:8`, not in the checkout. | ABSENT in checkout |

## OK cites, REVIEW.md

| doc line | cite | what the file says | verdict |
|---|---|---|---|
| 14 | tests fail on old code: 15 failed, 55 passed | evidence-13.md:23-24: "15 failed, 55 passed in 17.19s"; list = C-01 8 + A-01 5 + p7_tick 2 (order + manifest). Matches 8+5+1+1. | OK |
| 14 | `ruff check`, `format --check`, `bandit -ll` rc 0; patches apply alone and in order | evidence-13.md:18, :102 (git apply --check each rc=0). `patch --dry-run` of all three on the checkout also succeeds (offsets only). | OK |
| 14 | five mutations each caught | evidence-13.md:95-99 (a, a2, b1, b2, c). | OK |
| 15 | 5 failures in BOTH trees, 6th is uv.lock test | evidence-13.md:16-17 (AFTER 5 failed) and :90 (BEFORE 6 failed incl. `test_uv_lock_version_matches_the_package`). | OK |
| 16 | direct A-01 tests did not fail when step removed from STEPS | evidence-13.md:99. | OK |
| 17 | `approvals/channel.py:29` runs `redact_text` last | channel.py:29 `out = runmap.redact_text(...)` inside `clean()` whose docstring says "then ONE redaction, last". | OK |
| 45 (G-1) | "the Slack channel also redacts once more" | slack_channel.py:71, :81 (`redact_text` once more). | OK |
| 45 (G-1) | gate.py lines 7-8 header | Patched gate.py:7-8 contain "nothing in this repository re-scans text before it leaves". | OK |
| 46 (G-2) | `guard/redact.py:947` "the gate re-scans with a fresh one" | Unpatched checkout redact.py:947 (patched copy 948). | OK |
| 46 (G-2) | gate.py:9 and :61-66 | Patched gate.py:9 ("The original module notes follow"), :61-66 ("Every way out ... Verdicts"). Unpatched is 58-63. | OK (patched tree) |
| 24 (C-3) | `backends.detector` with `llm_judge` can name a route | config.py:384-386 in checkout. | OK |
| 25 (C-4) | `k1b/replay.py:87` duplicate zero-price check | replay.py:85-87 `_refuse_zero_price`; line 87 is the zero test. | OK |
| 26 (C-5) | `table.py:43-61` `AnthropicSettings` | backends/table.py:43-61 is exactly `class AnthropicSettings` ... `return self`. | OK |
| 33 (A-2) | `audit/protocol.py:27`, `app.audit` typed AuditSink | protocol.py:27 `def reconcile(self) -> int`; app.py:50 `audit: AuditSink`. | OK |
| 33 (A-2) | docstring promise in `k1b/audit_sink.py` | audit_sink.py:38 "on failure the sink keeps it for ``reconcile``". | OK |
| 35 (A-4) | `local_dir.py:130` last resort goes to in-memory list; WARNING but no ERROR | Patched local_dir.py: WARNING at :120, `except` at :130, `_pending.append` at :131. Unpatched file has no logging. | OK (patched tree) |
| 64 | full run: baseline 2 failed 9389 passed, patched 2 failed 9404; ruff/format/bandit 0 | heavy-test-lane/SUMMARY.md lines 20-21; the two failures are guard tests that scan handover/ files (SUMMARY.md:8-12). Note SUMMARY.md:14-15 says the 5 scratch-tree failures "did not reproduce; likely cause ... not tested"; REVIEW.md:64 says they "do not occur", which is true but omits "cause untested". | OK (wording slightly stronger than source) |
| 3 | inputs R1-01..R1-14, F1..F9 | review-design-r1.md has R1-01..R1-14; review-codebase-r1.md has F1..F9. | OK |

## OK cites, F6B-AUDIT.md (all checked; none wrong except as listed above)

| doc line | cite | what the file says | verdict |
|---|---|---|---|
| 18, 22 | SCENE-FLOW-MAP.md:66 (C1), "UNCHECKED", four real flows | Line 66 is C1; says "Whether the take tool already does it is UNCHECKED"; "deactivate ALL FOUR real-v5 flows". | OK |
| 20 | build_mainframe.py:51,54 | :51 SetCrmId (needs `state='processing'`), :54 MailClaim. | OK |
| 18 | 12 `mf-recovery.json`, same title, 2 are v5, one in v1-superseded | `find` gives 12; all 12 titled "Lead desk main frame: recovery (every 30 s)". | OK |
| 60 | real-v5 and film-v5 recovery differ only in lines 177-178 | `diff` shows only hunk 177,178c177,178. | OK |
| 60 | `n8n-flows/mf_leads.sql` lacks alert columns | It has 11 columns, none of the four alert columns; v4 file has them. | OK |
| 79 F6B-01 | json:26,102,124 | Query text of ClaimStuck, MarkFailed, AlertClaim at those lines. | OK |
| 79 | T11 `mf.py:214-219` | t11 starts 214, uses `recovery_copies=2`; `summarize` is line 220. | OK |
| 80 F6B-02 | no clean-up text in V5-README, RERUN-RUNBOOK, VIDEO-RUNSHEET; `mf.py:44-47` | grep for truncate / drop table / stuck rows: no hit in the three files; hit only in SCENE-FLOW-MAP.md. mf.py:44-47 DROP and CREATE TABLE. | OK |
| 81 F6B-03 | build_mainframe.py:82-83, :91, :103, :108-109; :54, :59 | Claim `ON CONFLICT DO NOTHING` 82-83; ReplyStored 91; MarkFailed 103 (`CASE WHEN mail_sent THEN 'unknown' ELSE 'failed'`); alert texts 108-109; MailClaim 54; MarkUnknownB 59. Quoted alert sentences match exactly. No file gives a reset instruction (alert_sent appears only as a column name in VIDEO-RUNSHEET:39,40,50). | OK |
| 82 F6B-04 | :112-113 AlertMark | Exact. | OK |
| 83 F6B-05 | :108-109, :51, `mf.py:72`; `[demo]` prefix in real-v5 | Exact; real-v5 json:179 subject starts `[demo]`. | OK |
| 84 F6B-06 | `mf_leads.sql:6-13`; :98-100, :103 | claimed_until (line 9) has no NOT NULL; state CHECK includes 'new' (line 8). | OK |
| 85 F6B-07 | :103, :98-100, :27, :26,28,29, `mf.py:201-213` | HubSpot "NO timeout option" comment at :27; upsert on e-mail :26,28; `hadavin_lead_id` :29; T10 201-213. | OK |
| 86 F6B-08 | :115 links; json:255, 260; node positions | :115 link order MarkFailed, ClaimStuck, AlertClaim; json:255 MarkFailed, :260 ClaimStuck; ClaimStuck pos [220,-100] above MarkFailed [220,120]. (Range 250-262: see failures.) | OK |
| 87 F6B-09 | :99,105 LIMIT 5; :103 no limit; backoff 60-300 s | :110 `60 s * LEAST(alert_attempts,5)`. Arithmetic (10 mails/min) follows. | OK |
| 88 F6B-10 | `mf_leads.sql:5-20`; 8,640 scans/day | Only `lead_key` PRIMARY KEY; 3 queries x 2880 ticks = 8640. | OK |
| 89 F6B-11 | `mf.py:48-58`, `:44-47`, `V5-README.md:8-9,20`, `mf.py:254-255` | mf.py:13 `MF_LEASE` default 20; :54 build call passes only lease; V5-README:8-9 commands, :20 says T17/T18 build with env; mf.py:255 sets MF_V4 for B90. | OK |
| 90 F6B-12 | :99, :103, :109, :105,106, :97, :10, :8 | All exact (lease default 120 at :8; TRIES :10; timer :97). | OK |
| 91 F6B-13 | `.drop` at mf.py:224 | t12, line 224 writes `MAIL + ".drop"`. | OK |
| 94 F6B-16 | `mf.py:273` T15 limit `3 x lease + 150 s` | Line 273 contains `3 * LEASE + 150`. Arithmetic 135-255 s follows. | OK |
| 95 F6B-17 | :105,108-113; AF2 "2 alerts = duplicate" | mf.py:252 "alerts for A %d (2 = duplicate case)". | OK |
| 3, 33, 52 | counts: 17 rows; 1 take Blocker; 2 Major; 2 conditional Major; 1 Nit-may-be-Major; 11 Nit; client 2 Blocker | Table has F6B-01..17. Take column: Blocker 01; Major 02, 13; conditional 14, 15; 08 Nit/Major; Nit 03,04,05,06,07,09,10,11,12,16,17 = 11. Client Blocker 01, 03. | OK |
| 62 | F-001, F-008, F-010, F-012, F-014, F-018, F-029, F-030, F-031, F-032, F-035, F-037, F-039, F-044 | Every id exists in FINDINGS.md with the topic the doc gives (F-014 "288 per lead per day"; F-039 lists exactly five sub-workflow nodes; F-008 six recovery nodes; F-012 "no timeout option (build_mainframe.py:27)"). | OK |
| 52, 57 | PLAN-002.md:61 rubric; FINDINGS.md:93 = F-031; R370, R460 named in FINDINGS | PLAN-002.md:61 is the Severity line; FINDINGS.md:93 is F-031 (invalid e-mail, `review`); R370 and R460 both appear in FINDINGS.md. | OK |
| 116 | `run_mf.py:15` postgres 16 by digest, UNVERIFIED for arm64 | `PG_IMAGE = "postgres@sha256:..."  # postgres:16 ... UNVERIFIED`. | OK |
| 29 | reviews/ files f6b-naive-r1, f6b-design-r1, f6b-naive-r2, f6b-facts-r2 | All four exist in `handover/flows-audit/reviews/`. | OK |
| 55, 62 | K-SERIES-V4.md, CUT-LIST.md, RUNSHEET-WORDING N-1, VIDEO-RUNSHEET 11 scenes | All files exist; N-1 present; run sheet table runs to scene 11. | OK |
| 56 | the T-... tests are "PROPOSED, none exists" | No T-TWOSETS / T-CLEAN etc. in any .py under handover. | OK |

## Not checked
- Whether the b4cce5b tree matches the offsets exactly (no git history).
- `load_config` end to end with a NaN price (I ran `Route` only; module `pydantic_settings` was loaded via the repo `.venv`, not via `uv run`).
- Timing, n8n and Postgres behaviour claims in F6B-AUDIT.md (the doc itself marks them UNVERIFIED; nothing was run).
- DEAD-MAN-CHECK.md cites (`runtime/tick.py:323`, migration lines 30-35) were only glanced at (tick.py:320-325 builds the TickState row; the table is in the 0003 migration); they are cited in the patch note, not in REVIEW.md.

EGM skipped: read-only citation check. No agents started; no processes left running; one scratch copy in the scratchpad (`.../scratchpad/pt`).
