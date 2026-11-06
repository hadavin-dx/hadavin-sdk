> **PAUSED by owner 2026-11-06 (lead order 49), resume only when a client asks. Saved as found, possibly incomplete (the agent was stopped mid-work). Not reviewed, not to be built. Nothing deleted.**

# JG-1: cloud ops reader (design)

* **Author:** Claude (cloud session, `egm:egm-draft`, AUTO mode)
* **Date:** 2026-11-06 (about 08:00 UTC / 13:30 IST)
* **Status:** draft for the ticket's review rounds. Not reviewed. Intake: `concepts_brief.md` in this folder.

**Honest notes.** AUTO mode: every section approval gate and the target-directory gate were skipped; the file goes to `handover/egm/hadavin-sdk/jg-1/` (the handover rule), not `docs/designs/`. The skill's `resources/execution_instructions.md` does not exist in the installed plugin (`ls` of the skill folder shows `SKILL.md`, `TEST.md`, `agents`, `assets`, `references`, `test_scenarios.yaml` and no `resources`), so it was not applied. Where the skill says the author chooses between options, this draft takes the option the frozen core design took (named per decision) and lists it in section 9 for the lead. No live research: facts about the `kubectl` and `aws` programs are UNVERIFIED. Code cites are on `src/` at `a412ca9`, equal to `origin/main` `39b2c88` for `src/`.

## 1. Overview and the problem

Jagrat must read the state of a client's Kubernetes clusters (EKS or any other) and AWS services (ECS, EC2, CloudWatch, EKS) to explain an incident (order 47, item 1). Engineers and models both think in `kubectl` and `aws` commands. Running those programs for a model is dangerous even without a shell: they read hidden config, run plugins and credential programs, and can switch identity (brief, risk 1). Their output also holds secrets that do not look like secrets (environment values), which pattern masking misses (brief, risk 2).

JG-1 adds one read tool, `cloud_ops`, that accepts a command as a list of words, checks it against a closed grammar and the client's allowlist, turns it into one fixed HTTP read, runs it on a backend, keeps only listed fields, and hands the text to the existing tool-output path, which masks it, records it and audits it.

## 2. Goals and non-goals

Goals (v1): the closed grammar for `kubectl` and `aws` reads; a per-client allowlist that only narrows; backends `recorded` (dev only) and `kubernetes_api` (local `kind` cluster, EKS, any conformant cluster); projection; credential lifetime check; reuse of the existing probe, fetch guard, masking, record and audit; a mutant for every rule.

Non-goals (v1): any write command; running the `kubectl` or `aws` program; the real AWS backend (outline, section 7); Secrets objects; ConfigMap data (PENDING LEAD); `exec`, `cp`, `attach`, `port-forward`, `proxy`, `--raw`, `--watch`; Azure and GCP.

## 3. Critical user journeys

- **CUJ 1, demo (recorded).** Config `environment: dev`, tool options `backend: recorded`, `environment_name: demo`. The model calls `cloud_ops` with `{"argv": ["kubectl", "get", "pods", "-n", "shop"]}`. The answer is a compact list from the made-up recording, masked. The audit chain gets one `tool` event.
- **CUJ 2, demo (local `kind` cluster).** Same, with `backend: kubernetes_api` and `source: demo-cluster`, a configured `kubernetes` source whose ServiceAccount token is short-lived and read-only. Start-up runs the scope probe; a token with `pods/exec` access stops start-up.
- **CUJ 3, refused.** The model sends `["kubectl", "delete", "pod", "web-1", "-n", "shop"]` or `["aws", "s3", "cp", "s3://b/k", "."]`. The tool returns `ERROR: refused (rule K-VERB): ...`; the run loop records and audits it as an error result. Nothing reaches a backend.

## 4. Technical plan

```
model tool call {"argv": [...]}
  -> ToolBox.invoke (tools.py:1162): arguments restored, schema checked, timeout, rate cap
     -> cloud_ops.tool.run(args, ctx)
        1 grammar.parse(argv)            closed grammar, rule id on every refusal
        2 allowlist.admit(op, options)   client allowlist: only narrows
        3 backend.run(op, ctx)           recorded: files | kubernetes_api: ctx.fetch with bound op id
        4 project(op, records)           allow-listed field paths only
        5 render(op, kept, environment_name) -> text
  <- prepare_output (tools.py:936): secret scrub, escape, redact_layered (:976) -> runmap.redact_untrusted
<- run loop: ToolCallRecord (agent_loop.py:485-494), store, audit event _note(run, "tool", ...) (:509-515)
   -> audit kind; outside dev the hash chain ChainAudit (audit/chain.py:152) that AK-G16 deploys
```

