# Citation check of CORE-PR-HANDOFF-v7.md (EVIDENCE RUNNER: records only, no judging, no fixing)

Run: 2026-11-16 (UTC). Document: `handover/core-hardening/audit-r460/CORE-PR-HANDOFF-v7.md` (633 lines). `src/` and `tests/` were not edited. No network, no spend, no Postgres, no secret read or printed. The three cloud variable names present in the sandbox (`AWS_SECRET_ACCESS_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_CA_BUNDLE`, plus `ANTHROPIC_BASE_URL`) were unset for the pytest run; values never read.

## 0. Counts and limits first

| Item | Number |
|---|---|
| `file:line` or `file:a-b` cites extracted by script (including bare `:N` that follow a file name on the same line) | 340 (2 are false matches from `<call_id>:1`, `:2` in line 118; ignored) |
| extra comma-list cites (`file.py:65,123,148`) checked by script and by eye | 22 |
| distinct existing files cited | 79, all exist |
| files cited that do not exist today | 25 mentions of 14 names; every one is described by the document as new (list in section D); `.github/workflows/ci.yml` exists |
| cites whose line is beyond end of file | 0 |
| cites where the text does not support the claim (WRONG) | 2 |
| cites partly right (range or detail off) | 4 |
| stated counts recomputed | 13 checked, 12 match, 1 incomplete list (section B) |
| Everything else | text at the cited line supports the claim (section C) |

What I did NOT do: I read, for every cite, the document sentence and the first one to three source lines of the range (all 340 are in `raw-all-cites.tsv`). For about 90 of them (every one that carries a number, a named symbol or a "not X" claim) I opened more of the range. For the rest, "supports" means the cited line holds the named construct; I did not read every line of every wide range. I did not check document claims that cite no file (for example claims about what the provider bills). `bandit -ll` was not run: `bandit` is not installed in the sandbox and installing needs network.

## A. FAILURES FIRST (wrong or partly right)

| # | Doc line | Claim in doc | True value (file read) | Verdict |
|---|---|---|---|---|
| 1 | 225 | the second database connection for purge is built at `app.py:131-139` ("builds the second connection for purge the same way") | `app.py:131-139` is the `for name in cfg.scope_inventory:` warning loop and the start of `_toolbox(...)`. The purge connection is built at `app.py:152-160` (`if purge_name := getattr(b.store, "purge_dsn_secret_name", None):` at 152, `update={"dsn_secret_name": purge_name, ...}` at 157). The refusal for a missing purge DSN is at `app.py:86-89` | WRONG (lines 152-160) |
| 2 | 437 | "`Money` is the class at `config.py:41-47`" | `Money` is not a class. `config.py:45` is `Money = Annotated[Decimal, BeforeValidator(_money)]` (a type alias); the validator function `_money` is `:38-42`; `:48` starts `class _Strict`. Line 52 (F15) uses the same range for "rejects floats only", which is right | WRONG word and range (alias at :45) |
| 3 | 410 | the `make("llm"...)` sites in `tests/warden_port/test_providers.py` are `:65,123,148,172` | `grep -n 'make("llm"' tests/warden_port/test_providers.py` also finds `:198` (inside `test_a_model_must_be_named_exactly`, under `pytest.raises(ConfigError)`). The list is one site short; the other four files match (`test_bedrock_provider_r16.py` 74,79,90; `test_p5p6_followups.py` 300,302,417; `test_p5_llm.py` 230,301; `llm_wire.py` 66,91,119,192 and `test_p5_llm.py:248` direct constructions) | partly (1 site missing; this is the list the document calls "corrected") |
| 4 | 392, 410 | `tests/test_p6_detectors.py:351` | `:351` is `from hadavin_sdk.guard import bedrock_guardrail`; the test body that calls `make("detector", guardrail_settings())` follows at about `:355`. File and test are right; line is the import | partly (line off by about 4) |
| 5 | 53 (F16) | "`redact_untrusted` escapes marker and placeholder look-alikes; `redact_text` does not (`runmap.py:275-304`)" | `:275` is `escape_placeholders`, `:298` is `redact_untrusted`; `redact_text` is at `runmap.py:417`, outside the cited range. The statement about `redact_text` is not shown by the cited lines | partly (range covers only the first half of the claim) |
| 6 | 305, 614 (E0-12 pass rule), 3 | "no new cycle, only the cycle that exists today in the approvals package" | Recomputed (section E): at runtime-import level exactly one cycle: `approvals`, `approvals.channel`, `approvals.requests`. If imports under `if TYPE_CHECKING:` are counted there are two more: `{config, deferred, registry, replay_records}` and `{k1b.replay, k1b.report, k1b.score}`. The document does not say which counting it used | partly (true for runtime imports only) |

