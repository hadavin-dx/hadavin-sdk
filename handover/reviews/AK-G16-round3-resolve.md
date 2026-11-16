# AK-G16 round 3 resolve (ticket revision 3; LAST review round)

**Honest note (read first).** This is the resolve step, `egm:egm-resolve` in AUTO mode, with the interactive gate skipped as the brief orders. This file replaces the skill's default `goldfish_review_report.md`. I did not write revision 3, so I have no author memory of it.

**What I ran.** No pytest, no import of the package, no Postgres, no network call, no install. I read `src/` and `tests/` on the working tree (`git log -1 -- tickets/AK-G16.md` = `a4b7a3c`, the revision under review) and grepped them. I did the arithmetic for the time budget (BN-2) and the counts (BN-31) by hand.

**What I did NOT check:**
- Every Kubernetes fact. That covers the meaning of an empty `namespaceSelector` or `podSelector`, `ttlSecondsAfterFinished` (and that it leaves the Secret), `startingDeadlineSeconds`, Secret-volume ownership, and whether NetworkPolicy applies to node-local metadata agents. A rule that refuses these inputs is safe whatever they mean.
- The NAT64 well-known prefix `64:ff9b::/96`. It is RFC 6052, from memory. I also did not check `192.0.0.192/32` (from the reviewer). Both are UNVERIFIED and go into evidence item 7.
- Gunicorn and Waitress flag names, and whether Waitress can express the five server limits.
- Whether PyYAML lets a loader subclass refuse aliases, merge keys and tags. The duplicate-key half is proven by `config.py:400-415`. The rest is not.
- P4b2's step as it will merge, beyond `tickets/P4b2.md:203` and `:232`.
- `tools/mutation_runner.py` arguments.
- The EGM brainstorm and draft for this ticket (PENDING LEAD 1). They are still not run, and I did not run them.

**What is design on paper.** Every build note below is text. No code proves any of them. Two notes are MEANWHILE texts. They describe my recommendation and are NOT instructions until the lead answers.

- **Status:** resolved (AUTO). The ticket is FROZEN at revision 3. Build notes BN-1 to BN-31 are appended to the end of `tickets/AK-G16.md`, and line 1 now says FROZEN. No other existing text was changed. I did not push and did not write DECISIONS.md.
- **Target:** `tickets/AK-G16.md` revision 3 DRAFT, commit `a4b7a3c`, full file (458 lines).
- **Findings:** `reviews/AK-G16-round3-adversarial.md` (R3-ADV-1..18: 0 Blocker, 6 Major, 8 Minor, 2 Nit). `reviews/AK-G16-round3-correctness.md` (R3-COR-1..18: 0 Blocker, 7 Major, 8 Minor, 3 Nit).
- **Gate:** round 3 of 3 (order 20 item 6; order 24 items 34, 40 and 44 apply the same "no round 4, build notes win" rule). There were 0 Blockers and 13 Majors, so the round is not clean. Under the design-doc stop rule (`.claude/rules/review-loop-speed-rules.md`), the remaining Majors become build-time fixes. They are the build notes. The RESULT review of built code has no cap (security path).
- **Build-blocking:** PENDING LEAD 19 and 20 (below). Until they are answered:
  - The -a builder builds everything except the re-put part of the re-anchor pass (BN-1).
  - The -b1 builder builds everything except the pilot-gate row (BN-6).

## Facts I checked myself (they decide rows)

1. **The re-put pass never runs in a v1 render (ADV-1).**
   - R15 and order 45 item 17 refuse every `backends.anchor` except `none` (ticket lines 138 and 281; `LEAD-ORDERS.md` order 45 item 17).
   - The pass runs only "when `anchor_recheck > 0` and an anchor is configured" (line 107).
   - `part=None` passes `anchor_recheck=0` (line 107).
   - So the pass runs only for a client who deploys `tick --part audit` with their own anchor, outside our render and lint.
   - The checks (i)-(iii) and `_checked_through` do NOT depend on an anchor. They need only the signer, so they work in the audit part and in `part=None`.
   - Today's in-memory retry `_retry_anchors` (`chain.py:302`, `:338-340`) is separate. It is unchanged.
