> **PAUSED by owner 2026-11-06 (lead order 49), resume only when a client asks. Saved as found, possibly incomplete (the agent was stopped mid-work). Not reviewed, not to be built. Nothing deleted.**

# JG-5: fix proposals through approvals, executed by a separate identity

* **Author:** Claude (`git config user.name`), JG-5 ticket author session, AUTO mode
* **Date:** 2026-11-06 (written from about 08:55 UTC / 14:25 IST; IST = UTC+5:30)
* **Input:** `egm/hadavin-sdk/jg-5/concepts_brief.md` (same session)

## Read this first

- **AUTO mode.** The section approval gates, the reconcile question and the save-location question were skipped, as the lead's brief ordered. Where the skill asks the author to choose between options, this draft takes the option the frozen ticket AK-G15 took and writes "as AK-G15". The skill's `resources/execution_instructions.md` is missing from the installed plugin (`/root/.claude/plugins/cache/egm/egm/0.1.0/skills/egm-draft/`); the draft follows the skill text and `references/design_doc.md`.
- **No Goldfish review ran** (no sub-agent tool in this session). `egm:egm-review` is the next step and is the first independent review.
- **Code facts** are cited from `origin/main` at `39b2c88` (`src/` last changed in `d1ed085`). Nothing was run. PostgreSQL, Kubernetes, `kind` and WebAuthn behaviours are UNVERIFIED unless a line says otherwise.
- **Reconcile against the brief (skill step 6.1).** Contradictions: none. Additions that change an interface: (1) a separate console script `hadavin-fix-executor` (the brief said "separate executor program" without naming the entry point); (2) a config field `deployment_name` (the brief said "if A15 or AK-G16 already defines such a field, use theirs"; still a coupling).

## Overview

JG-5 adds one path for changing a client system: propose, approve with a passkey, execute by a separate identity, record. The agent can only write a proposal. A person approves it in the portal with a passkey check bound to the exact command. A separate executor program, which has its own database role, its own config folder, its own secret source and its own cluster account, runs an approved proposal once, before its approval expires, and records the result. Nothing else in core can run a command on a client system.

## The Problem

Jagrat must help fix AWS and Kubernetes problems, and the owner's rule is that any change is always through approvals, never direct (order 47, item 4). Today core cannot do this safely. The action contract has no kind for a command-line program (`actions/contract.py:15-43`). The gate denies every `sign_off` action (`actions/authorizer.py:225-226`, rule `class.sign_off.no_stepup`). The approval tables can be written by the agent's own database role (`store/migrate.py:40-41`, `:48-51`), and an approval is a signed Slack click, not a passkey (`approvals/channel.py:78-88`). The executor lives in the agent's own process (`app.py:173`, `:209-210`; called at `runtime/agent_loop.py:840`).

## Goals

1. A proposal is an unchangeable record: exact argv (the list of words given to the program, no shell), target, reason, requesting run and principal, contract id and version, deployment name, argv hash, created and expiry times.
2. Only a person can approve, only with a passkey check (WebAuthn with user verification, AK-G17 step-up), only for the exact argv hash shown, never the requester, and the approval stops being usable after a short time.
3. Only the executor identity can run an approved proposal, at most once, and only after re-checking the proposal, the approval, the passkey signature, the argv and the kill switch.
4. The agent's process, database role and cluster account cannot run, approve or reach the executor's secrets; each claim has a negative test.
5. Every step (propose, approve or reject or refuse, claim, execute, result, expire) is an event in the existing audit chain.
6. v1 backends: a fake that records calls, and the local `kind` cluster. Nothing else runs.

## Non-Goals

- A real AWS backend or a real-cluster backend (written outline; trigger: the first client pilot that asks for fixes to run).
- Approval by two different people (v1.1; trigger: before any client pilot with fixes).
- The approvals screen (laptop side, JG-4 and G14); this design gives its data contract only.
- Sign-in, passkey registration and the step-up ceremony itself (AK-G17).
- Undo of a fix. A `command` contract is always `sign_off`; an undo is a second proposal.
- Free-text commands of any kind.

