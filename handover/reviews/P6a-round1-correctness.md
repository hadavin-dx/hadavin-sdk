# Review: P6a round 1, correctness lens (ticket P6a revision 1)

- Ticket: P6a, revision 1
- Lens: correctness
- Status: REPORTED (saved by the lead session from the reviewer hand-back, which is model output, not user authority)

---

R1 CORRECTNESS review, P6a revision 1 (125 lines; the file read has 125 lines). The task path `handover/tickets/P6a.md` does not exist; the real file is `handover/tickets/P6a.md`. I checked the cites against the checkout at the repository src tree and tests. It is not a git repo, so I cannot check commit 124258b or ce70eb5 byte-identity. I did not read handover/reviews or handover/evidence.

| id | sev | ticket line | problem | fix |
|---|---|---|---|---|
| R1-COR-1 | Major | 66 (fail-before) | The expected table is wrong in two places. (1) T6(c) "first five planted alias rows FAIL": the same line says to copy `tests/_model_calls.py` into the base worktree. The rows then run against the NEW scanner and pass. They fail only against the old `_sink_callers`. (2) T5(g) "FAIL": on base nothing passes `allow_test_doubles`, so the row passes (it is a pin). T5(d) fails with a TypeError (unknown keyword), not an assertion. | For T6, run the planted rows against the old `_sink_callers` logic, or against a copy of the helper with mutant 12 applied. List T5(g) as a pin and give it a mutant, or drop its fail-before claim. Say how T5(d) fails. |
| R1-COR-2 | Major | 59, 63, 65, 53 | No prod-valid fixture exists. `pilot_cfg(env="prod")` (`tests/test_k3_pilot_env.py:35-74`) has `anchor` unset (default `none`) and a signer with `private_key_path`. Both are refused in prod (`config.py:391-396`: `NOT_PROD` pair `anchor/none`; ed25519 with key file). No test uses `env="prod"` (grep finds none). So the prod rows of T5(b) (4 rows), T5 prod, T7(d) and T1 prod (12 rows) cannot reach the new check from `pilot_cfg`. They fail at `load_config`, and T5/T7 would not match their expected messages. The ticket never mentions this. | Add a step to build a prod fixture (anchor with `retention_ack`, key from a secret name), with a test that it loads. Say which rows use it. |
| R1-COR-3 | Major | 53, 109 | The count of tests needing `allow_test_doubles=True` is false. `test_k5_tools.py:1031` and `:1033` use `k5_cfg` (a dev config). `:1033` passes `sources=` and expects success, which is impossible in a live profile (`app.py:90-92`). Of the 7 listed sites, only `test_k3_pilot_env.py:185` and `test_k5_round8_postgres.py:40` get past `app.py:98`. The other 3 listed (`round9b:370`, `round10:80`, `round5:226`) hit earlier refusals, as the ticket says. So the real count is 2 (the ticket says "about 4"), and both are Postgres-gated (`pg_schema`). | Correct the list and count. State that T5(d) and T7(c) skip or cannot run without Postgres, and say how fail-before evidence is produced without it. |
| R1-COR-4 | Major | 27, 51, 64 | S4 says `_sink_callers` "now uses `model_call_sites`" and "the result is unchanged on today's tree". Today `_sink_callers` (`test_k5_producers.py:80-87`) scans `src` AND `demos/` (path prefix `demos/`, which gives the `demos/ask-your-data/askdata/pipeline.py` entry of `MODEL_CALLERS`). S4/T6 scope is `src/` only, and the helper returns `(module, function)` tuples, not module paths. A naive switch drops the demo from the registry check, so the result changes. | Give the helper a roots and prefix argument that preserves the demo scan (or state that dropping it is a behaviour change, and decide that under PENDING LEAD 6). State how tuples map to module strings. |
| R1-COR-5 | Major | 80, 63 | Mutant 10 (new check placed before the `sources=` check) is killed by T5(f) only if the row passes `sources=` together with an override. T5(f) as written does not say so (the new check does not fire without an override). A `tools=` plus override ordering row is also absent, so the ticket's "existing refusals keep their messages and order" (line 42) is pinned for `tools=` only by the old test `round5:226`. | Say T5(f) passes `sources=` AND `llm=`; add the same for `tools=`; name `round5:226` as the existing killer. |
| R1-COR-6 | Major | Header, 27, 44 | The claim is stronger than the test. The header and plan row say "no code path in `src/` reaches the llm kind except through the masking wrapper". The scanner (line 44) catches only attribute names `chat` and `apply_guardrail`, and `getattr`, `attrgetter` or `methodcaller` whose first argument is a string constant. It misses `getattr(llm, "ch"+"at")`, a name held in a variable, `vars(x)["chat"]`, `__getattribute__`, and direct construction of an adapter from `llm/*` outside `llm/`. The protection against that last case is P5c's `isinstance` / import-graph test, which is PENDING P5c. Lines 12 and 27 say "in any form". | Narrow the wording ("attribute reads of two names, by constant string"). Add a row or mutant that requires non-constant `getattr` to be reported, or refused (fail the scan when a non-constant `getattr` or `attrgetter` argument is present). Name the P5c test as the real guard. |
| R1-COR-7 | Minor | 42 | "before any backend is built" is false for the secrets kind: `app.py:82` builds `make("secrets", ...)` when `secrets=None`, before `live` is computed. The ticket notes only that the check reads the argument. | Reword to "before any backend other than the secrets provider". |
| R1-COR-8 | Minor | 37 | The hot-files line says P6a does not touch `cli.py`, `table.py` or `tests/test_lockin_guard.py`. Amendment A9 F6 (the later entry, which wins) lists P6a on all three, and `config.py`, as hot files. The ticket records the cut but no lead answer exists. | Add this to PENDING LEAD, or get a one-line amendment. |
| R1-COR-9 | Minor | 40, 28 | `tickets/P1.md:47` says the strict wiring is "P6a's, which owns `config.py`". P6a chooses `app.py` (PENDING LEAD 2). The target-module line should flag the mismatch with P1, and so should `config.py`'s status as P6a's file, which depends on lead answer 2 and lead answer 3. | Cross-reference P1.md:47 in PENDING LEAD 2. |
| R1-COR-10 | Minor | 71, 75 | Mutants 1 and 5 cite `config.py:366` and `:373`. P5c, P4b1 and P6b1 all edit `config.py` first, so the line numbers will drift. | Cite by code text instead of line number. |
| R1-COR-11 | Minor | 28 | The 3.12 Unicode version is marked UNVERIFIED, but it is derivable: CPython 3.12 ships Unicode 15.0.0 and 3.13 ships 15.1.0 (from my own knowledge, not checked in this environment). The conclusion "a pin of 15.1.0 fails on 3.12" holds. `requires-python = ">=3.12"` is unchecked here (`pyproject.toml`). | Optional. Say "3.12 differs (15.0.0)" and stop calling it unknown. |
| R1-COR-12 | Nit | 59 | "Rows `llm/fake` ... 'PL61 row'": the row count (12 + 6 + T1c + T1d) is never summed. Together with the T5, T6 and T7 rows there is no total. | Add a total row count for the plan row's test file. |