2. **A slow store can starve signing (ADV-2/COR-5).**
   - The S3 anchor uses a 3 s connect timeout, a 5 s read timeout and 2 attempts (`anchor_s3.py:88`). So one call can take up to 16 s.
   - A re-put that meets an existing object is a conditional put plus a read (`:55-67`): up to 32 s.
   - The audit CronJob's `activeDeadlineSeconds` is 55 (line 139).
3. **The migrate Job has no config inputs (ADV-3/COR-1).**
   - `Part` excludes `migrate` (line 210), so `secret_objects: Mapping[Part, str]` has no key for it (line 216).
   - The migration secret is P6b2's `backends.store.migrate_credential_ref` (`tickets/P6b2.md:412`).
   - The migrate command reads the CA bundle through the secrets kind (`cli.py:329`).
4. **P4b2's step reads `app.maintenance_store` (COR-2).** See `tickets/P4b2.md:232` ("picks the store: `app.maintenance_store` if set; ... RAISES `ConfigError`" in pilot and prod). `PartApp` has six fields, and none of them is that one (line 211).
5. **Tool secrets come from the registry, not the config (COR-3).** See `app.py:111-121` (`reg.tools`). `load_registry(config)` is at `registry.py:207`.
6. **The lag step fails for ever in dev (COR-4).**
   - Pilot may run `signer: none`; `NOT_PROD` refuses it only in prod (`table.py:604`).
   - With no signer there is no checkpoint, so every row is "unsigned".
7. **The tick cites are off by 2 (COR-8).** Qualification is `cli.py:291-298`. `build(None, agents)` is `:299`. The error mapping is `:300-308`. `run_tick(app)` is `:309`.
8. **Two more cites (COR-17).** The label check is `chain.py:508-511`. `STEPS` is `tick.py:249-266`.
9. **A strict YAML loader already exists (COR-9).** `_UniqueKeyLoader(yaml.SafeLoader)` refuses duplicate keys (`config.py:400-415`).
10. **The host pattern flags Kubernetes names (COR-10).** The `host` pattern flags any dotted name ending in `io` (`test_no_hardcoded_values.py:34-38`), so `networking.k8s.io` and `kubernetes.io/...` are flagged.
11. **The secrets error names no part (COR-11).** `platform_secrets.check` raises `"secret 'x' cannot be read at start-up"` (`backends/platform_secrets.py:63`).
12. **`ed25519_local` accepts a key file path (COR-13).** It accepts `private_key_path` or `private_key_secret_name`, exactly one of them (`table.py:213-225`).
13. **The hold setting defaults to true (COR-14).** `retention.hold_labelled` defaults to `True` (`config.py:185`).
14. **Rows without an `alg` are checked with the signer's (COR-15).** See `chain.py:371-373`.
15. **`App.clock` is the UTC wall clock (ADV-11 c).** It defaults to `models.now`, that is `datetime.now(UTC)` (`models.py:19-20`; `app.py:73`; `approvals/requests.py:65`). This closes ticket line 447 (UNVERIFIED).
16. **`signed_through()` has test callers (ADV-18).** `tests/warden_port/test_audit_chain.py:494` and `:671` call it. `Verification.signed_through` is a different field, used at `cli.py:357`.
17. **A base-runnable twin is possible (ADV-14/COR-7).**
    - Existing tests build `audit.ChainAudit(audit._Db.memory(), key, anchor, every)` (`tests/warden_port/test_audit_chain.py:77`).
    - The base constructor is `(db, signer, anchor, checkpoint_every)` (`chain.py:156-162`).
18. **Smoke has a known way into the database (COR-18).** `chain.build` reaches the store's private `_db` (`chain.py:525-527`), which gives the smoke an access path that is already in use.

