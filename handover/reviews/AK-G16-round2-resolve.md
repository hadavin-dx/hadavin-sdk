# AK-G16 round 2 resolve (ticket revision 2)

**Honest note (read first).** This is the resolve step, `egm:egm-resolve` in AUTO mode, with the interactive gate skipped as the brief orders. This file replaces the skill's default `goldfish_review_report.md` and uses its layout. I did not write revision 2, so I have no author memory of it.

**What I ran.** I ran no pytest, no import of the package, no Postgres, no scanner and no network call. I ran one `python3 -I` for arithmetic: file-mode bits and request counts. Every other fact below comes from reading or grepping `src/` at `ce70eb5` (`git log -1 -- src`), `handover/tickets/` and `handover/LEAD-ORDERS.md`.

**What I did NOT check:**
- Every Kubernetes fact: Secret-volume ownership and `fsGroup`, CronJob field meanings, NetworkPolicy `except` semantics, and whether metadata agents on the node obey NetworkPolicy.
- The extra cloud metadata addresses named in ADV-3. They come from memory and stay UNVERIFIED; the builder checks them against provider documents.
- How PyYAML and `kubectl` differ on duplicate keys, aliases and tags.
- Object-store prices. The cost multiplier is arithmetic only; the dollar figures stay with PENDING LEAD 9.
- The P2a stopper and reset field names.
- Whether any K6 or P3c ticket exists outside `handover/tickets/`. There is no `K6.md` or `P3c.md` there.
- The text of `tests/` and `ci.yml` on `d1ed085`.

**What is design on paper.** The decisions on the re-anchor checks (ADV-1, ADV-8, R2-RES-2), the audit-lag step (ADV-4) and the strict loader (ADV-5) are designs only; no code proves them. PENDING LEAD 1 (EGM brainstorm and draft not run) stays open. I ran neither skill.

- **Status:** resolved (AUTO). I did not edit the ticket, did not commit, did not push and did not write DECISIONS.md. The author writes revision 3 from the table below.
- **Target:** `tickets/AK-G16.md` revision 2 DRAFT, commit `6d47d13`, full file (401 lines).
- **Gate:** round 2 of at most 3 (order 20 item 6).
  - Round 2 found 0 Blockers and 13 Majors (adversarial 8, correctness 5). Not clean.
  - Round 3 is the last ticket round. After it, the remaining Majors become build-time fixes, under the design-doc stop rule in `.claude/rules/review-loop-speed-rules.md`.
  - The RESULT review of built code has no cap (security path).
  - **Build-blocking:** PENDING LEAD 16, 17 and 18 below must be answered before -a or -b1 starts building the parts they name. The brief says: do not build ADV-2's path meanwhile.
- **Lead answers applied (order 43 item 102):** PENDING LEAD 12, 13, 14 and 15 are **ANSWERED**. Revision 3 removes every "MEANWHILE (NEEDS LEAD 12-15)" marker and writes decided text (row COR-13).

## Facts I checked myself (they decide rows)

1. **A forged checkpoint row is possible, and so is a stall (ADV-1, R2-RES-1).**
   - The runtime role holds `SELECT, INSERT` on `audit_checkpoints` (`store/migrate.py:58`, `_APPEND`).
   - `checkpoint()` inserts with `ON CONFLICT (seq) DO NOTHING` (`audit/chain.py:310-313`) and anchors only a row it got back (`:318-319`).
   - `signed_through()` is `MAX(seq)` over every row, checked or not (`:290-293`), and `checkpoint()` returns early when `signed_through() >= seq` (`:307-308`).
   - So one junk row at a very large `seq`, inserted by anything that holds the runtime login, stops all future signing. The defect exists today (every process holds that login) and is NOT new with parts. The reviewers did not name it (R2-RES-1).
2. **Verify knows only one public key.**
   - `ChainAudit.verify()` takes `self.signer.public_key()` (`chain.py:352`) and checks every checkpoint with it (`_check_checkpoints`, `:414-437`).
   - `verify_anchor_bodies` reports more than one `key_label` as a problem (`:507-510`).
   - So after a key rotation, today's core already cannot check old-key checkpoints. The audit part holds no old public key, and there is no keyring in config.