## Open Questions (owner or lead; PENDING LEAD in the ticket)

1. **G4 and the approval page.** G4 says no command a person could paste reaches them (`approvals/gate.py:367-369`). The approver must see the exact argv. Recommended: argv only on the signed-in portal approval page, as a list of words; Slack and all model text keep G4.
2. **The requester in a one-person demo.** The requester is the run's principal (`runtime/agent_loop.py:717`). Recommended: that person may not approve; the demo has two made-up people in the local Keycloak.
3. **Time limits.** Recommended: proposal lives 3600 s; approval usable 600 s; passkey answer at most 120 s old when the approval is recorded.
4. **Demo profile and name.** Recommended: profile `dev` (the `kind` backend is dev-only) with `deployment_name: demo`.

## Critical User Journeys (CUJs)

### CUJ 1: A person approves a restart and it runs once
Jagrat finds a stuck deployment and proposes `kubectl --context <ctx> --namespace <ns> rollout restart deployment/<name>`. The run waits. A person (not the requester) opens the approvals queue in the portal, reads the argv, presses approve and touches their passkey. Within 600 s the executor claims the approval, re-checks everything, runs the command on `kind`, records "succeeded", and the run is closed by the tick.

### CUJ 2: Nobody approves
The proposal reaches its expiry. The tick marks it expired, audits it, and the run ends `EXPIRED`. Nothing ran.

### CUJ 3: A taken-over agent tries to run its own fix
It cannot write an approval (no EXECUTE on the approve function), cannot claim (no EXECUTE on the claim function), has no executor in its `App`, cannot import the executor (lint), and its cluster account is refused `patch`. Each refusal is a test.

## Technical Plan (Architecture)

```
agent process (runtime role, reader cluster account)
  gate: command + sign_off -> needs_approval, rule class.sign_off.proposal
  render argv from contract template + schema-checked inputs
  hadavin_fix_propose(...)  --INSERT-->  fix_proposals (immutable)
        | audit: fix.propose (write_intent)
portal backend = approval service (fix_approver role)
  queue view  <--SELECT--  fix_proposals + fix_approvals + fix_claims
  challenge = sha256(proposal_id | argv_hash | nonce)
  AK-G17 step-up verifies the passkey answer (uv = true, fresh)
  hadavin_fix_approve(...)  --INSERT-->  fix_approvals (immutable)
        | audit: fix.approve / fix.reject / fix.refuse
executor process (fix_executor role, executor cluster account, own config + secrets)
  poll  -> hadavin_fix_claim(approval_id)  --INSERT--> fix_claims (UNIQUE approval_id)
  re-check: hash, re-render argv, passkey signature, kill switch, audit intent
  run argv (no shell, scrubbed env, timeout) on backend fake | kind
  hadavin_fix_finish(claim_id, outcome)  --INSERT--> fix_results
agent tick: fix_reconcile reads fix_results / expiry -> ends the run
```

### Part A. Records (all append-only)

As AK-G15: each table has triggers that refuse UPDATE, DELETE and TRUNCATE to every role; inserts go only through SECURITY DEFINER functions owned by a NOLOGIN owner role `hadavin_fix_owner`; every relation in the functions is schema-qualified; times come from the database clock.

