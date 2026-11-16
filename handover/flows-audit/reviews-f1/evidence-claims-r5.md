# Evidence, claims table round 5 (EVIDENCE RUNNER; raw output, no judgement). Run 2026-11-16.

## Failures and oddities first
- Rule 'every to-do row has a tag': 37 of 79 rows have NO [LIVE]/[LIVE, TEXT ONLY]/[OUT OF THIS VIDEO] tag: rows 41 to 77, which are all of Table 2 (the fix log says tags were put on Table 1 rows only). Table 1 rows (1-40, 78, 79) all carry a tag. Tags seen: LIVE 10, LIVE TEXT ONLY 8, OUT OF THIS VIDEO 24 (19 'kept for the later video', 5 'document wording: fix when next touched').
- Unmentioned verdict changes in the fix log: none (all 4 changed ids are named in fix-f1-r5.md).
- Banned phrases still present in CLAIMS-TABLE.md: grep hits at lines 35, 103, 107, 108, 183, 387, 388, 727, 729 ('one database' and 'audit trail'; 'paste-ready' none). Lines 107, 108, 387, 388, 727 state the rule that the video must not say them; line 183 quotes DECISION-one-store.md:14; lines 35 and 103 hit on a longer string (see raw grep, cut at 200 chars, not inspected further).
- Cite sample: the cited files exist in the canonical folder handover/demo or handover/flows-audit/inputs. Copies in handover/flows-audit/tools/scratch/** differ from handover/demo (e.g. VIDEO-RUNSHEET.md:23, PAGE-STATEMENTS-V4.md:120 and :130 differ), so a cite is only right for one version. Canonical (non-scratch) lines are printed below.

## Count script (python3 claims-count.py CLAIMS-TABLE.md)
verdicts: {'UNSUPPORTED': 28, 'SUPPORTED': 113, 'UNTRACED': 69, 'OVERSTATED': 48, 'RELAYED-ONLY': 69} total 327
lanes (A, B incl. X): {'A': 97, 'B': 226, 'X': 4}
to-do rows: 79
offenders: 0 []
ids: 327 unique: 327
round 4 copy:
verdicts: {'UNSUPPORTED': 25, 'SUPPORTED': 114, 'UNTRACED': 70, 'OVERSTATED': 49, 'RELAYED-ONLY': 69} total 327
lanes (A, B incl. X): {'A': 97, 'B': 226, 'X': 4}
to-do rows: 78
offenders: 0 []
ids: 327 unique: 327
Fixer's claim: SUPPORTED 113, RELAYED-ONLY 69, OVERSTATED 48, UNSUPPORTED 28, UNTRACED 69, total 327, 79 rows, 0 offenders, 327 unique: MATCHES r5 output.

## Verdict changes r4 -> r5 (ids compared: 327 both, none added or removed)
r4 ids 327 r5 ids 327 only r4 [] only r5 []
B-032 OVERSTATED -> UNSUPPORTED MENTIONED
B-056 OVERSTATED -> UNSUPPORTED MENTIONED
B-189 UNTRACED -> UNSUPPORTED MENTIONED
B-219 SUPPORTED -> OVERSTATED MENTIONED

## Tag check (to-do rows 79; untagged rows listed)
untagged: 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 

## Banned phrase grep (case-insensitive), line numbers and first 200 chars
35:- n8n runs on its own database today (a small SQLite file). This rests on one earlier smoke run (a first trial run of the whole take set-up; DECISION-one-store.md line 8), not on a check of the tak
103:- P4b (n8n database): list the files in the take's n8n data folder; if a SQLite file (database.sqlite and its -shm, -wal files) is there, n8n keeps its own records in it, and the video says only "
107:- Q4 (the video says nothing about "one database"; wording "n8n keeps its own records"): nothing breaks; DECISION-one-store.md:14 is an aim, not a state (new row).
108:- Q5 (no "approval" and no "audit trail" in the video; the narrow claim is "the same lead id sent twice is processed once"): at risk in the rows for A-036, A-050, B-078, B-183, B-189, B-024, X-4 a
183:| 36 | DECISION-one-store.md | DECISION-one-store.md:14 | (no lane row) (was new) | "ONE database for everything we own: the single Postgres instance of the take (one container, one engine)." (DEC
387:- Q4 ("the video says nothing about one database; default 'n8n keeps its own records'"): grep for "one database" and "single database" in R and P: 0 hits. No break. Caveat: A-010, A-053 and A-074 
388:- Q5 (neither "approval" nor "audit trail" in the video; narrow claim is "the same lead id sent twice is processed once"): grep for "approv" in R and P: 0 hits; "audit trail" 0 hits; the word "aud
727:Rules: (R1) the video does not say "one database" (default: "n8n keeps its own records"); (R2) no "approval" and no "audit trail" words (narrow claim: "the same lead id sent twice is processed onc
729:R1, "one database": none of the 14 files says it. Not a break. But DECISION-one-store.md:14 ("ONE database for everything we own") is a decision in force, and N8N-START.md:4 ("separate from n8n's 

## Random 25 cites, seed 20261116 (canonical files, scratch copies excluded)
row  1:
  VIDEO-RUNSHEET.md:4 [handover/demo/VIDEO-RUNSHEET.md] -> - Matched to the real take: lease 45 s; real mail service and real CRM service in scenes 1 to 5 (made-up people only); t
row  2:
  VIDEO-RUNSHEET.md:8 [handover/demo/VIDEO-RUNSHEET.md] -> Written by the cloud demo session from: V7-NUMBERS-lead-read, DOUBTFUL-SCENE, PLAN-4-NLITE-FROM-LEAD (section 0, WP5, se
row  3:
  VIDEO-RUNSHEET.md:23 [handover/demo/VIDEO-RUNSHEET.md] -> - Recovery wording: NONE for now (lead 17:05Z dropped the plus 25 to 30 s caption); after lane3 lease-45 runs land: meas
row  15:
  VIDEO-RUNSHEET.md:41 [handover/demo/VIDEO-RUNSHEET.md] -> | 12. Closing card | No clicks. Voice over one card, six short lines. | Line 1, claim: a lead sent twice with the same i
  PLAN-4-NLITE-FROM-LEAD.md:57 [handover/demo/PLAN-4-NLITE-FROM-LEAD.md] -> Claims check: the video may say "leads arrive through n8n; n8n writes the CRM contact and sends the mail; our code caps 
row  17:
  VIDEO-RUNSHEET.md:41 [handover/demo/VIDEO-RUNSHEET.md] -> | 12. Closing card | No clicks. Voice over one card, six short lines. | Line 1, claim: a lead sent twice with the same i
row  23:
  VIDEO-RUNSHEET.md:90 [handover/demo/VIDEO-RUNSHEET.md] -> Scene 4 caption (FINAL, lane3 HB194, lease 45 s, film-v4, RELAYED-INDEPENDENT): "About a minute after the crash (measure
  PAGE-STATEMENTS-V4.md:150 [handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md] -> NAMING (lead, final): lane3 K3 = this page's K3B (killed after the mail left: unknown + 1 alert); lane3 K6 = this page's
row  25:
  PAGE-STATEMENTS-V4.md:120 [handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md] -> 17. "Recovery within 60 s was measured only at the 20 s test lease (max 59.6 s, margin 0.4 s, n=20 per kill point, one m
row  27:
  PAGE-STATEMENTS-V4.md:149 [handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md] -> 20. "At the film lease of 45 s, a lead interrupted by an n8n crash was finished about a minute after the crash." Seconds
row  28:
  PAGE-STATEMENTS-V4.md:159 [handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md] -> Caption rule: only K1 and K2 (done), or the range. NEVER "within 60 s".
row  32:
  OWNER-STEPS-realrun-v3.md:99 [handover/flows-audit/inputs/OWNER-STEPS-realrun-v3.md] -> - During the take: contacts appear in HubSpot, one mail per person appears in the `demo` label. The lead stops and resta
row  36:
  DECISION-one-store.md:14 [handover/flows-audit/inputs/DECISION-one-store.md] -> 1. **ONE database for everything we own: the single Postgres instance of the take** (one container, one engine). n8n's i
row  42:
  PAGE-STATEMENTS-V4.md:130 [handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md] -> Total: 18 statements.
row  44:
  AGENT-SCOPE-DO-AND-DONT.md:6 [handover/flows-audit/inputs/AGENT-SCOPE-DO-AND-DONT.md] -> - MAY: receive a lead on its webhook or form; claim the lead key once in Postgres; write one HubSpot contact; send the i
row  45:
  AGENT-SCOPE-DO-AND-DONT.md:7 [handover/flows-audit/inputs/AGENT-SCOPE-DO-AND-DONT.md] -> - MUST NOT: process the same lead key twice; send mail to an address it was not given by the take config; read or print 
row  50:
  PLAN-4-NLITE-FROM-LEAD.md:78 [handover/demo/PLAN-4-NLITE-FROM-LEAD.md] -> - **Why three idempotency layers exist (so a reviewer does not cut one):** the n8n claim row stops a second door/resend 
row  52:
  PLAN-4-NLITE-FROM-LEAD.md:122 [handover/demo/PLAN-4-NLITE-FROM-LEAD.md] -> - Tests: T17 (stand-in CRM answers with only `id`: crm_id stored, lead done) ; T18 (answers with neither: lead ends fail
row  54:
  FAILED-TAKE-NOTE.md:16 [handover/demo/FAILED-TAKE-NOTE.md] -> - **`end.flag`**: what it is, who writes it, when it ends a take. Not found anywhere.
row  61:
  DESIGN-A-README.md:15 [handover/demo/n8n-flows/DESIGN-A-README.md] -> Sub-workflow: Qualify (HTTP Request to the cap stage, retry 3, error output) -> IF label is hot/warm/cold and not unknow
row  62:
  DESIGN-A-README.md:15 [handover/demo/n8n-flows/DESIGN-A-README.md] -> Sub-workflow: Qualify (HTTP Request to the cap stage, retry 3, error output) -> IF label is hot/warm/cold and not unknow
row  63:
  DESIGN-A-README.md:15 [handover/demo/n8n-flows/DESIGN-A-README.md] -> Sub-workflow: Qualify (HTTP Request to the cap stage, retry 3, error output) -> IF label is hot/warm/cold and not unknow
row  65:
  DESIGN-A-README.md:17 [handover/demo/n8n-flows/DESIGN-A-README.md] -> Constants in the nodes (no expression): mail recipient intake at example.test, alert recipient alerts at example.test. M
row  66:
  DESIGN-A-README.md:20 [handover/demo/n8n-flows/DESIGN-A-README.md] -> Shipped lease for the real and film flows (lead decision 17:05Z): 45 seconds, built with 2 tries of 10 s per stage (v4 a
row  70:
  V5-README.md:4 [handover/demo/n8n-flows-film-v5/V5-README.md] -> - NEW IF node CrmIdOk right after SetCrmId. It checks the same value (read from the CrmUpsert answer). Non-empty goes on
row  73:
  n8n-published-numbers.md:4 [handover/demo/n8n-published-numbers.md] -> - K1 (crash after step 1): crashed entry visible 1 of 5 (builder rerun matched differently)
row  79:
  OWNER-STEPS-realrun-v3.md:131 [handover/flows-audit/inputs/OWNER-STEPS-realrun-v3.md] -> NEEDS-OWNER. You post; Claude never posts. The post says only: leads arrive through n8n; n8n writes the CRM contact and 
ABSENT: 0
