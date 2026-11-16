# AK-G16 render and refusal-gate flow (`deploy render`, `deploy check`)

*   **Author:** Claude (lead's session, `egm:egm-draft`, AUTO mode)
*   **Status:** Draft (for the build-start review; not yet reviewed)
*   **Date:** 2026-11-06

--------------------------------------------------------------------------------

**Read this first (honest notes).**
- **What was skipped.** AUTO mode: every section approval gate, the save-location gate and the "decide each contradiction" stop of the draft skill were skipped (order 46 PL1). Where the skill would ask the author to choose an architecture, this design takes the option the FROZEN ticket took. Where the ticket took none, the design marks the point **OPEN FOR LEAD** and does not choose.
- **A missing skill file.** The draft skill tells me to apply `resources/execution_instructions.md`. That file does not exist in the installed plugin, so it was not applied.
- **No Goldfish review yet.** The brainstorm ran without its Goldfish review: this session has no sub-agent tool (see `concepts_brief.md`). This design has had no independent review either. `egm:egm-review` comes next.
- **Code read.** Core code was read on `ce70eb5`, the last commit touching `src/`, at `<repo>/src`. Every `src/...` or `tests/...` cite below was re-read today. Ticket cites are `tickets/AK-G16.md:<line>` in `<repo>/handover`.
- **Nothing in this design exists in code yet.** There is no `src/hadavin_sdk/deploy/` folder, no `deploy` config section, no `deploy` CLI command and no `AUDIT_WRITER_SEPARATE` constant. This was checked with `ls` and `grep` over `src` and `tests`. Every behaviour of `deploy render` and `deploy check` below is design on paper.
- **What the ticket says wins.** Where this design and the ticket or a build note differ, the ticket and the build notes win. Every such place is listed in **Contradictions for the lead** below. The ticket itself is not changed.

## Overview

AK-G16-b1 adds two plan-only commands to the core CLI:
- **`hadavin-sdk --config <dir> deploy render --out <folder>`** writes plain Kubernetes files plus one container-file recipe from the client's config.
- **`hadavin-sdk --config <dir> deploy check <folder>`** reads files the client's team may have edited and refuses any file that breaks a rule.

Neither command calls a cluster, a cloud, a secret store or the network. Neither ever reads a secret value.

This design fixes four things:
- the **order** in which the two commands run their checks;
- the **refusal gate**: pilot and prod are refused until V7, the separate audit-writer database role, exists;
- the **target refusals**: no anchor, no key file, mounted-file secrets only, distinct Secret objects, and every database role mapped to a login;
- **what each part gets** in the render, and **how each lint rule fires**.

## The Problem

The ticket spreads the render and gate behaviour over many places. It sits in Interface 3 and 4 (`tickets/AK-G16.md:206-207`), in rows R1-R15 (`:267-281`), in the lint paragraph (`:282`), and in build notes BN-3, BN-4, BN-5, BN-6, BN-9, BN-10, BN-12, BN-13, BN-24, BN-26 and BN-32 (`:521-791`).

None of these places says in what order the checks run, which ones stop the run, or how the gate and the no-anchor refusal combine. These gaps matter:
- A builder who puts the gate first and stops there hides the anchor refusal from a prod config.
- A builder who runs the gate only in `render` lets `deploy check` pass a pilot folder that render would refuse.
- The prod half of the gate's own test (R16) cannot reach the gate as worded (see C3).

## Goals

*   One written order of checks, shared by `deploy render` and `deploy check`, so each builder decision has one answer.
*   The gate refuses `environment: pilot` and `prod` in both commands while `defaults.AUDIT_WRITER_SEPARATE` is `False`, and the message names V7 (BN-6 as decided by BN-32, `tickets/AK-G16.md:559-572`, `:791`).
*   The `kubernetes` render refuses whenever `backends.anchor` is not `none` (R15 as narrowed by BN-10, `:281`, `:606`).
*   Every pre-render refusal is reported at once, the same way the config reports every refusal (`src/hadavin_sdk/config.py:365-373`).
*   `deploy render` writes nothing unless its own in-memory output passes the full lint (`tickets/AK-G16.md:206`).
*   Every lint problem starts with its rule id (BN-5, `:551`).
*   Every place where this flow would contradict the frozen ticket or a build note is listed for the lead.

## Non-Goals

*   The parts build (D1), `secret_names_for` internals, the smoke test, the WSGI doors, the image build or push.
*   Any cloud adapter (V1-V3), any `deploy apply`, any Kubernetes RBAC.
*   V7 itself. Its own PR flips `AUDIT_WRITER_SEPARATE` to `True` (BN-6 item 3, `:564`).
*   Inventing refusals the ticket does not name. Gaps found are listed as OPEN FOR LEAD, not filled.
*   Changing `tickets/AK-G16.md`.

## Open Questions

*   **Q1 (C1, C2): Does `dev` render?** And if it does, must the render refuse the dev-only kinds that the config allows in `dev`?
*   **Q2 (C3): How does R16 prove the prod refusal?** As worded it cannot reach the gate.
*   **Q3 (C8): What command does the migrate Job run?** R1 says every part command starts with `deploy.entry`, but the entry only understands `--part` with the five built parts.
*   **Q4 (G1): What does `render --out` do when the folder already exists?** The ticket does not say.
*   **Q5 (G2): Does a folder given to `deploy check` that holds a file outside the plan's file list fail?** The design reads such a file as an L17 problem, from L17's "more documents than the plan's file list" (`:282`).

## Critical User Journeys (CUJs)

### CUJ 1: A client's pilot config before V7
*   **Given**: a valid pilot config with a `deploy` section and `backends.anchor: none`, and `defaults.AUDIT_WRITER_SEPARATE` as shipped (`False`).
*   **When**: the platform team runs `deploy render --out <folder>` (runbook R5).
*   **Then**: exit 2 and one `refused:` line that includes "pilot and prod need the separate audit-writer role (V7); not built yet". No file is written and no lint runs.

### CUJ 2: A prod config
*   **Given**: a prod config. It must have a signer and an anchor to load at all (`src/hadavin_sdk/backends/table.py:604`, `src/hadavin_sdk/config.py:391-394`).
*   **When**: `deploy render`.
*   **Then**: exit 2. While the gate is shut, the refusal list holds both the V7 line and the anchor line (R15). After V7, the anchor line alone still refuses. In v1 prod never renders, which matches limit O5 (`tickets/AK-G16.md:400`).

### CUJ 3: The gate is open (tests, or after V7)
*   **Given**: the fixture pilot config, with the constant set to `True` (monkeypatched in tests, BN-6 item 4).
*   **When**: `deploy render --out <folder>`.
*   **Then**: the render builds the plan, renders in memory and lints its own output with zero problems, then writes the file set of R1. Exit 0.

### CUJ 4: An edited folder
*   **Given**: the rendered folder, edited by the client's team (for example a second container added to the tick pod).
*   **When**: `deploy check <folder>` with the same config.
*   **Then**: exit 1. Every problem is listed, each starting with its rule id (here `L18: ...`).

## Technical Plan (Architecture)

### 1. The flow, stage by stage

Both commands share stages A-D and F. Only E (where the files come from) and G (what happens at the end) differ.

```
 A argparse ──► B load config ──► C target refusals (gate first in the list) ──► D plan
                 exit 2 on error     exit 2 if the list is not empty
                                                                         │
           render: E render in memory  ◄──────────────────────────────────┤
           check:  E' read <folder> through the strict loader  ◄──────────┘
                                   │
                         F lint (L17 ► L18 ► all other rules; -b2: L10, L13 on rights_for(plan))
                                   │
           render: G any problem ► exit 2, write nothing; none ► write files, exit 0
           check:  G any problem ► exit 1; none ► exit 0
```

**Stage A: parse the arguments.** argparse refuses unknown arguments with exit 2 (general Python behaviour, UNVERIFIED today). `--config` is the existing global option (`src/hadavin_sdk/cli.py:88`). `deploy` becomes a new sub-parser beside the existing ones (`:89-124`).

**Stage B: load the config.** The existing `load_config` turns every problem into a `ConfigError` (`src/hadavin_sdk/config.py:436-454`). `main` maps a `ConfigError` to `refused: <text>` on standard error and exit 2 (`src/hadavin_sdk/cli.py:70-76`); any other uncaught error exits 3 (`:77-83`). The config's own checks run here, before any deploy code:
- **Dev-only kinds refused outside `dev`.** The fake model, fake channel, fake and env secrets, the memory store and `local_dir` audit (`src/hadavin_sdk/backends/table.py:593-602`) are collected into one list (`src/hadavin_sdk/config.py:365-370`).
- **The prod rules.** Prod refuses `signer: none` and `anchor: none` (`src/hadavin_sdk/backends/table.py:604`, applied at `src/hadavin_sdk/config.py:391-392`). It refuses an anchor without `retention_ack` (`:393-394`). It refuses `ed25519_local` with a key file (`:395-396`).
- **One error for everything.** All of these are reported together in one `ValueError` that becomes a `ConfigError` (`:372-373`, `:454`).
- **The new `deploy` section's field rules** also run here, because -b1 adds the section to `config.py` (`tickets/AK-G16.md:215`). They cover:
  - patterns and ranges (Interface 4, `:207`; R12 and R14, `:278`, `:280`);
  - non-empty selector maps (BN-4 item 1, `:536`);
  - `deploy.migrate` (BN-3 item 1, `:523`);
  - the `wsgi_app` pattern (BN-9 item 3, `:596`);
  - the minimum prefix length and strict parsing of every `cidr` and `except` (BN-13, `:626-631`).
- **Duplicate YAML keys** are already refused by `_UniqueKeyLoader` (`src/hadavin_sdk/config.py:400-410`).

**Stage C: target refusals.** One function, `target_refusals(cfg, reg, deploy) -> list[str]`, runs in both commands and collects every refusal in a fixed reporting order. The order only changes the order of lines in the message. No item stops the others, except the first: without a `deploy` section nothing else can be checked.

| # | Refusal | Source | Message names |
|---|---|---|---|
| C0 | `deploy` section absent, reported alone | Interface 4, `tickets/AK-G16.md:207` | `deploy` |
| C1 | **Gate:** `cfg.environment` is `pilot` or `prod` and `defaults.AUDIT_WRITER_SEPARATE` is `False` | BN-6 items 1-2 (`:562-563`) as decided by BN-32 (`:791`); order 46 item 108 | V7 |
| C2 | **No anchor:** `backends.anchor.kind` is not `none` | R15 (`:281`) narrowed by BN-10 (`:606`) | `backends.anchor` |
| C3 | Any set signer field whose name ends in `_path`. Today that is `ed25519_local.private_key_path` (`src/hadavin_sdk/backends/table.py:217`) | BN-26 (`tickets/AK-G16.md:737`) | the field; use `private_key_secret_name` |
| C4 | Secrets kind not `mounted_file`. The mount path is `MountedFileSettings.dir` (`src/hadavin_sdk/backends/table.py:316`) | R2 and D2 (`tickets/AK-G16.md:268`, `:136`) | `backends.secrets` |
| C5 | A configured secret name that is not a valid Secret key (Kubernetes rule UNVERIFIED) | R2 (`:268`) | the name, never a value |
| C6 | Two of the six Secret object names equal (five parts plus `deploy.migrate.secret_object`) | BN-3 item 4 (`:526-527`) | `secret object <name> is used by <a> and <b>` |
| C7 | A `_role` keyword-only parameter of `store.migrate.migrate` with no `deploy.logins` entry. On `ce70eb5` these are `runtime_role`, `portal_role` and `purge_role` (`src/hadavin_sdk/store/migrate.py:283-293`) | R3 (`tickets/AK-G16.md:269`, `:163`) | the keyword |
| C8 | From -d on: `deploy.wsgi_app` missing | BN-9 item 3 (`:598`) | `deploy.wsgi_app` |

If the list is not empty: raise one `ConfigError("; ".join(list))`. That gives exit 2 through `cli.py:74-76`. No plan is built, nothing is rendered, nothing is written and no lint runs.

Gate details:
- **The gate reads the constant at call time**, as `defaults.AUDIT_WRITER_SEPARATE` through the module, never as a name copied at import. The shared test fixture can then monkeypatch it to `True` (BN-6 item 4, `tickets/AK-G16.md:565`), and R16 sees the shipped `False`.
- **`dev` is not gated** (BN-32, "dev renders stay allowed"). This follows BN-32 over I6; see C1.
- **C4 refuses some dev configs anyway.** A dev config with `fake` or `env` secrets is refused by C4 (those kinds are not `mounted_file`).
- **No new refusal is invented** for the memory store, the fake model or `local_dir` audit in a dev render; see C2.

C5 and C6 need each part's secret names, so stage C first loads the registry: `load_registry(cfg)` (`src/hadavin_sdk/registry.py:207`). It then calls `secret_names_for(cfg, reg, part)` (BN-20, `tickets/AK-G16.md:693`) and `migrate_secret_names(cfg)` (BN-3 item 2, `:524`), both from -a. Whether `load_registry` raises only `ConfigError` is UNVERIFIED (the body was not read). Any other error exits 3 (`cli.py:77-83`).

**Stage D: build the plan.** `plan_for(cfg, deploy) -> DeployPlan` (Interface 2, `tickets/AK-G16.md:205`) gives one `PartPlan` per part. Each holds the command, the secret names, the Secret object, the database logins, the egress hosts and rules, the schedule and the resources. The egress hosts note is `backends.factory.hosts` of that part's backends (`src/hadavin_sdk/backends/factory.py:60-66`; R10, `tickets/AK-G16.md:276`). Stage C has already refused every input the plan cannot express, so `plan_for` raises nothing on valid input.

**Stage E (render): render in memory.** `DeployTarget.render(plan) -> dict[str, bytes]` (Interface 3, `:206`). It is pure: no network, no secret value, no clock.
- Every YAML document is built as Python objects and written only through `yaml.safe_dump` (D2, `:135`). PyYAML is already a base dependency (`<repo>/pyproject.toml:18`).
- Every Kubernetes API group, `apiVersion`, kind and label key comes from `deploy/k8s_names.py` (BN-24, `tickets/AK-G16.md:725`). That file is the one new `ALLOWED` entry in the hard-coded-values scan. The scan's `host` pattern would otherwise flag names such as `networking.k8s.io` (`tests/test_no_hardcoded_values.py:34-38`; existing precedent for `sources/kubernetes.py`, `:54-60`).
- The container file comes from the string constant in `deploy/render_image.py` (D2, `tickets/AK-G16.md:144`; BN-17, `:673`).

**Stage E' (check): read the folder.** Read only the paths in the plan's file list, through the strict loader (L17). A file in the folder outside that list is an L17 problem; see Q5. A path in the list that is missing is an L17 problem too. That reading is an author choice, since the ticket does not say.

**Stage F: lint.** `DeployTarget.lint(files, plan) -> list[str]` (Interface 3, `:206`). Every problem starts with `L<n>: ` (BN-5 item 1, `:551`). All problems are collected. Rule order:
1. **L17, the strict loader, per YAML file.** It subclasses `config._UniqueKeyLoader` (BN-23, `:718`; `src/hadavin_sdk/config.py:400-410`). It maps that loader's duplicate-key `ConfigError` to `L17: duplicate key ...`. It also refuses aliases and anchors, the merge key `<<`, explicit tags, and more documents than the plan's file list. That a subclass can refuse each of these is UNVERIFIED (BN-23 item 4). A file that fails L17 is not checked by any other rule, because there is nothing parsed to check.
2. **L18, the closed allow-list, per parsed document.** Allowed kinds are ServiceAccount, Deployment, CronJob, Job, NetworkPolicy and Service, each with allowed field paths (`tickets/AK-G16.md:282`). Role, ClusterRole and Secret documents fail here (BN-5 items 2-3, `:552-555`).
3. **Every other rule, on every parsed document, whether or not L18 fired.** So a hostile case can assert its own id even when L18 also fires (BN-5 item 4, `:556`).
4. **-b2 only: L10 and L13** on `rights_for(plan)` (Interface 2, `:205`; `:282`), not on files.

**Stage G: finish.**
- **Render:** with any problem, exit 2 and print every problem; write nothing (Interface 3, `:206`). A problem here means a render bug: the clean render must lint clean, which is the killer of every -b1 render mutant (`:301`). With no problem, write the files under `--out` and exit 0.
- **Check:** exit 1 with any problem (Interface 3), else exit 0. A stage B or C refusal in `check` exits 2, like any `ConfigError`. The ticket does not name this code; see C4.

### 2. What each part gets in the render

This assumes the gate is open (tests or after V7) and stage C is clean. The rows come from R1 (`tickets/AK-G16.md:267`), as changed by BN-3, BN-9, BN-11 and BN-12.

| Unit | Kubernetes objects | Command | Secret volume (`items` exactly) | Network |
|---|---|---|---|---|
| namespace | 1 deny-all NetworkPolicy (`spec.podSelector: {}` allowed only here, BN-4 item 4, `:541`) | none | none | denies all ingress and egress |
| `app` | ServiceAccount, Deployment (`deploy.replicas`), Service (`deploy.port`) | -b1: exactly `[deploy.entry]` (BN-9 item 2, `:595`); -d: the Gunicorn argument list with the `deploy.server` limits and `deploy.wsgi_app` (BN-9 item 4, `:599`) | `secret_objects.app`; `secret_names_for(cfg, reg, "app")` | ingress only from `deploy.ingress` on `deploy.port`; egress = `deploy.egress.app` + the DNS rule |
| `tick` | ServiceAccount, CronJob | `[deploy.entry, "--part", "tick"]` (BN-11 item 2, `:611`) | `secret_objects.tick`; same names as `app` (P7) | `deploy.egress.tick` + DNS |
| `purge` | ServiceAccount, CronJob | `[deploy.entry, "--part", "purge"]` | runtime login + purge login (+ CA bundle) | `deploy.egress.purge` + DNS |
| `maintenance` | ServiceAccount, CronJob | `[deploy.entry, "--part", "maintenance"]` | runtime login + maintenance login (+ CA bundle) | `deploy.egress.maintenance` + DNS |
| `audit` | ServiceAccount, CronJob | `[deploy.entry, "--part", "audit"]` | runtime login + the signer's own secret; no anchor (C2) | `deploy.egress.audit` + DNS |
| `migrate` (Job, not a part) | ServiceAccount, Job with `ttlSecondsAfterFinished` from `defaults.py` and no retry (R1, L12) | **OPEN FOR LEAD (C8)** | `deploy.migrate.secret_object`; `migrate_secret_names(cfg)` (BN-3 item 3, `:525`) | `deploy.migrate.egress` + DNS |
| image | one container file | n/a | none | n/a |

Common to every pod:
- **Secret volume.** A `secret` volume with `defaultMode` the integer 288 (0o440), mounted at `backends.secrets.dir`, with `fsGroup` = `deploy.run_as_gid` (R2, `tickets/AK-G16.md:268`; Rules "Secrets", `:161`). Decimal 288 passes the file-mode mask of `src/hadavin_sdk/actions/secrets_file.py:54`, which refuses files that others may read or that group or others may write.
- **Pod hardening** as in the Security notes (`tickets/AK-G16.md:230`); `automountServiceAccountToken: false` (L2).
- **Every CronJob** carries:
  - the configured schedule with the UTC time zone (R9, `:275`);
  - `concurrencyPolicy: Forbid`;
  - `startingDeadlineSeconds: 50` (BN-12, `:619`);
  - `activeDeadlineSeconds` 55 for `tick` and `audit`, 600 for `purge` and `maintenance`;
  - `backoffLimit: 0`;
  - history limits 1 and 3 (R11, `:277`).
- **The DNS rule** opens UDP and TCP port 53 only to the `deploy.cluster_dns` selectors (L15). Every egress entry names its ports (L20).
- **Counts** (R1): 6 ServiceAccounts, 1 Deployment, 1 Service, 4 CronJobs, 1 Job, 1 deny-all and 6 allow policies, 6 secret volumes.

### 3. How each lint rule fires (after BN-5: 17 YAML rules in -b1, 2 rights rules in -b2)

| Rule | Fires when | Notes |
|---|---|---|
| L2 | `automountServiceAccountToken` not false on a pod or ServiceAccount | |
| L3 | a pod lacks any hardening item | `:230` |
| L4 | no deny-all policy; an egress rule with no `to`; ranges that, after `except`, cover all IPv4 or all IPv6; an empty selector in any `from` or `to`; an empty `spec.podSelector` outside deny-all (BN-4); a prefix shorter than `/16` or `/48`; an unparsable or host-bits `cidr` (BN-13) | set arithmetic with `ipaddress`, IPv4-mapped normalised first (`:229`) |
| L5 | a secret volume not of type `secret` with an explicit `items` list, or with a `defaultMode` other than the integer 256, or 288 with an `fsGroup` | cases 420, 440, `"0440"` |
| L6 | an `env` entry with `value` or `secretKeyRef` for a secret | Secret-object half cut (BN-5) |
| L7 | two workloads share a ServiceAccount, or reference the same Secret object (BN-3) | |
| L8 | a workload other than the migrate Job mounts the migrate Secret; the app volume holds the purge, maintenance or signer name | |
| L9 | an image reference without a digest | |
| L11 | a container without resource limits | |
| L12 | a CronJob for `migrate`, or a migrate Job that retries | |
| L14 | any egress range, after `except`, overlaps `METADATA_FORBIDDEN` | includes the NAT64 form and `192.0.0.192/32` (BN-13 item 3), both UNVERIFIED |
| L15 | a port-53 rule other than UDP and TCP to the configured DNS selectors | |
| L16 | a projected `serviceAccountToken` volume | kept by BN-5 item 4 |
| L17 | duplicate key, alias or anchor, `<<`, explicit tag, extra document (and, in this design, a file outside or missing from the plan's list) | stops further rules for that file |
| L18 | a kind outside the six, or a field path outside the allow-list (Role, ClusterRole, Secret, RoleBinding, `initContainers`, `hostPath`, `privileged`, ...) | |
| L19 | a CronJob missing a policy field or carrying another value (50 s on every CronJob, BN-12) | |
| L20 | an egress rule without ports | |
| L10 (-b2) | a rights row with `*`, an empty reason or a literal resource | on `rights_for(plan)` |
| L13 (-b2) | an identity other than `audit` holding `sign` or `anchor_put` (except `operator` with `sign`, O7); `anchor_list` held by anyone but `operator` | on `rights_for(plan)` |

L1 is cut and its number is not reused (BN-5 item 2).

## Alternatives Considered

### Alternative A: gate checked by a person only (PL20 (b))
Rejected by the lead (order 46 item 108; BN-32, `tickets/AK-G16.md:791`): "enforced by code and a test, not left to a human". Option (c), code plus a person, was not chosen either. The lead still shows O12 at the pilot gate as a separate person's step (order 45 item 16).

### Alternative B: gate first, stop at once
Rejected by author:
- It breaks the one-fix-round rule the config already follows (`src/hadavin_sdk/config.py:365`).
- For prod, it would hide the R15 refusal behind V7, so the client learns about the second blocker only after V7 merges.

### Alternative C: gate only in `deploy render`
Rejected by author:
- BN-6 item 2 names both commands (`tickets/AK-G16.md:563`), and BN-32 decides "as BN-6 describes".
- A `check` that passes a pilot folder would give the client's team a pass that `render` refuses.

### Alternative D: lint only on disk, after writing
Rejected by author:
- Interface 3 says render "writes nothing if any problem" (`:206`).
- The mutation plan kills render mutants with the clean-render lint (`:301`), so the lint must run on the in-memory output before any write.

### Alternative E: allow an anchor when "a cloud adapter is configured" (order 45 item 17 wording)
Narrowed by BN-10 (`:606`): v1 has no adapter field and `target` is `Literal["kubernetes"]`, so the refusal is unconditional.

### Alternative F: the L1 rule and L6's Secret-object half
Cut by BN-5 (`:552-555`): L18 refuses those kinds, so neither rule could ever be the only one that fails.

## Non-Functional Requirements

- **Plan-only.** No network, no cluster, no secret read (R5, `tickets/AK-G16.md:271`). Tests render to `tmp_path` and commit no hostile file (PENDING LEAD 13, `:366`).
- **Output.** A refusal or problem line names config paths, part names, secret NAMES and rule ids only, never a value, a DSN or a host.
- **Speed.** Not measured. Render and lint are pure in-memory work on about 20 small YAML documents. No number is claimed.
- **No single dependency.** PyYAML sits behind our strict loader. The `DeployTarget` protocol is the seam for V4 and V5 (`:206`, `:165`).

### Future Improvements
- V7 flips `AUDIT_WRITER_SEPARATE`. V1-V3 bring an anchor through a cloud adapter. Each needs its own change to C1 and C2.

## Contradictions for the lead (design vs. the frozen ticket or a build note; the ticket is NOT changed)

| id | Where the ticket or a build note says | What this design does | Why / the lead's call |
|---|---|---|---|
| **C1** | I6 "`deploy render` refuses a `dev` config" (`tickets/AK-G16.md:348`). The Security notes say the same (`:227`). BN-6's cost text says "`dev` is already refused (I6)" (`:568`), and so does the resolve (`reviews/AK-G16-round3-resolve.md:107`). | Follows BN-32 and order 46 item 108: "dev renders stay allowed" (`:791`). `dev` is not gated. | BN-32 overrides BN-1, BN-6 and BN-31 by name but does not name I6. The lead confirms that I6 is superseded, or reverses BN-32's sentence. |
| **C2** | No row refuses the dev-only kinds (memory store, fake model, fake channel, `local_dir` audit) in a render. Outside `dev` the config refuses them (`src/hadavin_sdk/config.py:365-370`, `src/hadavin_sdk/backends/table.py:593-602`); inside `dev` it allows them. | Adds no refusal. Only C4 (mounted-file secrets) blocks a dev config with `fake` or `env` secrets. | With C1 as decided, a dev config can render deployable-looking files backed by an in-memory store. OPEN FOR LEAD: add a render refusal of every `DEV_ONLY` kind (one new row and one mutant), or accept. |
| **C3** | BN-6 item 4: "the fixture config set to pilot and then to prod is refused, and the message names V7" (`:565`). | The R16 prod case must use a prod variant that loads: signer set, anchor set with `retention_ack: true`. Its expected refusal holds both the V7 line and the R15 anchor line, because stage C collects both. | The pilot fixture has `anchor: none` (R15). Set to `prod`, it fails at config load (`src/hadavin_sdk/backends/table.py:604`, `src/hadavin_sdk/config.py:391-392`, `:436-454`) with exit 2 before any gate code, and the message names the anchor, not V7. The lead accepts the prod variant, or rewords R16's prod half to "refused at load". |
| **C4** | BN-6 item 2: render AND check refuse pilot and prod (`:563`). Order 46 and BN-32 word it "`deploy render` REFUSES" (`:791`). Interface 3 gives `check` only "exit 1 on a problem" (`:206`). | The gate runs in both commands. In `check`, a stage B or C refusal exits 2 (`ConfigError`, `src/hadavin_sdk/cli.py:74-76`); lint problems exit 1. | The exit code for a gate refusal in `check` is the author's choice. The lead confirms it. |
| **C5** | Interface 3: render exits 2 "with every problem listed" (`:206`). | Every problem of the stage that stopped the run: a stage C refusal list stops before lint. | Lint cannot run without a plan. Low impact. |
| **C6** | Ticket line 1 and the build-notes banner say "BN-1 to BN-31 ... win" (`:1`, `:462`). BN-32 is appended after them (`:791`). | Treats BN-32 as a winning build note (order 46 item 108 is its source). | Header text only. The lead may update the banner in the next ticket touch. |
| **C7** | D2 and order 45 item 17: refuse an anchor "unless a cloud adapter is configured" (`:138`). | BN-10's unconditional refusal (`:606`). | Already settled by a build note. Listed for completeness; no action. |
| **C8** | R1: "every part command starting with `deploy.entry`" (`:267`). The entry calls `deploy.parts.main`, which parses only `--part` with the four tick parts (Interface 1d, `:204`). `Part` and `Identity` exclude `migrate` as a built part (`:201`). | **Does not define** the migrate Job's command. | No written path lets `deploy.entry` run `hadavin-sdk migrate --runtime-role ...` (`src/hadavin_sdk/cli.py:97`). OPEN FOR LEAD: (a) `deploy.parts.main` forwards a `migrate` sub-command to the core CLI; or (b) the migrate Job runs the core `hadavin-sdk migrate` command directly, which breaks R1's "every command starts with the entry" (the image holds the core, so the command exists). The ticket chose neither, so this design does not choose. |
| **C9** | BN-2 item 4 puts a budget guard "(-b1, in R11)": `ANCHOR_RECHECK_BUDGET_S + 32 < 55` (`:511`). | No budget guard in R11. | BN-32 answers PL19 (b): BN-2's budget moves to V1 (BN-1, `:481`), so the constant does not exist in v1. Settled by the build notes; listed so the -b1 builder does not add it. |

**Gaps (not contradictions; the ticket is silent):**
- **G1:** `--out` pointing at an existing or non-empty folder. The design does not choose; an existing CLI precedent refuses a non-empty score folder (`src/hadavin_sdk/cli.py:258`).
- **G2:** a file in a `deploy check` folder that is not in the plan's list. The design reads it as an L17 problem.

## Reconciliation with the brief (draft skill step 6.1)

- **Contradictions between `concepts_brief.md` and this design:** none. Each of the brief's Key Decisions 1-6 is applied unchanged.
- **Additions this design decides that the brief did not raise:**
  - C8, the migrate command (left OPEN, not decided);
  - C6, C7 and C9 (settled by build notes; listed only);
  - the fixed reporting order inside stage C;
  - L17 stopping further rules for an unparsed file;
  - G1 and G2.

  None of them changes an external interface beyond what the ticket already names.

## UNVERIFIED (not read in code, or general knowledge not checked today)

- **Kubernetes facts:**
  - the meaning of every rendered field (`ttlSecondsAfterFinished`, `startingDeadlineSeconds`, `activeDeadlineSeconds`, `concurrencyPolicy`, `timeZone`, empty selectors);
  - the rules for Secret key names and label keys;
  - Secret-volume file ownership.
- **PyYAML:**
  - that a `SafeLoader` subclass can refuse aliases, merge keys and tags;
  - that `yaml.safe_dump` writes 288 as a plain integer.
- **argparse** exits 2 on unknown arguments.
- **`load_registry`** raises only `ConfigError` on bad input (`src/hadavin_sdk/registry.py:207`, body not read).
- **Names from tickets that have not merged:**
  - `backends.store.migrate_credential_ref` (P6b2, read in ticket text only);
  - `maintenance_dsn_secret_name` (P4b2, ticket text only);
  - `secret_names_for` and `migrate_secret_names` (AK-G16-a, not built).
- **The added `METADATA_FORBIDDEN` addresses** (`fd00:ec2::254/128`, `168.63.129.16/32`, `100.100.100.200/32`, `64:ff9b::a9fe:0/112`, `192.0.0.192/32`): from memory or from the reviewer; the builder checks them (evidence item 7).
- **All of `deploy/`**: design on paper; nothing in code proves it.

## Detailed Implementation Plan

No code here; the files are the ticket's (-b1 `tickets/AK-G16.md:215`, -b2 `:216`, -d `:218`, as changed by BN-3, BN-24, BN-26).

### Target Files to Create/Modify

#### 1. `src/hadavin_sdk/deploy/lint.py` (Create, -b1; L10 and L13 added in -b2)
- **`target_refusals(cfg, reg, deploy)`**: stage C, with the gate as C1, reading `defaults.AUDIT_WRITER_SEPARATE` through the module at call time. Where it lives is the author's choice: one function shared by both commands, so the gate cannot exist in one command and not the other.
- **The strict loader (L17)**: subclasses `config._UniqueKeyLoader`.
- **The L18 allow-list and the other rules**: run in the order of section 1, stage F. Every problem is prefixed `L<n>: `.

#### 2. `src/hadavin_sdk/deploy/plan.py` (Create, -b1)
- **`plan_for`**: stage D. It assumes stage C passed.

#### 3. `src/hadavin_sdk/deploy/render_k8s.py`, `deploy/render_image.py`, `deploy/k8s_names.py` (Create, -b1)
- **Stage E**: a pure render to `dict[str, bytes]` through `yaml.safe_dump`.
- **The per-part content**: as in section 2.
- **`k8s_names.py`**: the one `ALLOWED` entry (BN-24).

#### 4. `src/hadavin_sdk/cli.py` (Modify, -b1)
- **The `deploy` sub-parser**: `render --out` and `check <dir>`, beside the existing sub-parsers (`:89-124`).
- **The flow**: A → B → C → D → E/E' → F → G.
- **Exit codes**: 2 for any refusal (through `main`, `:70-76`), 2 for render lint problems, 1 for check lint problems.

#### 5. `src/hadavin_sdk/config.py` (Modify, -b1)
- **The optional `deploy` section**: field validation as Interface 4, BN-3, BN-4, BN-9 and BN-13. It runs in stage B.

#### 6. `src/hadavin_sdk/defaults.py` (Modify, -b1)
- **Constants**: `AUDIT_WRITER_SEPARATE = False`, `CRONJOB_STARTING_DEADLINE_S = 50`, `EGRESS_MIN_PREFIX_V4 = 16`, `EGRESS_MIN_PREFIX_V6 = 48`, `METADATA_FORBIDDEN`, and the other -b1 values (`tickets/AK-G16.md:164`).
- **Layout**: in their own `# --- deployment (AK-G16-b1) ---` block, in the existing block style (`src/hadavin_sdk/defaults.py:12`).

#### 7. `tests/test_deploy_render.py`, `tests/test_deploy_lint.py`, `tests/fixtures/deploy/config/` (Create, -b1)
- **R16**: the pilot case, plus the prod variant per C3.
- **One shared fixture** that monkeypatches the gate to `True` for every other row.
- **Hostile lint cases**: each built in memory and asserting its own rule id.

#### 8. `tests/test_no_hardcoded_values.py` (Modify, -b1)
- **One `ALLOWED` entry** for `deploy/k8s_names.py` (BN-24).

#### 9. `src/hadavin_sdk/deploy/rights.py` (Create, -b2)
- **`rights_for(plan)`**: the input of L10 and L13.

### Verification Plan

- The ticket's rows R1-R16 (R16 per BN-6 and C3), the 17 -b1 lint rows, and L10 and L13 in -b2.
- Each lint problem is asserted by its rule id.
- The fail-before run on the -b1 base gives an import error for every row (`tickets/AK-G16.md:297`).
- The mutants of BN-31 under BN-32 (99 in total), including M-b54 (the gate removed, killed by R16) and M-b46 (the anchor refusal removed, killed by R15).
- The evidence commands of `tickets/AK-G16.md:312-319`.
- Nothing in this plan has been run.
