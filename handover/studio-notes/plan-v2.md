# Core completion plan v2 (hadavin-sdk)

Author: Hadavin lead session, for owner the owner. Date: 2026-11-05 (UTC; IST = UTC+5:30).
Status: DRAFT for plan review round 2 of at most 3. After round 3 the plan is frozen and only changed through a written amendment.
Replaces plan-v1.md. Answers review-plan-1.md (6 blockers BL1-BL6, 18 majors M1-M18) and review-brainstorm-1.md.
Evidence base: inventories A-D (docstrings, file names, git probes; function bodies were NOT read), s0-merge-probe.md (dry-run merges against origin/main ce70eb5). Every file-level claim is a lead to be re-measured in step S0, not a fact.

## 0. How the work is split (owner order 2026-11-05)

The laptop cannot run many agents. So:
* **This laptop (lead):** collects the code (done: branch `core/cloud-handover`), runs S0 measurements that need local worktrees, re-checks everything the cloud session produces against the studio rules (bible), keeps the ledger, runs the final integration, re-pin and sign-off.
* **Cloud Claude session (many agents):** all bulk work: promoting code into the core, writing tests, mutation runs, fixing CI (CodeQL, SonarCloud, CodeRabbit), review rounds. It works on branches of this repo and opens one pull request per package.
* **Rule that does not change:** the cloud session must follow the same EGM order. Authors never review their own work; reviewers are fresh `egm:*` agents (or, if EGM is not available in the cloud, fresh agents given the EGM reviewer personas and only the diff, the spec and the evidence). Nothing counts as done in the cloud until the laptop re-verifies it (section 8).

## 1. Problem, goals, non-goals

Problem: the best shared code is spread over unmerged branches, demo repos and Warden. Demos hold byte copies pinned to an old core commit (6608146); the core's main moved to ce70eb5 on 2026-11-04. Three "reserve then settle" money designs and several text-folding versions exist. The redaction work (masking personal data before it reaches a model or a log) is blocked on a branch whose design the owner replaced on 2026-11-05.

Goal: a core that any new agent project can start from in hours: each reusable capability exists once, behind one interface, with a neutral default, a working alternative (or a written outline and a trigger), tests that fail on the old code, and evidence.

Non-goals: the multi-document matching module; portal UI redesign; any paid model call; deleting old branches before the replacement passes; autonomy levels, passkeys, edge authentication, MCP schemas, payload codec, Temporal runtime, the name index, a copy of the killswitch package, Helios (each is "deferred with trigger": built only when a named consumer exists).

## 2. Core v1 (client-ready) and v1.1

Core v1 is done when every row of the table in section 8 passes. The v1 package list is exactly: **P0a-P0f, P1, P2a, P2d, P3a, P4a, P4b, P4c, P4d, P5a, P5b1-P5b6, P5c, P6a, P6b, P8a, P8b, P8c.** Everything else is v1.1 and starts only when its trigger (section 4) is met.

Moved to v1.1 by lead decision (reviewers asked for justification): P2b egress text and P2c mutation-runner cleanup (no v1 consumer needs them); SQLite backend (Postgres exists and the in-memory store is refused in client profiles); PR #41, #43, #47, #49 (no v1 consumer); C9 eval gate buckets (trigger: before any pilot or production configuration).
Kept in v1: the frozen diagnostics redesign R1-R5 (owner said yes 2026-11-05; it is the largest block).

## 3. Rules for every package