3. **Without a signer, `checkpoint()` does nothing.** It returns `None` at once (`chain.py:299-300`), so a re-anchor pass placed inside it runs only in a process that has a signer. With `part=None` (today's behaviour) that is EVERY process that signs inline, the app included (R2-RES-2).
   - Each put can wait up to about 3 s to connect plus 5 s to read, with 2 attempts (`anchor_s3.py:89`).
   - So during an outage, a pass of N puts on the request path could take minutes.
4. **The anchor has no way to sign in.**
   - Anchor settings have no `*_secret_name` field: S3 has bucket, region and `endpoint_url` (`backends/table.py:159-175`); Azure and GCS have only a URL or a bucket (`:177-189`).
   - `anchor_s3.build` uses the ambient boto3 credential chain (`anchor_s3.py:89-92`).
   - So in the neutral kit (no cloud identity, L16 refuses projected tokens, and P6b2 N2 refuses static-key variables) the audit part has NO defined way to authenticate to any anchor (ADV-2).
   - `NOT_PROD` refuses `anchor: none` only in prod (`table.py:604`), so a pilot may run without an anchor.
5. **`limits` reads the purge login (COR-1).**
   - `secret_names(settings)` returns every set `*_secret_name` (`platform_secrets.py:18-20`).
   - The store entry carries `purge_dsn_secret_name` (`table.py:120`) and `sslrootcert_secret_name` (`:130`).
   - The `limits` and `audit verify` block checks `[b.signer, b.anchor, b.store, b.audit]` (`cli.py:186`).
6. **The signer probe signs once at build time (COR-3).** `probe()` signs and verifies a test message (`audit/signer.py:79-90`), and `build_local` calls it (`:116`).
7. **The CLI tick path (COR-5).** `cli._tick` takes no arguments, checks qualification per agent, calls `build(None, agents)` (`cli.py:299`) and maps errors to exit codes: `StoreUnavailable` to 4, `ConfigError` to 2, anything else to 2 (`:300-308`).
8. **`App` (COR-6).** It is a dataclass whose fields after `runtime` all have defaults (`app.py:45-59`). `purge_evidence` reads `app.runtime.hooks.hold_run_ids` (`tick.py:203`).
9. **The hold source belongs to K6 (PL15).**
   - `runtime/tick.py:189-190` says "none before K6".
   - The hook is declared at `runtime/agent_loop.py:175-178` and passed at `app.py:72` and `:225`.
   - P6a lists `hold_run_ids` as a live hook (`tickets/P6a.md:21`, `:107`).
   - No ticket under `tickets/` names P3c as the hold source. A grep of `P3a.md` for P3c with "hold" found nothing relevant.
10. **File modes (COR-10, RES-2), by arithmetic.**
    - Decimal 288 is 0o440, and decimal 256 is 0o400. Both pass the mask of `secrets_file.py:54`.
    - Decimal 440 is 0o670, and 420 is 0o644. The mask refuses both.
11. **No bootstrap secret names exist today (COR-11).**
    - Every secrets kind on `ce70eb5` has no `*_secret_name` field: env, aws, vault, azure, gcp, mounted_file (`table.py:141-149`, `:255-262`, `:310-320`).
    - Vault reads its token from an environment variable or a service-account token path (`:257-261`). L6 and L16 refuse both in the neutral kit.
12. **Other checks.**
    - P4b2's field is `maintenance_dsn_secret_name` (`tickets/P4b2.md:203`).
    - `pyyaml==6.0.3` is a base dependency (`pyproject.toml:18`).
    - `retention.purge_every_s` exists (`config.py:190`).

## Decisions (30 finding ids; 2 duplicate pairs merged; plus 2 resolver findings = 30 rows; one decision per row)

Category labels:
- "PROPOSE FIX (INFORM)" means my decision on my recommendation, final unless the lead says otherwise.
- "NEEDS LEAD" means an owner hard rule is touched (least privilege, secrets), so the lead decides.

| id(s) | category | decision for revision 3 |
|---|---|---|
| R2-ADV-1 (Major) | PROPOSE FIX (INFORM); the deeper role question is PL16 | Valid (facts 1, 2). The re-anchor pass re-puts a row ONLY if it passes all three checks:<br>(i) its `key_label` equals `signer_label(current signer)` and its `alg` equals `signer.alg`;<br>(ii) its signature verifies with the current public key over `_signed_message(seq, hash)`;<br>(iii) its `hash` equals `audit_entries.hash` at that `seq`.<br>A row that fails any check is skipped and logged by kind only ("checkpoint row failed check: signature, hash or key"), never re-put.<br>**Window:** the newest N rows that PASS, with `seq <= head`, reading at most `4 x N` rows. That scan cap is a validated `defaults.py` value. Rows beyond the cap are counted in one error line. So N junk rows cannot push a genuine row out of the window unless there are more than 3N of them, and then the error line says so.<br>**Rotation:** the core has no old public key (fact 2), so a row under another key is SKIPPED and logged "signed by a different key: not rechecked". It is not re-put. This replaces revision 2's "re-put with the row's own alg and key_label" for other keys. A keyring is new surface; it joins V8 as a written row.<br>**New rows:** P16e forged signature; P16f wrong hash; P16g 3N junk rows below head plus one genuine unanchored row (the genuine one is re-anchored).<br>**P16b rewritten:** after a key rotation, the old-key row is skipped with that log line; nothing raises.<br>**Mutants:** M-a16 signature check removed (P16e); M-a17 hash check removed (P16f); M-a18 window counts unchecked rows (P16g). M-a14 is reworded to "key check removed: a row under another label is re-put" (P16b). |
| R2-ADV-2 (Major) | **NEEDS LEAD (PL17)**; not built meanwhile | Valid (fact 4). It touches secrets and least privilege, so the lead decides (options in PL17). Revision 3 writes the question and the options only. It does NOT write an anchor-authentication path as decided, adds no lint rule for one, and keeps PL11 and O5 marked "depends on PL17". |
| R2-ADV-3 (Major) | PROPOSE FIX (INFORM) | Valid. L4 and L14 become set arithmetic in `deploy/lint.py` using Python's `ipaddress` module:<br>• For each egress `ipBlock`, take `cidr` minus every `except` entry. Refuse the rule if what remains overlaps the forbidden set.<br>• The forbidden set is a `defaults.py` tuple: `169.254.0.0/16`, `fe80::/10`, `::ffff:169.254.0.0/112`, plus `fd00:ec2::254/128`, `168.63.129.16/32` and `100.100.100.200/32`. Those last three are UNVERIFIED; the builder checks each against the provider's documents and removes any it cannot confirm, saying so in the evidence.<br>• L4 refuses any egress rule whose ranges, after `except`, cover all IPv4 or all IPv6 addresses (two /1 halves included). It also refuses an egress rule with no `to`, which allows every destination.<br>• Mapped IPv6 is normalised before the comparison.<br>**Hostile cases:** overlap through a /8, through two /1 halves, through mapped v6, and through an `except` that leaves a metadata address uncovered.<br>**Mutants:** M-b36 L14 compares exact strings only; M-b37 `except` ignored. |
| R2-ADV-4 (Major) | PROPOSE FIX (INFORM) | Valid: the unsigned period is unbounded, and nothing in v1 notices.<br>• **O3 is reworded:** "Audit rows written after the last signing pass are linked but not signed. If the signing job stops, fails or is evicted, that period has no upper limit. The tick part logs an error and marks its step failed once the oldest unsigned row is older than `audit.max_unsigned_s`. Nothing in v1 alerts a person (V11)." The phrase "about one minute" is deleted, and so is any "no worse than today" claim.<br>• **New tick step `audit_lag`** (read-only, assigned to the `tick` part, appended to `STEPS` in -a). It compares `MAX(seq)` and the age of `audit_entries` with `signed_through()`, using only rows that pass the ADV-1 check. Past the bound it fails the step: `tick_state.last_error` shows it, plus one log line.<br>• The bound `max_unsigned_s` is a validated `defaults.py` value: default 600 s, range 60-3600 (thresholds come from config, so this does not bend the owner rule).<br>• This is one more `STEPS` edit by -a. Hot files and P1 say so.<br>**New row:** P19 (lag beyond the bound fails the step; within it, it passes). **Mutant:** M-a20 bound ignored (P19). |
| R2-ADV-5 (Major) | PROPOSE FIX (INFORM) | Valid.<br>• **L17 strict loader:** a `yaml.SafeLoader` subclass that refuses duplicate mapping keys, aliases and anchors, merge keys `<<`, any explicit tag, and more documents than the plan's file list.<br>• **L18 closed allow-list:** kinds {ServiceAccount, Deployment, CronJob, Job, NetworkPolicy, Service}, with a per-kind allowed field-path list in `deploy/lint.py`. Anything else is refused: RoleBinding and every other RBAC kind, `initContainers`, `ephemeralContainers`, a second container, `hostPath`, `privileged`, `hostNetwork`, `hostPID`, `hostIPC`, unknown fields.<br>• Each gets an in-memory hostile case, and L17 and L18 each get a disable mutant (M-b38, M-b39).<br>• D0 (a) gains one sentence: "`deploy check` reads files only; it cannot see what is running in the cluster." |
| R2-ADV-6 + R2-COR-2 (e) (Majors) | PROPOSE FIX (INFORM) | Valid. CronJob policy fields go in `defaults.py`, rendered and linted:<br>• `concurrencyPolicy: Forbid` for every CronJob;<br>• `startingDeadlineSeconds` shorter than the shortest period (50 for every-minute parts);<br>• `activeDeadlineSeconds` 55 for tick and audit, 600 for purge and maintenance;<br>• `backoffLimit: 0` (the next schedule is the retry);<br>• history limits: success 1, failed 3.<br>The Kubernetes meaning of each field is UNVERIFIED.<br>**New row:** R11 (render pins each field). **Lint:** L19 refuses a CronJob that lacks one of them or carries any other value. **Mutant:** M-b43 `Forbid` dropped. |
| R2-ADV-7 (Major) | **NEEDS LEAD (PL18)** | Valid. The migration login is a schema-owner credential kept in the cluster for good. That is least privilege, so the lead decides (PL18). Whatever the answer, revision 3 adds:<br>• L8 extended: only the migrate Job mounts the migration secret;<br>• limit O10 in plain words, naming who holds that login. |
| R2-ADV-8 (Major) | PROPOSE FIX (INFORM) | Valid. **N = 30**, as a validated `defaults.py` value `ANCHOR_RECHECK = 30`, range 1-120 (checked at import by a guard test). There is no config field; order 43 says `defaults.py`.<br>Why 30: at one audit pass per minute it covers a 30-minute anchor outage. The cost is in ADV-13. The reviewer's 10 covers only 10 minutes. The lead may lower it.<br>**New row:** P16d (window edge: with N+1 rows that pass, the newest N are re-put and the (N+1)th is not). **Mutant:** M-a19 the window is off by one (P16d). |
| R2-ADV-9 (Minor) | PROPOSE FIX | Valid.<br>• **Per-field patterns:** `entry` is a console-script name `^[A-Za-z][A-Za-z0-9_.-]{0,63}$`; `namespace` and each `secret_objects` value are DNS labels; `logins` keys are `_role` keywords and values are plain role names (the same rule as `migrate.py:298-300`); `schedules` are 5 fields drawn from `[0-9*/,-]`.<br>• One line: "the renderer builds Python objects and writes them only through `yaml.safe_dump`; no string templating of YAML".<br>• `egress_cidrs` entries become `{cidr, ports: [int 1-65535], protocol: TCP\|UDP}`, with ports required. **L20** refuses an egress rule without ports.<br>**New row:** R14 (a hostile config with a newline in `namespace` and a `:` in `entry` is refused). **Mutant:** M-b44 ports dropped (L20). |
| R2-ADV-10 (Minor) | PROPOSE FIX | Valid. `rights_for` lists the operator's `sign` and `anchor_list`, which is honest about O7. L13 is reworded: "any identity other than `audit` holding `sign` or `anchor_put` is refused, except `operator` holding `sign` (named exception, reason O7, until V8); `anchor_list` may be held only by `operator`". |
| R2-ADV-11 (Minor) | PROPOSE FIX | Valid. For `mounted_file`, the negative probe checks only whether `<dir>/<name>` exists, using `os.lstat`. It never opens the file and never calls `provider.get`. S10 adds a spy on `open` and `os.open` that records 0 opens of the probe name, and a mutant M-c13 (the probe reads the file). |
| R2-ADV-12 (Minor) | PROPOSE FIX (wording; keep) | Kept: deleting the rights list would reopen least-privilege rule item 5 (the policy text and a reason per action). Revision 3 states that `deploy/rights.py` is the written rights list and that nothing consumes it until V1-V3. The lead may cut -b2 if time is short; L13 and L10 leave with it. |
| R2-ADV-13 (Minor) | PROPOSE FIX | Valid. PL12's cost text gains the multiplier. At one pass per minute that is 43,200 passes a month, and each makes up to N conditional puts plus up to N single-key reads. With N = 30, that is up to 1,296,000 of each per month (arithmetic, fact 10). Prices stay with PENDING LEAD 9. |
| R2-ADV-14 + R2-COR-12 (Nits/Minor) | PROPOSE FIX | Valid. The fail-before plan states one expected result per row on the -a base:<br>• P16: fails ("never anchored").<br>• P16b: fails (no "different key" log line).<br>• P16c: asserts the logged `AnchorConflict` (caplog) AND 0 overwrites, so it fails on the base (no log line).<br>• P16d to P16g: fail (no pass exists).<br>The sentence "or pass by accident" is deleted. |
| R2-ADV-15 + R2-COR-15 (Nits) | PROPOSE FIX | One sentence: "the hostile lint cases are N YAML cases (-b1) plus 2 rights-row cases (-b2, L10 and L13)". N is recounted after L17-L20. |
| R2-COR-1 (Major) | PROPOSE FIX | Valid (fact 5).<br>• **`limits stop` and `limits reset`:** the check list is `[b.store.model_copy(update={"purge_dsn_secret_name": None}), b.audit]`, so the runtime login and the CA bundle are read and nothing else.<br>• **`audit verify`:** the same stripped store, plus the signer and the anchor.<br>• The D1 operator row is corrected.<br>• P12 asserts the exact set read against a written oracle, for both commands.<br>**Mutant:** M-a21 purge name still read (P12). |
| R2-COR-2 (a-d, f) (Major) | PROPOSE FIX (INFORM) | Valid. New `deploy:` fields:<br>• `ingress: {namespace_selector, pod_selector}` (label maps; the source of app ingress);<br>• `port` (int 1024-65535);<br>• `replicas` (int 1-20);<br>• `server: {workers, timeout_s, limit_request_line, limit_request_fields, limit_request_field_size}`, validated, defaults in `defaults.py`; H6 and -d read these, and DoorLimits keeps the body caps only.<br>**Mount path:** the secret volume's `mountPath` equals `backends.secrets.dir` (`table.py:316`); the render refuses any other secrets kind for the `kubernetes` target (closes fact 11's Vault path). R2 asserts the path.<br>**R1 counts** gain 1 Service. **Schedules:** purge and maintenance default `*/15 * * * *`; the step's own `retention.purge_every_s` still decides (`config.py:190`).<br>**New row:** R12 (each new input reaches the render; a missing one refuses it). (e) is in the row ADV-6 + COR-2 (e). |
| R2-COR-3 (Major) | PROPOSE FIX | Valid (fact 6). Spies count from the moment build returns. P5 reads "after build: exactly 1 sign call and 1 anchor put for one checkpoint". S5 reads "build-time: 1 signature (the probe) for `audit`". P8's spy is counted the same way. M-a9 is unchanged. |
| R2-COR-4 (Major) | PROPOSE FIX | Valid. The rollback text becomes: "after -a is reverted, a rendered command fails loudly. The entry's import of `deploy.parts.main` raises `ImportError`, and an old `build()` called with `part=` raises `TypeError`." The P3d claim is dropped from Rollback.<br>**New plan-only row:** P20 (with `deploy.parts` hidden by a stub import hook, and with a `build` stub that has no `part` parameter, `main` and the entry exit non-zero with a one-line message, and nothing is built). |
| R2-COR-5 (Major) | PROPOSE FIX | Valid (fact 7). `cli._tick` is refactored into one function, `run_tick_command(part: Part \| None = None, **build_kwargs) -> int`, which does qualification, logging, build and the exit-code mapping. `cli._tick()` and `deploy.parts.main` both call it, so there is one copy.<br>**New row:** P8b (on the small-part path, a store that cannot be reached gives 4 and a config error gives 2). **Mutant:** M-a22 `StoreUnavailable` mapped to 2 (P8b). |
| R2-COR-6 (Minor) | PROPOSE FIX | Valid (fact 8). `App` gains read-only PROPERTIES, not fields: `hooks` returns `self.runtime.hooks`, and `clock` returns `self.approvals.clock`. So there is no dataclass-default problem and they cannot drift. `PartApp` keeps its two plain fields.<br>**New row:** P21 (a hook replaced on `app.runtime.hooks` after build is seen by `purge_evidence`). |
| R2-COR-7 (Minor) | PROPOSE FIX | Valid (`platform_secrets.py:58-63` stops at the first sorted failure). P3d's provider fails ONLY the purge name. |
| R2-COR-8 (Minor) | PROPOSE FIX | Valid. D5 and S3 state where the delay sits and the sign of the skew:<br>• delay before the database read, database +29 s: fails;<br>• delay before the database read, database -29 s: passes;<br>• delay after the database read, database -29 s: fails (only t1 exceeds).<br>**Mutant:** M-c12 uses t0 only (killed by the last case). |
| R2-COR-9 (Minor) | PROPOSE FIX | M-c10 moves to -b1 with a config test that refuses 31 and 0. Its row stays inside the S3 text as a config case, now in -b1. Counts: -b1 +1 mutant, -c -1. |
| R2-COR-10 (Minor) | PROPOSE FIX (also the lead's plan-only file-mode test, order 43) | Valid (fact 10).<br>• The renderer writes the integer 288 (`0o440`), never the text `0440`.<br>• L5 parses the integer and accepts only 256, or 288 with an `fsGroup`.<br>• **New plan-only row R13:** apply exactly the `secrets_file.py:54` mask to the rendered `defaultMode` and expect a pass. A rendered 440 (that is, 0o670) must be refused.<br>**Mutant:** M-b42 writes decimal 440 (R13, L5).<br>The Kubernetes ownership facts stay UNVERIFIED (RES-1 and RES-2 of round 1, accepted by order 43). |
| R2-COR-11 (Minor) | PROPOSE FIX (with a fact) | Today the set is empty (fact 11). One sentence anyway: "bootstrap names in the secrets entry's own settings belong to every part's set". P2 adds a fixture with a fake secrets kind that carries one such name. |
| R2-COR-13 (Minor) | PROPOSE FIX | Valid. Revision 3 marks PL12-15 ANSWERED with order 43 item 102 and turns the MEANWHILE texts into decided text:<br>• **PL12 (a):** N is in `defaults.py`; P16 simulates one failed anchor write and proves the NEXT tick (`tick --part audit`, in a fresh process) anchors it.<br>• **PL13 (a):** no scanner or workflow change.<br>• **PL14:** the relay line is added to AK-G1 and AK-G2. The lead ordered it; the next revision's author or the lead adds the line. This resolve edits neither file.<br>• **PL15:** AK-G16 owns NO hold source. It refuses only a bare `tick --part purge` and runs every tick part through the agent's entry. The bare `tick` with no `--part` is unchanged (P9). The hold source belongs to **K6** (fact 9); Couplings say "K6", not "K6 or P3c".<br>• RES-1 and RES-2 accepted; the Kubernetes facts are marked UNVERIFIED; plan-only file-mode test R13. |
| R2-COR-14 (Nit) | PROPOSE FIX | Name `maintenance_dsn_secret_name` (`tickets/P4b2.md:203`). The P2a stopper and reset fields read "as named in P2a-1" (not checked). |
| **R2-RES-1** (resolver; Major class) | **NEEDS LEAD (PL16)** | Defect (fact 1), pre-existing: anything holding the runtime login can insert a junk checkpoint row and stall signing, permanently with one row at a huge `seq`. Revision 3 adds the code defence in -a either way:<br>• `signed_through()` for the decision in `checkpoint()` counts only rows with `seq <= head` that pass the ADV-1 checks;<br>• a row beyond head is logged by kind.<br>**Residual:** a compromised app part can still pre-fill a seq range so that the genuine inserts conflict. Signing then pauses over that range. The pause is detected (verify reports the invalid signatures, and the lag step fires) but not prevented. Only role separation prevents it, which is least privilege, so the lead decides (PL16).<br>**New row:** P16h (junk row beyond head: signing continues). **Mutant:** M-a24 `signed_through` counts every row. |
| **R2-RES-2** (resolver; Major class) | PROPOSE FIX (INFORM) | Defect (fact 3): with `part=None`, the pass would run inline in the app on every checkpoint, with up to N slow puts during an outage. Decision:<br>• The pass runs only when `anchor_recheck > 0`. `ChainAudit`'s default is 0. Only the audit part's build passes `ANCHOR_RECHECK`. So `part=None` is exactly today's behaviour (P9).<br>• The pass stops at the first put that fails with anything other than `AnchorConflict` (an outage), so one run fits inside `activeDeadlineSeconds`.<br>**New row:** P22 (`part=None` makes 0 re-puts; with an anchor that raises on every put, the pass makes 1 attempt and stops). **Mutant:** M-a23 the pass is on with `part=None` (P22). |

## Positions (the reasons behind the larger calls)

- **Verify, then re-put; never trust a row.** The audit part is the only part with the key. It can check a row as cheaply as it can sign one (one public-key verify plus one indexed read). Anchoring an unchecked row would let the least trusted part (the app, which holds INSERT) write into the store that even we cannot rewrite, for good. Skipping rows signed by another key is honest, because today's `verify` cannot check them either (fact 2).
- **Lag detector as a tick step, not only a smoke check.** Smoke runs once per deployment, so it would never see a CronJob that stops on day 3. A read-only step in the `tick` part needs no new right and puts the failure where an operator already looks (`tick_state.last_error`). Paging a person is still V11, and O3 says so plainly.
- **N = 30.** The value balances the outage covered (30 minutes) against requests (about 1.3 million conditional puts a month). Lowering it is a one-line change of a validated constant.
- **Cuts considered.** Deleting -b2 would close ADV-10, ADV-12 and ADV-15, but it reopens the least-privilege rule's "reason per action" item, so it is kept (the lead may cut it). No other deletion closes a finding.

## Couplings (text other owners change; this resolve edits none of them)

- **K6:** owns the hold source (PL15 answered). AK-G16 only refuses the bare `tick --part purge`.
- **AK-G1, AK-G2:** the relay line ordered by PL14. -a also appends `audit_lag` to `STEPS` (ADV-4). AK-G2-b appends after it, and P1 still covers both.
- **P3a/P4d chain (`store/migrate.py`):** touched only if the lead picks PL16 (b).
- **PL11, O5:** depend on PL17.

## PENDING LEAD (continuing the ticket's numbering; my recommendation first)

12-15. **ANSWERED** (order 43 item 102); applied in row COR-13.

16. **Who may write audit checkpoint rows (R2-RES-1, ADV-1; least privilege).**
    - (a) **Recommended for v1:** keep the runtime role's INSERT (`migrate.py:58`) and add the code defence above (checked window, `signed_through` over checked rows, logging, the lag step). Add limit O11 in plain words: "a compromised work part can pause audit signing for a while; this is detected, not prevented". Make V7 (a separate audit role) required before the first prod.
    - (b) **V7 now:** a new audit-writer role owns INSERT on `audit_checkpoints`, and the runtime role loses it. This is a `migrate.py` change in the frozen P3a/P4d chain. It also means `part=None` inline signing must be refused in pilot and prod, which changes today's behaviour for every current user.

    Owner rule 1 names "audit writer (append-only)" as its own identity, which points to (b). I still recommend (a) for v1, because integrity is kept (forged rows fail verify), the hole already exists today, and (b) reopens a frozen chain. Confidence about 60 percent. Reversible: (b) can follow as V7.
17. **How the audit part reaches a locked anchor in the neutral kit (R2-ADV-2; secrets and least privilege).** NOT built until answered.
    - (a) **Recommended:** the neutral kit renders NO anchor. The kubernetes render refuses a config whose `backends.anchor` is not `none` unless a cloud adapter is configured (none exist in v1). A neutral pilot therefore signs with `ed25519_local` and has no proof copy. Any locked anchor arrives with V1-V3 through that cloud's short-lived workload identity. O5 is reworded: "the neutral kit alone runs a pilot without a stored proof copy; a proof copy needs a cloud adapter". PL11's "the client's own S3-compatible store" route leaves v1.
    - (b) A new `access_key_secret_name` (or similar) on the S3 anchor settings, read through the secrets kind from a mounted file. That is a long-lived static key, against "short-lived credentials only". It also changes `backends/table.py` and `anchor_s3.py`, both NOT touched today.
    - (c) A projected web-identity token file for the audit pod. That is a cloud identity in all but name: it needs an adapter and conflicts with L16 in v1.

    Confidence in (a): about 75 percent. The doubt is whether a pilot without a proof copy is acceptable to the first client. The owner may want (b) with rotation for a client-run MinIO.
18. **Lifetime of the migration login in the cluster (R2-ADV-7; least privilege).**
    - (a) **Recommended:** the runbook creates the migrate Secret just before the Job, and the Job is rendered with `ttlSecondsAfterFinished`. The runbook then deletes the Secret right after the Job ends (R7: a client operator step; the Kubernetes field meaning is UNVERIFIED). L8 is extended: only the migrate Job mounts it. Limit O10: "the client's database owner holds the schema-owner login; it is in the cluster only while the migrate Job runs".
    - (b) The Job fetches the login from the client's secret store at run time. That needs a cloud identity, so it is an adapter row.
    - (c) Keep it in the cluster for good, as revision 2 has it (not recommended).

## Counts

- **Input:** 30 finding ids (adversarial 15: 8 Major, 5 Minor, 2 Nit; correctness 15: 5 Major, 8 Minor, 2 Nit). 2 duplicate pairs were merged (ADV-14 + COR-12, ADV-15 + COR-15). ADV-6 also takes COR-2 (e), and COR-2 keeps its own row for (a-d, f). Plus 2 resolver findings (R2-RES-1, R2-RES-2): **30 rows**.
- **Decisions:**
  - NEEDS LEAD: 3 rows (ADV-2 to PL17, ADV-7 to PL18, RES-1 to PL16).
  - PROPOSE FIX: 27 rows. ADV-12 keeps -b2, with the cut offered to the lead.
  - CONTEST: 0; DECLINE: 0; ESCALATE: 0.
- **PENDING LEAD:** 12-15 ANSWERED; 16-18 new, so 18 in all. PL1 is still open.
- **Expected revision 3 totals (the author recounts):**
  - **Test rows:**
    - -a 22 + 10 = 32 (P16d, P16e, P16f, P16g, P16h, P19, P8b, P20, P21, P22);
    - -b1 24 + 8 = 32 (R11, R12, R13, R14, L17, L18, L19, L20);
    - -b2 2; -c 10; -d 7;
    - about **83 rows**.
  - **Mutants:**
    - -a 15 + 9 = 24 (M-a16 to M-a24);
    - -b1 31 + 1 (M-c10 moved) + 9 = 41 (M-b36 to M-b39, M-b42 to M-b44, plus the disables of L19 and L20 as M-b40 and M-b41);
    - -b2 4;
    - -c 11 - 1 + 2 = 12 (M-c12, M-c13);
    - -d 6;
    - about **87 mutants**.
  - **Owner-visible limits:** 9 + O10 + O11 (if PL16 (a)) = up to 11. O3 and O5 are reworded.