### Not cite errors, recorded because they bear on what the document says it ran
- Line 3/section 0 item 1: document says the v6 shape had cycle `[llm.gate, llm.common]`. `llm/gate.py` does not exist in the repository, so I cannot reproduce that; I can only confirm that today no `llm.*` module is in any cycle (section E).
- `checkpoint-handoff-v7.md` line 5 repeats the same cycle statement; same limit.

## B. COUNT CLAIMS

| Claim | Recomputed | Verdict |
|---|---|---|
| decisions D1-D25 (25 rows in section 3) | rows `\| D1 \|` .. `\| D25 \|`: 25 distinct, none missing, none duplicated | match |
| facts table: F1 .. F23 | 23 distinct rows (the document states no total) | match |
| E0 items: E0-1 .. E0-13 | 13 distinct list items | match |
| "12 gating PRs" (line 594) | numbered rows 1-12 in section 6 "Gating track" | match |
| "three call sites that can raise `SpendRefused`", all in `Runtime.handle` (`agent_loop.py:325-541`) | `_screen` at `:387`, `.chat(` at `:425`, `_screen` at `:520`; `handle` is `:325`, next method `:542`. Three, inside the range | match |
| `.chat(` call sites in `src/`: 5 (`extract.py:47`, `evals.py:73`, `guard/judge.py:72`, `runtime/agent_loop.py:425`, `k1b/loop.py:94`) | grep finds exactly these 5 real calls plus a docstring mention `guard/producers.py:5` (excluded by the document on purpose) | match |
| outside `src/`: `demos/ask-your-data/askdata/pipeline.py:155` | present (`reply = self.llm.chat(`) | match |
| all four network kinds call `self._retry(` (anthropic 122, bedrock 156, gemini 86, openai_compat 119) | grep: same four lines | match |
| `Limits(` built with three positional arguments at 9 places (`app.py:171`, `cli.py:209`, tests `test_s5_runtime.py:28`, `k5_support.py:206`, `test_k3_pilot.py:104`, `test_k5_postgres.py:58`, `test_k5_round5.py:241`, `test_k5_tools.py:1133`, `:1269`) | grep `Limits(` finds exactly these 9 (other `Limits(` hits are an unrelated demo class `askdata Limits`) | match |
| direct network-kind constructions in tests: `llm_wire.py:66,91,119,192`, `test_p5_llm.py:248` | grep finds exactly these 5 | match |
| `make("llm"...)` sites in tests | 15 sites by grep; document lists 14 (misses `test_providers.py:198`) | one missing (row 3) |
| security review had 5 majors and 7 nits; readiness review 2 blockers and 11 majors | `review-handoff-v6-security.md`: Major items 1-5, Nit items 1-7; `review-handoff-v6-readiness.md`: B1-B2, M1-M11 | match |
| v6 citation check had 4 wrong and 6 partly right | `evidence-handoff-v6/citation-check-v6.md`: rows 1-4 wrong, 5-10 partly | match |
| "125 pytest passed, 36 probes, 0 mismatches" from `evidence-handoff-v4.md` | `evidence-handoff-v4.md` says 125 passed and 0 mismatches; `raw-v4/probe.json` has 36 entries | match |
| numbers in section 0 item 6: `0.00225` per fake call; reserve about 0.0154 | `test_s4_llm_guard.py:38-39`: 500 in x 3/M + 50 out x 15/M = 0.00225 (comment and assert). `max_tokens` 1024 x 15/M = 0.01536; plus an input estimate gives "about 0.0154" (arithmetic only, not run) | match |
| fixture route 3.00 / 15.00, `max_tokens` 1024 (`tests/fixtures/config/config.yaml:6-8`) | those three lines | match |
| default `call_timeout_s` 60 and `max_attempts` 3 (`backends/table.py:34-40`) | `default=60.0`, `default=3` | match |

## C. Cites checked and supported (summary)

All other cites: text at the cited line or range holds the named construct. Every cited range was inside its file. Full machine list: `raw-all-cites.tsv` (document line, file, start, end, file length, in-file yes/no, first source line). Spot results worth knowing:

