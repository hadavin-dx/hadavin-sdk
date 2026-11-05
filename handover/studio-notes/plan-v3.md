# Core completion plan v3 (hadavin-sdk)

Author: Hadavin lead session, for the owner. Date: 2026-11-05 (UTC; IST = UTC+5:30).
Status: DRAFT for plan review round 3, the LAST allowed round. After it the plan is frozen: only a written amendment can change it.
Replaces plan-v2.md. Answers review-plan-2.md (5 blockers B1-B5, 22 majors M1-M22) and review-plan-1.md.
How reliable are the facts here? File-level claims come from the inventories and `s0-merge-probe.md` (a dry-run merge of every branch against origin/main `ce70eb5`). The planners did not read function bodies. Part S0 re-measures before anything is built.

## Contents
1 Terms. 2 Goal and the two milestones. 3 Who does what (laptop and cloud). 4 Rules for every package. 5 Kinds in v1. 6 Packages (one table). 7 Start order. 8 Money-base rule. 9 Done conditions. 10 Rollback and re-pin. 11 Owner questions. 12 Rejected ideas. 13 Open risks.

## 1. Terms (read first)
| Term | Meaning |
|---|---|
| the core | the GitHub repo `hadavin-sdk` (Python package `hadavin_sdk`): the shared code every Hadavin build starts from |
| a kind | a replaceable part with a fixed interface, a default and an alternative, chosen by configuration (example: the redactor kind) |
| the lead | the Claude session on the owner's laptop that coordinates, verifies and merges |
| the cloud session | a Claude session in the cloud with many agents that does the bulk coding; it opens pull requests and never merges |
| EGM | the review method used by the studio (plugin `egm@egm`): ticket review, build, evidence, two independent reviews, resolve, repeat |
| a reviewer pass ("round") | one review of a package by two fresh reviewers (one checks correctness, one attacks it) who read only the change, the ticket and the evidence |
| a fix batch | one set of changes that answers one round |
| a clean round | a round with no blocker and no major finding. Blocker = must be fixed before merge. Major = real defect, must be fixed before merge. Minor = fix in the same batch, no new round needed |
| Tier A / Tier B | review depth, see section 4 rule 3 |
| evidence | raw test, mutation and hostile-input output saved in a file; a separate runner produces it and does not judge it |
| mutation run | the tests are run against deliberately broken copies of the code; a "survivor" means a weak test |
| fail-before test | a test that fails on the old code and passes on the fix |
| ledger | the table of every blocker and major finding with its status (`egm/BLOCKER-LEDGER.md` on the laptop; `handover/ledger.md` in the cloud) |
| WAIVED | a ledger status meaning the owner accepted a finding in writing; the waiver id is listed in the final report |
| snapshot diff | the change under review saved as a fixed file |
| re-pin | point a demo's copied core files at a newer core commit |
| `check_core_copies` | the script in each demo repo that compares its copied core files with the core |
| proof pack | the script `tools/proof_pack.py` that runs each v1 kind on made-up data with the fake model |
| fake model | a built-in stand-in that returns fixed answers; no paid model call |
| personal data | names, account numbers, e-mail addresses and similar (the plan never uses the abbreviation "PII") |
| P-ids | packages in section 6 |
| C-ids | packages of the earlier course re-read, file `handover/studio-notes/WORK-PACKAGES.md` (C1, C2, C17 ...) |
| R-ids | packages of the frozen diagnostics redesign in `design-v3.md` (R1, R1P, R3a, R3b, R3c, R2, R5): they remove personal data from error messages and logs |
| KERNEL-1 | the "pilot kernel" package described in `core-v5-pilot-kernel.md`; P0e reads it and either joins it to a v1 package or moves it to v1.1 by written amendment |
| PR numbers | #41 K6 measurement; #43 ask-your-data gaps; #47 ask-your-data export adapter; #48 hardening (extract leaks, spend-cap 429, reserve/settle); #49 promoted refunds fixes; #50 promoted apexc fixes (text folding, stop gate, row store, egress text, mutation runner, redact patterns) |
| commits | `ce70eb5` = current core main (PR #42 merged 2026-11-04); `6608146` = the older commit the demos are pinned to (apexc and refunds: an even older one); `748849c` = the local, unpushed head of PR #50; `8460813` = the C1a branch head |
| review ids | B/M/m in review reports are finding numbers of those reports, not ledger ids; ledger ids look like `BL-core-...` |

## 2. Goal and milestones
Problem: reusable code is spread over unmerged branches, demo repos and Warden/Jagrat; demos hold byte copies of the core pinned to an old commit; three "reserve then settle" money designs and several text-folding versions exist; the redaction redesign (masking personal data before a model or a log sees it) is unbuilt.
Goal: a core from which a new agent project starts in hours: each capability exists once, behind one kind, with tests that fail on old code.
Out of scope: the multi-document matching module; portal redesign; any paid model call; deleting old branches before their replacement passes; autonomy levels; passkeys; edge authentication; MCP schemas; payload codec; Temporal runtime; name index; a copy of the killswitch package; Helios. Each is deferred until a named consumer exists.

**Core v1 (ready for a first client's build).** The v1 packages are exactly: P0a, P0c, P0d, P0e, P0b, P1, P2a, P2d, P3a, P4a, P4d, P4b, P4c, P5a, P5b1, P5b2, P5b3, P5b4, P5b5, P5c, P6a, P6b, P8a, P8b, P8c. Core v1 is done when every row of section 9 passes. v1 permits building and demo runs; no pilot or production configuration until the eval-gate package P7f (C9) is done.
**v1.1:** everything else, started only on its trigger (section 6, second table). v1 is the owner's choice of scope; the recorded decision is "full core wanted, v1 first" (2026-11-05).

## 3. Who does what
* **Laptop (the lead):** S0 measurements that need local worktrees; verification of every cloud pull request before it merges (re-run the package evidence command at the merge commit, read the review files, check the plan's rules); the ledger; merges; the re-pin of demos; the final checks of section 9. The lead compares cloud work with the studio's full rule book (the "bible"), which stays on the laptop except for a rule-only copy shipped in the handover folder.
* **Cloud session:** all bulk work in the order of section 7. One pull request per row of section 6 unless the row says "N PRs". Each pull request title starts with the P-id. Each review is committed on the pull request branch as `reviews/<P-id>-round<n>.md` with the reviewer role, the diff commit, the ticket commit and the reviewed commit. If EGM is not available in the cloud, Tier A rows are built and reviewed by fresh agents given the reviewer role text from `handover/` and only the diff, the ticket and the evidence; the lead then repeats the Tier A review on the laptop with the real EGM reviewers before merging.
* **Findings:** the cloud keeps `handover/ledger.md`; the lead copies open rows into the laptop ledger when it verifies a pull request.
* **Limits:** at most 3 cloud pull requests wait for the lead at one time. The lead verifies at most one money pull request and one redaction/security pull request at a time.
* **Handover folder:** branch `core/cloud-handover` carries `handover/` (prompt, rules, ticket template, copied code, plan, notes). The ticket template is `handover/TICKET-TEMPLATE.md`; the plan copy is `handover/studio-notes/plan-v3.md`.

## 4. Rules for every package
1. **Ticket first**, from the ticket template. Tier A tickets are reviewed by `egm:egm-review-loop` before building; Tier B tickets are reviewed by the template checklist only.
2. **Order:** ticket, build by one builder, evidence by a separate runner (raw output saved as `evidence/<P-id>-<n>.md`; mutation summary read row by row), review, ledger, resolve, repeat, lead verification, squash merge by the lead.
3. **Review depth.** *Tier A* = money, redaction, stop state, text folding, signed paths, client-profile gates, store: two reviewers per round (correctness and adversarial), no round cap; the stop rule below applies; after round 5 the package escalates to the lead in writing (the lead may waive a finding with a written reason, split the package or retire it; work continues on other rows meanwhile). *Tier B* = everything else: one fresh reviewer, one round, at most 2 fix batches, green CI.
4. **Stop rule (Tier A).** The package is clean when two rounds in a row, both done at the final commit, find no blocker and no major, and evidence at that commit is green. The final commit id is written in the ledger. "Changed code" means files in the pull request diff, not evidence or ledger files.
5. **Fail-before:** every fix and guard has a test that fails on the old code (the failing run is pasted into the evidence file).
6. **One pull request per row** unless the row says "N PRs". Merge only after review, evidence, CI, CodeQL, SonarCloud and CodeRabbit are green and the lead has verified.
7. **Promote** = rewrite behind a core kind with names stripped (Warden, Eldane, Helios, Jagrat, Apexc, vendor-inspired names). Reuse first: `hashing.py`, `k1b/atomic.py`, `k1b/redaction.py`, `stats.py`, `evals.py`, `store/memory.py`, `askdata/meter.py`, `tests/contracts/`.
8. **Single dependency:** every kind has a default and a working alternative, or a written outline with a named trigger. A test double is not an alternative.
9. **Least privilege, and how it is enforced:** (a) main is protected (required checks, only the lead merges, no force-push, no deletion); (b) tags `pre-*` and release tags are created only by the lead; (c) the cloud token is fine-grained: write to non-main branches and pull requests only, no admin, no workflow or secret scope, expiry within 30 days; (d) CI runs with read-only permission, no secrets, no network for tests; (e) a lint rule bans `os.environ` and `os.getenv` outside the secrets kind and an import test keeps secret reads inside the executor package; (f) every kind declares `identity` and `rights` and a contract test fails when they are empty; (g) every kind that exists at v1 carries a `dev_only` flag from the package that adds it; (h) a CI job scans every push for secrets and for banned names (vendor-inspired product names, client and demo names) because the repo is public. P0a sets up (a)-(d) and (h) and records the owner's approval for the cloud pushes (owner, 2026-11-05).
10. **Hot files** (`limits.py`, `store/memory.py`, `store/migrate.py`, `config.py`, `registry.py`, `CHANGELOG.md`) are changed in this order: P3a, P4d, P4a, P4b. `CHANGELOG.md` is append-only per package; the lead resolves conflicts. P0e writes a file-overlap table per ticket; two packages that change the same file are never in progress together.
11. **Rebase rule:** after a rebase, reviewers read the range-diff and evidence is rerun in full; a ledger row is carried only if its files are untouched by the conflict set.
12. **Dependabot bumps** (#51-#56) may be merged without the full process when CI, the lock-in guard and the full suite are green and no new transitive dependency appears; major bumps (pytest 9, sqlglot 30) first rerun the migration-regex and SQL parser tests.

## 5. Kinds in v1 (single-dependency check; "claim" means P0e must confirm it in code)
| Kind | Default | Alternative or outline with trigger | Where |
|---|---|---|---|
| textnorm | built-in fold | outline: ICU fold; trigger: a client language the standard tables mishandle | P1 |
| stop_state | store-backed | outline: hosted killswitch adapter; trigger: a client asks | P2a |
| usage | five-class dataclass | outline: provider-specific usage adapters are inside the llm kind | P4a |
| store | Postgres | memory (dev/test only); outline: SQLite; trigger: Intake moves onto the core meter | P4d |
| meter | store-backed reserve/settle | the second durable backend comes with the SQLite outline | P4b |
| diagnostic | closed codes and locators | none needed: it is a rendering rule, not an external dependency | P5a-P5b5 |
| redactor | pattern-based `guard.redact` | outline: detector-model backend; trigger: a client document type the patterns miss | P5c |
| llm | claim: Anthropic default, other backends exist or are outlined | P0e confirms; if missing, an outline with trigger is added to P6b | already in core |
| secrets | claim: environment/file default and a managed-secret alternative | P0e confirms | already in core |
| signer, channel, executor | claim: exist with one or two backends | P0e confirms; gaps become outlines in the s0-report | already in core |

## 6. Packages
Columns: Id | Step or lane | What (one sentence; numbered notes below the table) | Depends on | Tier | Consumers | Milestone.
| Id | Step / lane | What | Depends on | Tier | Consumers | Milestone |
|---|---|---|---|---|---|---|
| P0a | S0 | Back up unpushed work (push local PR #50 head and C1a head as branches), set the push model of rule 9 (a)-(d), (h), check the core repo for third-party files and notice duties (note 1) | none | B | none | v1 |
| P0c | S0 | Measure every branch and PR against ce70eb5 and write `s0-report.md`; includes the slot count and the answer to "is refunds the first client" (note 2) | none | B | none | v1 |
| P0d | S0 | Repair the ledger tooling: WAIVED status, topic rule, raw-newline lint `egm/tools/ledger_lint.py`, tests; give each superseded redesign-predecessor row a disposition; give the rest of PR #50 a disposition (note 3) | P0c | B | none | v1 |
| P0e | S0 | Write the decision memos: text folding base, money base, store note, migration plan, file-overlap table, KERNEL-1 placement; also confirm the kinds marked "claim" in section 5 (note 4) | P0c | B | none | v1 |
| P0b | S0 | Merge the Dependabot batch (rule 12) and then re-run the conflict and test columns of `s0-report.md` | P0c, P0d, P0e | B | none | v1 |
| P1 | S1 | Move the text-folding code out of PR #50 into one small pull request with named views and a stored version | P0e | A | all demos | v1 |
| P3a | S3 | Add the migration rule: renumber in merge order, forward-only, CI fails on duplicate or out-of-order numbers; includes a test that the previous release code reads the new schema or fails loudly | P0e | B | all | v1 |
| P2a | S2 | Turn PR #50's stop gate, row store and config view into one stop-state module with audited reset; first fix PR #50's failing test and weak mutant row (3 PRs: gate, row store, config view) | P1 | A | apexc, dealdesk, refunds, jagrat | v1 |
| P2d | S2 | Land PR #50's change to `guard/redact.py` | P1 | A | all | v1 |
| P4d | M | Add one contract test suite for the store over memory and Postgres and keep the database library inside the store kind (note 5) | P3a, P0e | A | all | v1 |
| P4a | M | Refuse instead of estimate (C2), five-class usage (C3), price tiers by prompt length (C4a) (3 PRs) | P0e, P4d | A | Intake, askdata | v1 |
| P6b | M | Add the no-training lock inside the llm kind and an import test that only the executor reads secrets | P4a | A | Intake, askdata | v1 |
| P4b | M | Build the one reserve/settle meter chosen by section 8, sharing one counter with `limits.py` (note 6) | P4a, P4d | A | Intake, askdata, refunds | v1 |
| P4c | M | Enforce `AgentRecord.max_run_usd` on the run path and add the loud-wall alert at the daily limit | P4b | A | Intake | v1 |
| P5a | R | Redesign step R1: closed error codes, safe diagnostic text and the hostile test corpus, rebuilt on ce70eb5 | P0d, P1 | A | all | v1 |
| P5b1 | R | Redesign step R1P | P5a | A | all | v1 |
| P5b2 | R | Redesign step R3a | P5b1 | A | all | v1 |
| P5b3 | R | Redesign steps R3c and R3b (one pull request, as in the frozen design) | P5b2 | A | all | v1 |
| P5b4 | R | Redesign step R2 | P5b3 | A | all | v1 |
| P5b5 | R | Redesign step R5 | P5b4 | A | all | v1 |
| P5c | R | Redactor kind and masked model wrapper (C1a-C1d) plus put-back (C1f): mask the document before the model, no model call after a redactor error, restore values in code (note 7) (4 PRs) | P2d, P5b5 | A | Intake, all | v1 |
| P6a | S4 | Turn on the client-profile check: dev-only kinds refused; the llm kind refused unless the redactor kind is selected; CI test that no code path in `src/` calls the llm kind except through the masking wrapper | P4b, P5c | A | all | v1 |
| P8a | S5 | Tag each demo repo `pre-repin`, then re-pin each demo once to the final core commit and make each demo's own tests pass | all other v1 rows | B | all demos | v1 |
| P8b | S5 | Write one README per kind, run the drift report and the ledger check | P8a | B | none | v1 |
| P8c | S5 | Write and run `tools/proof_pack.py` | P8a | B | none | v1 |

Numbered notes
1. P0a pass criterion: a text file listing every third-party file or notice duty found, or "none".
2. P0c rules: merge a branch only if it has 0 conflict files and the full suite passes (command: `uv run --all-extras --group test pytest` on Python 3.12 and 3.13; failures already present on ce70eb5 are listed, not hidden); rebase if it has at most 5 conflict files and shares no file with another row of `s0-report.md`; anything else is split or retired by the lead with a written reason. Retiring needs a ledger disposition per open row. The merge probe is re-run, not trusted. The S0 exit = P0a, P0c, P0d, P0e, P0b finished and `s0-report.md` carries a verdict for every row, the first measured package and round counts, the file-overlap table and the answer on refunds.
3. P0d also adds a name scan to the CI job of rule 9 (h).
4. P0e memo items: (1) text folding: run every demo's version against all demo fixtures plus an attack corpus; the base must be a superset; (2) money: apply section 8; the memo covers both answers on "refunds first client"; (3) store: reservations, inbox, queue and tenant namespace over memory and Postgres; (4) migration plan, including whether any demo database ever ran a branch-numbered migration 0005; (5) file-overlap table; (6) KERNEL-1.
5. P4d facts: the files that import the database library are `store/migrate.py`, `store/postgres.py` and `demos/ask-your-data/askdata/pgsource.py`; `store/protocol.py` and `runtime/tick.py` only mention its name, so they need a name-string check. Tests touching it: `test_p2_postgres`, `test_k2_migrations`, `test_migrate_regex_linear`, `tests/contracts/kinds/store_postgres.py`; `test_lockin_guard` has an allow-list (line 67) that P4d updates. SQLite is v1.1.
6. P4b: spend is integer millionths of a dollar; prices are integers per million tokens; the in-memory backend is dev/test only and P6a refuses it in a client profile; the extras of PR #48 (extract leaks, spend-cap 429) are separate pull requests after P4b. Reuse `askdata/meter.py`.
7. P5c includes decisions already taken: the wording of rule F10, a sixth error code `session_closed`, and REGEX_VERSION 4.

Second table: v1.1 packages (each starts only on its trigger)
| Id | What | Trigger | Tier |
|---|---|---|---|
| P2b | egress text check from PR #50 | a second consumer | A |
| P2c | mutation-runner cleanup (Intake's killed/crashed split, remove duplicates) | before the next mutation-heavy package | B |
| P3b | PR #49 rebase onto the new base (signed approvals, reply check, identity text, outbox; reservations only if refunds is the first client). Known conflict surface with #50: `guard/textnorm.py`, `limits.py`, `store/memory.py`, `tests/contracts/test_store.py`, `tests/test_k2_migrations.py`, `tests/test_p2_postgres.py`, `CHANGELOG.md`; depends on P1, P2a, P3a | a client needs signed approvals | A |
| P3c | PR #41 (measurement, demotion) rebase; depends on P3a and P4d (it conflicts in store files and `runtime/tick.py`) | first pilot | B |
| P3d | PR #43 and #47 (ask-your-data) | that demo is shown | B |
| P4e | per-call log sink (JSONL default; outline: OpenTelemetry, trigger: a client uses it) | after P4b | B |
| P7a | inbound message ledger with one terminal state for a reused message id | second consumer | A |
| P7b | tenant namespace, rate cap, read log, data-source loader, test helpers | second consumer | B |
| P7c | least-privilege authorize/requires extension | second consumer | A |
| P7d | canonical JSON ASCII option (default unchanged); signer split | signatures needed | A |
| P7e | money parsing in minor units (reconcile negative amounts) | refunds or an invoice export | A |
| P7f | eval gate buckets (C9) and eval core | before any pilot or production configuration | B |
| P7g | hygiene batch (C18b) and cheap duplicate removals | with a pull request touching the file | B |
| P7h | Jagrat/Warden batch A: numbers check, evidence ids, grounding, language detect, freeze windows, safe path, confidence labels | a consumer names one | B |
| P7i | batch B: breaker, target lock, landed check, environment policy | Jagrat needs it | A |
| P7j | batch C: quarantine, vault, webhook and read scope | Intake's untrusted path names it | A |
| P7k | scan, work queue, approval service and payment-detail checks as a core kind | those lanes' own reviews close | A |
| P7l | SQLite store, second channel, second executor | triggers in section 5 | A |
Each v1.1 package that changes files copied into demos includes its own re-pin (section 10).
Course packages: C1, C1a-d, C1f in P5c; C2, C3, C4a in P4a; C5 in P4c and the Intake lane; C6 in P4e; C8 in P4c; C9 in P7f; C17 in P4b; C18a in P5a-P5b5; C18b in P7g; C4b, C7, C10-C16 are Intake or bible work; C19-C22 are lead work.
If S0 shows the work exceeds the owner's review budget, v1 is cut in this order: P5b2-P5b5 (only with the owner's written yes), P4c, P3a, P6b.

## 7. Start order (derived from the Depends-on column)
1. P0a, P0c.
2. P0d, P0e.
3. P0b.
4. P1 and P3a.
5. In this order: P2a and P4d; then P4a, P2d and P5a; P6b starts as soon as P4a is merged.
6. P4b and P5b1; then P4c, P5b2, P5b3, P5b4, P5b5.
7. P5c, then P6a.
8. P8a, then P8b and P8c.
9. v1.1 packages in the order of their triggers.
The cloud may work on rows of step 5 in parallel branches if their file lists do not overlap (rule 10); the lead's verification limit in section 3 is the real brake.
Why PR #50's pieces go before #48: #50 merges cleanly today; #48 conflicts in 15 files (including `llm/common`, `config`, `extract`, `ci.yml`, `pyproject`) and sits on shapes P4a changes, so rebuilding it after P4a avoids doing it twice.

## 8. Money-base rule (decides P4b's starting code)
Candidates, tried in this order: PR #48 `llm/metered.py`, then `askdata/meter.py`; the others (PR #49 reservations, Intake `budget.py`) only if both fail a gate.
Gates (a candidate failing any gate is out): (1) with 8 separate processes against Postgres, total reserved spend never exceeds the cap by more than one worst-case call; (2) integers only; (3) missing usage settles at the reserved worst case; (4) settle is idempotent; (5) release happens in a `finally` block; (6) one counter shared with `limits.py`.
Scored items among survivors: expiry sweep; monotonic clock for clock-back refusal; rounding up per token class then summing; spend and business money as separate types; parity with Intake `budget.py` on shared fixtures. Tie-break: fewer files, then one durable backend. If no candidate survives, build from the best one and make its gap list the ticket. The owner is told if the winner is not PR #48.

## 9. Done conditions (checked by the lead after the cloud work; each command names the repo)
| Condition | Created by | Repo and full command | Expected result | Evidence file |
|---|---|---|---|---|
| Every v1 code row merged | each row | core: `git log --first-parent main --oneline` and `gh pr list --state merged`; every PR title starts with its P-id | one merge per code row (P0*, P8* are reports and tags, listed separately) | `merged.md` |
| Text folding | P1 | core: `uv run --all-extras --group test pytest tests/test_textnorm_differential.py`; and the same test on ce70eb5 (`git stash`-free: run in a throwaway worktree at ce70eb5) | passes at the merge commit, fails at ce70eb5 | `evidence-p1.md` |
| Stop state | P2a | core: `pytest tests/test_stop_state*.py` | passes; the weak-mutant row is killed | `evidence-p2a.md` |
| Migration rule | P3a | core: `pytest tests/test_migration_numbers.py` | passes; fails with a duplicated number | `evidence-p3a.md` |
| Store contract | P4d | core: `pytest tests/contracts/` | passes on memory and Postgres | `evidence-p4d.md` |
| Money chain | P4a-P4c | core: `pytest tests/test_usage*.py tests/test_meter*.py tests/test_run_cap.py` including the 8-process race test | passes | `evidence-money.md` |
| No-training lock and secrets reads | P6b | core: `pytest tests/test_training_lock.py tests/test_secrets_import.py` | passes | `evidence-p6b.md` |
| Redaction before the model | P5c | core: `pytest tests/test_c1_acceptance.py`: a made-up document with personal data reaches the fake model only masked; a redactor error stops the run with zero model calls; restored values appear only in the proposal | passes; fails at ce70eb5 | `evidence-c1.md` |
| Diagnostics redesign | P5a-P5b5 | core: `pytest tests/test_diagnostics_hostile.py` (one input per ledger row of the earlier design) | passes | `evidence-r.md` |
| Client profile | P6a | core: `pytest tests/test_client_profile.py` | passes | `evidence-p6a.md` |
| No unresolved findings | P0d | studio repo: `python egm/tools/ledger_check.py --topic core` and `python egm/tools/ledger_lint.py` | both exit 0; WAIVED rows listed by id | `ledger-check.txt` |
| Demos re-pinned | P8a | each demo repo: `python tools/check_core_copies.py` (or the path P0e records) and the demo's own full test suite | 0 drift, suite green | `repin.md` |
| Proof pack | P8c | core: `python tools/proof_pack.py` | exit 0 | `proofpack.txt` |
| Drift | P8b | studio repo: `egm:egm-drift-report` | no open drift | `drift.md` |
All test files named above are created by the package in column 2 as part of its fail-before work; if a package names its test file differently, P8b updates this table.

## 10. Rollback and re-pin
Before each merge the lead tags main `pre-<P-id>`. Migrations are forward-only; each includes the downgrade-read test of P3a. Semantic changes (text-folding version, price units, REGEX_VERSION 4) are marked non-revertible and carry a test that old code reading new data fails loudly. Old branches stay until their replacement passes. Each demo repo gets a `pre-repin` tag before P8a. After v1, any package that changes files copied into demos re-pins them in the same package.
Estimates: none until S0 exits. After S0 the lead reports per step the package count, rounds seen, wall-clock days; the plan has no hour column on purpose.

## 11. Owner questions (defaults apply if unanswered)
| Question | Why it matters | Lead default |
|---|---|---|
| Is refunds the first client? | decides whether PR #49 reservations become the meter's durable backend | no |
| Portal kit: separate package or core module? | affects v1.1 only | separate package pinned like a core copy |
| Copy the killswitch package? | avoids a fourth stop design | no: absorbed into stop_state |
| Publish the extra private Warden code? | Warden is a private repo; the public Jagrat repo is its trimmed copy | not published until the owner says so |
| Review budget | Tier A rows are many | owner is asked once after S0, with measured numbers |
Decided on 2026-11-05: full core wanted with v1 first; the public core repo is used for the handover; at the end only the branch main exists (the lead merges, then deletes all other branches and the `handover/` folder); the diagnostics redesign R1-R5 stays in v1 (owner said yes).

## 12. Rejected ideas
One flat "do everything" order (no stop line). Merging #48 first (rebuilt twice). Keeping three money designs (two spend counters). Copying the killswitch package (a fourth stop design). Promoting all of Warden (no consumer). Repair batch 6 of the old redaction design (replaced on the owner's yes).

## 13. Open risks
Planners did not read function bodies; S0 corrects the plan once by amendment. The repo is public, so nothing private may be committed; CI scans each push. Cloud sessions may claim done without proof; the lead re-runs evidence before every merge. The number of Tier A rows is large for one person to verify; the lead verifies one money and one redaction/security row at a time.