1. **Ticket first.** Before building, the package gets a ticket from `handover/TICKET-TEMPLATE.md`: id, source branch and paths, target module, interface, default and alternative, files to change, tests (including the test that must fail on the old code), evidence commands, reviewers, path class, dependencies. The ticket is reviewed (`egm:egm-review-loop`, or `egm:egm-review` for big packages).
2. **Order:** ticket review -> build (one builder) -> evidence (raw output saved as `evidence-<n>.md`, mutant summary lines read row by row, not just pass counts) -> two independent reviewers (correctness and adversarial) on a snapshot diff -> findings recorded in the ledger with the reviewed commit -> resolve -> repeat.
3. **Round and stop rule.** A *round* = fresh reviewers on a snapshot diff of the package. A package is clean when the last round found no BLOCKER and no MAJOR AND the previous round, taken after the last code change, also found none (two clean rounds in a row after the final fix) AND evidence at the final commit is green. "Changed code" = files in the pull request diff. Extended-review packages (money, all redaction, signed approvals, stop state, canonical JSON, quarantine/vault/webhook) have no round cap but escalate to the lead in writing after round 5. All other packages get at most 2 fix batches, then a written escalation to the lead.
4. **Fail-before:** every fix and guard has a test shown to fail on the old code (proof in the evidence file).
5. **One pull request per package**; the lead merges (squash, pinned to the reviewed commit) after review, evidence, CI, CodeQL, SonarCloud and CodeRabbit are green. Authors never merge.
6. **Promote** = rewrite behind a core interface with names stripped (Warden, Eldane, Helios, Jagrat, Apexc, vendor-inspired names); Apache-2.0 code copied verbatim keeps its header and a NOTICE entry. `test_lockin_guard` and `test_no_reference_material` stay green. Reuse first: `hashing.py`, `k1b/atomic.py`, `k1b/redaction.py`, `stats.py`, `evals.py`, `store/memory.py`, `askdata/meter.py`, `tests/contracts/`.
7. **Single dependency rule, stated once:** every kind has a default and either a working alternative or a written outline with a named trigger. A test double is not an alternative.
8. **Least privilege, enforced by:** branch protection on main (only the lead merges); cloud sessions use a repository-scoped token with no admin right; tests run with no secrets and no network; the secrets kind is importable only from the executor package (import test); every kind README lists its identity and rights; dev-only kinds carry a `dev_only` flag that the client profile rejects (P6a).
9. **Rebase rule:** after a rebase, reviewers read the range-diff and evidence is rerun in full; a ledger row is carried only if its files are untouched by the conflict set.
10. **Capacity:** at most one money package and one redaction/security package in progress at the same time on the laptop; the cloud session may run more, each in its own branch, but never two packages that change the same file (the ticket lists files; the lead checks overlap).

## 4. Glossary (read this first)

| Term | Meaning |
|---|---|
| core | the repo `hadavin-sdk` (package `hadavin_sdk`); the shared code every project starts from |
| kind | a pluggable part with an interface, a default and an alternative, chosen by configuration (for example the redactor kind) |
| promote | rewrite a piece of demo or Warden code behind a core interface, with tests |
| P-ids, S-steps | work packages and steps of this plan |
| C-ids | work packages of the course re-read (`handover/studio-notes/WORK-PACKAGES.md`) |
| R-ids | packages of the frozen diagnostics redesign (R1, R1P, R3a, R3b, R3c, R2, R5) in `design-v3.md` |
| BL-... | rows of the blocker ledger (`egm/BLOCKER-LEDGER.md` on the laptop) |
| ledger | the table of every blocker/major finding with status |
| fail-before test | a test that fails on the old code and passes on the fix |
| mutation run | the tests are run against deliberately broken copies of the code; survivors mean weak tests |
| snapshot diff | a saved file of the change under review so reviewers read a fixed text |
| extended review | review with no round cap (money, redaction, security paths) |
| re-pin | point a demo's copy of core files at the new core commit |
| sync check | a script (`check_core_copies`, in the demo repos) that compares a demo's pinned core copies with the core |
| drift report | `egm:egm-drift-report`: compares docs and code for differences |
| proof pack | a script that runs each v1 kind on made-up data with the fake model |
| PII | personal data (names, account numbers, e-mail addresses) |
| heavy-job slot | one of 5 machine slots (0-4) in `tools/heavy_slot.py`; builders use 0-2, the lead 3-4 (laptop only) |
| path class | money, redaction, security or other; decides the review rules |

