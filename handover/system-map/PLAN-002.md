# PLAN for ORDER 002 (system-map), version 2 (after plan review round 1 and egm:egm-resolve; written 2026-11-16 ~06:50 UTC / 12:20 IST)
ORDER 002 was written by the lead on 2026-11-16 (no clock time in the order). This is a STATIC review in a cloud box: no n8n runtime, no network to real services, made-up data only. Anything that needs a runtime to confirm is marked UNVERIFIED.

## 0. Goal in plain words
Give the lead evidence-backed answers (not opinions) to three questions about the whole demo as this repo shows it: (1) what exists and who owns each job (MASTER-MAP), (2) what is duplicated, dead, idle, inconsistent, or claimed without proof (SWEEP), (3) for each job (store, log, filter, counter, retry engine, notice) which single place should own it and what to cut or archive (ONE-PLACE-TABLE). The owner found many duplicates and idle parts (desk vs n8n vs portal vs CRM, several stores); the standing audit rule asks for this.

## 1. Ladder line (plain words)
"Tool ladder" = the studio rule to use something that already exists before writing code. Rung 1 (reuse): the method is ARCHITECTURE-AUDIT-CHECKLIST.md and the baseline is DECISION-one-store.md. All map work is reading and grep. Our own code is limited to two tiny scripts, each a safety check with nothing higher that does the same job: `tools/partition.py` (every file belongs to exactly one lane) and `tools/check_citations.py` (every cited file:line exists and the quote is there). Verdict: KEEP-CODE for those two only; both are specified in section 6.

## 2. Outputs (all in handover/system-map/; no file outside this folder is changed)
| # | File | Content |
|---|---|---|
| 1 | MASTER-MAP.md | the map (columns in section 4). Includes an explicit row `TAKE-REPO` = "duplicate-proof-lead-desk take code repo: NOT VISIBLE in this box, lead covers locally; content not guessed" and a row `CORE` = "src/hadavin_sdk and tests/: the shared core, out of take scope, not mapped module by module (directory list and README only)". |
| 2 | SWEEP.md | findings table (section 4) PLUS these sections, so every checklist output has a home: fix plan in order; exceptions list (reason, owner, removal trigger); claims check (claim, source, evidence or UNVERIFIED); lessons (for checklist, memory, brief preamble); counts per claim type. |
| 3 | ONE-PLACE-TABLE.md | one block per job key (section 5), the SEED rows from DECISION-one-store.md, verdicts, cut-or-archive proposals, and the row `TAKE-REPO` again. |
| 4 | patches/ledger-rows.md | proposed rows for the blocker ledger (`handover/ledger.md`, outside our folder, so a patch for the lead to apply) and any other proposed fix as a `git diff`-format patch against branch head at write time. Created only if needed. |
| 5 | work/ | lane files, manifests, checker output, review reports, resolve reports, checkpoint notes. |