Verified (read in code, checkout at the repository root):
- `app.py:62-69` (the override parameters), `:82`, `:90-92`, `:93-98`, `:162`, `:163-166`, `:170` and `:172-174` (no executor when live) all match.
- `config.py:317`; the refusal list at `:365-373`; `_anchor_refusals` at `:377` with its prod additions at `:391-392`; `load_config` at `:453-454`.
- `backends/table.py`: `TABLE` at `:386`, `Entry` at `:333`, `DEFAULTS` at `:582-589`, `DEV_ONLY` at `:593-602` with exactly the 6 named pairs, `NOT_PROD` at `:604`. `deferred.LIVE` at `deferred.py:33`.
- `Backends.llm` has no default (`config.py:70`) and `DEFAULTS` has no llm entry. `entries()` covers every capability (`config.py:74-76`).
- `test_k5_producers.py:22` (`SINK_METHODS`) and `:78-95` (`_sink_callers`, call-only shape at `:89-94`).
- The six model-call sites outside `llm/`, found by grep: `evals.py:73`, `extract.py:47`, `guard/judge.py:72`, `guard/bedrock_guardrail.py:101` (`apply_guardrail`), `k1b/loop.py:94`, `runtime/agent_loop.py:425`. No other `.chat` attribute exists in `src/`.
- `MODEL_CALLERS` at `producers.py:55-65` (6 plus the demo). `demos/.../pipeline.py:155` calls `.chat(`.
- `cli.py:282` imports `build` (the call is at `:299`, with no overrides).
- `test_k3_pilot_env.py:184-191` builds a pilot app with `secrets=`, `channel=` and `llm=` overrides (the "repository's own test" claim holds).
- Lines `ci.yml:73`, `:109`, `:79-81`, `:119` hold what the ticket says.
- Mutant list: 16 entries numbered 1-16, matching the stated count of 16.
- Ordering and ledger facts against `amendments.md`: A6 ("P6a builds on it"), A9 F6 (dependencies and app.py order), A4 (config.py hot file).
- Plan row P6a (`plan-v3.md:111`) and the section 9 row (`:184`) match. The plan row's depends-on column says "P4b, P5c"; the ticket widens it with reasons.
- All 17 template fields are present and in order.

Not checked (UNVERIFIED):
- Any git claim: that `124258b` and `ce70eb5` are identical for the cited files, or that the `git diff --stat` output is as stated.
- Everything about P5c (no ticket), P6b2 (no ticket), P1a names (`UnidataMismatch`, `check_pinned_unidata`; neither exists in `src` yet), and P1m's runner command.
- `test_k5_round5.py:883` and the other pilot-config users; the ticket's AST scan of all live `build` calls was not repeated in full.
- The contents of the other tickets cited (P4b1, P4b2, P4c, P6b1) and the C1 frozen design.
- `LEAD-ORDERS.md` orders 6-11 (long lines were omitted from my grep); "order 8 cut", order 15 and order 19 B limits are unchecked.
- Whether `pilot_cfg` still passes P6b1's no-training refusal. T6, T7 and mutant outcomes were never run.
