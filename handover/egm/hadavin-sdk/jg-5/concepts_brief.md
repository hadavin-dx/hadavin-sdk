> **PAUSED by owner 2026-11-06 (lead order 49), resume only when a client asks. Saved as found, possibly incomplete (the agent was stopped mid-work). Not reviewed, not to be built. Nothing deleted.**

# JG-5: fix proposals through approvals (short brainstorm)

* **Author:** Claude (`git config user.name`), JG-5 ticket author session, AUTO mode
* **Date:** 2026-11-06 (written from about 08:40 UTC / 14:10 IST; IST = UTC+5:30)

## Read this first (what was and was not done)

- **Scope.** Lead order 47 task 1, last bullet (`LEAD-ORDERS.md:316-330`): a proposed change on a client system (for example `kubectl rollout restart`, `kubectl scale`, `aws ecs update-service`) is only a PROPOSAL until a person approves it with a passkey, and it is run by a separate executor identity that the agent can never hold. v1 runs nothing against a real system; in the demo the only system that is changed is the local `kind` cluster (a throwaway Kubernetes cluster on the laptop).
- **AUTO mode.** The skill's clarifying questions, readiness gate and hand-off gate were skipped, as the lead's brief ordered. Where a design choice existed, this brief takes the option the frozen ticket AK-G15 took (`tickets/AK-G15.md`, revision 3, FROZEN; design `egm/hadavin-sdk/ak-g15/design.md`): its own table guarded by database triggers, a SECURITY DEFINER database function as the only write path for the risky step, a separate database role with its own secret name, and the database clock for times. Each such choice says "as AK-G15".
- **No Goldfish review ran.** This session has no tool to start a sub-agent. The "Analysis" below is the author's own stress test in one context. It is NOT a Goldfish review. The `egm:egm-review` step after the draft is the first independent review.
- **Code.** Every claim about existing code was re-read on `origin/main` at `39b2c88` (last commit touching `src/`: `d1ed085`), exported to a scratch copy because the on-disk `src/` differs from `origin/main` in 7 files. Nothing was run: no Python, no PostgreSQL, no Kubernetes. Every PostgreSQL, Kubernetes and WebAuthn behaviour below is UNVERIFIED.
- **Tickets this depends on that do not exist yet.** AK-G17 (sign-in and passkey step-up) and JG-1 (read-only cloud commands, the `cloud_ops` kind and the `kind` cluster backend) have no ticket on disk. Amendment A15 and `speed-plan-jagrat-first.md` are being written (questions-for-lead item 113) and are not on disk. This brief names the contract it needs from each and marks it as a coupling, not a fact.

## Overview

Jagrat (the one showcase demo, order 47) diagnoses incidents in AWS and Kubernetes with read-only commands. When it finds a fix, the owner's rule is that it may never change a system itself. JG-5 turns a fix into a stored, unchangeable proposal: the exact command words (the "argv": the list of words passed to the program, with no shell), the target, the reason, and which run asked. A person sees it in the approvals queue in the portal, signs in, and approves it with a passkey (a WebAuthn check on their own device, AK-G17 step-up). The approval names the exact command by its hash and expires after a short time. A separate executor program, with its own credentials that the agent's process, database role and cluster account cannot reach, picks up the approved proposal, checks everything again, runs it once, and records the result. Every step goes into the existing audit chain.

## What exists in core today (re-read)

- The action contract has three executor kinds: `none`, `manual` and `http` (`actions/contract.py:15-43`). There is no kind for a command-line program.
- The executor re-checks the plan hash and the approval's hash before it acts (`actions/executor.py:106-116`), never retries a write blindly, and turns a timeout into "unknown" or a lookup (`:124-148`). It runs HTTP only (`:117-119`).
- The gate gives `sign_off` actions a flat deny, `class.sign_off.no_stepup` (`actions/authorizer.py:224-226`): the step-up that JG-5 brings is exactly the missing piece that rule names.
- Approvals already refuse a decision by the requester (`approvals/requests.py:158-159`), a decision after the step's time ran out (`:154-155`), a decision for another plan hash (`:160-161`), and keep one decision per step atomically (`:167-172`).
- BUT the agent's own database role can write those tables: the runtime role has SELECT, INSERT and UPDATE on `plans` and `approval_requests` and SELECT, INSERT on `approval_decisions` (`store/migrate.py:40-41`, `:48-51`). A Slack click is an HMAC-signed callback (`approvals/channel.py:78-88`), not a passkey. So today's approval rows cannot be trusted for a change on a client system.
- The executor is built inside the same `App` as the agent, with the same secrets provider, in `dev` (`app.py:173`, wired as a hook at `:209-210`) and called in-process (`runtime/agent_loop.py:840`). In `pilot` and `prod` it is `None` (`app.py:52`, `:173`). The import lint keeps `runtime`, `approvals` and `llm` from importing the executor or a secret provider (`tests/test_repo_rules.py:131-142`, `:151-169`), but one process still holds both.
- The audit chain (`audit/chain.py:152`) has a fail-loud `write_intent` (`:207-213`) and a never-raising `write_outcome` (`:215-230`); AK-G16 adds the checkpoint anchor and the re-anchor pass.
- The safety profile is `environment: Literal["dev", "pilot", "prod"]` (`config.py:317`); "demo" is not one of them.

## Analysis (author's own stress test; not a Goldfish review)

Weakest points first.

