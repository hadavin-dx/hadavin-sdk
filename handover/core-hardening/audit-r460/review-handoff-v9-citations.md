# Independent citation check of CORE-PR-HANDOFF-v9 (spend track) and v9-other-tracks, 2026-11-16 UTC

Checker: citation checker (checks, does not rewrite). I did not use the builder's `cite_check_v9.py`. My own programs and raw output are in `evidence-handoff-v9-independent/`. Nothing was run except reads, greps and read-only Python that parses source text. No test suite, no network, no spend, no commit.

## Counts (at the top)

| Item | Result |
|---|---|
| Cite occurrences extracted by my own program (path:line, `:line` after a path, ranges) | 240 (158 in the spend file, 82 in the other-tracks file); 203 distinct (file, range) pairs |
| Cites where I opened the file at the cited line and read the actual text | all 240 (printed in `raw-cites-shown.txt`) |
| WRONG | 1 cite plus 1 wrong count plus 1 unsupported count (details below) |
| UNREADABLE | 0 |
| Cites that need a second look at meaning only (range loose by one blank or comment line) | 4 (listed under "Minor") |
| Import cycles | builder's numbers REPRODUCED under the builder's counting; one caveat below |
| Counts of the builder's own script | it reports 113 (spend) and 72 (other tracks); `v9-CHANGES.md` says 104 for the spend file. My program finds more because it also counts a bare `:NNN` that follows a path. The 104 against 113 difference is inside the builder's own papers (see C3). |

## Failures first

### C1. WRONG cite: `chain.py:171` (other-tracks, section O-4.6, line 59)
Text: "`ChainAudit.verify` passes `self.checkpoint_every` (`chain.py:171`)".
What the line holds: `src/hadavin_sdk/audit/chain.py:171` is `self.checkpoint_every = checkpoint_every` (a constructor assignment). The real `ChainAudit.verify` ends at `chain.py:360` with `return verify_rows(rows, checkpoints, public, anchors, alg, row_algs)`, which passes no `checkpoint_every`. So the sentence describes a change that does not exist yet as if it did, and the cite does not support it. Fix: say "will pass" and cite `chain.py:360` (the call) plus `:171` (where the value is kept).

### C2. WRONG count: "calls `Limits(` in nine places" (spend file, F16, line 51, marked "carried")
My grep (`raw-greps-independent.txt`): the core `Limits` class is constructed at 7 test sites (`tests/test_k5_round5.py:241`, `tests/k5_support.py:206`, `tests/test_k5_postgres.py:58`, `tests/test_k5_tools.py:1133` and `:1269`, `tests/test_k3_pilot.py:104`, `tests/test_s5_runtime.py:28`). Nine is true only if the two source sites (`app.py:171`, `cli.py:209`) are added. The sentence is about the test suite. (`tests/demo_askdata/*` and `demos/` use a different class also named `Limits`; they are not counted.)

### C3. UNSUPPORTED count in `v9-CHANGES.md` (not a target file, but it states a number the targets contradict)
- "six test sites build a non-fake kind": spend file section 5.1 item 5 lists five places (`test_k3_pilot_env.py:61`, `test_p5p6_followups.py:82` and `:392`, `test_p5_llm.py:38-46`, `test_p1a_fixes.py:117`). By line, `test_p5_llm.py` alone has five config lines (38, 40, 42, 43, 46), giving nine lines in four files. Six matches neither.
- "104 in SP" against the program output `TOTAL cites=113`: two numbers for one thing.

### C4. Caveat on the import-cycle claim (not a wrong cite, a limit of the claim)
My own program (`cycles.py`, ast based, 102 modules) reproduces the builder's numbers under the builder's counting (module-level imports, parent package not counted as imported):
- run time only: 1 cycle, 3 modules (`approvals`, `approvals.channel`, `approvals.requests`), 330 edges;
- with `TYPE_CHECKING` imports: 3 cycles (`config`/`deferred`/`registry`/`replay_records`; the 4-module approvals set that includes `approvals.cards`; `k1b.replay`/`k1b.report`/`k1b.score`), 335 edges;
- planned table of section 4.2, read from the document: 0 new cycles under both countings.
So "3 versus 4" is right: 3 cycles, and the approvals one has 4 modules once `TYPE_CHECKING` is counted.
Caveat: Python really runs a package's `__init__.py` when a submodule is imported. If that parent edge is counted, today has 4 run-time cycles and 6 with `TYPE_CHECKING`, and with the planned table `llm.spend` and `llm.callgate` would join the existing big cycle (`config`, `deferred`, `guard.judge`, `llm`, `llm.common`, `llm.fake`, `llm.retry`, `registry`, `replay_records`). The count of cycles does not change, but the sentence "no module in this table may end up in an import cycle that does not exist today" would then fail for those two new modules, because `llm/__init__.py` imports `llm.fake` and `llm.protocol`. The document does not say which counting it uses for the parent package. Fix: state it, or keep the new modules out of that cycle.