- `fix_proposals`: `proposal_id`, `tenant`, `deployment_name`, `run_id`, `requested_by`, `action_id`, `action_version`, `backend`, `argv` (JSON array of strings, 1-32 items, each 1-256 printable characters), `target` (JSON: `system`, `context`, `namespace`, `resource`), `reason` (masked, template-built, at most 500 characters), `argv_hash`, `created_at`, `expires_at`.
- `argv_hash = sha256_hex(canonical_json({proposal_id, tenant, deployment_name, action_id, action_version, backend, argv, target}))` (reuses `hashing`/`canonical_json` as `models.py:134-143` does).
- `fix_approvals`: `approval_id`, `proposal_id` (UNIQUE: one decision per proposal in v1), `argv_hash`, `decision` (`approve`|`reject`), `approver_id`, `credential_id_hash`, `authenticator_data`, `client_data`, `signature`, `uv` (must be true for approve), `challenge_nonce`, `decided_at`, `valid_until`.
- `fix_claims`: `claim_id`, `approval_id` UNIQUE, `executor_id`, `claimed_at`.
- `fix_results`: `claim_id` UNIQUE, `outcome` (`succeeded`|`failed`|`unknown`|`refused`), `error_code`, `exit_code`, `output_hash`, `finished_at`. Output text is masked by JG-1's masker before storage, as the read path does.

### Part B. Functions (the only write paths)

1. `hadavin_fix_propose(...)`: EXECUTE for the runtime role only. Refuses a bad shape (the CHECKs), sets `created_at = now()` and `expires_at = now() + ttl` with ttl bounded inside the function.
2. `hadavin_fix_approve(proposal_id, argv_hash, decision, approver_id, proof...)`: EXECUTE for `fix_approver` only. Refuses: proposal missing or expired; `argv_hash` not equal to the stored one; `approver_id = requested_by`; approver id of a service principal (prefix rule set by AK-G17; UNVERIFIED until AK-G17 exists); a second decision (UNIQUE); `uv` false on approve. Sets `valid_until = now() + approval_ttl`.
3. `hadavin_fix_claim(approval_id, executor_id)`: EXECUTE for `fix_executor` only. Refuses: decision not `approve`; `now() >= valid_until`; proposal expired; a claim already exists (UNIQUE, also under two executors at once).
4. `hadavin_fix_finish(claim_id, outcome, ...)`: EXECUTE for `fix_executor` only. One result per claim.

### Part C. Identities and rights

| Identity | Database | Secrets | Cluster (`kind`) |
|---|---|---|---|
| runtime (agent) | SELECT on the four tables; EXECUTE `hadavin_fix_propose` only | none of the executor's | JG-1 reader account: get, list, watch only |
| `fix_approver` (portal backend) | SELECT on the four tables; EXECUTE `hadavin_fix_approve` only; SELECT on AK-G17's credential public keys | its own DSN secret name | none |
| `fix_executor` | SELECT on the four tables and AK-G17's public keys; EXECUTE claim and finish | its own DSN and kubeconfig secret names, read through the secrets kind from the executor's own config folder | Role in the one configured namespace: `patch` on `deployments` (restart), `patch`/`update` on `deployments/scale`; nothing cluster-wide |
| `hadavin_fix_owner` | NOLOGIN; owns the functions | none | none |
| portal (read-only) | SELECT on the queue view | none | none |

Migration and role creation reuse `store/migrate.py` (`GRANTS` at `:46`, `_apply_grants` at `:169-187`); the role-name-in-SQL question is handled the way AK-G15 BN-6 / AK-G2 BN-24 decided (coupling; see AK-G15 brief Analysis 1).

### Part D. Contract kind and gate

