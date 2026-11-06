# AK-G16 round 1 resolve (ticket revision 1)

**Honest note (read first).** This is the resolve step: `egm:egm-resolve` in AUTO mode, with the interactive gate skipped as ordered. The skill's default `goldfish_review_report.md` is replaced by this file and its layout. I did not write revision 1, so I have no author memory of it.

I ran nothing: no pytest, no import of the package, no Python, no Postgres, no scanner, no network. Every fact below comes from reading or grepping files under `src/`, `tests/`, `.github/` and `handover/`.

**What I did NOT check:**
- All Kubernetes facts, including the ones that rows 2, 3 and 28 rest on:
  - the owner and group of files in a Secret volume;
  - the rules for Secret key names;
  - whether NetworkPolicy governs traffic to node-local metadata agents;
  - how the cluster DNS is labelled.
- Whether Trivy 0.76.0 flags YAML under `tests/`, and whether it treats a file named `Containerfile.tmpl` as a container file. Row 6's choice avoids both questions instead of answering them.
- Object-store request prices for the re-anchor cost in PL12 (stated without numbers).
- The tick steps that P4b2, AK-G1 and AK-G2-b will add (not merged; I read no code for them).
- `Approvals`' default clock.
- `tests/test_p7_tick.py` beyond the grep hit at `:82`.
- The AK-G1 and AK-G2 ticket texts (couplings taken from AK-G16's own cites).
- The `_BOUNDED` arguments of `anchor_gcs.py`.
- `verify_rows` beyond `_check_anchors`.

The re-anchor design in PL12, the build split in row 19 and the duplicate-header rule in row 15 are my design choices on paper. No code proves them.

PENDING LEAD 1 (EGM brainstorm and draft not run) stays open, as the lead's brief said. I ran neither.

- **Status:** resolved (AUTO). I did not edit the ticket, did not commit, did not push, and did not write DECISIONS.md. The author writes revision 2 from the table below.
- **Target:** `tickets/AK-G16.md` revision 1 DRAFT, commit `c816370`, full file (315 lines), all four sub-PRs.
- **Gate (order 20 item 6; order 23):** round 1 of at most 3.
  - Round 1 found 1 Blocker and 13 Majors (adversarial 8, correctness 5). Two correctness Majors repeat a finding already counted: COR-2 is the Blocker and COR-3 is ADV-9. So 11 distinct defects carry Major. Not clean.
  - The Blocker needs a lead decision (PL12) because it changes core audit behaviour.
  - Next: revision 2, then round 2 with FRESH reviewers and one Opus resolve.
  - AK-G16 is a security path. The 3-round cap applies to the ticket review only; the result review of built code has no cap.
- **Facts I checked myself (they decide rows):**
  1. **The Blocker is real.**
     - `audit/chain.py:174-176`: `_unanchored` is an in-process dict, and the code comment says a restart drops it.
     - `:302`: `checkpoint()` retries only that dict.
     - `:307-308`: it returns early when `signed_through() >= seq`.
     - `:314-319`: the anchor is put only when the INSERT returned a row.
     - `_check_anchors` (`:440-450`) then reports "checkpoint N was never anchored" for ever.
     - With a CronJob, every run is a fresh process, so one failed put is never retried.
  2. **A re-put is safe on every anchor kind.**
     - `anchors.already_there` (`audit/anchors.py:40-42`): the same bytes already under the name count as anchored; different bytes raise `AnchorConflict`.
     - S3 does this through `IfNoneMatch="*"`, then a 412, then `get_object` of that one key (`anchor_s3.py:55-68`).
     - GCS does it through `if_generation_match=0`, then download (`anchor_gcs.py:42-48`).
     - Azure does it through `overwrite=False`, then download (`anchor_azure.py:55-60`).
     - So re-putting a checkpoint needs no list right and no new right: put plus a read of one key by name, which D1's audit row already grants.
     - The body includes `alg` and `key_label` (`anchors.py:20-32`). A re-put must therefore take them from the checkpoint ROW, never from the current signer, or a key rotation would raise a false `AnchorConflict`.
  3. **No "anchored" flag can be stored on the checkpoint row.** `audit_checkpoints` is append-only, by the triggers at `0002_audit_chain.sql:30-34`. A durable flag would need a new table, a migration and a grant.
  4. **`app.build` cannot skip what the reviewers say it cannot skip (COR-1).**
     - The `Runtime(...)` constructor (`app.py:228`) and the `Approvals(...)` constructor (`:176`) take the model, the detector and the channel.
     - The scope probes and the source builds are unconditional (`:107-128`), and so is the restored-hash key (`:202-206`).
     - `purge_evidence` reads `app.runtime.hooks.hold_run_ids` (`tick.py:203`).
     - When it is given no time, `run_tick` takes the time from `app.approvals.clock()` (`tick.py:338`).
     - The only `ctx.app.*` reads in `tick.py` are: `approvals.{sweep, resend_unsent, update_message}`, `audit`, `config.*`, `runtime`, `store` (grep).
  5. **`limits` and `audit verify` share one block (cli.py:166-209).**
     - That block calls `platform_secrets.check(secrets, [b.signer, b.anchor, b.store, b.audit], set())` at `:186`, then makes the signer, anchor, store and audit.
     - It never calls `app.build`.
     - The chain factory passes `deps.signer` straight through (`chain.py:547`), and `ChainAudit` with `signer=None` skips signing (`:203`, `:299`). So `limits` can build its audit sink without a signer.
  6. **The CLI tick passes no hold hook, and holds are on by default.**
     - `cli.py:298` calls `build(None, agents)` with no `hold_run_ids`.
     - `config.py:185` sets `hold_labelled: bool = True`.
     - `tick.py:205`: with no hook, nothing is held.
     - Today nothing provides holds before K6 (`tick.py:189`). Once something does, a purge part started through the bare CLI would delete runs that should be held (row 27, a defect no reviewer raised).
  7. **The `migrate` signature** is `dsn, *, runtime_role, portal_role, purge_role, iam_auth, region, sslmode, sslrootcert` (`store/migrate.py:283-293`). The filter "keyword-only, name ends in `_role`" selects exactly the three role keywords.
  8. **The hardcoded-values test scans only `.py` string constants.**
     - `tests/test_no_hardcoded_values.py:66-83` walks `src.rglob("*.py")` and AST string constants only.
     - `sources/kubernetes.py` already needs an `ALLOWED` entry for API-group names (`:54-60`).
     - `test_every_allowed_file_exists_and_still_needs_its_entry` keeps such entries honest.
  9. **The CI scanners.**
     - `ci.yml:144`: `trivy fs --skip-dirs .venv --scanners vuln,misconfig,secret --severity HIGH,CRITICAL --exit-code 1 .`
     - The repository root has no `trivy.yaml` and no `.trivyignore` (only `.gitleaks.toml` and `.gitleaksignore`).
     - Semgrep runs `p/secrets` over `src tests demos` (`ci.yml:123`).
     - Precedent: `questions-for-lead.md` item 99 / NEEDS LEAD 30. A test fixture holding 64-hex strings turned gitleaks red on every PR. The fix needed a scanner-config decision by the lead.
  10. **The secret-file permission rule.**
      - `actions/secrets_file.py:6-8` and `:54` refuse a world-readable file, and a file writable by group or others.
      - The docstring allows `defaultMode: 0400`, or 0440 with an `fsGroup`.
  11. **The approval receiver has a consumer of production hosting today.** `approvals/receiver.py:5` and `:40-60` show a framework-free door (`handle_slack_action(approvals, headers, body)`) and a dev-only server.

## Decisions (31 finding ids, 5 duplicate pairs merged, plus 2 resolver findings = 28 rows; one decision per row)

R1-RES-1 and R1-RES-2 are defects this resolve found while checking. They are not in either report.

| id(s) | category | decision for revision 2 |
|---|---|---|
| R1-ADV-1 + R1-COR-2 (Blocker; COR Major) | **NEEDS LEAD (PL12)** | Valid (facts 1-3). The decision changes behaviour in `audit/chain.py`, so the lead decides (options below). Revision 2 writes the RECOMMENDED option (a), marked "PENDING LEAD 12":<br>• The audit part stays a CronJob.<br>• `chain.py` moves from "NOT touched" to -a's CHANGE list.<br>• D1's audit rights are unchanged: put, plus get one key, plus no list.<br>• O3 gains one sentence: "a checkpoint whose anchor put kept failing for more than N later checkpoints is reported by `audit verify` as never anchored. The chain is still protected by the next anchored checkpoint, whose signed head hash covers every earlier row."<br>New rows:<br>• **P16:** the anchor fails once, a FRESH `ChainAudit` on the same database re-anchors it, and verify is clean.<br>• **P16b:** a key rotation between the two runs still re-anchors with the row's own `alg` and `key_label` (no `AnchorConflict`).<br>• **P16c:** different bytes under the name are logged as `AnchorConflict` and never overwritten.<br>New mutants: **M-a13** (re-anchor pass removed; killed by P16) and **M-a14** (re-put takes `alg` and `key_label` from the signer; killed by P16b). If the lead picks (b), the author swaps the audit row to a one-replica Deployment and drops P16-P16c. |
| R1-ADV-2 (Major) | PROPOSE FIX | Valid. D2 and the Security notes state the volume source:<br>• It is a Kubernetes `secret` volume that references a Secret object which the CLIENT creates (runbook R4).<br>• The Secret's name comes from config (`deploy.secret_objects[<part>]`); there is no fixed default.<br>• Its `items` map each key to a file of the same name, which is exactly `secret_names_for(cfg, part)`. `mounted_file` reads `<dir>/<name>`.<br>• The render refuses a configured secret name that is not a valid Secret key (letters, digits, `-`, `_`, `.`; Kubernetes rule UNVERIFIED, the builder checks the documentation). This is folded into R2.<br>• Lint row L5 also refuses a secret volume whose source is not `secret` with `items`. CSI and SecretProviderClass are provider-specific, so they go to the adapter rows V1-V3.<br>• New limit **O9:** "who in the client's cluster may read Secret objects (Kubernetes RBAC) is the client's. The kit makes sure each part's pod mounts only its own names; it cannot stop a cluster administrator reading them." Contract line **K3** gains "cluster RBAC for secrets". |
| R1-ADV-3 (Major) | PROPOSE FIX | Valid.<br>• New lint row **L14:** any egress rule that reaches `169.254.0.0/16` or `fe80::/10` is refused. v1 has no adapter, so there is no exception.<br>• New lint row **L15:** DNS egress is only UDP and TCP port 53 to the cluster-DNS pods, chosen by a configured namespace selector and pod selector. Any other port-53 rule is refused.<br>• New lint row **L16:** any `serviceAccountToken` projected volume is refused in v1. A cloud adapter adds the audience-bound token with its own row.<br>• D2 states plainly: the neutral kit gives NO pod a cloud identity. The model key, signer and store logins come only from mounted secret files. A pilot therefore signs with a local-file signer (`ed25519_local`); cloud-key signing and cloud workload identity arrive with V1-V3. The D2 (b) "metadata address" argument is reworded to "a pod's cloud identity can be per-pod (adapter rows); one machine's cannot".<br>• Render mutants M-b30..M-b32 (L14-L16 restriction removed) and lint mutants M-b33..M-b35 (L14-L16 disabled) are added. |
| R1-ADV-4 (Major) | PROPOSE FIX (cut) | Valid. The sentence "Kubernetes runs `smoke --part app` as its start-up probe" is DELETED. v1 renders no probe and has no health surface (this joins the cut list). New row **V15**, "readiness check without negative probes", trigger: a client's platform requires readiness probes. |
| R1-ADV-5 (Major) | PROPOSE FIX (cut) | Valid (fact 8).<br>• The container-file template becomes a Python string constant in `deploy/render_image.py`. `deploy/templates/Containerfile.tmpl` and its package data are deleted, so the AST test really covers it.<br>• -b CHANGES `tests/test_no_hardcoded_values.py`: one `ALLOWED` entry for `deploy/render_k8s.py` (`{"host"}`, reason "Kubernetes API group names such as networking.k8s.io, protocol identifiers and not hosts"), the same pattern as `sources/kubernetes.py`.<br>• R8 is reworded to "the AST scan of `src/` covers `deploy/`, including the image template". |
| R1-ADV-6 (Major) | PROPOSE FIX (cut); PL13 confirms | Valid (fact 9; item 99 is the same class of collision). Chosen without touching any scanner or workflow, as the reviewer preferred:<br>• The 13 `tests/fixtures/deploy/hostile/*.yaml` files are DELETED.<br>• Each hostile case is a Python function that takes the clean render IN MEMORY and removes one restriction. The test writes the result to `tmp_path` and runs `deploy check` on it.<br>• The clean fixture config stays YAML and holds no workload manifest.<br>• Evidence command 6 renders to a scratch folder outside the repository (it already says scratch).<br>No `.github/` or `.gitleaks.toml` change, and no Trivy skip. PL13 asks the lead only to confirm. |
| R1-ADV-7 (Major) | PROPOSE FIX | Valid.<br>• D3 defines the negative secret probe per kind. For `mounted_file` (the only secrets kind the neutral kit renders), "refused" means "no such file in this part's folder", and that IS the control under test (the mount list).<br>• For any other kind in v1 the probe reports `not_checked`, which is never a pass, and the result line says so.<br>• S10 adds a precondition: the probe name is in `secret_names_for(cfg, <other part>)` and its file EXISTS in the fixture's shared source, so a typo or an empty folder cannot pass.<br>• D3 and O6 say live mode proves the mounted list, not a cloud policy.<br>• New mutant **M-c11:** for a non-file kind, a "not found" counts as refused (killed by S10). |
| R1-ADV-8 (Major) | PROPOSE FIX (reword; no new check) | Valid. K2 is reworded to "...keeps every machine's clock synchronised; the program checks each part's clock against the database clock (at most 30 seconds) when the smoke test runs at each deployment, not continuously." The operator-notes line gets the same wording. New row **V16** (continuous skew check as a tick step), trigger: the first client clock incident, or a contract that asks for it. |
| R1-ADV-9 + R1-COR-3 (Majors) | PROPOSE FIX | Valid. P3 is split honestly:<br>• **P3 (new behaviour):** `build(part="app")` starts with a provider that raises for every name outside the app's set. On the -a base it fails with `TypeError` (unknown keyword). That shows the feature is missing, and the ticket says so.<br>• **P3d ("defect shown", a characterisation row):** with the same provider, `build()` WITHOUT a part raises `ConfigError` naming the purge login (`app.py:122`), on the base AND on the new code (because `part=None` is unchanged).<br>The fail-before field quotes both outputs. M-a1's killer stays P3 on the new code. |
| R1-ADV-10 + R1-COR-4 (Majors) | PROPOSE FIX | Valid (fact 5). The -a change to `cli.py` is named in the existing block (`:166-209`):<br>• For `limits`, the check list is `[b.store, b.audit]`, the signer and anchor are not made, and the audit sink is built with `signer=None, anchor=None`.<br>• `audit verify` keeps today's list and objects (limit O7).<br>• The wording "`limits` builds with `part="operator"`" is deleted (see row 22).<br>• P12 asserts that the signer's secret NAME is never read by `limits stop` or `limits reset` (provider spy), and that their audit row is still written. |
| R1-ADV-11 (Minor) | PROPOSE FIX | Valid. D3 and O6 say live smoke performs the build-time checks:<br>• For the app part: the source scope probes, which are read-only calls to the client's systems (`app.py:123-128`).<br>• For the audit part: one test signature by the signer (`audit/signer.py:79-90`).<br>• No other part builds a signer.<br>S5 adds spies that COUNT these calls and pins them: app = number of configured sources, audit = 1 signature, others = 0. |
| R1-ADV-12 (Minor) | PROPOSE FIX (cut) | Valid.<br>• Interface 5 and D3 call `--order` "a label that ties the run to the lead's numbered order in the records; it authorises nothing. The control is the client's written yes and the access they grant (PENDING LEAD 10)".<br>• S4 stays as a parse check.<br>• **S9 is DELETED** (it guarded a gate that does not exist).<br>• M-c1 stays (killed by S4). |
| R1-ADV-13 (Minor) | PROPOSE FIX | Closed by row 5's cut: there is no template package data. So `pyproject.toml` is changed by -d only, as the hot-file list says. The -b Files line drops `pyproject.toml`. |
| R1-ADV-14 + R1-COR-6 (Minors) | PROPOSE FIX | Valid (fact 7). The rule is written down: "the keyword-only parameters of `store.migrate.migrate` whose name ends in `_role`". R3 adds two fakes:<br>• an extra non-role keyword (`audit_region`), which is ignored;<br>• an extra `audit_role` with no `deploy.logins` entry, which fails the render.<br>M-b28 is reworded to "selection rule takes every keyword-only parameter" (killed by the first fake). |
| R1-ADV-15 (Minor) | PROPOSE FIX (decided now) | H5 is decided, so the builder chooses nothing.<br>• Under WSGI, the server folds duplicate headers into one environ value; how it folds them depends on the server (Gunicorn joins them with a comma, general knowledge, UNVERIFIED). The adapter cannot count duplicates.<br>• Rule: for every header a door reads for authentication (signature, timestamp), a value that contains `,` is refused with the door's single refusal status. Other headers are passed through as the server gives them.<br>• H5 tests a joined signature and a joined timestamp.<br>The Gunicorn licence stays under PENDING LEAD 6 (ii): the default is named only after the licence files are read. |
| R1-ADV-16 + R1-COR-9 (Minors) | PROPOSE FIX | Valid. Rollback says: "-a is revertible only after -d, -c and -b are reverted, in that order". The loud-failure behaviour is named and tested:<br>• A rendered tick-part command run against a core without `--part` exits 2 (argparse).<br>• The app part run against a core without `part` fails start-up with `ConfigError` naming the secret, which is P3d.<br>The CHANGELOG line stays. |
| R1-ADV-17 (Nit) | PROPOSE FIX (split only; no other cut) | Order 8 applied item by item: cut only where deleting closes a finding.<br>• (i) `Right` and `deploy/rights.py`: KEPT. The least-privilege rule (item 5) requires the policy text and a reason per action for every identity, and this is that list. Deleting it would open a finding.<br>• (ii) The `DeployTarget` protocol: KEPT. The no-single-dependency rule needs the seam for V4 and V5; it is 3 members and deleting it closes no finding.<br>• (iii) "-d has no consumer": the premise is wrong (fact 11). The approval receiver needs production hosting now (`receiver.py:5`). Decision: -d depends on -b ONLY, ships the approval receiver's hosting, and AK-G2's door joins through one mapping line when AK-G2-b merges (coupling). This also removes -d's dependency on AK-G2-b from the split table.<br>• (iv) -b is split into **-b1**: image template, Kubernetes renderer, lint L1-L9, L11, L12, L14-L16, `deploy render` and `deploy check`, `deploy` config. And **-b2**: rights list, L10, L13, runbook. -b2 depends on -b1, and -c depends on -b2. |
| R1-ADV-18 (Nit) | PROPOSE FIX | One word: "about one sub-PR (an estimate, UNVERIFIED)". The money figures stay with PENDING LEAD 9. |
| R1-COR-1 (Major) | PROPOSE FIX | Valid (fact 4). Interface 1 gains the build design:<br>• **Full parts (`app`, `tick`):** today's build, except no signer and no anchor (the audit sink gets `signer=None, anchor=None`), no purge store, and `platform_secrets.check` over `secret_names_for(cfg, part)`. That set excludes the purge, maintenance, signer and anchor secrets.<br>• **Small parts (`purge`, `maintenance`, `audit`):** `deploy.parts.build_part(config_dir, part, *, hold_run_ids=None, secrets=None)` returns a `PartApp` with exactly six fields: `config`, `store`, `purge_store`, `audit`, `hooks`, `clock`. It builds no model, detector, channel, source, tool, executor or restored key, and runs no scope probe.<br>• **-a CHANGES `runtime/tick.py` in two reads only:** `run_tick` takes the time from `app.clock` when none is given (App gains `clock`, set from `approvals.clock`); `purge_evidence` reads `app.hooks.hold_run_ids` (App gains `hooks`). `STEPS` is not edited.<br>• New row **P17:** each small part's steps run against a strict `PartApp` that raises on any other attribute.<br>• P5, P6 and P13 then hold as written (with row 25's wording). |
| R1-COR-5 (Major) | PROPOSE FIX; relay = PL14 | Valid. One order:<br>• -a builds after P4b2 (already a dependency) and puts every step that is on main at its base into `STEP_PART`, P4b2's sweep included.<br>• A step-adding PR that merges AFTER -a (AK-G1, AK-G2-b) adds its step to `deploy/parts.STEP_PART` in the same PR; P1 fails loudly otherwise.<br>• Field 3 and the Couplings say this in the same words; no ticket calls it "not a dependency" any more.<br>• The relay lines in AK-G1 and AK-G2 are the lead's to add (PL14). With row 17 (iii), -d no longer depends on AK-G2-b. |
| R1-COR-7 (Minor) | PROPOSE FIX | Valid: the kit renders no Role and no environment value. M-b1 becomes "the app's DNS egress opened to every namespace" (killed by L15 and the clean render). M-b6 becomes "the secret volume's `items` list dropped, so the whole Secret is mounted" (killed by L5 and R2). The mutant count is unchanged by this row. |
| R1-COR-8 (Minor) | PROPOSE FIX (cut) | Valid.<br>• `Part` keeps only the five parts that are built: `app`, `tick`, `purge`, `maintenance`, `audit`.<br>• `migrate` and `operator` move to a separate `Identity` literal, used only by the rights table and `Right` (`Right.identity`).<br>• `build(part="migrate")` and `build(part="operator")` are refused with the same `ConfigError` as an unknown part; P10 adds both cases. |
| R1-COR-10 (Minor) | PROPOSE FIX | Cites updated to current main: `tick.py:335`, `:351`, `platform_secrets.py:36-63`. They stay informative, never test literals (the ticket already says so). |
| R1-COR-11 (Minor) | PROPOSE FIX | D5 and S3 state the measure:<br>• Read the local clock (t0), then the database clock, then the local clock again (t1).<br>• The part passes only if both `abs(db - t0)` and `abs(db - t1)` are at most `max_clock_skew_s`. Round-trip time counts against the part (the conservative side).<br>• Boundary: exactly 30 passes, 31 fails.<br>S3 adds a 30.0 s case with a zero-delay fake, and a case where a 29 s skew plus a 2 s delay fails. |
| R1-COR-12 (Minor) | PROPOSE FIX | Valid. "Login" in the D1 table means every `*_secret_name` value of that store entry (DSN and `sslrootcert_secret_name`, `backends/table.py:120-128`), and likewise for an anchor or signer entry. P2, P6 and P13 assert against a set written out from the fixture config file in the test (an oracle that does not depend on the code under test), and then assert that it equals `secret_names_for`. |
| R1-COR-13 (Nit) | DECLINE | The reviewer confirms the counts; no change. The counts move in revision 2 (see Counts). |
| **R1-RES-1** (resolver; Major class) | PROPOSE FIX; owner of the hold source = PL15 | Defect (fact 6): the rendered purge part calls the bare `hadavin-sdk tick`, which passes no `hold_run_ids`. With `hold_labelled: True` (the default), a held run is purged once a hold source exists.<br>Fix in AK-G16:<br>• Every rendered tick-part command is the ASSEMBLED AGENT's own entry command (new config field `deploy.entry`, a console command name), which calls `deploy.parts.main(argv, **build_kwargs)` and so passes the agent's hooks.<br>• The bare CLI `tick --part purge` exits 2 with "no hold source wired: run the purge part through the agent's entry" when `retention.hold_labelled` is true and no hook was given.<br>New rows: **P18** (the purge part through the entry calls the hook; spy) and **P18b** (bare CLI refused). New mutant **M-a15** (the hook not passed to the purge part; killed by P18). The bare `tick` with no `--part` keeps today's behaviour (P9); its pre-existing gap is PL15. |
| **R1-RES-2** (resolver; Minor) | PROPOSE FIX | The rendered secret mode should be 0440 with a pod `fsGroup`, not 0400.<br>• The render runs every part as a non-root numeric user. Kubernetes writes Secret-volume files with root as owner (general knowledge, UNVERIFIED), so a 0400 file would be unreadable by that user.<br>• `secrets_file.py` accepts 0440 with an `fsGroup` (fact 10).<br>• The render therefore writes `defaultMode: 0440` (octal 288) and `securityContext.fsGroup` = a new config field `deploy.run_as_gid` (int, greater than 0).<br>• L5 keeps accepting 0400, or 0440 with `fsGroup`, for client-edited files.<br>• S1's temporary folder uses 0440 with the test user's group.<br>• The live smoke ("own secrets resolve") is where a wrong ownership shows up; the ticket says so. |

## Positions (the reasons behind the larger calls)

- **Why recommend (a) for the Blocker.** Option (a) is a bounded re-put pass:
  1. At the start of every `checkpoint()` call, read the newest `anchor_recheck` checkpoint ROWS (`seq`, `hash`, `signature`, `alg`, `key_label`).
  2. Re-put each one with the row's own `alg` and `key_label`. Existing identical bytes count as success (fact 2).
  3. The default `anchor_recheck` comes from `defaults.py` (a block headed for AK-G16). It is a `ChainAudit` constructor argument, so `backends/table.py` is not touched unless the lead wants a config field.

  Why this option:
  - It closes the defect for every process, the long-lived ones after a restart included, with no schema change and no new cloud right.
  - It counts in checkpoints, not in time: with no new rows, the same rows keep being retried.
  - Its cost is up to `anchor_recheck` extra conditional puts per run, each answered "already there" plus one read of a single key. That is small, but a recurring request cost on the client's bill (prices not read; PL12 asks for a number only if the lead wants one).

  Option (b), a long-lived Deployment:
  - needs a new loop command;
  - still loses the retry list on every rollout, node drain or eviction;
  - only narrows the gap.

  Option (c), a durable "anchored" table:
  - needs a migration and a grant in `migrate.py`;
  - is more surface for the same result.

  Limit after (a): an anchor outage longer than `anchor_recheck` new checkpoints leaves the older ones reported as "never anchored". That report is true, and the chain stays protected by the next anchored head.
- **Why fixtures in memory and not a Trivy skip.** A skip is a scanner-config change, which only the lead makes (item 99 / NEEDS LEAD 30 shows what such a collision costs: every PR red). In-memory hostile cases scan clean, keep each rule's test next to its rule, and delete 13 files. Nothing is weaker: `deploy check` still reads real files from `tmp_path`.
- **Why `PartApp` and not optional fields on `App`.** Making `Runtime` and `Approvals` optional would touch every caller of `App` in frozen packages (P6a, P6b2, AK1-c, AK-G2-b all edit `app.py`). A separate six-field type touches only two reads in `tick.py`. A strict test (P17) catches a step that reaches for anything else.
- **Cuts taken in this resolve (order 8, each closes a finding):**
  - the start-up probe sentence (ADV-4);
  - the 13 hostile YAML files and the template package data (ADV-5, ADV-6, ADV-13);
  - S9 (ADV-12);
  - `migrate` and `operator` as build parts (COR-8);
  - `build(part="operator")` (ADV-10);
  - a continuous skew check, which is not added (ADV-8).
- **Not cut (deleting would open a finding):** the rights list, the target protocol, sub-PR -d.

## Couplings (text other owners change; this resolve edits none of them)

- **AK-G1, AK-G2-b:** a step merged after -a adds itself to `STEP_PART` (row 20; relay PL14). AK-G2's webhook door joins -d through one mapping line (row 17).
- **P4b2:** its sweep step is in `STEP_PART` from -a's base. It must read only the six `PartApp` fields (row 19); otherwise it is assigned to a full part, which the author writes down.
- **K6 / P3c (owner of `hold_run_ids`):** the hold source must reach the purge part (row 27, PL15).
- **CI and scanners (lead):** no change asked (row 6, PL13). PENDING LEAD 7 (an image build-and-scan job) is unchanged and would scan rendered files only inside that job.
- **`owner-visible-limits.md`, `contract-terms-notes.md`:** O3 is reworded and O9 added; K2 is reworded and K3 extended. These move there when the lead accepts the ticket, as the ticket already says.

## PENDING LEAD (continuing the ticket's numbering; my recommendation first)

12. **Lost anchor retries with a CronJob audit part (Blocker R1-ADV-1, R1-COR-2). This is a core behaviour change in `audit/chain.py`.**
    - (a) Recommended: a bounded re-put pass in `ChainAudit.checkpoint()`. It re-puts the newest `anchor_recheck` checkpoint rows with each row's own `alg` and `key_label`, as described in Positions, with rows P16, P16b, P16c and mutants M-a13, M-a14.
    - (b) Run the audit part as a one-replica Deployment with a loop command. There is no `chain.py` change, but every restart still loses retries.
    - (c) A durable "anchored" table, which needs a migration and a grant.

    Reversible: (a) is one method and a constructor argument. My confidence in (a): about 80 percent. The rest is doubt about the default N, and about whether the lead wants N in config rather than `defaults.py`.
13. **Hostile lint fixtures and the CI scanners (R1-ADV-6).** Recommended: confirm that NO scanner or workflow change is made. The hostile cases live in Python and are written to `tmp_path` at test time. Alternative: a path-anchored Trivy skip for a fixtures folder, a `.github/` change only the lead makes. Not recommended, given the precedent of item 99 / NEEDS LEAD 30.
14. **Relay lines in AK-G1 and AK-G2 (R1-COR-5).** Recommended: the lead adds one build-note line to each: "if this PR merges after AK-G16-a, add your tick steps to `deploy/parts.STEP_PART`; AK-G16 test P1 fails otherwise". AK-G16 edits no other ticket.
15. **Hold source for the bare CLI tick (R1-RES-1).** No hold source exists before K6, so nothing is lost today. Recommended: the ticket that delivers `hold_run_ids` (K6 or P3c) makes it reachable from config, or refuses the bare `tick` when `hold_labelled` is true and no source is wired. AK-G16 already refuses the bare `tick --part purge` (row 27). The lead names the owner.

PENDING LEAD 1 (EGM brainstorm and draft before review) stays open and unanswered. This resolve did not run either skill.

## Counts

- **Input:** 31 finding ids (adversarial 18: 1 Blocker, 8 Major, 7 Minor, 2 Nit; correctness 13: 0 Blocker, 5 Major, 7 Minor, 1 Nit). 5 duplicate pairs were merged, giving 26 rows, plus 2 resolver findings: **28 rows**.
- **Decisions:**
  - NEEDS LEAD: 1 row (PL12).
  - PROPOSE FIX: 26 rows. 5 of them are labelled cuts (ADV-4, ADV-5, ADV-6, ADV-12, COR-8); ADV-8 is a rewording instead of a new check, and ADV-13 is closed by the ADV-5 cut. Two also carry a PENDING LEAD: row 6 (PL13) and row 20 (PL14). Row 27 carries PL15.
  - DECLINE: 1 row (COR-13).
  - CONTEST: 0 rows. Row 17 (iii) rejects one sub-premise with evidence, inside a PROPOSE FIX.
  - ESCALATE: 0 rows.
- **New PENDING LEAD:** 4 (12-15), so 15 in all. PL1 is still open.
- **Expected revision 2 totals (the author recounts):**
  - **Tests:** 56 - 1 (S9) + 11 (P3d, P16, P16b, P16c, P17, P18, P18b, L14, L15, L16, and one new S3 case counted inside S3, so +10 rows) = **65 rows**, 66 if the author lists the S3 case as its own row. The -b fixture rows are now in-memory cases, not files.
  - **Mutants:** 57 + 3 (M-a13 to M-a15) + 6 (M-b30 to M-b35) + 1 (M-c11) = **67**.
  - **Sub-PRs:** 5 (-a, -b1, -b2, -c, -d).
  - **v1.1 rows:** 16 (V15, V16 added).
  - **Owner-visible limits:** 9 (O9 added).
