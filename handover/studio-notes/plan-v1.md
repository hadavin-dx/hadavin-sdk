# Core completion plan v1 (hadavin-sdk)

* **Author:** Hadavin lead session, for owner Veera Rakesh Kethari
* **Date:** 2026-11-05 (UTC; IST = UTC+5:30)
* **Status:** DRAFT for plan review round 1 of max 3, then FREEZE. Replaces concepts_brief.md. Answers review-brainstorm-1.md (7 BLOCKER, 17 MAJOR; finding ids B1-B7, M1-M17, m1-m11 are cited as [B1] etc.).
* **Inputs:** concepts_brief.md, review-brainstorm-1.md, s0-merge-probe.md, inventory.md and inventory-A..D.md, handoff/CORE-FIRST-MISSION-2026-11-05.md, egm/course-reread/pass2/WORK-PACKAGES.md, egm/hadavin-sdk/c18a-redesign/design-v3.md + design-v3-FROZEN-amendments.md, core-and-portal-v4.md, core-v5-pilot-kernel.md, core-only-amendment.md, core-hardening-1/, core-sync-check/.
* **Honesty note:** every file-level claim comes from inventories (docstrings, file names, git probes). Function bodies were not read by the planners. S0 re-measures before anything is built [M11]. No total effort or date is promised before S0 exits [M5].

## 1. The problem (plain words)

Hadavin sells fixed-price AI builds. After the first client, the core repo is the proof of what Hadavin can do. Today the best shared code is spread over unmerged branches, demo repos and Warden. Demos do not import the core; they hold byte copies pinned to an old commit (6608146), and the core's main moved to ce70eb5 on 2026-11-04. Three "reserve then settle" money designs and at least three versions of the text-folding code exist. The redaction work (the biggest safety item) is stuck in a branch whose design the owner replaced on 2026-11-05.

## 2. Goals, Core v1 line, non-goals

**Two milestones in one plan (owner mission says full core; reviewers say mark a stop line [B4]):**

* **Core v1 = ready for a first client's build.** Done when ALL hold:
  1. the open PR set that v1 needs is merged on the new main in the order of section 5;
  2. redaction before the model is closed: C1 (document masked before the model, restore in code) plus the frozen C18a diagnostics redesign R1-R5 merged;
  3. the money chain is merged: five-class Usage, price tiers, one reserve/settle meter, run cap, loud wall alert (C2, C3, C4a, C17, C8, C5-core);
  4. client-profile safety gates exist (section 6, M14 list);
  5. every demo re-pinned to the new core commit, `check_core_copies` green, `python egm\tools\ledger_check.py --topic core` passes (zero unresolved BLOCKER/MAJOR, or an owner waiver written in the ledger);
  6. a thin proof pack (each v1 kind run on made-up data with the fake LLM; no model call, no real names).
* **v1.1 = everything else**, each package started only on a named need (a client, or a second demo consuming it) and each with a one-page outline and trigger if not built (allowed by the no-single-dependency rule). Section 4 marks every package v1 or v1.1.

**Non-goals:** the multi-document matching module (parked until partner discovery says what to build); portal UI redesign; any live model call or spend (none in this plan; budget US$189 stays for demo tests); deleting old branches before their replacement passes; autonomy levels (B3), passkeys (B11), edge_auth (B12), MCP schemas (B15), payload codec (B17), Temporal runtime (G1), the nameindex, the agent-killswitch package copy, Helios [M6]. Each is "deferred with trigger": built only when a named consumer exists.

## 3. Method rules for every package (apply once, listed here only)