**4.1 Where the kind lives (decision D1).** A small registry inside a new package `src/hadavin_sdk/cloud_ops/`, in the shape of `sources/kinds.py:24-61` (a frozen dataclass per kind plus a module-level dict), selected by the tool's `options.backend`. Kinds: `recorded` (dev only) and `kubernetes_api`; `aws_api` is a registry row that refuses with the outline's trigger. This contradicts brief KD2 ("backends table"); see section 9 C1 for why the draft differs.

**4.2 Grammar (closed, in code).** Input is `{"argv": [str, ...]}`; the tool's `input_schema` has `additionalProperties: false`, so no `env`, `cwd` or `stdin` field can exist. Rules, each with an id used in the refusal text and in the mutant list:

- **G-SHAPE**: 2 to `CLOUD_OPS_MAX_ARGV` (32) items; every item a `str` (`type(x) is str`), ASCII, matching `^[A-Za-z0-9._:/=,@+\-]{1,253}$` (no space, quote, `$`, `;`, `|`, `&`, `>`, `<`, backtick, `*`, `~`, newline). An ALLOW check: exact grammar, no text folding (P5a's rule for allow checks).
- **G-PROG**: item 0 is exactly `kubectl` or `aws` (not a path, not upper case, not `kubectl.exe`, not `env`, not `KUBECONFIG=...`).
- **G-FLAG**: flags are parsed by our table only: `--name value` or `--name=value`; a short flag only as its own item followed by its value (`-n shop`; glued `-nshop` refused); a repeated flag refused; `--` refused; a flag not listed for that command refused (this is where `--kubeconfig`, `--context`, `--cluster`, `--server`, `-s`, `--token`, `--as`, `--as-group`, `--as-uid`, `--user`, `--insecure-skip-tls-verify`, `--raw`, `-w`, `--watch`, `-f`, `-k`, `-o go-template`, `-o jsonpath`, `--profile`, `--endpoint-url`, `--no-verify-ssl`, `--cli-input-json`, `--cli-input-yaml`, `--query`, `--debug`, `--ca-bundle`, `--no-sign-request` all fall out, with no special case). `-o wide` and `-o json` (kubectl), `--output json` (aws) are accepted and ignored: the output shape is ours.
- **G-VALUE**: values typed per flag: namespace and object names DNS-1123 (`^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$`, no `/`), label selectors `key=value` or `key!=value` comma lists of plain names, durations `^[0-9]{1,5}[smh]$`, counts integers within caps, AWS names `^[A-Za-z0-9_\-]{1,255}$`, AWS times ISO 8601. Any value starting `file://`, `fileb://`, `http://`, `https://` refused (rule G-URI) even though no program runs, so the shape never implies a file or network read.
- **K-VERB** (kubectl): only `get`, `describe`, `logs`, `rollout status`, `rollout history`, `top pods`, `top nodes`. Every other first word is refused, including the write verbs (`apply`, `create`, `delete`, `edit`, `patch`, `replace`, `scale`, `set`, `label`, `annotate`, `taint`, `drain`, `cordon`, `uncordon`, `rollout restart|undo|pause|resume`, `autoscale`, `expose`, `run`, `debug`), the shell and tunnel verbs (`exec`, `cp`, `attach`, `port-forward`, `proxy`), `config`, `plugin`, `auth`, and any unknown word (which the real program would run as a `kubectl-<word>` plugin, UNVERIFIED).
- **K-RES**: `get`/`describe` resource types: `pods|pod|po`, `deployments|deployment|deploy`, `replicasets|rs`, `statefulsets|sts`, `daemonsets|ds`, `services|svc`, `jobs`, `events|ev`, `nodes|no`, `horizontalpodautoscalers|hpa`. Also `<type>/<name>`. Refused: comma lists, `all`, any dotted form (`secrets.v1.`), `secrets`/`secret` (rule K-SECRET: refused whatever the allowlist says), `configmaps`/`cm` (rule K-CM: refused in v1, PENDING LEAD).
- **K-SCOPE**: a namespaced read needs `-n`/`--namespace`; `-A`/`--all-namespaces` refused; `nodes` and `top nodes` only if the allowlist sets `cluster_reads: true`.
- **K-LOGS**: `logs <pod> -n NS [-c NAME] [--tail N<=CLOUD_OPS_LOG_TAIL_MAX] [--since D<=CLOUD_OPS_LOG_SINCE_MAX_S] [--previous]`; `-f`/`--follow` refused.
- **A-SVC** (aws): only these service and command pairs: `ecs list-clusters|describe-clusters|list-services|describe-services|list-tasks|describe-tasks|describe-task-definition`; `ec2 describe-instances|describe-instance-status`; `cloudwatch describe-alarms|get-metric-statistics`; `logs describe-log-groups|filter-log-events|get-log-events`; `eks list-clusters|describe-cluster|list-nodegroups|describe-nodegroup`. Everything else refused, named in tests: `s3` (all, including `cp`, `sync`, `presign`, `ls`), `sts` (all), `configure`, `ssm`, `ecs execute-command`, `ecs update-service`, `ec2 get-console-output`, `ec2 describe-instance-attribute`, `lambda invoke`, `eks update-kubeconfig`, `eks get-token`, `logs start-live-tail`, `cloudwatch get-metric-data` (JSON query values, v1.1).
- **A-REGION**: `--region` only if the value is in the allowlist's `regions`; absent means the allowlist's first region.

The parser returns `Operation(op_id, program, params, rule_id)`; `params` holds only typed values. One `(program, verb, resource)` gives exactly one `op_id`.

**4.3 Operations and bindings.** Kubernetes ops reuse the existing ids where they exist (`k8s.list_deployments`, `k8s.list_events`, `k8s.pod_log`, `sources/kubernetes.py:27-32`) and add `k8s.list_pods`, `k8s.get_pod`, `k8s.get_deployment`, `k8s.list_replicasets`, `k8s.list_statefulsets`, `k8s.list_daemonsets`, `k8s.list_services`, `k8s.list_jobs`, `k8s.list_hpa`, `k8s.list_nodes`, `k8s.metrics_pods`, `k8s.metrics_nodes`, each bound to `("GET", path regex)` in the tool module's `READ_OPERATIONS`, which `tools.read_operations` (`tools.py:415-444`) loads and `ToolContext.fetch` enforces (`tools.py:551-568`). The `k8s.` prefix makes the existing source rules apply: a tool whose operation has a source kind's prefix needs a probe (`app.py:353-385`) and is switched off when that source's re-probe fails (`app.py:399`). AWS ops get ids `aws.<service>.<command>` (no binding in v1: only `recorded` answers them).

**4.4 Allowlist (per client).** In the tool manifest `options.allowlist`, validated at start-up: `commands` (a subset of the grammar's rule-level command names; empty means none), `namespaces`, `cluster_reads` (default false), `aws.regions`, `aws.clusters` (ECS and EKS names), `aws.log_groups` (exact names or prefixes ending `/`). Every field can only narrow: a name not in the grammar fails validation at start-up. Defaults: nothing allowed.

**4.5 Backends.** `recorded`: reads made-up JSON answers keyed by `op_id` and params from `recorded_dir`; dev only. `kubernetes_api`: needs `options.source` naming a configured `kubernetes` source (`config.py:276-296`); the tool's `secret_names` is exactly that source's token secret and its `hosts` hold that source's host, the existing coverage rule (`app.py:358-380`), so the start-up probe (`sources/kubernetes.py:319-351`, rules `:100-125`) vouches for the credential. Paging and caps reuse the source's `page_size`, `max_pages`, `json_cap_bytes`, `log_bytes` (`sources/kubernetes.py:53-64`). The body sends `Authorization: Bearer` from `ctx.secret(name)` (so `prepare_output` scrubs the token if it ever appears) and checks its lifetime first (4.6).

**4.6 Short-lived credential check.** Before any fetch the body reads the token's JWT payload (base64 only, no signature trust) and refuses when there is no `exp`, when `exp - iat > CLOUD_OPS_MAX_TOKEN_TTL_S`, or when less than `CLOUD_OPS_MIN_TOKEN_LEFT_S` remains. The demo token comes from the TokenRequest API (for example `kubectl create token <sa> --duration=1h` on the laptop sandbox, UNVERIFIED flag spelling); the secrets kind's cache TTL (`backends/table.py:244`, 300 s default) picks up a renewed one.

**4.7 Projection and masking.** One table `PROJECTION[op_id]` of kept field paths. Example, pods: `metadata.name`, `metadata.namespace`, `metadata.labels`, `metadata.creationTimestamp`, `metadata.ownerReferences[].kind|name`, `spec.nodeName`, `spec.containers[].name|image|resources`, `status.phase`, `status.conditions[].type|status|reason`, `status.containerStatuses[].name|ready|restartCount|state|lastState`. Never kept: `env`, `envFrom`, `command`, `args`, `volumes`, all annotations, `managedFields`; for ECS task definitions `containerDefinitions[].environment` values and `secrets`; EC2 `UserData`. A list over `CLOUD_OPS_MAX_RECORDS` is cut and says so (as `sources/kubernetes.py:263-271` does). Masking is the existing `prepare_output` unchanged; once P2d-2 merges, its look-alike and hidden-channel checks (built on P1's `guard/textnorm.py`) run inside it with no JG-1 change.

**4.8 Audit.** No new audit code. Every call, refused or not, ends as a `ToolCallRecord` and a `tool` event (`agent_loop.py:485-515`). The rendered text starts with one header line `cloud_ops env=<environment_name> op=<op_id> rule=<rule_id>`, so the stored output (masked) shows what ran; the audit event carries the hashes of inputs and output (`:513-515`). A repo test (AST) checks that only `cloud_ops/tool.py` imports the backends.

**4.9 Environment name.** `options.environment_name` (pattern `^[a-z][a-z0-9-]{0,30}$`; "demo" in the demo config) is a label in the header line only. No code compares it; `Config.environment` (`config.py:317`) stays the policy level.

**4.10 Start-up checks.** A new `_cloud_ops_problems(cfg, reg)` next to `_unprobed_tools` (called at `app.py:129`): validate every `cloud_ops` tool's options; refuse `recorded` when `cfg.environment != "dev"`; refuse `kubernetes_api` without `options.source`; refuse an `aws_api` backend with the outline's trigger text.

## 5. Non-functional requirements

Timeout: the tool's whole call shares `tool_timeout_s` (`config.py:333`, `tools.py:495`). Size: `max_output_bytes` (never above the redactor cap, `tools.py:83-87`) and the fetch caps. Rate: the box's per-minute and concurrency caps (`tools.py:1057-1059`). No new dependency in v1. Security path: no round cap; extended review.

## 6. Alternatives considered

- **Run the real programs (subprocess, no shell, flag allowlist, empty `HOME`).** Rejected by author: hidden config, plugins and credential programs; two programs to install; printed text is hard to project.
- **Kubernetes Python client or boto3 everywhere.** Rejected by author for Kubernetes (bypasses `ToolContext.fetch`'s host, method and path binding); boto3 only inside the future AWS adapter module.
- **An MCP server as default.** Rejected by author as default (wide tool surface, often with writes, output not projected, UNVERIFIED); outline backend with trigger "a client already runs one and accepts it in writing".
- **A string command split by `shlex`.** Rejected by author: a second quoting parser.
- **Field deny list.** Rejected by author: new fields would pass.
- **Audit intent before each read.** Rejected by author for v1: `write_intent` is for side effects (`audit/protocol.py:19-21`).
- **A capability in `backends/table.py` (brief KD2).** Rejected by the draft, section 9 C1.

## 7. Outline: `aws_api` backend (not built in v1)

Trigger: a client pilot that needs live ECS, EC2, CloudWatch or EKS reads, AND the owner's yes for an AWS account (money and a login). Shape: `cloud_ops/aws_api.py`, the only module that imports boto3; credentials from STS `AssumeRole` with `DurationSeconds` at most `CLOUD_OPS_MAX_TOKEN_TTL_S`, role ARN from config, the source identity from the deployment's workload identity (AK-G16's V-rows); one boto3 client per service with `endpoint_url` built from the allowlisted region; a start-up probe with the IAM policy simulator that fails on any non-read action (the read list is exactly the grammar's A-SVC commands); same projection; egress allowlist for the service hosts. Conditions to build: the probe, a negative test per write action, the over-breadth review. Alternatives at the same trigger: Azure and GCP adapters (outline row), an MCP backend.

## 8. Detailed implementation (no code)

Two pull requests: **JG-1a** (grammar, allowlist, recorded backend, projection, tool, start-up checks) and **JG-1b** (kubernetes_api backend, token check, a local `kind` cluster test marked opt-in). Files are listed in the ticket's "Files" field; tests and mutants in the ticket.

## 9. Reconciliation with the brief (step 6.1, AUTO: draft wins, lead may reverse)

- **C1 (contradiction).** Brief KD2: "capability `cloud_ops` in the backends table". Draft: a registry inside `cloud_ops/` selected by tool options. Why: a backends-table capability is one per deployment (`backends/table.py:386`, `DEFAULTS` `:582`), but a client may read two clusters; its factory gets a secret resolver (`backends/factory.py:50-53`), which tool code must never hold (`tools.py:8-9`); and the tool-options route reuses the source probe and switch-off rules for free (`app.py:353-399`). The frozen-core precedent is `sources/kinds.py` plus tool `options` (`tools.py:89-91`).
- **A1 (addition, changes an interface).** Kubernetes op ids share the `k8s.` prefix and reuse three existing ids, so the existing probe rules cover the tool.
- **A2 (addition, a dependency).** In-cluster deployment: AK-G16's lint L16 refuses any projected `serviceAccountToken` volume (`tickets/AK-G16.md:282`), so a deployed Jagrat pod has no cluster token. v1 demos run against the laptop's `kind` cluster from outside the kit. PENDING LEAD in the ticket.