1. **Trusting the existing approval tables would be a hole.** Because the runtime role can INSERT an `approval_decisions` row and UPDATE `approval_requests.status` (`store/migrate.py:48-51`), an agent process that is taken over could write "APPROVED" for its own proposal. So the executor must trust only rows that the agent's role cannot write at all. As AK-G15: new tables guarded by triggers, written only through SECURITY DEFINER functions that the runtime role cannot EXECUTE.
2. **A passkey check that only the approval service makes is one point of trust.** If the approval service's database role leaks, it could write an approval with no passkey behind it. Stronger: store the signed passkey answer (authenticator data, client data, signature, credential id) and let the executor check the signature again against the person's registered public key. The challenge the device signs is built from the proposal id, the argv hash and a one-time number, so the signature is for THIS command only. Cost: the executor needs AK-G17's verify function (a library call, not our own crypto: tool ladder). Kept.
3. **The model must not write the command words.** If the argv came from model text, a flag such as `--server=` or `--kubeconfig=` could point the command somewhere else. The argv is rendered by our code from a template in the action contract and from inputs that pass the contract's schema (patterns such as `[a-z0-9-]{1,63}`). The executor renders it again and refuses if it is not identical to the stored argv.
4. **Replay.** One approval must run at most once. A claim table with UNIQUE on the approval id, written only by a definer function, closes it, including two executors at once.
5. **Expiry needs one clock.** Approval valid-until and proposal expiry are checked by the database clock inside the claim function, as AK-G15 did for its lease.
6. **"The agent can never hold the executor's secret" is a claim about deployment, not just code.** Code can prove: no import, no EXECUTE grant, no executor in the agent's `App`, a separate config folder and secret source for the executor. A cluster can prove: the agent's read-only service account is refused `patch` (a `kubectl auth can-i` negative test on `kind`). What code cannot prove: that a client's operator does not put both secrets on one machine. That stays an owner-visible limit, in plain words.
7. **G4 says no command a person could paste reaches them** (`approvals/gate.py:367-369`). An approver must see the exact argv to approve it. Resolution: the argv is shown only on the signed-in portal approval page, as a list of words; the Slack card and all model-written text keep G4 (no argv there). This needs the lead's yes (PENDING LEAD).
8. **Self-approval in a one-person demo.** The requester is the run's principal (`runtime/agent_loop.py:717`). If a person asks the agent in the portal chat to restart something, that person is the requester and may not approve. The demo then needs two made-up people. Owner-only choice (PENDING LEAD).
9. **"demo" is a name, not a safety profile.** The kind backend is a dev-only kind; the demo deployment runs profile `dev` with the configured deployment name "demo". If A15 or AK-G16 already defines such a name field, JG-5 uses theirs (coupling).
10. **Result of a run that timed out.** `kubectl` gives no idempotency key. A timeout or a lost connection is "unknown" and goes to a person; the executor never runs it again (as `actions/executor.py:130-137`).

## Goals vs. Non-Goals

* **In-Scope Goals:** a new executor kind `command` in the action contract with an argv template; the gate rule that lets a `sign_off` action of kind `command` become a proposal (all other `sign_off` stays denied); an immutable proposal record; an approval record with the passkey proof, bound to the argv hash, with a valid-until time; a single-use claim; a separate executor program with its own database role, config folder, secret source and cluster account; two backends (a fake that records, and the local `kind` cluster); every step in the audit chain; the queue data the portal (JG-4) reads; rights listed per identity with negative tests.
* **Out-of-Scope Non-Goals:** a real AWS or real-cluster backend (written outline, trigger "first client pilot that asks for fixes"); approval by two different people (v1.1 row); the approvals screen itself (laptop, JG-4/G14); sign-in and passkey registration (AK-G17); undo of a fix (v1.1 row; a fix whose contract has no undo stays `sign_off`); free-text commands.

## Alternatives Weighed

- **Reuse `plans`, `approval_requests` and `approval_decisions` for fixes.** Rejected by author: the runtime role can write all three (`store/migrate.py:48-51`); narrowing those grants would change every existing approval path. The existing `Approvals` checks are reused as rules (requester, expiry, hash), re-stated inside the definer function.
- **Approve by Slack button.** Rejected by author: an HMAC click proves the Slack workspace, not the person with a passkey (owner rule: approvers need passkey MFA). The Slack card links to the portal only.
- **Executor in the agent process, kept apart by the import lint only.** Rejected by author: one OS process holds both identities; the lint proves imports, not memory.
- **Executor trusts the approval service and does not re-check the passkey signature.** Rejected by author: one leaked role would be enough to run a change. Re-check kept (Analysis 2).
- **Free argv from the model, checked by an allowlist of shapes.** Rejected by author: an allowlist of shapes is the surface that kept failing in G4's history (`approvals/gate.py:371-376`); rendering from a template is smaller.
- **The executor listens for "run this" calls.** Rejected by author: anything that can reach it could call it. The executor has no listener; it pulls approved claims from the database.

## Key Decisions & Staging for Next Steps

1. Three sub-PRs: JG-5a records and rules (tables, triggers, functions, roles, contract kind, gate rule, proposal API, audit events); JG-5b approval service (passkey step-up via AK-G17, approve/reject, queue data for JG-4); JG-5c executor program (claim, checks, fake and `kind` backends, result, the tick step that ends the run).
2. As AK-G15: triggers refuse UPDATE, DELETE and TRUNCATE on the proposal, approval and claim tables for every role; definer functions are owned by their own NOLOGIN owner role; every relation is schema-qualified; times use the database clock.
3. Three new identities beside the runtime role: approval service, executor, and the executor's cluster account. The runtime role gets INSERT on proposals only.
4. PENDING LEAD: G4 exception for the portal approval page; requester rule in a one-person demo; approval time limit numbers; demo profile `dev` with deployment name "demo".