* Order per package: package ticket reviewed by `egm:egm-review-loop` (small) or `egm:egm-review` (big) -> build (one builder, Sonnet 5.5) -> LEAD EVIDENCE (raw output in `egm\hadavin-sdk\core-complete\<pkg>\evidence-<n>.md`; mutant summary lines read by row, not pass counts) -> two independent `egm:*` reviewers (correctness `egm:egm-codebase-details`, adversarial `egm:egm-design`) on a snapshot diff -> findings into `egm\BLOCKER-LEDGER.md` the same turn (row carries the reviewed sha [M10]) -> `egm:egm-resolve` -> one fix batch -> repeat.
* **Stop rule [M9]:** a package is clean when TWO consecutive rounds from independent reviewers add no new BLOCKER/MAJOR AND lead evidence at the final head is green. Uncapped packages (money, all redaction, signed approvals, canonical JSON, stop state, quarantine/vault/webhook) escalate to the owner after round 5 with a written reason; the other packages cap at 2 rounds. Uncapped applies to new or changed code, not to unchanged code carried through a rebase.
* **FAIL-BEFORE:** every fix and every new guard has a test that fails on the old code (proof saved in the evidence file) [M16].
* **One PR per package** so a revert is one commit [m3]. The lead merges (squash, pinned to the reviewed sha) only after review + EGM + CI + CodeQL + SonarCloud + CodeRabbit are green. Builders never push to main or merge.
* **Promote = rewrite behind a core Protocol, names stripped** (Warden, Eldane, Helios, Jagrat, Apexc); verbatim copy only with the Apache-2.0 header/NOTICE; `test_lockin_guard` and `test_no_reference_material` stay green [m4]. Check reuse first: `hashing.py`, `k1b/atomic.py`, `stats.py`, `evals.py`, `store/memory.py` [m5]. Each promoted module names one consuming demo and one source branch [M6, m10].
* **Nothing is promoted from a demo lane until that lane's own result review is closed** (zero open BLOCKER/MAJOR rows for its topic) [B7]. Intake lanes WP3, 6b, 6d, A12 are open, so scan/workqueue/payment-check promotion is v1.1 and waits.
* **Rebase rule [M10]:** after a rebase, reviewers review the range-diff and the evidence is rerun in full. A ledger row is carried only if its files are untouched by the conflict set; otherwise it is re-reviewed.
* **Capacity [M8]:** at most 3 builders and 2 reviewer pairs at once; at most 2 uncapped packages at once. Heavy jobs only through `tools\heavy_slot.py` (S0 confirms the real slot count; sources disagree: 3 vs 5). Never run evidence on a worktree a builder is editing. S0 agents are read-only (no push, no merge); only the lead merges.
* Reports, evidence and snapshots live in `egm\hadavin-sdk\core-complete\`, never in `projects\`.

## 4. Work-package table

Columns: Id | scope | depends on | milestone | kind: interface / neutral default / alternative | consuming demos | evidence and reviewers | uncapped | slots | builder-hours (UNMEASURED guess, no total).
"Rev" = two egm:* reviewers. "HS" = heavy-slot use (L low = lint/unit, M medium = full suite, H high = full suite + mutants + Linux Docker).

### Step S0: measure, back up, decide (no other step starts before S0 exits) [B3]
| Id | Scope | Dep | Ms | Evidence / reviewers | Unc | HS | h |
|---|---|---|---|---|---|---|---|
| P0a | Push the unpushed local PR #50 head 748849c (6 commits) to a backup branch on the remote (lead pushes; this is the only S0 push); grep core repo for third-party files/NOTICE obligations (licence check, D-licence) | - | v1 | lead; one grep output saved | n | L | 0.5 |
| P0b | Dependabot #51-#56: merge green, non-major bumps once as a batch (exemption from review-before-merge, written here); majors (pytest 9.x, sqlglot 30.x) first rerun the migration-regex and SQL parser tests | - | v1 | lead; CI green | n | M | 1-2 |
| P0c | `s0-report.md`: one row per branch/PR (#41,#43,#47,#48,#49,#50-pushed,#50-local,C18a-old,C1a): true diff size vs ce70eb5 (reuse s0-merge-probe.md), conflict files, test result on a clean THROWAWAY worktree off ce70eb5 (never the live worktrees pr50b3-wt, core-c18a, core-c1a), `gh pr checks` state, verdict (merge / rebase / split / retire) with fixed rules: merge only if clean and tests pass; rebase if few conflicts; split on file collision; retire only with a per-row ledger disposition | - | v1 | 2 read-only research agents, lead checks 2 rows by hand | n | M | 3-5 |
| P0d | Ledger: re-run `ledger_check` (done once 2026-11-05: parses, 83 unresolved); re-count by topic; map #49's 31 `BL-demos-refunds-*` rows and #41's k6 review to their PRs; re-topic #41/#43/#47/#48/#49 rows as `BL-core-*`; C18a-old rows get a per-row disposition (carried to the redesign hostile corpus / obsolete with reason / fixed elsewhere); add a ledger lint that rejects raw newlines in a row; define passing = zero unresolved BLOCKER/MAJOR or a written owner waiver [B5] | P0c | v1 | lead; script via Write tool (.py) | n | L | 2-3 |
| P0e | Decision memos from CODE, not from review history: (1) textnorm: differential test over the union of all demos' fixtures plus the attack corpus; base must be a superset [M2]; (2) money base: checklist in section 7 applied to #48 / #49 / Intake `budget.py` / `askdata/meter.py` [M3]; (3) store-protocol note: reservations, inbox, queue, tenant namespace against memory, sqlite, postgres [M4]; (4) migration plan [B6]; (5) read `core-v5-pilot-kernel.md` and classify KERNEL-1 and C1f into a step (this plan has not read them) | P0c | v1 | `egm:egm-review-loop` on each memo | n | M | 4-6 |
| P0f | One measuring pin: run `check_core_copies` for each demo against ce70eb5 (no commit to any live lane) and record drift counts [M13]; confirm real heavy-slot count and set the WIP limit [M8]; confirm refunds-first-client question (decides #49 reservations) | P0c | v1 | lead | n | L | 1 |
S0 exit artifact: `s0-report.md` with a go/no-go table, the first MEASURED estimate (package count, builder hours, expected review rounds, reviewer-slots, wall-clock days; no calendar promise). If S0 changes the order, the plan is amended once and listed in the amendments file; the 3-round plan-review cap still holds.

### Step S1: text normalisation slice [B2, M2]
| P1 | Split `guard/textnorm.py`, `_confusables`, `tools/gen_confusables.py` out of PR #50 into a small PR on ce70eb5; superset behaviour proven by P0e differential test; named views (identity key, display, scan) so dealdesk's wrapper and the kit's casefold are deleted; `FOLD_VERSION` stored with identity keys (no client deployed: change now); pin `unicodedata.unidata_version` and test it across the Python matrix. PR #49 then drops its own textnorm. Kind: `textnorm` / interface `fold(text, view) -> text` / default = this module / alternative = outlined (ICU-backed fold, trigger: a client language the stdlib tables mishandle) | P0e | v1 | all four demos (re-pin at S8) | evidence: full suite + mutants + differential test; Rev | YES (identity/security) | H | 6-10 |

### Step S2: PR #50 slices [M8, M7, M16]
| P2a | Stop state: `stop_gate` + `rowstore` + `config_view` as ONE stop-state module (scoped kill, audited reset, breaker); this replaces `limits.KillSwitch` variants and the agent-killswitch package (not copied). First fix: the failing test and the BAD mutant row `rows: no default row limit` (BL-core-pr50-ev5-001/002), the restore-without-audit rows r2-005/007/022, and the open r3 majors. Kind `stop_state`: interface engage/status/release(audited) / default = store-backed / alternative = a PyPI killswitch adapter, outlined, trigger: a client asks | P1 (or independent if files disjoint, S0 decides) | v1 | apexc, dealdesk, refunds, jagrat | evidence + Rev | YES (security) | H | 12-20 |
| P2b | `egress_text` (outbound text check) slice | P1 | v1 | apexc, dealdesk, refunds | Rev | YES | H | 4-8 |
| P2c | `testing/mutation` runner: adopt Intake's KILLED/CRASH split; delete the three duplicate runners over time; mutant lists stay in demos; take only `evalcore.py` from the kit, merged later with C9 [m5] | P1 | v1 | all | Rev | n | M | 3-5 |
| P2d | `redact.py` pattern changes carried by #50 (owner of that file; C1a pattern ticket BL-core-c1a-001/020 slow patterns waits on this slice) | P1 | v1 | all | Rev | YES (redaction) | H | 8-14 |

### Step S3: migrations and PR #49 [B6]
| P3a | Migration rule: main's numbers never change; renumber in merge order at merge time; additive, forward-only; a migrate test from the prior head for each renumber; CI check that fails on duplicate or out-of-order numbers; check whether any demo or pilot DB ever ran a branch-numbered 0005 (main 0005_evidence, #41 0005_measure, #49 0005_reservations) | P0e | v1 | all | Rev | n | M | 2-3 |
| P3b | PR #49 rebase onto the new base: `approvals/signed`, `reply_check`, `identity_text`, `actions/outbox`, `audit/refusal`; `store/reservations` dropped unless S0 says refunds is the first client (then it is the meter's durable backend, see P4b). Default milestone v1.1 | P1, P2*, P3a | v1.1 | refunds, dealdesk | Rev | YES (signed approvals) | H | 10-16 |
| P3c | PR #41 (K6 measurement, demotion, promotion evidence): rebase (10 conflict files), renumber migration, review; default v1 candidate (reliability evidence) unless P0c shows it unreviewed and large, then v1.1 | P3a | v1/v1.1 | all | Rev | n | H | 8-14 |
| P3d | PR #43 and #47 (ask-your-data gaps; demo-export adapter): #47 merges clean, #43 needs 4 files; no Intake consumer; default v1.1 unless P0c shows they are already reviewed and green | P0c | v1.1 | ask-your-data demo | Rev | n | M | 4-8 |

### Lane M (money, parallel to Lane R from S0 on) [B1, M3, M4]
Order inside the lane: P4a -> P4b -> P4c; P4d runs alongside P4b; P4e after P4b.
| P4a | C2 (refuse instead of estimate: typed `UsageMissing`, settled at worst case, `is None` checks, sweep `x or default` on numeric fields), C3 (five-class `Usage`: input, cache_write, cache_read, output, thinking-for-visibility; Anthropic and Bedrock field names; multi-turn thinking test), C4a (prompt-length price tiers, optional inference-geo multiplier, dated price check in config). Spend is integer micro-USD per 1M tokens; business amounts are a separate type (minor units, exponent table, `allow_negative`) [M3] | P0e | v1 | Intake, askdata | FAIL-BEFORE tests; evidence + Rev | YES (money) | M | 12-20 |
| P4b | C17 reserve/settle meter. Base = the memo winner from P0e (default bias PR #48 `llm/metered.py`; #48 conflicts in 15 files, rebase = a rewrite onto P4a shapes). Kind `meter`: interface reserve(worst_case)->handle / settle(handle, usage) / release; default = store-backed meter; the in-memory backend is refused in multi-worker or client config; alternative = in-memory (tests) and the second durable backend from P4d. One spend counter shared with `limits.py` budgets (no two counters). Also carries #48's other items (extract leaks, spend-cap 429). Parity tests with Intake `budget.py` on shared fixtures; Intake becomes a consumer afterwards | P4a, P4d, P3a | v1 | Intake, askdata, refunds | N-thread race test at the cap never exceeds it by more than one worst case; clock-back refusal; idempotent settle; expiry sweep; Rev | YES (money) | H | 16-28 |
| P4c | C8 run cost cap (`Agent.budget_usd.per_run` required; stop at run cost + next worst case; audit event) + C5-core loud-wall alert hook on `limits.daily_budget` | P4b | v1 | Intake | FAIL-BEFORE; Rev | YES (money) | M | 4-8 |
| P4d | SQLite store kind (one durable backend besides Postgres) + one shared contract suite across memory, sqlite, postgres (pattern `tests/contracts/test_store.py`) + move psycopg dialect behind the store kind (psycopg is imported in `store/migrate.py`, `store/postgres.py`, `store/protocol.py`, `runtime/tick.py`; make the lock-in guard cover them) | P0e store note | v1 | Intake (budget, queue, inbox), all | contract suite on 3 backends; Rev | YES (store holds money state) | H | 10-18 |
| P4e | C6-core call log sink (one metadata record per `llm.chat` from a `finally`; sink kind: JSONL default / OpenTelemetry alternative outlined) | P4b | v1.1 | Intake | Rev | n | M | 4-6 |

### Lane R (redaction; design check on the new main starts in S0, build starts after P2d/P1) [M1, M10]
Override of the brief's order: redaction is a PARALLEL lane because C1 is a gate for any client use. PR #50 owns `redact.py` so C1a waits for P2d only for that file.
| P5a | C18a redesign R1 (`codes.py` leaf, `guard/diagnostic.py`, `diagnostic_schema.py`, `t1.py`, class `code` on the 17 own exception classes, hostile corpus, type tests, mutants) rebuilt on ce70eb5 (old branch core/c18a-injection-log-redact is superseded; its 51 open rows follow the P0d dispositions) | P0d, P1 | v1 | all | per design-v3 + FROZEN amendments D1-D16 | YES | H | 12-18 |
| P5b | R1P -> R3a -> R3c+R3b -> R2 -> R5 in the frozen build order, one PR each | P5a | v1 | all | as above | YES | H | 35-50 |
| P5c | C1a redactor kind + C1b/C1c masked LLM wrapper (run the redactor on `document` in `AgentLoop.handle` before `_screen` and `llm.chat`; redactor error -> NEEDS_PERSON `redaction_error` and no chat call; send only masked text; one metadata outbound record; restore values in the proposal in code = C1f put-back) + C1d. Kind `redactor`: interface `mask(text, session) -> masked, mapping handle` / default = `guard.redact` / alternative = a detector-model or NER backend, OUTLINED with trigger (a client document type the patterns miss); the second backend is a closure condition for the kind, not v1.1 [M14]. Includes the decisions already in the C1 amendments (F10 wording; D5 sixth code `session_closed`; REGEX_VERSION 4) | P2d, P5a | v1 | Intake, all | C1a branch head 8460813 rebased (conflicts: CHANGELOG, config, redact, registry); open rows BL-core-c1a-* re-reviewed | YES | H | 20-35 |

### Step S4a: client-profile gates (new, from M14)
| P6a | Config-validation test: dev-only kinds (hmac_v0 signer, env secrets, memory meter, fake channel) unselectable in a client profile | P4b | v1 | all | FAIL-BEFORE; Rev | YES (security) | L | 2-3 |
| P6b | No-training lock as a gate inside the llm kind before any non-fake call (not a helper); test that only the executor reads the secrets kind | P4a | v1 | Intake, askdata | Rev | YES | L | 3-5 |

### v1.1 promotions (each starts only on its trigger; "clean" inputs only [B7])
| Id | Scope | Source branch (named before start) | Consumer | Unc |
|---|---|---|---|---|
| P7a | Inbound message ledger with one defined terminal state for a reused message id (dealdesk `inbox.py`, apexc `intake.py`, Intake inbox) | S0 names one | Intake, dealdesk | YES (money-adjacent) |
| P7b | Tenant namespace helper; RateCap and ReadLog; data-source loader; test helpers (SplitMix64/FNV rng, FakeClock, FaultSchedule) in `testing/` | demos | dealdesk, refunds, apexc | n |
| P7c | Least-privilege `authorize`/`requires` extending `actions/authorizer.py` | dealdesk, refunds | those | YES (security) |
| P7d | Canonical JSON ASCII form as an OPTION (default unchanged); dev signer / Ed25519 `can_mint` split | refunds, dealdesk | those | YES (signature) |
| P7e | Money parsing (minor units; reconcile negative-amount disagreement between refunds and apexc; non-two-decimal currencies) | refunds | those | YES (money) |
| P7f | C9 eval gate buckets + `evalcore.py` merge; trigger: before any pilot or prod config | kit | all | n |
| P7g | C18b hygiene batch; cheap duplicate deletions (secrets reader, strict_json, time seam, freeze) only when a PR already touches that file [m7] | core | all | n |
| P7h | Warden batch A (numbers check, evidence ids, grounding core, language detect, freeze windows, safe path, confidence/hand-back labels), promoted from `reference\warden` after refreshing it from GitHub (it is 3 merges behind), not from the Jagrat copy | warden | jagrat, Intake | n |
| P7i | Warden batch B (breaker/bounds merged into the stop-state module and `limits.py`, target lock, landed-check, environment policy) | warden | jagrat | YES |
| P7j | Warden batch C (quarantine of untrusted text as typed facts, vault/reveal, webhook and read scope) only if Intake's untrusted-input path names it | warden | Intake | YES |
| P7k | Scan, workqueue, approval service pieces (6b/6d) and WP3 payment-detail checks as a core kind; waits for those lanes' own reviews to close | Intake lanes | Intake | YES |
| P7l | Second channel (email) and second executor: outline with trigger; code only on demand | - | - | n |
| P7m | Jagrat incident kinds (catalogue, playbook, verifier) stay in Jagrat; WP3 payment checks and Jagrat kinds are listed here as deferred, not dropped [m11] | - | - | - |

### Step S8: finish [m1, M13]
| P8a | Sync check and ONE real re-pin per demo to the final core commit (never into a worktree a builder edits); core version tag + CHANGELOG per merge; `core_copies.json` updated in every promotion; public API stability note (`__all__`, deprecation policy) and Python-version matrix [m9] | all v1 | v1 | evidence + Rev | YES | M | 6-10 |
| P8b | Docs (README per kind), `egm:egm-drift-report`, `ledger_check --topic core` passing, rollback tags | P8a | v1 | lead | n | L | 3-5 |
| P8c | Thin proof pack: each v1 kind run on made-up data with the fake LLM; no model call; no real names or PII | P8a | v1 | reviewed as a script | n | L | 4-8 |

### WP-id matrix: where every course work package goes [B1]
C1 -> P5c. C1a -> P5c. C1b/C1c -> P5c. C1d -> P5c. C1f (put-back) -> P5c. C2 -> P4a. C3 -> P4a. C4a -> P4a. C4b -> Intake lane (consumer after P4a). C5 -> P4c (core part) and Intake lane. C6 -> P4e (core, v1.1) and Intake lane. C7 -> Intake lane. C8 -> P4c. C9 -> P7f (v1.1, trigger: before any pilot/prod). C10 -> bible/template work, not core. C11-C16 -> Intake lanes (not core). C17 -> P4b. C18a -> P5a/P5b (redesign). C18b -> P7g. C19-C22 -> lead/bible work, not core. KERNEL-1 -> classified in P0e from `core-v5-pilot-kernel.md` (not read by this plan). Glossary: C-ids = WORK-PACKAGES.md; P-ids and S-steps = this plan; R-ids in section Lane R = design-v3 package names (R1, R1P, R2, R3a/b/c, R5); bible rule numbers are written "bible R214".

## 5. Merge order (to be confirmed by P0c verdicts)
Dependabot batch (P0b) -> P1 textnorm slice -> P2a..d slices of #50 (the pushed head already contains ce70eb5 and merges clean) -> P3a migration rule -> Lane M: P4a, P4d, P4b, P4c, P6 gates -> Lane R P5a, P5b, P5c (parallel with Lane M, serial inside the lane) -> P3c (#41) -> v1.1: P3b (#49), P3d (#43, #47) -> P8. Reason for #50 before #48: #50 merges clean today and holds the shared text/redaction files; #48 conflicts in 15 files including `llm/common`, `config`, `extract` and CI files, so rebasing it AFTER P4a avoids doing the rewrite twice. Split #48's `ci.yml`/`pyproject` edits into a separate reviewed commit after the Dependabot batch.

## 6. Security and least-privilege items inside v1 [M14]
Client-profile gate (P6a); no-training lock (P6b); only the executor reads secrets (P6b); S0 agents read-only; push to remote only by the lead; every new kind lists its identity and rights in its README; probe and promotion reports carry no real client data; Warden is refreshed before copying; the redactor kind's second backend is outlined with trigger (P5c).

## 7. Money-base checklist for P0e(2) [M3]
Atomic reservation across processes; integer micro-USD per 1M tokens rounded UP per call; worst-case reserve; `UsageMissing` settles at the reserved worst case; release in `finally`; expiry sweep; idempotent settle; N-thread race at the cap; clock-back refusal; one shared counter with `limits.py`; in-memory refused in multi-worker config; separate types for spend and business money; parity with Intake `budget.py` on shared fixtures; bible R110, R214, R215, R278-R292, R335 cited in the memo. Winner is chosen from code; if two tie, the one with fewer files and one durable backend wins; the owner is told only if the winner is not #48.

## 8. Success measures, exit artifacts, rollback
* **Success (Core v1):** the six conditions of section 2, each shown by a file: merged PR list with shas; `ledger_check` output; re-pin diff per demo; proof-pack run log.
* **Per-step exit artifacts:** S0 `s0-report.md`; every package `evidence-<n>.md`, review reports, ledger rows (with reviewed sha), merge sha; S8 drift report.
* **Rollback:** tag main before each merge (`pre-<pkg>`); one PR per package; migrations additive so a code revert leaves the schema valid; old branches kept until the replacement passes; nothing deleted before its replacement's tests pass.
* **Estimate honesty:** the hour ranges above are guesses by the planner, not measurements. They are summed nowhere. After S0 the lead reports for each step: package count, builder hours, review rounds seen (3-5 expected on money/redaction), reviewer slots and wall-clock days, and re-measures against the real clock every report.

## 9. Owner-only decisions (table) [M15]
| Decision | Blocks | Lead default | If unanswered |
|---|---|---|---|
| D-kit: portal kit separate package or core module | v1.1 only | separate package, pinned like a core copy | default applies from the start of v1.1 |
| D-killswitch | P2a | absorbed into the stop-state module; PyPI adapter only if a client asks | default applies at P2a start |
| D-licence | P7h | core is `LicenseRef-Proprietary`, Warden is owner-authored Apache-2.0: the lead greps for third-party files/NOTICE in P0a; the owner is asked only if a third-party file turns up; reference\ killswitch, helios, temporal sample get their own licence checks before any copy | - |
| Refunds-first-client? (decides whether #49 reservations land) | P3b, P4b | no | default applies at P4b start |
| v1-first vs full core | scope | v1 stop line, then v1.1 on need (this plan) | applies |
| Live model calls | - | none in this plan | owner's yes with numbers |

## 10. Alternatives considered
* **One flat "complete everything" order (the concepts brief).** Rejected: no stop line, merge-order contradictions [B2, B4].
* **Merge #48 first.** Rejected for now: it conflicts in 15 files and sits on shapes (Usage, Route) that P4a changes; rebuilding twice wastes review rounds.
* **Keep all three reserve/settle designs.** Rejected: two spend counters is a money bug class; one meter, one counter.
* **Copy agent-killswitch into core.** Rejected: a fourth stop design; absorb behaviour into one stop-state module.
* **Promote everything from Jagrat/Warden.** Rejected: no consumer for most of it [M6]; batch A only on need.
* **Restart the C18a branch fix loop (batch 6).** Rejected by the owner's yes of 2026-11-05 11:08Z; the redesign replaces it.

## 11. Rejected risks I could not close (for the reviewers)
* The planners did not read function bodies; P0c/P0e replace claims with measurements.
* KERNEL-1 and C1f scope are not read; P0e classifies them and may add a package.
* S0 may find #41/#43/#47/#48/#49 reviews missing; verdicts and milestones above are defaults that S0 can change once.