## Verified OK (every item opened at the cited line)

Money / config / limits:
- `config.py:47` is `Money = Annotated[Decimal, BeforeValidator(_money)]`; `_money` is `:40-44` and rejects floats only; `Route` is `:55-59` with exactly `model_id`, `input_usd_per_mtok`, `output_usd_per_mtok`, `max_tokens`; `Config.environment` `Literal["dev","pilot","prod"]` at `:317`; the validator decorator is `:349` (function `_cross_checks`) and the stage table is `:366-373`; `load_config` error mapping `:451-454`; YAML loader `:400-415`; `ed25519_local` prod refusal `:395-396`; `config.py:19`, `:346` fine.
- `Reply.cost_usd` `models.py:294`; `Verdict.cost_usd` `:305`; `runs.cost_usd` `:98`; `Reply`/`Verdict` ranges `:289-297`, `:300-307`; `Shape` is not frozen (`extra="forbid"` only); `models.now` `:19-20`; `new_id` `:23-24` gives `prefix-hex`.
- `Budget` `registry.py:33-36` (cite says 33-37, last line blank); `spend` table `0001_core.sql:87-92`; `spend_month` `0003_approvals_tick.sql:15-20`; both `usd NUMERIC NOT NULL`, no sign check.
- `Limits.__init__(store, audit, registry)` `limits.py:14`; `charge` calls `now()` `:18`; `blocked` `:21-35` reads `registry.agents[agent_id]` and tests `>=`; built at `app.py:171` and `cli.py:209`; `app.py:73` takes `clock`.
- `Store.add_spend` `store/protocol.py:107`; Postgres `:416-431` (one transaction, two upserts with `RETURNING`, `with self._lock, self._db.transaction()`); memory `:196-204` (one lock); one connection `autocommit=True` `postgres.py:146`; class and lock `:192-197`.

Retry / LLM kinds:
- `with_retry` `retry.py:83-108`; `except ProviderError: raise` `:95-96`; non-transient wrapped `:97-99`; `ProviderExhausted` `:100-103`.
- `NetworkLLM.__init__` `common.py:200-206`; `chat` `:208-220`; `_retry` `:233-241`; `estimate_tokens` `:59-62` (`max(1, len(text)//3)`); pricing in `reply()` `:164-172`.
- `self._retry(` at `anthropic.py:122`, `bedrock.py:156`, `gemini.py:86`, `openai_compat.py:119`; two request groups `openai_compat.py:117-129`, tokens summed `:122` and set `:131`; `anthropic.make` `:80-88` builds by hand; `FakeLLM` `fake.py:21` is a plain class; `fake.py:39-40` sha256 key.
- `gemini.py:96-100` adds `thoughtsTokenCount`; the only `thinking` hits in `llm/*.py` are `anthropic.py:136` and `gemini.py:98` (comments); no `cache_control`, `cachedContent`, `cache_read` (grep).
- `Deps` fields `resolve, routes, store, signer, anchor, llm` (`factory.py:17-30`); `ALLOWED["llm"]={"routes"}`, `ALLOWED["detector"]={"llm"}` (`table.py:570-579`); `DEV_ONLY` contains `("llm","fake")` (`table.py:593-602`) and `config.py:366-369` refuses it outside `dev`.

Runtime (`runtime/agent_loop.py`) every cite read: `_REASON_TEXT` `:87` (one key `ungrounded`) and read at `:574`; `GUARD_STOP_REASONS` `:83`; K6 comment `:79-82`; `_limits_stop` `:239-250` (blocked ends with `_to`, no card; `run_budget` goes through `_abstain`); `_screen` charges `verdict.cost_usd` `:310-316`; `_to` `:318-322`; `handle` starts `:325`; document screen `:387`; `chat` `:425`; `except (ProviderError)` `:432`; `limits.charge` `:440`; `add_cost` `:441`; tool screen `:520`; `agent_id` used at `:403`, `:405`, `:418`, `:440`; `_deliver` `:560-567` never raises; `_abstain` `:569-597`; kill switch `:241-242`.

`.chat(` sites (F8) exactly `extract.py:47`, `evals.py:73`, `guard/judge.py:72`, `runtime/agent_loop.py:425`, `k1b/loop.py:94` (the sixth grep hit, `guard/producers.py:5`, is a docstring); `apply_guardrail` only at `bedrock_guardrail.py:101`; `extract(` has no caller in `src/`; `make("llm"` and `make("detector"` at `app.py:162,165` and `cli.py:150,221,222` (five sites, as claimed).