## 5. Work packages

Columns: Id | What | Depends on | Kind: interface / default / alternative | Consumers | Milestone | Path class | Extended review

### Step S0: measure, decide, repair (nothing in S1 or later starts until S0 exits)
| Id | What | Depends on | Kind | Consumers | Milestone | Path class | Extended |
|---|---|---|---|---|---|---|---|
| P0a | Backup of unpushed work: push local PR #50 head 748849c and C1a head 8460813 as branches (owner approved pushing on 2026-11-05); check the core repo for third-party files and NOTICE duties (one grep, output saved) | - | - | - | v1 | other | no |
| P0c | `s0-report.md`: one row per branch (#41, #43, #47, #48, #49, #50 pushed, #50 local, C18a old, C1a): diff size against ce70eb5, conflict files (start from s0-merge-probe.md), test result on a clean throwaway worktree, `gh pr checks`, verdict. **Thresholds:** merge only if 0 conflict files and the suite passes; rebase if at most 5 conflict files and none shared with another row in the same wave; split if any file is shared; retire only with a ledger disposition per open row | - | - | - | v1 | other | no |
| P0d | Ledger repair: extend `egm/tools/ledger_check.py` with a WAIVED status (needs a written owner waiver id), a topic rule for re-topicked rows, a raw-newline lint (script path `egm/tools/ledger_lint.py`), tests; re-count by topic; give each superseded C18a row a disposition (carried into the hostile corpus / obsolete with reason / fixed elsewhere) | P0c | - | - | v1 | other | no |
| P0e | Decision memos from code: (1) text normalisation: differential test of all demo versions over all demo fixtures plus the attack corpus; the base must be a superset; (2) money: apply the checklist in section 7 to PR #48, PR #49, Intake `budget.py`, `askdata/meter.py`; (3) store note: reservations, inbox, queue, tenant namespace over memory and Postgres; (4) migration plan; (5) read `core-v5-pilot-kernel.md` and place KERNEL-1 and C1f in a package | P0c | - | - | v1 | other | no |
| P0f | Measuring pin of each demo against ce70eb5 (no commit to live lanes); record real slot count; decide "refunds is first client?" (default no) | P0c | - | - | v1 | other | no |
| P0b | Dependabot batch: merge green non-major bumps once, as the LAST S0 action; record the new base commit. Bound of the review exemption: CI green, lock-in guard green, full suite green, no new transitive dependency. Major bumps (pytest 9, sqlglot 30) first rerun the migration-regex and SQL parser tests | P0c, P0f | - | - | v1 | other | no |
S0 exit = P0a, P0c, P0d, P0e, P0f, P0b done; `s0-report.md` has a verdict for every row and the first measured package/round counts. If S0 changes the order, one written amendment is made.

### Step S1: text normalisation
| P1 | Small PR: split `guard/textnorm.py`, `_confusables`, `tools/gen_confusables.py` out of PR #50; superset behaviour proven by the P0e test; named views (identity key, display, scan); `FOLD_VERSION` stored with identity keys; Unicode data version pinned and tested across the Python matrix | P0e | textnorm / `fold(text, view)` / this module / outline: ICU-backed fold, trigger: a client language the standard tables mishandle | all demos | v1 | security | yes |

### Step S2: PR #50 slices
| P2a | Stop state: `stop_gate` + `rowstore` + `config_view` as one stop-state module (scoped kill, audited reset, breaker). First fix PR #50's failing test, the weak mutant row `rows: no default row limit` (verify the ledger ids in P0d), the restore-without-audit rows, the open round-3 majors | P1 | stop_state / engage, status, audited release / store-backed / outline: adapter to a hosted killswitch, trigger: a client asks | apexc, dealdesk, refunds, jagrat | v1 | security | yes |
| P2d | `redact.py` pattern changes carried by PR #50 (that PR owns the file; C1a waits for it) | P1 | - | all | v1 | redaction | yes |
| P2b | `egress_text` slice | P1 | - | apexc, dealdesk, refunds | v1.1 | security | yes |
| P2c | `testing/mutation` runner: use Intake's KILLED/CRASH split, remove the duplicates | P1 | - | all | v1.1 | other | no |

### Step S3: migrations
| P3a | Migration rule and CI check: numbers on main never change; renumber in merge order; additive and forward-only; migrate test from the previous head; CI fails on duplicate or out-of-order numbers. Extends `store/migrate.py` and `tests/test_migrate_regex_linear.py` | P0e | - | all | v1 | other | no |

### Lane M: money
| P4a | C2 (typed `UsageMissing`, settle at worst case, `is None` checks, sweep of `x or default` on numbers), C3 (five-class `Usage`), C4a (prompt-length price tiers, dated price check in config). Three pull requests, one per C-id | P0e | usage / dataclass / this module | Intake, askdata | v1 | money | yes |
| P4d | Store contract suite over memory and Postgres (extend `tests/contracts/`); move psycopg behind the store kind (importers: `store/migrate.py`, `store/postgres.py`, `store/protocol.py`, `runtime/tick.py`, `demos/ask-your-data/askdata/pgsource.py`; update `test_lockin_guard` list); SQLite backend is v1.1 | P0e, P3a | store / protocol / Postgres / memory (dev only); outline: SQLite, trigger: Intake moves onto the core meter | all | v1 | money | yes |
| P4b | C17 reserve/settle meter. Base chosen in P0e by the section 7 rule. One spend counter shared with `limits.py`. Durable store per P4d; in client profile memory is rejected by P6a. #48's extras (extract leaks, spend-cap 429) are separate pull requests | P4a, P4d | meter / reserve, settle, release / store-backed / test double: memory | Intake, askdata, refunds | v1 | money | yes |
| P4c | C8 run cost cap (`Agent.budget_usd.per_run`) and the core alert hook on `limits.daily_budget` | P4b | - | Intake | v1 | money | yes |
| P4e | Per-call log sink (JSONL default; outline: OpenTelemetry, trigger: a client uses it) | P4b | sink | Intake | v1.1 | other | no |

### Lane R: redaction (the frozen redesign, one row per package; order inside the lane is serial)
| P5a | R1: `codes.py`, `guard/diagnostic.py`, `diagnostic_schema.py`, `t1.py`, class `code` on the 17 own exception classes, hostile corpus, type tests, mutants; rebuilt on ce70eb5 | P0d, P1 | - | all | v1 | redaction | yes |
| P5b1 | R1P | P5a | - | all | v1 | redaction | yes |
| P5b2 | R3a | P5b1 | - | all | v1 | redaction | yes |
| P5b3 | R3c | P5b2 | - | all | v1 | redaction | yes |
| P5b4 | R3b | P5b3 | - | all | v1 | redaction | yes |
| P5b5 | R2 | P5b4 | - | all | v1 | redaction | yes |
| P5b6 | R5 | P5b5 | - | all | v1 | redaction | yes |
| P5c | C1: redactor kind (C1a, C1b, C1c, C1d) plus put-back (C1f): mask the document before the model; redactor error -> NEEDS_PERSON `redaction_error` and no model call; restore values in the proposal in code. Decisions already taken: F10 wording, 6th code `session_closed`, REGEX_VERSION 4 | P2d, P5b6 | redactor / `mask(text, session)` / `guard.redact` / outline: detector-model backend, trigger: a client document type the patterns miss (outlined, not a closure condition) | Intake, all | v1 | redaction | yes |

### Step S4: client-profile gates
| P6a | Every kind has a `dev_only` flag; the client profile refuses dev-only kinds (hmac_v0 signer, env secrets, memory store/meter, fake channel) and refuses the llm kind unless the redactor kind is selected; test for each | P4b, P5c | - | all | v1 | security | yes |
| P6b | No-training lock as a gate in the llm kind before any non-fake call; import test that only the executor package reads the secrets kind | P4a | - | Intake, askdata | v1 | security | yes |

### Step S5: finish
| P8a | Re-pin each demo once to the final core commit (never into a worktree being edited); version tag and CHANGELOG per merge; `core_copies.json` updated; public API note (`__all__`, deprecation rule); Python-version matrix | all v1 | - | all demos | v1 | other | no |
| P8b | Per-kind README, `egm:egm-drift-report`, `ledger_check --topic core`, rollback tags | P8a | - | - | v1 | other | no |
| P8c | Proof pack: the script `tools/proof_pack.py` runs each v1 kind on made-up data with the fake model (no model call, no real names) and exits 0 | P8a | - | - | v1 | other | no |

### v1.1 packages (each starts only on its trigger; the source branch is named in its ticket)
| Id | What | Trigger | Extended |
|---|---|---|---|
| P3b | PR #49 rebase: signed approvals, reply check, identity text, outbox; reservations only if refunds is the first client | a client needs signed approvals | yes |
| P3c | PR #41 (measurement, demotion) rebase and renumber | first pilot | no |
| P3d | PR #43 and #47 (ask-your-data) | that demo is shown | no |
| P7a | Inbound message ledger with one terminal state for a reused message id | second consumer | yes |
| P7b | Tenant namespace, RateCap, ReadLog, data-source loader, test helpers | second consumer | no |
| P7c | Least-privilege authorize/requires extension | second consumer | yes |
| P7d | Canonical JSON ASCII form as an option (default unchanged); signer split | signatures needed | yes |
| P7e | Money parsing in minor units (reconcile negative amounts) | refunds or Intake export | yes |
| P7f | C9 eval gate buckets and eval core | before any pilot/prod | no |
| P7g | C18b hygiene batch and cheap duplicate removals | with a PR touching the file | no |
| P7h | Warden batch A (numbers check, evidence ids, grounding, language detect, freeze windows, safe path, confidence labels), from refreshed Warden | a consumer names one | no |
| P7i | Warden batch B (breaker, target lock, landed check, environment policy) | Jagrat needs it | yes |
| P7j | Warden batch C (quarantine, vault, webhook/read scope) | Intake's untrusted path names it | yes |
| P7k | Scan, workqueue, approval service and payment-detail checks as a core kind | their lane reviews close | yes |
| P7l | SQLite store, second channel, second executor | trigger in P4d / a client | yes |

WP matrix: C1/C1a-d/C1f -> P5c. C2, C3, C4a -> P4a. C4b -> Intake lane. C5 -> P4c plus Intake lane. C6 -> P4e. C7 -> Intake. C8 -> P4c. C9 -> P7f. C10-C16 -> bible/Intake, not core. C17 -> P4b. C18a -> P5a-P5b6. C18b -> P7g. C19-C22 -> lead. KERNEL-1 -> placed by P0e.

## 6. Order (derived from the Dependencies column; a package may start when its dependencies are merged)
Wave 1: P0a, P0c. Wave 2: P0d, P0e, P0f. Wave 3: P0b. Wave 4: P1, P3a. Wave 5: P2a, P2d, P4a, P4d, P5a (laptop limit: one money + one redaction/security package at a time; the cloud may run these in parallel branches if their file lists do not overlap). Wave 6: P4b, P5b1. Then P4c, P5b2-P5b6, P6b. Then P5c, P6a. Then P8a, P8b, P8c. v1.1 packages only after P8c, in the order of their triggers.
Reason PR #50 slices come before PR #48: #50 merges cleanly today; #48 conflicts in 15 files including `llm/common`, `config`, `extract`, `ci.yml` and `pyproject`, and sits on shapes P4a changes, so rebuilding it after P4a avoids doing it twice.

## 7. Money-base rule (P0e step 2)
Checklist: atomic reservation across processes (test with N processes, not only N threads); integers only; micro-USD means millionths of a dollar for amounts, and prices are stored per million tokens as integers; round up per token class and then sum; worst-case reserve; missing usage settles at the reserved worst case; release in `finally`; expiry sweep; settle is idempotent; clock-back refusal uses a monotonic clock; one counter shared with `limits.py`; memory backend only in dev/test profiles (enforced by P6a); spend and business money are separate types; parity with Intake `budget.py` on shared fixtures; bible rules R110, R214, R215, R278-R292, R335 cited. The winner is the candidate that passes the most checks; ties go to fewer files and one durable backend; the owner is told if the winner is not PR #48.

## 8. Done conditions and how each is checked (run on the laptop after the cloud work)
| Condition | Command or check | Expected | Evidence path |
|---|---|---|---|
| Needed pull requests merged in wave order | `gh pr list --state merged` and `git log --first-parent main` | every v1 package has a merge commit | `egm/hadavin-sdk/core-complete/merged.md` |
| Redaction before the model | test `tests/test_c1_acceptance.py`: made-up PII document reaches the fake model only masked; redactor error -> NEEDS_PERSON with 0 model calls; restored values appear only in the proposal | passes; fails on ce70eb5 | `evidence-c1.md` |
| Diagnostics redesign | the hostile corpus test over every ledger row of C18a | passes | `evidence-r5.md` |
| Money chain | N-process race test at the cap; missing-usage test; parity test with Intake | passes | `evidence-p4b.md` |
| Client-profile gates | `tests/test_client_profile.py` | passes | `evidence-p6.md` |
| No unresolved findings | `python egm/tools/ledger_check.py --topic core` | exit 0 (WAIVED rows listed by id in the report) | `ledger-check.txt` |
| Demos re-pinned | `check_core_copies` in each demo repo | 0 drift | `repin.md` |
| Proof pack | `python tools/proof_pack.py` | exit 0 | `proofpack.txt` |
| Drift | `egm:egm-drift-report` | no open drift | `drift.md` |
Rollback: tag main before each merge (`pre-<package>`); one pull request per package; old branches stay until the replacement passes; semantic changes (FOLD_VERSION, price units, REGEX_VERSION 4) are marked non-revertible and carry a test that old code reading new data fails loudly.
Estimates: none until S0 exits. After S0 the lead reports per step the package count, review rounds seen, and wall-clock days, and re-measures every report. There is no hour column on purpose: the earlier guess counted builder time only and misled.

## 9. Questions and defaults (owner)
| Question | Why it matters | Default | If unanswered |
|---|---|---|---|
| Is refunds the first client? | decides whether PR #49 reservations become the durable meter | no | the default stands from the end of S0 |
| Portal kit: separate package or core module? | affects v1.1 only | separate package pinned like a core copy | default stands |
| Copy the killswitch package? | avoids a fourth stop design | no: absorbed into the stop-state module | default stands |
| Live model calls? | costs money | none in this plan; the US$189 demo-test budget is separate and needs the owner's yes with numbers | none happen |
Decided by the owner on 2026-11-05: full core is wanted (with the v1 line above as first milestone); public repo is used for the handover; at the end only the branch main may exist.

## 10. Alternatives rejected
One flat "do everything" order (no stop line). Merge #48 first (rebuilt twice). Keep three money designs (two spend counters = a money bug). Copy the killswitch package (a fourth stop design). Promote all of Warden (no consumer). Fix batch 6 of the old C18a design (owner replaced it).

## 11. Open risks
Planners did not read function bodies. KERNEL-1 and C1f are not read. S0 may find reviews missing for #41, #43, #47, #48, #49. Cloud sessions may claim "done" without evidence: the laptop re-verifies (section 8). The repo is public: nothing private may be committed there (secret scan before every push).
