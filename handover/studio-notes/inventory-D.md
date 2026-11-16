# Inventory D: generic code in apexc, dealdesk, refunds, hadavin-demos, website that could move to core

Date 2026-11-05. Read-only. EGM skipped: read-only inventory (the lead runs EGM on the plan built from this).
Method: file docstrings + def/class lists (AST), `core_copies.json` and `CORE_COPIES.md` of each standalone demo, `git diff --stat main...<branch>` of the four core promotion branches, `git grep` over core `main` and those branches. I did NOT read function bodies in full, so "generic" below is a judgement from docstring, name and the demo's own `allowed_local` reasons; the porter must read the body before building.

## 0 Facts that frame everything

- Core `main` = 6608146 (#46). Open core PRs touching this area: **#50** (branch `core/promote-apexc-review8`, ready, head 153d217 per demo pins; the local branch `core/promote-apexc-review8` is at older 3224f3d, the `-b9` branch is at 153d217) and **#49** (`core/promote-refunds-r8`, draft, local head 96a5709; branch `-r8-b` at cd62212 is what the demos pin). Both unmerged; no promoted module is in core main.
- Repos: the **standalone** repos `projects\hadavin-demo-<x>` are the live ones (they carry `core_copies.json`). `projects\hadavin-demos-<x>` are monorepo-shaped copies (`demos/<x>/...`); they are STALE relative to standalone: md5 differs for apexc `executor.py`, refunds `store.py`, `writegate.py`; dealdesk `inbox.py` identical. `projects\hadavin-demos` itself holds only a README (scaffold, 6a4c2dc); worktrees of it live under `_local\scratch\wt\`. `hadavin-demos-apexc` and `-dealdesk` have uncommitted changes (`git status`). Treat `hadavin-demos-*` as a copy of the standalone repo, not a second source; do not promote from it.
- `core_copies.json` exists in: hadavin-demo-apexc, -dealdesk, -refunds, -intake (+2 intake wp4 worktree dirs), hadavin-demos-apexc, hadavin-demos-dealdesk, wt-pr47. Not in website, hadavin-demos, hadavin-portal-kit, hadavin-demos-kit.
- Demo pins (`core_commit`): apexc and refunds 660814674ece (core main older than 6608146), dealdesk 6608146. Core `main` has no `guard/textnorm`, `runtime/config_view`, `runtime/stop_gate`, `runtime/rowstore`, `testing/`, `approvals/signed`, `guard/reply_check`, `guard/identity_text`, `store/reservations`, `actions/outbox`, `audit/refusal`, `audit/capped`: they exist only in the PR branches.

## 1 Already promoted (in PR #50 or #49), verified present in the branches

| Capability | Demo files | Core file (branch) | In core main? | Pinned in core_copies.json? | Size | Consumers |
|---|---|---|---|---|---|---|
| Unicode fold + UTS 39 skeleton/mixed-script (text normalisation) | apexc `textnorm.py`, `_confusables.py` (692 l); dealdesk `core_copy/textnorm.py`, `core_copy/_confusables.py`; refunds `core_copy/textnorm.py`, `core_copy/_confusables.py` | `guard/textnorm.py` (181 l), `guard/_confusables.py` (692 l), generator `tools/gen_confusables.py` + `tools/data/confusables.txt` | no, PR #50 | yes, all three demos (snapshot 153d217) | ~870 | apexc, dealdesk, refunds, intake, kit (kit has its own 35-l `textnorm.py`, deliberately not swapped) |
| Egress text screen (`LeakPolicy`, `text_leaks`, digit budget) | apexc `egress_text.py` (454); dealdesk `core_copy/egress_text.py` | `guard/egress_text.py` (454) | no, PR #50 | apexc yes, dealdesk yes; refunds NO (refunds keeps `guards.egress_check`, see 2.4) | 454 | apexc, dealdesk |
| Frozen config view + swap | apexc `config_view.py` (179) | `runtime/config_view.py` (179) | no, PR #50 | apexc yes | 179 | apexc (dealdesk has own `freeze.py`, see 2.3) |
| Stop gate (kill switch, per-kind ceiling hook) | apexc `stop_gate.py` (304) | `runtime/stop_gate.py` (304) | no, PR #50 | apexc yes (import rewrite to `apexc.audit_event`) | 304 | apexc only so far |
| Row store: pending keys, validated JSON copy | apexc `rowstore.py` (132) | `runtime/rowstore.py` (132) | no, PR #50 | apexc yes | 132 | apexc |
| Mutation judge/runner | apexc `mutation_judge.py` (95) | `testing/mutation.py` (95), `tools/mutation_runner.py` (185) | no, PR #50 | apexc yes | ~280 | apexc, dealdesk and refunds each have their own `mutation_check.py` (704 / 1204 / 703 l) that do NOT use the core runner |
| Capped audit | apexc `fakes.Audit` uses own chain | `audit/capped.py` (157) | no, PR #50 | not copied | 157 | refunds `store.audit` wants it (CORE_COPIES.md), not adopted |
| Signed one-use approvals | dealdesk `core_copy/approvals_signed.py` (146); refunds `approval.py`+`signers.py` (local) | `approvals/signed.py` (146) | no, PR #49 | dealdesk yes (core_pr 49, cd62212); refunds NO (local, needs differential test) | 146 | dealdesk; refunds pending |
| Reply/egress check for customer replies | refunds `guards.egress_check`; dealdesk `guards.egress_check` | `guard/reply_check.py` (173) | no, PR #49 | neither | 173 | refunds, dealdesk |
| Identity text keys | refunds `identity.py` | `guard/identity_text.py` (120) | no, PR #49 | no | 120 | refunds |
| Reservations (cap-before-spend) | refunds `store.reserve/release/sweep` + `core_seam.py` | `store/reservations.py` + `Store.reserve` + migration 0005 | no, PR #49 | no | ~300 incl. pg | refunds (dealdesk has cumulative discount check in `executor`, check overlap) |
| Outbox (intent/applied, IN_DOUBT) | refunds `writegate.py` docstring R-REF-024 | `actions/outbox.py` (229) | no, PR #49 | no | 229 | refunds, apexc/dealdesk executors |
| Refusal audit fields | refunds `writegate.py` | `audit/refusal.py` (56) | no, PR #49 | no | 56 | refunds |

Known conflict inside the PRs: #49 and #50 both add `guard/textnorm.py` with different content (#49: 76 or 131 l, #50: 181 l). Kit CORE-COPIES.md says "which one lands is open". Branch `-r8-b` already carries a 131-l variant. This must be settled before either merges; the demos pin the #50 variant (153d217) for textnorm.

## 2 Generic candidates NOT yet in core or any open PR

Columns: capability | files | in core/PR? | pinned in core_copies? | size | risk | consumers.

### 2.1 Inbound message ledger (no message lost or double-applied)
- Files: dealdesk `inbox.py` (287 l: `LedgerStore` protocol, `MemoryLedger`, `SqliteLedger`, `Inbox`, `reconcile`, deadline, bounded queue, id-reuse row), apexc `intake.py` (173 l, in-memory `Intake`), intake demo (`hadavin-demo-intake\src\intake\`, not in my scope but named by apexc `allowed_local`).
- Core: `store/protocol.py` + `store/memory.py` + `store/postgres.py` + migration 0001 already have an inbox table (grep hit "inbox/dead_letter"); no `Inbox` class with write-ahead/ack/reconcile. Not in #49/#50 (grep empty).
- allowed_local entries: apexc `intake.py` ("promotion candidate runtime/inbox.py"; id reuse ends `rejected:<reason>` in apexc, `rejected` in dealdesk, `dead_lettered` in intake: three different terminal states, must be reconciled).
- Pinned: no (listed only as allowed_local, expires 2026-12-31).
- Risk: MEDIUM-HIGH. Three demos differ on terminal states; the deadline thread-abandon known limit is stated in dealdesk; must reuse core store tables rather than add a second ledger. Owner rule "no lost messages" (bible R368-R370) makes this the most valuable item.
- Consumers: dealdesk, apexc, intake, refunds (refunds has no inbox yet).

### 2.2 Tenant-scoped store keys + namespace (client/demo segregation)
- Files: dealdesk `store.py` (105 l: `check_tenant`, `TenantStore`, `AuditChain`); refunds `namespace.py` (62 l: `Namespace`, `CrossClientAccess`, `config_key`); apexc tenant keys inside `intake.py`/`fakes.py`.
- Core: `store` kinds are tenant-aware in SQL (grep hits for tenant in store/postgres), but no fail-closed key-builder helper like `Namespace`. Not in a PR.
- Pinned: no. Size ~170 l. Risk LOW-MEDIUM (small, pure). Two implementations with different key shapes (`dealdesk/<tenant>/<kind>/<name>` vs Namespace); pick one and test both demos against it.
- Consumers: dealdesk, refunds, apexc, intake.

### 2.3 Immutable config freeze / Sealed
- Files: dealdesk `freeze.py` (36 l: `freeze`, `thaw`, `Sealed`); apexc already copies core `config_view.py` (PR #50) which does a similar job; core `k1b/causelist.py`, `k1b/score.py` have their own freeze code.
- Core: partial (PR #50 `config_view`; `k1b` internal freeze). Dealdesk docstring states an honest limit.
- Pinned: no. Size 36. Risk LOW. Action: do not add a third freeze; check if dealdesk can use `runtime/config_view` after #50 and delete `freeze.py`. Class: merge, not new module.

### 2.4 Rate cap (token bucket) and read log (blast radius)
- Files: dealdesk `guards.py` (105 l: `RateCap` with injectable clock, connection cap, `ReadLog`, `egress_check`); refunds `guards.py` (275 l, same `RateCap`, `ReadLog`, `egress_check`). refunds CORE_COPIES says "RateCap is locked (same code as dealdesk)".
- Core: none (grep `RateCap`, `ReadLog`, token bucket empty on main and all four branches). `llm/retry.py` and `limits.py` exist but are different.
- Pinned: no. Size ~100 for the generic parts (the `egress_check` part is replaced by `guard/reply_check.py` of #49). Risk LOW-MEDIUM: small, but needs a thread-race test (refunds `tests/test_review12.py` has one) and a backwards-clock test; carry both over.
- Consumers: dealdesk, refunds, apexc (has own per-kind denial ceiling in stop_gate), intake.

### 2.5 Least-privilege identity table / `requires` decorator
- Files: dealdesk `identities.py` (83 l: `authorize`, `requires` decorator, deny-all start); refunds `identities.py` (204 l: `authorize`, `model_callable_tools`); apexc `rules.identity_can/authorize_op/identity_conflicts` (in a 709-l file).
- Core: `actions/authorizer.py` exists on main (grep `def authorize|requires(`); it is the closest thing. I did not read it, so whether it already covers a per-operation `requires` decorator and an identity-conflict check is UNVERIFIED.
- Pinned: no. Risk MEDIUM: three different shapes; extend core `actions/authorizer.py` rather than add a module (improve-before-replace). Least-privilege HARD rule makes a shared, negatively-tested implementation valuable.
- Consumers: all demos.

### 2.6 Canonical JSON / args-hash / idempotency-key
- Files: dealdesk `canon.py` (101 l: `canonical_json`, `sha256_hex`, `idem_key`, `*_hash`, `mint_id`); refunds `hashing.py` (27 l: `canonical_json` ASCII-escaped, `args_hash`); apexc `ports.idem_key/release_key`.
- Core: `models.canonical_json` (ensure_ascii=False, per refunds' note) and `hashing.py` exist. Refunds says hashes differ, "switch when core adds an ASCII form (duplication map item 6)".
- Pinned: no. Risk MEDIUM-HIGH: changing a hash form changes every stored/signed hash; must be an added option (`ascii=True`), not a change of the default; this is a money/signature path (uncapped review).
- Consumers: dealdesk, refunds, apexc, intake.

### 2.7 Signers: HMAC dev kind + Ed25519 with `can_mint`
- Files: refunds `signers.py` (119 l); dealdesk `signing.py` (60 l, "local re-implementation of core audit/signer.py (PR #48)", only module importing cryptography).
- Core: `audit/signer.py` + cloud signers on main (Ed25519 and KMS kinds); no HMAC kind, no `can_mint` split (minting vs verifying).
- Pinned: no. Risk MEDIUM (security path, uncapped review; the HMAC kind is dev-only and must be impossible to select in a client config). Core PR #48 (core-hardening-1) is open and touches signing; check for overlap first.
- Consumers: dealdesk, refunds.

### 2.8 Money parsing, per-currency caps and rounding
- Files: refunds `money.py` (34 l: `parse_minor`, `parse_nonneg`), `config.py` caps and tiers (373 l); apexc `normalise.minor/round_half_even_div/tax_minor` (apexc allows negatives, half-even tax).
- Core: nothing (grep parse_minor, half-even empty).
- Pinned: no. Size ~80 generic. Risk MEDIUM: money path; two demos disagree on negatives, so a core `minor_units` helper needs explicit `allow_negative` and per-currency exponent table (refunds assumes two-decimal currencies only; JPY/KWD would be wrong). Limit/tier logic in refunds `config.py` is domain-specific (stays).
- Consumers: refunds, apexc, dealdesk (discount percent is not money; check).

### 2.9 Statistics: Clopper-Pearson, pass^k, verdict
- Files: refunds `verdict.py` (90 l: `upper_bound_zero_wrong`, `clopper_pearson`, `verdict` with amber cap for scripted runs).
- Core: `stats.py` and `evals.py` on main already hold clopper/pass-k (grep hits stats.py, evals.py, models.py); kit `evalcore.py` already imports `hadavin_sdk.stats.upper_error_bound`.
- Pinned: no. Risk LOW. Action: diff `verdict.py` against core `stats.py`/`evals.py`; likely only the "amber cap for scripted runs" rule is new. Port that rule, delete the rest. Needs a read of both before sizing.
- Consumers: refunds, intake, kit.

### 2.10 Deterministic RNG (SplitMix64 + FNV-1a), fake clock, fault-injection ports
- Files: apexc `rng.py` (31 l), `ports.py` (221: `FaultSchedule`, `FaultStep`, `CallResult`, `Clock`, Protocols for ERP/Payments/Callout/Directory), `fakes.py` (798: `FakeClock`, `_Faulty`, `RateLimited`, `ConnectionRefused`, `EgressDenied`, `ReadOnlyErp`, `EgressGate`, in-memory `Audit` chain); dealdesk `ports.py` (99), `world.py` (191).
- Core: nothing matching FaultSchedule/FakeClock/splitmix on main or branches. `llm/fake.py` is a fake model only.
- Pinned: no. Risk LOW for `rng.py`, `FakeClock`, `FaultSchedule` (pure test helpers, ~150 l, belongs in `hadavin_sdk/testing/` next to PR #50's `testing/`); HIGH to try to generalise the ERP/Payments ports (domain-shaped). apexc `allowed_local` already marks `fakes.py` audit chain as "promotion candidate: MemoryChain kind" duplicating core `audit/chain.py` in memory form.
- Consumers: all demos for the test helpers.

### 2.11 Config-selected data source (demo vs client loader)
- Files: dealdesk `data_source.py` (36), refunds `data_source.py` (41: `NoSourceConfigured`, `Source`, `load`); intake has the same pattern (not read).
- Core: none. This is the loader the demo-only-folder rule (`memory\demo-only-folder-and-secrets.md`) demands in every repo; the env var name is per demo (DEALDESK_/REFUNDS_DATA_SOURCE).
- Pinned: no. Risk LOW, size ~40. Make it a core `register_source/configured_source/load` with the env var name passed in; the CI guard "product code never references demo_only" is separate.
- Consumers: all demos, every client build.

### 2.12 No-training lock for live model runs
- Files: dealdesk `lockcheck.py` (25 l: `live_run_allowed` requires explicit boolean, real date, not future, not stale).
- Core: none. Relates to bible/AI-provider-terms memory. Risk LOW. Candidate for `guard/` or `llm/` pre-flight. Needs a decision whether it belongs in the `llm` kind (yes, as a gate before any non-fake backend call).
- Consumers: dealdesk, refunds, apexc, intake.

### 2.13 Purpose limitation `model_view` (field allow-list before the model)
- Files: dealdesk `purposes.py` (66), refunds `purposes.py` (64, same `model_view` shape).
- Core: `guard/redact.py` (1132 l) and `k1b/redaction.py` mask PII; no purpose-based field allow-list helper (not verified by reading `redact.py`).
- Risk LOW-MEDIUM: the allow-list contents are per-job (stay in demos); only the "project dict to allowed fields, fail closed on unknown" mechanic is generic (~20 l). Probably too small to justify a module; fold into `guard/redact.py` as a helper if the lead wants it.
- Consumers: dealdesk, refunds, apexc, intake.

### 2.14 Name index (inverted index so scan cost is candidates, not accounts)
- Files: dealdesk `nameindex.py` (65). Core: none. Generic idea, but tied to `lower_norm` of tenant account names; dealdesk-only need today (a burst-load finding). Risk LOW. Defer unless a second consumer exists (YAGNI).

### 2.15 Typed errors, input limits and per-message deadline
- Files: dealdesk `errors.py` (33), `limits.py` (36); refunds `config.Limits`, `GateInputError`; apexc `config.py`.
- Core: `errors.py` and `limits.py` exist on main, #49/#50 already edit `limits.py`. Dealdesk's limits are documented defaults "in ONE place" for message size and deadline. Risk LOW; merge into core `limits.py` via config rather than a new module. Beware conflict: three PRs edit `limits.py`.

### 2.16 Kill-switch / control state in executor
- apexc `executor.ControlState`, `guarded` (inside 1007-l `executor.py`); core PR #50 already has `runtime/stop_gate.py` + `runtime/control.py` (15 l, on the first branch only). The executor stays demo-specific (apexc `allowed_local`), but check whether `ControlState` duplicates `control.py`.

### 2.17 Test split / segregation self-run (demo-only folder proof)
- Files: dealdesk `selfrun.py` (46: runs a fixed scenario, hashes outputs, audit hook records every file opened), `tests_oneshot/test_test_split.py` (43) and `conftest.py` (31); refunds `tests_oneshot/test_test_split.py` (75).
- Core: none. This is the machine proof that deleting `demo_only/` keeps the build green, a rule in every repo. Risk LOW-MEDIUM; best as a pytest plugin in the kit or `hadavin_sdk.testing`. Overlaps with the CI guard the kit/SDK already has ("no reference material"). Size ~120.

### 2.18 Mutation harness
- Three separate `mutation_check.py` (apexc 522, dealdesk 1204, refunds 703) + `mutants_*.py` in refunds (298+269+328) + dealdesk `prefix_proof.py` (93). Core PR #50 brings `testing/mutation.py` + `tools/mutation_runner.py`. Only apexc uses the core judge. Risk LOW to adopt the runner, MEDIUM to move mutant lists (they are tied to demo line numbers; stay in demos).

### 2.19 Hash-chained audit in memory + per-tenant chain
- apexc `fakes.Audit`, dealdesk `store.AuditChain`, refunds `store.audit`/`audit_chain_ok` (SQLite). Core `audit/chain.py` (547 l) is signed and anchored; no `MemoryChain` / unsigned chain with `verify`. Risk MEDIUM: three implementations may have different hash recipes; kit `chain.py` (hash-chain/1 and /2) is a fourth, JS-reproducible. Do not unify recipes without a design note; honest-tamper-evidence rule applies (`memory\honest-tamper-evidence-claims.md`).

## 3 hadavin-portal-kit / hadavin-demos-kit (named by the brief via "UI kit")

- `hadavin-portal-kit` (standalone, with LICENSE) and `hadavin-demos-kit\portal-kit` are the same kit in two repos; the kit is vendored into demos (`core_sync_check` item (c): kit hash file `KIT-SHA256SUMS`). `CORE-COPIES.md` in the kit lists its own promotion candidates:
  - `hadavin_kit/evalcore.py` (~400 l: lock, freeze, sealed gate, verdict, compare, report): generic eval gate, "core PR number NOT YET OPENED". Largest unpromoted generic block. Overlaps core `evals.py`/`stats.py` (see 2.9).
  - `hadavin_kit/textnorm.py` (35 l): kit-local fold, not a drop-in for core fold; stays until #49/#50 resolved.
  - `hadavin_kit/chain.py`, `strict_json.py` (40 l; candidate for shared loader), `scripted_llm.py` (107 l; core has `llm/fake.py` and `replay_records.py`, overlap not checked), `export_rules.py`/`rules_v11.py`/`versioning.py`/`kitcheck.py`/`kitsum.py` (kit-specific export/schema; stay).
  - `console/` (HTML/CSS/JS, `build_console.py`) is UI: stays in the kit, not core.
- I did not diff the two kit repos against each other (unverified whether identical).

## 4 projects\website: generic parts

- Astro site: `src/components` (Art, Backdrop, CtaBand, FlowDiagram, Footer, Header, Mark, Portal 353 l, SampleReport, Simple, Wordmark), `src/scripts/portal-demo.ts` (91), `flow-pause.ts` (30), `src/styles/global.css` (224), `functions/api` (Cloudflare functions, contact/check form), `scripts/headers.mjs`.
- Verdict: nothing here belongs in the Python core `hadavin_sdk`. A reusable UI kit would belong in the portal kit (client portal spec `research\port-ui-catalog\CLIENT-PORTAL-SPEC.md`), but the website components are Hadavin-brand marketing (Wordmark, Mark, Art, Backdrop) and `Portal.astro` is a marketing demo of the portal, not the kit. `global.css` design tokens (colours, light/dark) could seed the portal kit's `console/app.css` for brand consistency; not read, so UNVERIFIED whether they already share tokens.
- Do not promote anything; if a shared design-token file is wanted, that is a kit task, not core.

## 5 Demo-specific code that MUST stay (do not promote)

- apexc: `classify.py` (553, reference classifier), `rules.py` (709, hold/SoD/approval policy), `tools.py` (249, AP tool signatures), `executor.py` (1007, two-person lift, per-kind ceiling workflow), `normalise.py` (104, supplier-bank-change money/text rules; its look-alike table is superseded by the copied fold), `audit_event.py` (19 stand-in, deleted at pin move), `data\gen.py` (1953), `mutation_check.py` (522), `mutation_judge.py` is a copy.
- dealdesk: `desk.py` (648), `desk_rules.py` (281), `gate_rules.py` (561), `handler.py` (165), `tools.py` (191), `world.py` (191), `executor.py` (102, commit step), `textnorm.py` (45 wrapper: two views, injection phrases, name scans), `data\gen*.py` (725+296), `mutation\*`.
- refunds: `gate.py` (290 eligibility), `validate.py` (113), `desk.py` (176), `tools.py` (325), `writegate.py` (476; refund write path, only its refusal-audit and outbox parts are generic), `identity.py` (112, until `identity_text` lands), `config.py` thresholds/tier tables (373), `store.py` domain methods (`sum_order`, `sum_customers_since`, `order_rows`, `void_key`, compensation records), `core_seam.py` (58, deleted with demo reserve), `adapters\ports.py` (235; refund-domain ports), `data\gen.py` (2906), `mutation\*`.
- Anything in `demo_only\`, `config\`, acceptance/eval-contract/scoping/runbook documents: stay in the demo repos.

## 6 Suggested promotion order (for the lead's plan, not a decision)

1. Settle #49 vs #50 `guard/textnorm.py` conflict and merge #50, then #49 (they unblock 12 of the pinned copies and the switch-over sweeps).
2. Small, low-risk, many consumers: 2.11 data-source loader, 2.10 test helpers (rng/FakeClock/FaultSchedule into `testing/`), 2.4 RateCap/ReadLog, 2.12 no-training lock, 2.2 tenant key helper.
3. Medium, extend existing core modules: 2.5 identities into `actions/authorizer.py`, 2.9 verdict into `stats.py`/`evals.py` (+ kit `evalcore`), 2.15 limits into `limits.py`.
4. Money/security paths (uncapped review, own PRs): 2.1 inbox ledger (biggest value), 2.6 canonical ASCII hash form, 2.7 signers (after #48), 2.8 money parsing, 2.19 memory chain.
5. Then the re-pin sweep and `core_sync_check` run per `memory\core-modules-one-source-of-truth.md` rule 5.

## 7 Files read / what I could not verify

Read in full: the preamble, `core-modules-one-source-of-truth.md`, `promote-generic-fixes-to-core.md`, `hadavin-demo-refunds\CORE_COPIES.md`, `builder-notes-6.md` (PR #50 tail), first ~25 lines of `dealdesk\inbox.py`, kit `CORE-COPIES.md` (first 40 l).
Read as docstring + def list only (AST, no bodies): the 15 dealdesk/apexc/refunds modules listed in section 2 and `rules.py`, `classify.py`, `tools.py`, `ports.py`, `fakes.py`, `executor.py`, `intake.py`, `normalise.py`, refunds `store.py` method list.
Parsed: all three `core_copies.json`. Listed: `git diff --stat` for four core branches; `gh pr list` (open PRs).
Not verified:
- Function bodies of every candidate (generic-vs-demo judgement is from docstrings and each demo's own `allowed_local` reasons).
- Core `main` modules that may already cover a candidate: `actions/authorizer.py`, `stats.py`, `evals.py`, `hashing.py`, `limits.py`, `errors.py`, `llm/fake.py`, `replay_records.py`, `guard/redact.py`, `store/*` inbox tables. I only grepped by keyword.
- Whether PR #50 head on GitHub equals 153d217 (local branch `core/promote-apexc-review8` is at 3224f3d, `-b9` at 153d217; PR #49 local head 96a5709 vs demos' pin cd62212 on `-r8-b`). CI/review state of #49/#50 not checked.
- `hadavin-demo-intake` and `hadavin-demos-intake` (not in lane D); the intake demo likely holds more candidates (inbox, dead-letter).
- Whether `hadavin-portal-kit` and `hadavin-demos-kit\portal-kit` are identical; website design tokens vs kit tokens; `website\functions\api`.
- `git status` of standalone demo repos (only the `hadavin-demos-*` copies showed uncommitted files).
- Line counts are `wc -l` of the standalone repos at their current working trees, not at the pinned commits.
