# Citation check of CORE-PR-HANDOFF-v6.md (EVIDENCE RUNNER: records only, no judging)

Run: 2026-11-16 (UTC). Read-only on src/ and tests/. No git, no network, no spend, nothing executed except `sed`/`grep` and small inline Python that reads files. Doc checked: handover/core-hardening/audit-r460/CORE-PR-HANDOFF-v6.md (436 lines).

## A. FAILURES FIRST (wrong or partly right)

| # | Doc line | Claim in doc | True value (file read) | Verdict |
|---|---|---|---|---|
| 1 | 161 (4.1) | `agent_loop`'s `except ProviderError` at `:431` | `runtime/agent_loop.py:431` is `documents=[safe_doc],` (end of the `chat(` call). The `except (ProviderError) as exc:` is at lines 432-434 | wrong (off by 1 to 3) |
| 2 | 293 (4.7) | today `extract.py:55` passes no mapping to `safe_head` | `extract.py:55` is `try:`. The call `safe_head(str(exc), 300)` is at `extract.py:58`. The "no mapping" part is right | wrong line (58) |
| 3 | 45 (F21) | `_FILE` regex `\d{4}_[a-z0-9_]+\.sql` at `store/migrate.py:70` | `:70` is `_ROLE`; `_FILE` is `:71`. `check_ledger` exists (`:97`) | wrong line (71) |
| 4 | 299, 301 (4.7) | tests search `FakeLLM.everything_sent` | `FakeLLM` (`llm/fake.py:21-54`) has no `everything_sent`; it keeps `.calls`. `everything_sent()` is a method of the test class `ScriptLLM` (`tests/k5_support.py:124`, method at `:156`) | wrong object |
| 5 | 34 (F10), 301 (4.7) | recorded fake replies are keyed on `sha256(documents[0])` (`llm/fake.py:39-40`) | Only when `documents` is non-empty. With no documents the key is `sha256(json.dumps(messages, sort_keys=True))` (`fake.py:39`) | partly |
| 6 | 212, 278 (4.2, 4.5), 416 (E0-8) | the five files that "build a NetworkLLM kind directly": `tests/test_k1b_replay.py`, `tests/warden_port/test_bedrock_provider_r16.py`, `tests/warden_port/test_providers.py`, `tests/test_p5p6_followups.py`, `tests/test_p5_llm.py` | `tests/test_k1b_replay.py:391` only passes the string `llm_kind="anthropic"` with a `ScriptedLLM`; it builds no network kind. The other four build through `make("llm", ...)`. NOT in the list: `tests/contracts/kinds/llm_wire.py` constructs `AnthropicLLM` (`:66`), `OpenAICompatLLM` (`:91`), `GeminiLLM` (`:119`), `BedrockLLM` (`:192`) by hand; `tests/test_p5_llm.py:248` also constructs `GeminiLLM` by hand. `tests/contracts/kinds/builtin.py:53` calls `make("llm", ...)` but with the fake kind (no gate needed). I could not reproduce the doc's own grep, so the list is checked against my own grep | partly (one entry does not fit, one real builder missing) |
| 7 | 35 (F11) | `verify_rows(...)` at `audit/chain.py:362-385` | function is `:363-383` (`:362` blank, `:384-385` blank/next def at `:386`) | partly (range slightly wide) |
| 8 | 30 (F6) | Bedrock status in `response["ResponseMetadata"]["HTTPStatusCode"]` (`bedrock.py:93-110`) | `detail()` is `:93-101`; `retryable()` is `:104-110` and also reads that field (`:108`). Both read it, so the content is right; the range covers two functions | partly (range) |
| 9 | 32 (F8), 214 | `tests/k5_support.py:160-204` builds a `Runtime` | `build_runtime` is `:160-211`; the `Runtime(` call is `:200-209`. `:204` is the `llm,` argument line | partly (range) |
| 10 | 83 (D18) | the S3 module docstring does not state the identity rights (`anchor_s3.py:1-12`) | The docstring (`:1-12`) does not name actions (grep `PutObject|GetObject|ListBucket` in `audit/*.py`: no hit, as stated). It does state one constraint: "The bucket must be written by a principal the runtime cannot delete with (S11)" (`:5-7`). So "states no rights" is right for actions, not for the constraint | partly |
| 11 | 7, 94, 70 (D5, section 0) vs ORDERS.md | Q28 says D5 is OWNER-OPEN, "non-blocking" (`ORDERS.md` lines 185-198) | `handover/core-hardening/ORDERS.md:192` says exactly that. The doc states it knowingly disagrees (needed before M2a). Not a citation error; recorded because the doc contradicts the cited answer on purpose | match (disagreement is stated in the doc) |

Rows 1-4 are wrong. Rows 5-10 are partly right. Everything else I checked matched (section C).

## B. COUNT CLAIMS (counted in the doc itself, by inline Python)

| Claim | Counted | Verdict |
|---|---|---|
| 25 decisions D1-D25 | rows `| D1 |` to `| D25 |` in section 3: ids 1..25, 25 distinct, none missing, none duplicated | match |
| 22 facts F1-F22 | rows `| F1 |` to `| F22 |` in section 1: 22 distinct | match |
| 11 evidence items | `E0-1` to `E0-11` all present in section 7 as list items: 11 | match |
| 11 gating PRs | table "Gating track": PR-2, M1, M2a, M2b, M2c, M3, R, S1, A1, G-W, G = 11 (text at line 401 also says "11 gating PRs") | match |
| 3 housekeeping | H-0, H-1, H-2 (section 4.11 and line 403) = 3 | match |

Other number claims checked against code:

| Claim | True value | Verdict |
|---|---|---|
| `Limits(` built with three positional arguments at 9 places: app.py:171, cli.py:209, tests test_s5_runtime.py:28, k5_support.py:206, test_k3_pilot.py:104, test_k5_postgres.py:58, test_k5_round5.py:241, test_k5_tools.py:1133 and :1269 | grep `Limits(` finds exactly these 9 `Limits(store, audit, reg)` sites (other `Limits(` hits are a different class in `tests/demo_askdata/`) | match |
| `.chat(` call sites in src: 5 (extract.py:47, evals.py:73, guard/judge.py:72, runtime/agent_loop.py:425, k1b/loop.py:94) | grep finds these 5 plus a docstring mention in `guard/producers.py:5` (which the doc excludes by design) | match |
| `.chat(` outside src: demos/ask-your-data/askdata/pipeline.py:155 | match (only one hit in demos) | match |
| 4 network kinds call `self._retry(` (anthropic:122, bedrock:156, gemini:86, openai_compat:119) | all four lines hold `self._retry(` | match |
| migrations 0001-0005 exist, no 0006 | `store/migrations/` holds 0001..0005 only | match |
| default `retain_days` is 1 (`table.py:155`, `Field(default=1, ge=1)`) | match | match |
| `max_attempts` default 3 (`table.py:40`), `call_timeout_s` 60 (`table.py:37-39`) | match | match |
| `checkpoint_every` default 100 (`chain.py:161`), checkpoint at `seq % checkpoint_every == 0` (`:203`) | match | match |
| fixture route 3.00 / 15.00 per million, max_tokens 1024 (`config.yaml:6-8`); 0.00225 per fake call (`test_s4_llm_guard.py:39`, `test_s5_runtime.py:76`) | match | match |
| `evidence-handoff-v4.md`: 125 passed, 36 probes, 0 mismatches | 125 passed (lines 14, 25); `raw-v4/probe.json` is a list of 36 entries; "0 mismatches" at line 7 | match |
| `ORDERS.md` lines 185-198, answer Q28 | file is `handover/core-hardening/ORDERS.md`; Q28 at line 192 | match |
| No `thinking`, `cache_control`, `cachedContent`, `reasoning` in `llm/*.py`; no `cache` file under `llm/` | grep: no hits | match |
| `guard/bedrock_guardrail.py` has no cost field | grep `cost|price|usd`: no hit | match |
| `extract()` has no non-test caller in src | grep `extract(` / imports of `hadavin_sdk.extract` in src: no caller | match |