- Ranges named as a whole function or class match the real boundaries: `gate.py:647-678` (`_WRITE_SHAPES`), `gate.py:681-698` (`withhold_commands`), `chain.py:134-149` (`Verification`, decorator at 134), `chain.py:363-383` (`verify_rows`), `cli.py:349-363` (`audit_verify`), `agent_loop.py:239-250` (`_limits_stop`), `:318-322` (`_to`), `:569-597` (`_abstain`), `:560-567` (`_deliver`), `k1b/loop.py:40-52` (`Budget`), `:115-122` (`worst_case_usd`), `limits.py:13-30` (`Limits`).
- The v7 corrections to the v6 wrong cites hold: `agent_loop.py:432-434` is the `except ProviderError` clause; `extract.py:58` is the `safe_head(str(exc), 300)` call; `store/migrate.py:71` is `_FILE`; `ScriptLLM.everything_sent` at `tests/k5_support.py:156` in class `:124`; `FakeLLM` keys on `documents[0]` else `json.dumps(messages)` at `fake.py:39-40`.
- Claims with a "not" or "no": `FakeLLM` is a plain class with no base (`fake.py:21`); no "thinking", "cache_control", "cachedContent" or "reasoning" string in `src/hadavin_sdk/llm/*.py` (grep, 0 lines, exit 1; `raw-F19-grep.txt`); `rm` is not a key of `_VERB_FIRST` or `_WORD_RUN` (`gate.py:406`, `:463`; grep for `"rm"` finds nothing); `anchor_s3.py:1-12` states one constraint at `:5-7` and no action names; `audit/signer.py:104-108` does `is_file()` then `read_bytes()` with no mode check; `IBAN` is not in `defaults.STORED_KINDS` (`defaults.py:108-122`).
- `openai_compat.py:117-129` has `for _ in range(2)` around `self._retry(` (two request loops per call); `:122` sums tokens and `:131` sets `got.tokens`.
- Existing `retry.py:95-96` is `except ProviderError: raise`, so the proposed one-line change there is placed on the right lines.

## D. Files cited that do not exist today (document calls each new)

`llm/spend.py`, `llm/gate.py`, `llm/metered.py`, `llm/build.py`, `store/amounts.py`, `store/migrations/0006_spend_op.sql` (existing migrations are `0001`-`0005`, so "no gap" is right), `hadavin_sdk/fileguard.py`, `tests/gate_support.py`, `tests/false_abstain_report.py`. Their line numbers cannot be checked; none is cited with a line.

## E. Import graph (document E0-12)

Program: `import_graph.py` in this folder (AST; reads every `.py` under `src/hadavin_sdk`; resolves `import` and `from ... import` including relative and `from pkg import module`; Tarjan strongly connected sets of size 2 or more). Raw output: `raw-import-graph.txt`. 102 modules.

| Counting | Edges | Cycles |
|---|---|---|
| all imports | 353 | 3 |
| module level (not inside def/class) | 335 | 3 |
| runtime only (module level, skipping `if TYPE_CHECKING:` bodies) | 330 | 1: `approvals`, `approvals.channel`, `approvals.requests` |

The other two sets exist only through `TYPE_CHECKING` imports: `{config, deferred, registry, replay_records}` (`deferred.py:15`, `replay_records.py:22` import `registry` under `TYPE_CHECKING`) and `{k1b.replay, k1b.report, k1b.score}`.

Cycles that include an `llm.*` module: none, in any counting. Edges the document states: `llm.retry -> llm.protocol` exists (`retry.py:20`); `llm.protocol -> models` only (`protocol.py:7`); `llm.common -> {errors, guard.http, llm.retry, models}` today (`common.py:18-21`), so no `llm.common <-> llm.gate` edge can exist yet (`gate.py` is absent). The document's pass rule for E0-12 is therefore trivially true on today's tree; the check is meaningful only after M2-0.

## F. Document's own E0 commands (read-only, no network, no Postgres, no spend)

| Command | Run? | Result |
|---|---|---|
| E0-1 `ruff check` | yes, `ruff check --no-cache` (installed ruff, not `uv run`: `uv run` may sync and needs network) | exit 0, "All checks passed!" (`raw-E0-1-ruff-check.txt`) |
| E0-1 `ruff format --check` | yes, same way | exit 0, "299 files already formatted" (`raw-E0-1-ruff-format.txt`) |
| E0-1 `pytest` | yes, section G | exit 1: 2 failed, 9389 passed, 455 skipped (both failures are under `handover/`) |
| E0-1 `bandit -ll` | NOT run: `bandit` is not installed in `.venv` or the system Python, install needs network | skipped |
| F19 `grep thinking\|cache_control\|cachedContent\|reasoning llm/*.py` | yes (`raw-F19-grep.txt`) | exit 1, 0 lines (matches the document: no hits) |
| E0-8 `grep -rn "environment: dev\|environment=\"dev\"" tests demos docs` | yes (`raw-E0-8-grep.txt`) | exit 0, 2 lines: `tests/fixtures/config/config.yaml:2: environment: dev` and `tests/test_p4_secrets.py:106: def _config(..., environment="dev")` |
| E0-1 side greps (every `Limits(` caller, `.chat(` sites, direct network-kind constructions, `make("llm"`, `self._retry(`, `apply_guardrail(`) | yes (`raw-counts-grep.txt`) | section B |
| line 23 `grep -ril cache` | yes (`raw-line23-grep.txt`) | 25 files listed (the document gives no count) |
| E0-2 .. E0-7, E0-9 .. E0-11, E0-13 | NOT run: each needs Postgres, a script that the builders write in a later PR, or code that does not exist yet (`reserve_estimate`, `spend_op`, `false_abstain_report.py`, the invoice corpus) | skipped |
| E0-12 | yes, section E | no cycle with `llm.*` |