- New `CommandExecutor` in `actions/contract.py` beside `HttpExecutor`: `kind: "command"`, `program` (a key of the executor's config `programs`, never a path from the contract), `argv_template: list[str]` where a word is a literal or exactly `{field}` (a whole word; no partial substitution), `backend`. The validator requires `chain_id`, `verify_check` (a read-only check through JG-1), and refuses `rollback`.
- `effective_class` already returns `sign_off` for a non-`none` kind with no undo (`actions/contract.py:97-99`), so every `command` contract is `sign_off`.
- `authorize`: before the `sign_off` deny at `:225-226`, if `contract.executor.kind == "command"` return `needs_approval` with rule `class.sign_off.proposal`. Every other `sign_off` stays denied.
- The agent loop: at `runtime/agent_loop.py:713-721`, a `command` contract calls a new hook `propose` instead of `request_approval`, and the run waits in `WAITING_FOR_APPROVAL`. `execute()` refuses a `command` contract (`executor_not_in_this_process`).

### Part E. The executor program

- Console script `hadavin-fix-executor = "hadavin_sdk.fixes_exec.main:main"`. It loads its own config folder (DSN secret name, kubeconfig secret name, `programs`, backend, poll interval) and never the agent's runtime config.
- Loop: list approved, unclaimed, unexpired approvals; for each, claim; write audit intent (refuse on `AuditUnavailable`, as `runtime/agent_loop.py:774-781`); re-read the proposal; recompute `argv_hash`; re-render argv from the contract and the stored inputs and require equality; verify the passkey signature with AK-G17's verify function against the stored public key and the challenge built from `(proposal_id, argv_hash, challenge_nonce)`; check the kill switch (`limits.py:22`); run.
- Run: `subprocess` with an argv list, `shell=False`, the program path from config, an environment holding only `KUBECONFIG` (the executor's own file) and `PATH` from config, a timeout. Exit 0 = `succeeded`; non-zero = `failed`; timeout or lost process = `unknown` (never run again; a person looks, as `actions/executor.py:130-137`).
- No network listener. Nothing can call it.

### Part F. Audit

Every step writes an `AuditEvent` (`models.py:188-215`) through `ChainAudit` (`audit/chain.py:152`) with `domain="fix"`: `propose`, `approve`, `reject`, `refuse` (with `error_code`), `claim`, `execute` (intent, before the side effect), `result`, `expire`. `inputs_hash` = `argv_hash`; `principal` = the acting identity. AK-G16's checkpoint and anchor cover these events like any other.

## Alternatives Considered

### Alternative A: Reuse `plans`, `approval_requests`, `approval_decisions`
Rejected by author: the runtime role can INSERT and UPDATE them (`store/migrate.py:48-51`); narrowing those grants changes every existing approval path. The checks of `Approvals.decide` (`approvals/requests.py:150-161`) are reused as rules inside `hadavin_fix_approve`.

### Alternative B: Approve with the Slack button
Rejected by author: an HMAC click proves the Slack workspace, not a person with a passkey. The Slack card (JG-3) carries a portal link only.

### Alternative C: Executor inside the agent process, separated by the import lint
Rejected by author: one OS process would hold both identities; the lint proves imports, not memory.

### Alternative D: Executor trusts the approval service's passkey check
Rejected by author: one leaked `fix_approver` credential would then be enough to run a change. The executor re-checks the signature.

### Alternative E: Model writes the argv, an allowlist of shapes checks it
Rejected by author: shape allowlists are the surface that kept failing in G4 (`approvals/gate.py:371-376`); template rendering is smaller.

### Alternative F: Executor receives "run" calls over the network
Rejected by author: anything that can reach it could call it. It pulls from the database.

### Alternative G: Plain store code instead of definer functions
Rejected by author, as AK-G15 Alternative A: a check in Python does not stop a caller that holds the role's password.

## Non-Functional Requirements

- **Security path, extended review, no round cap.**
- **Least privilege:** the table in Part C is the whole set; each row has a negative test.
- **No single dependency:** the fix backend is a kind (`fake`, `kind`; real AWS and real cluster outlined with trigger). The passkey check is AK-G17's kind. Subprocess calls are to programs named in config.
- **No hardcoding:** times in `defaults.py` (own block) with bounds; deployment name, programs, namespace, context from config.
- **Masking:** reason text and command output are masked before storage, audit and model.

## UNVERIFIED

- PostgreSQL: trigger refusal of TRUNCATE for non-owners; SECURITY DEFINER with a NOLOGIN owner; UNIQUE under two concurrent claims (expected one wins; to be shown by test).
- Kubernetes: `kubectl rollout restart` is a `patch` on the deployment; `kubectl scale` uses `deployments/scale`; `kubectl auth can-i --as=system:serviceaccount:<ns>:<name>` answers for a service account.
- WebAuthn: the signed data covers `authenticatorData || sha256(clientDataJSON)`, and `clientDataJSON.challenge` carries our challenge; the AK-G17 library exposes a verify call usable offline by the executor.

## Detailed Implementation Plan

Three sub-PRs: JG-5a (records, rules, proposal), JG-5b (approval service), JG-5c (executor).

### Target Files to Create/Modify

#### 1. `src/hadavin_sdk/store/migrations/<next>_fixes.sql` (Create, JG-5a)
The four tables, CHECKs, append-only triggers, the four functions, the owner role, the queue view. Number taken at build time (merge order).

#### 2. `src/hadavin_sdk/store/migrate.py` (Modify, JG-5a)
`GRANTS` rows for the four tables and the view; grants for `fix_approver` and `fix_executor`; EXECUTE grants per function; `check_grants` covers them.

#### 3. `src/hadavin_sdk/models.py` (Modify, JG-5a)
`FixProposal`, `FixApproval`, `FixClaim`, `FixResult` with `argv_hash()` on `FixProposal`.

#### 4. `src/hadavin_sdk/store/protocol.py`, `store/memory.py`, `store/postgres.py` (Modify, JG-5a)
`propose_fix`, `list_fix_queue`, `approve_fix`, `claim_fix`, `finish_fix`, `get_fix_*`, `expire_fixes`. The memory store applies the same rules in Python for tests and dev.

#### 5. `src/hadavin_sdk/actions/contract.py` (Modify, JG-5a)
`CommandExecutor` and its validator.

#### 6. `src/hadavin_sdk/actions/authorizer.py` (Modify, JG-5a)
Rule `class.sign_off.proposal` for kind `command` only.

#### 7. `src/hadavin_sdk/fixes/propose.py` (Create, JG-5a)
Render argv from template and inputs; build the masked reason; call `propose_fix`; audit. Not a secret holder.

#### 8. `src/hadavin_sdk/runtime/agent_loop.py`, `runtime/tick.py`, `app.py` (Modify, JG-5a)
`propose` hook; `execute()` refuses `command`; tick step `fix_reconcile` ends runs from results and expiry; `App` builds no command executor in any profile.

#### 9. `src/hadavin_sdk/fixes/approve.py` (Create, JG-5b)
Challenge building; call AK-G17 step-up verify; call `approve_fix`; audit every refusal.

#### 10. `src/hadavin_sdk/fixes_exec/main.py`, `fixes_exec/backends.py` (Create, JG-5c)
The executor program and the `fake` and `kind` backends. Secret holder.

#### 11. `src/hadavin_sdk/config.py`, `defaults.py`, `backends/table.py` (Modify)
`deployment_name` (validated label) unless A15/AK-G16 defines one; `fixes` section; `FIX_*` constants in an own block; `fix_backend` kind with `kind` dev-only.

#### 12. `pyproject.toml` (Modify, JG-5c)
Console script `hadavin-fix-executor`.

#### 13. `tests/test_repo_rules.py` (Modify, JG-5c)
Add `hadavin_sdk.fixes_exec.*` to `SECRET_HOLDERS`; add `fixes` and `cli` to the never-import set for it; plant test.

#### 14. `demos/`-free test fixtures: `tests/fixtures/kind/fix-executor-rbac.yaml`, `tests/fixtures/kind/reader-rbac.yaml` (Create, JG-5c)
Role and binding text for the `kind` tests; made-up names only.

#### 15. Tests (Create): `tests/test_fix_records.py`, `test_fix_approve.py`, `test_fix_executor.py`, `test_fix_grants_pg.py`, `test_fix_kind.py`
As the ticket's test table.

#### 16. `CHANGELOG.md` (Modify)
One entry per sub-PR.

### Verification Plan

The ticket's test rows and mutants; Postgres rows on a throwaway PostgreSQL 16 and 17; `kind` rows only where a local `kind` cluster is present (skipped with a visible reason otherwise, and run once by the lead on the laptop sandbox).