## 3. Lanes (ordered rules, first match wins; `tools/partition.py` enforces it)
Model sonnet, Read/Grep/Glob plus Write limited to one path each; lanes never run repo files and never run git. The lead creates work/ and the manifests before launch.
| Lane | Owns (exact) | Writes only |
|---|---|---|
| L1 | handover/*.md and handover/tools/** ; handover/demo/{ORDERS.md, REPORT.md, APPLY-LIST.md, semgrep-pr-diff-lead.patch} ; handover/demo/{pr-text,pr-stack,followup,merge-ready,speed,reuse,drift}/** | work/L1.md |
| L2 | handover/demo3/kill/** (flows, SQL, harness, run scripts, results, run logs) ; handover/demo3/*.md (FREEZE, MATRIX-1, ORDERS, REPORT, WINDOWS-RUN-1, questions-for-lead, register) | work/L2.md |
| L3 | handover/demo3/{evidence,tools,scratch}/** | work/L3.md |
| L4 | REMAINDER of handover/demo/** (coverage, fixes, gitleaks, hang, integration, layout, outsider, outsider2, real-run, scans, semgrep, skips, sonar, stranger, triage, xss and anything new) | work/L4.md |
| L5 | every tracked file outside handover/ (.claude, .github, demos/, docs/, tools/, tests/, src/, root files). src/ and tests/ get ONE `CORE` row each plus any store/log/retry/counter/filter/notice found by grep; desk/portal docs live here if present, else the sweep says NOT FOUND | work/L5.md |
| L6 | no files of its own: the cross-cutting JOB PASS. Reads work/L1..L5.md and greps all folders per job key (section 5); one pass so verdict wording is consistent | work/L6.md |
Handover/system-map itself is out of scope except as inputs. Any file matching no rule is REMAINDER: `partition.py` exits non-zero and the lead assigns it before launch. Every file is in exactly one lane (script checks both directions).
Stages are sequential: L1..L5 in parallel (max 5 agents), then L6, then lead merge, then evidence runner, then reviewers.

## 4. Lane output template (exact; one table per kind; ids `L<n>-<kind>-<nnn>`)
Kinds: C component, S store, W workflow (node by node), X script, J job/loop/schedule, K credential (NAME only), P port/host, D doc, T test, A agent/session, R repo/branch, F folder.
Full row (W, S, J, K, X): id | name | purpose (one line) | owner of the job | inputs | outputs | failure path | retry | timeout | idempotency | writes log where | identity | tested where | used by | evidence (`path:line "quote"`) | job key(s).
Short row (D, T, F, C, P, A, R): id | name | purpose | evidence | job key(s) if any.
Sweep row: id | claim type (duplicate / dead / idle / inconsistent / unverified / security / ops) | severity (Blocker / Major / Nit) | evidence `path:line "quote"` | conflicts with (`path:line` or DECISION line) | job key.
Workflow walk (for every flow): trigger, every branch, every error path, retry and timeout, behaviour on kill / restart / duplicate / out-of-order / empty / huge input, what is written where, what a person sees, which identity acts, loops and their stop condition. Not run = UNVERIFIED.
Citation form is fixed: `path:line "quote"` (repo-relative path, one line number, quote copied exactly, 6 to 120 characters).

## 5. Job keys and verdict rules
Job keys (one place per job): STORE (holds state), LOG (execution/audit record), FILTER (decides what enters: dedupe, validity, spam), COUNTER (counts used for caps or proof), RETRY (re-runs stuck or failed work), NOTICE (tells a person: mail, alert, screen). Plus any further job the sweep finds (named by the lane).
Every lane tags each row with job keys; L6 builds one block per key.
Single owner = the one file/process that is the only writer of that job in the take as DECISION-one-store.md describes it; where the decision is silent the owner is the place the final flow actually calls (evidence required).
Verdicts: NEEDED = the only owner of a job the take uses. DUPLICATE = a second place does a job that already has an owner. NOT-NEEDED = nothing in the take calls it. CRM-COULD-DO = the client's CRM or a ready-made node would do the job; the capability claim needs a dated source, else it is marked UNVERIFIED. Every non-NEEDED row carries a proposal: ARCHIVE (move to `archive/<same path>` after the owner says yes) or MERGE-INTO <owner>. Never delete. Proposal columns: what | from | to | owner yes needed | reason | evidence.
DECISION seed (checked line by line; a row that differs is flagged `CONFLICT WITH DECISION (DECISION-one-store.md line n)`): (1) n8n internal data, (2) Postgres `mf_leads`, (3) desk SQLite plus portal (retired from the take), (4) `stage.journal` (the one stated exception), (5) process logs, (6) HubSpot and Gmail (external). Unverified items from the decision (schema setting honoured by n8n, one role vs three roles, table screen) stay UNVERIFIED unless a raw file proves them.
Cited sources that are not in this box (for example `film-v5`, `real-v5`, PLAN-4 files) are reported NOT VISIBLE, never guessed.

## 6. Coverage, manifests and the two scripts
Manifest per lane (`work/manifest-L<n>.tsv`: path, bytes, status) generated by `tools/partition.py`. Builder sets each status: READ (opened fully, files over 2000 lines read in slices of 2000), SKIMMED (headers, grep, or first and last slice; allowed ONLY for: patch chains `lane3-fix-*`, `checkpoint-*`, run logs under `kill/data/runs/**`, scan outputs, screenshots), or NOT-READ. At minute 60 a lane stops, writes everything found, lists NOT-READ files, marks the lane PARTIAL; the lead may launch one continuation lane for the NOT-READ list. A file that is not READ or SKIMMED is never reported as "nothing found". Very large files (demo/REPORT.md 660 KB, demo3/register.md) are searched by job key and read by section headers; the sections read are listed.
`tools/partition.py` (about 40 lines): input = `git ls-files` plus the handover file list; output = manifest per lane; fails on REMAINDER or on a file in two lanes. Tests: (a) a file in no rule fails, (b) a file in two lanes fails, (c) system-map files are excluded, (d) file counts per lane add up to the total.
`tools/check_citations.py` (about 30 lines, stdlib only): input = the three output files; extracts every `path:line "quote"`; match rule = after trimming whitespace at both ends, the quote must be an exact substring of that line; output `work/citations.tsv` (citation, FOUND / LINE-DRIFT (quote found within 5 lines) / MISMATCH / NO-FILE) and a count. It never judges what a finding means. Tests (6): found, not found, wrong line within 5, mismatch, missing file, binary or very long file.
Acceptance checks (scripted where stated): every MASTER-MAP row has all fields for its kind (empty-field scan, script); every SWEEP and table citation is FOUND (target: 100 percent; MISMATCH and NO-FILE are fixed or removed, LINE-DRIFT corrected); every job key has exactly one owner row and every other copy has a verdict and a proposal (script counts); every manifest file has a status; secret scan (below) finds nothing.
Secrets and personal data: if a lane meets a value that looks like a key, token, password, or personal e-mail address, it records `path:line` and the TYPE only, never the value. Final outputs get a pattern scan (gitleaks rules from `.gitleaks.toml` if available, plus the literal `AKIAIOSFODNN7EXAMPLE` allowed). Credentials are listed by NAME only.

## 7. Agent conduct (from ORDER 002)
Every agent brief starts with the contents of `handover/BRIEF-PREAMBLE.md` (first line `STUDIO-PREAMBLE v1`, contains `EGM-GATE v1`) and a MUST-NOT list: no writes outside the named file, no git, no network, no secrets or personal values, no merging, no deletion, no deferring ("fix or state exact blocker"), no unverified claim. Every Agent call sets `model` explicitly (sonnet for lanes, evidence and reviewers; opus only through egm-brainstorm, egm-draft, egm-resolve). Each agent is registered in REPORT.md BEFORE it starts. Status block in REPORT.md every 10 minutes (UTC and IST) with agents running and what each does, then commit and push to cloud/system-map. Checkpoint note every 30 minutes to `work/checkpoint-<lane>.md`. Builder time box 60 minutes. Finish with a FINAL block in REPORT.md, push, stop and wait.

## 8. EGM sequence and stop rules
1. Plan review: egm:egm-review-loop (Skill) with fresh egm:* reviewer agents, then egm:egm-resolve (Skill, opus); repeat as review, resolve up to 3 rounds; stop after a round with no Blocker. Round 1 done (work/plan-review-r1.md, work/plan-resolve-r1.md).
2. Build: lanes L1..L5, then L6, then lead merge into the three outputs (lead merge time box 40 minutes).
3. EVIDENCE RUNNER: a separate sonnet agent whose brief says "EVIDENCE RUNNER": runs partition.py, check_citations.py, the empty-field scan and the secret scan, saves raw output to work/evidence-<n>.md, never judges.
4. Result review: fresh egm:* agents, different lenses: codebase-details (are the cited facts true?), zoom-out (duplicates, dead parts, is the verdict right-sized?), comprehension (can a non-technical reader follow?), design (does the map match DECISION-one-store?); each reads the outputs and the evidence, never the author's verdict.
5. egm:egm-resolve (Skill), fix every Blocker and Major, repeat step 4 at most 2 rounds; Nits fixed in the same push. Then egm:egm-drift-report before FINAL.
No heavy jobs. Max 5 agents at once.