## Decisions (36 finding ids; 5 duplicate pairs merged = 31 rows; one decision per row)

| id(s) | category | decision (build note) |
|---|---|---|
| R3-ADV-1 (Major, cuttable) | **NEEDS LEAD 19** | Valid (Fact 1). The lead decided PL12 (a) in order 43 before order 45 refused every anchor, so re-deciding is the lead's call. My recommendation is (b): move the re-put to the first cloud adapter ticket (V1). The checks, `_checked_through`, the scan cap and the lag step stay in -a. -> BN-1 (MEANWHILE). |
| R3-ADV-2 + R3-COR-5 (Major) | PROPOSE FIX | Valid (Fact 2). Sign, insert and anchor the head first, then run the pass under a monotonic time budget (`ANCHOR_RECHECK_BUDGET_S = 15`). New row P16i, mutants M-a31 and M-a32. The PL12 and O3 cost text is corrected. This applies wherever the pass is built (-a, or V1 if PL19 is (b)). -> BN-2. |
| R3-ADV-3 + R3-COR-1 (Major) | PROPOSE FIX | Valid (Fact 3). New `deploy.migrate: {secret_object, egress}` and `migrate_secret_names(cfg)`. The six Secret object names must be distinct (render refusal plus an L7 case). The L8 input is named. Mutant M-b48. -> BN-3. |
| R3-ADV-4 (Major) | PROPOSE FIX | Valid. Each selector map needs at least one label (config). The lint refuses an empty selector in any `from` or `to`, and an empty `spec.podSelector` in any allow policy. Mutants M-b49 and M-b50. -> BN-4. |
| R3-ADV-5 (Major) | PROPOSE FIX (cut) | Valid. Every lint problem starts with its rule id, and every hostile case asserts that id. **L1 is CUT** and so is **L6's Secret-object half**: L18 refuses those kinds outright, so neither can be the only rule that fails. -b1 lint rows go from 18 to 17, and M-b14 is removed. -> BN-5. |
| R3-ADV-6 (Major) | **NEEDS LEAD 20** | Valid. This is an owner hard rule (the audit writer is its own identity). My recommendation is (a): `deploy render` refuses `pilot` and `prod` until V7 flips `defaults.AUDIT_WRITER_SEPARATE`. New row R16, mutant M-b54. -> BN-6 (MEANWHILE). |
| R3-ADV-7 (Major, honesty) | PROPOSE FIX | Valid. "Detected, not prevented" becomes "visible to a person who runs `audit verify`; no automatic alarm". The runbook (R11) and contract line K6 gain a person who runs `audit verify` at the contract interval. A last-signed marker is NOT built, because the same login could forge it. -> BN-7. |
| R3-ADV-8 (Minor) | PROPOSE FIX | Valid. One summary line per run, with counts by kind, replaces the per-row lines. "3N" is stated to hold for accidental junk only. -> BN-8. |
| R3-ADV-9 + R3-COR-6 (Major) | PROPOSE FIX | Valid. The `server` half of R12 moves to H6 (-d). The -b1 app command is exactly `[deploy.entry]`. New `deploy.wsgi_app` (`module:attr`) is validated in -b1 and rendered in -d. The server fields are Gunicorn's. Waitress becomes written outline V17. Mutant M-d7. -> BN-9. |
| R3-ADV-10 (Minor) | PROPOSE FIX | Valid. R15 reads "refuse whenever `backends.anchor` is not `none`". -> BN-10. |
| R3-ADV-11 (Minor) | PROPOSE FIX | Valid. Only `part=None` and `tick` qualify agents. The CronJob argv is `[deploy.entry, "--part", <part>]`. `PartApp.clock` defaults to `models.now` (Fact 15). -> BN-11. |
| R3-ADV-12 (Minor) | PROPOSE FIX | Valid. One value, `startingDeadlineSeconds: 50`, goes on every CronJob: no five-field schedule runs more often than once a minute. No schedule parsing is needed. -> BN-12. |
| R3-ADV-13 (Minor) | PROPOSE FIX | Valid. A minimum egress prefix length (`/16` for IPv4, `/48` for IPv6, `defaults.py`). A strict parse, where a parse error is a problem and never a skip. The NAT64 form of the metadata range is added, plus one UNVERIFIED address. Mutants M-b51 and M-b52. -> BN-13. |
| R3-ADV-14 + R3-COR-7 (Major) | PROPOSE FIX | Valid (Fact 17). Base-runnable twin P16h-base, plus P16-base where the pass is built. The fail-before text for P16-P22 now says plainly that the feature is missing. -> BN-14. |
| R3-ADV-15 + R3-COR-12 (Minor) | PROPOSE FIX | Valid. The runbook moves to -b1. -c depends on "-b2, or -b1 if -b2 is cut". The cut arithmetic is unchanged (the runbook is not a row). -> BN-15. |
| R3-ADV-16 (Minor) | PROPOSE FIX | Valid. O10 is reworded. Runbook R7 checks that the migrate Secret is gone and writes that down. -> BN-16. |
| R3-ADV-17 (Nit) | PROPOSE FIX | Valid. No ADD, curl or wget of a URL. The package index, through the lock, is the only network use. -> BN-17. |
| R3-ADV-18 (Nit) | PROPOSE FIX (deletion contested) | Contested in part: deleting `signed_through()` would break `tests/warden_port/test_audit_chain.py:494` and `:671` (Fact 16), and tests are never deleted. It keeps a docstring line instead. -> BN-18. |
| R3-COR-2 (Major) | PROPOSE FIX | Valid (Fact 4). `PartApp` gains a seventh field, `maintenance_store`. "Exactly six" now reads "exactly seven". Mutant M-a28. -> BN-19. |
| R3-COR-3 (Major) | PROPOSE FIX | Valid (Fact 5). The function becomes `secret_names_for(cfg, reg, part)`, with `reg` from `load_registry(cfg)`. Mutant M-a29. -> BN-20. |
| R3-COR-4 (Major) | PROPOSE FIX | Valid (Fact 6). `audit_lag` is a no-op pass when the config's `backends.signer.kind` is `none` or the sink has no `unsigned_age_s`. An empty chain passes. New row P19b, mutant M-a25. -> BN-21. |
| R3-COR-8 (Minor) | PROPOSE FIX | Valid (Fact 7). Re-cited. -> BN-22. |
| R3-COR-9 (Minor) | PROPOSE FIX | Valid (Fact 9). The L17 loader subclasses `config._UniqueKeyLoader`. The UNVERIFIED line narrows. -> BN-23. |
| R3-COR-10 (Minor) | PROPOSE FIX | Valid (Fact 10). One module, `deploy/k8s_names.py`, holds every API-group and label-key string, with one `ALLOWED` entry. -> BN-24. |
| R3-COR-11 (Minor) | PROPOSE FIX | Valid (Fact 11). `app.build(part=)` and `build_part` wrap the error with `part <p>: `, and `platform_secrets.py` stays unchanged. Mutant M-a30. -> BN-25. |
| R3-COR-13 (Minor) | PROPOSE FIX | Valid (Fact 12). The `kubernetes` render refuses any signer setting ending in `_path`. Mutant M-b53. -> BN-26. |
| R3-COR-14 (Minor) | PROPOSE FIX | Valid (Fact 13). The hold refusal sits in `run_tick_command` (the bare CLI and `main` without a hook). K6 joins the pilot gate, with a runbook R9 line. Mutant M-a26. -> BN-27. |
| R3-COR-15 (Minor) | PROPOSE FIX | Valid (Fact 14). A NULL `alg` counts as `signer.alg` in check (i). Mutant M-a27. -> BN-28. |
| R3-COR-16 (Nit) | PROPOSE FIX | Valid. The CHANGELOG derivation is corrected by note. -> BN-29. |
| R3-COR-17 (Nit) | PROPOSE FIX | Valid (Fact 8). Re-cited together with COR-8. -> BN-22. |
| R3-COR-18 (Nit) | PROPOSE FIX | Valid (Fact 18). S11 and the database clock read go through the store's `_db`, the precedent at `chain.py:525-527`. The purge part also uses `purge_store._db`. -> BN-30. |