## G. pytest (E0-1), run with no cloud variables, no Postgres DSN, no cache

Command (not the document's `uv run` form, which may sync packages over the network): `env -u AWS_SECRET_ACCESS_KEY -u AWS_ACCESS_KEY_ID -u AWS_CA_BUNDLE -u ANTHROPIC_BASE_URL -u HADAVIN_TEST_PG_DSN .venv/bin/python -m pytest -p no:cacheprovider -q --no-header`. Exit code gated, not piped.

- First run with `-x`: stopped at the first failure after 8712 passed (`raw-E0-1-pytest.txt`). Not a full run.
- Full run without `-x` (`raw-E0-1-pytest-full-no-x.txt`): **exit 1: 2 failed, 9389 passed, 455 skipped in 251 s.** The skips include the Postgres tests (no DSN set).
  1. `tests/test_repo_rules.py::test_licences_are_proprietary`: 10 problems, all under `handover/promotion-inputs/` (LICENSE text and `pyproject.toml` licence and author fields of copied demo projects).
  2. `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked`: one banned string in `handover/core-hardening/steps-edits/evidence-v23/plant-v23.py`.
  Both are about tracked files under `handover/`. Neither concerns the v7 document, `src/` or `tests/`. I did not check whether they fail at the repository's last commit; I did not fix them (evidence runner). My own files in this folder were tracked-scanned by the second test only if tracked; it names none of them.
- The cause of both failures is not judged here.

## H. Compared with `evidence-handoff-v6/citation-check-v6.md`: which v6 wrong cites are now right

| v6 row | v6 problem | In v7 |
|---|---|---|
| 1 | `:431` for `except ProviderError` | now `agent_loop.py:432-434` (line 445): RIGHT |
| 2 | `extract.py:55` | now `extract.py:58` (line 484): RIGHT |
| 3 | `_FILE` at `migrate.py:70` | now `:71` (lines 122, 225): RIGHT |
| 4 | `FakeLLM.everything_sent` | now `ScriptLLM.everything_sent` at `tests/k5_support.py:156`, class `:124` (lines 47, 60): RIGHT |
| 5 | recorded replies keyed only on `documents[0]` | now "when documents exist, else `json.dumps(messages, sort_keys=True)`" (`fake.py:39-40`, lines 47, 492): RIGHT |
| 6 | five files said to build a network kind directly | list rebuilt (line 410): direct constructions are `llm_wire.py` and `test_p5_llm.py:248`; `test_k1b_replay.py:391` removed. One `make("llm"` site missing (`test_providers.py:198`, section A row 3): PARTLY |
| 7 | `verify_rows` `:362-385` | now `:363-383`: RIGHT |
| 8 | Bedrock status range `bedrock.py:93-110` | now `detail()` `:93-101` and `retryable()` `:104-110` named separately (line 274): RIGHT |
| 9 | `k5_support.py:160-204` | now `:160-211` with `Runtime(` call at `:200-209`: RIGHT |
| 10 | S3 docstring claim | now "states one constraint at `:5-7`, no actions" (lines 97, 555): RIGHT |
| 11 | D5 vs `ORDERS.md` Q28 | still stated knowingly (line 7); not a cite error |

Result: 9 of the 10 v6 wrong or partly-right cites are now right; 1 (row 6) is partly right. New problems in v7 not present in v6: section A rows 1, 2, 4, 5, 6 (row 3 is the leftover of v6 row 6).

## Files in this folder

`citation-check-v7.md` (this file), `raw-all-cites.tsv`, `raw-counts-grep.txt`, `raw-F19-grep.txt`, `raw-E0-8-grep.txt`, `raw-line23-grep.txt`, `raw-E0-1-ruff-check.txt`, `raw-E0-1-ruff-format.txt`, `raw-E0-1-pytest.txt`, `raw-E0-1-pytest-full-no-x.txt`, `import_graph.py`, `raw-import-graph.txt`.

Note on the raw logs: the failing assertion of test 2 in section G printed the banned vendor string. I replaced it with `[banned-string-removed]` in the raw pytest log (the only edit to any raw file) so this folder passes the repository's own vendor-string test.
