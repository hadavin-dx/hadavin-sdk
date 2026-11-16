# Citation check of CORE-PR-HANDOFF-v4.md (2026-11-16, UTC)

Target sha256 3f9b1d848cc7d692f250b8878c286e356554e92b01b58d9ed7caa11b0f542612: MATCHES. Checked against the working tree at commit f3612a03f. Nothing was run; reads only. Paths are under src/hadavin_sdk/ unless stated.

## Failures first (9 findings; 0 files missing in src, 1 test path wrong, 1 wrong content)

| id | citation | verdict | right value | evidence |
|---|---|---|---|---|
| X1 | D18: "S3 kind docstring states the identity needs PutObject + GetObject + list on one prefix only" (audit/anchor_s3.py) | WRONG CONTENT | no such text exists | module docstring (lines 1-12) says only "written by a principal the runtime cannot delete with (S11)"; grep PutObject/GetObject/ListBucket in audit/*.py: no hits. The "default today" in D18 is false until the docstring is written. |
| X2 | 4.2 `tests/test_redaction.py:309,356` (4.10 CREDITCARD row) | FILE MISSING at that path | tests/warden_port/test_redaction.py:309,356 | lines 309 and 356 hold there (`"4111 1111 1111 1111"`, `"4111111111111111"`) |
| X3 | F9 `cli.py:179-184` ("other branches build secrets, probe them, then the store"); also 4.3 | WRONG LINE | cli.py:183-189 (secrets 184, `platform_secrets.check` 186, store 189) | 179-182 is the "refused: ... needs a shared store" message |
| X4 | F8 `app.py:164` (judge member gets the raw llm) | WRONG LINE | app.py:165 | 164 is `if detector is None:`; 165 is `make("detector", d, secrets, llm=llm)` |
| X5 | 4.8 `secrets_file.py:46-63` (S_ISREG, other-readable, group/other-writable, read) | WRONG LINE | actions/secrets_file.py:49-64 | 46-47 is the open-error branch; checks start at 49 (`fdopen`), end at 64 |
| X6 | F13 `limits.*` ends are `_to(...)` "at :244, :669, :702" | WRONG LINE (2 of 3) | :244 holds; the `_to` calls are :672 and :703 | 669 is the comment "limits unreadable: stop means stop, so no card"; 702 is the `if decision.rule_id.startswith("limits.")` line, `_to` on 703. Content (no card) is true. |
| X7 | 4.4 `run_budget` branch "(:245-247) already posts through `_abstain`" | WRONG LINE (range short) | :245-249 | `_abstain` call is on line 249 |
| X8 | 4.11 `backends/table.py:594` (`DEV_ONLY`) | WRONG LINE (off by one) | table.py:593 | 593 is `DEV_ONLY: frozenset...`; 594 is `{` |
| X9 | 4.11 `anchor_gcs.py:69-88`, `anchor_azure.py:80-95` | RANGE LOOSE (content holds) | gcs `probed` 69-85; azure `probed` 83-96 | 80 in azure is `return probed(...)`; gcs function ends at 85 |

Notes (not citation errors, but an agent following the text would be misled):
- 4.11 H-1: "a floor on the existing `retain_days` of 7": the existing default is 1 (`backends/table.py:155`, `Field(default=1, ge=1)`). The floor of 7 is new; the wording can read as if 7 already exists.
- 4.10 `CREDPAIR` is not an existing label in redact.py (grep: none); `~513` points at the HAR cookie pattern it is modelled on. Fine as a proposal, but it is a new name.
- `hadavin_sdk/fileguard.py` and `llm/metered.py` do not exist yet (stated as new). `worst_case_usd` exists only in k1b/loop.py:115 (the target says so).

## Full table (holds = line range exists and says what the target says)

| id | citation | verdict | evidence |
|---|---|---|---|
| 1 | sec0.2b `gate.py:608-615` first-token test | holds | `_story`: `first = toks[0]...`; `re.fullmatch(r"[A-Z][a-z]+\|[^\w/.~$-]+", first)` returns True (so `>` as first token is "story") |
| 2 | sec0.2c `gate.py:404`, `:597` `_AWS_READ_PREFIXES` | holds | 404 tuple incl. `"get-"`; 597 `words[1].startswith(_AWS_READ_PREFIXES)` |
| 3 | sec0.2d / F2 `gate.py:647-678` no IGNORECASE | holds | `re.compile(` ... closes 678 with no flag; `(?i:` only at 671-673; SQL words upper-case |
| 4 | sec0.5 `tests/test_s4_llm_guard.py:39` 0.00225 | holds | `assert reply.cost_usd == Decimal("0.00225")` |
| 5 | sec0.5 `tests/test_s5_runtime.py:76` | holds | `cost_usd == Decimal("0.00225")` |
| 6 | sec0.5 3 chars/token in `llm/common.py` | holds | common.py:59-62 `estimate_tokens` `len(text)//3` |
| 7 | sec0.5 fixture route 3.00/15.00, max_tokens 1024 | holds | tests/fixtures/config/config.yaml:6-8 |
| 8 | F1 `approvals/gate.py:681-698` | holds | `withhold_commands` def 681 to return 698 |
| 9 | F3 `agent_loop.py:440-441` | holds | `self.limits.charge(agent_id, reply.cost_usd)` / `self.store.add_cost(run.run_id, ...)` |
| 10 | F3 / 4.2 `agent_loop.py:313-315` (and `:314-315`, "if at :313") | holds | 313 `if verdict.cost_usd:`; 314 charge; 315 add_cost |
| 11 | F4 `store/memory.py:196-216` | holds | add_spend 196-204 under `self._lock`; spend_totals 206-216 |
| 12 | F4 `store/postgres.py:416-442` | holds | add_spend 416-431 (two upserts, RETURNING, one transaction); spend_totals 433-442 |
| 13 | F4 `migrations/0001_core.sql:87-92` | holds | `CREATE TABLE spend ... usd NUMERIC NOT NULL`, no FK, no check |
| 14 | F4 `0003_approvals_tick.sql:15-20` | holds | `spend_month`, `usd NUMERIC NOT NULL`; only CHECK is on month day |
| 15 | F4 `store/protocol.py:107-111` | holds | add_spend 107; spend_totals "a read with no write" 108-110 |
| 16 | F5 `limits.py:20-30` | holds | `registry.agents[agent_id]` line 25; `day >= budget.daily` 26, `month >=` 28 |
| 17 | F6 `llm/retry.py:83-108` | holds | `with_retry`; ProviderError re-raised 95-96; ProviderExhausted 101 |
| 18 | F6 `llm/protocol.py:9-15` | holds | classes at 10-15 (9 blank); Exhausted subclasses ProviderError |
| 19 | F7 `extract.py:47` | holds | `reply = llm.chat(` |
| 20 | F7 `evals.py:73` | holds | `reply = llm.chat(` |
| 21 | F7 `guard/judge.py:72` | holds | `reply = self.llm.chat(` |
| 22 | F7 `evals.py:109` (judge.qualify) | holds | `judge.qualify(judge.JudgeDetector(llm, ...))` |
| 23 | F7 `runtime/agent_loop.py:425` | holds | `reply = self.llm.chat(` |
| 24 | F7 `k1b/loop.py:94`; daemon thread | holds | 94 `llm.chat(*args...)`; 104 `daemon=True`. Five `.chat(` sites in src, none other (grep) |
| 25 | F8 `tests/k5_support.py:160-204` | holds | `build_runtime` 160; `Runtime(` 200 (call runs past 204), no app.py |
| 26 | F8 `app.py:162`, `:171` | holds | 162 `llm = llm or make("llm"...)`; 171 `limits = Limits(store, audit, reg)` |
| 27 | F8 `app.py:164` | WRONG LINE | see X4 |
| 28 | F9 `cli.py:146-153` | holds | gate branch builds only `make("llm", ...)` |
| 29 | F9 `cli.py:179-184` | WRONG LINE | see X3 |
| 30 | F9 `evals.py:101-110` | holds | judge qualification on the same `llm` |
| 31 | F10 `tests/test_s4_llm_guard.py:49`, `test_k5_round9.py`, `tests/demo_askdata/` | holds | 49 `extract(llm, ...)`; round9:108 calls extract; demo_askdata exists; no non-test caller in src (grep) |
| 32 | F10 `llm/fake.py:39-40` | holds | `doc = documents[0]...`; `sha256(doc)` |
| 33 | F11 `audit/chain.py:134-149` | holds | fields rows/signed_through/problems/unreadable; `ok`, `unsigned_tail` properties |
| 34 | F11 `chain.py:362-385` verify_rows | holds | `verify_rows(rows, checkpoints, public_key, anchors, alg, row_algs)` 363-383 |
| 35 | F11 `anchor_s3.py:70` | holds | `all() -> dict[int, tuple[str, str]]`; no timestamp |
| 36 | F12 `secrets_file.py:34-64` | holds | confined, os.open O_NOFOLLOW/O_NONBLOCK, fstat, S_ISREG, IROTH/IWGRP/IWOTH refusal (group read allowed) |
| 37 | F12 `audit/signer.py:104-108` | holds | `is_file()` 106, `read_bytes()` 108, no mode check |
| 38 | F13 `agent_loop.py:83`, `:79-82` | holds | GUARD_STOP_REASONS incl. `run_budget`; comment 79-82 |
| 39 | F13 `_abstain` caught_by `:575` | holds | `caught = "guard" if reason in GUARD_STOP_REASONS else None` |
| 40 | F13 `:244`; `:669`, `:702` | :244 holds; others WRONG LINE | see X6 |
| 41 | F14 `config.py:317` | holds | `environment: Literal["dev", "pilot", "prod"]` |
| 42 | F14 `config.py:453` | holds | `except (ValueError, ...) as exc: raise ConfigError(str(exc))` |
| 43 | F15 `config.py:41-47` | holds | `_money` rejects float; `Money` 47 |
| 44 | F15 `registry.py:33-36` | holds | `Budget(daily, monthly)`, no validators |
| 45 | 4.1 `memory.py:196-204`, `postgres.py:416-431` | holds | as 11, 12 |
| 46 | 4.1 `k1b/loop.py:115-122` worst_case_usd | holds | 115 def; 118-122 estimate + max_tokens x output price / 1e6 |
| 47 | 4.2 `k1b/loop.py:94` | holds | as 24 |
| 48 | 4.2 `agent_loop.py:425` | holds | as 23 |
| 49 | 4.2 `evals.py:105` judge routes | holds | `if d.kind == "llm_judge"` in `cfg.backends.detector` loop |
| 50 | 4.2 removal `agent_loop.py:440-441`, `:314-315`, `:313` | holds | as 9, 10 |
| 51 | 4.2 `tests/test_s5_runtime.py:107-111` | holds | `charge(..."0.999")`, "call costs 0.00225 and crosses 1.00", expects DENIED `limits.daily_budget` today |
| 52 | 4.2 `tests/test_k5_tools.py:717-731` | holds | CostLLM bills 0.30; run_budget test |
| 53 | 4.2 `k5_cfg(config=...)` shallow update | holds | k5_support.py:112-117 `d.update({"tool_modules": ..., **(config or {})})` |
| 54 | 4.3 `cli.py:146-153`, `:179-184` | 146-153 holds; 179-184 WRONG LINE | X3 |
| 55 | 4.3 `evals.py:109` | holds | as 22 |
| 56 | 4.4 `_limits_stop` `agent_loop.py:239-247`, kill switch `:241-242` | holds | 239 def; 241-242 `_to(run, S.STOPPED, "kill_switch")` |
| 57 | 4.4 run_budget `:245-247` | RANGE SHORT | X7 |
| 58 | 4.4 `agent_loop.py:669`, `:702` quotes | holds (quotes) | 669 comment "limits unreadable: stop means stop, so no card is posted"; 702 comment "stop means stop: no card, at any level" |
| 59 | 4.4 `_REASON_TEXT` `:87` | holds | `_REASON_TEXT = {"ungrounded": ...}` |
| 60 | 4.4 `GUARD_STOP_REASONS` `:83` | holds | as 38 |
| 61 | 4.4 `tests/test_s5_runtime.py:107-111` | holds | as 51 |
| 62 | 4.5 `k1b/replay.py:85-90` | holds | `_refuse_zero_price`, `llm_kind != "fake"` |
| 63 | 4.5 `guard/judge.py:3-4` | holds | "runs on any configured llm route and kind" |
| 64 | 4.5 `registry._cross_check` | holds | registry.py:338 |
| 65 | 4.6 `chain.py:203` | holds | `if self.signer is not None and seq % self.checkpoint_every == 0: self.checkpoint()` |
| 66 | 4.7 `guard/producers.py` row 36 | holds | producers.py:36 `("extract validation errors", "extract.py", "extract", frozenset({"safe_head"}))` |
| 67 | 4.7 `runmap.redact_text`, `restore_value`, `RedactionError` | holds | runmap.py:417, 560, 38 |
| 68 | 4.8 `secrets_file.py:46-63` | WRONG LINE | X5 |
| 69 | 4.8 `signer.py:104-108` | holds | as 37 |
| 70 | 4.8 `tests/test_lockin_guard.py:68-75` | holds | `LIBRARY_IMPORTS` psycopg, cryptography, markdown_it; vendor and library imports only |
| 71 | 4.9 `tests/test_g4_parity.py:98,221-222` | holds | 98 `update its set of rules`; 221 `delete from the queue only after a fix`; 222 `drop table pressure` |
| 72 | 4.9 `gate.py:664-666` UPDATE alias | holds | `\bUPDATE\s+` + `_ID` + `\s+SET\b` |
| 73 | 4.9 G1 `gate.py:4`, `:366-377`, `channel.py:20-21` | holds | 4 names G3/G4 in module docstring; 367-376 G4 comment block; channel.clean docstring 19-21 |
| 74 | 4.9 G2a `gate.py:546` `_TOKEN` | holds | `[^\S\n]+([^\s]+)` stops at newline |
| 75 | 4.9 G2b `gate.py:608-615` | holds | as 1 |
| 76 | 4.9 G4a `gate.py:674` `rm` shape | holds | `\brm\s+(?:-[a-zA-Z]*[rRf][a-zA-Z]*\|--recursive\|--force)(?=\s+\S)`; `rm` not in `_NAMES` (gate.py:540) |
| 77 | 4.9 G5a `gate.py:597` | holds | as 2 |
| 78 | 4.9 `gate.py:573-589` `_subcommands` lower-cases words | holds | `low = tok.lower()...` |
| 79 | 4.10 PHONE `~470`, IBAN `~247`, CREDITCARD `~451`, EMAIL `~236` (guard/redact.py) | holds | PHONE 472, IBAN 247, CREDITCARD 451 (4-4-4-4 only), EMAIL 236 |
| 80 | 4.10 CREDPAIR `~513` HAR cookie pair | holds (approx.) | HAR `"name": "Cookie"` pattern at ~513-516; label CREDPAIR is new (see notes) |
| 81 | 4.10 `k1b/redaction.py` `_pair` | holds | k1b/redaction.py:103 `def _pair` |
| 82 | 4.10 `tests/warden_port/privacy_corpus.py:42` | holds | `"card 4111 1111 1111 1111"` |
| 83 | 4.10 `tests/test_redaction.py:309,356` | FILE MISSING at path | X2 |
| 84 | 4.11 `config.py:317`, `:366-367`, `:19` | holds | 317 environment Literal; 366-367 `if self.environment != "dev": ... DEV_ONLY`; 19 imports DEV_ONLY |
| 85 | 4.11 `backends/table.py:594` | WRONG LINE | X8 |
| 86 | 4.11 `tests/test_lockin_guard.py:18,430` | holds | 18 imports DEV_ONLY; 430 `coverage_problems(TABLE, DEV_ONLY, ...)` |
| 87 | 4.11 `tests/fixtures/config/config.yaml:2` | holds | `environment: dev` |
| 88 | 4.11 `tests/test_p4_secrets.py:106` | holds | `def _config(tmp_path, secrets, environment="dev")` |
| 89 | 4.11 `tests/warden_port/test_audit_chain.py:568` | holds | `_anchor_refusals("dev", ...)` |
| 90 | 4.11 `tests/test_p1b_backends.py:~89-91` | holds | 89-91 parametrize pilot/prod, `d.update(environment=env)` |
| 91 | 4.11 wording `secrets_env.py:1` | holds | "(`dev` only, by the environment table)" (actions/secrets_env.py) |
| 92 | 4.11 `audit/signer.py:64,98` | holds | 64 "(dev and pilot...)"; 98 "(dev and pilot only...)" |
| 93 | 4.11 `table.py:126,214,254,591` | holds | 126 "opt-down for dev"; 214 "(dev, pilot)"; 254 "a dev server"; 591 "allowed only in `dev`" |
| 94 | 4.11 `config.py:346` | holds | `# dev executor only` |
| 95 | 4.11 `defaults.py:100` | holds | "the dev executor's per-call timeout" |
| 96 | 4.11 `registry.py:50` | holds | "None only in dev" |
| 97 | 4.11 `tools.py:361` | holds | "Without a pin (dev only...)" (src/hadavin_sdk/tools.py) |
| 98 | 4.11 `agent_loop.py:179,553,572` | holds | "dev only"; "slice-1 gate path (dev)"; "(dev slice-1)" |
| 99 | 4.11 `actions/contract.py:34` | holds | "kept in dev for the slice-1 tests" |
| 100 | 4.11 `store/postgres.py:75,90` | holds | "opt-down for dev"; "opt down with sslmode for dev" |
| 101 | 4.11 `guard/redact.py:1162` "a word list" | holds | `"dev",` inside a word list |
| 102 | 4.11 H-1 `anchor_s3.py:84-96` | holds | `build()` 84-97 |
| 103 | 4.11 H-1 `anchor_gcs.py:69`, `:69-88` | :69 holds; range loose | X9 |
| 104 | 4.11 H-1 `anchor_azure.py:80-95` | range loose | X9 |
| 105 | D11 `k1b/replay.py:85-90` | holds | as 62 |
| 106 | D18 S3 docstring needs PutObject+GetObject+list | WRONG CONTENT | X1 |
| 107 | 9 `test_s5_runtime.py:107-111` | holds | as 51 |

Counts: 107 rows; holds 94 (incl. approximate), wrong line or loose range 10, wrong content 1, file missing at cited path 1 (one row counts in two groups where noted).

## What I did NOT check
- Any claim not tied to a file:line (arithmetic such as the 0.0155 reserve, the 2% budget, behaviours predicted for new code, hand-traced G3/G4 results in the 4.9 tables).
- Postgres behaviour; nothing was run (no tests, no import of `approvals.gate`; `markdown_it` is indeed missing here: `ModuleNotFoundError`).
- Citations of files outside src, tests, migrations (`.claude/rules/...`, `resolve-handoff-v4.md`, v3 section 5, `ledger.md`).
- Whether `test_k5_layers.py` is "about secrets layers", and the claim "no test forbids audit importing a neutral module" (negative claim, not searched).
- The claims in section 8 and 7 that grep every demo config for a zero price.
- Line numbers inside `tests/test_k5_round9.py` and `tests/demo_askdata/` beyond existence and one extract() call.