## Positions (the reasons behind the larger calls)

- **ADV-1 goes to the lead, not to a cut I make.** Order 8 says cut surface, and the reviewer is right that the pass is unexercised in v1. But PL12 (a) is the lead's written decision (order 43 item 102), so I may not reverse it. I recommend (b) because:
  - nothing v1 renders can run the pass (Fact 1);
  - it costs 4 rows and 3 mutants in -a, plus BN-2's 1 row and 2 mutants;
  - its cost text describes a configuration the kit refuses.

  The part that guards against junk rows (checks (i)-(iii), `_checked_through`, the scan cap, the summary line) does NOT need an anchor. It stays in -a under every option.
- **ADV-6 goes to the lead** because it is the owner's hard rule (the audit writer is its own identity) and because option (a) has a real cost. Today `deploy render` refuses `dev` (I6), so with (a) **no real config renders at all until V7 merges**. The tests then run with the gate constant patched, and one row (R16) proves the shipped value refuses. That cost is the point of a code gate, and the lead should choose it knowingly.
- **ADV-5's cut** removes rules that can never fire alone: L18 already refuses the Role, ClusterRole and Secret kinds (ticket line 282). The rule-id assertion alone would also close the finding, so I cut only where the redundancy is certain. L16 stays, because I do not know whether L18's field allow-list admits `projected`.
- **ADV-13's numbers** (`/16`, `/48`) are my judgement. They are not an owner value. They tighten an existing least-privilege rule, they sit in `defaults.py` with a guard test (the pattern order 43 item 102 approved for `ANCHOR_RECHECK`), and they are reversible. The risk is that a client's model API needs a wider public range. The render then refuses, with the minimum named, which is loud, never silent. Confidence: about 70 percent that `/16` suits a first client.
- **ADV-9** makes Waitress a written outline (V17) instead of a rendered alternative. Its limits are not Gunicorn's flags, and v1 renders one server. The no-single-dependency rule is still met: the WSGI adapter is server-neutral, and V17 has a trigger.

