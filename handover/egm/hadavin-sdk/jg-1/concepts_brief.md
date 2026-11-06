> **PAUSED by owner 2026-11-06 (lead order 49), resume only when a client asks. Saved as found, possibly incomplete (the agent was stopped mid-work). Not reviewed, not to be built. Nothing deleted.**

# JG-1: cloud ops reader (read-only cluster and cloud commands for the agent)

* **Author:** Claude (cloud session, `egm:egm-brainstorm`, AUTO mode, SHORT)
* **Date:** 2026-11-06 (written about 07:50 UTC / 13:20 IST)

**Read this first (honest notes).**
- **This is NOT a Goldfish review.** The skill asks for six reviewer lenses run as fresh sub-agents. This session has no sub-agent tool, so none ran. The skill says a review in the same context does not count. The "Analysis" below is the author's own stress test. The real independent check is the ticket's review rounds and the build-start review.
- **AUTO mode.** The readiness gate, the iteration loop and the handoff gate were skipped (brief from the lead's session). Where the skill would ask, this brief takes the option the frozen core design already took for the same kind of problem: the Kubernetes read source (`src/hadavin_sdk/sources/kubernetes.py:1-9`: speak the REST API through the guarded `fetch`, no client library, no binary) and AK-G16 (frozen revision 3: text in, text out, refuse rather than guess). Each such choice is named in "Key decisions".
- **No live research was done** (no web tool was used in this session; the always-research-live rule wants it). Statements below about how the `kubectl` and `aws` programs behave (plugins, credential programs, config files) are from the author's knowledge and are marked UNVERIFIED in the ticket until a builder checks them against the current documentation.
- **Sources read:** `LEAD-ORDERS.md` orders 23, 27 and 47; core `src/` at `a412ca9` (its `src/` equals `origin/main` `39b2c88`: `git diff --stat origin/main HEAD -- src` prints nothing): `sources/`, `tools.py`, `runtime/agent_loop.py`, `backends/table.py`, `backends/factory.py`, `actions/secrets.py`, `audit/protocol.py`, `audit/chain.py`, `guard/redact.py`, `app.py`, `config.py`; tickets P1, P2d, P5c, AK-G16 (headers and the lines cited).

## Overview

Jagrat (the one showcase demo, order 47) must "check and help fix AWS and also EKS, ECS, EC2 and similar, by running read-only commands against them". JG-1 gives the agent that ability as one read tool. The model asks in the familiar shape of a command, for example `["kubectl", "get", "pods", "-n", "shop"]` or `["aws", "ecs", "describe-services", "--cluster", "demo-cluster", "--services", "web"]`. Our code:

1. checks the command against a closed list of allowed read commands and flags (anything not on the list is refused);
2. checks it against the client's own, narrower allowlist (namespaces, clusters, regions, which commands);
3. turns it into one fixed read request (an "operation") and runs that request on a backend: a recorded backend (made-up answers from files) or a real Kubernetes API (a free local `kind` cluster in the demo; EKS or any cluster for a client);
4. keeps only the allowed fields of the answer, then masks it with the existing tool-output path before the model sees it;
5. lets the existing run loop record and audit the call.

No write command exists in v1. The AWS backend is outlined, not built.

## Analysis (author's stress test; not Goldfish)

**What is wrong or risky, first.**
1. **Running the real `kubectl` or `aws` program is the biggest hazard, even with "argv, no shell".** Both programs read configuration the agent does not see and can run other programs (UNVERIFIED, from knowledge): `kubectl` reads `KUBECONFIG` and `~/.kube/config`, runs "exec" credential plugins named there, runs any `kubectl-<name>` program on `PATH` as a plugin, and takes `--kubeconfig`, `--server`, `--token`, `--as` (impersonation) and `--raw` (any API path). `aws` reads `~/.aws/config` and `~/.aws/credentials`, runs `credential_process` programs, switches identity with `--profile`, sends requests elsewhere with `--endpoint-url`, and reads local files for any parameter written `file://...` (a read of our own container's files) and through `--cli-input-json`. A flag allowlist on top of a real binary has to keep up with every release of two large programs. **Decision: v1 runs no program at all.** The command is only a request shape; our parser maps it to a fixed operation and our backend makes the HTTP read. Plugins, config files, credential programs, environment variables and `file://` then have nothing to act on. This is the choice the core already made for Kubernetes (`sources/kubernetes.py:3-6`).
2. **Masking patterns are not enough for cluster output.** The existing path masks pattern-shaped values: ARNs (`guard/redact.py:169`), 12-digit account ids (`:353`), IPv4 forms (`:355-357`), JWTs (`:185`), access-key ids (`:191-193`). But a pod or ECS task definition carries plain environment values (often passwords), a ConfigMap carries free text, and the `kubectl.kubernetes.io/last-applied-configuration` annotation repeats the whole object, environment included. A pattern redactor cannot know that `DB_PASS=hunter2-made-up` is secret if it has no secret shape. **Decision: projection first.** Each operation has a fixed list of fields that may be kept ("allow" check, exact field paths); everything else is dropped before any text is made. Then the existing masking runs (`tools.py:936` `prepare_output` -> `redact_layered` `:976` -> `runmap.redact_untrusted`), with P2d-2's look-alike and hidden-channel checks (built on P1's `guard/textnorm.py`) once those merge. Secrets objects are never readable, whatever the client allowlist says.
3. **"Read-only" by parser alone is one bug away from a write.** Defence in depth: the credential itself must be read-only. The core already has the probe: a SelfSubjectRulesReview whose rules must hold no write verb, no exec/attach/port-forward/proxy access and no read of Secrets (`sources/kubernetes.py:100-125`, run at start-up by `sources.scope_problems`, `sources/__init__.py:65-82`). The cloud_ops Kubernetes backend reuses it; a failed probe means the backend does not start. The AWS outline needs the same (a policy-simulation probe), named as a condition of building it.
4. **"Short-lived credentials" has to be checked, not hoped.** A Kubernetes token made by the TokenRequest API carries an expiry; an old-style ServiceAccount Secret token does not expire. The backend reads the token through the secrets kind and refuses one with no expiry or with a lifetime over a configured ceiling. It decodes the token only to read its lifetime, never to trust it.
5. **"Every call audited" is already true on the agent path; it is not true for any other caller.** The run loop records every tool call (`ToolCallRecord`, `runtime/agent_loop.py:485-494`) and writes an audit event for it (`_note(run, "tool", ...)`, `:509-515`) to the configured audit kind, which outside `dev` is the hash chain (`audit: chain`, `ChainAudit`, `audit/chain.py:152`; `local_dir` is dev-only, `backends/table.py:593-602`), the one AK-G16 deploys with signing in its `audit` part. A refused command is a tool error and is audited the same way. Risk: a later caller (JG-5, a CLI) that calls the backend directly would skip it. Decision: the backend is reachable only through the tool function; a repo test checks that nothing else imports it.
6. **The environment name.** `Config.environment` is a policy level (`dev`, `pilot`, `prod`, `config.py:317`), an owner-approved exception. Order 47 wants "demo" as a config value. It must not become a fourth policy level. Decision: a separate label `environment_name` (validated plain name, shown in output and audit), never read by any policy check.

**Counter-arguments weighed.**
- *"Re-implementing kubectl is a big job."* Not for a read-only v1: about a dozen `get` resource types, `logs`, `rollout status/history`, `top` (optional) and `events` are each one or two REST reads. The model does not need kubectl's table printing; it needs the fields.
- *"Engineers trust real kubectl output."* The output says plainly which operation ran and which fields were kept. The video shows the command shape the engineer knows.
- *"Use an existing Kubernetes or AWS MCP server (tool ladder rung 4)."* Kept as an outlined alternative backend behind the same parser and allowlist, with a trigger (a client already runs one and accepts it in writing). Not the default: such servers usually expose write tools too, and their output is not projected (UNVERIFIED, no live research).

**What survives.** One flow: argv list -> closed grammar -> client allowlist -> operation -> backend read under the existing guarded fetch (timeout, size cap, host, method and path bound) -> projection -> existing masking -> existing record and audit.

## Goals vs. Non-Goals

* **In-Scope Goals:**
  - the `cloud_ops` kind: one interface, backends `recorded` (neutral, dev-only) and `kubernetes_api` (neutral: local `kind` cluster, EKS, any conformant cluster);
  - a closed grammar of read commands for `kubectl` and `aws` (ECS, EC2, CloudWatch metrics and logs, EKS API), parsed from a list of strings, never from shell text;
  - a per-client allowlist that can only narrow the grammar;
  - projection per operation, then the existing masking;
  - short-lived credential check and the existing read-only scope probe;
  - one manifest tool so the existing tool path does timeout, size cap, masking, record and audit;
  - mutants for every grammar and allowlist rule.
* **Out-of-Scope Non-Goals:**
  - any write command (JG-5 proposes changes; an executor identity runs them);
  - the real AWS backend (outline only, with trigger and the conditions to build it);
  - running the `kubectl` or `aws` programs;
  - reading Secrets objects, ConfigMap data, `exec`, `cp`, `attach`, `port-forward`, `proxy`, `--raw`, `--watch`;
  - Azure and GCP (outline row only).

## Alternatives Weighed

1. **Run the real programs with `subprocess` (no shell), a flag allowlist, an empty `HOME` and a cleaned environment.** Rejected by author: the programs still read config and run plugins and credential programs unless every path is closed for every release; it needs both programs installed in the image; its printed text is harder to project field by field.
2. **Official client libraries for everything (the Kubernetes Python client, boto3).** Rejected for Kubernetes: the core already speaks the REST API through the guarded fetch, and a client library would bypass that fetch's host, method and path checks. Accepted only inside the AWS adapter module (vendor imports live only in their kind module).
3. **An MCP server as the default backend.** Rejected as default (see above); kept as an outline with a trigger.
4. **Accept a command string and split it with `shlex`.** Rejected by author: quoting rules are a second parser the checks could read differently. Only a JSON list of strings is accepted.
5. **A field deny list instead of an allow list for output.** Rejected by author: a new field in a new API version would pass through unmasked. The allow list fails closed.
6. **Audit intent before every read (as for side effects).** Rejected by author for v1: `write_intent` exists for side effects (`audit/protocol.py:19-21`); a read has none, and the existing outcome event (outbox on failure, `:23-25`) already covers every call on the agent path. Recorded as a decision the lead may reverse.

## Key Decisions & Staging for Next Steps

- **KD1** No program runs; the command is a request shape (frozen-core choice, `sources/kubernetes.py:3-6`).
- **KD2** The kind lives in the backends table pattern (`backends/table.py` `Entry`, `:332-345`; factory `backends/factory.py:29-57`), capability `cloud_ops`, kinds `recorded` (dev-only) and `kubernetes_api`; `aws_api` outline only. The Kubernetes backend reuses `KubernetesSettings`-style validated settings, the guarded fetch (`tools.py:536-600`) and the scope probe (`sources/kubernetes.py:100-125`).
- **KD3** Grammar is closed in code; the client allowlist (config) can only remove commands and narrow namespaces, clusters, regions and name patterns.
- **KD4** Projection (allow list of field paths per operation) before masking; Secrets never readable.
- **KD5** Masking reuses `prepare_output` (`tools.py:936`) unchanged; P2d-2's checks (on P1's textnorm) arrive when those merge. JG-1 adds no masking code of its own besides projection.
- **KD6** Audit reuses the run loop's per-call record and event (`agent_loop.py:485-515`) into the hash chain (`ChainAudit`); no new audit code; a repo test keeps the backend reachable only through the tool.
- **KD7** Token lifetime check on the credential; the ceiling is a validated config value.
- **KD8** `environment_name` is a label ("demo" in the demo config), never a policy level.
- **KD9** Security path: no review round cap; extended review (adversarial reviewer with the mutant list, plus the least-privilege over-breadth review).
- **Owner-only (to PENDING LEAD):** whether a client allowlist may ever add ConfigMap reads (with projection); the token-lifetime ceiling value; when the AWS backend is built (needs an AWS account, so money and a login).