## C. WHAT I CHECKED AND MATCHED (no listing of every row here; the raw rows are in section D)

Verified by reading the cited lines (not just the first line): F1 gate.py:681-698 (the string `[command withheld (G4)]` is `WITHHELD` at `gate.py:388`); F2 gate.py:647-678 (one `re.compile(` with no flags, `(?i:...)` only on some alternatives at 671-673); F3 agent_loop.py:440-441 and :314-315; F4 memory.py:196-204 (one lock), postgres.py:416-431 (one transaction, two upserts with RETURNING), 0001_core.sql:87-92 and 0003_approvals_tick.sql:15-20 (`usd NUMERIC NOT NULL`, no sign check), protocol.py:107-111; F5 limits.py:13-30 (`>=`, `registry.agents[agent_id]` raises KeyError for unknown id, bare `now()` at :18 and :24), models.py:19-20, app.py:73 and :176-184 (the `clock` argument is passed only to `Approvals`: the only other `clock` hit in app.py is the parameter itself); F6 retry.py:31-36, :55-63, :83-108, :95-96, :97-99, :100-103 and common.py:193-196, :233-241; F7 (all call sites, see B); F8 agent_loop.py:184-194, app.py:90-98, :162, :165, :171; F9 cli.py:146-153, :150, :173-182, :183-190, :221-222, evals.py:101-110; F12 secrets_file.py:34-64 (O_NOFOLLOW|O_NONBLOCK, fstat, S_ISREG, refuse S_IROTH|S_IWGRP|S_IWOTH, skip when `os.name == "nt"`), signer.py:104-108; F13 agent_loop.py:83, :79-82, :569-575, :244, :672, :703; F14 config.py:317, deferred.py:33 (`LIVE = ("pilot", "prod")`), table.py:593-602, config.py:366-370, :400-415, :453-460; F15 config.py:41-47 (float refused only), :57-58, registry.py:33-37 (no sign or order check), :53, models.py:294, :305, :98; F16 models.py:218-222, extract.py:18-25, runmap.py:218-227, :560-568, :275-304, defaults.py:108-122 (NAME, ADDRESS, PHONE, EMAIL stored; IBAN not), evals.py:63; F17 injection.py:85-101, judge.py:100-109; F18 factory.py:17-54, table.py:570-579, anthropic.py:80-88, common.py:200-206; F19 anthropic.py:107-120 and bedrock.py:132-154 (no cache or thinking field); F20 protocol.py:151-160, app.py:147-150, test_k5_round6_contracts.py:14-16, store_postgres.py:59-71 (`__getattr__` forwards); F21 migrate.py:46-67 (map), :150-166, :169-181, :71-86 (CREATE forms), `_APPEND = "SELECT, INSERT"` at :41, `runs` is `_RW` at :47; F22 k1b/loop.py:40-52, :179, :206, :115-122, :170, cli.py:115-117 (`--max-usd` required).
Section 4 and 6 citations matched: Limits.reset limits.py:48-51; agent_loop.py:239-250, :241-242, :245-249, :318-322, :325-541, :387, :425, :520, :560-567, :569-597, :87, :669-672, :702-703; cli.py:93-95, :209, :349-363; chain.py:134-149, :171, :203, :518-547; anchor_gcs.py:69-85; anchor_azure.py:83-96; anchor_s3.py:70; table.py:34-40, :155; gate.py:404, :540, :546, :573-589, :597, :608-615, :674, :695; channel.py:19-21; redact.py:236, :247, :451, :472, :513; privacy_corpus.py:42; test_redaction.py:309, :356; test_g4_parity.py:98, :221-222; test_lockin_guard.py:68-75, :18, :430; test_k5_tools.py:723-731 (cost 0.30, cap 0.50, 2 sent calls, `run_budget`); test_s5_runtime.py:107-111 (spent 0.999, DENIED `limits.daily_budget`); stage-word sites in section 4.11 (config.py:19, :317, :346, :366-367; table.py:126, :214, :254, :591, :593; defaults.py:100; registry.py:50; tools.py:361; contract.py:34; secrets_env.py:1; signer.py:64, :98; postgres.py:75, :90; agent_loop.py:179, :553, :572; config.yaml:2; test_p4_secrets.py:106; test_audit_chain.py:568; test_p1b_backends.py:89-91; redact.py:1162).

## D. NOT CHECKED

- Claims about behaviour (what a test or Postgres would do): not run, per the brief.
- Claim that the Runtime decodes documents with `decode("utf-8","replace")` (F16): the cited line `evals.py:63` shows it for evals; I did not search `agent_loop.py` for the same call.
- "7 citation rows of the v5 check (2 wrong, 5 partly)" (line 3): I did not open `evidence-handoff-v5/citation-check-v5.md` to count them.
- Review-finding ids (security B1, M-3, readiness M10, etc.): not checkable against code.
- `ci.yml`, `check_grants` behaviour on a 0006 file, and the docs/ folder: not read.
- Line numbers inside the *new* design (code the doc proposes) cannot be checked: the code does not exist.

## E. RAW AUTO-EXTRACTED ROWS (every `file:line` or bare `:line` token in the doc, with the first line of the cited range)

Format: `L<doc line> <as written>:<from>-<to> [resolved file; * = more than one file of that name exists, first taken] first line ... last line`.
Caution: bare `:NNN` tokens are attached by script to the last file named earlier in the doc, which is sometimes wrong (rows marked `(ctx)`). I checked each `(ctx)` row by hand against the file the sentence means; the script mis-attached these, and the true targets are all in agent_loop.py (for `guard/judge.py(ctx):310-316/387/520`, which are `_screen` call sites in `runtime/agent_loop.py`: 310-316 `_screen`, 387, 520 match), `llm/anthropic.py:107-120` and `llm/bedrock.py:132-154` (for the `table.py(ctx):107-120` row), `agent_loop.py:431` (for `llm/protocol.py(ctx):431`, see failure 1; `llm/protocol.py` is a new file in the design and has 29 lines today). `cli.py*` resolves to `src/hadavin_sdk/cli.py`, which is the right one (other cli.py files are demos and site-packages).