## Couplings (text other owners change; this resolve edits none of them)

- **P6b2:** BN-3 reads `backends.store.migrate_credential_ref` (`tickets/P6b2.md:412`) as named there.
- **P4b2:** BN-19 relies on `tickets/P4b2.md:232`. If P4b2's merged step reads any other `App` attribute, P17 fails, and the -a author adds that field and writes it in the evidence (as line 426 says).
- **K6:** BN-27 makes K6 a pilot-gate item next to V7. The lead's pilot-gate list gains it.
- **V1 (first cloud adapter ticket):** under PL19 (b), V1 receives the re-put pass, BN-2, P16, P16c, P16d, P22, P16-base, P16i and M-a13, M-a19, M-a23, M-a31, M-a32.
- **`owner-visible-limits.md`, `contract-terms-notes.md`:**
  - O10 and O11 are reworded (BN-16, BN-7). So is O3, under BN-1 and BN-2.
  - K6 gains `audit verify` (BN-7).
  - All of these move when the lead accepts.

## PENDING LEAD (continuing the ticket's numbering after 18; my recommendation first)

19. **Re-anchor pass vs. the neutral kit (R3-ADV-1; re-decide PL12 in the light of order 45 item 17).**
    - Options:
      - (a) Keep the pass in -a as written, with BN-2.
      - (b) **Recommended:** move the re-put pass to the first cloud adapter ticket (V1). This covers step 4 of D1, `anchor_recheck`, `ANCHOR_RECHECK`, the `AnchorConflict` handling and BN-2's budget. Checks (i)-(iii), `_checked_through`, `ANCHOR_RECHECK_SCAN` (with its own guard), the summary line and the lag step stay in -a.
      - (c) Keep the pass in -a but mark it unexercised in v1. O3 gains "the kit as rendered has no proof copy, so this retry never runs in v1".
    - Why (b): no v1 render can run the pass (R15). It saves 4 rows and 3 mutants in -a (plus BN-2's 1 row and 2 mutants). PL12's cost text is for a configuration the kit refuses. V1 is the only route to an anchor anyway (V1 text, line 378).
    - Confidence about 75 percent. The doubt: a client may run `tick --part audit` with their own S3-compatible anchor outside our render. Under (b) that client gets today's in-memory retry only (`chain.py:338-340`).
    - Reversible: the text moves to V1 and nothing is deleted.
    - **MEANWHILE:** BN-1. The -a builder builds the common part and holds the re-put part.
20. **Pilot gate in code or by a person (R3-ADV-6; owner hard rule: the audit writer is its own identity).**
    - Options:
      - (a) **Recommended:** `deploy render` (and `deploy check`) refuse `environment: pilot` and `prod` while `defaults.AUDIT_WRITER_SEPARATE` is `False`, naming V7. V7 flips it to `True` in its own PR. New row R16, mutant M-b54.
      - (b) The gate is human-only. The lead owns it and shows O12 at the pilot gate (today's text).
      - (c) Both.
    - Why (a): a sentence alone cannot stop a render, and V7 has no ticket yet.
    - Cost of (a): with I6 (dev refused), nothing renders for real use until V7. The tests patch the constant, so a single row proves the shipped value.
    - Confidence about 70 percent. The doubt: the lead may want a pre-V7 test render on a client's cloud.
    - Reversible.
    - **MEANWHILE:** BN-6. -b1 is not blocked. R16 and M-b54 are built only on (a) or (c).

## Counts

- **Input:** 36 finding ids (adversarial 18, correctness 18). 5 duplicate pairs merged (ADV-2/COR-5, ADV-3/COR-1, ADV-9/COR-6, ADV-14/COR-7, ADV-15/COR-12): **31 decision rows**.
- **Decisions:**
  - NEEDS LEAD: 2 (ADV-1 to PL19, ADV-6 to PL20).
  - PROPOSE FIX: 29. ADV-18's deletion is contested, and its docstring fix is accepted.
  - CONTEST as a whole: 0. DECLINE: 0. ESCALATE: 0.
- **Build notes:** BN-1 to BN-31.
  - 28 fix notes, covering 29 rows (BN-22 covers COR-8 and COR-17).
  - 2 MEANWHILE notes (BN-1, BN-6).
  - 1 counts note (BN-31).
- **PENDING LEAD:** 20 items. 12-18 answered; 3 and 11 settled. **Open: 1, 2, 4-10, 19, 20 (11 items).**
- **Rows and mutants after the notes.** BN-31 has the arithmetic. Counted with only the decided notes, and the pass and gate as revision 3 has them:
  - **rows 85** (-a 34, -b1 32, -b2 2, -c 10, -d 7);
  - **mutants 101** (-a 30, -b1 48, -b2 4, -c 12, -d 7).

  The answers to PL19 and PL20 then add to or take from these:

  | Answer | Rows | Mutants |
  |---|---|---|
  | PL19 (a) or (c) | +2 (P16-base, P16i) | +2 (M-a31, M-a32) |
  | PL19 (b) | -4 (P16, P16c, P16d, P22 move to V1) | -3 (M-a13, M-a19, M-a23 move to V1) |
  | PL20 (a) or (c) | +1 (R16) | +1 (M-b54) |

  With my recommendations (PL19 (b), PL20 (a)): **82 rows, 99 mutants.**
- **v1.1 rows:** 17 (V17 Waitress outline, BN-9). **Owner-visible limits:** 12 (O3, O10, O11 reworded). **Contract lines:** 6 (K6 reworded).