Guard: `GuardrailDetector.check` `:95-101` redacts then calls; `make` `:61` builds with four arguments; `injection_check` `:85-101` catches `Exception` and returns flagged `guard_unavailable`; `combine` sums `cost_usd` `:77`; `JudgeDetector` `judge.py:72-97`.

Demo meter and tests: `meter.py:1-17`, `:48-55`, `reserve` `:211-229`, `settle` `:221-229` (never below zero, above recorded); `pipeline.py:147` reserve, `:155` chat, `:232-236` settle helper; `tests/demo_askdata/test_meter.py` names match the F2 list (two caps, stale figure, broken and missing file, negative amounts, held lock, reserve then settle, four processes and ten reservations at `:153-166`); `k1b/loop.py:94`, `:104` (daemon thread), `:115-122`, `:170`, `:179`, `:206`.

Tests named in the spend file: `test_s5_runtime.py:107-111` (asserts `S.DENIED`, `limits.daily_budget`), `:76` and `test_s4_llm_guard.py:39` (the `0.00225` assertions), `test_k5_tools.py:723-731` (cost 0.30, cap 0.50, two calls, `run_budget`), `:608`; `test_p5p6_followups.py:101`; `test_p6_detectors.py:264,364`; `k5_support.py:160-211`; `ci.yml:119` is `run: bandit -q -r src demos -ll`; fixture route `config.yaml:6-8`; migrations `0001` to `0005` exist; `window_end` appears nowhere in `src/` (grep). Test classes that define `chat`: 26 (my ast count over `tests/`), as claimed.

Other-tracks file, every cite read: `approvals/gate.py` `:4`, `:366-377`, `:404` (`_AWS_READ_PREFIXES`), `:540` (`_NAMES`; `rm` is not a key of `_VERB_FIRST` or `_WORD_RUN`), `:546`, `:573-589`, `:597`, `:608-615`, `:647-678`, `:674` (the `rm` shape), `:681-698`, `:695`; `channel.py:19-21`; `chain.py:134-149`, `:161` (default 100), `:203`, `:363-383`; `table.py:192-193` (`checkpoint_every` default 100), `:150-157`, `:155` (`retain_days` default 1); `cli.py:349-363`; `anchor_gcs.py:69-85` and `anchor_azure.py:83-96` (`probed`); `anchor_s3.py:5-7` (the constraint sentence); `secrets_file.py:34-64`, `:49-64`, `:54`; `signer.py:104-108` (no checks), `:182`, `:197`, `:209`; `evals.py:63` (`"replace"`); `extract.py:18-25`, `:58` (no mapping passed); `models.py:218-222`, `:221` (`errors: list[str]`); `runmap` has `redact_untrusted`, `safe_head`, `storable`, `restore_value`; `redact.py` `:236` EMAIL, `:247` IBAN, `:451` CREDITCARD, `:472` PHONE, `:513` HAR cookie comment, `:1162` word list; `privacy_corpus.py:42`, `test_redaction.py:309,356`; `k1b/redaction.py:103` `_pair`; `test_lockin_guard.py:18,68-75,430`; `test_g4_parity.py:98,221-222`; every H-0 wording site (`secrets_env.py:1`, `signer.py:64,98`, `table.py:126,214,254,591`, `registry.py:50`, `tools.py:361`, `agent_loop.py:179,553,572`, `contract.py:34`, `postgres.py:75,90`, `defaults.py:100`).

## Minor (cites that point at the right place but are loose; fix when the file is next edited)
1. `registry.py:33-37`: `Budget` ends at 36; 37 is blank.
2. `migrate.py:86-90` named `_UNREAD`: `_UNREAD` is `:87-90`; 86 is `_ANY_CREATE`.
3. `postgres.py:191-197`: 191 is blank, the class starts at 192.
4. Bare names with no folder (`gate.py`, `table.py`, `signer.py`, `config.py`, `loop.py`) resolve to one `src/hadavin_sdk` file each, except `config.py`, which also exists as `demos/ask-your-data/askdata/config.py`; the spend file says paths are under `src/hadavin_sdk/` so it is fine, but a bare `:121-170` in section 10 and `:513`, `:236` in the other-tracks file depend on the previous path in the same sentence (all land correctly).

## Not checked
Meaning of vendor and Postgres statements (no network, no database); that the quoted code in the pseudocode fence would run; the future tests; the evidence ids E0-*; text outside the two target files except where noted in C3.

## Hygiene
Banned strings of `tests/test_no_reference_material.py` were scanned in all my output files: 0 hits. Programs used `python -I`; no `__pycache__` was written by my runs (the four `.pyc` files newer than 40 minutes in the repository are in `tests/__pycache__` and `.venv`, which I did not run).