```
L16 llm/common.py:59-62 [src/hadavin_sdk/llm/common.py] def estimate_tokens(text: str) -> int: ... return max(1, len(text) // 3)
L16 tests/fixtures/config/config.yaml:6-8 [tests/fixtures/config/config.yaml] input_usd_per_mtok: "3.00" ... max_tokens: 1024
L16 tests/test_s4_llm_guard.py:39-39 [tests/test_s4_llm_guard.py] assert reply.cost_usd == Decimal("0.00225")
L16 tests/test_s5_runtime.py:76-76 [tests/test_s5_runtime.py] assert rt.store.get_run(run.run_id).cost_usd == Decimal("0.00225")
L25 approvals/gate.py:681-698 [src/hadavin_sdk/approvals/gate.py] def withhold_commands(text: str) -> str: ... return "".join(out) + text[last:]
L26 gate.py:647-678 [src/hadavin_sdk/approvals/gate.py] _WRITE_SHAPES = re.compile( ... )
L27 runtime/agent_loop.py:440-441 [src/hadavin_sdk/runtime/agent_loop.py] self.limits.charge(agent_id, reply.cost_usd) ... self.store.add_cost(run.run_id, reply.cost_usd)
L27 runtime/agent_loop.py(ctx):314-315 [src/hadavin_sdk/runtime/agent_loop.py] self.limits.charge(run.agent_id, verdict.cost_usd) ... self.store.add_cost(run.run_id, verdict.cost_usd)
L28 store/memory.py:196-204 [src/hadavin_sdk/store/memory.py] def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]: ... return self._spend[(agent_id, day)], Decimal(month)
L28 store/postgres.py:416-431 [src/hadavin_sdk/store/postgres.py] def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]: ... return Decimal(d), Decimal(m)
L28 store/migrations/0001_core.sql:87-92 [src/hadavin_sdk/store/migrations/0001_core.sql] CREATE TABLE spend ( ... );
L28 store/migrations/0003_approvals_tick.sql:15-20 [src/hadavin_sdk/store/migrations/0003_approvals_tick.sql] CREATE TABLE spend_month ( ... );
L28 store/protocol.py:107-111 [src/hadavin_sdk/store/protocol.py] def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]: .. ... 
L29 models.py:19-20 [src/hadavin_sdk/models.py] def now() -> datetime: ... return datetime.now(UTC)
L29 app.py:73-73 [src/hadavin_sdk/app.py] clock: Callable[[], datetime] = now,
L29 app.py(ctx):176-184 [src/hadavin_sdk/app.py] approvals = Approvals( ... )
L29 limits.py:13-30 [src/hadavin_sdk/limits.py] class Limits: ... return reasons
L30 llm/retry.py:83-108 [src/hadavin_sdk/llm/retry.py] def with_retry[T]( ... raise AssertionError("unreachable")  # max_attempts >= 1 (settings)
L30 llm/retry.py(ctx):95-96 [src/hadavin_sdk/llm/retry.py] except ProviderError: ... raise
L30 llm/retry.py(ctx):97-99 [src/hadavin_sdk/llm/retry.py] except Exception as exc:  # every failure is classified below, never swallowed ... raise ProviderError(f"{label}: {describe(exc, detail)}") from exc
L30 llm/retry.py(ctx):100-103 [src/hadavin_sdk/llm/retry.py] if attempt == max_attempts: ... ) from exc
L30 llm/anthropic.py:122-122 [src/hadavin_sdk/llm/anthropic.py] got = self._retry(lambda: self._parse(self._current().messages.create(**request)))
L30 llm/bedrock.py:156-156 [src/hadavin_sdk/llm/bedrock.py] got = self._retry(lambda: self._parse(self._client.converse(**request), in_text))
L30 retry.py:55-63 [src/hadavin_sdk/llm/retry.py] def transient(exc: BaseException, retryable: Retryable | None = None) -> bool: ... return isinstance(exc, OSError)  # URLError, socket timeouts, connecti
L30 retry.py(ctx):97-99 [src/hadavin_sdk/llm/retry.py] except Exception as exc:  # every failure is classified below, never swallowed ... raise ProviderError(f"{label}: {describe(exc, detail)}") from exc
L30 llm/common.py:193-196 [src/hadavin_sdk/llm/common.py] class NetworkLLM: ... would strand the run. A kind writes ``_chat``."""
L30 anthropic.py:122-122 [src/hadavin_sdk/llm/anthropic.py] got = self._retry(lambda: self._parse(self._current().messages.create(**request)))
L30 bedrock.py:156-156 [src/hadavin_sdk/llm/bedrock.py] got = self._retry(lambda: self._parse(self._client.converse(**request), in_text))
L30 gemini.py:86-86 [src/hadavin_sdk/llm/gemini.py] got = self._retry(
L30 openai_compat.py:119-119 [src/hadavin_sdk/llm/openai_compat.py] got = self._retry(
L30 llm/common.py:233-241 [src/hadavin_sdk/llm/common.py] def _retry(self, call: Callable[[], Answer]) -> Answer: ... )
L30 retry.py:31-36 [src/hadavin_sdk/llm/retry.py] def status(exc: BaseException) -> int | None: ... return None
L30 bedrock.py:93-110 [src/hadavin_sdk/llm/bedrock.py] def detail(exc: BaseException) -> str: ... return None
L31 extract.py:47-47 [src/hadavin_sdk/extract.py] reply = llm.chat(
L31 evals.py:73-73 [src/hadavin_sdk/evals.py] reply = llm.chat(
L31 guard/judge.py:72-72 [src/hadavin_sdk/guard/judge.py] reply = self.llm.chat(
L31 runtime/agent_loop.py:425-425 [src/hadavin_sdk/runtime/agent_loop.py] reply = self.llm.chat(
L31 k1b/loop.py:94-94 [src/hadavin_sdk/k1b/loop.py] box["reply"] = llm.chat(*args, **kwargs)  # type: ignore[arg-type]
L31 k1b/loop.py(ctx):104-104 [src/hadavin_sdk/k1b/loop.py] t = threading.Thread(target=work, daemon=True, name="k1b-llm-call")
L31 demos/ask-your-data/askdata/pipeline.py:155-155 [demos/ask-your-data/askdata/pipeline.py] reply = self.llm.chat(
L31 guard/bedrock_guardrail.py:101-101 [src/hadavin_sdk/guard/bedrock_guardrail.py] resp = self._client.apply_guardrail(
L32 runtime/agent_loop.py:184-194 [src/hadavin_sdk/runtime/agent_loop.py] def __init__( ... ) -> None:
L32 tests/k5_support.py:160-204 [tests/k5_support.py] def build_runtime( ... llm,
L32 app.py:162-162 [src/hadavin_sdk/app.py] llm = llm or make("llm", b.llm, secrets, routes=cfg.routes)
L32 app.py(ctx):165-165 [src/hadavin_sdk/app.py] members = [make("detector", d, secrets, llm=llm) for d in b.detector]
L32 app.py(ctx):171-171 [src/hadavin_sdk/app.py] limits = Limits(store, audit, reg)
L32 app.py:90-98 [src/hadavin_sdk/app.py] if sources and live: ... )
L33 cli.py:146-153 [src/hadavin_sdk/cli.py*] if args.cmd == "gate": ... )
L33 cli.py(ctx):150-150 [src/hadavin_sdk/cli.py*] make("llm", b.llm, make("secrets", b.secrets), routes=cfg.routes),
L33 cli.py:221-222 [src/hadavin_sdk/cli.py*] llm = make("llm", cfg.backends.llm, secrets, routes=cfg.routes) ... detector = combine([make("detector", d, secrets, llm=llm) for d in cfg
L33 cli.py:183-190 [src/hadavin_sdk/cli.py*] try: ... audit = make("audit", b.audit, secrets, store=store, signer=signer, an
L33 cli.py:173-182 [src/hadavin_sdk/cli.py*] if b.store.kind == "memory": ... return 2
L33 evals.py:101-110 [src/hadavin_sdk/evals.py] # An llm_judge is qualified by its own golden set on the same model client, at its own rat ... judges_green = judges_green and total > 0 and ok / total >= cfg.eval_t
L34 llm/fake.py:39-40 [src/hadavin_sdk/llm/fake.py] doc = documents[0] if documents else json.dumps(messages, sort_keys=True).encode("utf-8") ... digest = hashlib.sha256(doc).hexdigest()
L34 llm/fake.py:21-21 [src/hadavin_sdk/llm/fake.py] class FakeLLM:
L34 llm/fake.py(ctx):29-29 [src/hadavin_sdk/llm/fake.py] def chat(
L35 audit/chain.py:134-149 [src/hadavin_sdk/audit/chain.py] @dataclass ... return self.rows - self.signed_through
L35 chain.py:362-385 [src/hadavin_sdk/audit/chain.py]  ... 
L35 chain.py:171-171 [src/hadavin_sdk/audit/chain.py] self.checkpoint_every = checkpoint_every
L35 anchor_s3.py:70-70 [src/hadavin_sdk/audit/anchor_s3.py] def all(self) -> dict[int, tuple[str, str]]:
L35 cli.py:349-363 [src/hadavin_sdk/cli.py*] def audit_verify(audit) -> int: ... return 0 if result.ok else 1
L36 audit/signer.py:104-108 [src/hadavin_sdk/audit/signer.py] else: ... source, pem = str(path), path.read_bytes()
L36 actions/secrets_file.py:34-64 [src/hadavin_sdk/actions/secrets_file.py] # ConfigError on `..`, absolute names or links out of the folder. The result is the real p ... ) from None
L37 agent_loop.py:83-83 [src/hadavin_sdk/runtime/agent_loop.py] GUARD_STOP_REASONS = frozenset(
L37 agent_loop.py(ctx):79-82 [src/hadavin_sdk/runtime/agent_loop.py] # What K6 counts as a caught mistake (it counts every non-null caught_by): only a control  ... # so it carries no caught_by (see "Limits and trust" in the README).
L37 agent_loop.py(ctx):569-575 [src/hadavin_sdk/runtime/agent_loop.py] def _abstain(self, run: Run, new: RunState, reason: str | None, cited: list[str]) -> Run: ... caught = "guard" if reason in GUARD_STOP_REASONS else None
L37 agent_loop.py(ctx):244-244 [src/hadavin_sdk/runtime/agent_loop.py] return self._to(run, S.NEEDS_PERSON, f"limits.{blocked[0]}")
L37 agent_loop.py(ctx):672-672 [src/hadavin_sdk/runtime/agent_loop.py] return self._to(run, S.NEEDS_PERSON, "limits_unavailable")
L37 agent_loop.py(ctx):703-703 [src/hadavin_sdk/runtime/agent_loop.py] return self._to(run, S.DENIED, decision.rule_id)
L38 config.py:317-317 [src/hadavin_sdk/config.py*] environment: Literal["dev", "pilot", "prod"]
L38 deferred.py:33-33 [src/hadavin_sdk/deferred.py] LIVE = ("pilot", "prod")
L38 backends/table.py:593-602 [src/hadavin_sdk/backends/table.py] DEV_ONLY: frozenset[tuple[str, str]] = frozenset( ... )
L38 config.py:366-370 [src/hadavin_sdk/config.py*] if self.environment != "dev": ... refused += ["allow_insecure_loopback"] if self.allow_insecure_loopback
L38 config.py:453-460 [src/hadavin_sdk/config.py*] except (ValueError, TypeError, yaml.YAMLError) as exc:  # pydantic errors are ValueErrors ... 
L38 config.py:400-415 [src/hadavin_sdk/config.py*] class _UniqueKeyLoader(yaml.SafeLoader): ... return yaml.load(text, Loader=_UniqueKeyLoader)  # noqa: S506  # nosec
L39 config.py:41-47 [src/hadavin_sdk/config.py*] if isinstance(v, float): ... Money = Annotated[Decimal, BeforeValidator(_money)]
L39 config.py:57-58 [src/hadavin_sdk/config.py*] input_usd_per_mtok: Money ... output_usd_per_mtok: Money
L39 registry.py:33-37 [src/hadavin_sdk/registry.py] class Budget(BaseModel): ... 
L39 registry.py:53-53 [src/hadavin_sdk/registry.py] max_run_usd: Money | None = (
L39 models.py:294-294 [src/hadavin_sdk/models.py] cost_usd: Decimal = Decimal(0)
L39 models.py:305-305 [src/hadavin_sdk/models.py] cost_usd: Decimal = Decimal(
L39 models.py:98-98 [src/hadavin_sdk/models.py] cost_usd: Decimal = Decimal(0)
L40 models.py:218-222 [src/hadavin_sdk/models.py] class DeadLetter(Shape): ... ts: datetime = Field(default_factory=now)
L40 extract.py:18-25 [src/hadavin_sdk/extract.py] @dataclass ... return sum((r.cost_usd for r in self.replies), Decimal(0))
L40 guard/runmap.py:218-227 [src/hadavin_sdk/guard/runmap.py] def storable(mapping: dict[str, str], kinds: frozenset[str] | None = None) -> dict[str, st ... 
L40 runmap.py:560-568 [src/hadavin_sdk/guard/runmap.py] def restore_value(value: Any, mapping: dict[str, str], kinds: frozenset[str] | None = None ... 
L40 defaults.py:108-122 [src/hadavin_sdk/defaults.py] STORED_KINDS = ( ... )  # not UUID: a UUID is often a session or API token, so it is placeh
L40 runmap.py:275-304 [src/hadavin_sdk/guard/runmap.py] def escape_placeholders(text: str) -> str: ... 
L40 evals.py:63-63 [src/hadavin_sdk/evals.py] doc = runmap.redact_untrusted(doc.decode("utf-8", "replace"), {}).encode("utf-8")
L41 guard/injection.py:85-101 [src/hadavin_sdk/guard/injection.py] def injection_check(detector: Detector, text: str, source: str) -> Verdict: ... return Verdict(flagged=True, score=1.0, backend=name, reason_code="gua
L41 judge.py:100-109 [src/hadavin_sdk/guard/judge.py] def qualify(judge: JudgeDetector, golden: Path) -> tuple[int, int]: ... return passed, len(cases)
L41 retry.py:97-99 [src/hadavin_sdk/llm/retry.py] except Exception as exc:  # every failure is classified below, never swallowed ... raise ProviderError(f"{label}: {describe(exc, detail)}") from exc
L42 backends/factory.py:17-54 [src/hadavin_sdk/backends/factory.py] @dataclass(frozen=True) ... built = getattr(module, func)(settings, deps)
L42 backends/table.py:570-579 [src/hadavin_sdk/backends/table.py] ALLOWED: dict[str, frozenset[str]] = { ... }
L42 llm/anthropic.py:80-88 [src/hadavin_sdk/llm/anthropic.py] def make(settings: Any, deps: Any) -> AnthropicLLM: ... )
L42 llm/common.py:200-206 [src/hadavin_sdk/llm/common.py] def __init__( ... self.routes, self.max_attempts, self._sleep = routes, max_attempts, sl
L43 table.py(ctx):107-120 [src/hadavin_sdk/backends/table.py]  ... purge_dsn_secret_name: str | None = None
L43 table.py(ctx):132-154 [src/hadavin_sdk/backends/table.py] @model_validator(mode="after") ... mode: Literal["GOVERNANCE", "COMPLIANCE"] = "GOVERNANCE"
L44 store/protocol.py:151-160 [src/hadavin_sdk/store/protocol.py] def missing_methods(store: object) -> list[str]: ... )
L44 app.py:147-150 [src/hadavin_sdk/app.py] if lacking := missing_methods(store): ... )
L44 tests/test_k5_round6_contracts.py:14-16 [tests/test_k5_round6_contracts.py] class OldStore: ... def get_run(self, run_id): ...
L44 tests/contracts/kinds/store_postgres.py:59-71 [tests/contracts/kinds/store_postgres.py] class _SplitStore: ... 
L45 store/migrate.py:46-67 [src/hadavin_sdk/store/migrate.py] GRANTS: dict[str, Grant] = { ... "dead_letters_seq_seq": Grant("sequence", "USAGE"),
L45 store/migrate.py(ctx):150-166 [src/hadavin_sdk/store/migrate.py] def check_grants(paths: list[Path]) -> list[str]: ... return problems
L45 store/migrate.py(ctx):169-181 [src/hadavin_sdk/store/migrate.py] def _apply_grants(db, role_name: str, privileges, columns=None) -> None: ... db.execute(sql.SQL("GRANT {} ON {} {} TO {}").format(sql.SQL(wanted), 
L45 store/migrate.py(ctx):70-70 [src/hadavin_sdk/store/migrate.py] _ROLE = re.compile(r"[a-z_][a-z0-9_]{0,62}")
L45 store/migrate.py(ctx):71-86 [src/hadavin_sdk/store/migrate.py] _FILE = re.compile(r"(\d{4})_[a-z0-9_]+\.sql") ... _ANY_CREATE = re.compile(r"\bCREATE\b", re.IGNORECASE)
L46 k1b/loop.py(ctx):40-52 [src/hadavin_sdk/k1b/loop.py] class Budget: ... return self.spent >= self.limit
L46 k1b/loop.py(ctx):179-179 [src/hadavin_sdk/k1b/loop.py] budget.charge(reply.cost_usd)
L46 k1b/loop.py(ctx):206-206 [src/hadavin_sdk/k1b/loop.py] budget.charge(verdict.cost_usd)
L46 k1b/loop.py(ctx):115-122 [src/hadavin_sdk/k1b/loop.py] def worst_case_usd(route: Route, system: str, messages: list[dict[str, str]]) -> Decimal: ... ) / Decimal(1_000_000)
L46 k1b/loop.py(ctx):170-170 [src/hadavin_sdk/k1b/loop.py] budget.charge(worst_case_usd(route_prices, system, messages))
L46 cli.py:115-117 [src/hadavin_sdk/cli.py*] rep.add_argument( ... )
L74 tests/test_s5_runtime.py:107-111 [tests/test_s5_runtime.py] def test_budget_crossed_by_this_call_is_denied_at_the_gate(cfg_dir): ... assert (run.state, run.reason_code) == (S.DENIED, "limits.daily_budget
L74 tests/test_k5_tools.py:723-731 [tests/test_k5_tools.py] def test_k5_run_budget_stops_run(tmp_path): ... assert next(e for e in _events(rt, run) if e.operation == "abstain").c
L74 agent_loop.py:245-249 [src/hadavin_sdk/runtime/agent_loop.py] cap = self.registry.agents[run.agent_id].max_run_usd ... return self._abstain(run, S.NEEDS_PERSON, "run_budget", cited or [])
L76 k1b/replay.py:85-90 [src/hadavin_sdk/k1b/replay.py] def _refuse_zero_price(registry: Registry, agent_id: str, llm_kind: str) -> None: ... raise ConfigError("replay refuses a route with a zero input or output 
L83 anchor_s3.py:1-12 [src/hadavin_sdk/audit/anchor_s3.py] """Checkpoint anchors in an S3 bucket under Object Lock (`pip install hadavin-sdk[aws]`). ... """
L102 retry.py:92-107 [src/hadavin_sdk/llm/retry.py] for attempt in range(1, max_attempts + 1): ... sleep(max(jitter, retry_after(exc)))
L102 backends/table.py:40-40 [src/hadavin_sdk/backends/table.py] max_attempts: int = Field(default=3, ge=1, le=10)
L129 store/migrate.py:46-67 [src/hadavin_sdk/store/migrate.py] GRANTS: dict[str, Grant] = { ... "dead_letters_seq_seq": Grant("sequence", "USAGE"),
L147 migrate.py:47-47 [src/hadavin_sdk/store/migrate.py] "runs": Grant("table", _RW, portal=True, purge_cols=("run_id", "state", "updated_at")),
L150 config.py:41-47 [src/hadavin_sdk/config.py*] if isinstance(v, float): ... Money = Annotated[Decimal, BeforeValidator(_money)]
L150 models.py:294-294 [src/hadavin_sdk/models.py] cost_usd: Decimal = Decimal(0)
L150 models.py(ctx):305-305 [src/hadavin_sdk/models.py] cost_usd: Decimal = Decimal(
L161 llm/protocol.py(ctx):431-431 [src/hadavin_sdk/llm/protocol.py] BEYOND EOF(29)
L173 common.py:244-244 [src/hadavin_sdk/llm/common.py] retryable: Callable[[BaseException], bool | None] | None = None
L173 bedrock.py:93-101 [src/hadavin_sdk/llm/bedrock.py] def detail(exc: BaseException) -> str: ... return " ".join(str(p) for p in (status, _code(exc)) if p)
L177 fake.py:50-53 [src/hadavin_sdk/llm/fake.py] cost = ( ... ) / Decimal(1_000_000)
L182 k1b/loop.py:115-115 [src/hadavin_sdk/k1b/loop.py] def worst_case_usd(route: Route, system: str, messages: list[dict[str, str]]) -> Decimal:
L182 common.py:65-83 [src/hadavin_sdk/llm/common.py] def tools_for( ... ], None
L182 common.py:86-100 [src/hadavin_sdk/llm/common.py] def turns( ... return out
L182 k1b/loop.py:115-124 [src/hadavin_sdk/k1b/loop.py] def worst_case_usd(route: Route, system: str, messages: list[dict[str, str]]) -> Decimal: ... 
L184 backends/table.py:34-40 [src/hadavin_sdk/backends/table.py]  ... max_attempts: int = Field(default=3, ge=1, le=10)
L184 limits.py:48-51 [src/hadavin_sdk/limits.py] def reset(self, by: str) -> None: ... self.store.set_kill_switch(KillSwitch(on=False, by=by))
L184 cli.py:183-190 [src/hadavin_sdk/cli.py*] try: ... audit = make("audit", b.audit, secrets, store=store, signer=signer, an
L209 llm/retry.py(ctx):95-96 [src/hadavin_sdk/llm/retry.py] except ProviderError: ... raise
L213 backends/factory.py:17-26 [src/hadavin_sdk/backends/factory.py] @dataclass(frozen=True) ... llm: Any = None
L213 backends/table.py:570-579 [src/hadavin_sdk/backends/table.py] ALLOWED: dict[str, frozenset[str]] = { ... }
L213 anthropic.py(ctx):95-104 [src/hadavin_sdk/llm/anthropic.py] def __init__( ... self._client, self._key = client, key
L213 bedrock.py(ctx):118-126 [src/hadavin_sdk/llm/bedrock.py] def __init__( ... self._client = client
L213 backends/builtin.py:39-40 [src/hadavin_sdk/backends/builtin.py] def fake_llm(settings, deps) -> FakeLLM: ... return FakeLLM(settings.recorded_dir, dict(deps.routes))
L213 app.py:162-162 [src/hadavin_sdk/app.py] llm = llm or make("llm", b.llm, secrets, routes=cfg.routes)
L213 cli.py:150-150 [src/hadavin_sdk/cli.py*] make("llm", b.llm, make("secrets", b.secrets), routes=cfg.routes),
L213 cli.py:221-221 [src/hadavin_sdk/cli.py*] llm = make("llm", cfg.backends.llm, secrets, routes=cfg.routes)
L213 app.py:171-171 [src/hadavin_sdk/app.py] limits = Limits(store, audit, reg)
L213 app.py(ctx):162-162 [src/hadavin_sdk/app.py] llm = llm or make("llm", b.llm, secrets, routes=cfg.routes)
L213 app.py(ctx):165-165 [src/hadavin_sdk/app.py] members = [make("detector", d, secrets, llm=llm) for d in b.detector]
L214 agent_loop.py:184-202 [src/hadavin_sdk/runtime/agent_loop.py] def __init__( ... self.hooks = hooks or Hooks()
L214 tests/k5_support.py:160-204 [tests/k5_support.py] def build_runtime( ... llm,
L215 app.py:90-98 [src/hadavin_sdk/app.py] if sources and live: ... )
L216 k1b/loop.py:104-104 [src/hadavin_sdk/k1b/loop.py] t = threading.Thread(target=work, daemon=True, name="k1b-llm-call")
L216 k1b/loop.py(ctx):92-104 [src/hadavin_sdk/k1b/loop.py] def work() -> None: ... t = threading.Thread(target=work, daemon=True, name="k1b-llm-call")
L222 agent_loop.py:425-425 [src/hadavin_sdk/runtime/agent_loop.py] reply = self.llm.chat(
L222 guard/judge.py:72-72 [src/hadavin_sdk/guard/judge.py] reply = self.llm.chat(
L222 guard/judge.py(ctx):310-316 [src/hadavin_sdk/guard/judge.py] BEYOND EOF(110)
L222 guard/judge.py(ctx):387-387 [src/hadavin_sdk/guard/judge.py] BEYOND EOF(110)
L222 guard/judge.py(ctx):520-520 [src/hadavin_sdk/guard/judge.py] BEYOND EOF(110)
L223 evals.py:73-73 [src/hadavin_sdk/evals.py] reply = llm.chat(
L223 evals.py:109-109 [src/hadavin_sdk/evals.py] ok, total = judge.qualify(judge.JudgeDetector(llm, d.route, d.threshold), path)
L224 extract.py:47-47 [src/hadavin_sdk/extract.py] reply = llm.chat(
L225 k1b/loop.py:94-94 [src/hadavin_sdk/k1b/loop.py] box["reply"] = llm.chat(*args, **kwargs)  # type: ignore[arg-type]
L225 k1b/loop.py:179-179 [src/hadavin_sdk/k1b/loop.py] budget.charge(reply.cost_usd)
L225 k1b/loop.py(ctx):206-206 [src/hadavin_sdk/k1b/loop.py] budget.charge(verdict.cost_usd)
L225 k1b/loop.py(ctx):170-170 [src/hadavin_sdk/k1b/loop.py] budget.charge(worst_case_usd(route_prices, system, messages))
L226 bedrock_guardrail.py:101-101 [src/hadavin_sdk/guard/bedrock_guardrail.py] resp = self._client.apply_guardrail(
L227 demos/ask-your-data/askdata/pipeline.py:155-155 [demos/ask-your-data/askdata/pipeline.py] reply = self.llm.chat(
L229 guard/injection.py:85-101 [src/hadavin_sdk/guard/injection.py] def injection_check(detector: Detector, text: str, source: str) -> Verdict: ... return Verdict(flagged=True, score=1.0, backend=name, reason_code="gua
L229 judge.py:100-109 [src/hadavin_sdk/guard/judge.py] def qualify(judge: JudgeDetector, golden: Path) -> tuple[int, int]: ... return passed, len(cases)
L231 agent_loop.py:440-441 [src/hadavin_sdk/runtime/agent_loop.py] self.limits.charge(agent_id, reply.cost_usd) ... self.store.add_cost(run.run_id, reply.cost_usd)
L231 agent_loop.py(ctx):313-315 [src/hadavin_sdk/runtime/agent_loop.py] if verdict.cost_usd: ... self.store.add_cost(run.run_id, verdict.cost_usd)
L233 guard/producers.py:5-5 [src/hadavin_sdk/guard/producers.py] that calls a model (`.chat(` or `.apply_guardrail(`) is not listed, or when a message is c
L235 tests/test_s5_runtime.py:107-111 [tests/test_s5_runtime.py] def test_budget_crossed_by_this_call_is_denied_at_the_gate(cfg_dir): ... assert (run.state, run.reason_code) == (S.DENIED, "limits.daily_budget
L249 registry.py:33-36 [src/hadavin_sdk/registry.py] class Budget(BaseModel): ... monthly: Money
L250 cli.py:146-153 [src/hadavin_sdk/cli.py*] if args.cmd == "gate": ... )
L250 cli.py:183-190 [src/hadavin_sdk/cli.py*] try: ... audit = make("audit", b.audit, secrets, store=store, signer=signer, an
L250 evals.py:109-109 [src/hadavin_sdk/evals.py] ok, total = judge.qualify(judge.JudgeDetector(llm, d.route, d.threshold), path)
L251 cli.py:93-95 [src/hadavin_sdk/cli.py*] lim = sub.add_parser("limits", help="kill switch") ... lim.add_argument("--by", required=True)
L251 cli.py:173-182 [src/hadavin_sdk/cli.py*] if b.store.kind == "memory": ... return 2
L256 agent_loop.py:325-541 [src/hadavin_sdk/runtime/agent_loop.py] def handle( ... 
L256 agent_loop.py(ctx):387-387 [src/hadavin_sdk/runtime/agent_loop.py] verdict = self._screen(run, safe_text, "document")
L256 agent_loop.py(ctx):425-425 [src/hadavin_sdk/runtime/agent_loop.py] reply = self.llm.chat(
L256 agent_loop.py(ctx):520-520 [src/hadavin_sdk/runtime/agent_loop.py] verdict = self._screen(run, out.text, f"tool:{call.name}")
L258 agent_loop.py:318-322 [src/hadavin_sdk/runtime/agent_loop.py] def _to(self, run: Run, new: RunState, reason: str | None = None) -> Run: ... return run
L261 agent_loop.py(ctx):241-242 [src/hadavin_sdk/runtime/agent_loop.py] if "kill_switch" in blocked: ... return self._to(run, S.STOPPED, "kill_switch")
L263 agent_loop.py(ctx):245-249 [src/hadavin_sdk/runtime/agent_loop.py] cap = self.registry.agents[run.agent_id].max_run_usd ... return self._abstain(run, S.NEEDS_PERSON, "run_budget", cited or [])
L268 agent_loop.py:239-250 [src/hadavin_sdk/runtime/agent_loop.py] def _limits_stop(self, run: Run, cited: list[str] | None = None) -> Run | None: ... return None
L268 agent_loop.py(ctx):244-244 [src/hadavin_sdk/runtime/agent_loop.py] return self._to(run, S.NEEDS_PERSON, f"limits.{blocked[0]}")
L270 agent_loop.py:569-597 [src/hadavin_sdk/runtime/agent_loop.py] def _abstain(self, run: Run, new: RunState, reason: str | None, cited: list[str]) -> Run: ... return run
L270 agent_loop.py(ctx):560-567 [src/hadavin_sdk/runtime/agent_loop.py] def _deliver(self, card: Card | None) -> Delivery: ... return Delivery(ok=False, reason=type(exc).__name__)
L270 agent_loop.py(ctx):87-87 [src/hadavin_sdk/runtime/agent_loop.py] _REASON_TEXT = {"ungrounded": "ungrounded (inputs not found in cited evidence)"}
L270 agent_loop.py(ctx):669-672 [src/hadavin_sdk/runtime/agent_loop.py] try:  # limits unreadable: stop means stop, so no card is posted ... return self._to(run, S.NEEDS_PERSON, "limits_unavailable")
L270 agent_loop.py(ctx):702-703 [src/hadavin_sdk/runtime/agent_loop.py] if decision.rule_id.startswith("limits."):  # stop means stop: no card, at any level ... return self._to(run, S.DENIED, decision.rule_id)
L270 agent_loop.py(ctx):83-83 [src/hadavin_sdk/runtime/agent_loop.py] GUARD_STOP_REASONS = frozenset(
L274 app.py:161-161 [src/hadavin_sdk/app.py] audit = make("audit", b.audit, secrets, store=store, signer=signer, anchor=anchor)
L274 config.py:349-375 [src/hadavin_sdk/config.py*] @model_validator(mode="after") ... 
L274 config.py:453-460 [src/hadavin_sdk/config.py*] except (ValueError, TypeError, yaml.YAMLError) as exc:  # pydantic errors are ValueErrors ... 
L276 app.py:171-171 [src/hadavin_sdk/app.py] limits = Limits(store, audit, reg)
L276 cli.py:209-209 [src/hadavin_sdk/cli.py*] return kill_switch(Limits(store, audit, reg), args.action, args.by)
L276 tests/test_s5_runtime.py:28-28 [tests/test_s5_runtime.py] limits = Limits(store, audit, reg)
L276 tests/k5_support.py:206-206 [tests/k5_support.py] Limits(store, audit, reg),
L276 tests/test_k3_pilot.py:104-104 [tests/test_k3_pilot.py] Limits(store, audit, reg),
L276 tests/test_k5_postgres.py:58-58 [tests/test_k5_postgres.py] Limits(pg_store, audit, reg),
L276 tests/test_k5_round5.py:241-241 [tests/test_k5_round5.py] reg, store, audit, ScriptLLM([]), RegexDetector(0.5), Limits(store, audit, reg),
L276 tests/test_k5_tools.py:1133-1133 [tests/test_k5_tools.py] reg, store, audit, ScriptLLM([]), RegexDetector(0.5), Limits(store, audit, reg),
L276 tests/test_k5_tools.py(ctx):1269-1269 [tests/test_k5_tools.py] Limits(store, audit, reg),
L276 limits.py:18-18 [src/hadavin_sdk/limits.py] return self.store.add_spend(agent_id, now().date(), usd)
L276 limits.py(ctx):24-24 [src/hadavin_sdk/limits.py] day, month = self.store.spend_totals(agent_id, now().date())  # a read, no write
L276 app.py:73-73 [src/hadavin_sdk/app.py] clock: Callable[[], datetime] = now,
L278 registry.py:338-338 [src/hadavin_sdk/registry.py] def _cross_check(config, agents, chains, contracts) -> list[str]:
L278 k1b/replay.py:85-90 [src/hadavin_sdk/k1b/replay.py] def _refuse_zero_price(registry: Registry, agent_id: str, llm_kind: str) -> None: ... raise ConfigError("replay refuses a route with a zero input or output 
L278 judge.py:3-4 [src/hadavin_sdk/guard/judge.py] The only cloud-agnostic model detector: it runs on any configured llm route and kind (Clau ... or a local open-weights model on `openai_compat`), so regex + llm_judg
L285 chain.py:161-161 [src/hadavin_sdk/audit/chain.py] checkpoint_every: int = 100,
L285 chain.py:519-547 [src/hadavin_sdk/audit/chain.py] """`backends.audit: {kind: chain, checkpoint_every, anchor}`, in the store's database.""" ... return ChainAudit(db, deps.signer, deps.anchor, settings.checkpoint_ev
L287 anchor_gcs.py:69-85 [src/hadavin_sdk/audit/anchor_gcs.py] def probed(bucket: Any, settings) -> GcsAnchor: ... return GcsAnchor(bucket)
L287 anchor_azure.py:83-96 [src/hadavin_sdk/audit/anchor_azure.py] def probed(container: Any, settings) -> AzureBlobAnchor: ... )
L289 cli.py:349-363 [src/hadavin_sdk/cli.py*] def audit_verify(audit) -> int: ... return 0 if result.ok else 1
L289 chain.py:171-171 [src/hadavin_sdk/audit/chain.py] self.checkpoint_every = checkpoint_every
L289 chain.py:203-203 [src/hadavin_sdk/audit/chain.py] if self.signer is not None and seq % self.checkpoint_every == 0:
L293 evals.py:63-63 [src/hadavin_sdk/evals.py] doc = runmap.redact_untrusted(doc.decode("utf-8", "replace"), {}).encode("utf-8")
L293 models.py:221-221 [src/hadavin_sdk/models.py] errors: list[str]
L293 evals.py:63-63 [src/hadavin_sdk/evals.py] doc = runmap.redact_untrusted(doc.decode("utf-8", "replace"), {}).encode("utf-8")
L293 extract.py:55-55 [src/hadavin_sdk/extract.py] try:
L305 actions/secrets_file.py:49-64 [src/hadavin_sdk/actions/secrets_file.py] with os.fdopen(fd, "rb") as f: ... ) from None
L307 signer.py:104-108 [src/hadavin_sdk/audit/signer.py] else: ... source, pem = str(path), path.read_bytes()
L307 secrets_file.py:54-54 [src/hadavin_sdk/actions/secrets_file.py] if os.name != "nt" and mode & (stat.S_IROTH | stat.S_IWGRP | stat.S_IWOTH):
L308 secrets_file.py:54-54 [src/hadavin_sdk/actions/secrets_file.py] if os.name != "nt" and mode & (stat.S_IROTH | stat.S_IWGRP | stat.S_IWOTH):
L308 config.py:395-396 [src/hadavin_sdk/config.py*] if b.signer.kind == "ed25519_local" and b.signer.private_key_path is not None: ... refused.append("signer ed25519_local with a key file (use private_key_
L308 signer.py:182-182 [src/hadavin_sdk/audit/signer.py] _create(private_real, pem, 0o600)
L309 tests/test_lockin_guard.py:68-75 [tests/test_lockin_guard.py] LIBRARY_IMPORTS: dict[str, set[str]] = {  # open-source libraries kept in their layer ... "markdown_it": {f"{PKG}.approvals.gate"},
L315 tests/test_g4_parity.py:98-98 [tests/test_g4_parity.py] "update its set of rules",
L338 gate.py:4-4 [src/hadavin_sdk/approvals/gate.py] (`sanitise_text` and its helpers) and G4 (`withhold_commands`, rewritten platform-neutral 
L338 gate.py:366-377 [src/hadavin_sdk/approvals/gate.py]  ... #
L338 channel.py:19-21 [src/hadavin_sdk/approvals/channel.py] """WARDEN's G3 cleaning (`gate.sanitise_text`): no link, image, HTML, mention, control cha ... paste to change a system, on any platform; then ONE redaction, last.""
L339 gate.py:546-546 [src/hadavin_sdk/approvals/gate.py] _TOKEN = re.compile(r"[^\S\n]+([^\s]+)")
L339 gate.py:695-695 [src/hadavin_sdk/approvals/gate.py] end = text.find("\n", m.end())
L340 gate.py:608-615 [src/hadavin_sdk/approvals/gate.py] def _story(text: str, prog: str, s: int, e: int, toks: list[str]) -> bool: ... return True  # `the aws Lambda runtime`: a capitalised word or punctua
L342 gate.py:674-674 [src/hadavin_sdk/approvals/gate.py] r"|\brm\s+(?:-[a-zA-Z]*[rRf][a-zA-Z]*|--recursive|--force)(?=\s+\S)"
L342 gate.py:540-540 [src/hadavin_sdk/approvals/gate.py] _NAMES = ["aws", *_VERB_FIRST, *_WORD_RUN]
L343 gate.py:404-404 [src/hadavin_sdk/approvals/gate.py] _AWS_READ_PREFIXES = ("describe-", "get-", "list-", "head-", "batch-get-", "lookup-", "sea
L343 gate.py(ctx):597-597 [src/hadavin_sdk/approvals/gate.py] words[1].startswith(_AWS_READ_PREFIXES) or (words[0] == "s3" and words[1] == "ls")
L348 gate.py:573-589 [src/hadavin_sdk/approvals/gate.py] def _subcommands(toks: list[str]) -> list[str]: ... return words
L353 guard/redact.py:472-472 [src/hadavin_sdk/guard/redact.py] "PHONE",
L354 guard/redact.py(ctx):247-247 [src/hadavin_sdk/guard/redact.py] "IBAN",
L355 guard/redact.py(ctx):451-451 [src/hadavin_sdk/guard/redact.py] ("CREDITCARD", re.compile(r"\b\d{4}[ \-]\d{4}[ \-]\d{4}[ \-]\d{4}\b")),
L355 tests/warden_port/privacy_corpus.py:42-42 [tests/warden_port/privacy_corpus.py] "card 4111 1111 1111 1111",
L355 tests/warden_port/test_redaction.py:309-309 [tests/warden_port/test_redaction.py] for pan in ("4111 1111 1111 1111", "4111-1111-1111-1111"):
L356 tests/warden_port/test_redaction.py(ctx):236-236 [tests/warden_port/test_redaction.py] 
L357 redact.py(ctx):513-513 [src/hadavin_sdk/guard/redact.py] # A HAR entry (`{"name": "Cookie", "value": "..."}`), curl's `--cookie`/`-b`, and a cookie
L357 k1b/redaction.py:103-103 [src/hadavin_sdk/k1b/redaction.py] def _pair(key: str, value: str, f: Callable[[str], str]) -> str:
L363 config.py:453-453 [src/hadavin_sdk/config.py*] except (ValueError, TypeError, yaml.YAMLError) as exc:  # pydantic errors are ValueErrors
L363 config.py:317-317 [src/hadavin_sdk/config.py*] environment: Literal["dev", "pilot", "prod"]
L363 config.py(ctx):366-367 [src/hadavin_sdk/config.py*] if self.environment != "dev": ... refused = [
L363 config.py(ctx):19-19 [src/hadavin_sdk/config.py*] from hadavin_sdk.backends.table import DEFAULTS, DEV_ONLY, NOT_PROD, TABLE, KindSettings
L363 backends/table.py:593-593 [src/hadavin_sdk/backends/table.py] DEV_ONLY: frozenset[tuple[str, str]] = frozenset(
L363 tests/test_lockin_guard.py:18-18 [tests/test_lockin_guard.py] from hadavin_sdk.backends.table import DEV_ONLY, NOT_PROD, TABLE
L363 tests/fixtures/config/config.yaml:2-2 [tests/fixtures/config/config.yaml] environment: dev
L363 tests/test_p4_secrets.py:106-106 [tests/test_p4_secrets.py] def _config(tmp_path, secrets, environment="dev"):
L363 tests/warden_port/test_audit_chain.py:568-568 [tests/warden_port/test_audit_chain.py] found = _anchor_refusals("dev", _backends(ANCHOR, KMS, local))
L363 tests/test_p1b_backends.py:89-91 [tests/test_p1b_backends.py] @pytest.mark.parametrize("env", ["pilot", "prod"]) ... _edit(cfg_dir, lambda d: d.update(environment=env))
L363 actions/secrets_env.py:1-1 [src/hadavin_sdk/actions/secrets_env.py] """`env` secrets: read from environment variables (`dev` only, by the environment table).
L363 audit/signer.py:64-64 [src/hadavin_sdk/audit/signer.py] """An Ed25519 key in a PEM file (dev and pilot; refused in prod by the environment table).
L363 table.py:126-126 [src/hadavin_sdk/backends/table.py] # (`require`, `disable`) is an explicit opt-down for dev, refused with iam_auth.
L363 config.py:346-346 [src/hadavin_sdk/config.py*] )  # dev executor only
L363 defaults.py:100-100 [src/hadavin_sdk/defaults.py] EXECUTOR_TIMEOUT_S = 10.0  # the dev executor's per-call timeout (Config.executor_timeout_
L363 registry.py:50-50 [src/hadavin_sdk/registry.py] # Per-action autonomy. None only in dev (the slice-1 gate path). Not part of config_hash: 
L363 tools.py:361-361 [src/hadavin_sdk/tools.py*] Without a pin (dev only; pilot and prod require one) it is an ordinary import."""
L363 agent_loop.py:179-179 [src/hadavin_sdk/runtime/agent_loop.py] # Keys the HMAC of the restored inputs on the gate's audit event (None: a plain hash, dev 
L363 actions/contract.py:34-34 [src/hadavin_sdk/actions/contract.py] """Hadavin-run execution (Phase 2): refused in pilot and prod, kept in dev for the slice-1
L363 store/postgres.py:75-75 [src/hadavin_sdk/store/postgres.py] captured by an impostor); an explicit weaker `sslmode` is an opt-down for dev. With iam_au
L363 guard/redact.py:1162-1162 [src/hadavin_sdk/guard/redact.py] "dev",
L364 backends/table.py:155-155 [src/hadavin_sdk/backends/table.py] retain_days: int = Field(default=1, ge=1)
L364 config.py:377-398 [src/hadavin_sdk/config.py*] def _anchor_refusals(environment: str, b: Backends) -> list[str]: ... 
L364 table.py:150-157 [src/hadavin_sdk/backends/table.py] class _AnchorSettings(KindSettings): ... 
L364 anchor_gcs.py:69-85 [src/hadavin_sdk/audit/anchor_gcs.py] def probed(bucket: Any, settings) -> GcsAnchor: ... return GcsAnchor(bucket)
L364 anchor_azure.py:83-96 [src/hadavin_sdk/audit/anchor_azure.py] def probed(container: Any, settings) -> AzureBlobAnchor: ... )
L374 cli.py:183-190 [src/hadavin_sdk/cli.py*] try: ... audit = make("audit", b.audit, secrets, store=store, signer=signer, an
L393 agent_loop.py:313-315 [src/hadavin_sdk/runtime/agent_loop.py] if verdict.cost_usd: ... self.store.add_cost(run.run_id, verdict.cost_usd)
L393 agent_loop.py(ctx):440-441 [src/hadavin_sdk/runtime/agent_loop.py] self.limits.charge(agent_id, reply.cost_usd) ... self.store.add_cost(run.run_id, reply.cost_usd)
L393 tests/test_s5_runtime.py:107-111 [tests/test_s5_runtime.py] def test_budget_crossed_by_this_call_is_denied_at_the_gate(cfg_dir): ... assert (run.state, run.reason_code) == (S.DENIED, "limits.daily_budget
L409 tests/k5_support.py:160-204 [tests/k5_support.py] def build_runtime( ... llm,
L436 test_s5_runtime.py:107-111 [tests/test_s5_runtime.py] def test_budget_crossed_by_this_call_is_denied_at_the_gate(cfg_dir): ... assert (run.state, run.reason_code) == (S.DENIED, "limits.daily_budget
```
