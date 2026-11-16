# R460 core pull request hand-off, version 2 (for the lead)

Written 2026-11-16 by a builder agent (Sonnet 5.5). It replaces `CORE-PR-HANDOFF.md` (kept unchanged). Inputs: that file, the five audits, `verification-blockers.md`, `review-handoff-readiness.md` (called READY below) and `review-handoff-zoomout.md` (called ZOOM below). Every reviewer Blocker and Major is answered; the map is in `resolve-handoff.md`.
Read-only work: I opened `src/` and `tests/`, ran `grep`, and ran ONE pure-library one-liner (Pydantic Decimal). I changed no `src/` or `tests/` file, used no git, and ran no repository test.

## 0. Read this first: what failed, what is uncertain, what I did not check

1. **I could not run the G4 bypass strings.** Importing `hadavin_sdk.approvals.gate` needs the `markdown_it` package, which is not installed in this sandbox (`ModuleNotFoundError`). I did not install anything. Every G4 claim is still "traced by reading". The first read-only evidence batch (section 7) is where they get run.
2. **Nothing was run against the real test suite.** Where a test expectation below says "expected 1 call" it comes from reading the fixture prices and the loop; nobody has seen it pass or fail.
3. **NaN question settled (partly).** I ran a Pydantic `Decimal` field alone (system Python, not the repo's pinned Pydantic): `"NaN"` and `"Infinity"` are REJECTED, `"-1"` is ACCEPTED. So audit claim SG-M5 "NaN passes" is wrong for the default field; only negative values and `daily > monthly` are real. The repo's own pinned version was not used; the evidence batch repeats it there.
4. **Still UNVERIFIED after this pass** (reasons in section 9): that masked text is a fixed point of `redact` (needed for the optional input tripwire, PR-2b); the real Postgres behaviour of the new reserve call (no Postgres service here); every regex-pattern claim in `guard/redact.py` and `approvals/gate.py`; whether `anchor_gcs`/`anchor_azure` probes really check Object Lock; vendor adapter bodies beyond `llm/common.py` and `llm/retry.py`.
5. **Decisions I made as safe defaults are not the owner's decisions.** Section 3 lists each default and who must confirm. Nothing below needs spend.
6. **Correction of v1 wording item:** v1 pointed only at `gate.py:373`. That comment block (`gate.py:366-377`) says "Platform-neutral and FAIL CLOSED here" (line 373) and then limits itself to known program names, so it is half right. The stronger over-claims are `gate.py:4` (module docstring: "rewritten platform-neutral and fail closed") and `approvals/channel.py:20-21` (`clean` docstring: "no command a person could paste ... on any platform"). I grepped `src/`, `docs/` and `README.md` for "fail closed" and "any platform": only those places. PR-G1 edits all three.

## 1. Facts I verified for this version (file:line read, or command run)

| # | Claim in v1 or in a review | Result | Evidence |
|---|---|---|---|
| F1 | `llm.chat` / adapters mask documents (ZOOM 6) | **NO masking anywhere in `llm/`.** `grep -n redact src/hadavin_sdk/llm/*.py` finds nothing. `NetworkLLM.chat` -> `turns()` just decodes documents to text (`llm/common.py:86-100`, UTF-8, bad bytes replaced). The fake LLM keys its recording on `sha256(documents[0])` (`llm/fake.py:37-39`). So RD-1.1 is a true leak for any caller that passes raw bytes, and masking must happen before `chat`. | grep, read |
| F2 | `extract()` has no caller in `src/` | Confirmed. Callers: `tests/test_s4_llm_guard.py:49,55` and `tests/test_k5_round9.py:108` only (`demos/` none). The leak is a library gap, not an active production leak. Priority stays high because the function is public and the repo promises masking at every model call. | grep over src, tests, demos |
| F3 | Where the llm object is built | `app.py:162`: `llm = llm or make("llm", b.llm, secrets, routes=cfg.routes)`, then passed to detectors (`:165`), runtime (`:232`). One place to wrap, and tests that inject `llm=` are also wrapped if the wrap goes after that line. | read |
| F4 | Model-call sites (the five from the audit) | `extract.py:47`, `evals.py:73`, `guard/judge.py:72`, `runtime/agent_loop.py:425`, `k1b/loop.py:94` (inside `_chat_bounded`). `agent_loop.py:430` passes `documents=[safe_doc]` (masked). `guard/producers.py:55-65` `MODEL_CALLERS` lists them; its `"extract validation errors"` row (`producers.py:36`) only proves the error text is `safe_head`-cut, not that the document is masked: that row gives false assurance for the document and must be reworded. | read |
| F5 | Alert kind exists? | **No.** `grep -ri alert src` finds only the k1b incident-alert data fields. The only notification path is the approvals channel card (`_abstain` posts one; `run_budget` already goes through `_abstain`, `agent_loop.py:245-248`). Daily and monthly stops use `_to(...)` (state row, no card, `agent_loop.py:240-243`). | grep, read |
| F6 | Zero-price configs in the repo | None. `tests/fixtures/config/config.yaml` uses 3.00 / 15.00; `tests/test_k3_pilot_env.py:47-48` same; the only zero price is the helper `_zero_price` in `tests/test_k1b_replay.py:381-384`. `demos/ask-your-data/askdata/config.py:42-43` copies prices, no zero. The refusal exists only in `k1b/replay.py:85-90` (`_refuse_zero_price`). `guard/judge.py:3-4` says the judge may run on "a local open-weights model on `openai_compat`": that is a self-hosted route that legitimately costs zero, so a blanket refusal would break it (ZOOM 4 confirmed). | grep, read |
| F7 | Slow-test marker | **There is no `slow` marker.** `pyproject.toml:87-90` defines only `live` and `perf`. CI runs `pytest -m "not live and not perf"` (`ci.yml:88`) and a separate `pytest -m perf` step (`ci.yml:94`, blocks a merge; one perf test needs `HADAVIN_TEST_PG_DSN`). Use `@pytest.mark.perf` for the patch's id-walk test and make sure it does not need Postgres. | read |
| F8 | `retry.py` | `with_retry` (`llm/retry.py:92-107`): non-transient failure -> `ProviderError` at once (no retry, request was refused, normally not billed); transient failure on the last attempt -> `ProviderExhausted`; `NetworkLLM.max_attempts` holds the attempt count (`llm/common.py:200-205`). Retries are inside ONE `chat()` call, so the caller sees one call and cannot see how many attempts ran. | read |
| F9 | Callers of `charge` / `blocked` / `add_spend` | src: `limits.py:18,24`, `agent_loop.py:240,314,440,670` (`self.limits.blocked`/`charge`), `store` protocol/impls. Tests: `test_p1a_fixes.py:76`, `test_review_fixes.py:151,154`, `test_review_pr3_round2.py:290`, `test_s5_runtime.py:109,116,128`, `test_p7_store.py:184`, `test_s1_foundation.py:161-164`, `contracts/test_store.py:179-189` (store contract, runs for each store kind), `tests/demo_askdata/*` (a separate meter class, `Decimal` `charge` on the demo's own `Meter`, not `Limits`). Tests that pin overshoot: `test_k5_tools.py:717-731` (`len(llm.sent) == 2`) and `test_s5_runtime.py:107-111`. | grep |
| F10 | Pydantic Decimal | NaN, Infinity rejected; `-1` accepted (one-liner, system Python). | ran |
| F11 | Stage name `"dev"` | Real stage uses are few: `config.py:317` (`Literal["dev","pilot","prod"]`), `config.py:366` (`if self.environment != "dev"`), `tests/fixtures/config/config.yaml:2`, `tests/test_p4_secrets.py:106` (default argument), `tests/warden_port/test_audit_chain.py:568`. The "26 hits in 6 files" READY counted dataset-split names (`"split": "dev"` in `tests/demo_askdata/*`, `demos/ask-your-data/data/*`) that are not stages. `guard/redact.py:1162` is a word list of environment names, not a stage check. D6 is therefore a small PR, not a repo-wide migration. I did not check yaml fixtures that build the value another way (a built `environment=` string); the PR-0 builder greps for `environment` again. | grep |
| F12 | Audit test "`:520`" | `tests/warden_port/test_audit_chain.py:520-525`, `test_an_unsigned_chain_still_verifies_its_links`: asserts `verify().ok` with no signer. This test pins the over-claim and must change in PR-D1. The CLI test at `:216-229` asserts `"NOT intact"` for a tampered chain (stays). `tests/demo_askdata/test_ledger.py:122` asserts the word "intact" is NOT in a demo text (unaffected). | read |
| F13 | S3 Object Lock probe | `anchor_gcs.py:69` and `anchor_azure.py:83` have a `probed(...)` step; `anchor_s3.py` has no probe function (grep "probe": none). So SA-3.4 "S3 start-up probe missing" is confirmed by grep; whether the GCS/Azure probes actually check the lock was not read. | grep |
| F14 | Signer key read | `audit/signer.py:104-108`: `Path(...).is_file()` (follows symlinks) then `read_bytes()`, no mode or symlink check (confirmed). `actions/secrets_file.py:21-23` imports `actions.secrets_cache` and `config.confined`; `audit/signer.py` imports only `hadavin_sdk.errors`. `tests/test_k5_layers.py` and `tests/test_lockin_guard.py` are the layer tests; I did not read what they forbid for `audit` -> `actions`. | read |
| F15 | `deferred.check` | `deferred.py:62-63`: `max_run_usd` required in pilot and prod, called from `registry.py:230` (per audit). `Budget` (`registry.py:33-36`) has `daily`, `monthly` as `Money`, no ordering check. | read |

## 2. Rung table (rule 20, CODE-LAST v1)

| Component | Need | Rung tried | What only our code gives | Verdict |
|---|---|---|---|---|
| Masking before a model call | personal data never reaches a model | A vendor guardrail exists as a kind (`guard/bedrock_guardrail.py`), but does not hold our run map or placeholders; a free library redactor was not evaluated (UNVERIFIED, no source dated) | placeholders restored per run, fail-closed, canary tests | KEEP-CODE (guarantee: redaction) |
| Spend reserve and cap | exact money caps | provider-side budgets/quotas: UNVERIFIED, not researched today; they do not stop one run mid-way and differ per vendor | reserve/settle, atomic across runs, per-agent | KEEP-CODE (guarantee: money) |
| Wall-hit notice (SG-M4) | a person learns the cap was hit | existing approvals channel card (`_abstain`); no-code webhook to a chat or email tool is a client-owned option | nothing new | CUT-TO-CONFIG+GLUE: reuse the card now; no new alert kind (D10) |
| Command filter display (G4) | approver does not see a pasteable command | none found (a shell parser library would not know cloud CLIs; UNVERIFIED) | the list and shapes | KEEP-CODE (approval path) |
| Audit chain honesty text | verify output tells the truth | none | wording from the verification result | KEEP-CODE (audit integrity) |
| Anchor object checks | detect a planted anchor | the storage vendor's Object Lock does the immutability; our code only checks names | name == key(seq) | KEEP-CODE, small |
| Key-file safety read | refuse unsafe key file | reuse `actions/secrets_file.py` reader (rung 1, in core) | none new | CUT-TO-CONFIG+GLUE: call the existing reader |

## 3. Decisions (rewritten; each with a safe default, the lead's yes needed only where marked)

| ID | Question | Safe default used in this hand-off | Who confirms |
|---|---|---|---|
| D1 | Is the spend window end a hard gate? | **Yes: Blocker.** `spend_window_end` required whenever the llm kind is not `fake`; goes in PR-M1. (The model-choice rule says "the code must enforce the end date of the window".) | lead (owner rule already says so) |
| D2 | G4 wording or behaviour first? | **Wording first** (PR-G1: `gate.py:4`, `gate.py:366-377`, `channel.py:20-21`), then shapes in PR-G2 onward. Done BEFORE any G4 behaviour PR. | lead |
| D3 | Are `get-secret-value` / `get-session-token` read-only in approval text? | **No.** They count as a command to withhold from the person's view (a secret read is not harmless). Done in PR-G5 (nit N4). | lead |
| D4 | Pilot refuses signer/anchor kind `none`? | **Not changed here.** Ship honest "NOT tamper-evident" output (PR-D1). Changing what a client build may run needs the owner. Owner-only item, dated 2026-11-16, next step: owner chooses at the pilot-start checklist. | owner |
| D5 | Money type (CLAUDE.md says integers; code uses Decimal) | **Keep Decimal.** Reject negative and non-finite (Decimal NaN/Infinity are already rejected by the field; make that an explicit test). Owner-only item (exception 2b): decide whether to move to integer minor units repo-wide; next step: lead asks the owner with the cost (every store column, every test). Dated 2026-11-16. | owner |
| D6 | Stage names | **Refuse `dev` with a message naming the rename (`demo`).** First small PR (PR-0), decided once for all four findings (SG-M7 `deferred.py:62-63`, SA-1.2 `config.py:395-396`, SA-3.2 `table.py:604`, `config.py:317`). Stage rules in later PRs are written against DEMO/PILOT/PROD only. See F11 for the real size. | lead |
| D7 | (was "reviews must run before PR-B") | **Not a decision.** It is EGM step 2 for every PR. Removed. | none |
| D8 | (was "ledger rows") | **Not a decision.** The lead writes the ledger rows before builders start (ledger rule). I could not write them (outside my folder). Step "L0" in section 5. | lead |
| D9 | May a builder rewrite tests that pin the overshoot? | **Yes, exactly two named tests**, each rewritten with the new expected value in the same PR: `tests/test_k5_tools.py:717-731` (`len(llm.sent) == 2` becomes `== 1` on a route whose worst-case reserve is 0.30) and `tests/test_s5_runtime.py:107-111` (DENIED at the gate becomes NEEDS_PERSON `limits.daily_budget` with no model call; a second test keeps the gate case with a fake whose cost is above its reserve). The old versions are deleted ONLY with the new ones in place; the PR text states this. No other pin may change without a new yes. | lead |
| D10 | New alert kind? | **No new kind now.** Wall hit = one log line + audit row + a card through the existing approvals channel. Named trigger for a real alert kind: a client asks for paging/email on cap hit. | lead |
| D11 | Zero-price routes | **Refuse at registry load** (every agent route) unless the route sets `self_hosted_zero_cost: true` AND its llm kind is `openai_compat`. Such a route needs the agent's `max_steps` (exists) and the PR-M6 calls cap, since a USD cap cannot bound it. | lead |
| D12 | `billing_timezone` | **Default `"UTC"`** (today's behaviour, no data migration). A named IANA zone is validated with `zoneinfo`. Switching zone mid-month re-buckets from the switch day; stated in the config comment. | lead |
| D13 | Retry accounting for a failed provider call | `ProviderError` (non-transient, request refused): release the reserve (not billed). `ProviderExhausted` (all attempts failed on transient errors, possibly billed): keep `worst_case x max_attempts` booked (conservative; may pass the cap by up to `(max_attempts - 1)` worst cases; stated in plain words). Timeout in the k1b replay: keep worst case (already so). | lead |
| D14 | Input tripwire in the seam (PR-2b) | Build only if E0-4 shows `redact(masked_text) == masked_text` on the corpus. Otherwise drop it and say why. | lead after evidence |

## 4. Pull request series (order, content, round status)

Round rule: security paths (money M, redaction R, secrets S, audit integrity A, approval text G) have NO round cap, but after round 2 only a Blocker or Major starts a new round (review-loop rule); minors are fixed in the same push and written to the ledger. PR-0 is the only capped PR (2 rounds). Heavy jobs: one full suite at the final head of each PR, through the 3-slot heavy runner; timing (`perf`) tests alone.
Lanes: L-A (masking seam: PR-1, PR-2, PR-3, PR-R*), L-B (money: PR-M1 to PR-M6), L-C (G4: PR-G0 to PR-G5), L-D (audit: PR-D*, PR-E*). Lanes touch different files except where noted; shared files: `agent_loop.py` (L-A PR-2b, L-B PR-M2/M3), `store/*` (L-B only), `models.py` (PR-R3 AuditEvent, PR-3 Shape): do not run two PRs that touch the same file at the same time.

### Step L0 (lead, before any builder): ledger rows for every item below (D8); run the evidence batch E0 (section 7); decide D1-D14.

| Order | PR | Contents (exact items) | Path | Rounds | Depends on |
|---|---|---|---|---|---|
| 0 | **PR-0 stage policy** | D6: `config.py:317` Literal becomes `demo/pilot/prod`; `config.py:366`; fixture `tests/fixtures/config/config.yaml:2`; `tests/test_p4_secrets.py:106`; `tests/warden_port/test_audit_chain.py:568`; a config with `dev` raises `ConfigError` naming the rename; update CLAUDE.md-independent docs only if grep finds them | other | capped 2 | none |
| 1 | **PR-G0 patch** | Apply `patches-ready/v6-extra/FIX-id-vs-command-withheld.patch` unchanged, plus `@pytest.mark.perf` on its id-walk test (F7; the test must not need Postgres) | G | uncapped (minors no new round) | none |
| 1 | **PR-1 seam** | `GuardedLLM` (new `llm/guarded.py`): a decorator implementing the `LLM` protocol, built once at `app.py:162` after `llm or make(...)`; pass-through in this PR (no behaviour change) with two hook points (`before(request)` / `after(request, reply_or_error)`) that PR-2b and PR-M3 fill. Repo guard test: only `llm/guarded.py` and the kind modules may call `.chat(`; callers get the wrapped object (the `MODEL_CALLERS` set in `guard/producers.py:55-65` is the allowlist base). RD-1.2. | R | uncapped | none |
| 2 | **PR-2 masking of the document (RD-1.1)** | Exact signatures in section 5.1. Also: fix `guard/producers.py:36` row; re-record fake recordings keyed by the document digest (`llm/fake.py:37-39`) for any test that sends a document with personal data; build the card number in `tests/test_k5_tools.py:371,378` from parts (RD-test) and search for the same literal in fixtures (`grep -rn "4111"` before the PR). PR-2b (optional, D14): input tripwire in the seam. | R | uncapped | PR-1 |
| 3 | **PR-3 error text (RD-1.3)** | `safe_head` once in `main()` and `_tick()` (`cli.py:75,300-305`); `hide_input_in_errors=True` on `models.Shape` (`_Strict` in `config.py:52` already has it); strip the YAML snippet in `registry.py:223-224` and `config.py:120,453`; test: config with a fake password (built from parts) in a bad field, stderr has none of it | R, S | uncapped | none (own PR per ZOOM 5) |
| 4 | **PR-M1 validation + window end** | SG-M5 (negative, `daily <= monthly`, explicit NaN/Infinity test), SG-M7 sign checks, **SG-B1** `spend_window_end` (section 5.2), D11 zero-price refusal at registry load (move `_refuse_zero_price` logic from `k1b/replay.py:85-90` to `registry.py`; keep a replay test), `billing_timezone` is NOT here | M | uncapped | PR-0 (stage names) |
| 5 | **PR-M2 every billed call reaches the ledger** | SG-M6, SV-A/B/C/F, SV-D (evals through the limits object with a separate eval budget), SV-E (`on_reply` callback, 5.3), SV-G (`Store.book_cost`, 5.3), judge cost (SG-M8) booked through `book_cost` BEFORE reserve exists. Retry/exhaustion policy per D13 | M | uncapped | PR-M1 |
| 6 | **PR-M3 reserve/reconcile + atomic reserve** | SG-B2, SG-B3, SG-M4 wall-hit notice (log + audit + card for daily/monthly through `_abstain`), the two test rewrites of D9. Exact design in 5.4 | M | uncapped | PR-M2 (ledger completeness FIRST, ZOOM 2), PR-1 (the seam carries reserve) |
| 7 | **PR-M4 timezone** | SG-M7 `billing_timezone` (D12), day/month keys (`limits.py:18,24`) | M | uncapped | PR-M3 |
| 8 | **PR-M5 calls cap for zero-price routes** | `Budget.daily_calls` / `monthly_calls` (needs a migration and store counter) used only when an agent's route is `self_hosted_zero_cost` | M | uncapped | PR-M1; only if D11 route flag is accepted |
| 9 | **PR-G1 wording** | G4-B1a: `gate.py:4`, `gate.py:366-377` (the "FAIL CLOSED here" sentence), `approvals/channel.py:20-21` say "a closed list of programs and SQL/shell shapes"; test that the docstring does not contain "any platform" is NOT added (a wording test is brittle); the behaviour tests come in later PRs | G | uncapped | none; MUST merge before PR-G2..G5 (READY 4) |
| 10 | **PR-G2 line joins and name normalising** | G4-B2 (join `\` + newline, `^` + newline, backtick + newline, before tokenising; a punctuation-first token is not prose when the next word is a known program, `gate.py:614-615`), G4-M7 (case, `.exe/.ps1/.cmd`, version suffix `kubectl-1.28`, `$VAR`, `${IFS}`), N3 (NBSP) | G | uncapped | PR-G1 |
| 11 | **PR-G3 SQL** | G4-M2 (case-insensitive statement shape: verb + object + `from/set/into` in order; keep pins `drop table pressure`, `we should delete from the queue only after a fix`), G4-M3 (shape gaps list) | G | uncapped | PR-G2 |
| 12 | **PR-G4 other shapes** | G4-B1b (shapes for dd, mkfs, `chmod -R`, kill, shutdown, `eksctl delete`, `cdk destroy`, dropdb, `crontab -r`, `sed -i`, `rsync --delete`, `> file`/`>>`/tee; plain `rm x` withheld unless the word after `rm` is an English determiner (`the, a, an, this, that, it, your, my, our`): this separates `rm x` from the pin `rm the file`, `test_g4_parity.py:224`), G4-M4 (PowerShell by verb + aliases), G4-M8 (rm flag set, find -delete, shred, unlink, truncate), G4-M9 (download-and-run) | G | uncapped | PR-G3 |
| 13 | **PR-G5 prose-versus-command rules** | G4-M1 (quoted exemption only when no write verb follows; keep pin `test_g4_parity.py:96`), G4-M5 (inversion), G4-M6 (read verb with write flag), G4-M10 (capital-first), G4-M11 (checkout, clean, commit, merge, rebase, pull), N1, N2, N4 (D3). Needs a prose false-positive budget: section 6 | G | uncapped | PR-G4 |
| 14 | **PR-R1 number formats** | RD-2.1 phone separators, RD-2.2 IBAN spaced/lower-case, RD-2.3 card layouts (15-digit grouping, 17-19 digits, dot separated) | R | uncapped | PR-2 |
| 15 | **PR-R2 credentials** | RD-2.6 JSON name/value pair on the LIVE path first (share one function with the k1b path), RD-2.5 credentials in signed URLs / reset links / unlisted webhook URLs / vendor prefixes, bare `passphrase, cvv, pin, dob` keys | R, S | uncapped | PR-2 |
| 16 | **PR-R3 email and encoded** | RD-2.4 email forms, RD-2.7 base64 second pass, `guard/__init__` exports of bare `redact`/`redact_many` (Nit) | R | uncapped | PR-R1 |
| 17 | **PR-R4 audit field allowlist** | RD-1.5 (`models.py:188-215`, `k1b/audit_sink.py:31-49`), RD-1.6 OS user name, RD-1.4 (`cli.py:81,287`, `receiver.py:63`), RD-1.7 retention note, RD-2.8/2.9 nits, 13 s hostile text nit (timing test, runs alone), vendor endpoints and redaction limits to config (no-hardcoding Nit, `llm/anthropic.py:23,54`, `llm/gemini.py:20`, `backends/table.py:370,540`) | R, A | uncapped | PR-3 (shares `models.py`) |
| 18 | **PR-D1 audit honesty (wording)** | SA-3.1, SA-3.2 text (5.5); test change at `tests/warden_port/test_audit_chain.py:520-525` | A | uncapped | none |
| 19 | **PR-D2 anchor names** | SA-3.3: one `anchors.collect(listing)` used by the three backends; two-process same-seq test (audit missing test 9) | A | uncapped | PR-D1 |
| 20 | **PR-D3 re-anchor** | SA-3.5 (`chain.py:174-176`: at start-up list checkpoints without an anchor, re-anchor; freshness alarm = a field `anchor_age_s` in `Verification` plus the log line, no new alert kind), test event time order (audit missing test 8; `AuditEvent.ts` is writer-chosen) | A | uncapped | PR-D2 |
| 21 | **PR-D4 retention floor and probe** | SA-3.4 config part: `retain_days` floor (`backends/table.py:155`) of 7 in pilot and prod (value from config, default documented; the owner can change it) and an S3 start-up Object Lock probe like `probed()` of GCS/Azure (`anchor_s3.py` has none) | A | uncapped | PR-0 |
| 22 | **PR-D5 outbox** | SA-3.6: `Verification.outside_chain` count; alert = log line by outbox age; remove DELETE on `audit_outbox` from the runtime role only if a purge identity exists (otherwise state it as a named owner item); negative test per role | A, least privilege | uncapped | PR-D1 |
| 23 | **PR-D6 identity split** | SA-4 + SA-3.4 identity part: separate anchor-writer setting and read-only verify role; policy text, per-action reason and negative test (5.6) | A, least privilege | uncapped | PR-D4 |
| 24 | **PR-E1 error chains** | SA-1.1 (`platform_secrets.py:63`, `signer.py:87`, `secrets_aws.py:34`, `cli.py:81-82`) | S | uncapped | none |
| 25 | **PR-E2 key file read** | SA-1.2 (5.7) | S | uncapped | PR-0 |
| 26 | **PR-E3 secret nits** | SA-nits: `__repr__` that hides values, add `audit/signer.py` and `signer_vault.py` to `SECRET_HOLDERS` (`tests/test_repo_rules.py:131-142`, F14), `local_dir.verify_object` returns False on a missing object (`audit/local_dir.py:158-164`; audit test 11), `secrets_file` folder mode/owner (audit test 12), chain id in the signed message, torn index lines, `index.jsonl` mode, `secrets_cache` eviction and lock | S, A | uncapped | none |

Parallel plan (real clock, builder time): wave 1 (start together): PR-0, PR-G0, PR-1, PR-3, PR-D1, PR-E1, PR-G1. Wave 2: PR-2, PR-M1, PR-D2, PR-G2, PR-E2, PR-E3. Wave 3: PR-M2, PR-R1, PR-R2, PR-G3, PR-D3, PR-D4. Wave 4: PR-M3, PR-R3, PR-G4, PR-D5. Wave 5: PR-M4, PR-M5, PR-R4, PR-G5, PR-D6. Each PR is expected to take one builder session of up to 60 minutes plus the review rounds; I did not measure any of these and the numbers are my estimate; re-baseline in the first report.

## 5. Concrete designs

### 5.1 RD-1.1 `extract` (PR-2)

```
def extract(
    llm: LLM,
    document: bytes,
    schema: type[BaseModel],
    *,
    run_id: str,
    route: str,
    mapping: dict[str, str],          # required, no default: a default {} would hide a missing mask
    system: str = "",
    on_reply: Callable[[Reply], None] | None = None,   # 5.3, added in PR-M2 (SV-E)
) -> Valid | DeadLetter
```
- **Map source:** the caller's run map: in the runtime it is `rmap` (the same dict `agent_loop.handle` saves through `_save_map`, defined `agent_loop.py:252`, called at `:363,379`). `extract` continues it in place (the contract of `runmap.redact_text`); the caller saves it (`store.put_redaction_map(run.run_id, runmap.storable(mapping, kinds))`). No `src/` caller exists (F2), so only the three test call sites change.
- **bytes or str:** the document stays `bytes` in the signature. Inside: `text = document.decode("utf-8", "replace")` (exactly what `llm/common.turns` does, `common.py:91-93`, so the text masked is the text sent), `masked = runmap.redact_untrusted(text, mapping)`, `documents=[masked.encode("utf-8")]`. A document that is not text (PDF or image bytes) is not a supported path (the docstring in `turns()` says so) and is treated as text.
- **Replayed assistant text** (`extract.py:61`): `runmap.redact_text(reply.text, mapping)`, NOT `redact_untrusted`: the model wrote it, so a placeholder it wrote is meant to be one (`runmap.py:299-302`). The validation error text keeps `safe_head(str(exc), 300, mapping)` (pass the map so numbering continues).
- **Fail closed:** any `runmap.RedactionError` (or any exception from masking) returns `DeadLetter(run_id=run_id, reason="redaction_failed", errors=["RedactionError"])` and NO model call is made. Never the exception text.
- **Tests (each must fail on the old code):** (1) recorder LLM storing `documents`: document with an email, a card number and a fake key built from parts: none appears in the recorded `documents`, the placeholders do; the existing driver `tests/test_k5_round9.py:91-109` records only messages, so add a `documents` field to it; (2) the assistant text replay: model reply containing an email: second call's messages contain the placeholder; (3) force `RedactionError` (monkeypatch `runmap.redact_untrusted`): result is the DeadLetter and `llm.calls == []`; (4) repo guard: every `MODEL_CALLERS` module that passes `documents=` also references `redact_untrusted` (extend `guard/producers.py` row).
- **Recordings:** `FakeLLM` finds recordings by `sha256(documents[0])` (F1), so any recording made from an unmasked document with personal data must be re-recorded from the masked bytes; list them with `grep -rln` on `tests/` recorded dirs in the PR.

### 5.2 SG-B1 window end (PR-M1)

- Field: top-level `Config.spend_window_end: AwareDatetime | None = None` (one value for the deployment, UTC; a naive value is refused at load). Required (non-None) whenever `backends.llm.kind != "fake"`, in every stage; a `ConfigError` names the field.
- `Limits.blocked()` returns `"window_ended"` when `now() >= window_end`, listed first after `kill_switch`. `_limits_stop` maps it to NEEDS_PERSON `limits.window_ended` through `_abstain` (a card goes out).
- Tests: patch `hadavin_sdk.limits.now` after the end: `blocked()` contains `window_ended`, the run ends NEEDS_PERSON with no model call; config with a real kind and no end date is refused; a naive datetime is refused. The "clock unreadable" row of v1 is dropped: `now()` is `datetime.now(UTC)` (`models.py:19-20`) and cannot be unreadable, so there is nothing to test.

### 5.3 Ledger completeness (PR-M2)

- New store call, both stores (`store/memory.py`, `store/postgres.py`, protocol `store/protocol.py:107`):
  `Store.book_cost(agent_id: str, run_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]`: adds to the day and month counters AND the run's `cost_usd` in ONE lock/transaction; returns the new (day, month). `NotFound` for an unknown run books nothing. Postgres: inside `self._db.transaction()` as `add_spend` already does (`postgres.py:416-431`) plus the `UPDATE runs` of `add_cost` (`postgres.py:276-277`). The two old calls stay (tests use `add_spend`).
- `Limits.book(agent_id, run_id, usd)` wraps it with the billing-day key (still UTC until PR-M4). Replaces the pairs at `agent_loop.py:314-315` and `:440-441`.
- Provider failure policy in the live loop (`agent_loop.py:424-439`): `ProviderError` -> nothing booked; `ProviderExhausted` -> `worst_case x llm.max_attempts` (D13). Parse failure after a billed reply (`extract`): `on_reply(reply)` is called as each reply arrives, so the caller books each real cost even when the final result is a DeadLetter (SV-E).
- k1b replay: when `route_prices is None`, refuse at start (today nothing is charged, audit M6); abandoned thread: unchanged worst case.
- Evals (SV-D): `evals.py:73-80,104-110` take a `Limits` and a pseudo agent id `"eval:<agent>"`; config `eval_budget_usd` (default `"0"`, meaning "no live eval calls"; the fake kind stays free).
- **Retry accounting (SV-A), honest limit:** retries run inside one `chat()` call (F8), so the caller cannot see failed attempts. PR-M2 therefore adds an `on_attempt` callback to `with_retry` (`llm/retry.py:92-107`) and `NetworkLLM._retry` (`llm/common.py`) so each failed transient attempt books one `worst_case` (D13). The builder must read the four adapter bodies first (UNVERIFIED here). Until that hook exists, a success after retries bills only the final reply; the PR must not claim more.
- Tests (each fails on old code): provider fails twice then succeeds -> ledger holds two failed-attempt worst cases plus the real reply; fake exhausted -> ledger greater than 0; fault injected between run-cost and spend -> no mismatch; two invalid replies of 0.1 -> `on_reply` called twice, sum 0.2; eval run with budget 0 stops before the first call.

### 5.4 Reserve and reconcile (PR-M3)

- **Reserve policy:** `worst_case_usd(route, system, messages, documents, tools)` moved from `k1b/loop.py:115-122` to `llm/common.py` beside `estimate_tokens` (`common.py:59`, pessimistic 3 chars per token); input estimate covers system + messages + decoded documents + tool specs JSON; output = `route.max_tokens x output price`; k1b imports the shared function. `_limits_stop` currently has no route: `agent_loop.handle` already knows `agent.model_route` (`:425`), so the reserve is computed in the loop right before `chat`, not inside `_limits_stop`.
- **Store call (names, signature, refusal):**
  `Store.reserve_spend(agent_id: str, run_id: str, day: date, usd: Decimal, *, daily_cap: Decimal, monthly_cap: Decimal, run_cap: Decimal | None) -> str | None`
  Returns `None` when it booked `usd` to the day, month and run counters, or the refusal code `"daily_budget" | "monthly_budget" | "run_budget"` (checked in that order) with NOTHING booked. A reservation is refused when `current + usd > cap` (not `>=`: exactly reaching the cap is allowed; the existing checks stay `>=` for already-spent).
  `Store.settle_spend(agent_id, run_id, day, reserved: Decimal, actual: Decimal) -> None` books `actual - reserved` (may be negative) to the same three counters atomically; never lets a counter go below zero (raises `ValueError`).
  Postgres: one transaction; insert-if-absent rows with `ON CONFLICT DO NOTHING`, then `SELECT ... FOR UPDATE` on `spend`, `spend_month`, `runs`, compare, `UPDATE`. Memory: under `self._lock`. Both stores run the shared contract tests in `tests/contracts/test_store.py` (F9) so each new test is written ONCE there.
- `Limits.reserve(agent_id, run_id, usd, run_cap) -> Reservation` (raises `BudgetRefused(code)`), `Limits.settle(res, actual)`, `Limits.release(res)` = settle 0. All model calls (loop, judge, evals, extract callers, k1b) go through the seam `GuardedLLM` hooks (`before` reserves, `after` settles), so there is one place (PR-1 is the prerequisite).
- **Reserve above the cap on a first call:** the call is refused with `run_budget` (or the daily/monthly code), the run goes NEEDS_PERSON with a card. In addition a load-time check (`deferred.check`) refuses an agent whose empty-call worst case (`max_tokens x output price`) exceeds `max_run_usd` or its daily budget, so this cannot happen silently in a live stage.
- **Release rules:** success -> settle actual (may exceed reserve with a fake or a mispriced provider: allowed, then the next reserve refuses); `ProviderError` -> release; `ProviderExhausted` -> settle `worst_case x max_attempts` (D13); process crash between reserve and settle -> the reserve stays booked (over-count, fail-safe); nothing sweeps it. State this in the PR; not fixed because no safe rule exists to tell an unfinished call from a finished one without per-call ids (owner-free, but a design choice for the lead: add a `reserve_id` table later if the over-count is seen).
- **Expected test numbers:**
  - Rewritten `test_k5_run_budget_stops_run` (`tests/test_k5_tools.py:717-731`): route override through `k5_cfg(config=...)`: `max_tokens: 1000`, `output_usd_per_mtok: "300"` (worst-case output 0.30) and a small input price; `CostLLM` 0.30; cap 0.50. Call 1: reserve about 0.3003 passes, settle 0.30. Call 2: `0.30 + 0.3003 = 0.6003 > 0.50` refused before sending. Expected `len(llm.sent) == 1`, `(run.state, run.reason_code) == (S.NEEDS_PERSON, "run_budget")`, card text contains `run_budget`. Old code makes 2 calls and books 0.60, so the test fails on old code. The old pin (2 calls) is replaced, not kept (D9).
  - Rewritten `tests/test_s5_runtime.py:107-111`: fixture route is the default 3.00/15.00/1024 (UNVERIFIED that `cfg_dir` uses it; builder checks), worst case about 0.0154 > the 0.001 left: expected `(NEEDS_PERSON, "limits.daily_budget")` and `rt.llm.calls == []`. A second test keeps the gate behaviour: a fake whose reply cost exceeds its reserve (as the old test intended) still ends DENIED at the gate.
  - Two-thread race (contract test, both stores): daily cap 1.00, each thread `reserve_spend(usd=0.60)`: exactly one returns `None`, the other `"daily_budget"`; final day total 0.60. Old code (`charge` after `blocked`): both pass. Run with a barrier so both enter together; 200 repeats for the memory store, 20 for Postgres.
  - Wall hit: daily/monthly stop calls `_abstain` (card + audit row) and one `logging` record from `Limits`; test with the fake channel and `caplog`.
- **No new alert kind (D10).**

### 5.5 Audit verify honesty (PR-D1)

- `Verification` (`audit/chain.py:134-150`) gets `signed: bool = False` and `anchored: bool = False` (set in `verify_rows` from `public is not None` and `anchors is not None`, `chain.py:366-382`) and a property `limits: list[str]` of plain-word reasons: "no signer: anyone who can write the database can rewrite the log and recompute it", "no anchor: removing the newest rows and their checkpoints cannot be detected", "N newest rows are not signed yet". Property `tamper_evident = ok and signed and anchored and unsigned_tail == 0`.
- CLI (`cli.py:349-363`): last line is `intact` only when `tamper_evident`; if `ok` but not tamper-evident, print `consistent, but NOT tamper-evident: <reasons>`; if not `ok` keep `NOT intact`. Exit codes UNCHANGED (0 consistent, 1 problems, 3 unreadable) so scripts do not break; the exit-0 case with limits is stated in the docstring.
- Tests: the old `test_an_unsigned_chain_still_verifies_its_links` (F12) keeps its assertions but gains `not v.tamper_evident`; CLI test: no signer -> output contains `NOT tamper-evident`, not `intact`; signer without anchor -> `NOT tamper-evident` and the rollback sentence; delete the last rows and their checkpoints with no anchor -> output says it cannot detect rollback (audit missing test 1 and 10).

### 5.6 Identity split policy text (PR-D6, least-privilege rule)

Policy to ship (names are config, no account ids): writer role: INSERT on `audit_entries`, `audit_checkpoints`, `audit_outbox`; SELECT only on what the next-row computation needs; no UPDATE/DELETE/TRUNCATE. Reader/verify role: SELECT on audit tables only. Anchor-writer identity: put-object on the anchor prefix only (no delete, no list outside the prefix). Per-action reason written beside each grant. Negative tests: reader cannot INSERT, writer cannot UPDATE or DELETE audit rows, anchor writer cannot delete, runtime cannot sign. Needs the Postgres service: UNVERIFIED here.

### 5.7 SA-1.2 key file read (PR-E2)

Call one shared checked reader. Layering: `actions/secrets_file.py` (the checks: `O_NOFOLLOW`, `fstat`, mode test, lines 35-58) must not be imported by `audit/` if a layer test forbids it (F14: not read); decision: move the checked-read function into a neutral module `hadavin_sdk/fileguard.py` (new, no vendor import), imported by both `actions/secrets_file.py` and `audit/signer.py`; the move keeps the existing tests of `secrets_file` unchanged. Refuse mode 0644 (group or other readable) and symlinks in EVERY stage (not only prod, `config.py:395-396` stays). Test keys in the repo that are written with default umask must be written with mode 0600 by the fixture helpers in `tests/test_p3b_neutral_audit.py`, `tests/warden_port/test_audit_chain.py`, `tests/contracts/kinds/audit_chain.py`, `tests/test_k3_pilot*.py` (they use `private_key_path`; I did not check each one's mode). Tests: key mode 0644 -> ConfigError; symlink -> ConfigError; 0600 regular file -> loads.

## 6. G4 prose false-positive budget (PR-G5 and every G PR)

- Existing: the false-positive corpus and prose pins in `tests/test_g4_parity.py` (pins: `rm the file` :224, `drop table pressure` and `we should delete from the queue only after a fix` :221-222, `a 'kubectl rollout restart' replaced the pods` :96, `the docker image was rebuilt overnight`, `update its set of rules`). Every PR must keep them all.
- New: a prose corpus file of at least 200 ordinary approval sentences (made up; includes each English-word program: git, docker, find, make, kill, sed in sentences). Budget: 0 new withheld lines on the pins and the existing corpus; on the new corpus every withheld line is listed in the PR text and accepted by the reviewer, maximum 2 percent of lines. Performance: the linear-time test already in `test_g4_parity.py` stays; the new shapes must not add backtracking (test with the 13-second class of input).
- Every new shape: one write string (withheld) and one prose near-miss (shown).
- G items by PR: G0 patch; G1 B1a; G2 B2, M7, N3; G3 M2, M3; G4 B1b, M4, M8, M9; G5 M1, M5, M6, M10, M11, N1, N2, N4.

## 7. First read-only evidence batch E0 (the lead runs it BEFORE any builder, with an EVIDENCE RUNNER agent; it never judges)

| # | Run | Expected if the audit is right |
|---|---|---|
| E0-1 | G4 strings through `withhold_commands` and `channel.clean`: `"kubectl \\\n delete ns prod"` (also `aws`, `docker`, `terraform`), `dd if=/dev/zero of=/dev/sda`, `drop table users;`, `rm x`, `rm the file`, `KUBECTL.EXE delete ns x`, `mysql Shop -e "delete from x"`, `Run: git checkout main`, `Please run the 'terraform destroy' now`, plus the pins | the bypass strings come back unchanged (shown to a person); the pins stay prose |
| E0-2 | Redaction canaries through `redact` and `redact_many` (and the runtime path `redact_text`): spaced IBAN, lower-case IBAN, `(555) 010-0000` style phone, 15-digit and dotted card, non-ASCII email, signed-URL credential, `{"name": "DB_PASSWORD", "value": "<fake built from parts>"}`, base64 email | each unmasked on the old code |
| E0-3 | `"NaN"`, `"Infinity"`, `"-1"` through the repo's `Money` type and `Budget` | NaN/Infinity refused, `-1` accepted (my one-liner showed this on a bare Decimal field) |
| E0-4 | `redact_bounded(masked, {})` on 100 already-masked strings: is the output equal to the input? | if not equal anywhere, D14 tripwire is dropped |
| E0-5 | A fake `LLM` that records `documents` fed to `extract`, `evals`, `judge`: which of them see raw personal data | `extract` yes (confirmed by reading); others UNVERIFIED |
| E0-6 | The `perf` patch id-walk test: wall time and whether it needs Postgres | adds seconds; no Postgres need |
| E0-7 | `pytest --collect-only -q` count, and `pytest -q tests/test_k5_tools.py::test_k5_run_budget_stops_run tests/test_s5_runtime.py` on the unchanged repo | pass (baseline) |
| E0-8 | `grep -rn "environment" tests src` once more for stage values built other ways (F11) | no new stage sites |

Cheaper than a review round: one runner, no review; raw output saved by the lead.

## 8. Every audit item has a home (dropped items now assigned)

| Item | PR or exception |
|---|---|
| SG-B1 | PR-M1 (Blocker, D1) |
| SG-B2, SG-B3 | PR-M3 |
| SG-M4 | PR-M3 (log + audit + card); real alert kind: D10 trigger |
| SG-M5 | PR-M1 |
| SG-M6, SV-A/B/C/F | PR-M2 |
| SG-M7 | PR-M1 (signs), PR-M4 (timezone) |
| SG-M8 | PR-M1 (zero price, D11), PR-M2 (judge booked), PR-M3 (judge reserved) |
| SV-D | PR-M2 |
| SV-E | PR-M2 (`on_reply`) |
| SV-G | PR-M2 (`book_cost`) |
| k1b/loop.py no charge when `route_prices` is None | PR-M2 |
| D5 Decimal vs integer | owner-only (2b), dated 2026-11-16 |
| RD-1.1 | PR-2 |
| RD-1.2 | PR-1 |
| RD-1.3 | PR-3 |
| RD-1.4, 1.6, 1.7, 2.8, 2.9, 13 s text | PR-R4 |
| RD-1.5 | PR-R4 |
| RD-2.1, 2.2, 2.3 | PR-R1 |
| RD-2.4, 2.7, `guard/__init__` exports | PR-R3 |
| RD-2.5, 2.6 | PR-R2 |
| RD-test (card literal) and other fake literals in fixtures | PR-2 (card) and PR-R4 (sweep of the remaining literal credentials; the only allowed literal is `AKIAIOSFODNN7EXAMPLE`) |
| Hardcoded vendor endpoints and redaction limits | PR-R4 |
| `demos/ask-your-data` pipeline "exempted" (unverified) | PR-2: add a test that its model input contains only the typed question after masking; if the demo has its own repo copy, the demo-repo owner; I did not open it |
| G4 items | section 6 per PR |
| SA-3.1, 3.2 | PR-D1 (D4 owner-only for refusing `none`) |
| SA-3.3 | PR-D2 |
| SA-3.4 | PR-D4 (retention, probe), PR-D6 (identity) |
| SA-3.5 | PR-D3 |
| SA-3.6 | PR-D5 |
| SA-1.1 | PR-E1 |
| SA-1.2 | PR-E2 |
| SA-4 | PR-D6 |
| SA-nits | PR-E3 |
| Twelve missing negative tests | 1 PR-D1; 2 PR-D2; 3 PR-E2; 4 PR-E1; 5 PR-D3; 6 PR-D4; 7 PR-D5; 8 PR-D3; 9 PR-D2; 10 PR-D1; 11 PR-E3; 12 PR-E3 |
| D6 stage | PR-0 |
| Zero-price calls cap | PR-M5 |

## 9. What I did not check

- Not run: any repository test, ruff, bandit, mutation, any G4 or redaction string (F-list above; dependency `markdown_it` missing in the sandbox).
- Not opened: `guard/redact.py` pattern code, `approvals/gate.py` beyond lines 1-12 and 366-377, adapter bodies (`anthropic.py`, `gemini.py`, `openai_compat.py`, `bedrock.py`), `store/postgres.py` outside lines 270-285 and 410-435, `evals.py`, `guard/judge.py` beyond its header, `handover/ledger.md`, `tests/test_k5_layers.py` content, the `demos/ask-your-data` pipeline, Postgres behaviour of the planned `FOR UPDATE` transaction.
- The PR sizes and wave timings in section 4 are my estimates, not measurements.
- EGM: "EGM skipped: read-only synthesis document, no plan or code produced; the lead runs the EGM chain on each PR and on this hand-off (egm-review-loop with `design_critic` and `implementation_readiness`)."
- Rules cited: bible R-numbers were not looked up (the bible folder is on the studio laptop, not in this repository); I used the rule text in `CLAUDE.md`, `.claude/rules/` and `BRIEF-PREAMBLE.md` (R215, R214, R211 as quoted there). Token use: about 150,000 tokens estimated (not measured).
